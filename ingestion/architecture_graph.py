from pathlib import Path


def build_architecture_graph(
    architecture_modules: list[dict],
) -> dict:
    """
    Build a clean architecture graph from
    production module information.

    Nodes represent production modules.
    Edges represent module dependencies.
    """

    nodes = []
    edges = []

    module_lookup = {
        module["file"]: module
        for module in architecture_modules
    }

    for module in architecture_modules:

        nodes.append(
            {
                "id": module["file"],
                "label": module["module_name"],
                "type": module["type"],
            }
        )

    for module in architecture_modules:

        source = module["file"]

        for target in module[
            "outgoing_dependencies"
        ]:

            if target not in module_lookup:
                continue

            edges.append(
                {
                    "source": source,
                    "target": target,
                }
            )

    nodes.sort(
        key=lambda node: node["id"]
    )

    edges.sort(
        key=lambda edge: (
            edge["source"],
            edge["target"],
        )
    )

    return {
        "nodes": nodes,
        "edges": edges,
    }


def summarize_architecture_graph(
    graph: dict,
) -> dict:
    """
    Create basic graph metrics.
    """
    nodes = graph["nodes"]
    edges = graph["edges"]

    incoming_counts = {
        node["id"]: 0
        for node in nodes
    }

    outgoing_counts = {
        node["id"]: 0
        for node in nodes
    }

    for edge in edges:
        source = edge["source"]
        target = edge["target"]

        if source in outgoing_counts:
            outgoing_counts[source] += 1

        if target in incoming_counts:
            incoming_counts[target] += 1

    connected_node_ids = set()

    for edge in edges:
        connected_node_ids.add(edge["source"])
        connected_node_ids.add(edge["target"])

    isolated_nodes = [
        node["id"]
        for node in nodes
        if node["id"] not in connected_node_ids
    ]

    isolated_nodes.sort()

    total_connections = {
        node_id: incoming_counts[node_id] + outgoing_counts[node_id]
        for node_id in incoming_counts
    }

    top_connected_nodes = sorted(
        total_connections,
        key=lambda node_id: (
            -total_connections[node_id],
            node_id,
        ),
    )[:5]

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "isolated_node_count": len(isolated_nodes),
        "isolated_nodes": isolated_nodes,
        "top_connected_nodes": top_connected_nodes,
    }


if __name__ == "__main__":

    from ingestion.architecture_builder import (
        build_architecture_modules,
    )
    from ingestion.dependency_graph import (
        build_dependency_edges,
    )

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        dependency_edges = (
            build_dependency_edges(
                repository_path
            )
        )

        architecture_modules = (
            build_architecture_modules(
                repository_path,
                dependency_edges,
            )
        )

        graph = build_architecture_graph(
            architecture_modules
        )

        summary = (
            summarize_architecture_graph(
                graph
            )
        )

        print(
            "Architecture graph built successfully."
        )

        print()

        print(
            f"Nodes: {summary['node_count']}"
        )

        print(
            f"Edges: {summary['edge_count']}"
        )

        print()

        print("Sample nodes:")

        for node in graph["nodes"][:10]:

            print(
                f"{node['id']} -> "
                f"{node['label']}"
            )

        print()

        print("Sample edges:")

        for edge in graph["edges"][:10]:

            print(
                f"{edge['source']} -> "
                f"{edge['target']}"
            )

    except Exception as error:

        print(
            f"Error: {error}"
        )