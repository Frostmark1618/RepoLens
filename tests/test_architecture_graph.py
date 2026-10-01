from ingestion.architecture_graph import (
    build_architecture_graph,
    summarize_architecture_graph,
)


def main():
    architecture_modules = [
        {
            "file": "src/a.py",
            "module_name": "a",
            "type": "production",
            "outgoing_dependencies": ["src/b.py"],
            "incoming_dependencies": ["src/c.py"],
        },
        {
            "file": "src/b.py",
            "module_name": "b",
            "type": "production",
            "outgoing_dependencies": [],
            "incoming_dependencies": ["src/a.py"],
        },
        {
            "file": "src/c.py",
            "module_name": "c",
            "type": "production",
            "outgoing_dependencies": ["src/a.py"],
            "incoming_dependencies": [],
        },
        {
            "file": "src/d.py",
            "module_name": "d",
            "type": "production",
            "outgoing_dependencies": [],
            "incoming_dependencies": [],
        },
    ]

    graph = build_architecture_graph(architecture_modules)
    summary = summarize_architecture_graph(graph)

    assert summary["node_count"] == 4
    assert summary["edge_count"] == 2

    assert summary["isolated_node_count"] == 1
    assert summary["isolated_nodes"] == ["src/d.py"]

    assert summary["top_connected_nodes"] == [
        "src/a.py",
        "src/b.py",
        "src/c.py",
        "src/d.py",
    ]

    print("Architecture graph unit verification passed.")
    print(f"Nodes: {summary['node_count']}")
    print(f"Edges: {summary['edge_count']}")
    print(f"Isolated nodes: {summary['isolated_nodes']}")
    print(f"Top connected nodes: {summary['top_connected_nodes']}")


if __name__ == "__main__":
    main()