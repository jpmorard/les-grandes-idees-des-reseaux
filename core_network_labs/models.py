"""Small, inspectable networking models with explicit event and unit conventions."""

from __future__ import annotations

import heapq
import ipaddress
import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Packet:
    packet_id: str
    flow: str
    arrival_us: int
    size_bytes: int
    priority: int = 1


def simulate_queue(
    packets: list[Packet], *, rate_bps: int, waiting_slots: int, policy: str = "fifo"
) -> dict[str, Any]:
    """One non-preemptive server; capacity counts waiting packets, not service.

    Durations are rounded up to integer microseconds. A completion and dispatch
    of already queued work precede arrivals at the same timestamp. Simultaneous
    arrivals are ordered by packet_id. No TCP, headers or propagation is modeled.
    """
    if rate_bps <= 0 or waiting_slots < 0 or policy not in {"fifo", "priority"}:
        raise ValueError(
            "positive rate, nonnegative capacity and known policy required"
        )
    if len({p.packet_id for p in packets}) != len(packets):
        raise ValueError("packet IDs must be unique")
    if any(p.arrival_us < 0 or p.size_bytes <= 0 for p in packets):
        raise ValueError("nonnegative arrivals and positive packet sizes required")
    arrivals = sorted(packets, key=lambda p: (p.arrival_us, p.packet_id))
    waiting: list[tuple[int, Packet]] = []
    current: tuple[Packet, int, int] | None = None
    delivered: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    index = 0

    def begin(packet: Packet, now: int) -> tuple[Packet, int, int]:
        duration = (packet.size_bytes * 8 * 1_000_000 + rate_bps - 1) // rate_bps
        return packet, now, now + duration

    while index < len(arrivals) or current is not None:
        next_arrival = arrivals[index].arrival_us if index < len(arrivals) else math.inf
        next_completion = current[2] if current is not None else math.inf
        now = int(min(next_arrival, next_completion))
        if current is not None and current[2] == now:
            packet, started, finished = current
            delivered.append(
                {
                    "packet_id": packet.packet_id,
                    "flow": packet.flow,
                    "arrival_us": packet.arrival_us,
                    "start_us": started,
                    "finish_us": finished,
                    "waiting_us": started - packet.arrival_us,
                    "sojourn_us": finished - packet.arrival_us,
                    "size_bytes": packet.size_bytes,
                }
            )
            current = None
            if waiting:
                selected = min(
                    range(len(waiting)),
                    key=lambda i: (
                        waiting[i][1].priority if policy == "priority" else 0,
                        waiting[i][0],
                    ),
                )
                _, packet = waiting.pop(selected)
                current = begin(packet, now)
        while index < len(arrivals) and arrivals[index].arrival_us == now:
            packet = arrivals[index]
            if current is None:
                current = begin(packet, now)
            elif len(waiting) < waiting_slots:
                waiting.append((index, packet))
            else:
                dropped.append(
                    {
                        "packet_id": packet.packet_id,
                        "flow": packet.flow,
                        "arrival_us": now,
                        "reason": "waiting_buffer_full",
                    }
                )
            index += 1

    summaries = []
    for flow in sorted({p.flow for p in packets}):
        sent = [p for p in delivered if p["flow"] == flow]
        delays = sorted(p["sojourn_us"] / 1000 for p in sent)
        offered = sum(p.flow == flow for p in packets)
        summaries.append(
            {
                "flow": flow,
                "offered": offered,
                "delivered": len(sent),
                "dropped": sum(p["flow"] == flow for p in dropped),
                "mean_sojourn_ms": round(sum(delays) / len(delays), 6)
                if delays
                else None,
                "p95_sojourn_ms": delays[math.ceil(0.95 * len(delays)) - 1]
                if delays
                else None,
            }
        )
    return {
        "policy": policy,
        "rate_bps": rate_bps,
        "waiting_slots": waiting_slots,
        "flows": summaries,
        "delivered": delivered,
        "dropped": dropped,
    }


