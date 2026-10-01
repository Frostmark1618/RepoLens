
from ingestion.risk_analyzer import (
    analyze_architecture_risks,
    classify_risk_severity,
    detect_architecture_hotspots,
)


def main():
    # Severity classification tests
    assert classify_risk_severity(8) == "medium"
    assert classify_risk_severity(14) == "medium"

    assert classify_risk_severity(15) == "high"
    assert classify_risk_severity(24) == "high"

    assert classify_risk_severity(25) == "critical"
    assert classify_risk_severity(40) == "critical"

    architecture_modules = [
        {
            "file": "src/a.py",
            "module_name": "a",
            "type": "production",
            "incoming_count": 3,
            "outgoing_count": 2,
            "total_connections": 5,
            "incoming_dependencies": [
                "src/x.py",
                "src/y.py",
                "src/z.py",
            ],
            "outgoing_dependencies": [
                "src/b.py",
                "src/c.py",
            ],
        },
        {
            "file": "src/b.py",
            "module_name": "b",
            "type": "production",
            "incoming_count": 6,
            "outgoing_count": 4,
            "total_connections": 10,
            "incoming_dependencies": [
                "src/a.py",
                "src/c.py",
                "src/d.py",
                "src/e.py",
                "src/f.py",
                "src/g.py",
            ],
            "outgoing_dependencies": [
                "src/a.py",
                "src/c.py",
                "src/d.py",
                "src/e.py",
            ],
        },
        {
            "file": "src/c.py",
            "module_name": "c",
            "type": "production",
            "incoming_count": 5,
            "outgoing_count": 10,
            "total_connections": 15,
            "incoming_dependencies": [
                "src/a.py",
                "src/b.py",
                "src/d.py",
                "src/e.py",
                "src/f.py",
            ],
            "outgoing_dependencies": [
                "src/a.py",
                "src/b.py",
                "src/d.py",
                "src/e.py",
                "src/f.py",
                "src/g.py",
                "src/h.py",
                "src/i.py",
                "src/j.py",
                "src/k.py",
            ],
        },
        {
            "file": "src/d.py",
            "module_name": "d",
            "type": "production",
            "incoming_count": 1,
            "outgoing_count": 1,
            "total_connections": 2,
            "incoming_dependencies": [
                "src/c.py",
            ],
            "outgoing_dependencies": [
                "src/c.py",
            ],
        },
        {
            "file": "src/e.py",
            "module_name": "e",
            "type": "production",
            "incoming_count": 15,
            "outgoing_count": 10,
            "total_connections": 25,
            "incoming_dependencies": [
                "src/a.py",
                "src/b.py",
                "src/c.py",
                "src/d.py",
                "src/f.py",
                "src/g.py",
                "src/h.py",
                "src/i.py",
                "src/j.py",
                "src/k.py",
                "src/l.py",
                "src/m.py",
                "src/n.py",
                "src/o.py",
                "src/p.py",
            ],
            "outgoing_dependencies": [
                "src/a.py",
                "src/b.py",
                "src/c.py",
                "src/d.py",
                "src/f.py",
                "src/g.py",
                "src/h.py",
                "src/i.py",
                "src/j.py",
                "src/k.py",
            ],
        },
    ]

    hotspots = detect_architecture_hotspots(
        architecture_modules,
        minimum_connections=8,
    )

    # a.py and d.py should not be detected.
    assert len(hotspots) == 3

    assert hotspots[0]["file"] == "src/e.py"
    assert hotspots[1]["file"] == "src/c.py"
    assert hotspots[2]["file"] == "src/b.py"

    # Verify severity levels.
    assert hotspots[0]["severity"] == "critical"
    assert hotspots[1]["severity"] == "high"
    assert hotspots[2]["severity"] == "medium"

    # Verify signal metadata.
    for hotspot in hotspots:
        assert hotspot["signal"] == "high_connectivity"
        assert hotspot["status"] == "possible_risk"

        assert "reason" in hotspot
        assert isinstance(
            hotspot["reason"],
            str,
        )
        assert hotspot["reason"]

        assert "dependency connections" in (
            hotspot["reason"]
        )

    # Verify connection information.
    assert hotspots[0]["connection_count"] == 25
    assert hotspots[0]["incoming_count"] == 15
    assert hotspots[0]["outgoing_count"] == 10

    assert hotspots[1]["connection_count"] == 15
    assert hotspots[1]["incoming_count"] == 5
    assert hotspots[1]["outgoing_count"] == 10

    assert hotspots[2]["connection_count"] == 10
    assert hotspots[2]["incoming_count"] == 6
    assert hotspots[2]["outgoing_count"] == 4

    # Verify evidence for the highest-risk signal.
    assert hotspots[0]["evidence"]["file"] == (
        "src/e.py"
    )

    assert (
        hotspots[0]["evidence"]["incoming_count"]
        == 15
    )

    assert (
        hotspots[0]["evidence"]["outgoing_count"]
        == 10
    )

    assert (
        hotspots[0]["evidence"]["total_connections"]
        == 25
    )

    assert (
        hotspots[0]["evidence"][
            "incoming_dependencies"
        ]
        == architecture_modules[4][
            "incoming_dependencies"
        ]
    )

    assert (
        hotspots[0]["evidence"][
            "outgoing_dependencies"
        ]
        == architecture_modules[4][
            "outgoing_dependencies"
        ]
    )

    result = analyze_architecture_risks(
        architecture_modules
    )

    assert result["risk_signal_count"] == 3
    assert result["risk_signals"] == hotspots

    print(
        "Risk analyzer unit verification passed."
    )
    print(
        f"Risk signals: "
        f"{result['risk_signal_count']}"
    )
    print(
        "Hotspots:",
        [
            item["file"]
            for item in result["risk_signals"]
        ],
    )

def test_risk_explanation_contract():
    from ingestion.risk_analyzer import (
        analyze_architecture_risks,
    )

    architecture_modules = [
        {
            "file": "src\\requests\\models.py",
            "module_name": "requests.models",
            "incoming_count": 10,
            "outgoing_count": 10,
            "total_connections": 20,
            "incoming_dependencies": [
                "requests.sessions",
            ],
            "outgoing_dependencies": [
                "requests.compat",
            ],
        }
    ]

    result = analyze_architecture_risks(
        architecture_modules
    )

    assert result["risk_signal_count"] == 1

    signal = result["risk_signals"][0]

    assert signal["status"] == "possible_risk"
    assert signal["signal"] == "high_connectivity"

    assert isinstance(
        signal["reason"],
        str,
    )
    assert signal["reason"]

    assert (
        "20 dependency connections"
        in signal["reason"]
    )

    assert (
        "10 incoming"
        in signal["reason"]
    )

    assert (
        "10 outgoing"
        in signal["reason"]
    )

    assert signal["evidence"]["file"] == (
        "src\\requests\\models.py"
    )

    assert signal["module_name"] == (
    "requests.models"
)

    assert (
        signal["evidence"]["total_connections"]
        == 20
    )

    print(
        "Risk explanation contract passed."
    )


if __name__ == "__main__":
    main()

