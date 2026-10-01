import math
import re


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "where",
    "which",
    "who",
    "why",
    "with",
    "does",
}


CONCEPT_ALIASES = {
    "authentication": {"authentication", "auth"},
    "authenticate": {"authenticate", "authentication", "auth"},
    "authorization": {"authorization", "authorize", "auth"},
    "session": {"session", "sessions"},
    "request": {"request", "requests"},
    "response": {"response", "responses"},
    "adapter": {"adapter", "adapters"},
    "cookie": {"cookie", "cookies"},
    "exception": {"exception", "exceptions"},
    "hook": {"hook", "hooks"},
    "model": {"model", "models"},
    "utility": {"utility", "utils"},
    "compatibility": {"compatibility", "compat"},
}


GENERIC_QUERY_WORDS = {
    "handle",
    "handles",
    "send",
    "sends",
    "sent",
    "work",
    "works",
    "working",
    "implement",
    "implementation",
    "process",
    "processes",
    "perform",
    "create",
    "prepare",
    "make",
    "made",
    "use",
    "uses",
    "using",
    "support",
    "supports",
    "manage",
    "manages",
    "requests",
}


def tokenize(text: str) -> list[str]:
    if not isinstance(text, str):
        raise TypeError("Text must be a string.")

    tokens = re.findall(
        r"[a-zA-Z_][a-zA-Z0-9_]*",
        text.lower(),
    )

    expanded_tokens = []

    for token in tokens:
        expanded_tokens.append(token)

        if "_" in token:
            expanded_tokens.extend(
                part
                for part in token.split("_")
                if part
            )

    return [
        token
        for token in expanded_tokens
        if token not in STOP_WORDS
    ]


def _unique_tokens(tokens: list[str]) -> set[str]:
    return set(tokens)


def _concept_tokens(tokens: set[str]) -> set[str]:
    expanded = set(tokens)

    for token in list(tokens):
        aliases = CONCEPT_ALIASES.get(token)

        if aliases:
            expanded.update(aliases)

    return expanded


def _query_anchor_tokens(query: str) -> set[str]:
    """
    Extract important repository concepts.

    Example:
        How does requests handle authentication?
        -> {"authentication", "auth"}
    """

    raw_tokens = {
        token
        for token in tokenize(query)
        if token not in GENERIC_QUERY_WORDS
        and token != "requests"
    }

    return _concept_tokens(raw_tokens)


def _build_idf_weights(
    chunks: list[dict],
) -> dict[str, float]:
    if not isinstance(chunks, list):
        raise TypeError("Chunks must be a list.")

    document_frequency: dict[str, int] = {}
    document_count = 0

    for chunk in chunks:
        if not isinstance(chunk, dict):
            continue

        content = str(chunk.get("content", ""))
        file_path = str(chunk.get("file", ""))

        tokens = set(
            tokenize(
                content + " " + file_path
            )
        )

        if not tokens:
            continue

        document_count += 1

        for token in tokens:
            document_frequency[token] = (
                document_frequency.get(token, 0) + 1
            )

    if document_count == 0:
        return {}

    return {
        token: (
            math.log(
                (document_count + 1)
                / (frequency + 1)
            )
            + 1.0
        )
        for token, frequency in document_frequency.items()
    }


def _repository_role(file_path: str) -> str:
    normalized_path = file_path.replace(
        "\\",
        "/",
    ).lower()

    path_parts = normalized_path.split("/")

    if "test" in path_parts or any(
        part.startswith("test_")
        or part.endswith("_test.py")
        for part in path_parts
    ):
        return "test"

    if (
        "src" in path_parts
        or "lib" in path_parts
        or "app" in path_parts
    ):
        return "production"

    return "neutral"


