def validate_code_evidence_reference(
    evidence: dict,
    chunks: list[dict],
) -> bool:
    """
    Verify that a code evidence reference points
    to an actual repository chunk.
    """

    if not isinstance(evidence, dict):
        raise TypeError(
            "Evidence must be a dictionary."
        )

    if not isinstance(chunks, list):
        raise TypeError(
            "Chunks must be a list."
        )

    if evidence.get("evidence_type") != "code":
        raise ValueError(
            "Evidence must have evidence_type 'code'."
        )

    file = evidence.get("file")
    start_line = evidence.get("start_line")
    end_line = evidence.get("end_line")

    if not isinstance(file, str) or not file.strip():
        raise ValueError(
            "Code evidence requires a file."
        )

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

    for chunk in chunks:
        if chunk.get("file") != file:
            continue

        chunk_start = chunk.get("start_line")
        chunk_end = chunk.get("end_line")

        if (
            isinstance(chunk_start, int)
            and isinstance(chunk_end, int)
            and start_line >= chunk_start
            and end_line <= chunk_end
        ):
            return True

    return False