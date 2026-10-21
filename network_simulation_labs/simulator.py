"""Pure standard-library simulation kernels; no command execution exists here."""

from __future__ import annotations

import heapq
import math
import random
import statistics
from collections import deque
from typing import Any, Iterable

from .contracts import ContractError


def _round(value: float) -> float:
    return round(float(value), 6)


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def summarize(values: Iterable[float]) -> dict[str, float | int]:
    samples = [float(value) for value in values]
    if not samples:
        raise ValueError("cannot summarize an empty sample")
    deviation = statistics.stdev(samples) if len(samples) > 1 else 0.0
    half_width = 1.96 * deviation / math.sqrt(len(samples))
    return {
        "n": len(samples),
        "mean": _round(statistics.fmean(samples)),
        "sample_stddev": _round(deviation),
        "ci95_half_width": _round(half_width),
        "minimum": _round(min(samples)),
        "maximum": _round(max(samples)),
    }


def simulate_queue(profile: dict[str, Any], seed: int) -> dict[str, Any]:
    """Replay an M/M/1/K queue with explicit arrival/departure events."""

    rng = random.Random(seed)
    duration = float(profile["duration_ms"])
    arrival_rate = float(profile["arrival_rate_pps"]) / 1000.0
    service_rate = float(profile["service_rate_pps"]) / 1000.0
    capacity = int(profile["buffer_packets"])

    events: list[tuple[float, int, str, int, float]] = []
    next_arrival = rng.expovariate(arrival_rate)
    packet_id = 0
    while next_arrival <= duration:
        service_ms = rng.expovariate(service_rate)
        heapq.heappush(events, (next_arrival, 1, "arrival", packet_id, service_ms))
        packet_id += 1
        next_arrival += rng.expovariate(arrival_rate)

    waiting: deque[tuple[int, float, float]] = deque()
    busy = False
    accepted = 0
    dropped = 0
    completed = 0
    total_service_ms = 0.0
    delays: list[float] = []
    last_departure = 0.0

    def start_service(now: float, packet: tuple[int, float, float]) -> None:
        nonlocal busy, total_service_ms
        queued_id, arrived_at, service_ms = packet
        busy = True
        total_service_ms += service_ms
        heapq.heappush(events, (now + service_ms, 0, "departure", queued_id, arrived_at))

    while events:
        now, _priority, kind, current_id, payload = heapq.heappop(events)
        if kind == "arrival":
            occupancy = len(waiting) + int(busy)
            if occupancy >= capacity:
                dropped += 1
                continue
            accepted += 1
            packet = (current_id, now, payload)
            if busy:
                waiting.append(packet)
            else:
                start_service(now, packet)
        else:
            completed += 1
            busy = False
            arrived_at = payload
            delays.append(now - arrived_at)
            last_departure = now
            if waiting:
                start_service(now, waiting.popleft())

    generated = accepted + dropped
    horizon = max(duration, last_departure)
    return {
        "seed": seed,
        "generated_packets": generated,
        "accepted_packets": accepted,
        "completed_packets": completed,
        "dropped_packets": dropped,
        "drop_rate": _round(dropped / generated if generated else 0.0),
        "mean_response_ms": _round(statistics.fmean(delays) if delays else 0.0),
        "p95_response_ms": _round(_percentile(delays, 0.95)),
        "throughput_pps": _round(completed * 1000.0 / horizon if horizon else 0.0),
        "server_utilization": _round(min(1.0, total_service_ms / horizon if horizon else 0.0)),
        "drain_time_ms": _round(max(0.0, last_departure - duration)),
    }