def _module_tokens(file_path: str) -> set[str]:
    """
    Extract only the concrete Python module name.

    Example:
        src/requests/sessions.py
        -> {"sessions", "session"}
    """

    normalized_path = file_path.replace(
        "\\",
        "/",
    )

    parts = normalized_path.split("/")

    if not parts:
        return set()

    filename = parts[-1]

    if filename.endswith(".py"):
        filename = filename[:-3]

    if not filename:
        return set()

    return _concept_tokens(
        _unique_tokens(
            tokenize(filename)
        )
    )


def _module_score(
    query_tokens: set[str],
    file_path: str,
) -> float:
    if not query_tokens:
        return 0.0

    module_tokens = _module_tokens(
        file_path
    )

    matches = query_tokens & module_tokens

    if not matches:
        return 0.0

    return min(
        1.0,
        len(matches) / len(query_tokens),
    )


def _symbol_entries(chunk: dict) -> list[dict]:
    symbols = chunk.get(
        "symbols",
        {},
    )

    if not isinstance(symbols, dict):
        return []

    entries = []

    for group in (
        "classes",
        "functions",
    ):
        for symbol in symbols.get(
            group,
            [],
        ):
            if isinstance(symbol, dict):
                entries.append(symbol)
            else:
                entries.append(
                    {
                        "name": str(symbol),
                    }
                )

    return entries


def _symbol_score(
    query_tokens: set[str],
    chunk: dict,
) -> float:
    if not query_tokens:
        return 0.0

    entries = _symbol_entries(chunk)

    if not entries:
        return 0.0

    symbol_tokens = set()

    for symbol in entries:
        symbol_tokens.update(
            _concept_tokens(
                _unique_tokens(
                    tokenize(
                        str(
                            symbol.get(
                                "name",
                                "",
                            )
                        )
                    )
                )
            )
        )

    if not symbol_tokens:
        return 0.0

    matches = query_tokens & symbol_tokens

    if not matches:
        return 0.0

    base_score = (
        len(matches) / len(query_tokens)
    )

    chunk_start = chunk.get(
        "start_line"
    )

    chunk_end = chunk.get(
        "end_line"
    )

    if not isinstance(chunk_start, int):
        return base_score

    if not isinstance(chunk_end, int):
        return base_score

    for symbol in entries:
        symbol_name = str(
            symbol.get(
                "name",
                "",
            )
        )

        symbol_tokens = _concept_tokens(
            _unique_tokens(
                tokenize(symbol_name)
            )
        )

        if not (
            query_tokens & symbol_tokens
        ):
            continue

        symbol_start = symbol.get(
            "start_line"
        )

        if (
            isinstance(symbol_start, int)
            and chunk_start
            <= symbol_start
            <= chunk_end
        ):
            return min(
                1.0,
                base_score + 0.5,
            )

    return base_score


def _has_primary_anchor(
    query: str,
    chunk: dict,
) -> bool:
    """
    Primary evidence requires a concrete module or
    symbol anchor.

    Content-only overlap is NOT enough.
    """

    anchors = _query_anchor_tokens(query)

    if not anchors:
        return False

    file_path = str(
        chunk.get(
            "file",
            "",
        )
    )

    module_tokens = _module_tokens(
        file_path
    )

    if anchors & module_tokens:
        return True

    symbol_tokens = set()

    for symbol in _symbol_entries(chunk):
        symbol_tokens.update(
            _concept_tokens(
                _unique_tokens(
                    tokenize(
                        str(
                            symbol.get(
                                "name",
                                "",
                            )
                        )
                    )
                )
            )
        )

    return bool(
        anchors & symbol_tokens
    )


