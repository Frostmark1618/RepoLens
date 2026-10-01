from __future__ import annotations

import re
from collections import Counter
from math import log
from typing import Any


# ============================================================
# TOKENIZATION
# ============================================================

_STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "to",
    "of",
    "for",
    "from",
    "in",
    "on",
    "at",
    "by",
    "with",
    "and",
    "or",
    "but",
    "if",
    "then",
    "than",
    "that",
    "this",
    "these",
    "those",
    "it",
    "its",
    "into",
    "through",
    "during",
    "using",
    "use",
    "uses",
    "used",
    "work",
    "works",
    "working",
    "handle",
    "handles",
    "handling",
    "do",
    "does",
    "did",
    "how",
    "what",
    "which",
    "where",
    "when",
    "why",
    "can",
    "could",
    "would",
    "should",
    "will",
    "may",
    "might",
    "all",
    "any",
    "some",
    "each",
    "every",
    "given",
    "appropriate",
    "corresponding",
}


_ALIASES = {
    "authentication": {"authentication", "auth"},
    "auth": {"authentication", "auth"},
    "session": {"session", "sessions"},
    "sessions": {"session", "sessions"},
    "request": {"request", "requests"},
    "requests": {"request", "requests"},
    "response": {"response", "responses"},
    "responses": {"response", "responses"},
    "adapter": {"adapter", "adapters"},
    "adapters": {"adapter", "adapters"},
    "cookie": {"cookie", "cookies"},
    "cookies": {"cookie", "cookies"},
    "exception": {"exception", "exceptions"},
    "exceptions": {"exception", "exceptions"},
    "hook": {"hook", "hooks"},
    "hooks": {"hook", "hooks"},
    "model": {"model", "models"},
    "models": {"model", "models"},
    "utility": {"utility", "utilities", "utils"},
    "utilities": {"utility", "utilities", "utils"},
    "utils": {"utility", "utilities", "utils"},
    "compatibility": {"compatibility", "compat"},
    "compat": {"compatibility", "compat"},
}


def _tokenize(value: str) -> set[str]:
    """
    Tokenize prose and code identifiers.

    Supports:
    - normal words
    - snake_case
    - kebab-case
    - CamelCase
    - dotted identifiers
    """

    text = str(value or "")

    text = re.sub(
        r"(?<=[a-z])(?=[A-Z])",
        " ",
        text,
    )

    text = re.sub(
        r"(?<=[A-Z])(?=[A-Z][a-z])",
        " ",
        text,
    )

    raw_tokens = re.findall(
        r"[A-Za-z_][A-Za-z0-9_]*",
        text,
    )

    tokens: set[str] = set()

    for token in raw_tokens:
        token = token.lower().strip("_")

        if not token:
            continue

        if token in _STOP_WORDS:
            continue

        if len(token) <= 1:
            continue

        tokens.add(token)

        # snake_case / dotted-like compound identifiers
        for part in re.split(r"[_\-.]+", token):
            if len(part) > 1 and part not in _STOP_WORDS:
                tokens.add(part)

    return tokens


def _expand_entity_forms(tokens: set[str]) -> set[str]:
    """
    Conservative singular/plural normalization.

    Keeps the original token and adds a closely related form.
    """

    expanded = set(tokens)

    for token in list(tokens):
        if len(token) > 3 and token.endswith("ies"):
            expanded.add(token[:-3] + "y")

        elif len(token) > 3 and token.endswith("ses"):
            expanded.add(token[:-2])

        elif len(token) > 3 and token.endswith("s"):
            expanded.add(token[:-1])

        elif len(token) > 2:
            expanded.add(token + "s")

        aliases = _ALIASES.get(token)

        if aliases:
            expanded.update(aliases)

    return expanded


def _extract_query_tokens(query: str) -> set[str]:
    return _expand_entity_forms(
        _tokenize(query)
    )


def _get_symbol_names(item: dict) -> list[str]:
    symbols = item.get(
        "symbols",
        {},
    )

    if not isinstance(symbols, dict):
        return []

    names: list[str] = []

    for symbol in symbols.get(
        "classes",
        [],
    ):
        if isinstance(symbol, dict):
            names.append(
                str(
                    symbol.get(
                        "name",
                        "",
                    )
                )
            )

    for symbol in symbols.get(
        "functions",
        [],
    ):
        if isinstance(symbol, dict):
            names.append(
                str(
                    symbol.get(
                        "name",
                        "",
                    )
                )
            )

    return names


