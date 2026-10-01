"""Fail-closed structural contracts for the pedagogical network notebooks."""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any

from .contracts import ContractError


ROOT = Path(__file__).resolve().parent
NOTEBOOK_ROOT = ROOT / "notebooks"
NOTEBOOK_SPECS = {
    "mini_fanet_reroutage.ipynb": {
        "audience": "student-technician-beginner",
        "duration_minutes": 45,
        "markdown": ("FANET", "public cible", "limites", "synthétique"),
        "code": ("SEED", "assert", "_repr_html_"),
        "rich_marker": "<svg",
    },
    "tp_voix_flowsynth.ipynb": {
        "audience": "student-packet-voip-beginner",
        "duration_minutes": 60,
        "markdown": ("FlowSynth", "public cible", "limites", "voix"),
        "code": ("SEED", "assert", "_repr_html_"),
        "rich_marker": "<audio",
    },
    "tp_detective_reseau.ipynb": {
        "audience": "student-technician-netops-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "prédire",
            "mesurer",
            "falsifier",
            "diagnostiquer",
            "transférer",
            "capacité",
            "MTU",
            "DF",
            "bufferbloat",
            "pertes radio",
            "contre-expérience",
            "rapport d'incident",
            "limites",
        ),
        "code": ("SEED", "assert", "_repr_html_", "incident_report"),
        "rich_marker": "<svg",
    },
    "tp_capture_replay.ipynb": {
        "audience": "student-technician-cyber-netops-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "PCAP",
            "capturer n'autorise pas à rejouer",
            "autorisation",
            "anonymiser",
            "horodatage",
            "fidélité",
            "plan inerte",
            "limites",
        ),
        "code": ("SEED", "assert", "_repr_html_", "pcap_bytes", "replay_plan"),
        "rich_marker": "<svg",
    },
    "tp_discovery_reseau.ipynb": {
        "audience": "student-technician-netops-cyber-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "passif",
            "actif",
            "non découvert",
            "absent",
            "confiance",
            "réconciliation",
            "angle mort",
            "autorisation",
            "limites",
        ),
        "code": ("SEED", "assert", "_repr_html_", "discovery_report", "probe_plan"),
        "rich_marker": "<svg",
    },
    "tp_dns_resolution.ipynb": {
        "audience": "student-technician-netops-cyber-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "résolveur récursif",
            "autoritatif",
            "délégation",
            "TTL",
            "cache négatif",
            "NXDOMAIN",
            "NODATA",
            "SERVFAIL",
            "limites",
        ),
        "code": ("SEED", "assert", "_repr_html_", "dns_trace", "incident_report"),
        "rich_marker": "<svg",
    },
    "tp_dhcp_bail.ipynb": {
        "audience": "student-technician-netops-cyber-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "DORA",
            "Discover",
            "Offer",
            "Request",
            "ACK",
            "bail",
            "T1",
            "T2",
            "relais DHCP",
            "pool épuisé",
            "autorisation",
            "limites",
        ),
        "code": ("SEED", "assert", "_repr_html_", "dhcp_trace", "incident_report"),
        "rich_marker": "<svg",
    },
    "tp_sous_reseau_passerelle.ipynb": {
        "audience": "student-technician-netops-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "sous-réseau",
            "255.255.255.0",
            "AND bit à bit",
            "adresse réseau",
            "broadcast",
            "/31",
            "/32",
            "préfixe le plus long",
            "passerelle par défaut",
            "prochain saut",
            "ARP",
            "Neighbor Discovery",
            "IPv6",
            "NAT",
            "DNS",
            "pare-feu",
            "limites",
        ),
        "code": (
            "SEED",
            "assert",
            "_repr_html_",
            "routing_cases",
            "incident_report",
            "execution_allowed",
        ),
        "rich_marker": "<svg",
    },
    "tp_modulation_symboles.ipynb": {
        "audience": "student-technician-radio-netops-beginner",
        "duration_minutes": 60,
        "markdown": (
            "public cible",
            "ordre de modulation",
            "constellation",
            "bits par symbole",
            "nombre de symboles",
            "baud",
            "bit/s",
            "bourrage",
            "Gray",
            "OFDM",
            "élément de ressource",
            "pilote",
            "préfixe cyclique",
            "échantillon I/Q",
            "Es/N0",
            "Eb/N0",
            "MCS",
            "EVM",
            "BLER",
            "limites",
        ),
        "code": (
            "SEED",
            "assert",
            "_repr_html_",
            "modulation_report",
            "ofdm_grid",
            "incident_report",
        ),
        "rich_marker": "<svg",
    },
}
NOTEBOOK_PATHS = tuple(NOTEBOOK_ROOT / name for name in NOTEBOOK_SPECS)

FORBIDDEN_IMPORTS = {
    "ftplib",
    "http",
    "os",
    "paramiko",
    "requests",
    "scapy",
    "socket",
    "subprocess",
    "telnetlib",
    "urllib",
}
FORBIDDEN_CALLS = {
    "__import__",
    "compile",
    "connect",
    "eval",
    "exec",
    "makedirs",
    "mkdir",
    "open",
    "popen",
    "remove",
    "rmdir",
    "rmtree",
    "run",
    "send",
    "sendto",
    "system",
    "touch",
    "unlink",
    "urlopen",
    "write_bytes",
    "write_text",
}
STDLIB_IMPORTS = frozenset(sys.stdlib_module_names) | {"__future__"}
REQUIRED_METADATA = {
    "artifact_class": "synthetic-pedagogical",
    "benchmark_family": None,
    "network_access": False,
    "privileged_actions": False,
    "production_evidence": False,
    "requires_network": False,
    "requires_privilege": False,
    "synthetic": True,
}


