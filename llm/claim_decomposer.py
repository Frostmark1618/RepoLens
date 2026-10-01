import re


# ---------------------------------------------------------
# PRESENTATION TEXT
# ---------------------------------------------------------

_PRESENTATION_PHRASES = (
    "here's how they interact",
    "here’s how they interact",
    "here is how they interact",
    "here's how it works",
    "here’s how it works",
    "here is how it works",
    "in summary",
    "to summarize",
    "overall",
    "in conclusion",
    "conclusion",
)


_LEADING_EXPLANATION_PREFIXES = (
    "in the provided code evidence",
    "based on the provided code evidence",
    "according to the provided code evidence",
    "from the provided code evidence",
    "the provided code evidence shows",
    "the provided repository evidence shows",
)


_SECTION_LABELS = {
    "session initialization",
    "request preparation",
    "adapter selection",
    "adapter usage",
    "request execution",
    "connection management",
    "closing connections",
    "cleanup",
    "execution",
    "execution flow",
    "request flow",
    "processing flow",
    "adapter retrieval",
    "adapter management",
    "adapter lifecycle",
    "summary",
    "conclusion",
    "how they interact",
    "how they work together",
}


# ---------------------------------------------------------
# NORMALIZATION
# ---------------------------------------------------------

def _normalize_text(value: str) -> str:
    value = value.replace(
        "\r\n",
        "\n",
    ).replace(
        "\r",
        "\n",
    )

    return value.strip()


def _remove_markdown_wrappers(
    value: str,
) -> str:
    value = value.strip()

    value = re.sub(
        r"^\s*#{1,6}\s+",
        "",
        value,
    )

    value = re.sub(
        r"^\s*[*_`]+",
        "",
        value,
    )

    value = re.sub(
        r"[*_`]+\s*$",
        "",
        value,
    )

    return value.strip()


def _remove_list_marker(
    value: str,
) -> str:
    value = re.sub(
        r"^\s*(?:[-*+])\s+",
        "",
        value,
    )

    value = re.sub(
        r"^\s*\d+[.)]\s+",
        "",
        value,
    )

    return value.strip()


# ---------------------------------------------------------
# PRESENTATION DETECTION
# ---------------------------------------------------------

def _is_presentation_text(
    value: str,
) -> bool:
    cleaned = _remove_markdown_wrappers(
        value
    )

    cleaned = _remove_list_marker(
        cleaned
    )

    cleaned = cleaned.strip()

    if not cleaned:
        return True

    label = cleaned.rstrip(":").strip()

    lower = label.lower()

    if any(lower.startswith(prefix) for prefix in _LEADING_EXPLANATION_PREFIXES):
        return True

    if lower in _PRESENTATION_PHRASES:
        return True

    if lower in _SECTION_LABELS:
        return True

    # Short colon-terminated headings.
    if (
        cleaned.endswith(":")
        and len(cleaned.split()) <= 8
    ):
        return True

    return False


# ---------------------------------------------------------
# REMOVE PRESENTATION PREFIX
# ---------------------------------------------------------

def _remove_presentation_prefix(
    value: str,
) -> str:
    """
    Remove presentation text only when it appears at
    the beginning of a block.

    Examples:

        Here's how they interact: When ...
        In summary: Sessions manage ...

    become:

        When ...
        Sessions manage ...
    """

    cleaned = value.strip()

    # Explicit phrases first.
    patterns = (
        r"(?i)^here(?:'|’)?s\s+how\s+they\s+interact\s*:\s*",
        r"(?i)^here\s+is\s+how\s+they\s+interact\s*:\s*",
        r"(?i)^here(?:'|’)?s\s+how\s+it\s+works\s*:\s*",
        r"(?i)^here\s+is\s+how\s+it\s+works\s*:\s*",
        r"(?i)^in\s+summary\s*:\s*",
        r"(?i)^to\s+summarize\s*:\s*",
        r"(?i)^overall\s*:\s*",
        r"(?i)^in\s+conclusion\s*:\s*",
        r"(?i)^conclusion\s*:\s*",
    )

    for pattern in patterns:
        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            count=1,
        )

    # Remove section heading when it is followed by
    # an actual sentence on the same block.
    for label in sorted(
        _SECTION_LABELS,
        key=len,
        reverse=True,
    ):
        pattern = (
            rf"(?i)^\s*"
            rf"(?:[*_`]+)?"
            rf"{re.escape(label)}"
            rf"(?:[*_`]+)?"
            rf"\s*:\s*"
        )

        cleaned = re.sub(
            pattern,
            "",
            cleaned,
            count=1,
        )

    return cleaned.strip()


