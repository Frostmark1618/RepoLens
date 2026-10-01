import json
from pathlib import Path

from ingestion.drift_analyzer import analyze_snapshot_drift


PROJECT_ROOT = Path(__file__).resolve().parent.parent

ANALYSIS_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "repository_analysis.json"
)

SNAPSHOT_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "architecture_snapshot.json"
)


with ANALYSIS_PATH.open(
    "r",
    encoding="utf-8",
) as file:
    analysis = json.load(file)


with SNAPSHOT_PATH.open(
    "r",
    encoding="utf-8",
) as file:
    snapshot = json.load(file)


current_snapshot = {
    "production_modules": analysis["architecture"][
        "production_modules"
    ],
}


baseline_snapshot = {
    "production_modules": snapshot[
        "production_modules"
    ],
}


drift_result = analyze_snapshot_drift(
    baseline_snapshot,
    current_snapshot,
)


assert drift_result["has_drift"] is False

assert (
    drift_result["module_drift"]["added_count"]
    == 0
)

assert (
    drift_result["module_drift"]["removed_count"]
    == 0
)

assert (
    drift_result["dependency_drift"]["changed_count"]
    == 0
)

assert (
    drift_result["layer_drift"]["changed_count"]
    == 0
)


print("Dashboard drift verification passed.")
print(
    "Architecture drift detected:",
    drift_result["has_drift"],
)