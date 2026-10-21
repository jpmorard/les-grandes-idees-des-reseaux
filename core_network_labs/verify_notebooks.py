"""Check or execute the three core notebooks in memory, without rewriting files."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NAMES = ("tp_latence_qos.ipynb", "tp_convergence.ipynb", "tp_bgp_rov.ipynb")


def verify(execute: bool = False) -> None:
    for name in NAMES:
        path = ROOT / "notebooks" / name
        notebook = json.loads(path.read_text(encoding="utf-8"))
        if (
            notebook["metadata"].get("book_evidence_scope")
            != "synthetic_no_real_protocol_execution"
        ):
            raise ValueError(f"Missing scope declaration: {name}")
        code = "\n".join(
            "".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"
        )
        tree = ast.parse(code, filename=name)
        if not any(isinstance(node, ast.Assert) for node in ast.walk(tree)):
            raise ValueError(f"Missing executable teaching checks: {name}")
        if execute:
            import nbformat
            from nbclient import NotebookClient

            nb = nbformat.read(path, as_version=4)
            NotebookClient(
                nb,
                timeout=120,
                kernel_name="python3",
                resources={"metadata": {"path": str(ROOT.parent)}},
            ).execute()
        print(
            f"{name}: PASS ({'executed in memory' if execute else 'static contract'})"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    verify(parser.parse_args().execute)


if __name__ == "__main__":
    main()