# ---------------------------------------------------------
# STRUCTURE EXTRACTION
# ---------------------------------------------------------

def _prepare_blocks(
    answer: str,
) -> list[str]:
    """
    Convert Markdown answer into logical blocks.

    Handles both normal Markdown and flattened provider output.
    """

    text = _normalize_text(
        answer
    )

    # Restore numbered-list boundaries.
    text = re.sub(
        r"(?<!^)\s+(?=\d+[.)]\s+)",
        "\n",
        text,
    )

    # Restore section-heading boundaries.
    for label in sorted(
        _SECTION_LABELS,
        key=len,
        reverse=True,
    ):
        text = re.sub(
            rf"(?i)\s+(?="
            rf"(?:[*_`#]+)?"
            rf"{re.escape(label)}"
            rf"(?:[*_`#]+)?"
            rf"\s*:)",
            "\n",
            text,
        )

    # Restore summary boundaries.
    for phrase in (
        "in summary",
        "to summarize",
        "overall",
        "in conclusion",
        "conclusion",
    ):
        text = re.sub(
            rf"(?i)\s+(?="
            rf"{re.escape(phrase)}\s*:)",
            "\n",
            text,
        )

    # Restore flow-introduction boundaries.
    text = re.sub(
        r"(?i)\s+(?="
        r"here(?:'|’)?s\s+how\s+they\s+interact\s*:)",
        "\n",
        text,
    )

    text = re.sub(
        r"(?i)\s+(?="
        r"here\s+is\s+how\s+they\s+interact\s*:)",
        "\n",
        text,
    )

    blocks = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        line = _remove_markdown_wrappers(
            line
        )

        # Pure presentation line.
        if _is_presentation_text(
            line
        ):
            continue

        line = _remove_list_marker(
            line
        )

        if not line:
            continue

        # Remove presentation prefix ONLY if actual
        # content follows it.
        line = _remove_presentation_prefix(
            line
        )

        if not line:
            continue

        blocks.append(
            line
        )

    return blocks


# ---------------------------------------------------------
# SENTENCE SPLITTER
# ---------------------------------------------------------

def _split_sentences(
    text: str,
) -> list[str]:
    """
    Split sentences while preserving dotted Python names.
    """

    return [
        part.strip()
        for part in re.split(
            r"(?<=[.!?])(?:\s+|$)",
            text,
        )
        if part.strip()
    ]


# ---------------------------------------------------------
# CLAIM CLEANUP
# ---------------------------------------------------------

def _clean_claim(
    value: str,
) -> str:
    cleaned = value.strip()

    cleaned = _remove_markdown_wrappers(
        cleaned
    )

    cleaned = _remove_list_marker(
        cleaned
    )

    cleaned = cleaned.strip()

    if not cleaned:
        return ""

    # Remove inline section labels emitted by Markdown answers, e.g.
    # "Adapter Retrieval**: ..." or "Session Initialization: ...".
    for label in sorted(_SECTION_LABELS, key=len, reverse=True):
        pattern = (
            rf"(?i)^\s*"
            rf"(?:[*_`]+)?"
            rf"{re.escape(label)}"
            rf"(?:[*_`]+)?"
            rf"\s*:\s*"
        )
        cleaned = re.sub(pattern, "", cleaned, count=1)

    if not cleaned:
        return ""

    # Reject obvious presentation-only fragments and explanatory
    # lead-ins that are not repository claims.
    if _is_presentation_text(
        cleaned
    ):
        return ""

    cleaned = cleaned.rstrip(
        ".!?"
    ).strip()

    if not cleaned:
        return ""

    return cleaned + "."


def _is_valid_claim(
    value: str,
) -> bool:
    cleaned = value.strip()

    if not cleaned:
        return False

    # Number-only fragments.
    if re.fullmatch(
        r"\d+[.)]?",
        cleaned,
    ):
        return False

    # Extremely short presentation fragments.
    if cleaned.lower() in {
        "here",
        "here's",
        "here’s",
        "in",
        "overall",
        "summary",
        "conclusion",
    }:
        return False

    if _is_presentation_text(
        cleaned
    ):
        return False

    return True


