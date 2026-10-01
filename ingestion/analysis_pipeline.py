import json
from datetime import datetime
from pathlib import Path


from ingestion.drift_analyzer import (
    analyze_snapshot_drift,
)

from ingestion.snapshot_loader import (
    load_architecture_snapshot,
    find_snapshot_pair,
)

from ingestion.architecture_builder import build_architecture_modules
from ingestion.architecture_graph import (
    build_architecture_graph,
    summarize_architecture_graph,
)

from ingestion.architecture_layers import (
    calculate_layer_percentages,
    classify_repository_layers,
    summarize_architecture_layers,
)

from ingestion.code_parser import parse_repository

from ingestion.dependency_graph import (
    build_dependency_edges,
    summarize_dependencies,
)

from ingestion.file_filter import collect_files

from ingestion.chunk_builder import (
    build_repository_chunks,
    save_repository_chunks,
)

from ingestion.repo_metadata import collect_repository_metadata
from ingestion.repo_tree import build_file_tree

from ingestion.risk_analyzer import analyze_architecture_risks

from ingestion.circular_dependency_analyzer import (
    detect_circular_dependencies,
)

from ingestion.layer_violation_analyzer import (
    detect_layer_violations,
)

from ingestion.testing_risk_analyzer import (
    detect_untested_production_modules,
)

from llm.risk_report import build_risk_report

from llm.risk_report_serializer import (
    serialize_risk_report,
)


def normalize_risk_signal(
    risk_signal: dict,
) -> dict:
    """
    Normalize every risk signal into a
    consistent minimum schema.
    """

    normalized = dict(risk_signal)

    normalized.setdefault(
        "category",
        "unknown",
    )

    normalized.setdefault(
        "signal",
        "unknown_risk",
    )

    normalized.setdefault(
        "severity",
        "medium",
    )

    normalized.setdefault(
        "status",
        "possible_risk",
    )

    normalized.setdefault(
        "evidence",
        {},
    )

    return normalized


def analyze_repository(
    repository_path: str,
) -> dict:
    """
    Run the complete deterministic repository
    analysis pipeline.
    """

    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: "
            f"{repository_path}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: "
            f"{repository_path}"
        )

    # Repository metadata
    metadata = collect_repository_metadata(
        repository_path
    )

    # Relevant files
    relevant_files = collect_files(
        repository_path
    )

    # Repository file tree
    file_tree = build_file_tree(
        repository_path
    )

    # Python code structure
    python_structure = parse_repository(
        repository_path
    )

    # Dependency analysis
    dependency_edges = build_dependency_edges(
        repository_path
    )

    dependency_summary = summarize_dependencies(
        dependency_edges
    )

    # Architecture modules
    architecture_modules = build_architecture_modules(
        repository_path,
        dependency_edges,
    )

    # Architecture layers
    architecture_layers = classify_repository_layers(
        repository_path
    )

    architecture_layer_summary = (
        summarize_architecture_layers(
            architecture_layers
        )
    )

    architecture_layer_percentages = (
        calculate_layer_percentages(
            architecture_layer_summary
        )
    )

    # Architecture graph
    architecture_graph = build_architecture_graph(
        architecture_modules
    )

    architecture_graph_summary = (
        summarize_architecture_graph(
            architecture_graph
        )
    )

    # Deterministic architecture risk signals
    architecture_risks = analyze_architecture_risks(
        architecture_modules
    )

    # Deterministic circular dependency risk signals
    circular_dependency_risks = (
        detect_circular_dependencies(
            dependency_edges
        )
    )

    architecture_risks["risk_signals"].extend(
        circular_dependency_risks
    )

    # Layer violation risk signals
    layer_violation_risks = detect_layer_violations(
        dependency_edges,
        architecture_layers,
    )

    architecture_risks["risk_signals"].extend(
        layer_violation_risks
    )

    # Testing risk signals
    production_files = [
        module["file"]
        for module in architecture_modules
    ]

    test_files = [
        item["file"]
        for item in architecture_layers
        if item.get("layer") == "test"
    ]

    testing_risks = detect_untested_production_modules(
        production_files,
        test_files,
    )

    architecture_risks["risk_signals"].extend(
        testing_risks
    )

    # Architecture drift risk signals
    baseline_snapshot_path, current_snapshot_path = (
        find_snapshot_pair(
            "artifacts/architecture_snapshots"
        )
    )

    if (
        baseline_snapshot_path is not None
        and current_snapshot_path is not None
    ):
        baseline_snapshot = load_architecture_snapshot(
            baseline_snapshot_path
        )

        current_snapshot = load_architecture_snapshot(
            current_snapshot_path
        )

        drift = analyze_snapshot_drift(
            baseline_snapshot,
            current_snapshot,
        )

        for removed_module in drift[
            "module_drift"
        ]["removed_modules"]:
            architecture_risks["risk_signals"].append(
                {
                    "category": "architecture",
                    "signal": "architecture_drift",
                    "severity": "medium",
                    "status": "possible_risk",
                    "drift_type": "removed_module",
                    "file": removed_module,
                    "evidence": {
                        "file": removed_module,
                        "drift_type": "removed_module",
                    },
                }
            )

    # Normalize every risk signal after
    # all risk analyzers have contributed.
    architecture_risks["risk_signals"] = [
        normalize_risk_signal(risk)
        for risk in architecture_risks["risk_signals"]
    ]

    architecture_risks["risk_signal_count"] = (
        len(
            architecture_risks["risk_signals"]
        )
    )

    # Unified evidence-backed risk intelligence
    risk_report = build_risk_report(
        architecture_risks["risk_signals"]
    )

    risk_intelligence = serialize_risk_report(
        risk_report
    )

    analysis = {
        "metadata": metadata,
        "relevant_files": [
            str(path)
            for path in relevant_files
        ],
        "file_tree": file_tree,
        "python_structure": python_structure,
        "dependency_graph": {
            "edges": dependency_edges,
            "summary": dependency_summary,
        },
        "architecture": {
            "production_modules": architecture_modules,
            "layers": architecture_layers,
            "layer_summary": architecture_layer_summary,
            "layer_percentages": architecture_layer_percentages,
            "graph": architecture_graph,
            "graph_summary": architecture_graph_summary,
        },
        "risks": architecture_risks,
        # Backward-compatible top-level access for risk consumers.
        "risk_signals": architecture_risks["risk_signals"],
        "risk_intelligence": risk_intelligence,
    }

    return analysis