def _anchor_score(
    query: str,
    chunk: dict,
) -> float:
    """
    Anchor hierarchy:

        module match   -> strongest
        symbol match   -> strong
        content match  -> weak
    """

    anchors = _query_anchor_tokens(query)

    if not anchors:
        return 0.0

    file_path = str(
        chunk.get(
            "file",
            "",
        )
    )

    module_tokens = _module_tokens(
        file_path
    )

    module_matches = (
        anchors & module_tokens
    )

    if module_matches:
        return min(
            1.0,
            0.85
            + (
                0.15
                * len(module_matches)
                / len(anchors)
            ),
        )

    symbol_tokens = set()

    for symbol in _symbol_entries(chunk):
        symbol_tokens.update(
            _concept_tokens(
                _unique_tokens(
                    tokenize(
                        str(
                            symbol.get(
                                "name",
                                "",
                            )
                        )
                    )
                )
            )
        )

    symbol_matches = (
        anchors & symbol_tokens
    )

    if symbol_matches:
        return min(
            0.85,
            0.65
            + (
                0.20
                * len(symbol_matches)
                / len(anchors)
            ),
        )

    content_tokens = set(
        tokenize(
            str(
                chunk.get(
                    "content",
                    "",
                )
            )
        )
    )

    content_matches = (
        anchors & content_tokens
    )

    if not content_matches:
        return 0.0

    return min(
        0.45,
        0.25
        + (
            0.20
            * len(content_matches)
            / len(anchors)
        ),
    )


def _role_score(file_path: str) -> float:
    role = _repository_role(file_path)

    if role == "production":
        return 1.0

    if role == "test":
        return 0.0

    return 0.5


def classify_query_intent(query: str) -> str:
    if not isinstance(query, str):
        raise TypeError("Query must be a string.")

    query_tokens = _unique_tokens(
        tokenize(query)
    )

    if not query_tokens:
        return "concept"

    symbol_indicators = {
        "class",
        "function",
        "method",
        "symbol",
    }

    implementation_indicators = {
        "implement",
        "implementation",
        "work",
        "works",
        "handle",
        "handles",
        "send",
        "prepare",
        "process",
        "create",
        "perform",
    }

    architecture_indicators = {
        "architecture",
        "dependency",
        "dependencies",
        "depend",
        "depends",
        "depending",
        "structure",
        "layer",
        "layers",
        "module",
        "modules",
    }

    if query_tokens & symbol_indicators:
        return "symbol"

    if query_tokens & architecture_indicators:
        return "architecture"

    if query_tokens & implementation_indicators:
        return "implementation"

    if len(query_tokens) == 1:
        return "symbol"

    return "concept"


def _intent_score(
    query_intent: str,
    file_path: str,
) -> float:
    role = _repository_role(file_path)

    if query_intent == "architecture":
        if role == "production":
            return 1.0

        if role == "test":
            return 0.4

        return 0.6

    if query_intent == "implementation":
        if role == "production":
            return 1.0

        if role == "test":
            return 0.2

        return 0.6

    if query_intent == "symbol":
        if role == "production":
            return 1.0

        if role == "test":
            return 0.4

        return 0.6

    return 0.5


