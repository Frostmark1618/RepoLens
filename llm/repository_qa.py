import re
from llm.answer import build_answer
from llm.answer_service import generate_repository_answer
from llm.base import LLMProvider

from retrieval.context_builder import build_rag_context
from retrieval.retrieval_service import retrieve_repository_evidence
from retrieval.architecture_evidence import retrieve_architecture_evidence
from retrieval.evidence_validator import validate_code_evidence_reference
from retrieval.metadata_evidence import (
    metadata_value_from_evidence,
    retrieve_repository_metadata_evidence,
)

from llm.claim_builder import build_answer_claim
from llm.claim_decomposer import decompose_answer_into_claims
from llm.evidence_selector import (
    select_claim_evidence,
    select_context_evidence,
)
from llm.claim_verifier import (
    verify_claim,
    _deterministic_architecture_fact_check,
)
from llm.claim_coverage import calculate_claim_coverage
from llm.qa_safety import is_sensitive_value_request


def _build_claim_evidence_pool(
    retrieval_result: dict,
) -> list[dict]:
    """
    Build the complete evidence pool used for claim attribution
    and semantic verification.

    Primary evidence remains primary.
    Supporting evidence is also available because a neighboring
    chunk may contain the continuation or implementation detail
    required to verify a claim.

    Architecture evidence remains a separate evidence type.
    """

    pool: list[dict] = []

    # ---------------------------------------------------------
    # PRIMARY CODE EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "evidence",
        [],
    ):
        pool.append(
            {
                "evidence_type": "code",
                "file": item.get(
                    "file",
                    "",
                ),
                "start_line": item.get(
                    "start_line"
                ),
                "end_line": item.get(
                    "end_line"
                ),
                "content": item.get(
                    "content",
                    "",
                ),
                "retrieval_score": item.get(
                    "retrieval_score",
                    0.0,
                ),
                "retrieval_role": "primary",
                "context_role": "retrieved",
                "symbols": item.get(
                    "symbols",
                    {},
                ),
            }
        )

    # ---------------------------------------------------------
    # SUPPORTING CODE EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "supporting_evidence",
        [],
    ):
        pool.append(
            {
                "evidence_type": "code",
                "file": item.get(
                    "file",
                    "",
                ),
                "start_line": item.get(
                    "start_line"
                ),
                "end_line": item.get(
                    "end_line"
                ),
                "content": item.get(
                    "content",
                    "",
                ),
                "retrieval_score": item.get(
                    "retrieval_score",
                    0.0,
                ),
                "retrieval_role": "supporting",
                "context_role": "neighbor",
                "symbols": item.get(
                    "symbols",
                    {},
                ),
            }
        )

    # ---------------------------------------------------------
    # REPOSITORY METADATA EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "metadata_evidence",
        [],
    ):
        pool.append(
            {
                "evidence_type": "repository_metadata",
                "file": item.get("file"),
                "start_line": item.get("start_line"),
                "end_line": item.get("end_line"),
                "metadata_key": item.get("metadata_key"),
                "label": item.get("label"),
                "value": item.get("value"),
            }
        )

    # ---------------------------------------------------------
    # ARCHITECTURE EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "architecture_evidence",
        [],
    ):
        pool.append(
            {
                "evidence_type": "architecture",
                "evidence_subtype": item.get(
                    "evidence_subtype",
                    "module_dependencies",
                ),
                "file": item.get(
                    "file"
                ),
                "module_name": item.get(
                    "module_name"
                ),
                "start_line": item.get(
                    "start_line"
                ),
                "end_line": item.get(
                    "end_line"
                ),
                "content": item.get(
                    "content",
                    "",
                ),
                "node_count": item.get(
                    "node_count"
                ),
                "edge_count": item.get(
                    "edge_count"
                ),
                "isolated_node_count": item.get(
                    "isolated_node_count"
                ),
                "isolated_nodes": item.get(
                    "isolated_nodes",
                    [],
                ),
                "top_connected_nodes": item.get(
                    "top_connected_nodes",
                    [],
                ),
                "top_connected_modules": item.get(
                    "top_connected_modules",
                    [],
                ),
                "top_outgoing_modules": item.get(
                    "top_outgoing_modules",
                    [],
                ),
                "top_incoming_modules": item.get(
                    "top_incoming_modules",
                    [],
                ),
                "all_module_facts": item.get(
                    "all_module_facts",
                    [],
                ),
                "layer": item.get("layer"),
                "outgoing_dependencies": item.get(
                    "outgoing_dependencies",
                    [],
                ),
                "incoming_dependencies": item.get(
                    "incoming_dependencies",
                    [],
                ),
                "outgoing_dependency_modules": item.get(
                    "outgoing_dependency_modules",
                    [],
                ),
                "incoming_dependency_modules": item.get(
                    "incoming_dependency_modules",
                    [],
                ),
                "outgoing_count": item.get("outgoing_count"),
                "incoming_count": item.get("incoming_count"),
                "total_connections": item.get("total_connections"),
                "status": item.get("status", "fact"),
                "retrieval_score": item.get(
                    "retrieval_score",
                    0.0,
                ),
                "retrieval_role": "architecture",
                "context_role": "architecture",
            }
        )

    return pool



