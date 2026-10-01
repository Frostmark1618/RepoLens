import re

def _normalize(text: str) -> str:
    return " ".join(
        text.lower().replace("\\", "/").split()
    )


def _query_tokens(query: str) -> set[str]:
    normalized_query = (
        _normalize(query)
        .replace(".", " ")
        .replace("/", " ")
        .replace("_", " ")
    )

    return {
        token
        for token in normalized_query.split()
        if token
    }


def _module_matches_query(
    module: dict,
    query_tokens: set[str],
) -> bool:
    module_name = str(
        module.get("module_name", "")
    )

    file_path = str(
        module.get("file", "")
    )

    searchable_text = (
        f"{module_name} {file_path}"
    )

    searchable_tokens = set(
        _normalize(searchable_text)
        .replace(".", " ")
        .replace("/", " ")
        .replace("_", " ")
        .split()
    )

    normalized_query_tokens = set()

    for token in query_tokens:
        normalized_query_tokens.add(token)

        if token.endswith("s") and len(token) > 3:
            normalized_query_tokens.add(
                token[:-1]
            )

    normalized_searchable_tokens = set()

    for token in searchable_tokens:
        normalized_searchable_tokens.add(token)

        if token.endswith("s") and len(token) > 3:
            normalized_searchable_tokens.add(
                token[:-1]
            )

    return bool(
        normalized_query_tokens
        & normalized_searchable_tokens
    )


def _build_module_evidence(
    module: dict,
    module_by_file: dict[str, dict] | None = None,
) -> dict:
    outgoing_dependencies = module.get("outgoing_dependencies", [])
    incoming_dependencies = module.get("incoming_dependencies", [])

    if not isinstance(outgoing_dependencies, list):
        outgoing_dependencies = []
    if not isinstance(incoming_dependencies, list):
        incoming_dependencies = []

    module_by_file = module_by_file or {}

    def dependency_modules(values: list) -> list[str]:
        labels = []
        for value in values:
            key = str(value).replace("\\", "/")
            target = module_by_file.get(key)
            if target is not None:
                labels.append(str(target.get("module_name", value)))
            else:
                labels.append(str(value))
        return labels

    return {
        "evidence_type": "architecture",
        "evidence_subtype": "module_dependencies",
        "file": module.get("file", ""),
        "module_name": module.get(
            "module_name",
            "",
        ),
        "layer": module.get(
            "layer",
            "unknown",
        ),
        "outgoing_dependencies": outgoing_dependencies,
        "incoming_dependencies": incoming_dependencies,
        "outgoing_dependency_modules": dependency_modules(outgoing_dependencies),
        "incoming_dependency_modules": dependency_modules(incoming_dependencies),
        "outgoing_count": module.get("outgoing_count"),
        "incoming_count": module.get("incoming_count"),
        "total_connections": module.get("total_connections"),
        "status": "fact",
    }

def _is_global_architecture_query(
    query: str,
) -> bool:
    normalized_query = _normalize(query)

    global_patterns = [
        "most connected",
        "highest connected",
        "top connected",
        "highest dependency connectivity",
        "highest connectivity",
        "greatest connectivity",
        "greatest dependency connectivity",
        "greatest dependency connections",
        "most connected component",
        "most connected file",
        "highest dependency connections",
        "most dependency connections",
        "most connected modules",
        "highest connected modules",
        "modules with highest connectivity",
        "modules with the highest connectivity",
        "modules with highest dependency connectivity",
        "modules with the highest dependency connectivity",
        "highest number of dependency connections",
        "highest number of connections",
        "most dependency connections",
        "most dependency relationships",
        "most dependencies",
        "most outgoing dependencies",
        "highest outgoing dependencies",
        "highest number of outgoing dependencies",
        "most incoming dependencies",
        "highest incoming dependencies",
        "highest number of incoming dependencies",
        "module with the highest dependency connections",
        "module with the most dependency connections",
        "module with the most dependencies",
        "architecture hotspots",
        "isolated modules",
        "isolated nodes",
        "dependency graph",
        "dependency edges",
        "number of edges",
        "edge count",
        "production modules",
        "fewest dependency connections",
        "least dependency connections",
        "lowest number of dependency connections",
        "lowest dependency connections",
        "fewest connections",
        "least connections",
        "fewest dependency relationships",
        "least dependency relationships",
    ]

    if any(
        pattern in normalized_query
        for pattern in global_patterns
    ):
        return True

    # Queries that ask which module has a specific connection count are also
    # repository-wide ranking/look-up questions, even when they do not use
    # the words "highest" or "most".
    return bool(
        re.search(
            r"\b(?:which|what)\s+module\b.*\b\d+\s+(?:dependency\s+)?connections?\b",
            normalized_query,
        )
    )


