from pathlib import Path


def _test_candidates(
    production_file: str,
) -> list[str]:
    path = Path(production_file)

    if path.suffix.lower() != ".py":
        return []

    module_name = path.stem

    parts = list(path.with_suffix("").parts)

    if "src" in parts:
        src_index = parts.index("src")
        module_parts = parts[src_index + 1:]
    else:
        module_parts = parts

    if not module_parts:
        module_parts = [module_name]

    package_parts = [
        part
        for part in module_parts[:-1]
        if part
    ]

    package_name = "_".join(package_parts)

    candidates = {
        f"test_{module_name}.py",
        f"test_{package_name}_{module_name}.py"
        if package_name
        else "",
        f"test_{package_name}.py"
        if package_name
        else "",
    }

    return [
        str(Path("tests") / candidate)
        for candidate in candidates
        if candidate
    ]


def _normalize_test_path(
    file: str,
) -> str:
    return str(
        Path(file)
    ).replace("\\", "/").lower()


def _has_direct_test_counterpart(
    production_file: str,
    test_files: list[str],
) -> bool:
    normalized_tests = {
        _normalize_test_path(file)
        for file in test_files
    }

    candidates = {
        _normalize_test_path(candidate)
        for candidate in _test_candidates(
            production_file
        )
    }

    return bool(
        candidates & normalized_tests
    )


def detect_untested_production_modules(
    production_files: list[str],
    test_files: list[str],
) -> list[dict]:
    if not isinstance(
        production_files,
        list,
    ):
        raise TypeError(
            "Production files must be a list."
        )

    if not isinstance(
        test_files,
        list,
    ):
        raise TypeError(
            "Test files must be a list."
        )

    risk_signals = []

    for production_file in production_files:
        if not isinstance(
            production_file,
            str,
        ):
            raise TypeError(
                "Each production file must be a string."
            )

        production_file = production_file.strip()

        if not production_file:
            raise ValueError(
                "Production file cannot be empty."
            )

        candidates = _test_candidates(
            production_file
        )

        if not candidates:
            continue

        if _has_direct_test_counterpart(
            production_file,
            test_files,
        ):
            continue

        risk_signals.append(
            {
                "category": "testing",
                "signal": "missing_test_counterpart",
                "status": "possible_risk",
                "file": production_file,
                "evidence": {
                    "production_file": production_file,
                    "expected_test_files": candidates,
                    "test_detection_scope": (
                        "direct_test_counterpart"
                    ),
                },
            }
        )

    return risk_signals


def detect_unreferenced_production_modules(
    production_modules: list[dict],
    test_references: dict[str, set[str]],
) -> list[dict]:
    if not isinstance(
        production_modules,
        list,
    ):
        raise TypeError(
            "Production modules must be a list."
        )

    if not isinstance(
        test_references,
        dict,
    ):
        raise TypeError(
            "Test references must be a dictionary."
        )

    risk_signals = []

    for module in production_modules:
        if not isinstance(module, dict):
            raise TypeError(
                "Each production module must be a dictionary."
            )

        file = module.get("file")
        module_name = module.get("module_name")

        if not isinstance(file, str):
            raise TypeError(
                "Production module file must be a string."
            )

        if not isinstance(module_name, str):
            raise TypeError(
                "Production module module_name "
                "must be a string."
            )

        references = test_references.get(
            file,
            set(),
        )

        if not isinstance(references, set):
            raise TypeError(
                "Test references for each module "
                "must be a set."
            )

        if references:
            continue

        risk_signals.append(
            {
                "category": "testing",
                "signal": "unreferenced_production_module",
                "status": "possible_risk",
                "file": file,
                "module_name": module_name,
                "evidence": {
                    "production_file": file,
                    "module_name": module_name,
                    "test_references": [],
                },
            }
        )

    return risk_signals