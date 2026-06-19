"""Validation helpers for Brave Search query limits."""

from __future__ import annotations

import re

from bsqb.exceptions import EmptyQueryError, QueryValidationError
from bsqb.operators import MAX_QUERY_CHARACTERS, MAX_QUERY_WORDS

_WORD_PATTERN = re.compile(r"\S+")


def count_words(query: str) -> int:
    """Count words in a query string."""
    return len(_WORD_PATTERN.findall(query))


def validate_query(query: str) -> str:
    """
    Validate a query against Brave Search API limits.

    Returns the query unchanged when valid.

    Raises:
        EmptyQueryError: When the query is empty or whitespace-only.
        QueryValidationError: When the query exceeds character or word limits.
    """
    normalized = query.strip()
    if not normalized:
        raise EmptyQueryError()

    if len(normalized) > MAX_QUERY_CHARACTERS:
        raise QueryValidationError(
            f"Query exceeds the maximum of {MAX_QUERY_CHARACTERS} characters "
            f"({len(normalized)} given).",
            query=normalized,
        )

    word_count = count_words(normalized)
    if word_count > MAX_QUERY_WORDS:
        raise QueryValidationError(
            f"Query exceeds the maximum of {MAX_QUERY_WORDS} words "
            f"({word_count} given).",
            query=normalized,
        )

    return normalized
