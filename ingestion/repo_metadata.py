from pathlib import Path


def collect_repository_metadata(
    repository_path: str,
) -> dict:
    """
    Collect basic metadata about a repository.

    Args:
        repository_path: Local path of the repository.

    Returns:
        A dictionary containing basic repository information.
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

    all_files = [
        path
        for path in root.rglob("*")
        if path.is_file()
    ]

    python_files = [
        path
        for path in all_files
        if path.suffix.lower() == ".py"
    ]

    return {
        "repository_name": root.name,
        "repository_path": str(root),
        "total_files": len(all_files),
        "python_files": len(python_files),
    }


if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        metadata = collect_repository_metadata(
            repository_path
        )

        print("Repository metadata:")
        print()

        for key, value in metadata.items():
            print(f"{key}: {value}")

    except Exception as error:

        print(f"Error: {error}")