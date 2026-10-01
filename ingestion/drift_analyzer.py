
def compare_production_modules(
    baseline_modules: list[dict],
    current_modules: list[dict],
) -> dict:
    """
    Compare production modules between two
    architecture snapshots.

    A module is identified by its file path.
    """

    baseline_files = {
        module["file"]
        for module in baseline_modules
    }

    current_files = {
        module["file"]
        for module in current_modules
    }

    added_modules = sorted(
        current_files - baseline_files
    )

    removed_modules = sorted(
        baseline_files - current_files
    )

    unchanged_modules = sorted(
        baseline_files & current_files
    )

    return {
        "added_modules": added_modules,
        "removed_modules": removed_modules,
        "unchanged_modules": unchanged_modules,
        "added_count": len(added_modules),
        "removed_count": len(removed_modules),
        "unchanged_count": len(unchanged_modules),
    }





def compare_module_dependencies(
    baseline_modules: list[dict],
    current_modules: list[dict],
) -> dict:
    """
    Compare dependencies of production modules
    between two architecture snapshots.

    A dependency change is identified by comparing
    the outgoing dependency lists of modules that
    exist in both snapshots.
    """

    baseline_by_file = {
        module["file"]: module
        for module in baseline_modules
    }

    current_by_file = {
        module["file"]: module
        for module in current_modules
    }

    changed_modules = []

    common_files = (
        baseline_by_file.keys()
        & current_by_file.keys()
    )

    for file in sorted(common_files):
        baseline_dependencies = set(
            baseline_by_file[file].get(
                "outgoing_dependencies",
                [],
            )
        )

        current_dependencies = set(
            current_by_file[file].get(
                "outgoing_dependencies",
                [],
            )
        )

        added_dependencies = sorted(
            current_dependencies - baseline_dependencies
        )

        removed_dependencies = sorted(
            baseline_dependencies - current_dependencies
        )

        if not added_dependencies and not removed_dependencies:
            continue

        changed_modules.append({
            "file": file,
            "added_dependencies": added_dependencies,
            "removed_dependencies": removed_dependencies,
        })

    return {
        "changed_modules": changed_modules,
        "changed_count": len(changed_modules),
    }



def analyze_architecture_drift(
    baseline_modules: list[dict],
    current_modules: list[dict],
) -> dict:
    """
    Combine production module drift, dependency drift,
    and layer drift into a single architecture drift result.
    """

    module_drift = compare_production_modules(
        baseline_modules,
        current_modules,
    )

    dependency_drift = compare_module_dependencies(
        baseline_modules,
        current_modules,
    )

    layer_drift = compare_module_layers(
        baseline_modules,
        current_modules,
    )

    return {
        "module_drift": module_drift,
        "dependency_drift": dependency_drift,
        "layer_drift": layer_drift,
        "has_drift": (
            module_drift["added_count"] > 0
            or module_drift["removed_count"] > 0
            or dependency_drift["changed_count"] > 0
            or layer_drift["changed_count"] > 0
        ),
    }




def analyze_snapshot_drift(
    baseline_snapshot: dict,
    current_snapshot: dict,
) -> dict:
    """
    Compare architecture drift between two
    loaded architecture snapshots.
    """

    baseline_modules = baseline_snapshot[
        "production_modules"
    ]

    current_modules = current_snapshot[
        "production_modules"
    ]

    architecture_drift = analyze_architecture_drift(
        baseline_modules,
        current_modules,
    )

    layer_drift = compare_module_layers(
        baseline_modules,
        current_modules,
    )

    architecture_drift["layer_drift"] = layer_drift

    architecture_drift["has_drift"] = (
        architecture_drift["has_drift"]
        or layer_drift["changed_count"] > 0
    )

    return architecture_drift


def build_drift_summary(
    drift_result: dict,
) -> str:
    """
    Build a deterministic human-readable summary
    from an architecture drift result.
    """

    module_drift = drift_result["module_drift"]
    dependency_drift = drift_result["dependency_drift"]
    layer_drift = drift_result["layer_drift"]

    added_count = module_drift["added_count"]
    removed_count = module_drift["removed_count"]

    dependency_change_count = (
        dependency_drift["changed_count"]
    )

    layer_change_count = (
        layer_drift["changed_count"]
    )



    if not drift_result["has_drift"]:
        return "No architecture drift detected."

    module_change_count = (
        added_count + removed_count
    )

    module_word = (
        "module"
        if module_change_count == 1
        else "modules"
    )

    added_word = (
        "module"
        if added_count == 1
        else "modules"
    )

    removed_word = (
        "module"
        if removed_count == 1
        else "modules"
    )

    dependency_word = (
        "module"
        if dependency_change_count == 1
        else "modules"
    )

    layer_word = (
        "module"
        if layer_change_count == 1
        else "modules"
    )

    return (
        f"{module_change_count} {module_word} changed "
        f"({added_count} {added_word} added, "
        f"{removed_count} {removed_word} removed), "
        f"{dependency_change_count} {dependency_word} have "
        f"dependency changes, and "
        f"{layer_change_count} {layer_word} have "
        f"layer changes."
    )

    






def compare_module_layers(
    baseline_modules: list[dict],
    current_modules: list[dict],
) -> dict:
    """
    Compare architecture layers of modules that
    exist in both baseline and current snapshots.

    A layer change is identified by comparing the
    architecture layer assigned to the same file.
    """

    baseline_by_file = {
        module["file"]: module
        for module in baseline_modules
    }

    current_by_file = {
        module["file"]: module
        for module in current_modules
    }

    changed_modules = []

    common_files = (
        baseline_by_file.keys()
        & current_by_file.keys()
    )

    for file in sorted(common_files):
        baseline_layer = baseline_by_file[file].get(
            "layer"
        )

        current_layer = current_by_file[file].get(
            "layer"
        )

        if baseline_layer == current_layer:
            continue

        changed_modules.append({
            "file": file,
            "baseline_layer": baseline_layer,
            "current_layer": current_layer,
        })

    return {
        "changed_modules": changed_modules,
        "changed_count": len(changed_modules),
    }








if __name__ == "__main__":
    print("Drift analyzer module loaded successfully.")

