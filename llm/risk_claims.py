from dataclasses import dataclass

from llm.claims import AnswerClaim


@dataclass
class RiskClaim(AnswerClaim):
    """
    Specialized repository claim for architecture
    risk signals.

    Extends the generic AnswerClaim with
    risk-specific category and severity metadata.
    """

    category: str | None = None
    severity: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()

        if not isinstance(self.category, str):
            raise TypeError(
                "Risk claim category must be a string."
            )

        self.category = self.category.strip().lower()

        allowed_categories = {
            "architecture",
            "security",
            "dependency",
            "testing",
            "documentation",
        }

        if self.category not in allowed_categories:
            raise ValueError(
                "Risk claim category must be one of: "
                "architecture, security, dependency, "
                "testing, documentation."
            )

        if not isinstance(self.severity, str):
            raise TypeError(
                "Risk claim severity must be a string."
            )

        self.severity = self.severity.strip().lower()

        allowed_severities = {
            "critical",
            "high",
            "medium",
        }

        if self.severity not in allowed_severities:
            raise ValueError(
                "Risk claim severity must be one of: "
                "critical, high, medium."
            )


def _get_severity(
    risk_signal: dict,
    default: str = "medium",
) -> str:
    severity = risk_signal.get(
        "severity",
        default,
    )

    if not isinstance(severity, str):
        raise TypeError(
            "Risk signal severity must be a string."
        )

    severity = severity.strip().lower()

    if severity not in {
        "critical",
        "high",
        "medium",
    }:
        raise ValueError(
            "Risk signal severity must be one of: "
            "critical, high, medium."
        )

    return severity


def _require_non_empty_string(
    risk_signal: dict,
    field_name: str,
) -> str:
    value = risk_signal.get(field_name)

    if not isinstance(value, str):
        raise TypeError(
            f"Risk signal {field_name} must be a string."
        )

    value = value.strip()

    if not value:
        raise ValueError(
            f"Risk signal {field_name} cannot be empty."
        )

    return value