def simulate_impairments(profile: dict[str, Any], seed: int) -> dict[str, Any]:
    """Apply delay, jitter, loss, duplication, and resulting reordering."""

    rng = random.Random(seed ^ 0x5A17)
    deliveries: list[dict[str, float | int | bool]] = []
    lost = 0
    duplicate_count = 0
    packet_count = int(profile["packet_count"])
    spacing = float(profile["spacing_ms"])
    base_delay = float(profile["base_delay_ms"])
    jitter = float(profile["jitter_ms"])

    for sequence in range(packet_count):
        sent_at = sequence * spacing
        if rng.random() < float(profile["loss_rate"]):
            lost += 1
            continue
        delay = base_delay + rng.uniform(-jitter, jitter)
        deliveries.append(
            {
                "sequence": sequence,
                "duplicate": False,
                "delay_ms": delay,
                "delivered_at_ms": sent_at + delay,
            }
        )
        if rng.random() < float(profile["duplicate_rate"]):
            duplicate_count += 1
            duplicate_delay = delay + float(profile["duplicate_extra_delay_ms"])
            deliveries.append(
                {
                    "sequence": sequence,
                    "duplicate": True,
                    "delay_ms": duplicate_delay,
                    "delivered_at_ms": sent_at + duplicate_delay,
                }
            )

    deliveries.sort(key=lambda item: (item["delivered_at_ms"], item["sequence"], item["duplicate"]))
    max_original_sequence = -1
    reordered = 0
    original_delays: list[float] = []
    for delivery in deliveries:
        if delivery["duplicate"]:
            continue
        sequence = int(delivery["sequence"])
        original_delays.append(float(delivery["delay_ms"]))
        if sequence < max_original_sequence:
            reordered += 1
        max_original_sequence = max(max_original_sequence, sequence)

    delivered_originals = packet_count - lost
    return {
        "seed": seed,
        "sent_packets": packet_count,
        "delivered_originals": delivered_originals,
        "lost_packets": lost,
        "duplicate_packets": duplicate_count,
        "reordered_originals": reordered,
        "observed_loss_rate": _round(lost / packet_count),
        "observed_duplicate_rate": _round(duplicate_count / delivered_originals if delivered_originals else 0.0),
        "observed_reorder_rate": _round(reordered / delivered_originals if delivered_originals else 0.0),
        "mean_delay_ms": _round(statistics.fmean(original_delays) if original_delays else 0.0),
        "p95_delay_ms": _round(_percentile(original_delays, 0.95)),
    }


def _shortest_path(
    nodes: list[str],
    links: dict[tuple[str, str], dict[str, Any]],
    source: str,
    destination: str,
) -> list[str]:
    adjacency: dict[str, list[tuple[str, float]]] = {node: [] for node in nodes}
    for (a, b), link in links.items():
        if link["up"]:
            adjacency[a].append((b, float(link["cost"])))
            adjacency[b].append((a, float(link["cost"])))
    queue: list[tuple[float, tuple[str, ...], str]] = [(0.0, (source,), source)]
    best: dict[str, float] = {source: 0.0}
    while queue:
        cost, path, node = heapq.heappop(queue)
        if cost > best.get(node, math.inf):
            continue
        if node == destination:
            return list(path)
        for neighbor, edge_cost in sorted(adjacency[node]):
            candidate = cost + edge_cost
            if candidate <= best.get(neighbor, math.inf):
                best[neighbor] = candidate
                heapq.heappush(queue, (candidate, path + (neighbor,), neighbor))
    return []


def _path_is_live(path: list[str], links: dict[tuple[str, str], dict[str, Any]]) -> bool:
    return bool(path) and all(
        links[tuple(sorted((a, b)))]["up"] for a, b in zip(path, path[1:])
    )


def replay_routing(dataset: dict[str, Any]) -> dict[str, Any]:
    nodes = list(dataset["nodes"])
    links = {
        tuple(sorted((link["a"], link["b"]))): {"cost": float(link["cost"]), "up": link["up"]}
        for link in dataset["links"]
    }
    source = dataset["source"]
    destination = dataset["destination"]
    active_path = _shortest_path(nodes, links, source, destination)
    initial_path = list(active_path)
    event_results: list[dict[str, Any]] = []
    total_blackhole_ms = 0

    for event in dataset["events"]:
        pair = tuple(sorted((event["a"], event["b"])))
        if event["action"] == "link_down":
            links[pair]["up"] = False
        elif event["action"] == "link_up":
            links[pair]["up"] = True
        else:
            links[pair]["cost"] = float(event["value"])
        convergence_ms = event["applied_at_ms"] - event["observed_at_ms"]
        blackhole_ms = convergence_ms if not _path_is_live(active_path, links) else 0
        total_blackhole_ms += blackhole_ms
        new_path = _shortest_path(nodes, links, source, destination)
        if new_path != event["expected_path"]:
            raise ContractError(
                f"routing replay mismatch at {event['observed_at_ms']} ms: "
                f"expected {event['expected_path']}, got {new_path}"
            )
        active_path = new_path
        event_results.append(
            {
                "observed_at_ms": event["observed_at_ms"],
                "applied_at_ms": event["applied_at_ms"],
                "action": event["action"],
                "link": list(pair),
                "convergence_ms": convergence_ms,
                "transient_blackhole_ms": blackhole_ms,
                "selected_path": new_path,
            }
        )
    return {
        "initial_path": initial_path,
        "events": event_results,
        "event_count": len(event_results),
        "max_convergence_ms": max(result["convergence_ms"] for result in event_results),
        "total_transient_blackhole_ms": total_blackhole_ms,
        "final_path": active_path,
    }


