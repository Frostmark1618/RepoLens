
import json
from pathlib import Path
from collections import Counter


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_FILE = PROJECT_ROOT / "artifacts" / "repository_analysis.json"


def main():
    assert ANALYSIS_FILE.exists(), (
        f"Analysis file not found: {ANALYSIS_FILE}"
    )

    with ANALYSIS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        analysis = json.load(file)

    metadata = analysis["metadata"]
    architecture = analysis["architecture"]
    dependency_graph = analysis["dependency_graph"]

    production_modules = architecture["production_modules"]
    graph = architecture["graph"]
    graph_summary = architecture["graph_summary"]

    # Repository metadata
    assert metadata["total_files"] >= 0
    assert metadata["python_files"] >= 0

    # Architecture nodes
    node_ids = {
        node["id"]
        for node in graph["nodes"]
    }

    assert len(node_ids) == len(graph["nodes"])
    assert graph_summary["node_count"] == len(graph["nodes"])

    # Architecture edges
    edge_pairs = {
        (edge["source"], edge["target"])
        for edge in graph["edges"]
    }

    assert len(edge_pairs) == len(graph["edges"])
    assert graph_summary["edge_count"] == len(graph["edges"])

    for edge in graph["edges"]:
        assert edge["source"] in node_ids
        assert edge["target"] in node_ids

    # Production modules must match graph nodes
    production_module_ids = {
        module["file"]
        for module in production_modules
    }

    assert production_module_ids == node_ids

    # Production module connection counts
    for module in production_modules:
        assert (
            module["total_connections"]
            == module["incoming_count"]
            + module["outgoing_count"]
        )

    # Architecture layer percentages
    layer_summary = architecture["layer_summary"]
    layer_percentages = architecture["layer_percentages"]

    assert set(layer_summary.keys()) == set(
        layer_percentages.keys()
    )

    if layer_percentages:
        assert round(
            sum(layer_percentages.values()),
            2,
        ) == 100.0

    # Graph summary consistency
    isolated_nodes = graph_summary["isolated_nodes"]

    assert (
        graph_summary["isolated_node_count"]
        == len(isolated_nodes)
    )

    assert graph_summary["isolated_node_count"] >= 0

    top_connected_nodes = graph_summary["top_connected_nodes"]

    assert len(top_connected_nodes) <= 5

    for node_id in top_connected_nodes:
        assert node_id in node_ids


    
    # Risk summary consistency
    risk_signals = analysis["risks"]["risk_signals"]
    risk_signal_count = analysis["risks"]["risk_signal_count"]

    severity_counts = Counter(
        risk["severity"]
        for risk in risk_signals
    )

    assert severity_counts["critical"] == 0
    assert severity_counts["high"] == 1
    assert severity_counts["medium"] == 7

    assert (
        sum(severity_counts.values())
        == risk_signal_count
    )


        # Risk percentage consistency
    total_risks = risk_signal_count

    severity_percentages = {
        severity: (
            count / total_risks * 100
            if total_risks
            else 0
        )
        for severity, count in severity_counts.items()
    }

    assert round(
        sum(severity_percentages.values()),
        2,
    ) == 100.0

    assert severity_percentages.get("critical", 0) == 0.0
    assert severity_percentages.get("high", 0) == 12.5
    assert severity_percentages.get("medium", 0) == 87.5

    print("Dashboard data verification passed.")
    print(f"Repository: {metadata['repository_name']}")
    print(f"Production modules: {len(production_modules)}")
    print(f"Architecture nodes: {len(graph['nodes'])}")
    print(f"Architecture edges: {len(graph['edges'])}")


if __name__ == "__main__":
    main()

