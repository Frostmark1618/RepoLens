from __future__ import annotations

import re
from typing import Any


_METADATA_SPECS = (
    {
        "key": "total_files",
        "label": "total files",
        "aliases": (
            ("total", "files"),
            ("repository", "size"),
            ("repo", "size"),
            ("how", "large"),
        ),
    },
    {
        "key": "python_files",
        "label": "Python files",
        "aliases": (
            ("python", "files"),
            ("python", "file"),
            ("py", "files"),
            ("py", "file"),
        ),
    },
    {
        "key": "relevant_file_count",
        "label": "relevant files",
        "aliases": (
            ("relevant", "files"),
            ("relevant", "file"),
        ),
    },
    {
        "key": "production_module_count",
        "label": "production modules",
        "aliases": (
            ("production", "modules"),
            ("production", "module"),
        ),
    },
    {
        "key": "dependency_edge_count",
        "label": "dependency edges",
        "aliases": (
            ("dependency", "edges"),
            ("dependency", "edge"),
            ("dependency", "relationships"),
            ("dependency", "relationship"),
        ),
    },
    {
        "key": "architecture_edge_count",
        "label": "architecture edges",
        "aliases": (
            ("architecture", "edges"),
            ("architecture", "edge"),
        ),
    },
    {
        "key": "risk_signal_count",
        "label": "risk signals",
        "aliases": (
            ("risk", "signals"),
            ("risk", "signal"),
        ),
    },
)


def _tokens(value: str) -> set[str]:
    text = str(value or "").lower()
    return set(re.findall(r"[a-z0-9]+", text))


def _matches_spec(query_tokens: set[str], spec: dict[str, Any]) -> bool:
    for alias in spec["aliases"]:
        alias_tokens = set(alias)
        if alias_tokens.issubset(query_tokens):
            return True
    return False


def build_repository_metadata_evidence(analysis: dict[str, Any]) -> list[dict]:
    """Build authoritative, repository-wide metadata evidence from analysis artifacts."""
    if not isinstance(analysis, dict):
        return []

    metadata = analysis.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    dependency_summary = analysis.get("dependency_graph", {}).get("summary", {})
    if not isinstance(dependency_summary, dict):
        dependency_summary = {}

    architecture = analysis.get("architecture", {})
    if not isinstance(architecture, dict):
        architecture = {}

    architecture_graph = architecture.get("graph_summary", {})
    if not isinstance(architecture_graph, dict):
        architecture_graph = {}

    production_modules = architecture.get("production_modules", [])
    if not isinstance(production_modules, list):
        production_modules = []

    relevant_files = analysis.get("relevant_files", [])
    if not isinstance(relevant_files, list):
        relevant_files = []

    risks = analysis.get("risk_signals", [])
    if not isinstance(risks, list):
        risks = []

    values = {
        "total_files": metadata.get("total_files"),
        "python_files": metadata.get("python_files"),
        "relevant_file_count": len(relevant_files),
        "production_module_count": len(production_modules),
        "dependency_edge_count": dependency_summary.get("total_edges"),
        "architecture_edge_count": architecture_graph.get("edge_count"),
        "risk_signal_count": analysis.get("risks", {}).get("risk_signal_count")
        if isinstance(analysis.get("risks"), dict)
        else len(risks),
    }

    evidence = []
    for spec in _METADATA_SPECS:
        value = values.get(spec["key"])
        if not isinstance(value, int) or value < 0:
            continue
        evidence.append(
            {
                "evidence_type": "repository_metadata",
                "evidence_subtype": "metadata_fact",
                "metadata_key": spec["key"],
                "label": spec["label"],
                "value": value,
                "file": "artifacts/repository_analysis.json",
                "start_line": None,
                "end_line": None,
                "status": "fact",
                "content": (
                    f"{spec['label']}: {value}. "
                    "Authoritative value derived from the repository analysis artifact."
                ),
            }
        )
    return evidence


def retrieve_repository_metadata_evidence(
    query: str,
    analysis: dict[str, Any],
    top_k: int = 5,
) -> list[dict]:
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")
    if not isinstance(analysis, dict):
        raise TypeError("Analysis must be a dictionary.")
    if not isinstance(top_k, int) or top_k <= 0:
        raise ValueError("top_k must be greater than zero.")

    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    evidence = build_repository_metadata_evidence(analysis)
    return [
        item
        for item in evidence
        if _matches_spec(query_tokens, next(
            spec for spec in _METADATA_SPECS
            if spec["key"] == item["metadata_key"]
        ))
    ][:top_k]


def metadata_value_from_evidence(
    claim_or_query: str,
    evidence: list[dict],
) -> dict | None:
    """Return the unique metadata fact relevant to a query/claim."""
    if not isinstance(claim_or_query, str) or not isinstance(evidence, list):
        return None

    tokens = _tokens(claim_or_query)
    matches = []
    for item in evidence:
        if not isinstance(item, dict) or item.get("evidence_type") != "repository_metadata":
            continue
        spec = next(
            (spec for spec in _METADATA_SPECS if spec["key"] == item.get("metadata_key")),
            None,
        )
        if spec and _matches_spec(tokens, spec):
            matches.append(item)

    if len(matches) == 1:
        return matches[0]
    return None
