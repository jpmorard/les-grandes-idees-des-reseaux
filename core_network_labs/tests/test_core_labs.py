"""Counterexamples and conservation checks for the core teaching models."""

from __future__ import annotations

import unittest
import tempfile
from pathlib import Path

from core_network_labs.models import (
    Packet,
    apply_origin_policy,
    classify_origin,
    convergence_case,
    simulate_queue,
)
from core_network_labs.run_labs import (
    build_manifest,
    build_results,
    canonical_json,
    check_artifacts,
)


class CoreNetworkTests(unittest.TestCase):
    def test_retained_evidence_rejects_a_modified_result(self):
        artifacts = build_results()
        with tempfile.TemporaryDirectory(prefix="book-core-evidence-test-") as temp:
            root = Path(temp)
            (root / "results").mkdir()
            for name, result in artifacts.items():
                (root / "results" / name).write_text(
                    canonical_json(result), encoding="utf-8"
                )
            (root / "manifest.json").write_text(
                canonical_json(build_manifest(artifacts)), encoding="utf-8"
            )
            check_artifacts(root)
            (root / "results" / "bgp_rov.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "bgp_rov.json"):
                check_artifacts(root)

    def test_one_packet_has_serialization_not_queue_delay(self):
        result = simulate_queue(
            [Packet("p", "voice", 0, 1000)], rate_bps=1_000_000, waiting_slots=0
        )
        self.assertEqual(result["delivered"][0]["waiting_us"], 0)
        self.assertEqual(result["delivered"][0]["sojourn_us"], 8000)

    def test_buffer_counts_waiters_not_packet_in_service(self):
        packets = [Packet(str(i), "bulk", 0, 1000) for i in range(3)]
        result = simulate_queue(packets, rate_bps=1_000_000, waiting_slots=1)
        self.assertEqual([p["finish_us"] for p in result["delivered"]], [8000, 16000])
        self.assertEqual([p["packet_id"] for p in result["dropped"]], ["2"])

    def test_priority_is_nonpreemptive(self):
        packets = [
            Packet("a", "bulk", 0, 1000, 1),
            Packet("b", "bulk", 1, 1000, 1),
            Packet("c", "voice", 2, 100, 0),
        ]
        result = simulate_queue(
            packets, rate_bps=1_000_000, waiting_slots=2, policy="priority"
        )
        self.assertEqual([p["packet_id"] for p in result["delivered"]], ["a", "c", "b"])
        self.assertEqual(result["delivered"][1]["start_us"], 8000)

    def test_completion_precedes_same_time_arrival(self):
        result = simulate_queue(
            [Packet("a", "bulk", 0, 1000), Packet("b", "bulk", 8000, 1000)],
            rate_bps=1_000_000,
            waiting_slots=0,
        )
        self.assertEqual(len(result["delivered"]), 2)

    def test_loss_and_delay_tradeoff_is_observed(self):
        cases = build_results()["latency_qos.json"]["cases"]
        for case in cases.values():
            for flow in case["flows"]:
                self.assertEqual(flow["offered"], flow["delivered"] + flow["dropped"])
        small = {f["flow"]: f for f in cases["fifo_small"]["flows"]}
        large = {f["flow"]: f for f in cases["fifo_large"]["flows"]}
        priority = {f["flow"]: f for f in cases["priority_large"]["flows"]}
        self.assertLess(
            small["voice"]["p95_sojourn_ms"], large["voice"]["p95_sojourn_ms"]
        )
        self.assertLess(
            priority["voice"]["p95_sojourn_ms"], large["voice"]["p95_sojourn_ms"]
        )
        self.assertGreater(
            len(cases["fifo_small"]["dropped"]), len(cases["fifo_large"]["dropped"])
        )

    def test_fib_installation_order_changes_transient_loop(self):
        result = build_results()["convergence.json"]["cases"]
        unordered = {r["time_ms"]: r for r in result["unordered"]}
        self.assertEqual(unordered[-1]["path"], ["A", "B", "C"])
        self.assertEqual(unordered[0]["status"], "failed_link")
        self.assertEqual(unordered[5]["path"], ["A", "B", "A"])
        self.assertEqual(unordered[5]["status"], "forwarding_loop")
        self.assertEqual(unordered[30]["path"], ["A", "C"])
        self.assertNotIn("forwarding_loop", [r["status"] for r in result["ordered"]])

    def test_missing_failure_target_is_rejected(self):
        with self.assertRaises(ValueError):
            convergence_case(
                [("A", "C", 3)],
                failed_link=("B", "C"),
                updates_ms={"A": 5},
                probes_ms=[5],
            )

    def test_validation_does_not_imply_policy(self):
        routes = build_results()["bgp_rov.json"]["routes"]
        self.assertEqual(
            [r["validation_state"] for r in routes],
            ["Valid", "Invalid", "Invalid", "NotFound"],
        )
        self.assertTrue(all(r["classification_only"] == "accept" for r in routes))
        self.assertEqual(
            [r["reject_invalid_policy"] for r in routes],
            ["accept", "reject", "reject", "accept"],
        )

    def test_any_authorizing_vrp_makes_route_valid(self):
        vrps = [
            {"prefix": "203.0.113.0/24", "max_length": 24, "origin_as": 64501},
            {"prefix": "203.0.113.0/24", "max_length": 25, "origin_as": 64500},
        ]
        self.assertEqual(classify_origin("203.0.113.0/25", 64500, vrps), "Valid")

    def test_ipv6_and_cache_failure_are_distinct(self):
        vrps = [{"prefix": "2001:db8::/32", "max_length": 48, "origin_as": 64500}]
        self.assertEqual(classify_origin("2001:db8:1::/48", 64500, vrps), "Valid")
        self.assertEqual(classify_origin("203.0.113.0/24", 64500, vrps), "NotFound")
        state = classify_origin("2001:db8:1::/48", 64500, vrps, cache_available=False)
        self.assertEqual(state, "Unavailable")
        self.assertEqual(apply_origin_policy(state, reject_invalid=True), "hold")

    def test_invalid_inputs_do_not_create_silent_examples(self):
        with self.assertRaises(ValueError):
            simulate_queue([], rate_bps=0, waiting_slots=2)
        with self.assertRaises(ValueError):
            classify_origin(
                "203.0.113.0/24",
                64500,
                [{"prefix": "203.0.113.0/24", "max_length": 33, "origin_as": 64500}],
            )


if __name__ == "__main__":
    unittest.main()
