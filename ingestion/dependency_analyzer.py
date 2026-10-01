import ast
from pathlib import Path


def analyze_python_dependencies(
    repository_path: str,
) -> list[dict]:
    """
    Analyze import relationships between Python files
    inside a repository.
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

    results = []

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

        imports = []

        for node in ast.walk(tree):

            if isinstance(node, ast.Import):

                for alias in node.names:
                    imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):

                if node.module:
                    imports.append(node.module)

        relative_path = python_file.relative_to(
            root
        )

        results.append(
            {
                "file": str(relative_path),
                "imports": sorted(set(imports)),
            }
        )

    return results


if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        dependencies = analyze_python_dependencies(
            repository_path
        )

        print(
            "Python dependency analysis completed."
        )

        print(
            f"Python files analyzed: "
            f"{len(dependencies)}"
        )

        print()

        for item in dependencies[:10]:

            print(
                f"File: {item['file']}"
            )

            print(
                f"Imports: {item['imports']}"
            )

            print()

    except Exception as error:

        print(f"Error: {error}")