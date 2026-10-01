from pathlib import Path
import json

import pytest

from app.repository_service import RepositoryService
from llm.fake_provider import FakeLLMProvider


def create_artifacts(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    analysis = {
        "metadata": {
            "python_files": 3,
        },
        "relevant_files": [
            "a.py",
            "b.py",
        ],
        "architecture": {
            "production_modules": [
                "a",
                "b",
            ],
            "graph_summary": {
                "node_count": 2,
                "edge_count": 1,
            },
            "layer_summary": {
                "source": 2,
            },
            "layer_percentages": {
                "source": 100.0,
            },
        },
        "dependency_graph": {
            "edges": [
                {
                    "source": "a",
                    "target": "b",
                }
            ],
        },
        "risks": {
            "risk_signals": [
                {
                    "type": "high_connectivity",
                }
            ],
        },
    }

    chunks = [
        {
            "file": "a.py",
            "start_line": 1,
            "end_line": 10,
            "content": "def hello(): return 'hello'",
            "symbols": ["hello"],
        }
    ]

    snapshot = {
        "modules": [
            "a",
            "b",
        ]
    }

    (artifacts / "repository_analysis.json").write_text(
        json.dumps(analysis),
        encoding="utf-8",
    )

    (artifacts / "repository_chunks.json").write_text(
        json.dumps(chunks),
        encoding="utf-8",
    )

    (artifacts / "architecture_snapshot.json").write_text(
        json.dumps(snapshot),
        encoding="utf-8",
    )

    return tmp_path


def test_repository_service_loads_analysis(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    analysis = service.load_analysis()

    assert isinstance(analysis, dict)
    assert analysis["metadata"]["python_files"] == 3


def test_repository_service_loads_chunks(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    chunks = service.load_chunks()

    assert isinstance(chunks, list)
    assert len(chunks) == 1
    assert chunks[0]["file"] == "a.py"


def test_repository_service_loads_snapshot(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    snapshot = service.load_snapshot()

    assert snapshot is not None
    assert snapshot["modules"] == ["a", "b"]


def test_repository_service_returns_overview(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    overview = service.get_repository_overview()

    assert overview["relevant_file_count"] == 2
    assert overview["python_file_count"] == 3
    assert overview["production_module_count"] == 2
    assert overview["dependency_edge_count"] == 1

    assert overview["architecture"]["node_count"] == 2
    assert overview["architecture"]["edge_count"] == 1

    assert overview["risk"]["signal_count"] == 1


def test_repository_service_ask(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    provider = FakeLLMProvider(
        response="The repository contains a hello function."
    )

    result = service.ask(
        query="What does hello do?",
        provider=provider,
    )

    assert isinstance(result, dict)
    assert "answer" in result
    assert "status" in result
    assert "evidence" in result


def test_repository_service_rejects_empty_query(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    provider = FakeLLMProvider()

    with pytest.raises(ValueError):
        service.ask(
            query="   ",
            provider=provider,
        )


def test_repository_service_rejects_invalid_top_k(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    provider = FakeLLMProvider()

    with pytest.raises(ValueError):
        service.ask(
            query="hello",
            provider=provider,
            top_k=0,
        )


def test_repository_service_rejects_invalid_neighbors(tmp_path):
    root = create_artifacts(tmp_path)

    service = RepositoryService(root)

    provider = FakeLLMProvider()

    with pytest.raises(ValueError):
        service.ask(
            query="hello",
            provider=provider,
            max_neighbors=-1,
        )


def test_repository_service_missing_analysis_fails(tmp_path):
    artifacts = tmp_path / "artifacts"
    artifacts.mkdir()

    service = RepositoryService(tmp_path)

    with pytest.raises(FileNotFoundError):
        service.load_analysis()

def test_repository_service_uses_latest_timestamped_snapshot_when_canonical_snapshot_is_missing(tmp_path: Path):
    artifacts = tmp_path / "artifacts"
    snapshots = artifacts / "architecture_snapshots"
    snapshots.mkdir(parents=True)
    (snapshots / "snapshot_20260916_204040.json").write_text(
        json.dumps({
            "metadata": {"repository_name": "requests"},
            "production_modules": [],
            "graph_summary": {
                "node_count": 1,
                "edge_count": 0,
                "top_connected_nodes": [],
            },
        }),
        encoding="utf-8",
    )
    (artifacts / "repository_analysis.json").write_text("{}", encoding="utf-8")
    (artifacts / "repository_chunks.json").write_text("[]", encoding="utf-8")

    service = RepositoryService(tmp_path)
    snapshot = service.load_snapshot()

    assert snapshot["metadata"]["repository_name"] == "requests"
