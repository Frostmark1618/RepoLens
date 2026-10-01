from __future__ import annotations

import re


_SECRET_NOUNS = (
    r"api[\s_-]*keys?",
    r"access[\s_-]*tokens?",
    r"auth[\s_-]*tokens?",
    r"private[\s_-]*keys?",
    r"passwords?",
    r"secrets?",
    r"credentials?",
    r"environment[\s_-]*(?:variables?|values?)",
)

_DISCLOSURE_VERBS = (
    r"show",
    r"reveal",
    r"print",
    r"give",
    r"tell",
    r"provide",
    r"output",
    r"dump",
    r"expose",
    r"return",
    r"list",
    r"extract",
)


def is_sensitive_value_request(query: str) -> bool:
    """Detect requests to disclose secret values, not questions about controls."""
    if not isinstance(query, str):
        return False
    normalized = re.sub(r"[^a-z0-9_-]+", " ", query.lower()).strip()
    if not normalized:
        return False

    noun_pattern = "(?:" + "|".join(_SECRET_NOUNS) + ")"
    verb_pattern = "(?:" + "|".join(_DISCLOSURE_VERBS) + ")"
    return bool(
        re.search(rf"\b{verb_pattern}\b.{{0,60}}\b{noun_pattern}\b", normalized)
        or re.search(rf"\b{noun_pattern}\b.{{0,60}}\b{verb_pattern}\b", normalized)
    )
