"""Strict input contracts for the offline network-simulation labs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class ContractError(ValueError):
    """Raised when a lab input violates its fail-closed contract."""


def _object(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ContractError(f"{where} must be an object")
    return value


def _exact_keys(
    value: dict[str, Any],
    required: set[str],
    where: str,
    optional: set[str] | None = None,
) -> None:
    optional = optional or set()
    missing = required - value.keys()
    unknown = value.keys() - required - optional
    if missing:
        raise ContractError(f"{where} is missing keys: {sorted(missing)}")
    if unknown:
        raise ContractError(f"{where} has unknown keys: {sorted(unknown)}")


def _number(value: Any, where: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ContractError(f"{where} must be a number")
    result = float(value)
    if minimum is not None and result < minimum:
        raise ContractError(f"{where} must be >= {minimum}")
    return result


def _integer(value: Any, where: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"{where} must be an integer >= {minimum}")
    return value


def _rate(value: Any, where: str) -> float:
    result = _number(value, where, minimum=0.0)
    if result > 1.0:
        raise ContractError(f"{where} must be <= 1")
    return result


def _text(value: Any, where: str, pattern: str | None = None) -> str:
    if not isinstance(value, str) or not value:
        raise ContractError(f"{where} must be a non-empty string")
    if pattern and not re.fullmatch(pattern, value):
        raise ContractError(f"{where} has a forbidden format")
    return value


def safe_relative_path(root: Path, relative: str) -> Path:
    """Resolve a path while rejecting absolute paths, traversal, and escapes."""

    candidate = Path(relative)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ContractError("dataset path must be a confined relative path")
    resolved_root = root.resolve()
    resolved = (root / candidate).resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ContractError("dataset path escapes the dataset root")
    return resolved


def load_json(root: Path, relative: str) -> dict[str, Any]:
    path = safe_relative_path(root, relative)
    try:
        with path.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot load {relative}: {exc}") from exc
    return _object(value, relative)


def validate_provenance(value: Any, where: str) -> None:
    item = _object(value, where)
    _exact_keys(item, {"kind", "generator", "license", "description"}, where)
    if item["kind"] != "synthetic":
        raise ContractError(f"{where}.kind must be synthetic")
    if item["license"] != "CC0-1.0":
        raise ContractError(f"{where}.license must be CC0-1.0")
    _text(item["generator"], f"{where}.generator")
    _text(item["description"], f"{where}.description")


def validate_scenario(value: Any) -> dict[str, Any]:
    item = _object(value, "scenario")
    _exact_keys(
        item,
        {"schema_version", "synthetic", "provenance", "seeds", "queue", "impairments"},
        "scenario",
    )
    if item["schema_version"] != "1.0" or item["synthetic"] is not True:
        raise ContractError("scenario must be schema 1.0 and explicitly synthetic")
    validate_provenance(item["provenance"], "scenario.provenance")
    seeds = item["seeds"]
    if not isinstance(seeds, list) or len(seeds) < 3:
        raise ContractError("scenario.seeds must contain at least three fixed seeds")
    checked_seeds = [_integer(seed, "scenario.seeds[]") for seed in seeds]
    if len(set(checked_seeds)) != len(checked_seeds):
        raise ContractError("scenario.seeds must be unique")

    queue = _object(item["queue"], "scenario.queue")
    _exact_keys(
        queue,
        {"duration_ms", "arrival_rate_pps", "service_rate_pps", "buffer_packets"},
        "scenario.queue",
    )
    _integer(queue["duration_ms"], "scenario.queue.duration_ms", minimum=1)
    arrival = _number(queue["arrival_rate_pps"], "scenario.queue.arrival_rate_pps", minimum=0.001)
    service = _number(queue["service_rate_pps"], "scenario.queue.service_rate_pps", minimum=0.001)
    if arrival >= service:
        raise ContractError("the baseline queue must have arrival_rate_pps < service_rate_pps")
    _integer(queue["buffer_packets"], "scenario.queue.buffer_packets", minimum=1)

    impairments = _object(item["impairments"], "scenario.impairments")
    _exact_keys(
        impairments,
        {
            "packet_count",
            "spacing_ms",
            "base_delay_ms",
            "jitter_ms",
            "loss_rate",
            "duplicate_rate",
            "duplicate_extra_delay_ms",
        },
        "scenario.impairments",
    )
    _integer(impairments["packet_count"], "scenario.impairments.packet_count", minimum=2)
    _number(impairments["spacing_ms"], "scenario.impairments.spacing_ms", minimum=0.001)
    base_delay = _number(impairments["base_delay_ms"], "scenario.impairments.base_delay_ms", minimum=0.0)
    jitter = _number(impairments["jitter_ms"], "scenario.impairments.jitter_ms", minimum=0.0)
    if jitter > base_delay:
        raise ContractError("jitter_ms cannot exceed base_delay_ms")
    _rate(impairments["loss_rate"], "scenario.impairments.loss_rate")
    _rate(impairments["duplicate_rate"], "scenario.impairments.duplicate_rate")
    _number(
        impairments["duplicate_extra_delay_ms"],
        "scenario.impairments.duplicate_extra_delay_ms",
        minimum=0.0,
    )
    return item


def validate_routing_replay(value: Any) -> dict[str, Any]:
    item = _object(value, "routing_replay")
    _exact_keys(
        item,
        {"schema_version", "synthetic", "provenance", "source", "destination", "nodes", "links", "events"},
        "routing_replay",
    )
    if item["schema_version"] != "1.0" or item["synthetic"] is not True:
        raise ContractError("routing_replay must be schema 1.0 and explicitly synthetic")
    validate_provenance(item["provenance"], "routing_replay.provenance")
    nodes = item["nodes"]
    if not isinstance(nodes, list) or len(nodes) < 2 or len(set(nodes)) != len(nodes):
        raise ContractError("routing_replay.nodes must be a unique node list")
    for index, node in enumerate(nodes):
        _text(node, f"routing_replay.nodes[{index}]", r"[A-Z][A-Z0-9]{0,7}")
    source = _text(item["source"], "routing_replay.source")
    destination = _text(item["destination"], "routing_replay.destination")
    if source not in nodes or destination not in nodes or source == destination:
        raise ContractError("routing endpoints must be distinct known nodes")

    links = item["links"]
    if not isinstance(links, list) or not links:
        raise ContractError("routing_replay.links must be a non-empty list")
    pairs: set[tuple[str, str]] = set()
    for index, raw_link in enumerate(links):
        link = _object(raw_link, f"routing_replay.links[{index}]")
        _exact_keys(link, {"a", "b", "cost", "up"}, f"routing_replay.links[{index}]")
        if link["a"] not in nodes or link["b"] not in nodes or link["a"] == link["b"]:
            raise ContractError("each link must join two distinct known nodes")
        pair = tuple(sorted((link["a"], link["b"])))
        if pair in pairs:
            raise ContractError(f"duplicate link: {pair}")
        pairs.add(pair)
        _number(link["cost"], f"routing_replay.links[{index}].cost", minimum=0.001)
        if not isinstance(link["up"], bool):
            raise ContractError("link.up must be boolean")

    events = item["events"]
    if not isinstance(events, list) or not events:
        raise ContractError("routing_replay.events must be a non-empty list")
    previous_time = -1
    for index, raw_event in enumerate(events):
        event = _object(raw_event, f"routing_replay.events[{index}]")
        _exact_keys(
            event,
            {"observed_at_ms", "applied_at_ms", "action", "a", "b", "expected_path"},
            f"routing_replay.events[{index}]",
            optional={"value"},
        )
        observed = _integer(event["observed_at_ms"], "event.observed_at_ms")
        applied = _integer(event["applied_at_ms"], "event.applied_at_ms")
        if observed < previous_time or applied < observed:
            raise ContractError("routing events must be ordered and applied no earlier than observed")
        previous_time = observed
        if tuple(sorted((event["a"], event["b"]))) not in pairs:
            raise ContractError("routing event references an unknown link")
        if event["action"] not in {"link_down", "link_up", "cost_change"}:
            raise ContractError("unsupported routing action")
        if event["action"] == "cost_change":
            _number(event.get("value"), "event.value", minimum=0.001)
        elif "value" in event:
            raise ContractError("value is only valid for cost_change")
        expected = event["expected_path"]
        if not isinstance(expected, list) or len(expected) < 2 or any(node not in nodes for node in expected):
            raise ContractError("event.expected_path must be a path over known nodes")
    return item


def validate_calibration_trace(value: Any) -> dict[str, Any]:
    item = _object(value, "calibration_trace")
    _exact_keys(
        item,
        {"schema_version", "synthetic", "provenance", "model", "records"},
        "calibration_trace",
    )
    if item["schema_version"] != "1.0" or item["synthetic"] is not True:
        raise ContractError("calibration_trace must be schema 1.0 and explicitly synthetic")
    validate_provenance(item["provenance"], "calibration_trace.provenance")
    if item["model"] != "mm1_mean_response_time":
        raise ContractError("unsupported calibration model")
    records = item["records"]
    if not isinstance(records, list) or len(records) < 6:
        raise ContractError("calibration_trace.records must contain train and held-out samples")
    splits: set[str] = set()
    for index, raw_record in enumerate(records):
        record = _object(raw_record, f"calibration_trace.records[{index}]")
        _exact_keys(
            record,
            {"split", "arrival_rate_pps", "observed_mean_delay_ms", "ood"},
            f"calibration_trace.records[{index}]",
        )
        if record["split"] not in {"train", "holdout"}:
            raise ContractError("record.split must be train or holdout")
        splits.add(record["split"])
        _number(record["arrival_rate_pps"], "record.arrival_rate_pps", minimum=0.001)
        _number(record["observed_mean_delay_ms"], "record.observed_mean_delay_ms", minimum=0.001)
        if not isinstance(record["ood"], bool):
            raise ContractError("record.ood must be boolean")
        if record["split"] == "train" and record["ood"]:
            raise ContractError("training records cannot be marked OOD")
    if splits != {"train", "holdout"}:
        raise ContractError("calibration trace needs both train and holdout records")
    return item


def validate_emulation_request(value: Any) -> dict[str, Any]:
    item = _object(value, "emulation_request")
    _exact_keys(
        item,
        {
            "schema_version",
            "synthetic",
            "provenance",
            "namespace",
            "interface",
            "peer_interface",
            "bandwidth_mbps",
            "delay_ms",
            "jitter_ms",
            "loss_rate",
            "duplicate_rate",
            "reorder_rate",
        },
        "emulation_request",
    )
    if item["schema_version"] != "1.0" or item["synthetic"] is not True:
        raise ContractError("emulation_request must be schema 1.0 and explicitly synthetic")
    validate_provenance(item["provenance"], "emulation_request.provenance")
    _text(item["namespace"], "emulation_request.namespace", r"simlab-[a-z0-9][a-z0-9-]{0,30}")
    interface = _text(item["interface"], "emulation_request.interface", r"lab[0-9]{1,3}")
    peer = _text(item["peer_interface"], "emulation_request.peer_interface", r"lab[0-9]{1,3}")
    if interface == peer:
        raise ContractError("emulation interfaces must be distinct")
    _number(item["bandwidth_mbps"], "emulation_request.bandwidth_mbps", minimum=0.001)
    delay = _number(item["delay_ms"], "emulation_request.delay_ms", minimum=0.0)
    jitter = _number(item["jitter_ms"], "emulation_request.jitter_ms", minimum=0.0)
    if jitter > delay:
        raise ContractError("emulation jitter cannot exceed delay")
    _rate(item["loss_rate"], "emulation_request.loss_rate")
    _rate(item["duplicate_rate"], "emulation_request.duplicate_rate")
    _rate(item["reorder_rate"], "emulation_request.reorder_rate")
    return item