def calibrate_queue_model(dataset: dict[str, Any]) -> dict[str, Any]:
    records = dataset["records"]
    train = [record for record in records if record["split"] == "train"]
    holdout = [record for record in records if record["split"] == "holdout"]
    maximum_arrival = max(record["arrival_rate_pps"] for record in records)

    def prediction(service_rate: float, arrival_rate: float) -> float:
        return 1000.0 / (service_rate - arrival_rate)

    candidates = [maximum_arrival + 1.0 + step / 10.0 for step in range(1000)]
    fitted_rate = min(
        candidates,
        key=lambda rate: sum(
            (prediction(rate, record["arrival_rate_pps"]) - record["observed_mean_delay_ms"]) ** 2
            for record in train
        ),
    )
    train_errors = [
        abs(prediction(fitted_rate, record["arrival_rate_pps"]) - record["observed_mean_delay_ms"])
        for record in train
    ]
    interval_half_width = max(0.5, max(train_errors))
    holdout_rows: list[dict[str, Any]] = []
    absolute_errors: list[float] = []
    percentage_errors: list[float] = []
    covered = 0
    ood_errors: list[float] = []
    for record in holdout:
        predicted = prediction(fitted_rate, record["arrival_rate_pps"])
        error = abs(predicted - record["observed_mean_delay_ms"])
        is_covered = error <= interval_half_width
        covered += int(is_covered)
        absolute_errors.append(error)
        percentage_errors.append(error / record["observed_mean_delay_ms"])
        if record["ood"]:
            ood_errors.append(error)
        holdout_rows.append(
            {
                "arrival_rate_pps": record["arrival_rate_pps"],
                "observed_mean_delay_ms": record["observed_mean_delay_ms"],
                "predicted_mean_delay_ms": _round(predicted),
                "absolute_error_ms": _round(error),
                "inside_train_residual_interval": is_covered,
                "ood": record["ood"],
            }
        )
    return {
        "model": dataset["model"],
        "fitted_service_rate_pps": _round(fitted_rate),
        "train_sample_count": len(train),
        "holdout_sample_count": len(holdout),
        "train_residual_interval_half_width_ms": _round(interval_half_width),
        "holdout_mae_ms": _round(statistics.fmean(absolute_errors)),
        "holdout_mape": _round(statistics.fmean(percentage_errors)),
        "holdout_interval_coverage": _round(covered / len(holdout)),
        "ood_mae_ms": _round(statistics.fmean(ood_errors) if ood_errors else 0.0),
        "holdout_predictions": holdout_rows,
    }


def generate_emulation_plan(request: dict[str, Any]) -> dict[str, Any]:
    """Generate inert argv records. This function cannot and does not execute them."""

    percentage = lambda rate: f"{float(rate) * 100.0:.3f}%"
    netem = [
        "tc",
        "qdisc",
        "replace",
        "dev",
        request["interface"],
        "root",
        "netem",
        "delay",
        f"{float(request['delay_ms']):.3f}ms",
        f"{float(request['jitter_ms']):.3f}ms",
        "loss",
        percentage(request["loss_rate"]),
        "duplicate",
        percentage(request["duplicate_rate"]),
        "reorder",
        percentage(request["reorder_rate"]),
        "rate",
        f"{float(request['bandwidth_mbps']):.3f}mbit",
    ]
    return {
        "schema_version": "1.0",
        "synthetic": True,
        "production_ready": False,
        "execution_allowed": False,
        "generator_executed_commands": False,
        "requires_separate_authorized_privileged_review": True,
        "warning": "Inert teaching plan only; no command was or may be executed by this package.",
        "actions": [
            {"id": "namespace", "argv": ["ip", "netns", "add", request["namespace"]]},
            {
                "id": "veth_pair",
                "argv": [
                    "ip",
                    "link",
                    "add",
                    request["interface"],
                    "type",
                    "veth",
                    "peer",
                    "name",
                    request["peer_interface"],
                ],
            },
            {"id": "impairment", "argv": netem},
        ],
    }