def _is_repository_identity_question(query: str) -> bool:
    """Return True only for repository-level authorship/ownership questions."""
    if not isinstance(query, str):
        return False

    normalized = re.sub(r"[^a-z0-9]+", " ", query.lower()).strip()
    if not normalized:
        return False

    repository_scope = any(
        phrase in normalized
        for phrase in (
            "this repository",
            "the repository",
            "this repo",
            "the repo",
            "this codebase",
            "the codebase",
        )
    )
    identity_term = any(
        phrase in normalized
        for phrase in (
            "author",
            "authored",
            "maintainer",
            "owner",
            "creator",
        )
    )
    return repository_scope and identity_term


def _build_deterministic_metadata_answer(
    query: str,
    metadata_evidence: list[dict],
) -> str | None:
    """Answer repository-wide metadata questions from authoritative analysis facts."""
    fact = metadata_value_from_evidence(query, metadata_evidence)
    if not fact:
        return None

    value = fact.get("value")
    label = fact.get("label")
    if not isinstance(value, int) or not isinstance(label, str) or not label:
        return None

    return f"The repository contains {value} {label}."


def _build_deterministic_architecture_answer(
    query: str,
    architecture_evidence: list[dict],
) -> str | None:
    """Answer directly from authoritative structured architecture facts."""
    if not isinstance(query, str) or not isinstance(architecture_evidence, list):
        return None

    normalized = re.sub(r"[^a-z0-9_.]+", " ", query.lower()).strip()
    if not normalized or not architecture_evidence:
        return None

    # Explanatory questions must reach the LLM. A deterministic ranking
    # shortcut can establish the numeric fact, but it cannot explain the
    # repository-level reason the user explicitly asked for.
    explanatory_request = any(
        phrase in normalized
        for phrase in (
            "why",
            "explain",
            "how does",
            "how do",
            "how is",
            "how are",
            "reason",
        )
    )
    if explanatory_request:
        return None

    graph_items = [
        item for item in architecture_evidence
        if isinstance(item, dict) and item.get("evidence_subtype") == "graph_summary"
    ]
    module_items = [
        item for item in architecture_evidence
        if isinstance(item, dict) and item.get("evidence_subtype") == "module_dependencies"
    ]

    graph = graph_items[0] if graph_items else None

    # Direct repository-wide graph counts.
    if "dependency edges" in normalized or "number of edges" in normalized or "edge count" in normalized:
        if graph is None:
            return None
        edge_count = graph.get("edge_count")
        if isinstance(edge_count, int):
            return f"The repository architecture contains {edge_count} dependency edges."
        return None

    if "production modules" in normalized and ("how many" in normalized or "number of" in normalized or "count" in normalized):
        if graph is None:
            return None
        node_count = graph.get("node_count")
        if isinstance(node_count, int):
            return f"The repository contains {node_count} production modules."
        return None

    # Exact global ranking/count questions.
    if any(term in normalized for term in (
        "highest number of dependency connections",
        "highest dependency connectivity",
        "highest number of connections",
        "most dependency connections",
        "most dependency relationships",
        "highest connectivity",
        "greatest connectivity",
        "greatest dependency connectivity",
        "greatest dependency connections",
        "most connected",
        "most connected component",
        "most connected file",
    )):
        if graph is None:
            return None
        ranked = graph.get("top_connected_modules", [])
        if not isinstance(ranked, list) or not ranked:
            return None
        first = ranked[0] if isinstance(ranked[0], dict) else None
        if not first:
            return None
        name = str(first.get("module_name", "")).strip()
        total = first.get("total_connections")
        if not name or not isinstance(total, int):
            return None
        return f"The module with the highest number of dependency connections is {name}, with {total} total dependency connections."

    # Exact global minimum-connectivity questions. Use every deterministic
    # module fact rather than the top-ranked list, because the minimum may be
    # absent from the first five highest-connectivity entries. Ties are kept
    # explicit instead of arbitrarily selecting one module.
    if any(term in normalized for term in (
        "fewest dependency connections",
        "least dependency connections",
        "lowest number of dependency connections",
        "lowest dependency connections",
        "fewest connections",
        "least connections",
        "fewest dependency relationships",
        "least dependency relationships",
    )):
        if graph is None:
            return None
        facts = graph.get("all_module_facts", [])
        valid = [
            item for item in facts
            if isinstance(item, dict)
            and str(item.get("module_name", "")).strip()
            and isinstance(item.get("total_connections"), int)
        ]
        if not valid:
            return None
        minimum = min(item["total_connections"] for item in valid)
        matches = [
            item for item in valid
            if item["total_connections"] == minimum
        ]
        matches.sort(key=lambda item: str(item.get("module_name", "")))
        names = [str(item["module_name"]).strip() for item in matches]
        if len(names) == 1:
            return f"The module with the fewest dependency connections is {names[0]}, with {minimum} total dependency connections."
        return f"The modules with the fewest dependency connections are {', '.join(names)}, with {minimum} total dependency connections each."

    # "dependencies" without "connections" means outgoing dependencies in
    # normal dependency-graph terminology. Use the complete ranked list, not
    # merely the top-total-connectivity modules.
    if "most dependencies" in normalized or "highest number of dependencies" in normalized:
        if graph is None:
            return None
        ranked = graph.get("top_outgoing_modules", [])
        if not isinstance(ranked, list) or not ranked:
            return None
        first = ranked[0] if isinstance(ranked[0], dict) else None
        if not first:
            return None
        name = str(first.get("module_name", "")).strip()
        count = first.get("outgoing_count")
        if not name or not isinstance(count, int):
            return None
        return f"The module with the most outgoing dependencies is {name}, with {count} outgoing dependencies."

    if (
        "most outgoing dependencies" in normalized
        or "highest outgoing dependencies" in normalized
        or "highest number of outgoing dependencies" in normalized
    ):
        if graph is None:
            return None
        ranked = graph.get("top_outgoing_modules", [])
        if not isinstance(ranked, list) or not ranked:
            return None
        first = ranked[0] if isinstance(ranked[0], dict) else None
        if not first:
            return None
        name = str(first.get("module_name", "")).strip()
        count = first.get("outgoing_count")
        if not name or not isinstance(count, int):
            return None
        return f"The module with the highest number of outgoing dependencies is {name}, with {count} outgoing dependencies."

    if (
        "most incoming dependencies" in normalized
        or "highest incoming dependencies" in normalized
        or "highest number of incoming dependencies" in normalized
    ):
        if graph is None:
            return None
        ranked = graph.get("top_incoming_modules", [])
        if not isinstance(ranked, list) or not ranked:
            return None
        first = ranked[0] if isinstance(ranked[0], dict) else None
        if not first:
            return None
        name = str(first.get("module_name", "")).strip()
        count = first.get("incoming_count")
        if not name or not isinstance(count, int):
            return None
        return f"The module with the highest number of incoming dependencies is {name}, with {count} incoming dependencies."

    # Exact "which module has N connections?" lookup across all modules.
    number_match = re.search(r"\b(\d+)\b\s+(?:dependency\s+)?connections?\b", normalized)
    if number_match and graph is not None:
        target = int(number_match.group(1))
        facts = graph.get("all_module_facts", [])
        matches = [
            item for item in facts
            if isinstance(item, dict) and item.get("total_connections") == target
        ]
        if len(matches) == 1:
            return f"{matches[0].get('module_name')} has {target} total dependency connections."
        if len(matches) > 1:
            names = ", ".join(str(item.get("module_name")) for item in matches)
            return f"The modules with {target} total dependency connections are {names}."

    if not module_items:
        return None

    # Architecture retrieval already narrows module evidence. Keep the highest
    # lexical match, with deterministic connectivity as a tie-breaker.
    def module_score(item: dict) -> tuple[int, int, int, str]:
        name = str(item.get("module_name", "")).lower().strip()
        tokens = [t for t in re.split(r"[^a-z0-9_]+", name) if t]
        score = sum(token in normalized.split() for token in tokens)
        exact = 1 if name and (name in normalized or normalized.endswith(name)) else 0
        return exact, score, int(item.get("total_connections") or 0), name

    module = max(module_items, key=module_score)
    name = str(module.get("module_name", "")).strip()
    if not name:
        return None

    # "Which modules depend on X?" is incoming dependency information and must
    # be evaluated before the generic "depend on" outgoing branch.
    if (
        "which modules depend on" in normalized
        or "who depends on" in normalized
        or "used by" in normalized
        or "incoming dependencies" in normalized
    ):
        count = module.get("incoming_count")
        deps = module.get("incoming_dependency_modules") or module.get("incoming_dependencies", [])
        if not isinstance(count, int) or not isinstance(deps, list):
            return None
        if "how many" in normalized or "number of" in normalized or "count" in normalized:
            return f"{name} has {count} incoming dependencies."
        dep_text = ", ".join(str(x) for x in deps) if deps else "none"
        return f"{name} has {count} incoming dependencies: {dep_text}."

    if (
        "what does" in normalized and "depend on" in normalized
        or "outgoing dependencies" in normalized
        or "depends on" in normalized
    ):
        count = module.get("outgoing_count")
        deps = module.get("outgoing_dependency_modules") or module.get("outgoing_dependencies", [])
        if not isinstance(count, int) or not isinstance(deps, list):
            return None
        if "how many" in normalized or "number of" in normalized or "count" in normalized:
            return f"{name} has {count} outgoing dependencies."
        dep_text = ", ".join(str(x) for x in deps) if deps else "none"
        return f"{name} has {count} outgoing dependencies: {dep_text}."

    if "dependency connections" in normalized or "total connections" in normalized:
        total = module.get("total_connections")
        if not isinstance(total, int):
            return None
        return f"{name} has {total} total dependency connections."

    if "layer" in normalized:
        layer = module.get("layer")
        if layer:
            return f"{name} belongs to the {layer} architecture layer."

    return None


