"""Fluent query builder for Brave Search operators."""

from __future__ import annotations

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
    "phrase",
    "raw",
    "term",
]


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

    # --- Content terms -------------------------------------------------

    def term(self, value: str) -> Query:
        """Append a plain search term."""
        return self._append(Term(value))

    def phrase(self, value: str) -> Query:
        """Append an exact phrase match."""
        return self._append(Phrase(value))

    def include(self, value: str) -> Query:
        """Force inclusion of a term (+term)."""
        return self._append(Include(value))

    def exclude(self, value: str) -> Query:
        """Exclude a term (-term)."""
        return self._append(Exclude(value))

    def raw(self, value: str) -> Query:
        """Append a raw query fragment."""
        return self._append(Raw(value))

    # --- Field operators -----------------------------------------------

    def ext(self, extension: str) -> Query:
        """Filter by file extension (ext:)."""
        return self._append(Field(FieldOperator.EXT, extension.lstrip(".")))

    def filetype(self, filetype: str) -> Query:
        """Filter by file type (filetype:)."""
        return self._append(Field(FieldOperator.FILETYPE, filetype.lstrip(".")))

    def intitle(self, value: str) -> Query:
        """Search in page title (intitle:)."""
        return self._append(Field(FieldOperator.INTITLE, value))

    def inbody(self, value: str) -> Query:
        """Search in page body (inbody:)."""
        return self._append(Field(FieldOperator.INBODY, value))

    def inpage(self, value: str) -> Query:
        """Search in title or body (inpage:)."""
        return self._append(Field(FieldOperator.INPAGE, value))

    def lang(self, code: str) -> Query:
        """Filter by language ISO 639-1 code (lang:)."""
        return self._append(Field(FieldOperator.LANG, code.lower()))

    def language(self, code: str) -> Query:
        """Alias for lang() using the language: operator."""
        return self._append(Field(FieldOperator.LANGUAGE, code.lower()))

    def loc(self, code: str) -> Query:
        """Filter by country ISO 3166-1 alpha-2 code (loc:)."""
        return self._append(Field(FieldOperator.LOC, code.lower()))

    def location(self, code: str) -> Query:
        """Alias for loc() using the location: operator."""
        return self._append(Field(FieldOperator.LOCATION, code.lower()))

    def site(self, domain: str) -> Query:
        """Limit results to a domain (site:)."""
        normalized = domain.removeprefix("https://").removeprefix("http://")
        normalized = normalized.removeprefix("www.").rstrip("/")
        return self._append(Field(FieldOperator.SITE, normalized))

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
