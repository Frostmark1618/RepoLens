ALLOWED_LAYER_DEPENDENCIES = {
    "source": {
        "source",
        "configuration",
        "documentation",
    },
    "test": {
        "test",
        "source",
        "configuration",
        "documentation",
    },
    "configuration": {
        "configuration",
        "documentation",
    },
    "documentation": {
        "documentation",
    },
    "other": {
        "other",
        "source",
        "test",
        "configuration",
        "documentation",
    },
}


def detect_layer_violations(
    dependency_edges: list[dict],
    architecture_layers: list[dict],
) -> list[dict]:
    """Detect dependency edges that violate layer direction rules."""

    if not isinstance(
        dependency_edges,
        list,
    ):
        raise TypeError(
            "Dependency edges must be a list."
        )

    if not isinstance(
        architecture_layers,
        list,
    ):
        raise TypeError(
            "Architecture layers must be a list."
        )

    file_to_layer = {}

    for item in architecture_layers:
        if not isinstance(item, dict):
            raise TypeError(
                "Each architecture layer item must be a dictionary."
            )

        file = item.get("file")
        layer = item.get("layer")

        if not isinstance(file, str):
            raise TypeError(
                "Architecture layer file must be a string."
            )

        if not isinstance(layer, str):
            raise TypeError(
                "Architecture layer must be a string."
            )

        file_to_layer[file] = layer.strip().lower()

    risk_signals = []

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

        source_layer = file_to_layer.get(source)
        target_layer = file_to_layer.get(target)

        if source_layer is None or target_layer is None:
            continue

        allowed_targets = ALLOWED_LAYER_DEPENDENCIES.get(
            source_layer,
            set(),
        )

        if target_layer in allowed_targets:
            continue

        risk_signals.append(
            {
                "category": "architecture",
                "signal": "layer_violation",
                "status": "possible_risk",
                "source": source,
                "target": target,
                "source_layer": source_layer,
                "target_layer": target_layer,
                "evidence": {
                    "source": source,
                    "target": target,
                    "source_layer": source_layer,
                    "target_layer": target_layer,
                },
            }
        )

    return risk_signals


if __name__ == "__main__":
    print(
        "Layer violation analyzer module loaded successfully."
    )