def _build_public_evidence(
    retrieval_result: dict,
) -> list[dict]:
    """
    Build the public/API evidence contract.

    Only primary evidence is exposed through the main evidence list.
    Supporting evidence remains in supporting_evidence.

    This preserves the existing RepoLens UI/audit contract.
    """

    evidence: list[dict] = []

    # ---------------------------------------------------------
    # PRIMARY CODE EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "evidence",
        [],
    ):
        evidence.append(
            {
                "evidence_type": "code",
                "file": item.get(
                    "file",
                    "",
                ),
                "start_line": item.get(
                    "start_line"
                ),
                "end_line": item.get(
                    "end_line"
                ),
            }
        )

    # ---------------------------------------------------------
    # REPOSITORY METADATA EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "metadata_evidence",
        [],
    ):
        evidence.append(
            {
                "evidence_type": "repository_metadata",
                "file": item.get("file"),
                "start_line": item.get("start_line"),
                "end_line": item.get("end_line"),
                "metadata_key": item.get("metadata_key"),
                "label": item.get("label"),
                "value": item.get("value"),
            }
        )

    # ---------------------------------------------------------
    # ARCHITECTURE EVIDENCE
    # ---------------------------------------------------------

    for item in retrieval_result.get(
        "architecture_evidence",
        [],
    ):
        evidence.append(
            {
                "evidence_type": "architecture",
                "file": item.get(
                    "file"
                ),
                "module_name": item.get(
                    "module_name"
                ),
                "start_line": item.get(
                    "start_line"
                ),
                "end_line": item.get(
                    "end_line"
                ),
            }
        )

    return evidence


