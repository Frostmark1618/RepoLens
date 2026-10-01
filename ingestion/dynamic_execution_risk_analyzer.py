import ast


DANGEROUS_CALLS = {
    "eval",
    "exec",
}


def detect_dynamic_execution_risks(
    call_records: list[dict],
) -> list[dict]:
    if not isinstance(call_records, list):
        raise TypeError(
            "Call records must be a list."
        )

    risk_signals = []

    for record in call_records:
        if not isinstance(record, dict):
            raise TypeError(
                "Each call record must be a dictionary."
            )

        file = record.get("file")
        line = record.get("line")
        function = record.get("function")

        if not isinstance(file, str):
            raise TypeError(
                "Call record file must be a string."
            )

        if not isinstance(line, int):
            raise TypeError(
                "Call record line must be an integer."
            )

        if not isinstance(function, str):
            raise TypeError(
                "Call record function must be a string."
            )

        if function not in DANGEROUS_CALLS:
            continue

        risk_signals.append(
            {
                "category": "security",
                "signal": "dynamic_code_execution",
                "status": "possible_risk",
                "file": file,
                "line": line,
                "function": function,
                "evidence": {
                    "file": file,
                    "line": line,
                    "function": function,
                },
            }
        )

    return risk_signals