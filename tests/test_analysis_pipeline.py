
import json
from pathlib import Path
from ingestion.risk_analyzer import classify_risk_severity


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ANALYSIS_FILE = (
    PROJECT_ROOT
    / "artifacts"
    / "repository_analysis.json"
)


def main():
    assert ANALYSIS_FILE.exists(), (
        f"Analysis file not found: {ANALYSIS_FILE}"
    )

    with ANALYSIS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        analysis = json.load(file)

    # Required top-level sections
    required_sections = {
        "metadata",
        "relevant_files",
        "file_tree",
        "python_structure",
        "dependency_graph",
        "architecture",
        "risks",
    }

    for section in required_sections:
        assert section in analysis

    metadata = analysis["metadata"]
    dependency_graph = analysis["dependency_graph"]
    architecture = analysis["architecture"]
    risks = analysis["risks"]

    # Metadata
    assert "repository_name" in metadata
    assert "repository_path" in metadata
    assert "total_files" in metadata
    assert "python_files" in metadata

    # Relevant files
    assert isinstance(
        analysis["relevant_files"],
        list,
    )

    # Python structure
    assert isinstance(
        analysis["python_structure"],
        list,
    )

    # Dependency graph
    assert isinstance(
        dependency_graph,
        dict,
    )

    assert isinstance(
        dependency_graph["edges"],
        list,
    )

    # Architecture
    assert isinstance(
        architecture,
        dict,
    )

    assert isinstance(
        architecture["production_modules"],
        list,
    )

    assert isinstance(
        architecture["layers"],
        list,
    )

    # Architecture graph
    graph = architecture["graph"]
    graph_summary = architecture[
        "graph_summary"
    ]

    assert isinstance(graph, dict)
    assert isinstance(
        graph["nodes"],
        list,
    )
    assert isinstance(
        graph["edges"],
        list,
    )

    assert isinstance(
        graph_summary,
        dict,
    )

    assert (
        graph_summary["node_count"]
        == len(graph["nodes"])
    )

    assert (
        graph_summary["edge_count"]
        == len(graph["edges"])
    )

    # Architecture graph node validation
    node_ids = {
        node["id"]
        for node in graph["nodes"]
    }

    assert len(node_ids) == len(
        graph["nodes"]
    )

    for node in graph["nodes"]:
        assert "id" in node
        assert "label" in node
        assert "type" in node

        assert isinstance(
            node["id"],
            str,
        )

        assert isinstance(
            node["label"],
            str,
        )

        assert node["type"] == "production"

    # Architecture graph edge validation
    edge_pairs = set()

    for edge in graph["edges"]:
        assert "source" in edge
        assert "target" in edge

        assert isinstance(
            edge["source"],
            str,
        )

        assert isinstance(
            edge["target"],
            str,
        )

        assert edge["source"] in node_ids
        assert edge["target"] in node_ids

        edge_pair = (
            edge["source"],
            edge["target"],
        )

        assert edge_pair not in edge_pairs
        edge_pairs.add(edge_pair)

    # Graph summary validation
    assert (
        "isolated_node_count"
        in graph_summary
    )

    assert (
        "isolated_nodes"
        in graph_summary
    )

    assert (
        "top_connected_nodes"
        in graph_summary
    )

    assert isinstance(
        graph_summary["isolated_node_count"],
        int,
    )

    assert isinstance(
        graph_summary["isolated_nodes"],
        list,
    )

    assert isinstance(
        graph_summary["top_connected_nodes"],
        list,
    )

    assert (
        graph_summary["isolated_node_count"]
        == len(
            graph_summary["isolated_nodes"]
        )
    )

    assert (
        len(
            graph_summary[
                "top_connected_nodes"
            ]
        )
        <= 5
    )

    for node_id in graph_summary[
        "top_connected_nodes"
    ]:
        assert node_id in node_ids

    # Architecture layer validation
    layer_summary = architecture[
        "layer_summary"
    ]

    layer_percentages = architecture[
        "layer_percentages"
    ]

    assert isinstance(
        layer_summary,
        dict,
    )

    assert isinstance(
        layer_percentages,
        dict,
    )

    assert set(
        layer_summary.keys()
    ) == set(
        layer_percentages.keys()
    )

    if layer_percentages:
        assert round(
            sum(layer_percentages.values()),
            2,
        ) == 100.0

    # Production module validation
    production_modules = architecture[
        "production_modules"
    ]

    assert (
        len(production_modules)
        == len(graph["nodes"])
    )

    production_module_ids = {
        module["file"]
        for module in production_modules
    }

    assert (
        production_module_ids
        == node_ids
    )

    for module in production_modules:
        assert "file" in module
        assert "module_name" in module
        assert "type" in module
        assert "incoming_dependencies" in module
        assert "outgoing_dependencies" in module
        assert "incoming_count" in module
        assert "outgoing_count" in module
        assert "total_connections" in module

        assert isinstance(
            module["module_name"],
            str,
        )

        assert module["module_name"]

        assert module["type"] == "production"

        assert isinstance(
            module["incoming_dependencies"],
            list,
        )

        assert isinstance(
            module["outgoing_dependencies"],
            list,
        )

        assert (
            module["incoming_count"]
            == len(
                module[
                    "incoming_dependencies"
                ]
            )
        )

        assert (
            module["outgoing_count"]
            == len(
                module[
                    "outgoing_dependencies"
                ]
            )
        )

        assert (
            module["total_connections"]
            == module["incoming_count"]
            + module["outgoing_count"]
        )

    # Architecture layer entries
    for layer_entry in architecture[
        "layers"
    ]:
        assert "file" in layer_entry
        assert "layer" in layer_entry

        assert isinstance(
            layer_entry["file"],
            str,
        )

        assert isinstance(
            layer_entry["layer"],
            str,
        )

    # Risk analysis
    assert isinstance(
        risks,
        dict,
    )

    assert "risk_signals" in risks
    assert "risk_signal_count" in risks

    risk_signals = risks[
        "risk_signals"
    ]

    risk_signal_count = risks[
        "risk_signal_count"
    ]

    assert isinstance(
        risk_signals,
        list,
    )

    assert isinstance(
        risk_signal_count,
        int,
    )

    assert (
        risk_signal_count
        == len(risk_signals)
    )

    # Risk signal validation
    for risk in risk_signals:
        assert "file" in risk
        assert "module_name" in risk
        assert "signal" in risk
        assert "connection_count" in risk
        assert "incoming_count" in risk
        assert "outgoing_count" in risk
        assert "severity" in risk
        assert "status" in risk
        assert "evidence" in risk

        assert risk["file"] in (
            production_module_ids
        )

        assert isinstance(
            risk["module_name"],
            str,
        )

        assert isinstance(
            risk["connection_count"],
            int,
        )

        assert isinstance(
            risk["incoming_count"],
            int,
        )

        assert isinstance(
            risk["outgoing_count"],
            int,
        )

        assert (
            risk["connection_count"]
            == risk["incoming_count"]
            + risk["outgoing_count"]
        )

        assert risk["signal"] == (
            "high_connectivity"
        )

        assert risk["severity"] == classify_risk_severity(
    risk["connection_count"]
)
        assert risk["status"] == (
            "possible_risk"
        )

        # Evidence validation
        evidence = risk["evidence"]

        assert isinstance(
            evidence,
            dict,
        )

        assert evidence["file"] == risk[
            "file"
        ]

        assert (
            evidence["incoming_count"]
            == risk["incoming_count"]
        )

        assert (
            evidence["outgoing_count"]
            == risk["outgoing_count"]
        )

        assert (
            evidence["total_connections"]
            == risk["connection_count"]
        )

        assert isinstance(
            evidence[
                "incoming_dependencies"
            ],
            list,
        )

        assert isinstance(
            evidence[
                "outgoing_dependencies"
            ],
            list,
        )

    print(
        "Repository analysis verification passed."
    )
    print(
        f"Repository: "
        f"{metadata['repository_name']}"
    )
    print(
        f"Total files: "
        f"{metadata['total_files']}"
    )
    print(
        f"Relevant files: "
        f"{len(analysis['relevant_files'])}"
    )
    print(
        f"Python files: "
        f"{len(analysis['python_structure'])}"
    )
    print(
        f"Production modules: "
        f"{len(production_modules)}"
    )
    print(
        f"Architecture layers: "
        f"{len(architecture['layers'])}"
    )
    print(
        f"Risk signals: "
        f"{risk_signal_count}"
    )


if __name__ == "__main__":
    main()