def _select_claim_candidates(
    claim_text: str,
    evidence_pool: list[dict],
) -> list[dict]:
    """
    Select deterministic candidate evidence for a claim.

    This function does NOT decide whether a claim is true.

    It only narrows the evidence pool.

    The final semantic decision is made by claim_verifier.py.
    """

    metadata_fact = metadata_value_from_evidence(
        claim_text,
        evidence_pool,
    )
    if metadata_fact is not None:
        return [metadata_fact]

    selected = select_claim_evidence(
        query=claim_text,
        evidence=evidence_pool,
    )

    if selected:
        return selected

    # Fail-safe fallback:
    # If deterministic ranking cannot find a candidate,
    # provide the complete retrieved evidence pool to the
    # verifier rather than inventing or discarding evidence.

    return evidence_pool



def _build_targeted_repository_evidence(
    claim_text: str,
    chunks: list[dict],
    existing_evidence: list[dict],
) -> list[dict]:
    """
    Find precise repository chunks for a claim when normal retrieval did not
    expose enough attribution candidates.

    This is a claim-attribution fallback only. It does not change normal
    retrieval ranking or the public evidence contract.
    """

    if not isinstance(chunks, list) or not chunks:
        return []

    candidates: list[dict] = []

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        candidates.append(
            {
                "evidence_type": "code",
                "file": chunk.get("file", ""),
                "start_line": chunk.get("start_line"),
                "end_line": chunk.get("end_line"),
                "content": chunk.get("content", ""),
                "symbols": chunk.get("symbols", {}),
                "retrieval_score": chunk.get("retrieval_score", 0.0),
                "retrieval_role": "targeted_claim_fallback",
                "context_role": "claim_fallback",
            }
        )

    selected = select_claim_evidence(
        query=claim_text,
        evidence=candidates,
    )

    if not selected:
        return []

    existing_keys = {
        (
            str(item.get("file", "")).replace("\\", "/").lower(),
            item.get("start_line"),
            item.get("end_line"),
        )
        for item in existing_evidence
        if isinstance(item, dict)
    }

    return [
        item
        for item in selected
        if (
            str(item.get("file", "")).replace("\\", "/").lower(),
            item.get("start_line"),
            item.get("end_line"),
        ) not in existing_keys
    ]


