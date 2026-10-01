def _find_strongly_connected_components(
    graph: dict[str, set[str]],
) -> list[list[str]]:
    """Find strongly connected components using Tarjan's algorithm."""

    index = 0
    indices: dict[str, int] = {}
    low_links: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    components: list[list[str]] = []

    def strong_connect(node: str) -> None:
        nonlocal index

        indices[node] = index
        low_links[node] = index
        index += 1

        stack.append(node)
        on_stack.add(node)

        for neighbor in sorted(
            graph.get(node, set())
        ):
            if neighbor not in indices:
                strong_connect(neighbor)

                low_links[node] = min(
                    low_links[node],
                    low_links[neighbor],
                )

            elif neighbor in on_stack:
                low_links[node] = min(
                    low_links[node],
                    indices[neighbor],
                )

        if low_links[node] == indices[node]:
            component = []

            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.append(member)

                if member == node:
                    break

            components.append(
                sorted(component)
            )

    for node in sorted(graph):
        if node not in indices:
            strong_connect(node)

    return components


def detect_circular_dependencies(
    dependency_edges: list[dict],
) -> list[dict]:
    """Detect circular dependency components from dependency edges."""

    if not isinstance(
        dependency_edges,
        list,
    ):
        raise TypeError(
            "Dependency edges must be a list."
        )

    graph: dict[str, set[str]] = {}

    for edge in dependency_edges:
        if not isinstance(edge, dict):
            raise TypeError(
                "Each dependency edge must be a dictionary."
            )

        source = edge.get("source")
        target = edge.get("target")

        if not isinstance(source, str):
            raise TypeError(
                "Dependency edge source must be a string."
            )

        if not isinstance(target, str):
            raise TypeError(
                "Dependency edge target must be a string."
            )

        source = source.strip()
        target = target.strip()

        if not source or not target:
            raise ValueError(
                "Dependency edge source and target "
                "cannot be empty."
            )

        graph.setdefault(source, set()).add(target)
        graph.setdefault(target, set())

    components = _find_strongly_connected_components(
        graph
    )

    risk_signals = []

    for component in components:
        is_cycle = len(component) > 1

        if not is_cycle:
            node = component[0]

            if node not in graph.get(node, set()):
                continue

        component_set = set(component)

        component_edges = []

        for source in sorted(component_set):
            for target in sorted(
                graph.get(source, set())
            ):
                if target in component_set:
                    component_edges.append(
                        {
                            "source": source,
                            "target": target,
                        }
                    )

        risk_signals.append(
            {
                "category": "architecture",
                "signal": "circular_dependency",
                "status": "possible_risk",
                "severity": "high",
                "cycle": component,
                "evidence": {
                    "nodes": component,
                    "edges": component_edges,
                },
            }
        )

    risk_signals.sort(
        key=lambda item: item["cycle"]
    )

    return risk_signals


if __name__ == "__main__":
    print(
        "Circular dependency analyzer module loaded successfully."
    )