def forwarding_table(
    edges: list[tuple[str, str, int]], destination: str
) -> dict[str, str | None]:
    """Shortest paths on an undirected positive-cost graph, with lexical ties."""
    graph: dict[str, dict[str, int]] = {destination: {}}
    for left, right, cost in edges:
        if cost <= 0 or left == right:
            raise ValueError("positive costs and distinct endpoints required")
        graph.setdefault(left, {})[right] = cost
        graph.setdefault(right, {})[left] = cost
    table: dict[str, str | None] = {}
    for source in sorted(graph):
        queue: list[tuple[int, tuple[str, ...]]] = [(0, (source,))]
        visited: set[str] = set()
        table[source] = None
        while queue:
            cost, path = heapq.heappop(queue)
            node = path[-1]
            if node in visited:
                continue
            visited.add(node)
            if node == destination:
                table[source] = path[1] if len(path) > 1 else None
                break
            for neighbor, weight in sorted(graph[node].items()):
                if neighbor not in visited:
                    heapq.heappush(queue, (cost + weight, (*path, neighbor)))
    return table


def trace_forwarding(
    table: dict[str, str | None],
    edges: list[tuple[str, str, int]],
    source: str,
    destination: str,
) -> dict[str, Any]:
    live = {frozenset((left, right)) for left, right, _ in edges}
    path = [source]
    while path[-1] != destination:
        next_hop = table.get(path[-1])
        if next_hop is None:
            return {"status": "no_route", "path": path}
        if frozenset((path[-1], next_hop)) not in live:
            return {"status": "failed_link", "path": [*path, next_hop]}
        if next_hop in path:
            return {"status": "forwarding_loop", "path": [*path, next_hop]}
        path.append(next_hop)
    return {"status": "delivered", "path": path}


def convergence_case(
    edges: list[tuple[str, str, int]],
    *,
    failed_link: tuple[str, str],
    updates_ms: dict[str, int],
    probes_ms: list[int],
    source: str = "A",
    destination: str = "C",
) -> list[dict[str, Any]]:
    """Failure occurs at t=0; each node installs its final FIB at its stated time."""
    if any(time < 0 for time in updates_ms.values()):
        raise ValueError("post-failure FIB updates must be nonnegative")
    remaining = [edge for edge in edges if set(edge[:2]) != set(failed_link)]
    if len(remaining) != len(edges) - 1:
        raise ValueError("exactly one existing link must fail")
    old = forwarding_table(edges, destination)
    final = forwarding_table(remaining, destination)
    rows = []
    for now in probes_ms:
        fib = dict(old)
        if now >= 0:
            for node, installed_at in updates_ms.items():
                if installed_at <= now:
                    fib[node] = final.get(node)
        trace = trace_forwarding(
            fib, edges if now < 0 else remaining, source, destination
        )
        rows.append({"time_ms": now, "fib": fib, **trace})
    return rows


def classify_origin(
    prefix: str,
    origin_as: int,
    vrps: list[dict[str, Any]],
    *,
    cache_available: bool = True,
) -> str:
    """Validation state only. Unavailable is explicitly distinct from NotFound."""
    network = ipaddress.ip_network(prefix)
    if origin_as <= 0:
        raise ValueError("this teaching route model requires a positive origin ASN")
    if not cache_available:
        return "Unavailable"
    covering = []
    for vrp in vrps:
        authorized = ipaddress.ip_network(vrp["prefix"])
        maximum = vrp["max_length"]
        if not authorized.prefixlen <= maximum <= authorized.max_prefixlen:
            raise ValueError("max_length outside the authorized address-family range")
        if authorized.version == network.version and network.subnet_of(authorized):
            covering.append(vrp)
    if not covering:
        return "NotFound"
    if any(
        v["origin_as"] == origin_as and network.prefixlen <= v["max_length"]
        for v in covering
    ):
        return "Valid"
    return "Invalid"


def apply_origin_policy(
    state: str, *, reject_invalid: bool, unavailable_policy: str = "hold"
) -> str:
    """A local example policy, not a universal operational recommendation."""
    if state not in {"Valid", "Invalid", "NotFound", "Unavailable"}:
        raise ValueError("unknown origin-validation state")
    if unavailable_policy not in {"hold", "accept"}:
        raise ValueError("unknown cache-unavailable policy")
    if state == "Unavailable":
        return unavailable_policy
    return "reject" if reject_invalid and state == "Invalid" else "accept"
