from pathlib import Path

from config.settings import (
    SUPPORTED_EXTENSIONS,
    IGNORED_DIRECTORIES,
)


def collect_files(repository_path: str) -> list[Path]:
    """
    Collect relevant files from a repository.

    Args:
        repository_path: Local path of the cloned repository.

    Returns:
        A sorted list of relevant file paths.
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

    collected_files = []

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if any(
            ignored_directory in path.parts
            for ignored_directory in IGNORED_DIRECTORIES
        ):
            continue

        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            collected_files.append(path)

    return sorted(collected_files)


if __name__ == "__main__":
    repository_path = "artifacts/repositories/requests"

    try:
        files = collect_files(repository_path)

        print(f"Relevant files found: {len(files)}")
        print()

        for file_path in files:
            print(file_path)

    except Exception as error:
        print(f"Error: {error}")