def score_chunk(
    query: str,
    chunk: dict,
    idf_weights: dict[str, float] | None = None,
) -> float:
    if not isinstance(chunk, dict):
        raise TypeError("Chunk must be a dictionary.")

    content = str(
        chunk.get(
            "content",
            "",
        )
    )

    file_path = str(
        chunk.get(
            "file",
            "",
        )
    )

    query_tokens = _unique_tokens(
        tokenize(query)
    )

    if not query_tokens:
        return 0.0

    content_tokens = tokenize(content)
    content_token_set = _unique_tokens(
        content_tokens
    )

    file_tokens = _unique_tokens(
        tokenize(file_path)
    )

    query_normalized = " ".join(
        tokenize(query)
    )

    content_normalized = " ".join(
        content_tokens
    )

    exact_phrase_score = 0.0

    if (
        query_normalized
        and query_normalized
        in content_normalized
    ):
        exact_phrase_score = 1.0

    content_matches = (
        query_tokens & content_token_set
    )

    if idf_weights:
        total_query_weight = sum(
            idf_weights.get(
                token,
                1.0,
            )
            for token in query_tokens
        )

        matched_query_weight = sum(
            idf_weights.get(
                token,
                1.0,
            )
            for token in content_matches
        )

        content_score = (
            matched_query_weight
            / total_query_weight
            if total_query_weight > 0
            else 0.0
        )
    else:
        content_score = (
            len(content_matches)
            / len(query_tokens)
        )

    file_matches = (
        query_tokens & file_tokens
    )

    file_score = (
        len(file_matches)
        / len(query_tokens)
    )

    frequency_score = 0.0

    for token in query_tokens:
        frequency_score += (
            content_tokens.count(token)
        )

    if frequency_score > 0:
        frequency_score = min(
            frequency_score / 10,
            1.0,
        )

    symbol_score = _symbol_score(
        query_tokens,
        chunk,
    )

    query_intent = classify_query_intent(
        query
    )

    definition_score = 0.0

    if query_intent == "symbol":
        chunk_start = chunk.get(
            "start_line"
        )

        chunk_end = chunk.get(
            "end_line"
        )

        if (
            isinstance(chunk_start, int)
            and isinstance(chunk_end, int)
        ):
            for symbol in _symbol_entries(
                chunk
            ):
                name_tokens = _concept_tokens(
                    _unique_tokens(
                        tokenize(
                            str(
                                symbol.get(
                                    "name",
                                    "",
                                )
                            )
                        )
                    )
                )

                if not (
                    query_tokens & name_tokens
                ):
                    continue

                symbol_start = symbol.get(
                    "start_line"
                )

                if (
                    isinstance(symbol_start, int)
                    and chunk_start
                    <= symbol_start
                    <= chunk_end
                ):
                    definition_score = 1.0
                    break

    module_score = _module_score(
        _concept_tokens(query_tokens),
        file_path,
    )

    anchor_score = _anchor_score(
        query,
        chunk,
    )

    if (
        exact_phrase_score == 0.0
        and content_score == 0.0
        and file_score == 0.0
        and frequency_score == 0.0
        and symbol_score == 0.0
        and definition_score == 0.0
        and module_score == 0.0
        and anchor_score == 0.0
    ):
        return 0.0

    role_score = _role_score(
        file_path
    )

    score = (
        exact_phrase_score * 0.07
        + content_score * 0.16
        + file_score * 0.03
        + frequency_score * 0.02
        + role_score * 0.06
        + symbol_score * 0.19
        + definition_score * 0.12
        + module_score * 0.20
        + anchor_score * 0.15
    )

    return round(
        score,
        6,
    )


def _chunk_similarity(
    first: dict,
    second: dict,
) -> float:
    first_text = (
        str(first.get("content", ""))
        + " "
        + str(first.get("file", ""))
    )

    second_text = (
        str(second.get("content", ""))
        + " "
        + str(second.get("file", ""))
    )

    first_tokens = set(
        tokenize(first_text)
    )

    second_tokens = set(
        tokenize(second_text)
    )

    if not first_tokens or not second_tokens:
        return 0.0

    intersection = (
        first_tokens & second_tokens
    )

    union = (
        first_tokens | second_tokens
    )

    if not union:
        return 0.0

    return len(intersection) / len(union)


