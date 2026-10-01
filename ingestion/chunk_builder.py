import ast
import json
from pathlib import Path


def _extract_python_symbols(
    file_path: Path,
    start_line: int,
    end_line: int,
) -> dict:
    """
    Extract Python classes and functions whose source
    ranges overlap the requested chunk.

    Each symbol keeps its name and exact source range.
    """

    try:
        source_code = file_path.read_text(
            encoding="utf-8"
        )

        tree = ast.parse(source_code)

    except (
        SyntaxError,
        UnicodeDecodeError,
    ):
        return {
            "classes": [],
            "functions": [],
        }

    classes = []
    functions = []

    for node in ast.walk(tree):

        if isinstance(node, ast.ClassDef):
            node_start = node.lineno
            node_end = getattr(
                node,
                "end_lineno",
                node.lineno,
            )

            if (
                node_start <= end_line
                and node_end >= start_line
            ):
                classes.append(
                    {
                        "name": node.name,
                        "start_line": node_start,
                        "end_line": node_end,
                    }
                )

        elif isinstance(
            node,
            (
                ast.FunctionDef,
                ast.AsyncFunctionDef,
            ),
        ):
            node_start = node.lineno
            node_end = getattr(
                node,
                "end_lineno",
                node.lineno,
            )

            if (
                node_start <= end_line
                and node_end >= start_line
            ):
                functions.append(
                    {
                        "name": node.name,
                        "start_line": node_start,
                        "end_line": node_end,
                    }
                )

    classes.sort(
        key=lambda item: (
            item["start_line"],
            item["name"],
        )
    )

    functions.sort(
        key=lambda item: (
            item["start_line"],
            item["name"],
        )
    )

    return {
        "classes": classes,
        "functions": functions,
    }


def build_file_chunks(
    repository_path: str,
    file_path: str,
    chunk_size: int = 50,
) -> list[dict]:
    """
    Build evidence-preserving line-based text chunks
    for a repository file.

    Python chunks additionally include class/function
    metadata.
    """

    root = Path(repository_path)
    path = Path(file_path)

    if not root.exists():
        raise FileNotFoundError(
            f"Repository path does not exist: "
            f"{repository_path}"
        )

    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: "
            f"{repository_path}"
        )

    if not path.exists():
        raise FileNotFoundError(
            f"File does not exist: {file_path}"
        )

    if not path.is_file():
        raise ValueError(
            f"Path is not a file: {file_path}"
        )

    if chunk_size <= 0:
        raise ValueError(
            "Chunk size must be greater than zero."
        )

    try:
        relative_path = path.relative_to(root)
    except ValueError as error:
        raise ValueError(
            f"File is outside repository: {file_path}"
        ) from error

    text = path.read_text(
        encoding="utf-8"
    )

    if not text.strip():
        return []

    lines = text.splitlines()
    chunks = []

    for start_index in range(
        0,
        len(lines),
        chunk_size,
    ):
        end_index = min(
            start_index + chunk_size,
            len(lines),
        )

        start_line = start_index + 1
        end_line = end_index

        chunk_lines = lines[
            start_index:end_index
        ]

        # Persist repository-relative evidence paths in the canonical Windows
        # representation used by RepoLens artifacts and API evidence records.
        # This keeps regenerated artifacts stable across Windows/Linux tooling.
        canonical_relative_path = str(relative_path).replace("/", "\\")

        chunk = {
            "file": canonical_relative_path,
            "extension": path.suffix.lower(),
            "start_line": start_line,
            "end_line": end_line,
            "content": "\n".join(chunk_lines),
        }

        if path.suffix.lower() == ".py":
            symbols = _extract_python_symbols(
                path,
                start_line,
                end_line,
            )

            chunk["symbols"] = symbols

        chunks.append(chunk)

    return chunks


def build_repository_chunks(
    repository_path: str,
    file_paths: list[str],
    chunk_size: int = 50,
) -> list[dict]:
    """
    Build evidence-preserving chunks for multiple
    repository files.
    """

    chunks = []

    for file_path in file_paths:
        file_chunks = build_file_chunks(
            repository_path,
            file_path,
            chunk_size=chunk_size,
        )

        chunks.extend(file_chunks)

    return chunks


def save_repository_chunks(
    chunks: list[dict],
    output_path: str,
) -> None:
    """
    Save repository chunks as a JSON artifact.
    """

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file.write_text(
        json.dumps(
            chunks,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )