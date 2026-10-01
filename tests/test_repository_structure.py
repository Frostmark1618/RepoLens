import json
from pathlib import Path


ARTIFACT_PATH = Path(
    "artifacts/repository_structure.json"
)


def test_repository_structure():

    if not ARTIFACT_PATH.exists():
        raise FileNotFoundError(
            f"Artifact not found: {ARTIFACT_PATH}"
        )

    data = json.loads(
        ARTIFACT_PATH.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(data, list):
        raise ValueError(
            "Repository structure must be a list."
        )

    if len(data) == 0:
        raise ValueError(
            "No Python files were found."
        )

    required_keys = {
        "file",
        "imports",
        "functions",
        "classes",
    }

    for item in data:

        if not required_keys.issubset(item.keys()):
            raise ValueError(
                f"Invalid structure: {item}"
            )

    total_imports = sum(
        len(item["imports"])
        for item in data
    )

    total_functions = sum(
        len(item["functions"])
        for item in data
    )

    total_classes = sum(
        len(item["classes"])
        for item in data
    )

    print("Repository structure verification passed.")
    print(f"Python files: {len(data)}")
    print(f"Total imports: {total_imports}")
    print(f"Total functions: {total_functions}")
    print(f"Total classes: {total_classes}")


if __name__ == "__main__":
    try:
        test_repository_structure()

    except Exception as error:
        print(f"Error: {error}")