# ============================================================
# BASIC EVIDENCE SCORING
# ============================================================

def _score_evidence(
    query_tokens: set[str],
    item: dict,
) -> tuple[int, set[str], set[str], set[str]]:
    content_tokens = _expand_entity_forms(
        _tokenize(
            item.get(
                "content",
                "",
            )
        )
    )

    file_tokens = _expand_entity_forms(
        _tokenize(
            item.get(
                "file",
                "",
            )
        )
    )

    symbol_tokens: set[str] = set()

    for name in _get_symbol_names(item):
        symbol_tokens.update(
            _expand_entity_forms(
                _tokenize(name)
            )
        )

    content_matches = (
        query_tokens
        & content_tokens
    )

    file_matches = (
        query_tokens
        & file_tokens
    )

    symbol_matches = (
        query_tokens
        & symbol_tokens
    )

    matched_tokens = (
        content_matches
        | file_matches
        | symbol_matches
    )

    score = (
        len(content_matches)
        + 5 * len(file_matches)
        + 3 * len(symbol_matches)
    )

    return (
        score,
        matched_tokens,
        file_matches,
        symbol_matches,
    )


# ============================================================
# CONTEXT EVIDENCE SELECTION
# ============================================================

def _select_diverse_code_evidence(
    query_tokens: set[str],
    scored_evidence: list[
        tuple[int, dict, set[str], set[str], set[str]]
    ],
    limit: int = 3,
) -> list[dict]:

    if not scored_evidence:
        return []

    def relevance_key(entry):
        (
            score,
            item,
            matched_tokens,
            file_matches,
            symbol_matches,
        ) = entry

        direct_symbol_match = bool(
            symbol_matches
        )

        direct_file_match = bool(
            file_matches
        )

        return (
            1 if direct_symbol_match else 0,
            1 if direct_file_match else 0,
            len(symbol_matches),
            len(file_matches),
            len(matched_tokens),
            score,
            float(
                item.get(
                    "retrieval_score",
                    0.0,
                )
                or 0.0
            ),
        )

    ranked = sorted(
        scored_evidence,
        key=relevance_key,
        reverse=True,
    )

    selected: list[dict] = []
    selected_ids: set[int] = set()
    covered_tokens: set[str] = set()

    # --------------------------------------------------------
    # First pass: structural matches
    # --------------------------------------------------------

    for entry in ranked:
        if len(selected) >= limit:
            break

        (
            _score,
            item,
            matched_tokens,
            file_matches,
            symbol_matches,
        ) = entry

        item_id = id(item)

        if item_id in selected_ids:
            continue

        if file_matches or symbol_matches:
            selected.append(item)
            selected_ids.add(item_id)
            covered_tokens.update(matched_tokens)

    # --------------------------------------------------------
    # Second pass: content overlap
    # --------------------------------------------------------

    remaining = [
        entry
        for entry in ranked
        if id(entry[1]) not in selected_ids
    ]

    structural_matches_exist = any(
        entry[3] or entry[4]
        for entry in ranked
    )

    for entry in remaining:
        if len(selected) >= limit:
            break

        (
            _score,
            item,
            matched_tokens,
            file_matches,
            symbol_matches,
        ) = entry

        if (
            structural_matches_exist
            and not (
                file_matches
                or symbol_matches
            )
        ):
            continue

        selected.append(item)
        selected_ids.add(id(item))
        covered_tokens.update(matched_tokens)

    return selected


# ============================================================
# CLAIM TOKEN EXTRACTION
# ============================================================

def _claim_entity_tokens(
    claim: str,
) -> set[str]:
    """
    Extract claim tokens with conservative
    singular/plural normalization.

    Relationship words are intentionally kept out
    through _STOP_WORDS so they don't dominate selection.
    """

    tokens = _extract_query_tokens(
        claim
    )

    return _expand_entity_forms(
        tokens
    )


# ============================================================
# CLAIM EVIDENCE SCORING
# ============================================================

