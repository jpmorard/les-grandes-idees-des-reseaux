from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from network_simulation_labs.contracts import (
    ContractError,
    load_json,
    safe_relative_path,
    validate_emulation_request,
    validate_scenario,
)
from network_simulation_labs.run_labs import DATASETS, build_artifacts
from network_simulation_labs.notebook_contracts import NOTEBOOK_PATHS, validate_notebook
from network_simulation_labs.simulator import simulate_queue
from network_simulation_labs.verify import verify_all


class DeterminismTests(unittest.TestCase):
    def test_same_seed_is_byte_level_repeatable(self) -> None:
        scenario = validate_scenario(load_json(DATASETS, "scenario.json"))
        first = simulate_queue(scenario["queue"], 43)
        second = simulate_queue(scenario["queue"], 43)
        self.assertEqual(first, second)

    def test_suite_has_multiple_seeds_uncertainty_and_negative_findings(self) -> None:
        result, plan = build_artifacts()
        self.assertGreaterEqual(len(result["seeds"]), 3)
        self.assertGreater(result["queue"]["summary"]["p95_response_ms"]["sample_stddev"], 0.0)
        self.assertGreater(result["packet_impairments"]["summary"]["observed_loss_rate"]["sample_stddev"], 0.0)
        self.assertGreaterEqual(len(result["negative_findings"]), 4)
        self.assertFalse(result["production_evidence"])
        self.assertFalse(plan["execution_allowed"])
        self.assertFalse(plan["generator_executed_commands"])

    def test_routing_and_calibration_expose_failures(self) -> None:
        result, _plan = build_artifacts()
        self.assertEqual(result["routing_replay"]["total_transient_blackhole_ms"], 45)
        self.assertLess(result["calibration"]["holdout_interval_coverage"], 0.95)
        self.assertGreater(result["calibration"]["ood_mae_ms"], 0.0)


class FailClosedContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_request = load_json(DATASETS, "emulation_request.json")

    def test_rejects_execute_flag_even_when_false(self) -> None:
        request = copy.deepcopy(self.valid_request)
        request["execute"] = False
        with self.assertRaises(ContractError):
            validate_emulation_request(request)

    def test_rejects_shell_metacharacters(self) -> None:
        for malicious in ("simlab-ok;id", "simlab-$(id)", "simlab-ok|sh"):
            request = copy.deepcopy(self.valid_request)
            request["namespace"] = malicious
            with self.subTest(malicious=malicious), self.assertRaises(ContractError):
                validate_emulation_request(request)

    def test_rejects_unknown_and_unsafe_interface(self) -> None:
        request = copy.deepcopy(self.valid_request)
        request["interface"] = "../../eth0"
        with self.assertRaises(ContractError):
            validate_emulation_request(request)

    def test_rejects_absolute_and_traversal_paths(self) -> None:
        with self.assertRaises(ContractError):
            safe_relative_path(DATASETS, "../README.md")
        with self.assertRaises(ContractError):
            safe_relative_path(DATASETS, "/etc/passwd")

    def test_rejects_malformed_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "bad.json").write_text("{not-json", encoding="utf-8")
            with self.assertRaises(ContractError):
                load_json(root, "bad.json")

    def test_rejects_unstable_baseline_queue(self) -> None:
        scenario = load_json(DATASETS, "scenario.json")
        scenario["queue"]["arrival_rate_pps"] = scenario["queue"]["service_rate_pps"]
        with self.assertRaises(ContractError):
            validate_scenario(scenario)


class ReleaseArtifactTests(unittest.TestCase):
    def test_notebooks_have_fail_closed_pedagogical_contracts(self) -> None:
        self.assertEqual(len(NOTEBOOK_PATHS), 9)
        for path in NOTEBOOK_PATHS:
            notebook = validate_notebook(path)
            self.assertFalse(notebook["metadata"]["agilab"]["network_access"])
            self.assertFalse(notebook["metadata"]["agilab"]["production_evidence"])

    def test_notebooks_reject_hidden_non_stdlib_dependencies(self) -> None:
        source_path = NOTEBOOK_PATHS[0]
        notebook = json.loads(source_path.read_text(encoding="utf-8"))
        code_cell = next(cell for cell in notebook["cells"] if cell["cell_type"] == "code")
        original = code_cell["source"]
        if isinstance(original, list):
            code_cell["source"] = ["import numpy\n", *original]
        else:
            code_cell["source"] = "import numpy\n" + original
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / source_path.name
            candidate.write_text(json.dumps(notebook), encoding="utf-8")
            with self.assertRaisesRegex(ContractError, "non-stdlib"):
                validate_notebook(candidate)

    def test_full_verifier(self) -> None:
        verify_all()


if __name__ == "__main__":
    unittest.main()