def _build_global_architecture_evidence(
    snapshot: dict,
) -> list[dict]:
    graph_summary = snapshot.get(
        "graph_summary",
        {},
    )

    if not isinstance(graph_summary, dict):
        return []

    evidence = []

    node_count = graph_summary.get(
        "node_count",
        0,
    )

    edge_count = graph_summary.get(
        "edge_count",
        0,
    )

    isolated_nodes = graph_summary.get(
        "isolated_nodes",
        [],
    )

    if not isinstance(
        isolated_nodes,
        list,
    ):
        isolated_nodes = []

    # Do not trust a precomputed ranking field when the complete production
    # module facts are available. Recompute the ranking from the same module
    # records used by the Dependencies page so a stale/corrupt graph-summary
    # ordering cannot silently become an authoritative Q&A fact.
    production_modules = snapshot.get(
        "production_modules",
        [],
    )
    if not isinstance(production_modules, list):
        production_modules = []

    module_by_file = {
        str(module.get("file", "")): module
        for module in production_modules
        if isinstance(module, dict)
    }

    ranked_modules = [
        module for module in production_modules
        if isinstance(module, dict)
    ]

    def ranked_fact(key: str) -> list[dict]:
        return [
            {
                "file": module.get("file", ""),
                "module_name": module.get("module_name", ""),
                "incoming_count": module.get("incoming_count"),
                "outgoing_count": module.get("outgoing_count"),
                "total_connections": module.get("total_connections"),
            }
            for module in sorted(
                ranked_modules,
                key=lambda module: (
                    -(module.get(key) or 0),
                    str(module.get("module_name", "")),
                ),
            )
        ]

    all_module_facts = ranked_fact("total_connections")
    top_connected_modules = all_module_facts[:5]
    top_outgoing_modules = ranked_fact("outgoing_count")[:5]
    top_incoming_modules = ranked_fact("incoming_count")[:5]

    evidence.append(
        {
            "evidence_type": "architecture",
            "evidence_subtype": "graph_summary",
            # The existing RepoLens evidence contract requires every
            # architecture evidence item to carry a non-empty module_name.
            # Global graph evidence is repository-scoped, so use an explicit
            # repository scope identifier rather than inventing a module.
            "module_name": "repository",
            "file": "repository-analysis",
            "node_count": node_count,
            "edge_count": edge_count,
            "isolated_node_count": graph_summary.get(
                "isolated_node_count",
                len(isolated_nodes),
            ),
            "isolated_nodes": isolated_nodes,
            "top_connected_nodes": [
                    item.get("file", "")
                    for item in top_connected_modules
                    if isinstance(item, dict) and item.get("file")
                ],
            "top_connected_modules": top_connected_modules,
            "top_outgoing_modules": top_outgoing_modules,
            "top_incoming_modules": top_incoming_modules,
            "all_module_facts": all_module_facts,
            "status": "fact",
        }
    )

    return evidence


def retrieve_architecture_evidence(
    query: str,
    snapshot: dict,
    top_k: int = 5,
) -> list[dict]:
    """
    Retrieve deterministic architecture evidence
    from an architecture snapshot.

    This does not inspect code text. It uses only
    structured architecture facts already produced
    by the analysis pipeline.
    """

    if not isinstance(query, str):
        raise TypeError(
            "Query must be a string."
        )

    if not isinstance(snapshot, dict):
        raise TypeError(
            "Snapshot must be a dictionary."
        )

    if not isinstance(top_k, int):
        raise TypeError(
            "top_k must be an integer."
        )

    if top_k <= 0:
        raise ValueError(
            "top_k must be greater than zero."
        )

    query_tokens = _query_tokens(query)

    if not query_tokens:
        return []

    if _is_global_architecture_query(query):
        return _build_global_architecture_evidence(
            snapshot
        )[:top_k]

    production_modules = snapshot.get(
        "production_modules",
        [],
    )

    if not isinstance(
        production_modules,
        list,
    ):
        return []

    matched_modules = []

    module_by_file = {
        str(module.get("file", "")).replace("\\", "/"): module
        for module in production_modules
        if isinstance(module, dict)
    }

    for module in production_modules:
        if not isinstance(module, dict):
            continue

        if _module_matches_query(
            module,
            query_tokens,
        ):
            evidence = _build_module_evidence(module, module_by_file)

            module_name = str(
                module.get("module_name", "")
            )

            normalized_module_tokens = set(
                _normalize(module_name)
                .replace(".", " ")
                .replace("/", " ")
                .replace("_", " ")
                .split()
            )

            query_overlap = len(
                normalized_module_tokens
                & query_tokens
            )

            normalized_query = _normalize(query)
            normalized_module_name = _normalize(module_name)
            exact_module_match = int(
                bool(normalized_module_name)
                and (
                    normalized_module_name in normalized_query
                    or normalized_query.endswith(normalized_module_name)
                )
            )

            matched_modules.append(
                (
                    exact_module_match,
                    query_overlap,
                    evidence,
                )
            )

    matched_modules.sort(
        key=lambda item: (
            -item[0],
            -item[1],
            -(item[2].get("total_connections") or 0),
            item[2]["module_name"],
        )
    )

    return [
        evidence
        for _, _, evidence in matched_modules[:top_k]
    ]