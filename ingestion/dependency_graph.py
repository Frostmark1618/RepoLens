import ast
from pathlib import Path

from ingestion.dependency_resolver import (
    build_python_module_map,
    resolve_internal_import,
)


def build_dependency_edges(
    repository_path: str,
) -> list[dict]:
    """
    Build unique dependency edges between Python files.

    Each edge represents:

        source file -> target file
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

    module_map = build_python_module_map(
        repository_path
    )

    edge_set = set()

    python_files = sorted(
        root.rglob("*.py")
    )

    for python_file in python_files:

        try:
            source_code = python_file.read_text(
                encoding="utf-8"
            )

            tree = ast.parse(source_code)

        except (
            SyntaxError,
            UnicodeDecodeError,
        ) as error:

            print(
                f"Skipping {python_file}: {error}"
            )

            continue

        # Keep dependency graph paths platform-independent.
        # pathlib returns Windows separators on Windows, while the
        # resolver/module map and API contract use POSIX repository paths.
        source_file = python_file.relative_to(root).as_posix()

        imported_modules = []

        # Resolve both absolute imports and Python relative imports.
        # `from . import b` has node.module=None, so looking only at
        # node.module silently drops valid internal dependencies.
        source_parts = list(Path(source_file).parts)
        if source_parts and source_parts[0] == "src":
            source_parts = source_parts[1:]

        source_package = source_parts[:-1]
        if source_parts and source_parts[-1] == "__init__.py":
            source_package = source_parts[:-1]

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.level == 0:
                    base_module = node.module
                    if base_module:
                        imported_modules.append(base_module)
                        # `from package import module` may point at a
                        # concrete child module; prefer it when present.
                        for alias in node.names:
                            if alias.name == "*":
                                continue
                            imported_modules.append(f"{base_module}.{alias.name}")
                else:
                    # level=1 means current package; level=2 means its
                    # parent, etc. Clamp at repository root rather than
                    # producing an invalid dotted path.
                    parent_index = len(source_package) - (node.level - 1)
                    if parent_index < 0:
                        continue
                    base_parts = source_package[:parent_index]
                    if node.module:
                        base_parts.extend(node.module.split("."))
                        imported_modules.append(".".join(base_parts))
                    else:
                        for alias in node.names:
                            if alias.name == "*":
                                continue
                            candidate = [*base_parts, alias.name]
                            if candidate:
                                imported_modules.append(".".join(candidate))

        for imported_module in sorted(
            set(imported_modules)
        ):

            target_file = resolve_internal_import(
                imported_module,
                module_map,
            )

            if target_file is None:
                continue

            if target_file == source_file:
                continue

            edge_set.add(
                (
                    source_file,
                    target_file,
                    imported_module,
                )
            )

    edges = [
        {
            "source": source,
            "target": target,
            "import": imported_module,
        }
        for source, target, imported_module
        in sorted(edge_set)
    ]

    return edges


def summarize_dependencies(
    edges: list[dict],
) -> dict:
    """
    Create a summary of dependency relationships.
    """

    incoming = {}
    outgoing = {}

    for edge in edges:

        source = edge["source"]
        target = edge["target"]

        outgoing[source] = (
            outgoing.get(source, 0) + 1
        )

        incoming[target] = (
            incoming.get(target, 0) + 1
        )

    return {
        "total_edges": len(edges),
        "files_with_outgoing_dependencies": len(
            outgoing
        ),
        "files_with_incoming_dependencies": len(
            incoming
        ),
        "outgoing_dependencies": dict(
            sorted(
                outgoing.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )
        ),
        "incoming_dependencies": dict(
            sorted(
                incoming.items(),
                key=lambda item: (
                    -item[1],
                    item[0],
                ),
            )
        ),
    }


if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        edges = build_dependency_edges(
            repository_path
        )

        summary = summarize_dependencies(
            edges
        )

        print(
            "Dependency analysis completed."
        )

        print(
            f"Unique dependency edges: "
            f"{summary['total_edges']}"
        )

        print(
            f"Files with outgoing dependencies: "
            f"{summary['files_with_outgoing_dependencies']}"
        )

        print(
            f"Files with incoming dependencies: "
            f"{summary['files_with_incoming_dependencies']}"
        )

        print()

        print(
            "Top files by outgoing dependencies:"
        )

        for file, count in list(
            summary["outgoing_dependencies"].items()
        )[:10]:

            print(
                f"{file}: {count}"
            )

        print()

        print(
            "Top files by incoming dependencies:"
        )

        for file, count in list(
            summary["incoming_dependencies"].items()
        )[:10]:

            print(
                f"{file}: {count}"
            )

    except Exception as error:

        print(f"Error: {error}")