def _cell_source(cell: dict[str, Any], path: Path, number: int) -> str:
    source = cell.get("source", "")
    if isinstance(source, str):
        return source
    if isinstance(source, list) and all(isinstance(line, str) for line in source):
        return "".join(source)
    raise ContractError(f"{path.name}: cell {number} has an invalid source")


def _check_code(source: str, path: Path, number: int) -> None:
    for line in source.splitlines():
        if line.lstrip().startswith(("!", "%")):
            raise ContractError(f"{path.name}: cell {number} contains a shell or magic escape")
    try:
        tree = ast.parse(source, filename=f"{path.name}:cell-{number}")
    except SyntaxError as exc:
        raise ContractError(f"{path.name}: cell {number} is not valid Python: {exc}") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".", 1)[0] for alias in node.names}
            blocked = roots & FORBIDDEN_IMPORTS
            if blocked:
                raise ContractError(f"{path.name}: cell {number} imports {sorted(blocked)}")
            external = roots - STDLIB_IMPORTS
            if external:
                raise ContractError(
                    f"{path.name}: cell {number} imports non-stdlib modules {sorted(external)}"
                )
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in FORBIDDEN_IMPORTS:
                raise ContractError(f"{path.name}: cell {number} imports {root}")
            if root and root not in STDLIB_IMPORTS:
                raise ContractError(
                    f"{path.name}: cell {number} imports non-stdlib module {root}"
                )
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                name = node.func.attr
            else:
                name = ""
            if name in FORBIDDEN_CALLS:
                if (
                    isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and (node.func.value.id, name) in {("wave", "open"), ("re", "compile")}
                ):
                    continue
                raise ContractError(f"{path.name}: cell {number} calls forbidden function {name}")


def validate_notebook(path: Path) -> dict[str, Any]:
    """Validate one notebook without executing any cell."""

    try:
        notebook = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot parse notebook {path.name}: {exc}") from exc
    if not isinstance(notebook, dict) or notebook.get("nbformat") != 4:
        raise ContractError(f"{path.name}: nbformat 4 is required")

    metadata = notebook.get("metadata")
    if not isinstance(metadata, dict):
        raise ContractError(f"{path.name}: notebook metadata must be an object")
    agilab = metadata.get("agilab")
    if not isinstance(agilab, dict):
        raise ContractError(f"{path.name}: metadata.agilab is required")
    for key, expected in REQUIRED_METADATA.items():
        if agilab.get(key) != expected:
            raise ContractError(f"{path.name}: metadata.agilab.{key} must be {expected!r}")

    cells = notebook.get("cells")
    if not isinstance(cells, list) or len(cells) < 6:
        raise ContractError(f"{path.name}: at least six teaching cells are required")
    markdown_parts: list[str] = []
    code_parts: list[str] = []
    code_count = 0
    cell_ids: set[str] = set()
    for number, cell in enumerate(cells, start=1):
        if not isinstance(cell, dict):
            raise ContractError(f"{path.name}: cell {number} must be an object")
        cell_id = cell.get("id")
        if (
            not isinstance(cell_id, str)
            or not re.fullmatch(r"[a-z0-9-]{1,64}", cell_id)
            or cell_id in cell_ids
        ):
            raise ContractError(f"{path.name}: cell {number} needs a stable unique id")
        cell_ids.add(cell_id)
        source = _cell_source(cell, path, number)
        if cell.get("cell_type") == "markdown":
            markdown_parts.append(source)
        elif cell.get("cell_type") == "code":
            code_count += 1
            code_parts.append(source)
            if cell.get("execution_count") is not None or cell.get("outputs") not in (None, []):
                raise ContractError(f"{path.name}: committed code cells must have clean outputs")
            _check_code(source, path, number)
        else:
            raise ContractError(f"{path.name}: unsupported cell type in cell {number}")
    if code_count < 3:
        raise ContractError(f"{path.name}: at least three executable cells are required")

    spec = NOTEBOOK_SPECS.get(path.name)
    if spec is None:
        raise ContractError(f"unexpected notebook: {path.name}")
    for key in ("audience", "duration_minutes"):
        if agilab.get(key) != spec[key]:
            raise ContractError(f"{path.name}: metadata.agilab.{key} must be {spec[key]!r}")
    markdown = "\n".join(markdown_parts).casefold()
    code = "\n".join(code_parts)
    for phrase in spec["markdown"]:
        if str(phrase).casefold() not in markdown:
            raise ContractError(f"{path.name}: missing teaching phrase {phrase!r}")
    for phrase in spec["code"]:
        if str(phrase) not in code:
            raise ContractError(f"{path.name}: missing executable contract {phrase!r}")
    return notebook


def verify_notebooks() -> None:
    actual = {path.name for path in NOTEBOOK_ROOT.glob("*.ipynb")}
    expected = set(NOTEBOOK_SPECS)
    if actual != expected:
        raise ContractError(
            f"notebook inventory mismatch: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}"
        )
    for path in NOTEBOOK_PATHS:
        validate_notebook(path)
