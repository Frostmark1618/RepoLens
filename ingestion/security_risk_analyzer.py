from pathlib import Path


SECRET_NAME_HINTS = {
    "password",
    "passwd",
    "secret",
    "api_key",
    "apikey",
    "access_key",
    "private_key",
    "auth_token",
    "access_token",
}


PLACEHOLDER_VALUES = {
    "",
    "password",
    "secret",
    "token",
    "changeme",
    "change_me",
    "example",
    "test",
    "dummy",
    "placeholder",
    "your_password",
    "your_secret",
    "your_token",
}


def _looks_like_secret_name(name: str) -> bool:
    normalized = name.strip().lower()

    return any(
        hint in normalized
        for hint in SECRET_NAME_HINTS
    )


def _is_test_or_example_file(file_path: str) -> bool:
    path = Path(file_path)

    parts = {
        part.lower()
        for part in path.parts
    }

    name = path.name.lower()

    return (
        "test" in parts
        or "tests" in parts
        or name.startswith("test_")
        or name.endswith("_test.py")
        or "example" in name
    )


def _looks_like_placeholder(value: str) -> bool:
    normalized = value.strip().lower()

    return normalized in PLACEHOLDER_VALUES


def detect_hardcoded_secret_risks(
    assignments: list[dict],
) -> list[dict]:
    """Detect conservative possible hardcoded-secret risks."""

    if not isinstance(
        assignments,
        list,
    ):
        raise TypeError(
            "Assignments must be a list."
        )

    risk_signals = []

    for assignment in assignments:
        if not isinstance(
            assignment,
            dict,
        ):
            raise TypeError(
                "Each assignment must be a dictionary."
            )

        file = assignment.get("file")
        line = assignment.get("line")
        name = assignment.get("name")
        value = assignment.get("value")

        if not isinstance(file, str):
            raise TypeError(
                "Assignment file must be a string."
            )

        if not isinstance(line, int):
            raise TypeError(
                "Assignment line must be an integer."
            )

        if not isinstance(name, str):
            raise TypeError(
                "Assignment name must be a string."
            )

        if not isinstance(value, str):
            raise TypeError(
                "Assignment value must be a string."
            )

        if _is_test_or_example_file(file):
            continue

        if not _looks_like_secret_name(name):
            continue

        if _looks_like_placeholder(value):
            continue

        risk_signals.append(
            {
                "category": "security",
                "signal": "possible_hardcoded_secret",
                "status": "possible_risk",
                "file": file,
                "line": line,
                "name": name,
                "evidence": {
                    "file": file,
                    "line": line,
                    "name": name,
                },
            }
        )

    return risk_signals


if __name__ == "__main__":
    print(
        "Security risk analyzer module loaded successfully."
    )
