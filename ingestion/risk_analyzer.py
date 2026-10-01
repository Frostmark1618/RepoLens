
def classify_risk_severity(
    connection_count: int,
) -> str:
    """
    Classify risk severity from deterministic
    dependency connectivity.

    This is a risk-signal severity, not a confirmed
    vulnerability severity.
    """

    if connection_count >= 25:
        return "critical"

    if connection_count >= 15:
        return "high"

    return "medium"


def build_risk_reason(
    incoming_count: int,
    outgoing_count: int,
) -> str:
    """
    Build a human-readable explanation from
    deterministic dependency evidence.
    """

    total_connections = (
        incoming_count + outgoing_count
    )

    return (
        f"This module has {total_connections} "
        f"dependency connections "
        f"({incoming_count} incoming and "
        f"{outgoing_count} outgoing). "
        "High connectivity may indicate that "
        "the module is highly coupled with other "
        "production modules."
    )


def detect_architecture_hotspots(
    architecture_modules: list[dict],
    minimum_connections: int = 8,
) -> list[dict]:
    """
    Detect production modules with a high number
    of incoming and outgoing dependency connections.

    These are risk signals, not confirmed risks.
    """

    hotspots = []

    for module in architecture_modules:
        total_connections = module[
            "total_connections"
        ]

        if total_connections < minimum_connections:
            continue

        incoming_count = module[
            "incoming_count"
        ]

        outgoing_count = module[
            "outgoing_count"
        ]

        severity = classify_risk_severity(
            total_connections
        )

        hotspots.append(
            {
                "file": module["file"],
                "module_name": module["module_name"],
                "signal": "high_connectivity",
                "category": "architecture",
                "connection_count": total_connections,
                "incoming_count": incoming_count,
                "outgoing_count": outgoing_count,
                "severity": severity,
                "status": "possible_risk",
                "reason": build_risk_reason(
                    incoming_count,
                    outgoing_count,
                ),
                "evidence": {
                    "file": module["file"],
                    "incoming_dependencies": module[
                        "incoming_dependencies"
                    ],
                    "outgoing_dependencies": module[
                        "outgoing_dependencies"
                    ],
                    "incoming_count": incoming_count,
                    "outgoing_count": outgoing_count,
                    "total_connections": total_connections,
                },
            }
        )

    hotspots.sort(
        key=lambda item: (
            -item["connection_count"],
            item["file"],
        )
    )

    return hotspots


def analyze_architecture_risks(
    architecture_modules: list[dict],
) -> dict:
    """
    Run deterministic architecture risk-signal analysis.
    """

    hotspots = detect_architecture_hotspots(
        architecture_modules
    )

    return {
        "risk_signals": hotspots,
        "risk_signal_count": len(hotspots),
    }


if __name__ == "__main__":
    print(
        "Risk analyzer module loaded successfully."
    )

