"""Fluent query builder for Brave Search operators."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from bsqb.exceptions import EmptyQueryError
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
    empty_node,
)
from bsqb.operators import FieldOperator, LogicalOperator
from bsqb.validation import validate_query

__all__ = [
    "Query",
    "ValueOrValues",
    "phrase",
    "raw",
    "term",
]

ValueOrValues = str | Iterable[str]


def term(value: str) -> Term:
    """Create a plain search term node."""
    return Term(value)


def phrase(value: str) -> Phrase:
    """Create an exact phrase match node."""
    return Phrase(value)


def raw(value: str) -> Raw:
    """Create a raw query fragment node."""
    return Raw(value)


class Query:
    """
    Fluent builder for Brave Search query strings.

    Supports all operators documented at:
    https://api-dashboard.search.brave.com/documentation/resources/search-operators

    Examples:
        >>> str(Query("machine learning").filetype("pdf").lang("en"))
        'machine learning filetype:pdf lang:en'

        >>> str(Query("visa").loc("gb").and_(Query().lang("en")))
        'visa loc:gb AND lang:en'
    """

    __slots__ = ("_node",)

    def __init__(
        self,
        *parts: str | Node,
        _node: Node | None = None,
    ) -> None:
        if _node is not None:
            self._node = _node
            return

        nodes: list[Node] = []
        for part in parts:
            if isinstance(part, Node):
                nodes.append(part)
            elif isinstance(part, str) and part:
                nodes.append(Term(part))

        if not nodes:
            self._node = empty_node()
        elif len(nodes) == 1:
            self._node = nodes[0]
        else:
            self._node = Sequence(tuple(nodes))

    @classmethod
    def from_nodes(cls, *nodes: Node) -> Query:
        """Create a query from explicit AST nodes."""
        if not nodes:
            return cls(_node=empty_node())
        if len(nodes) == 1:
            return cls(_node=nodes[0])
        return cls(_node=Sequence(tuple(nodes)))

    @classmethod
    def parse(cls, value: str) -> Query:
        """
        Wrap a pre-built query string without parsing.

        Use this when you already have a valid Brave Search query string.
        """
        stripped = value.strip()
        if not stripped:
            return cls()
        return cls(_node=Raw(stripped))

    def _append(self, node: Node) -> Query:
        current = self._node
        if isinstance(current, Sequence):
            return Query(_node=Sequence((*current.parts, node)))
        if isinstance(current, (BinaryLogical, Not)) or not current:
            return Query(_node=Sequence((current, node)) if current else node)
        return Query(_node=Sequence((current, node)))

    def _logical(self, operator: LogicalOperator, other: Query) -> Query:
        return Query(_node=BinaryLogical(operator, self._node, other._node))

    def _append_many(
        self,
        values: ValueOrValues,
        factory: Callable[[str], Node],
    ) -> Query:
        if isinstance(values, str):
            return self._append(factory(values))
        result = self
        for value in values:
            result = result._append(factory(value))
        return result

    def _normalize_site(self, domain: str) -> str:
        normalized = domain.removeprefix("https://").removeprefix("http://")
        return normalized.removeprefix("www.").rstrip("/")

    # --- Content terms -------------------------------------------------

    def term(self, value: ValueOrValues) -> Query:
        """Append one or more plain search terms."""
        return self._append_many(value, Term)

    def phrase(self, value: ValueOrValues) -> Query:
        """Append one or more exact phrase matches."""
        return self._append_many(value, Phrase)

    def include(self, value: ValueOrValues) -> Query:
        """Force inclusion of one or more terms (+term)."""
        return self._append_many(value, Include)

    def exclude(self, value: ValueOrValues) -> Query:
        """Exclude one or more terms (-term)."""
        return self._append_many(value, Exclude)

    def raw(self, value: ValueOrValues) -> Query:
        """Append one or more raw query fragments."""
        return self._append_many(value, Raw)

    # --- Field operators -----------------------------------------------

    def ext(self, extension: ValueOrValues) -> Query:
        """Filter by file extension (ext:)."""
        return self._append_many(
            extension,
            lambda value: Field(FieldOperator.EXT, value.lstrip(".")),
        )

    def filetype(self, filetype: ValueOrValues) -> Query:
        """Filter by file type (filetype:)."""
        return self._append_many(
            filetype,
            lambda value: Field(FieldOperator.FILETYPE, value.lstrip(".")),
        )

    def intitle(self, value: ValueOrValues) -> Query:
        """Search in page title (intitle:)."""
        return self._append_many(
            value,
            lambda v: Field(FieldOperator.INTITLE, v),
        )

    def inbody(self, value: ValueOrValues) -> Query:
        """Search in page body (inbody:)."""
        return self._append_many(
            value,
            lambda v: Field(FieldOperator.INBODY, v),
        )

    def inpage(self, value: ValueOrValues) -> Query:
        """Search in title or body (inpage:)."""
        return self._append_many(
            value,
            lambda v: Field(FieldOperator.INPAGE, v),
        )

    def lang(self, code: ValueOrValues) -> Query:
        """Filter by language ISO 639-1 code (lang:)."""
        return self._append_many(
            code,
            lambda value: Field(FieldOperator.LANG, value.lower()),
        )

    def language(self, code: ValueOrValues) -> Query:
        """Alias for lang() using the language: operator."""
        return self._append_many(
            code,
            lambda value: Field(FieldOperator.LANGUAGE, value.lower()),
        )

    def loc(self, code: ValueOrValues) -> Query:
        """Filter by country ISO 3166-1 alpha-2 code (loc:)."""
        return self._append_many(
            code,
            lambda value: Field(FieldOperator.LOC, value.lower()),
        )

    def location(self, code: ValueOrValues) -> Query:
        """Alias for loc() using the location: operator."""
        return self._append_many(
            code,
            lambda value: Field(FieldOperator.LOCATION, value.lower()),
        )

    def site(self, domain: ValueOrValues) -> Query:
        """Limit results to one or more domains (site:)."""
        return self._append_many(
            domain,
            lambda value: Field(FieldOperator.SITE, self._normalize_site(value)),
        )

    # --- Logical operators ---------------------------------------------

    def and_(self, other: Query) -> Query:
        """Combine with AND (both conditions required)."""
        return self._logical(LogicalOperator.AND, other)

    def or_(self, other: Query) -> Query:
        """Combine with OR (either condition sufficient)."""
        return self._logical(LogicalOperator.OR, other)

    def not_(self, other: Query | None = None) -> Query:
        """
        Negate a condition with NOT.

        When called with another query, appends ``NOT`` to the current query.
        When called without an argument, negates the current query.
        """
        if other is None:
            return Query(_node=Not(self._node))
        return Query(_node=Sequence((self._node, Not(other._node))))

    # --- Python operators for ergonomics --------------------------------

    def __and__(self, other: Query) -> Query:
        return self.and_(other)

    def __or__(self, other: Query) -> Query:
        return self.or_(other)

    def __invert__(self) -> Query:
        return self.not_()

    # --- Output --------------------------------------------------------

    def render(self) -> str:
        """Render the query string without validation."""
        return self._node.render()

    def build(self, *, validate: bool = True) -> str:
        """
        Build and optionally validate the query string.

        Args:
            validate: When True (default), enforce Brave Search API limits.

        Raises:
            EmptyQueryError: When the query is empty.
            QueryValidationError: When limits are exceeded.
        """
        rendered = self.render()
        if not rendered:
            raise EmptyQueryError()
        if validate:
            return validate_query(rendered)
        return rendered

    def __str__(self) -> str:
        return self.render()

    def __repr__(self) -> str:
        return f"Query({self.render()!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Query):
            return NotImplemented
        return self.render() == other.render()

    def __hash__(self) -> int:
        return hash(self.render())

    def __bool__(self) -> bool:
        return bool(self.render())


def combine_and(*queries: Query) -> Query:
    """Combine multiple queries with AND."""
    if not queries:
        return Query()
    result = queries[0]
    for query in queries[1:]:
        result = result.and_(query)
    return result


def combine_or(*queries: Query) -> Query:
    """Combine multiple queries with OR."""
    if not queries:
        return Query()
    result = queries[0]
    for query in queries[1:]:
        result = result.or_(query)
    return result
