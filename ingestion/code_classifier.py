from pathlib import Path


def classify_python_file(
    file_path: str,
) -> str:
    """
    Classify a Python file as production code or test code.
    """

    path = Path(file_path)

    parts = {
        part.lower()
        for part in path.parts
    }

    filename = path.name.lower()

    if "tests" in parts:
        return "test"

    if filename.startswith("test_"):
        return "test"

    if filename.endswith("_test.py"):
        return "test"

    return "production"


def classify_repository_python_files(
    repository_path: str,
) -> list[dict]:
    """
    Classify all Python files in a repository.
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

    results = []

    for python_file in sorted(
        root.rglob("*.py")
    ):

        relative_path = python_file.relative_to(
            root
        )

        classification = classify_python_file(
            str(relative_path)
        )

        results.append(
            {
                "file": str(relative_path),
                "type": classification,
            }
        )

    return results


if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        results = classify_repository_python_files(
            repository_path
        )

        production_count = sum(
            1
            for item in results
            if item["type"] == "production"
        )

        test_count = sum(
            1
            for item in results
            if item["type"] == "test"
        )

        print(
            "Python file classification completed."
        )

        print(
            f"Production files: {production_count}"
        )

        print(
            f"Test files: {test_count}"
        )

        print()

        print("Test files:")

        for item in results:

            if item["type"] == "test":
                print(
                    f"  {item['file']}"
                )

    except Exception as error:

        print(f"Error: {error}")