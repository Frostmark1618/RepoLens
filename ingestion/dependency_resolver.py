from collections import defaultdict
from pathlib import Path


def _module_parts(relative_path: Path) -> list[str]:
    """Return importable Python module parts for a repository-relative file."""
    parts = list(relative_path.parts)

    # src-layout repositories expose packages below src, not "src.<package>".
    if parts and parts[0] == "src":
        parts = parts[1:]

    if not parts:
        return []

    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = relative_path.stem

    return parts


def build_python_module_map(repository_path: str) -> dict[str, str]:
    """
    Build an internal Python module index.

    Exact fully-qualified module names are always indexed. A short module
    name (e.g. ``utils``) is indexed only when it is unique in the repository;
    ambiguous short names are deliberately omitted so an internal import is
    never silently attributed to an arbitrary file.
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

    module_map: dict[str, str] = {}
    short_candidates: dict[str, list[str]] = defaultdict(list)

    for python_file in sorted(root.rglob("*.py")):
        relative_path = python_file.relative_to(root)
        parts = _module_parts(relative_path)

        if not parts:
            continue

        module_name = ".".join(parts)
        relative_name = relative_path.as_posix()

        # Exact module names are authoritative.
        module_map[module_name] = relative_name

        short_name = python_file.stem
        short_candidates[short_name].append(relative_name)

    # A bare module import is safe to resolve only when the name is unique.
    for short_name, candidates in short_candidates.items():
        if len(candidates) == 1:
            module_map[short_name] = candidates[0]

    return module_map


def resolve_internal_import(
    imported_module: str,
    module_map: dict[str, str],
) -> str | None:
    """
    Resolve an imported module to a repository file.

    Returns:
        Relative POSIX file path if the module is unambiguously internal.
        None otherwise.
    """
    if not isinstance(imported_module, str):
        return None

    normalized = imported_module.strip().replace("/", ".").replace("\\", ".")
    if not normalized:
        return None

    return module_map.get(normalized)


if __name__ == "__main__":
    repository_path = "artifacts/repositories/requests"

    try:
        module_map = build_python_module_map(repository_path)

        print("Python module map created.")
        print(f"Python modules found: {len(module_map)}")

        for module in ["models", "sessions", "adapters", "auth", "urllib3"]:
            resolved_file = resolve_internal_import(module, module_map)
            print(f"{module} -> {resolved_file}")

    except Exception as error:
        print(f"Error: {error}")
