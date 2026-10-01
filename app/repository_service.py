import json
from pathlib import Path

from llm.base import LLMProvider
from llm.repository_qa import answer_repository_query
from ingestion.snapshot_loader import find_latest_architecture_snapshot, load_architecture_snapshot


class RepositoryService:
    """
    Application-level service for accessing an analyzed
    repository and running repository-aware operations.

    This layer intentionally does not perform repository
    analysis itself.

    It coordinates existing RepoLens core components so
    Streamlit, FastAPI, tests, and future clients can use
    the same application logic.
    """

    def __init__(
        self,
        project_root: str | Path | None = None,
    ):
        if project_root is None:
            self.project_root = (
                Path(__file__).resolve().parent.parent
            )
        else:
            self.project_root = Path(project_root)

        self.artifacts_directory = (
            self.project_root / "artifacts"
        )

        self.analysis_file = (
            self.artifacts_directory
            / "repository_analysis.json"
        )

        self.chunks_file = (
            self.artifacts_directory
            / "repository_chunks.json"
        )

        self.snapshot_file = (
            self.artifacts_directory
            / "architecture_snapshot.json"
        )

        self.snapshot_directory = (
            self.artifacts_directory
            / "architecture_snapshots"
        )

    def _load_json(
        self,
        path: Path,
    ) -> dict | list:
        if not path.exists():
            raise FileNotFoundError(
                f"Required artifact not found: {path}"
            )

        with path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    def load_analysis(self) -> dict:
        """
        Load the unified deterministic repository analysis.
        """
        analysis = self._load_json(
            self.analysis_file
        )

        if not isinstance(analysis, dict):
            raise ValueError(
                "Repository analysis must be a JSON object."
            )

        return analysis

    def get_repository_analysis(self) -> dict:
        """
        Return the complete deterministic repository analysis.

        This method keeps repository artifact access inside
        the application service layer so API clients do not
        access JSON artifacts directly.
        """
        return self.load_analysis()

    def load_chunks(self) -> list[dict]:
        """
        Load repository chunks used by retrieval.
        """
        chunks = self._load_json(
            self.chunks_file
        )

        if not isinstance(chunks, list):
            raise ValueError(
                "Repository chunks must be a JSON list."
            )

        return chunks

    def load_snapshot(self) -> dict | None:
        """
        Load the architecture snapshot if available.
        """
        snapshot_path = self.snapshot_file

        # Release artifacts may retain only timestamped architecture snapshots.
        # Prefer the canonical snapshot when present, otherwise load the newest
        # timestamped snapshot so repository Q&A remains architecture-aware after
        # a clean release/ZIP extraction.
        if not snapshot_path.exists():
            latest_snapshot = find_latest_architecture_snapshot(
                str(self.snapshot_directory)
            )
            if latest_snapshot is None:
                # The unified analysis artifact already contains the complete
                # architecture structure. Use it as a final deterministic
                # fallback when a release has no persisted snapshot file.
                analysis = self.load_analysis()
                architecture = analysis.get("architecture")
                if not isinstance(architecture, dict):
                    return None
                return architecture
            snapshot_path = Path(latest_snapshot)

        snapshot = load_architecture_snapshot(
            str(snapshot_path)
        )

        if not isinstance(snapshot, dict):
            raise ValueError(
                "Architecture snapshot must be a JSON object."
            )

        return snapshot

    def get_repository_drift(self) -> dict:
        """Compare the two newest persisted architecture snapshots.

        Drift is reported only when two real snapshots exist; otherwise the
        response explicitly remains unconfigured instead of fabricating a
        baseline.
        """
        from ingestion.drift_analyzer import analyze_snapshot_drift, build_drift_summary
        from ingestion.snapshot_loader import find_snapshot_pair, load_architecture_snapshot

        snapshot_dir = self.artifacts_directory / "architecture_snapshots"
        baseline_path, current_path = find_snapshot_pair(str(snapshot_dir))
        if not baseline_path or not current_path:
            return {
                "status": "unconfigured",
                "message": "Two architecture snapshots are required for drift comparison.",
                "baseline": None,
                "current": None,
                "drift": None,
            }

        baseline = load_architecture_snapshot(baseline_path)
        current = load_architecture_snapshot(current_path)
        drift = analyze_snapshot_drift(baseline, current)
        return {
            "status": "ready",
            "message": build_drift_summary(drift),
            "baseline": {"path": baseline_path, "created_at": baseline.get("created_at")},
            "current": {"path": current_path, "created_at": current.get("created_at")},
            "drift": drift,
        }

    def get_repository_overview(self) -> dict:
        """
        Return the stable repository overview required by
        application clients.
        """
        analysis = self.load_analysis()

        metadata = analysis.get(
            "metadata",
            {},
        )

        architecture = analysis.get(
            "architecture",
            {},
        )

        dependency_graph = analysis.get(
            "dependency_graph",
            {},
        )

        risks = analysis.get(
            "risks",
            {},
        )

        production_modules = architecture.get(
            "production_modules",
            [],
        )

        graph_summary = architecture.get(
            "graph_summary",
            {},
        )

        return {
            "metadata": metadata,
            "relevant_file_count": len(
                analysis.get(
                    "relevant_files",
                    [],
                )
            ),
            "python_file_count": metadata.get(
                "python_files",
                0,
            ),
            "production_module_count": len(
                production_modules
            ),
            "dependency_edge_count": len(
                dependency_graph.get(
                    "edges",
                    [],
                )
            ),
            "architecture": {
                "node_count": graph_summary.get(
                    "node_count",
                    0,
                ),
                "edge_count": graph_summary.get(
                    "edge_count",
                    0,
                ),
                "layer_summary": architecture.get(
                    "layer_summary",
                    {},
                ),
                "layer_percentages": architecture.get(
                    "layer_percentages",
                    {},
                ),
            },
            "risk": {
                "signal_count": len(
                    risks.get(
                        "risk_signals",
                        [],
                    )
                ),
            },
        }

    def ask(
        self,
        query: str,
        provider: LLMProvider,
        top_k: int = 5,
        max_neighbors: int = 1,
        status: str = "fact",
    ) -> dict:
        """
        Run the existing complete repository Q&A pipeline.

        This method is deliberately thin. Retrieval,
        context construction, answer generation, evidence
        validation, claim decomposition, evidence selection,
        and coverage remain inside their existing modules.
        """

        if not isinstance(query, str):
            raise TypeError(
                "Query must be a string."
            )

        if not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not isinstance(
            top_k,
            int,
        ) or top_k <= 0:
            raise ValueError(
                "top_k must be a positive integer."
            )

        if not isinstance(
            max_neighbors,
            int,
        ) or max_neighbors < 0:
            raise ValueError(
                "max_neighbors must be a non-negative integer."
            )

        analysis = self.load_analysis()
        chunks = self.load_chunks()
        snapshot = self.load_snapshot()

        return answer_repository_query(
            query=query.strip(),
            chunks=chunks,
            provider=provider,
            top_k=top_k,
            max_neighbors=max_neighbors,
            architecture_snapshot=snapshot,
            repository_analysis=analysis,
            status=status,
        )