# ---------------------------------------------------------
# DEPENDENCY COUNT SPECIAL CASE
# ---------------------------------------------------------

def _expand_dependency_claim(
    claim: str,
) -> list[str] | None:
    body = claim.rstrip(
        ".!?"
    ).strip()

    pattern = (
        r"^(.*?)\s+has\s+"
        r"(.+?)\s+outgoing\s+dependencies"
        r"\s+and\s+"
        r"(.+?)\s+incoming\s+"
        r"dependenc(?:y|ies)$"
    )

    match = re.match(
        pattern,
        body,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    prefix = match.group(1).strip()
    outgoing = match.group(2).strip()
    incoming = match.group(3).strip()

    if not prefix:
        return None

    return [
        f"{prefix} has "
        f"{outgoing} outgoing dependencies.",
        f"{prefix} has "
        f"{incoming} incoming dependency.",
    ]


# ---------------------------------------------------------
# CONTINUATION DETECTION
# ---------------------------------------------------------

def _is_continuation_sentence(value: str) -> bool:
    """
    Detect sentences that continue the previous repository claim.

    Local LLMs often format one logical step as multiple sentences,
    where the second sentence starts with a pronoun or continuation
    phrase such as ``It also ...`` or ``This allows ...``. Treating
    those as independent claims makes evidence attribution weaker
    because the second sentence may not repeat the symbol/module name.
    """
    cleaned = value.strip().lower()

    prefixes = (
        "it ",
        "it also ",
        "it then ",
        "this allows ",
        "the adapter then ",
        "the session then ",
        "which ",
        "and then ",
        "also ",
    )

    return cleaned.startswith(prefixes)


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def decompose_answer_into_claims(
    answer: str,
) -> list[str]:
    """
    Convert an LLM repository answer into independently
    stated claims.

    Presentation text is removed before sentence splitting.
    """

    if not isinstance(answer, str):
        raise TypeError(
            "Answer must be a string."
        )

    answer = answer.strip()

    if not answer:
        raise ValueError(
            "Answer cannot be empty."
        )

    # -----------------------------------------------------
    # STATUS PREFIX
    # -----------------------------------------------------

    normalized = answer

    for prefix in (
        "FACT:",
        "INFERENCE:",
        "POSSIBLE_RISK:",
        "UNKNOWN:",
    ):
        if normalized.upper().startswith(
            prefix
        ):
            normalized = normalized[
                len(prefix):
            ].strip()
            break

    # -----------------------------------------------------
    # BLOCKS
    # -----------------------------------------------------

    blocks = _prepare_blocks(
        normalized
    )

    claims = []

    # -----------------------------------------------------
    # SENTENCES
    # -----------------------------------------------------

    for block in blocks:

        sentences = _split_sentences(
            block
        )

        for sentence in sentences:

            claim = _clean_claim(
                sentence
            )

            if not claim:
                continue

            if not _is_valid_claim(
                claim
            ):
                continue

            # Preserve logical claim units.  Continuation sentences
            # usually depend on the symbol/context introduced by the
            # previous sentence, so keeping them together gives the
            # evidence verifier enough context to attribute the claim.
            if claims and _is_continuation_sentence(claim):
                previous = claims.pop()
                previous_body = previous.rstrip(".")
                continuation_body = claim.rstrip(".")
                claims.append(
                    f"{previous_body}. {continuation_body}."
                )
            else:
                claims.append(
                    claim
                )

    # -----------------------------------------------------
    # DEDUPLICATE
    # -----------------------------------------------------

    unique_claims = []
    seen = set()

    for claim in claims:
        key = claim.lower()

        if key in seen:
            continue

        seen.add(key)
        unique_claims.append(
            claim
        )

    # -----------------------------------------------------
    # DEPENDENCY SPECIAL CASE
    # -----------------------------------------------------

    final_claims = []

    for claim in unique_claims:

        expanded = _expand_dependency_claim(
            claim
        )

        if expanded:
            final_claims.extend(
                expanded
            )
        else:
            final_claims.append(
                claim
            )

    return final_claims