def _claim_evidence_score(
    claim_tokens: set[str],
    item: dict,
) -> tuple[
    int,
    set[str],
    set[str],
    set[str],
]:

    content_tokens = _expand_entity_forms(
        _tokenize(
            item.get(
                "content",
                "",
            )
        )
    )

    file_tokens = _expand_entity_forms(
        _tokenize(
            item.get(
                "file",
                "",
            )
        )
    )

    symbol_tokens: set[str] = set()

    for name in _get_symbol_names(item):
        symbol_tokens.update(
            _expand_entity_forms(
                _tokenize(name)
            )
        )

    content_matches = (
        claim_tokens
        & content_tokens
    )

    file_matches = (
        claim_tokens
        & file_tokens
    )

    symbol_matches = (
        claim_tokens
        & symbol_tokens
    )

    matched_tokens = (
        content_matches
        | file_matches
        | symbol_matches
    )

    score = (
        len(content_matches)
        + 8 * len(file_matches)
        + 5 * len(symbol_matches)
    )

    return (
        score,
        matched_tokens,
        file_matches,
        symbol_matches,
    )


# ============================================================
# CLAIM CODE EVIDENCE
# ============================================================

def _select_claim_code_evidence(
    query: str,
    evidence: list[dict],
    limit: int = 6,
) -> list[dict]:
    """
    Select deterministic evidence for semantic claim
    verification.

    IMPORTANT:
    Claim verification is broader than LLM context selection.

    A claim can be supported by:
    - symbol match
    - file/module match
    - content match

    Therefore content-only matches MUST NOT be discarded
    when no structural match exists.
    """

    if not evidence:
        return []

    claim_tokens = _claim_entity_tokens(
        query
    )

    if not claim_tokens:
        return []

    scored: list[
        tuple[int, dict, set[str], set[str], set[str]]
    ] = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        # Only actual code evidence.
        evidence_type = str(
            item.get(
                "evidence_type",
                "code",
            )
            or "code"
        ).lower()

        if evidence_type != "code":
            continue

        (
            score,
            matched_tokens,
            file_matches,
            symbol_matches,
        ) = _claim_evidence_score(
            claim_tokens,
            item,
        )

        if score <= 0:
            continue

        scored.append(
            (
                score,
                item,
                matched_tokens,
                file_matches,
                symbol_matches,
            )
        )

    if not scored:
        return []

    # --------------------------------------------------------
    # Rank:
    # 1. symbol
    # 2. file
    # 3. content overlap
    # 4. retrieval score
    # --------------------------------------------------------

    def structural_key(entry):
        (
            score,
            item,
            matched_tokens,
            file_matches,
            symbol_matches,
        ) = entry

        return (
            1 if symbol_matches else 0,
            1 if file_matches else 0,
            len(symbol_matches),
            len(file_matches),
            len(matched_tokens),
            score,
            float(
                item.get(
                    "retrieval_score",
                    0.0,
                )
                or 0.0
            ),
        )

    scored.sort(
        key=structural_key,
        reverse=True,
    )

    selected: list[dict] = []
    selected_ids: set[int] = set()
    selected_files: set[str] = set()

    # --------------------------------------------------------
    # PASS 1:
    # Prefer structurally strong evidence and
    # diversify across files.
    # --------------------------------------------------------

    for entry in scored:

        if len(selected) >= limit:
            break

        (
            _score,
            item,
            _matched_tokens,
            file_matches,
            symbol_matches,
        ) = entry

        item_id = id(item)

        if item_id in selected_ids:
            continue

        # IMPORTANT FIX:
        # content-only matches are valid evidence.
        if not (
            file_matches
            or symbol_matches
            or _matched_tokens
        ):
            continue

        file_name = str(
            item.get(
                "file",
                "",
            )
        ).lower()

        # Prefer a new file for relationship claims.
        if file_name in selected_files:
            continue

        selected.append(item)
        selected_ids.add(item_id)

        if file_name:
            selected_files.add(file_name)

    # --------------------------------------------------------
    # PASS 2:
    # Fill remaining slots with strongest evidence,
    # including content-only evidence.
    # --------------------------------------------------------

    for entry in scored:

        if len(selected) >= limit:
            break

        (
            _score,
            item,
            matched_tokens,
            file_matches,
            symbol_matches,
        ) = entry

        item_id = id(item)

        if item_id in selected_ids:
            continue

        # IMPORTANT FIX:
        # matched_tokens alone is enough to retain evidence.
        if not (
            file_matches
            or symbol_matches
            or matched_tokens
        ):
            continue

        selected.append(item)
        selected_ids.add(item_id)

    return selected


# ============================================================
# PUBLIC CLAIM EVIDENCE SELECTOR
# ============================================================

