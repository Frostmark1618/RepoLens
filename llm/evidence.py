def validate_evidence_reference(
    evidence: dict,
) -> dict:
    """
    Validate and normalize a single RepoLens
    evidence reference.
    """

    if not isinstance(evidence, dict):
        raise TypeError(
            "Evidence reference must be a dictionary."
        )

    evidence_type = evidence.get(
        "evidence_type"
    )

    if evidence_type not in {
        "code",
        "architecture",
    }:
        raise ValueError(
            "Evidence type must be "
            "'code' or 'architecture'."
        )

    if evidence_type == "code":
        file = evidence.get("file")

        if not isinstance(file, str) or not file.strip():
            raise ValueError(
                "Code evidence requires a file."
            )

        start_line = evidence.get("start_line")
        end_line = evidence.get("end_line")

        if not isinstance(start_line, int):
            raise ValueError(
                "Code evidence requires an integer "
                "start_line."
            )

        if not isinstance(end_line, int):
            raise ValueError(
                "Code evidence requires an integer "
                "end_line."
            )

        if start_line < 1:
            raise ValueError(
                "start_line must be at least 1."
            )

        if end_line < start_line:
            raise ValueError(
                "end_line cannot be smaller than "
                "start_line."
            )

    if evidence_type == "architecture":
        module_name = evidence.get(
            "module_name"
        )

        if (
            not isinstance(module_name, str)
            or not module_name.strip()
        ):
            raise ValueError(
                "Architecture evidence requires "
                "a module_name."
            )

    return evidence