def _select_diverse_results(
    scored_chunks: list[dict],
    top_k: int,
    diversity_lambda: float = 0.75,
) -> list[dict]:
    if not scored_chunks:
        return []

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    if not 0.0 < diversity_lambda <= 1.0:
        raise ValueError(
            "diversity_lambda must be between 0 and 1."
        )

    candidates = list(
        scored_chunks
    )

    selected = []

    first = max(
        candidates,
        key=lambda item: (
            item.get(
                "retrieval_score",
                0.0,
            ),
            item.get(
                "file",
                "",
            ),
            item.get(
                "start_line",
                0,
            ),
        ),
    )

    selected.append(first)
    candidates.remove(first)

    while (
        candidates
        and len(selected) < top_k
    ):
        best_candidate = None
        best_mmr_score = float("-inf")

        for candidate in candidates:
            relevance = candidate.get(
                "retrieval_score",
                0.0,
            )

            max_similarity = max(
                (
                    _chunk_similarity(
                        candidate,
                        previous,
                    )
                    for previous in selected
                ),
                default=0.0,
            )

            mmr_score = (
                diversity_lambda * relevance
                - (
                    1.0
                    - diversity_lambda
                )
                * max_similarity
            )

            candidate_key = (
                mmr_score,
                relevance,
                candidate.get(
                    "file",
                    "",
                ),
                candidate.get(
                    "start_line",
                    0,
                ),
            )

            current_key = (
                best_mmr_score,
                best_candidate.get(
                    "retrieval_score",
                    0.0,
                )
                if best_candidate
                else 0.0,
                best_candidate.get(
                    "file",
                    "",
                )
                if best_candidate
                else "",
                best_candidate.get(
                    "start_line",
                    0,
                )
                if best_candidate
                else 0,
            )

            if candidate_key > current_key:
                best_candidate = candidate
                best_mmr_score = mmr_score

        if best_candidate is None:
            break

        selected.append(
            best_candidate
        )

        candidates.remove(
            best_candidate
        )

    selected.sort(
        key=lambda item: (
            -item.get(
                "retrieval_score",
                0.0,
            ),
            item.get(
                "file",
                "",
            ),
            item.get(
                "start_line",
                0,
            ),
        )
    )

    return selected


def _filter_weak_candidates(
    query: str,
    scored_chunks: list[dict],
) -> list[dict]:
    """
    Apply anchor-aware candidate filtering.

    If a concrete component is identified:
        primary evidence is preserved.

    Supporting production evidence is allowed only when
    it is sufficiently strong.

    Test evidence is excluded from implementation retrieval
    unless it has a direct module/symbol anchor.
    """

    if not scored_chunks:
        return []

    query_intent = classify_query_intent(
        query
    )

    primary = [
        chunk
        for chunk in scored_chunks
        if _has_primary_anchor(
            query,
            chunk,
        )
    ]

    if not primary:
        return scored_chunks

    max_primary_score = max(
        chunk.get(
            "retrieval_score",
            0.0,
        )
        for chunk in primary
    )

    supporting_threshold = max(
        0.58,
        max_primary_score * 0.78,
    )

    filtered = []

    for chunk in scored_chunks:
        file_path = str(
            chunk.get(
                "file",
                "",
            )
        )

        role = _repository_role(
            file_path
        )

        is_primary = _has_primary_anchor(
            query,
            chunk,
        )

        score = chunk.get(
            "retrieval_score",
            0.0,
        )

        if is_primary:
            filtered.append(chunk)
            continue

        if (
            query_intent == "implementation"
            and role == "test"
        ):
            continue

        if (
            role == "production"
            and score >= supporting_threshold
        ):
            filtered.append(chunk)

    return filtered