def save_analysis(
    analysis: dict,
    output_path: str,
) -> None:
    """
    Save repository analysis as JSON.
    """

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            analysis,
            file,
            indent=2,
        )


def save_architecture_snapshot(
    analysis: dict,
    output_path: str,
) -> None:
    """
    Save the architecture-related data needed
    for future architecture drift comparison.
    """

    snapshot = {
        "metadata": analysis["metadata"],
        "production_modules": analysis[
            "architecture"
        ]["production_modules"],
        "layers": analysis["architecture"]["layers"],
        "layer_summary": analysis[
            "architecture"
        ]["layer_summary"],
        "layer_percentages": analysis[
            "architecture"
        ]["layer_percentages"],
        "graph": analysis["architecture"]["graph"],
        "graph_summary": analysis[
            "architecture"
        ]["graph_summary"],
    }

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            snapshot,
            file,
            indent=2,
        )


def save_versioned_architecture_snapshot(
    analysis: dict,
) -> str:
    """
    Save a timestamped architecture snapshot for
    future architecture drift comparison.
    """

    snapshot_dir = Path(
        "artifacts/architecture_snapshots"
    )

    snapshot_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    snapshot_path = (
        snapshot_dir
        / f"snapshot_{timestamp}.json"
    )

    save_architecture_snapshot(
        analysis,
        str(snapshot_path),
    )

    return str(snapshot_path)


if __name__ == "__main__":
    repository_path = (
        "artifacts/repositories/requests"
    )

    output_path = (
        "artifacts/repository_analysis.json"
    )

    analysis = analyze_repository(
        repository_path
    )

    save_analysis(
        analysis,
        output_path,
    )

    # Repository content chunks
    repository_chunks = build_repository_chunks(
        repository_path,
        analysis["relevant_files"],
    )

    chunks_path = (
        "artifacts/repository_chunks.json"
    )

    save_repository_chunks(
        repository_chunks,
        chunks_path,
    )

    # Latest architecture snapshot
    snapshot_path = (
        "artifacts/architecture_snapshot.json"
    )

    save_architecture_snapshot(
        analysis,
        snapshot_path,
    )

    # Versioned architecture snapshot
    versioned_snapshot_path = (
        save_versioned_architecture_snapshot(
            analysis
        )
    )

    print(
        "Versioned architecture snapshot:",
        versioned_snapshot_path,
    )

    print(
        "Repository analysis completed."
    )

    print(
        f"Repository: "
        f"{analysis['metadata']['repository_name']}"
    )

    print(
        f"Total files: "
        f"{analysis['metadata']['total_files']}"
    )

    print(
        f"Relevant files: "
        f"{len(analysis['relevant_files'])}"
    )

    print(
        f"Python files parsed: "
        f"{len(analysis['python_structure'])}"
    )

    print(
        f"Dependency edges: "
        f"{len(analysis['dependency_graph']['edges'])}"
    )

    print(
        f"Production modules: "
        f"{len(analysis['architecture']['production_modules'])}"
    )

    print(
        f"Architecture layers: "
        f"{len(analysis['architecture']['layers'])}"
    )

    print(
        f"Risk signals: "
        f"{analysis['risks']['risk_signal_count']}"
    )

    print(
        f"Repository chunks: "
        f"{len(repository_chunks)}"
    )

    print(
        f"Analysis saved to: "
        f"{output_path}"
    )

    print(
        f"Chunks saved to: "
        f"{chunks_path}"
    )