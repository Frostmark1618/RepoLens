import json
import re
from pathlib import Path




_SNAPSHOT_NAME_PATTERN = re.compile(
    r"^snapshot_(?P<timestamp>\d{8}_\d{6})\.json$"
)


def _snapshot_sort_key(path: Path) -> tuple[str, str]:
    """Sort snapshots by their embedded creation timestamp, not filesystem mtime."""
    match = _SNAPSHOT_NAME_PATTERN.match(path.name)
    if match:
        return (match.group("timestamp"), path.name)
    # Unknown names sort before versioned snapshots while remaining deterministic.
    return ("", path.name)

def load_architecture_snapshot(
    snapshot_path: str,
) -> dict:
    """
    Load an architecture snapshot from a JSON file.
    """

    snapshot_file = Path(snapshot_path)

    if not snapshot_file.exists():
        raise FileNotFoundError(
            f"Architecture snapshot not found: "
            f"{snapshot_file}"
        )

    if not snapshot_file.is_file():
        raise NotADirectoryError(
            f"Architecture snapshot path is not a file: "
            f"{snapshot_file}"
        )

    with snapshot_file.open(
        "r",
        encoding="utf-8",
    ) as file:
        snapshot = json.load(file)

    return snapshot


def find_latest_architecture_snapshot(
    snapshot_directory: str,
) -> str | None:
    """
    Find the newest versioned architecture snapshot.
    """

    snapshot_dir = Path(snapshot_directory)

    if not snapshot_dir.exists():
        return None

    if not snapshot_dir.is_dir():
        raise NotADirectoryError(
            f"Snapshot directory path is not a directory: "
            f"{snapshot_dir}"
        )

    snapshots = sorted(
        snapshot_dir.glob(
            "snapshot_*.json"
        )
    )

    if not snapshots:
        return None

    latest_snapshot = max(
        snapshots,
        key=_snapshot_sort_key,
    )

    return str(latest_snapshot)


if __name__ == "__main__":
    print(
        "Snapshot loader module loaded successfully."
    )


def find_snapshot_pair(
    snapshot_directory: str,
) -> tuple[str | None, str | None]:
    """
    Find the two newest versioned architecture snapshots.

    Returns:
        (baseline_snapshot, current_snapshot)
    """

    snapshot_dir = Path(
        snapshot_directory
    )

    if not snapshot_dir.exists():
        return None, None

    if not snapshot_dir.is_dir():
        raise NotADirectoryError(
            f"Snapshot directory path is not a directory: "
            f"{snapshot_dir}"
        )

    snapshots = sorted(
        snapshot_dir.glob(
            "snapshot_*.json"
        ),
        key=_snapshot_sort_key,
    )

    if len(snapshots) < 2:
        return None, None

    baseline = snapshots[-2]
    current = snapshots[-1]

    return (
        str(baseline),
        str(current),
    )