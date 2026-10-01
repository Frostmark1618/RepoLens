from pathlib import Path


def classify_architecture_layer(
    file_path: str,
) -> str:
    """
    Classify a repository file into a basic
    architectural layer based on its path.
    """

    path = Path(file_path)

    parts = {
        part.lower()
        for part in path.parts
    }

    filename = path.name.lower()

    # Test layer
    if "tests" in parts:
        return "test"

    if filename.startswith("test_"):
        return "test"

    if filename.endswith("_test.py"):
        return "test"

    # Documentation layer
    if "docs" in parts:
        return "documentation"

    if path.suffix.lower() in {
        ".md",
        ".txt",
    }:
        return "documentation"

    # Configuration / project setup
    if filename in {
        "setup.py",
        "pyproject.toml",
        "setup.cfg",
        "tox.ini",
        "pytest.ini",
    }:
        return "configuration"

    # Source / production layer
    if "src" in parts:
        return "source"

    # Root-level Python files
    if path.suffix.lower() == ".py":
        return "source"

    return "other"


def classify_repository_layers(
    repository_path: str,
) -> list[dict]:
    """
    Classify repository files into basic
    architectural layers.
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

    for file_path in sorted(
        root.rglob("*")
    ):

        if not file_path.is_file():
            continue

        if ".git" in file_path.parts:
            continue

        relative_path = file_path.relative_to(
            root
        )

        layer = classify_architecture_layer(
            str(relative_path)
        )

        results.append(
            {
                "file": str(relative_path),
                "layer": layer,
            }
        )

    return results







def summarize_architecture_layers(
    layer_results: list[dict],
) -> dict:
    """
    Create a summary of architecture layer counts.
    """

    layer_counts = {}

    for item in layer_results:

        layer = item["layer"]

        layer_counts[layer] = (
            layer_counts.get(layer, 0) + 1
        )

    return dict(
        sorted(
            layer_counts.items()
        )
    )


def calculate_layer_percentages(
    layer_summary: dict[str, int],
) -> dict[str, float]:
    """
    Calculate the percentage of files
    belonging to each architecture layer.
    """

    total_files = sum(
        layer_summary.values()
    )

    if total_files == 0:
        return {}

    percentages = {}

    for layer, count in layer_summary.items():

        percentages[layer] = round(
            (count / total_files) * 100,
            2,
        )

    return percentages



if __name__ == "__main__":

    repository_path = (
        "artifacts/repositories/requests"
    )

    try:

        results = classify_repository_layers(
            repository_path
        )

        layer_counts = summarize_architecture_layers(
            results
        )
        layer_percentages = calculate_layer_percentages(
            layer_counts
        )
        print()

        print("Layer percentages:")

        for layer, percentage in layer_percentages.items():

            print(
                f"{layer}: {percentage}%"
            )

        print(
            "Architecture layer classification completed."
        )

        print()

        print("Layer counts:")

        for layer, count in sorted(
            layer_counts.items()
        ):

            print(
                f"{layer}: {count}"
            )

        print()

        print("Sample classifications:")

        for item in results[:15]:

            print(
                f"{item['file']} -> "
                f"{item['layer']}"
            )

    except Exception as error:

        print(
            f"Error: {error}"
        )