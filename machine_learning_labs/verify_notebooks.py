"""Validate and optionally execute the ML/RL notebooks without rewriting them."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
NOTEBOOK_ROOT = ROOT / "notebooks"
NOTEBOOK_SPECS = {
    "svd_radio.ipynb": {
        "markdown": (
            "SVD",
            "ACP",
            "RPCA",
            "MIMO",
            "synthétiques",
            "PCP exacte",
            "identifiabilité",
            "pas un détecteur calibré",
        ),
        "code": (
            "np.linalg.svd",
            "robust_pca",
            "capacity_from_modes",
            "naive_support_false_alarm_rate",
            "assert",
        ),
    },
    "tp_ml_classification_rare.ipynb": {
        "markdown": ("validation", "seuil", "test scellé", "fuite"),
        "code": ("fit_score_model", "select_threshold", "run_experiment", "assert"),
    },
    "tp_rl_retour_q_td.ipynb": {
        "markdown": ("retour", "avantage", "terminaison", "troncature"),
        "code": ("discounted_return", "td_error", "assert"),
    },
    "tp_rl_dqn_relais.ipynb": {
        "markdown": ("DQN", "rejeu", "réseau cible", "contraintes"),
        "code": ("RelayQueueEnv", "train_dqn", "evaluate_policy", "assert"),
    },
}
FORBIDDEN_IMPORT_ROOTS = {
    "ftplib",
    "http",
    "os",
    "paramiko",
    "requests",
    "socket",
    "subprocess",
    "urllib",
}
FORBIDDEN_CELL_PREFIXES = ("!", "%pip", "%conda")


def _audit_code(path: Path, code: str) -> None:
    for line in code.splitlines():
        if line.lstrip().startswith(FORBIDDEN_CELL_PREFIXES):
            raise AssertionError(f"{path.name}: forbidden notebook command {line!r}")
    tree = ast.parse(code, filename=path.name)
    for node in ast.walk(tree):
        imported: list[str] = []
        if isinstance(node, ast.Import):
            imported = [alias.name.split(".", 1)[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported = [node.module.split(".", 1)[0]]
        forbidden = sorted(set(imported) & FORBIDDEN_IMPORT_ROOTS)
        if forbidden:
            raise AssertionError(f"{path.name}: forbidden imports {forbidden}")


def load_notebook(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("nbformat") != 4 or not isinstance(data.get("cells"), list):
        raise AssertionError(f"{path.name}: invalid notebook structure")
    return data


def validate_notebook(path: Path) -> dict[str, int | str]:
    specification = NOTEBOOK_SPECS[path.name]
    notebook = load_notebook(path)
    cell_ids = [cell.get("id") for cell in notebook["cells"]]
    if any(not isinstance(cell_id, str) or not cell_id for cell_id in cell_ids):
        raise AssertionError(f"{path.name}: every cell must have a non-empty id")
    if len(set(cell_ids)) != len(cell_ids):
        raise AssertionError(f"{path.name}: cell ids must be unique")
    markdown = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "markdown"
    )
    code = "\n".join(
        "".join(cell.get("source", []))
        for cell in notebook["cells"]
        if cell.get("cell_type") == "code"
    )
    lowered_markdown = markdown.casefold()
    for marker in specification["markdown"]:
        if marker.casefold() not in lowered_markdown:
            raise AssertionError(f"{path.name}: missing markdown marker {marker!r}")
    for marker in specification["code"]:
        if marker not in code:
            raise AssertionError(f"{path.name}: missing code marker {marker!r}")
    _audit_code(path, code)
    code_cells = [cell for cell in notebook["cells"] if cell.get("cell_type") == "code"]
    for cell in code_cells:
        if cell.get("execution_count") is not None or cell.get("outputs"):
            raise AssertionError(f"{path.name}: committed outputs must stay empty")
    return {
        "notebook": path.name,
        "cells": len(notebook["cells"]),
        "code_cells": len(code_cells),
    }


def execute_notebook(path: Path) -> None:
    import nbformat
    from nbclient import NotebookClient

    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=900,
        kernel_name="python3",
        resources={"metadata": {"path": str(NOTEBOOK_ROOT)}},
    )
    client.execute()


def verify_all(*, execute: bool = False) -> list[dict[str, int | str]]:
    results: list[dict[str, int | str]] = []
    for name in NOTEBOOK_SPECS:
        path = NOTEBOOK_ROOT / name
        if not path.is_file():
            raise AssertionError(f"missing notebook: {path}")
        results.append(validate_notebook(path))
        if execute:
            execute_notebook(path)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    for result in verify_all(execute=args.execute):
        print(result)


if __name__ == "__main__":
    main()
