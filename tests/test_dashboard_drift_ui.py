from ingestion.drift_analyzer import analyze_architecture_drift


baseline_modules = [
    {
        "file": "src/auth.py",
        "layer": "source",
        "outgoing_dependencies": ["src/utils.py"],
    },
    {
        "file": "src/models.py",
        "layer": "configuration",
        "outgoing_dependencies": ["src/utils.py"],
    },
    {
        "file": "src/utils.py",
        "layer": "source",
        "outgoing_dependencies": [],
    },
]


current_modules = [
    {
        "file": "src/auth.py",
        "layer": "source",
        "outgoing_dependencies": [
            "src/utils.py",
            "src/database.py",
        ],
    },
    {
        "file": "src/models.py",
        "layer": "source",
        "outgoing_dependencies": [],
    },
    {
        "file": "src/database.py",
        "layer": "source",
        "outgoing_dependencies": [],
    },
]


drift_result = analyze_architecture_drift(
    baseline_modules,
    current_modules,
)


assert drift_result["has_drift"] is True

assert (
    drift_result["module_drift"]["added_modules"]
    == ["src/database.py"]
)

assert (
    drift_result["module_drift"]["removed_modules"]
    == ["src/utils.py"]
)

assert (
    drift_result["dependency_drift"]["changed_count"]
    == 2
)

assert (
    drift_result["layer_drift"]["changed_count"]
    == 1
)

assert (
    drift_result["layer_drift"]["changed_modules"][0]
    == {
        "file": "src/models.py",
        "baseline_layer": "configuration",
        "current_layer": "source",
    }
)


print("Synthetic dashboard drift verification passed.")
print(
    "Architecture drift detected:",
    drift_result["has_drift"],
)
print(
    "Modules added:",
    drift_result["module_drift"]["added_count"],
)
print(
    "Modules removed:",
    drift_result["module_drift"]["removed_count"],
)
print(
    "Dependency changes:",
    drift_result["dependency_drift"]["changed_count"],
)
print(
    "Layer changes:",
    drift_result["layer_drift"]["changed_count"],
)