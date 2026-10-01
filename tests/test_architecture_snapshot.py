import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ANALYSIS_FILE = (
    PROJECT_ROOT
    / "artifacts"
    / "repository_analysis.json"
)

SNAPSHOT_FILE = (
    PROJECT_ROOT
    / "artifacts"
    / "architecture_snapshot.json"
)


def main():
    assert ANALYSIS_FILE.exists(), (
        f"Analysis file not found: {ANALYSIS_FILE}"
    )

    assert SNAPSHOT_FILE.exists(), (
        f"Architecture snapshot not found: {SNAPSHOT_FILE}"
    )

    with ANALYSIS_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        analysis = json.load(file)

    with SNAPSHOT_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    architecture = analysis["architecture"]

    assert snapshot["metadata"] == analysis["metadata"]

    assert (
        snapshot["production_modules"]
        == architecture["production_modules"]
    )

    assert (
        snapshot["layers"]
        == architecture["layers"]
    )

    assert (
        snapshot["layer_summary"]
        == architecture["layer_summary"]
    )

    assert (
        snapshot["layer_percentages"]
        == architecture["layer_percentages"]
    )

    assert (
        snapshot["graph"]
        == architecture["graph"]
    )

    assert (
        snapshot["graph_summary"]
        == architecture["graph_summary"]
    )

    print("Architecture snapshot verification passed.")
    print(
        "Production modules:",
        len(snapshot["production_modules"]),
    )
    print(
        "Architecture nodes:",
        len(snapshot["graph"]["nodes"]),
    )
    print(
        "Architecture edges:",
        len(snapshot["graph"]["edges"]),
    )


if __name__ == "__main__":
    main()