def _select_relevant_architecture_evidence(
    query_tokens: set[str],
    architecture_evidence: list[dict],
    query_lower: str = "",
) -> list[dict]:
    """Select the architecture item most directly tied to the query."""

    if not architecture_evidence:
        return []

    scored: list[tuple[int, dict]] = []

    for item in architecture_evidence:
        # Graph-summary evidence represents a repository-wide fact rather than
        # a single module. Keep it for global architecture/dependency claims.
        if item.get("evidence_subtype") == "graph_summary":
            scored.append((100, item))
            continue

        module_tokens = _expand_entity_forms(
            _tokenize(item.get("module_name", ""))
        )
        file_tokens = _expand_entity_forms(
            _tokenize(item.get("file", ""))
        )

        module_name = str(item.get("module_name", "")).lower().strip()
        exact_module = bool(module_tokens) and module_tokens <= query_tokens
        subject_text = re.split(r"\bhas\b|\bdepends\b", query_lower, maxsplit=1)[0].strip()
        full_name_match = bool(module_name) and module_name in subject_text
        module_matches = query_tokens & module_tokens
        file_matches = query_tokens & file_tokens

        score = (
            (1000 if full_name_match else 0)
            + (100 if exact_module else 0)
            + 10 * len(module_matches)
            + 3 * len(file_matches)
        )

        if score > 0:
            scored.append((score, item))

    if not scored:
        return []

    scored.sort(key=lambda entry: entry[0], reverse=True)
    return [scored[0][1]]


def select_claim_evidence(
    query: str,
    evidence: list[dict],
) -> list[dict]:
    """
    Select deterministic evidence for claim verification.

    Claim verification intentionally has a larger evidence budget than
    answer-generation context selection. It can preserve multiple files for
    relationship claims, while still choosing one exact architecture module
    when a claim targets a specific module.
    """

    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    if not isinstance(evidence, list):
        raise TypeError("Evidence must be a list.")

    if not evidence:
        return []

    query_tokens = _extract_query_tokens(query)
    query_lower = query.lower()

    architecture_evidence = [
        item
        for item in evidence
        if str(item.get("evidence_type", "")).lower() == "architecture"
    ]

    # Architecture claims are module-oriented. Select the exact module first;
    # otherwise select the single architecture item with the strongest module
    # or file overlap. Do not return every architecture node for a claim about
    # one module.
    architecture_keywords = {
        "architecture", "layer", "layers", "depend", "depends", "dependency", "dependencies",
        "module", "modules", "component", "components", "design",
        "structure", "flow", "relationship",
    }

    if query_tokens & architecture_keywords and architecture_evidence:
        selected_architecture = _select_relevant_architecture_evidence(
            query_tokens,
            architecture_evidence,
            query_lower=query_lower,
        )
        if selected_architecture:
            return selected_architecture

    # Broad conceptual/relationship claims should retain the supplied evidence
    # because retrieval has already performed the repository-level filtering.
    # This is especially important for claims spanning multiple components.
    explicit_symbol_or_implementation = any(
        phrase in query_lower
        for phrase in (
            "how does", "how do", "how is", "how are", "what does",
            "what is", "what are", "implementation", "implement",
            "class", "method", "function", "symbol",
        )
    )

    if not explicit_symbol_or_implementation and not (
        query_tokens & architecture_keywords
    ):
        return list(evidence)

    selected = _select_claim_code_evidence(
        query=query,
        evidence=evidence,
        limit=6,
    )

    if selected:
        return selected

    # Symbol/implementation claims must still receive available code evidence
    # when the test fixture or repository chunk does not carry content/symbol
    # metadata. The fallback never invents evidence; it only preserves actual
    # supplied code references.
    code_evidence = [
        item
        for item in evidence
        if str(item.get("evidence_type", "code") or "code").lower() == "code"
    ]

    if code_evidence:
        return code_evidence[:6]

    # Last safe fallback: preserve the supplied evidence rather than fabricating
    # a reference. The verifier remains the final truth gate.
    return list(evidence)


# ============================================================
# CONTEXT EVIDENCE SELECTOR
# ============================================================

