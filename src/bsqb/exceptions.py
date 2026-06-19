"""Custom exceptions for bsqb."""

from __future__ import annotations


class BsqbError(Exception):
    """Base exception for all bsqb errors."""


class QueryValidationError(BsqbError):
    """Raised when a built query violates Brave Search API limits."""

    def __init__(self, message: str, *, query: str | None = None) -> None:
        super().__init__(message)
        self.query = query


class EmptyQueryError(QueryValidationError):
    """Raised when attempting to build an empty query."""

    def __init__(self) -> None:
        super().__init__(
            "Query cannot be empty. "
            "The Brave Search API requires a non-empty q parameter."
        )
