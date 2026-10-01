def detect_unreferenced_production_modules(
    production_modules: list[dict],
    test_references: dict[str, set[str]],
) -> list[dict]:
    if not isinstance(production_modules, list):
        raise TypeError(
            "Production modules must be a list."
        )

    if not isinstance(test_references, dict):
        raise TypeError(
            "Test references must be a dictionary."
        )

    risks = []

    for module in production_modules:
        if not isinstance(module, dict):
            raise TypeError(
                "Each production module must be a dictionary."
            )

        module_name = module.get("module_name")
        file = module.get("file")

        if not isinstance(module_name, str):
            raise TypeError(
                "Production module_name must be a string."
            )

        if not isinstance(file, str):
            raise TypeError(
                "Production module file must be a string."
            )

        references = test_references.get(
            module_name,
            set(),
        )

        if references:
            continue

        risks.append(
            {
                "category": "testing",
                "signal": "unreferenced_production_module",
                "status": "possible_risk",
                "file": file,
                "module_name": module_name,
                "evidence": {
                    "file": file,
                    "module_name": module_name,
                    "test_references": [],
                },
            }
        )

    return risks