def build_risk_claim(
    risk_signal: dict,
) -> RiskClaim:
    """
    Convert a deterministic repository risk signal
    into an evidence-backed POSSIBLE_RISK claim.
    """

    if not isinstance(risk_signal, dict):
        raise TypeError(
            "Risk signal must be a dictionary."
        )

    status = risk_signal.get("status")
    signal = risk_signal.get("signal")

    if status != "possible_risk":
        raise ValueError(
            "Risk signal status must be "
            "'possible_risk'."
        )

    if signal == "circular_dependency":
        cycle = risk_signal.get("cycle")

        if not isinstance(cycle, list):
            raise TypeError(
                "Circular dependency cycle must be a list."
            )

        if len(cycle) < 2:
            raise ValueError(
                "Circular dependency cycle must contain "
                "at least two modules."
            )

        if not all(
            isinstance(node, str) and node.strip()
            for node in cycle
        ):
            raise TypeError(
                "Circular dependency cycle nodes "
                "must be non-empty strings."
            )

        evidence_data = risk_signal.get("evidence")

        if not isinstance(evidence_data, dict):
            raise TypeError(
                "Circular dependency evidence "
                "must be a dictionary."
            )

        nodes = evidence_data.get("nodes")
        edges = evidence_data.get("edges")

        if nodes != cycle:
            raise ValueError(
                "Circular dependency evidence nodes "
                "must match the cycle."
            )

        if not isinstance(edges, list):
            raise TypeError(
                "Circular dependency evidence edges "
                "must be a list."
            )

        evidence = [
            {
                "evidence_type": "architecture",
                "file": None,
                "module_name": None,
                "start_line": None,
                "end_line": None,
                "nodes": nodes,
                "edges": edges,
            }
        ]

        claim_text = (
            "Circular dependency detected across "
            f"{len(cycle)} production modules: "
            f"{', '.join(cycle)}."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="architecture",
            severity=_get_severity(
                risk_signal,
                "high",
            ),
        )

    if signal == "high_connectivity":
        module_name = _require_non_empty_string(
            risk_signal,
            "module_name",
        )

        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        reason = _require_non_empty_string(
            risk_signal,
            "reason",
        )

        evidence_data = risk_signal.get("evidence")

        if not isinstance(evidence_data, dict):
            raise TypeError(
                "Risk signal evidence must be a dictionary."
            )

        evidence_file = evidence_data.get("file")

        if not isinstance(evidence_file, str):
            raise TypeError(
                "Risk evidence file must be a string."
            )

        evidence_file = evidence_file.strip()

        if not evidence_file:
            raise ValueError(
                "Risk evidence file cannot be empty."
            )

        connection_count = risk_signal.get(
            "connection_count"
        )

        if not isinstance(connection_count, int):
            raise TypeError(
                "Risk signal connection_count "
                "must be an integer."
            )

        if connection_count < 0:
            raise ValueError(
                "Risk signal connection_count "
                "cannot be negative."
            )

        evidence = [
            {
                "evidence_type": "architecture",
                "file": evidence_file,
                "module_name": module_name,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            f"{module_name} has "
            f"{connection_count} "
            "dependency connections. "
            f"{reason}"
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="architecture",
            severity=_get_severity(
                risk_signal,
            ),
        )

    if signal == "architecture_drift":
        drift_type = risk_signal.get(
            "drift_type"
        )

        if drift_type != "removed_module":
            raise ValueError(
                "Architecture drift type must be "
                "'removed_module'."
            )

        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        evidence = [
            {
                "evidence_type": "architecture",
                "file": file,
                "module_name": None,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            "Architecture drift detected: "
            "production module "
            f"{file} was removed between snapshots."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="architecture",
            severity=_get_severity(
                risk_signal,
                "high",
            ),
        )

    if signal == "missing_test_counterpart":
        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        module_name = risk_signal.get(
            "module_name"
        )

        if module_name is not None:
            if not isinstance(module_name, str):
                raise TypeError(
                    "Risk signal module_name must be "
                    "a string or None."
                )

            module_name = module_name.strip()

        evidence = [
            {
                "evidence_type": "testing",
                "file": file,
                "module_name": module_name,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            f"Production module {file} has no "
            "detected test counterpart."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="testing",
            severity=_get_severity(
                risk_signal,
            ),
        )

    if signal == "layer_violation":
        source = _require_non_empty_string(
            risk_signal,
            "source",
        )

        target = _require_non_empty_string(
            risk_signal,
            "target",
        )

        source_layer = _require_non_empty_string(
            risk_signal,
            "source_layer",
        )

        target_layer = _require_non_empty_string(
            risk_signal,
            "target_layer",
        )

        evidence_data = risk_signal.get("evidence")

        if not isinstance(evidence_data, dict):
            raise TypeError(
                "Layer violation evidence "
                "must be a dictionary."
            )

        evidence = [
            {
                "evidence_type": "architecture",
                "file": source,
                "module_name": source,
                "target": target,
                "source_layer": source_layer,
                "target_layer": target_layer,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            "Architecture layer violation detected: "
            f"{source} ({source_layer}) depends on "
            f"{target} ({target_layer})."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="architecture",
            severity=_get_severity(
                risk_signal,
            ),
        )

    if signal == "unresolved_internal_import":
        module = _require_non_empty_string(
            risk_signal,
            "module",
        )

        evidence_data = risk_signal.get("evidence")

        if not isinstance(evidence_data, dict):
            raise TypeError(
                "Unresolved dependency evidence "
                "must be a dictionary."
            )

        evidence_file = evidence_data.get("file")

        if not isinstance(evidence_file, str):
            raise TypeError(
                "Dependency evidence file "
                "must be a string."
            )

        evidence_file = evidence_file.strip()

        if not evidence_file:
            raise ValueError(
                "Dependency evidence file "
                "cannot be empty."
            )

        evidence = [
            {
                "evidence_type": "dependency",
                "file": evidence_file,
                "module_name": module,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            "Unresolved internal dependency detected "
            f"for module {module}."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="dependency",
            severity=_get_severity(
                risk_signal,
            ),
        )

    if signal == "possible_hardcoded_secret":
        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        evidence_data = risk_signal.get("evidence")

        if not isinstance(evidence_data, dict):
            raise TypeError(
                "Hardcoded secret evidence "
                "must be a dictionary."
            )

        evidence_file = evidence_data.get("file")

        if not isinstance(evidence_file, str):
            raise TypeError(
                "Security evidence file "
                "must be a string."
            )

        evidence_file = evidence_file.strip()

        if not evidence_file:
            raise ValueError(
                "Security evidence file "
                "cannot be empty."
            )

        evidence = [
            {
                "evidence_type": "security",
                "file": evidence_file,
                "module_name": None,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            "Possible hardcoded secret detected in "
            f"{file}."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="security",
            severity=_get_severity(
                risk_signal,
            ),
        )

    if signal == "dynamic_code_execution":
        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        function = risk_signal.get(
            "function"
        )

        if function is not None:
            if not isinstance(function, str):
                raise TypeError(
                    "Dynamic execution function "
                    "must be a string or None."
                )

            function = function.strip()

        line = risk_signal.get("line")

        if not isinstance(line, int):
            raise TypeError(
                "Dynamic execution line "
                "must be an integer."
            )

        evidence = [
            {
                "evidence_type": "security",
                "file": file,
                "module_name": function,
                "start_line": line,
                "end_line": line,
            }
        ]

        claim_text = (
            "Dynamic code execution detected in "
            f"{file}"
        )

        if function:
            claim_text += (
                f" within function {function}"
            )

        claim_text += "."

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="security",
            severity=_get_severity(
                risk_signal,
                "high",
            ),
        )

    if signal == "missing_module_documentation":
        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        module_name = risk_signal.get(
            "module_name"
        )

        if not isinstance(module_name, str):
            raise TypeError(
                "Documentation risk module_name "
                "must be a string."
            )

        module_name = module_name.strip()

        if not module_name:
            raise ValueError(
                "Documentation risk module_name "
                "cannot be empty."
            )

        evidence = [
            {
                "evidence_type": "documentation",
                "file": file,
                "module_name": module_name,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            f"Production module {module_name} "
            f"({file}) has no detected module "
            "documentation."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="documentation",
            severity=_get_severity(
                risk_signal,
            ),
        )

    if signal == "unreferenced_production_module":
        file = _require_non_empty_string(
            risk_signal,
            "file",
        )

        module_name = risk_signal.get(
            "module_name"
        )

        if not isinstance(module_name, str):
            raise TypeError(
                "Unreferenced module module_name "
                "must be a string."
            )

        module_name = module_name.strip()

        if not module_name:
            raise ValueError(
                "Unreferenced module module_name "
                "cannot be empty."
            )

        evidence = [
            {
                "evidence_type": "testing",
                "file": file,
                "module_name": module_name,
                "start_line": None,
                "end_line": None,
            }
        ]

        claim_text = (
            f"Production module {module_name} "
            f"({file}) has no detected test "
            "reference."
        )

        return RiskClaim(
            text=claim_text,
            status="possible_risk",
            evidence=evidence,
            category="testing",
            severity=_get_severity(
                risk_signal,
            ),
        )

    raise ValueError(
        "Unsupported risk signal type: "
        f"{signal!r}."
    )