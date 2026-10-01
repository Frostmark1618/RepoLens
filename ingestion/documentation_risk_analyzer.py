def detect_missing_module_documentation(
    modules: list[dict],
) -> list[dict]:
    if not isinstance(modules, list):
        raise TypeError(
            "Modules must be a list."
        )

    risks = []

    for module in modules:
        if not isinstance(module, dict):
            raise TypeError(
                "Each module must be a dictionary."
            )

        file = module.get("file")
        module_name = module.get("module_name")
        has_docstring = module.get(
            "has_docstring"
        )

        if not isinstance(file, str):
            raise TypeError(
                "Module file must be a string."
            )

        if not isinstance(module_name, str):
            raise TypeError(
                "Module name must be a string."
            )

        if not isinstance(has_docstring, bool):
            raise TypeError(
                "has_docstring must be a boolean."
            )

        if has_docstring:
            continue

        risks.append(
            {
                "category": "documentation",
                "signal": "missing_module_documentation",
                "status": "possible_risk",
                "file": file,
                "module_name": module_name,
                "evidence": {
                    "file": file,
                    "module_name": module_name,
                    "has_docstring": False,
                },
            }
        )

    return risks