from pathlib import Path

from ingestion.architecture_layers import classify_architecture_layer

def build_architecture_modules(
    repository_path: str,
    dependency_edges: list[dict],
) -> list[dict]:
    """
    Build production architecture information
    from dependency edges.
    """

    root = Path(repository_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: {repository_path}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repository_path}"
        )

    python_files = sorted(
        root.rglob("*.py")
    )

    production_files = set()

    for python_file in python_files:
        relative_path = python_file.relative_to(root)
        relative_path_string = str(relative_path)

        if classify_architecture_layer(relative_path_string) != "source":
            continue

        production_files.add(relative_path_string)

    modules = {}

    for production_file in sorted(
        production_files
    ):

        module_path = Path(production_file)

        module_parts = list(
            module_path.parts
        )

        if module_parts and module_parts[0] == "src":
            module_parts = module_parts[1:]

        if module_parts[-1] == "__init__.py":

            module_parts = module_parts[:-1]

        else:

            module_parts[-1] = module_path.stem

        module_name = ".".join(
            module_parts
        )

        modules[production_file] = {
            "file": production_file,
            "module_name": module_name,
            "type": "production",
                        "layer": classify_architecture_layer(
                production_file
            ),
            "outgoing_dependencies": [],
            "incoming_dependencies": [],
        }

    for edge in dependency_edges:

        source = edge["source"]
        target = edge["target"]

        if source not in production_files:
            continue

        if target not in production_files:
            continue

        if target not in modules[source][
            "outgoing_dependencies"
        ]:
            modules[source][
                "outgoing_dependencies"
            ].append(target)

        if source not in modules[target][
            "incoming_dependencies"
        ]:
            modules[target][
                "incoming_dependencies"
            ].append(source)

    for module in modules.values():

        module[
            "outgoing_dependencies"
        ].sort()

        module[
            "incoming_dependencies"
        ].sort()

        module["outgoing_count"] = len(
            module[
                "outgoing_dependencies"
            ]
        )

        module["incoming_count"] = len(
            module[
                "incoming_dependencies"
            ]
        )

        module["total_connections"] = (
            module["outgoing_count"]
            + module["incoming_count"]
        )

    return list(
        modules.values()
    )


if __name__ == "__main__":

    from ingestion.dependency_graph import (
        build_dependency_edges,
    )

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        edges = build_dependency_edges(
            repository_path
        )

        modules = build_architecture_modules(
            repository_path,
            edges,
        )

        total_edges = sum(
            module[
                "outgoing_count"
            ]
            for module in modules
        )

        print(
            "Production architecture analysis completed."
        )

        print(
            f"Production modules: "
            f"{len(modules)}"
        )

        print(
            f"Production dependency edges: "
            f"{total_edges}"
        )

        print()

        print(
            "Top modules by total connections:"
        )

        sorted_modules = sorted(
            modules,
            key=lambda module: (
                -module["total_connections"],
                module["file"],
            ),
        )

        for module in sorted_modules[:10]:

            print(
                f"{module['file']}: "
                f"incoming={module['incoming_count']}, "
                f"outgoing={module['outgoing_count']}, "
                f"total={module['total_connections']}"
            )

    except Exception as error:

        print(
            f"Error: {error}"
        )