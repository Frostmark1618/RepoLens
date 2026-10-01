import ast
import json
from pathlib import Path


def parse_python_file(file_path: str) -> dict:
    """
    Extract basic structural information from a Python file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    if path.suffix.lower() != ".py":
        raise ValueError(
            f"Not a Python file: {file_path}"
        )

    source_code = path.read_text(
        encoding="utf-8"
    )

    try:
        tree = ast.parse(source_code)

    except SyntaxError as error:
        raise SyntaxError(
            f"Could not parse {file_path}: {error}"
        ) from error

    imports = []
    functions = []
    classes = []

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.append(node.module)

        elif isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):

            functions.append(node.name)

        elif isinstance(node, ast.ClassDef):

            classes.append(node.name)

    return {
        "file": str(path),
        "imports": sorted(set(imports)),
        "functions": sorted(set(functions)),
        "classes": sorted(set(classes)),
    }


def parse_repository(repository_path: str) -> list[dict]:
    """
    Parse all Python files inside a repository.
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
            result = parse_python_file(
                str(python_file)
            )

            results.append(result)

        except (
            SyntaxError,
            UnicodeDecodeError,
        ) as error:

            print(
                f"Skipping {python_file}: {error}"
            )

    return results


def save_repository_structure(
    results: list[dict],
    output_path: str,
) -> None:
    """
    Save parsed repository structure as a JSON artifact.
    """

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(
            results,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    output_path = (
        "artifacts/repository_structure.json"
    )

    try:

        results = parse_repository(
            repository_path
        )

        save_repository_structure(
            results,
            output_path,
        )

        print(
            f"Python files parsed successfully: "
            f"{len(results)}"
        )

        print(
            f"Structure saved to: {output_path}"
        )

    except Exception as error:

        print(f"Error: {error}")