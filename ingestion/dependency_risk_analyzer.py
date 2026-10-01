def detect_unresolved_internal_imports(
    dependency_records: list[dict],
) -> list[dict]:
    """
    Detect imports that appear to be internal repository
    dependencies but could not be resolved.

    External dependencies are not treated as risks.
    """

    if not isinstance(
        dependency_records,
        list,
    ):
        raise TypeError(
            "Dependency records must be a list."
        )

    risk_signals = []

    for record in dependency_records:
        if not isinstance(record, dict):
            raise TypeError(
                "Each dependency record must be a dictionary."
            )

        imported_module = record.get(
            "imported_module"
        )

        if not isinstance(
            imported_module,
            str,
        ):
            continue

        imported_module = imported_module.strip()

        if not imported_module:
            continue

        is_internal = record.get(
            "is_internal"
        )

        is_resolved = record.get(
            "is_resolved"
        )

        if is_internal is True and is_resolved is False:
            risk_signals.append(
                {
                    "category": "dependency",
                    "signal": (
                        "unresolved_internal_import"
                    ),
                    "status": "possible_risk",
                    "module": imported_module,
                    "evidence": {
                        "imported_module": imported_module,
                    },
                }
            )

    return risk_signals