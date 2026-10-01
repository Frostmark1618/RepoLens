def build_rag_context(
    retrieval_result: dict,
) -> str:
    """
    Build an evidence-bounded context string from
    retrieved repository evidence.

    Primary evidence and supporting neighboring
    context are rendered separately.
    """

    if not isinstance(retrieval_result, dict):
        raise TypeError(
            "Retrieval result must be a dictionary."
        )

    query = retrieval_result.get(
        "query",
        "",
    )

    evidence = retrieval_result.get(
        "evidence",
        [],
    )

    supporting_evidence = retrieval_result.get(
        "supporting_evidence",
        [],
    )

    architecture_evidence = retrieval_result.get(
        "architecture_evidence",
        [],
    )

    metadata_evidence = retrieval_result.get(
        "metadata_evidence",
        [],
    )

    if not isinstance(query, str):
        query = str(query)

    if not isinstance(evidence, list):
        raise TypeError(
            "Evidence must be a list."
        )

    if not isinstance(
        supporting_evidence,
        list,
    ):
        raise TypeError(
            "Supporting evidence must be a list."
        )

    if not isinstance(
        architecture_evidence,
        list,
    ):
        raise TypeError(
            "Architecture evidence must be a list."
        )

    if not isinstance(metadata_evidence, list):
        raise TypeError("Metadata evidence must be a list.")

    if (
        not evidence
        and not supporting_evidence
        and not architecture_evidence
        and not metadata_evidence
    ):
        return (
            "No repository evidence was retrieved "
            "for this query."
        )

    context_sections = [
        "REPOSITORY EVIDENCE",
        f"User Query: {query}",
        "",
    ]

    for index, item in enumerate(
        evidence,
        1,
    ):
        context_sections.extend(
            _format_evidence_item(
                item,
                index,
                "Primary Evidence",
            )
        )

    for index, item in enumerate(
        supporting_evidence,
        1,
    ):
        context_sections.extend(
            _format_evidence_item(
                item,
                index,
                "Supporting Context",
            )
        )

    if metadata_evidence:
        context_sections.extend(
            [
                "REPOSITORY METADATA FACTS",
                "",
            ]
        )
        for index, item in enumerate(metadata_evidence, 1):
            context_sections.extend(
                [
                    f"[Metadata Fact {index}]",
                    f"Field: {item.get('label', '')}",
                    f"Value: {item.get('value', '')}",
                    f"Source: {item.get('file', '')}",
                    "Status: fact",
                    "",
                ]
            )

    if architecture_evidence:
        context_sections.extend(
            [
                "ARCHITECTURE FACTS",
                "",
            ]
        )

        for index, item in enumerate(
            architecture_evidence,
            1,
        ):
            if item.get("evidence_subtype") == (
                "graph_summary"
            ):
                formatted = (
                    _format_global_architecture_evidence(
                        item,
                        index,
                    )
                )
            else:
                formatted = (
                    _format_architecture_evidence_item(
                        item,
                        index,
                    )
                )

            context_sections.append(formatted)
            context_sections.append("")

    return "\n".join(
        context_sections
    )


def _format_evidence_item(
    item: dict,
    index: int,
    section_name: str,
) -> list[str]:
    """
    Format one evidence item for the RAG context.
    """

    file_path = item.get(
        "file",
        "unknown",
    )

    start_line = item.get(
        "start_line",
        "?",
    )

    end_line = item.get(
        "end_line",
        "?",
    )

    score = item.get(
        "retrieval_score",
        0.0,
    )

    content = item.get(
        "content",
        "",
    )

    symbols = item.get(
        "symbols",
        {},
    )

    if not isinstance(symbols, dict):
        symbols = {}

    classes = symbols.get(
        "classes",
        [],
    )

    functions = symbols.get(
        "functions",
        [],
    )

    class_names = []

    for symbol in classes:
        if isinstance(symbol, dict):
            class_names.append(
                str(symbol.get("name", ""))
            )
        else:
            class_names.append(
                str(symbol)
            )

    function_names = []

    for symbol in functions:
        if isinstance(symbol, dict):
            function_names.append(
                str(symbol.get("name", ""))
            )
        else:
            function_names.append(
                str(symbol)
            )

    return [
        f"[{section_name} {index}]",
        (
            f"File: {file_path} "
            f"(lines {start_line}-{end_line})"
        ),
        f"Retrieval Score: {score}",
        f"Evidence Role: {item.get('retrieval_role', 'supporting')}",
        (
            "Classes: "
            f"{', '.join(class_names) if class_names else 'None'}"
        ),
        (
            "Functions: "
            f"{', '.join(function_names) if function_names else 'None'}"
        ),
        "Content:",
        content,
        "",
    ]