def _verify_claim_with_fallbacks(
    claim_text: str,
    candidate_evidence: list[dict],
    chunks: list[dict],
    provider: LLMProvider,
) -> dict:
    """
    Verify a claim against selected evidence.

    The first pass uses the complete deterministic candidate set. If that
    mixed set is judged unsupported, retry with smaller evidence subsets.
    This prevents a strong, directly supporting code block from being masked
    by unrelated neighboring evidence while preserving fail-closed behavior.
    """

    # Repository metadata is authoritative for repository-wide counts.
    # Check it before architecture facts so "dependency edges" (analysis
    # dependency graph) cannot be confused with "architecture edges".
    metadata_fact = metadata_value_from_evidence(
        claim_text,
        candidate_evidence,
    )
    if metadata_fact:
        expected = metadata_fact.get("value")
        match = re.search(r"\b(\d+)\b", claim_text)
        if isinstance(expected, int) and match:
            observed = int(match.group(1))
            return {
                "decision": "supported" if observed == expected else "unsupported",
                "reason": (
                    f"Authoritative repository metadata reports "
                    f"{expected} {metadata_fact.get('label', 'repository facts')}."
                ),
            }

    # Deterministic architecture facts are authoritative. If the structured
    # snapshot directly contradicts the claim, do not let a later code-only
    # fallback override that contradiction.
    deterministic = _deterministic_architecture_fact_check(
        claim_text,
        candidate_evidence,
    )
    if deterministic is not None:
        return deterministic

    verification = verify_claim(
        claim=claim_text,
        evidence=candidate_evidence,
        chunks=chunks,
        provider=provider,
    )

    decision = str(
        verification.get("decision", "unsupported")
    ).strip().lower()

    if decision != "unsupported":
        return verification

    # Try each selected evidence item independently. A claim can be fully
    # established by one precise implementation chunk even when the complete
    # candidate set contains distracting neighboring code.
    for item in candidate_evidence:
        retry = verify_claim(
            claim=claim_text,
            evidence=[item],
            chunks=chunks,
            provider=provider,
        )
        retry_decision = str(
            retry.get("decision", "unsupported")
        ).strip().lower()
        if retry_decision != "unsupported":
            return retry

    # Finally try the strongest small prefix for relationship claims that may
    # require more than one evidence block, while avoiding the full noisy set.
    for size in (2, 3):
        if len(candidate_evidence) < size:
            continue
        retry = verify_claim(
            claim=claim_text,
            evidence=candidate_evidence[:size],
            chunks=chunks,
            provider=provider,
        )
        retry_decision = str(
            retry.get("decision", "unsupported")
        ).strip().lower()
        if retry_decision != "unsupported":
            return retry

    # Final deterministic attribution fallback: inspect the repository-loaded
    # chunks directly. This does not alter retrieval; it only prevents a valid
    # claim from becoming UNKNOWN because the exact implementation chunk was
    # outside the normal top-k evidence set.
    targeted = _build_targeted_repository_evidence(
        claim_text=claim_text,
        chunks=chunks,
        existing_evidence=candidate_evidence,
    )

    if targeted:
        retry = verify_claim(
            claim=claim_text,
            evidence=targeted,
            chunks=chunks,
            provider=provider,
        )
        retry_decision = str(
            retry.get("decision", "unsupported")
        ).strip().lower()
        if retry_decision != "unsupported":
            return retry

    return verification


