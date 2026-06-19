"""Brave Search query builder (bsqb)."""

from bsqb.builder import (
    Query,
    ValueOrValues,
    combine_and,
    combine_or,
    phrase,
    raw,
    term,
)
from bsqb.exceptions import BsqbError, EmptyQueryError, QueryValidationError
from bsqb.nodes import (
    BinaryLogical,
    Exclude,
    Field,
    Include,
    Node,
    Not,
    Phrase,
    Raw,
    Sequence,
    Term,
)
from bsqb.operators import (
    MAX_QUERY_CHARACTERS,
    MAX_QUERY_WORDS,
    FieldOperator,
    LogicalOperator,
)
from bsqb.validation import count_words, validate_query

__all__ = [
    "MAX_QUERY_CHARACTERS",
    "MAX_QUERY_WORDS",
    "BinaryLogical",
    "BsqbError",
    "EmptyQueryError",
    "Exclude",
    "Field",
    "FieldOperator",
    "Include",
    "LogicalOperator",
    "Node",
    "Not",
    "Phrase",
    "Query",
    "QueryValidationError",
    "Raw",
    "Sequence",
    "Term",
    "ValueOrValues",
    "combine_and",
    "combine_or",
    "count_words",
    "phrase",
    "raw",
    "term",
    "validate_query",
]

__version__ = "0.2.0"
