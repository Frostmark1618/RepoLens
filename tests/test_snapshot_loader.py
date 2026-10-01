from ingestion.snapshot_loader import (
    load_architecture_snapshot,
)


from ingestion.drift_analyzer import (
    analyze_snapshot_drift,
)


def main():
    snapshot_path = (
        "artifacts/architecture_snapshot.json"
    )

    snapshot = load_architecture_snapshot(
        snapshot_path
    )

    assert isinstance(snapshot, dict)

    assert "metadata" in snapshot
    assert "production_modules" in snapshot
    assert "layers" in snapshot
    assert "graph" in snapshot
    assert "graph_summary" in snapshot

    assert (
        len(snapshot["production_modules"])
        == 19
    )

    assert (
        len(snapshot["graph"]["nodes"])
        == 19
    )

    assert (
        len(snapshot["graph"]["edges"])
        == 73
    )


    baseline_snapshot = load_architecture_snapshot(
        snapshot_path
    )

    current_snapshot = load_architecture_snapshot(
        snapshot_path
    )

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


        # Synthetic drift scenario
    synthetic_current_snapshot = {
        "production_modules": [
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
    }

    synthetic_baseline_snapshot = {
        "production_modules": [
            {
    "file": "src/auth.py",
    "layer": "source",
    "outgoing_dependencies": [
        "src/utils.py",
    ],
},
            {
    "file": "src/models.py",
    "layer": "configuration",
    "outgoing_dependencies": [
        "src/utils.py",
    ],
},
           {
    "file": "src/utils.py",
    "layer": "source",
    "outgoing_dependencies": [],
},
        ]
    }

    synthetic_result = analyze_snapshot_drift(
        synthetic_baseline_snapshot,
        synthetic_current_snapshot,
    )

    assert synthetic_result["has_drift"] is True

    assert (
        synthetic_result["module_drift"]["added_modules"]
        == ["src/database.py"]
    )

    assert (
        synthetic_result["module_drift"]["removed_modules"]
        == ["src/utils.py"]
    )

    assert (
        synthetic_result["dependency_drift"]["changed_count"]
        == 2
    )




    assert (
        synthetic_result["layer_drift"]["changed_count"]
        == 1
    )

    assert (
        synthetic_result["layer_drift"]["changed_modules"]
        == [
            {
                "file": "src/models.py",
                "baseline_layer": "configuration",
                "current_layer": "source",
            }
        ]
    )



        # Layer-only drift scenario
    layer_only_baseline = {
        "production_modules": [
            {
                "file": "src/config.py",
                "layer": "configuration",
                "outgoing_dependencies": [],
            }
        ]
    }

    layer_only_current = {
        "production_modules": [
            {
                "file": "src/config.py",
                "layer": "source",
                "outgoing_dependencies": [],
            }
        ]
    }

    layer_only_result = analyze_snapshot_drift(
        layer_only_baseline,
        layer_only_current,
    )

    assert layer_only_result["has_drift"] is True

    assert (
        layer_only_result["module_drift"]["added_count"]
        == 0
    )

    assert (
        layer_only_result["module_drift"]["removed_count"]
        == 0
    )

    assert (
        layer_only_result["dependency_drift"]["changed_count"]
        == 0
    )

    assert (
        layer_only_result["layer_drift"]["changed_count"]
        == 1
    )

    assert (
        layer_only_result["layer_drift"]["changed_modules"]
        == [
            {
                "file": "src/config.py",
                "baseline_layer": "configuration",
                "current_layer": "source",
            }
        ]
    )




   


    print("Snapshot loader verification passed.")
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

def test_snapshot_pair_is_deterministic_when_mtimes_match(tmp_path):
    from ingestion.snapshot_loader import find_snapshot_pair
    older = tmp_path / "snapshot_20260916_203726.json"
    newer = tmp_path / "snapshot_20260916_204040.json"
    older.write_text("{}", encoding="utf-8")
    newer.write_text("{}", encoding="utf-8")
    import os
    os.utime(older, (1000, 1000))
    os.utime(newer, (1000, 1000))
    baseline, current = find_snapshot_pair(str(tmp_path))
    assert baseline.endswith("snapshot_20260916_203726.json")
    assert current.endswith("snapshot_20260916_204040.json")
