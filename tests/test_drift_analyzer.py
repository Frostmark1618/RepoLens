
from ingestion.drift_analyzer import (
    analyze_architecture_drift,
    build_drift_summary,
    compare_module_dependencies,
    compare_module_layers,
    compare_production_modules,
)


def main():
    baseline_modules = [
        {"file": "src/auth.py"},
        {"file": "src/models.py"},
        {"file": "src/utils.py"},
    ]

    current_modules = [
        {"file": "src/auth.py"},
        {"file": "src/models.py"},
        {"file": "src/database.py"},
    ]

    result = compare_production_modules(
        baseline_modules,
        current_modules,
    )

    assert result["added_modules"] == [
        "src/database.py"
    ]

    assert result["removed_modules"] == [
        "src/utils.py"
    ]

    assert result["unchanged_modules"] == [
        "src/auth.py",
        "src/models.py",
    ]

    assert result["added_count"] == 1
    assert result["removed_count"] == 1
    assert result["unchanged_count"] == 2




    
    baseline_dependencies = [
        {
            "file": "src/auth.py",
            "outgoing_dependencies": [
                "src/utils.py",
            ],
        },
        {
            "file": "src/models.py",
            "outgoing_dependencies": [
                "src/utils.py",
            ],
        },
    ]

    current_dependencies = [
        {
            "file": "src/auth.py",
            "outgoing_dependencies": [
                "src/utils.py",
                "src/database.py",
            ],
        },
        {
            "file": "src/models.py",
            "outgoing_dependencies": [],
        },
    ]

    dependency_result = compare_module_dependencies(
        baseline_dependencies,
        current_dependencies,
    )

    assert dependency_result["changed_count"] == 2

    assert dependency_result["changed_modules"] == [
        {
            "file": "src/auth.py",
            "added_dependencies": [
                "src/database.py",
            ],
            "removed_dependencies": [],
        },
        {
            "file": "src/models.py",
            "added_dependencies": [],
            "removed_dependencies": [
                "src/utils.py",
            ],
        },
    ]


        # Combined architecture drift test
    combined_result = analyze_architecture_drift(
        baseline_dependencies,
        current_dependencies,
    )

    assert combined_result["has_drift"] is True

    assert (
        combined_result["module_drift"]["added_count"]
        == 0
    )

    assert (
        combined_result["module_drift"]["removed_count"]
        == 0
    )

    assert (
        combined_result["module_drift"]["unchanged_count"]
        == 2
    )

    assert (
        combined_result["dependency_drift"]["changed_count"]
        == 2
    )


        # No-drift case
    no_drift_result = analyze_architecture_drift(
        baseline_dependencies,
        baseline_dependencies,
    )

    assert no_drift_result["has_drift"] is False

    assert (
        no_drift_result["module_drift"]["added_count"]
        == 0
    )

    assert (
        no_drift_result["module_drift"]["removed_count"]
        == 0
    )

    assert (
        no_drift_result["dependency_drift"]["changed_count"]
        == 0
    )



        # Drift summary test
    drift_summary = build_drift_summary(
        combined_result
    )

    assert (
    drift_summary
    == "0 modules changed "
"(0 modules added, 0 modules removed), "
"2 modules have dependency changes, and "
"0 modules have layer changes."
)

    no_drift_summary = build_drift_summary(
        no_drift_result
    )

    assert (
        no_drift_summary
        == "No architecture drift detected."
    )


        # Layer drift test
    baseline_layer_modules = [
        {
            "file": "src/auth.py",
            "layer": "source",
        },
        {
            "file": "src/config.py",
            "layer": "configuration",
        },
        {
            "file": "src/models.py",
            "layer": "source",
        },
    ]

    current_layer_modules = [
        {
            "file": "src/auth.py",
            "layer": "source",
        },
        {
            "file": "src/config.py",
            "layer": "source",
        },
        {
            "file": "src/models.py",
            "layer": "source",
        },
    ]

    layer_result = compare_module_layers(
        baseline_layer_modules,
        current_layer_modules,
    )

    assert layer_result["changed_count"] == 1

    assert layer_result["changed_modules"] == [
        {
            "file": "src/config.py",
            "baseline_layer": "configuration",
            "current_layer": "source",
        }
    ]



    print("Drift analyzer verification passed.")
    print(f"Added: {result['added_count']}")
    print(f"Removed: {result['removed_count']}")
    print(f"Unchanged: {result['unchanged_count']}")


if __name__ == "__main__":
    main()

