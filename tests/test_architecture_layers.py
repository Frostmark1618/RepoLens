from ingestion.architecture_layers import (
    calculate_layer_percentages,
    classify_architecture_layer,
    summarize_architecture_layers,
)


def main() -> None:

    test_data = [
        {
            "file": "src/requests/models.py",
            "layer": "source",
        },
        {
            "file": "src/requests/sessions.py",
            "layer": "source",
        },
        {
            "file": "tests/test_models.py",
            "layer": "test",
        },
        {
            "file": "docs/index.md",
            "layer": "documentation",
        },
        {
            "file": "setup.py",
            "layer": "configuration",
        },
    ]

    summary = summarize_architecture_layers(
        test_data
    )

    assert summary == {
        "configuration": 1,
        "documentation": 1,
        "source": 2,
        "test": 1,
    }

    assert sum(
        summary.values()
    ) == len(test_data)


    percentages = calculate_layer_percentages(
        summary
    )

    assert percentages == {
        "configuration": 20.0,
        "documentation": 20.0,
        "source": 40.0,
        "test": 20.0,
    }

    assert round(
        sum(percentages.values()),
        2,
    ) == 100.0

    init_layer = classify_architecture_layer(
        "src/requests/__init__.py"
    )

    assert init_layer == "source"

    print(
        "Architecture layer summary verification passed."
    )

    print(
        f"Layer summary: {summary}"
    )


if __name__ == "__main__":
    main()