def answer_repository_query(
    query: str,
    chunks: list[dict],
    provider: LLMProvider,
    top_k: int = 5,
    max_neighbors: int = 1,
    architecture_snapshot: dict | None = None,
    repository_analysis: dict | None = None,
    status: str = "fact",
) -> dict:
    """
    Run the complete evidence-grounded repository Q&A pipeline.

    Pipeline:

        retrieval
            ↓
        focused context selection
            ↓
        context building
            ↓
        evidence-grounded LLM answer
            ↓
        claim decomposition
            ↓
        complete evidence candidate pool
            ↓
        deterministic claim evidence selection
            ↓
        semantic claim verification
            ↓
        claim status
            ↓
        claim coverage

    Important design rules:

    1. Retrieval remains the source of repository evidence.
    2. Focused context controls only what the LLM sees.
    3. Original retrieval evidence remains available for auditing.
    4. Supporting evidence may participate in claim verification.
    5. The LLM never gets to decide whether its own claim is factual.
    6. Claim verification is the final evidence gate.
    """

    # ---------------------------------------------------------
    # INPUT VALIDATION
    # ---------------------------------------------------------

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "Query must be a string."
        )

    if not isinstance(
        chunks,
        list,
    ):
        raise TypeError(
            "Chunks must be a list."
        )

    # Secret-value disclosure is outside the repository-Q&A trust contract.
    # Return a safe, evidence-free UNKNOWN before retrieval or LLM generation.
    if is_sensitive_value_request(query):
        return {
            "answer": "UNKNOWN",
            "status": "unknown",
            "evidence": [],
            "claims": [],
            "supporting_evidence": [],
            "architecture_evidence": [],
            "metadata_evidence": [],
            "retrieval_counts": {
                "primary": 0,
                "supporting": 0,
                "architecture": 0,
                "metadata": 0,
            },
            "claim_coverage": {
                "claim_count": 0,
                "supported_claims": 0,
                "unsupported_claims": 0,
                "coverage": 0.0,
            },
        }

    # ---------------------------------------------------------
    # REPOSITORY IDENTITY TRUST BOUNDARY
    # ---------------------------------------------------------
    # A package-level declaration such as ``__author__`` is not, by itself,
    # authoritative evidence that a person is the author/owner/maintainer of
    # the repository being analyzed. Keep repository-level identity questions
    # UNKNOWN unless an explicit repository-level identity artifact exists.
    if _is_repository_identity_question(query):
        metadata = repository_analysis.get("metadata", {}) if isinstance(repository_analysis, dict) else {}
        explicit_identity_keys = (
            "author",
            "authors",
            "maintainer",
            "maintainers",
            "owner",
            "owners",
            "creator",
            "creators",
        )
        has_explicit_identity = isinstance(metadata, dict) and any(
            key in metadata and metadata.get(key) not in (None, "", [], {})
            for key in explicit_identity_keys
        )
        if not has_explicit_identity:
            return {
                "answer": "UNKNOWN",
                "status": "unknown",
                "evidence": [],
                "claims": [],
                "supporting_evidence": [],
                "architecture_evidence": [],
                "metadata_evidence": [],
                "retrieval_counts": {
                    "primary": 0,
                    "supporting": 0,
                    "architecture": 0,
                    "metadata": 0,
                },
                "claim_coverage": {
                    "claim_count": 0,
                    "supported_claims": 0,
                    "unsupported_claims": 0,
                    "coverage": 0.0,
                },
            }

    # ---------------------------------------------------------
    # RETRIEVAL
    # ---------------------------------------------------------

    retrieval_result = retrieve_repository_evidence(
        query=query,
        chunks=chunks,
        top_k=top_k,
        max_neighbors=max_neighbors,
        architecture_snapshot=architecture_snapshot,
    )

    # ---------------------------------------------------------
    # AUTHORITATIVE ARCHITECTURE RECOVERY
    # ---------------------------------------------------------
    # Architecture facts must not depend on a secondary query-intent
    # classifier or context selector. If a structured snapshot exists,
    # retrieve the architecture evidence directly from that snapshot as a
    # second deterministic path. This prevents a wording/paraphrase mismatch
    # from silently routing an exact architecture fact to the LLM.
    #
    # This also repairs an important trust-boundary failure mode: if code
    # retrieval succeeds but architecture retrieval is accidentally empty, a
    # model must never be allowed to invent a repository-wide ranking fact.

    authoritative_architecture_evidence = []
    if isinstance(architecture_snapshot, dict):
        authoritative_architecture_evidence = retrieve_architecture_evidence(
            query=query,
            snapshot=architecture_snapshot,
            top_k=max(top_k, 5),
        )

    if authoritative_architecture_evidence:
        existing_architecture = retrieval_result.get(
            "architecture_evidence",
            [],
        )
        if not isinstance(existing_architecture, list):
            existing_architecture = []

        def _architecture_key(item: dict) -> tuple:
            return (
                str(item.get("evidence_subtype", "")),
                str(item.get("file", "")).replace("\\", "/").lower(),
                str(item.get("module_name", "")).lower(),
            )

        merged = []
        seen = set()
        for item in authoritative_architecture_evidence + existing_architecture:
            if not isinstance(item, dict):
                continue
            key = _architecture_key(item)
            if key in seen:
                continue
            seen.add(key)
            merged.append(item)

        retrieval_result["architecture_evidence"] = merged

    # ---------------------------------------------------------
    # AUTHORITATIVE REPOSITORY METADATA RECOVERY
    # ---------------------------------------------------------
    if isinstance(repository_analysis, dict):
        retrieval_result["metadata_evidence"] = retrieve_repository_metadata_evidence(
            query=query,
            analysis=repository_analysis,
            top_k=max(top_k, 7),
        )
    else:
        retrieval_result["metadata_evidence"] = []

    # ---------------------------------------------------------
    # FOCUSED LLM CONTEXT
    # ---------------------------------------------------------
    #
    # Retrieval may contain several useful chunks.
    #
    # The LLM receives only the focused subset to reduce
    # topic drift, especially with smaller local models.
    #
    # IMPORTANT:
    # This does NOT modify the original retrieval result.
    #

    focused_context = select_context_evidence(
        query=query,
        evidence=retrieval_result.get(
            "evidence",
            [],
        ),
        supporting_evidence=retrieval_result.get(
            "supporting_evidence",
            [],
        ),
        architecture_evidence=retrieval_result.get(
            "architecture_evidence",
            [],
        ),
        limit=4,
    )

    context_result = {
        "evidence": focused_context.get(
            "evidence",
            [],
        ),
        "supporting_evidence": focused_context.get(
            "supporting_evidence",
            [],
        ),
        "architecture_evidence": focused_context.get(
            "architecture_evidence",
            [],
        ),
        "metadata_evidence": retrieval_result.get(
            "metadata_evidence",
            [],
        ),
    }

    repository_context = build_rag_context(
        context_result
    )

    # ---------------------------------------------------------
    # PUBLIC EVIDENCE
    # ---------------------------------------------------------
    #
    # Keep the existing public/API evidence contract.
    #

    public_evidence = _build_public_evidence(
        retrieval_result
    )

    # ---------------------------------------------------------
    # VALIDATE PRIMARY CODE EVIDENCE
    # ---------------------------------------------------------

    for item in public_evidence:

        if item.get(
            "evidence_type"
        ) != "code":
            continue

        if not validate_code_evidence_reference(
            item,
            chunks,
        ):
            raise ValueError(
                "Retrieved code evidence does not "
                "match any repository chunk."
            )

    # ---------------------------------------------------------
    # ANSWER GENERATION
    # ---------------------------------------------------------
    # Structured architecture facts are authoritative and deterministic.
    # Resolve those questions before invoking the LLM so a local model cannot
    # turn a directly provable fact into UNKNOWN, and Ollama availability is
    # not a dependency for deterministic architecture Q&A.
    deterministic_answer = _build_deterministic_metadata_answer(
        query=query,
        metadata_evidence=retrieval_result.get(
            "metadata_evidence",
            [],
        ),
    )

    if deterministic_answer is None:
        deterministic_answer = _build_deterministic_architecture_answer(
            query=query,
            architecture_evidence=retrieval_result.get(
                "architecture_evidence",
                [],
            ),
        )

    if deterministic_answer:
        result = build_answer(
            answer=deterministic_answer,
            status="fact",
            evidence=public_evidence,
        )
    else:
        result = generate_repository_answer(
            query=query,
            repository_context=repository_context,
            provider=provider,
            status=status,
            evidence=public_evidence,
        )

    # ---------------------------------------------------------
    # CLAIM DECOMPOSITION
    # ---------------------------------------------------------

    claim_texts = decompose_answer_into_claims(
        result["answer"]
    )

    # ---------------------------------------------------------
    # COMPLETE CLAIM EVIDENCE POOL
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    #
    # Claim verification must NOT be limited to the primary
    # evidence shown in the public answer.
    #
    # Supporting neighboring chunks can contain the exact
    # implementation needed to establish a claim.
    #

    evidence_pool = _build_claim_evidence_pool(
        retrieval_result
    )

    claims = []

    # ---------------------------------------------------------
    # CLAIM VERIFICATION
    # ---------------------------------------------------------

    for claim_text in claim_texts:

        # -----------------------------------------------------
        # UNKNOWN ANSWER
        # -----------------------------------------------------

        if result["status"] == "unknown":

            claims.append(
                build_answer_claim(
                    answer=claim_text,
                    status="unknown",
                    evidence=[],
                )
            )

            continue

        # -----------------------------------------------------
        # SELECT CANDIDATE EVIDENCE
        # -----------------------------------------------------

        candidate_evidence = _select_claim_candidates(
            claim_text=claim_text,
            evidence_pool=evidence_pool,
        )

        # -----------------------------------------------------
        # SEMANTIC VERIFICATION
        # -----------------------------------------------------
        #
        # The verifier receives actual repository chunks and
        # candidate evidence references.
        #
        # It must fail closed:
        #
        # supported
        # partially_supported
        # unsupported
        #

        verification = _verify_claim_with_fallbacks(
            claim_text=claim_text,
            candidate_evidence=candidate_evidence,
            chunks=chunks,
            provider=provider,
        )

        decision = str(
            verification.get(
                "decision",
                "unsupported",
            )
        ).strip().lower()

        # -----------------------------------------------------
        # MAP VERIFIER DECISION → REPO LENS STATUS
        # -----------------------------------------------------

        if decision == "supported":

            claim_status = "fact"

        elif decision == "partially_supported":

            claim_status = "inference"

        else:

            claim_status = "unknown"

            # IMPORTANT:
            # Unsupported claims must not retain evidence.
            #
            # Otherwise the UI could incorrectly interpret
            # merely retrieved evidence as proof.

            candidate_evidence = []

        claims.append(
            build_answer_claim(
                answer=claim_text,
                status=claim_status,
                evidence=candidate_evidence,
            )
        )

    # ---------------------------------------------------------
    # ATTACH CLAIMS
    # ---------------------------------------------------------

    result["claims"] = claims

    # ---------------------------------------------------------
    # PRESERVE ORIGINAL RETRIEVAL ORGANIZATION
    # ---------------------------------------------------------
    #
    # Do not replace these with focused context.
    #

    result["supporting_evidence"] = retrieval_result.get(
        "supporting_evidence",
        [],
    )

    result["architecture_evidence"] = retrieval_result.get(
        "architecture_evidence",
        [],
    )

    result["metadata_evidence"] = retrieval_result.get(
        "metadata_evidence",
        [],
    )

    result["retrieval_counts"] = {
        "primary": len(
            retrieval_result.get(
                "evidence",
                [],
            )
        ),
        "supporting": len(
            retrieval_result.get(
                "supporting_evidence",
                [],
            )
        ),
        "architecture": len(
            retrieval_result.get(
                "architecture_evidence",
                [],
            )
        ),
        "metadata": len(
            retrieval_result.get(
                "metadata_evidence",
                [],
            )
        ),
    }

    # ---------------------------------------------------------
    # FINAL ANSWER TRUST GATE
    # ---------------------------------------------------------
    # Generation alone cannot promote an answer to "fact". The final status
    # is derived from the independently verified claim statuses.
    if claims:
        claim_statuses = [
            str(getattr(claim, "status", "unknown")).lower()
            for claim in claims
        ]

        if all(status == "unknown" for status in claim_statuses):
            result["status"] = "unknown"
            result["answer"] = "UNKNOWN"
        elif any(status == "unknown" for status in claim_statuses):
            result["status"] = "inference"
        elif any(status == "inference" for status in claim_statuses):
            result["status"] = "inference"
        else:
            result["status"] = "fact"

    # ---------------------------------------------------------
    # CLAIM COVERAGE
    # ---------------------------------------------------------

    result["claim_coverage"] = (
        calculate_claim_coverage(
            claims
        )
    )

    return result