def select_context_evidence(
    query: str,
    evidence: list[dict],
    supporting_evidence: list[dict] | None = None,
    architecture_evidence: list[dict] | None = None,
    limit: int = 5,
) -> dict[str, list[dict]]:
    """
    Select focused evidence for the LLM answer-generation
    context.

    This remains intentionally stricter than claim
    verification.
    """

    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "Query must be a string."
        )

    if not isinstance(
        evidence,
        list,
    ):
        raise TypeError(
            "Evidence must be a list."
        )

    supporting_evidence = (
        supporting_evidence
        if isinstance(
            supporting_evidence,
            list,
        )
        else []
    )

    query_tokens = _extract_query_tokens(
        query
    )

    query_lower = query.lower()

    # --------------------------------------------------------
    # Intent classification
    # --------------------------------------------------------
    # Architecture terms take precedence over generic question forms such
    # as "what does ... do?". Otherwise a query like "What does X depend
    # on?" can be misclassified as implementation and lose its structured
    # architecture evidence before the LLM sees it.

    if any(
        phrase in query_lower
        for phrase in (
            "architecture",
            "layer",
            "dependency",
            "dependencies",
            "depend on",
            "depends on",
            "depending on",
            "module relationship",
            "relationship",
            "structure",
            "connectivity",
            "connected module",
            "dependency graph",
        )
    ):
        query_intent = "architecture"

    elif any(
        phrase in query_lower
        for phrase in (
            "how does",
            "how do",
            "how is",
            "how are",
            "what does",
            "what is",
            "what are",
            "implementation",
            "implement",
        )
    ):
        query_intent = "implementation"

    elif any(
        phrase in query_lower
        for phrase in (
            "class",
            "method",
            "function",
            "symbol",
        )
    ):
        query_intent = "symbol"

    else:
        query_intent = "general"

    # --------------------------------------------------------
    # Score primary evidence
    # --------------------------------------------------------

    scored = []

    for item in evidence:

        if not isinstance(item, dict):
            continue

        evidence_type = str(
            item.get(
                "evidence_type",
                "code",
            )
            or "code"
        ).lower()

        if evidence_type != "code":
            continue

        (
            score,
            matched,
            file_matches,
            symbol_matches,
        ) = _score_evidence(
            query_tokens,
            item,
        )

        if score > 0:
            scored.append(
                (
                    score,
                    item,
                    matched,
                    file_matches,
                    symbol_matches,
                )
            )

    context_limit = (
        min(
            limit,
            3,
        )
        if query_intent in {
            "implementation",
            "symbol",
        }
        else limit
    )

    selected = _select_diverse_code_evidence(
        query_tokens,
        scored,
        limit=context_limit,
    )

    selected_ids = {
        id(item)
        for item in selected
    }

    # --------------------------------------------------------
    # Architecture evidence
    # --------------------------------------------------------

    architecture_source = (
        architecture_evidence
        if isinstance(architecture_evidence, list)
        else []
    )

    architecture_selected = [
        item
        for item in architecture_source
        if isinstance(item, dict)
        and str(
            item.get(
                "evidence_type",
                "",
            )
        ).lower()
        == "architecture"
    ]

    if query_intent != "architecture":
        architecture_selected = []

    # --------------------------------------------------------
    # Supporting evidence
    # --------------------------------------------------------

    supporting_candidates = []

    for item in supporting_evidence:

        if not isinstance(item, dict):
            continue

        evidence_type = str(
            item.get(
                "evidence_type",
                "code",
            )
            or "code"
        ).lower()

        if evidence_type != "code":
            continue

        (
            score,
            matched,
            file_matches,
            symbol_matches,
        ) = _score_evidence(
            query_tokens,
            item,
        )

        if score > 0:
            supporting_candidates.append(
                (
                    score,
                    item,
                    matched,
                    file_matches,
                    symbol_matches,
                )
            )

    supporting_candidates.sort(
        key=lambda entry: (
            1 if entry[4] else 0,
            1 if entry[3] else 0,
            entry[0],
        ),
        reverse=True,
    )

    # Keep implementation/symbol context tight.
    supporting_limit = (
        0
        if query_intent in {
            "implementation",
            "symbol",
        }
        else 2
    )

    focused_supporting: list[dict] = []

    for (
        _score,
        item,
        _matched,
        file_matches,
        symbol_matches,
    ) in supporting_candidates:

        if supporting_limit == 0:
            break

        if id(item) in selected_ids:
            continue

        if (
            query_intent
            in {
                "implementation",
                "symbol",
            }
            and not (
                file_matches
                or symbol_matches
                or _matched
            )
        ):
            continue

        focused_supporting.append(item)

        if (
            len(focused_supporting)
            >= supporting_limit
        ):
            break

    return {
        "evidence": selected,
        "supporting_evidence": focused_supporting,
        "architecture_evidence": architecture_selected[:4],
    }