def retrieve_chunks(
    query: str,
    chunks: list[dict],
    top_k: int = 5,
) -> list[dict]:
    if not isinstance(
        query,
        str,
    ):
        raise TypeError(
            "Query must be a string."
        )

    if not query.strip():
        raise ValueError(
            "Query cannot be empty."
        )

    if not isinstance(
        chunks,
        list,
    ):
        raise TypeError(
            "Chunks must be a list."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    query_intent = classify_query_intent(
        query
    )

    idf_weights = _build_idf_weights(
        chunks
    )

    scored_chunks = []

    for chunk in chunks:
        base_score = score_chunk(
            query,
            chunk,
            idf_weights=idf_weights,
        )

        if base_score <= 0:
            continue

        file_path = str(
            chunk.get(
                "file",
                "",
            )
        )

        intent_score = _intent_score(
            query_intent,
            file_path,
        )

        reranking_adjustment = (
            intent_score - 0.5
        ) * 0.14

        final_score = round(
            base_score
            + reranking_adjustment,
            6,
        )

        result = dict(
            chunk
        )

        result[
            "retrieval_score"
        ] = final_score

        result[
            "retrieval_role"
        ] = (
            "primary"
            if _has_primary_anchor(
                query,
                chunk,
            )
            else "supporting"
        )

        scored_chunks.append(
            result
        )

    scored_chunks.sort(
        key=lambda item: (
            -item.get(
                "retrieval_score",
                0.0,
            ),
            item.get(
                "file",
                "",
            ),
            item.get(
                "start_line",
                0,
            ),
        )
    )

    filtered_chunks = _filter_weak_candidates(
        query,
        scored_chunks,
    )

    candidate_limit = max(
        top_k * 4,
        top_k,
    )

    candidates = filtered_chunks[
        :candidate_limit
    ]

    return _select_diverse_results(
        candidates,
        top_k=top_k,
        diversity_lambda=0.75,
    )


def expand_with_neighboring_chunks(
    retrieved_chunks: list[dict],
    all_chunks: list[dict],
    max_neighbors: int = 1,
) -> list[dict]:
    if not isinstance(
        retrieved_chunks,
        list,
    ):
        raise TypeError(
            "Retrieved chunks must be a list."
        )

    if not isinstance(
        all_chunks,
        list,
    ):
        raise TypeError(
            "All chunks must be a list."
        )

    if max_neighbors < 0:
        raise ValueError(
            "max_neighbors cannot be negative."
        )

    if not retrieved_chunks:
        return []

    chunks_by_file = {}

    for chunk in all_chunks:
        file_path = chunk.get(
            "file",
            "",
        )

        chunks_by_file.setdefault(
            file_path,
            [],
        ).append(chunk)

    for file_chunks in chunks_by_file.values():
        file_chunks.sort(
            key=lambda item: (
                item.get(
                    "start_line",
                    0,
                ),
                item.get(
                    "end_line",
                    0,
                ),
            )
        )

    expanded = []
    seen = set()

    for retrieved in retrieved_chunks:
        file_path = retrieved.get(
            "file",
            "",
        )

        file_chunks = chunks_by_file.get(
            file_path,
            [],
        )

        retrieved_key = (
            file_path,
            retrieved.get(
                "start_line"
            ),
            retrieved.get(
                "end_line"
            ),
        )

        if retrieved_key in seen:
            continue

        original = dict(
            retrieved
        )

        original["context_role"] = (
            "retrieved"
        )

        expanded.append(
            original
        )

        seen.add(
            retrieved_key
        )

        retrieved_index = None

        for index, chunk in enumerate(
            file_chunks
        ):
            chunk_key = (
                file_path,
                chunk.get(
                    "start_line"
                ),
                chunk.get(
                    "end_line"
                ),
            )

            if chunk_key == retrieved_key:
                retrieved_index = index
                break

        if retrieved_index is None:
            continue

        base_score = retrieved.get(
            "retrieval_score",
            0.0,
        )

        for distance in range(
            1,
            max_neighbors + 1,
        ):
            neighbor_indexes = [
                retrieved_index - distance,
                retrieved_index + distance,
            ]

            for neighbor_index in neighbor_indexes:
                if (
                    neighbor_index < 0
                    or neighbor_index >= len(file_chunks)
                ):
                    continue

                neighbor = file_chunks[
                    neighbor_index
                ]

                neighbor_key = (
                    file_path,
                    neighbor.get(
                        "start_line"
                    ),
                    neighbor.get(
                        "end_line"
                    ),
                )

                if neighbor_key in seen:
                    continue

                neighbor_result = dict(
                    neighbor
                )

                neighbor_result[
                    "retrieval_score"
                ] = round(
                    base_score * 0.5,
                    6,
                )

                neighbor_result[
                    "context_role"
                ] = "neighbor"

                neighbor_result[
                "retrieval_role"
                ] = "supporting"

                expanded.append(
                    neighbor_result
                )

                seen.add(
                    neighbor_key
                )

    expanded.sort(
        key=lambda item: (
            0
            if item.get(
                "context_role"
            ) == "retrieved"
            else 1,
            -item.get(
                "retrieval_score",
                0.0,
            ),
            item.get(
                "file",
                "",
            ),
            item.get(
                "start_line",
                0,
            ),
        )
    )

    return expanded