def _format_architecture_evidence_item(
    item: dict,
    index: int,
) -> str:
    outgoing = item.get(
        "outgoing_dependencies",
        [],
    )

    incoming = item.get(
        "incoming_dependencies",
        [],
    )

    if not isinstance(outgoing, list):
        outgoing = []

    if not isinstance(incoming, list):
        incoming = []

    lines = [
        f"[Architecture Fact {index}]",
        f"Module: {item.get('module_name', '')}",
        f"File: {item.get('file', '')}",
        f"Layer: {item.get('layer', 'unknown')}",
        (
            "Outgoing Dependencies: "
            f"{item.get('outgoing_count', 0)}"
        ),
        (
            "Incoming Dependencies: "
            f"{item.get('incoming_count', 0)}"
        ),
        (
            "Total Connections: "
            f"{item.get('total_connections', 0)}"
        ),
        f"Status: {item.get('status', 'unknown')}",
    ]

    if outgoing:
        lines.append(
            "Depends On:"
        )
        lines.extend(
            f"- {dependency}"
            for dependency in outgoing
        )

    if incoming:
        lines.append(
            "Depended On By:"
        )
        lines.extend(
            f"- {dependency}"
            for dependency in incoming
        )

    return "\n".join(lines)


def _format_global_architecture_evidence(
    item: dict,
    index: int,
) -> str:
    top_connected = item.get("top_connected_modules", [])
    top_outgoing = item.get("top_outgoing_modules", [])
    top_incoming = item.get("top_incoming_modules", [])
    isolated_nodes = item.get("isolated_nodes", [])

    if not isinstance(top_connected, list):
        top_connected = []
    if not isinstance(top_outgoing, list):
        top_outgoing = []
    if not isinstance(top_incoming, list):
        top_incoming = []
    if not isinstance(isolated_nodes, list):
        isolated_nodes = []

    lines = [
        f"[Architecture Fact {index}]",
        "Scope: Repository Architecture",
        f"Production Modules: {item.get('node_count', 0)}",
        f"Dependency Edges: {item.get('edge_count', 0)}",
        f"Isolated Modules: {item.get('isolated_node_count', 0)}",
        f"Status: {item.get('status', 'unknown')}",
    ]

    def append_ranked(title: str, values: list, count_key: str) -> None:
        if not values:
            return
        lines.append(title)
        for rank, module in enumerate(values, start=1):
            if not isinstance(module, dict):
                continue
            name = module.get("module_name", "")
            count = module.get(count_key)
            total = module.get("total_connections")
            if count_key == "total_connections":
                lines.append(f"- {rank}. {name} ({total} total connections)")
            else:
                lines.append(f"- {rank}. {name} ({count} {count_key.replace('_', ' ')})")

    append_ranked("Most Connected Modules:", top_connected, "total_connections")
    append_ranked("Most Outgoing Dependencies:", top_outgoing, "outgoing_count")
    append_ranked("Most Incoming Dependencies:", top_incoming, "incoming_count")

    if isolated_nodes:
        lines.append("Isolated Modules:")
        lines.extend(f"- {module}" for module in isolated_nodes)

    return "\n".join(lines)

