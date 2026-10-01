from retrieval.architecture_evidence import (
    retrieve_architecture_evidence,
)


def test_session_dependency_evidence():
    snapshot = {
        "production_modules": [
            {
                "file": "src\\requests\\sessions.py",
                "module_name": "requests.sessions",
                "type": "production",
                "layer": "source",
                "outgoing_dependencies": [
                    "src\\requests\\adapters.py",
                    "src\\requests\\models.py",
                ],
                "incoming_dependencies": [
                    "src\\requests\\api.py",
                ],
                "outgoing_count": 2,
                "incoming_count": 1,
                "total_connections": 3,
            },
            {
                "file": "src\\requests\\models.py",
                "module_name": "requests.models",
                "type": "production",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 0,
                "incoming_count": 0,
                "total_connections": 0,
            },
        ]
    }

    results = retrieve_architecture_evidence(
        "session dependencies",
        snapshot,
        top_k=5,
    )

    assert len(results) == 1

    result = results[0]

    assert result["module_name"] == "requests.sessions"
    assert result["file"] == (
        "src\\requests\\sessions.py"
    )
    assert result["layer"] == "source"

    assert result["outgoing_count"] == 2
    assert result["incoming_count"] == 1
    assert result["total_connections"] == 3

    assert result["status"] == "fact"
    assert result["evidence_type"] == "architecture"
    assert result["evidence_subtype"] == (
        "module_dependencies"
    )


def test_module_query_supports_plural_variation():
    snapshot = {
        "production_modules": [
            {
                "file": "src\\requests\\models.py",
                "module_name": "requests.models",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 0,
                "incoming_count": 0,
                "total_connections": 0,
            }
        ]
    }

    results = retrieve_architecture_evidence(
        "models dependencies",
        snapshot,
        top_k=5,
    )

    assert len(results) == 1
    assert results[0]["module_name"] == (
        "requests.models"
    )


def test_unrelated_query_returns_no_architecture_evidence():
    snapshot = {
        "production_modules": [
            {
                "file": "src\\requests\\sessions.py",
                "module_name": "requests.sessions",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 0,
                "incoming_count": 0,
                "total_connections": 0,
            }
        ]
    }

    results = retrieve_architecture_evidence(
        "database migrations",
        snapshot,
        top_k=5,
    )

    assert results == []


def test_architecture_evidence_respects_top_k():
    snapshot = {
        "production_modules": [
            {
                "file": "src\\requests\\sessions.py",
                "module_name": "requests.sessions",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 12,
                "incoming_count": 1,
                "total_connections": 13,
            },
            {
                "file": "src\\requests\\models.py",
                "module_name": "requests.models",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 10,
                "incoming_count": 2,
                "total_connections": 12,
            },
        ]
    }

    results = retrieve_architecture_evidence(
        "requests",
        snapshot,
        top_k=1,
    )

    assert len(results) == 1
    assert results[0]["module_name"] == (
        "requests.sessions"
    )

def test_global_connectivity_ranking_recomputes_from_production_module_facts():
    snapshot = {
        "production_modules": [
            {
                "file": "src\\requests\\models.py",
                "module_name": "requests.models",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 10,
                "incoming_count": 10,
                "total_connections": 20,
            },
            {
                "file": "src\\requests\\sessions.py",
                "module_name": "requests.sessions",
                "layer": "source",
                "outgoing_dependencies": [],
                "incoming_dependencies": [],
                "outgoing_count": 1,
                "incoming_count": 1,
                "total_connections": 2,
            },
        ],
        "graph_summary": {
            "node_count": 2,
            "edge_count": 2,
            "isolated_node_count": 0,
            "isolated_nodes": [],
            # Deliberately stale/wrong ordering.
            "top_connected_nodes": [
                "src\\requests\\sessions.py",
                "src\\requests\\models.py",
            ],
        },
    }

    results = retrieve_architecture_evidence(
        "Which module has the highest dependency connectivity?",
        snapshot,
        top_k=5,
    )

    assert results[0]["top_connected_modules"][0]["module_name"] == (
        "requests.models"
    )
    assert results[0]["top_connected_modules"][0]["total_connections"] == 20
