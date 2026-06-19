"""Abstract syntax tree nodes for Brave Search queries."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from bsqb.operators import FieldOperator, LogicalOperator


def _format_operand(value: str, *, quote: bool = False) -> str:
    """Format an operator operand, quoting when it contains whitespace."""
    if quote or any(char.isspace() for char in value):
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def _format_term(value: str) -> str:
    """Format a plain search term."""
    return value


class Node(ABC):
    """Base class for all query AST nodes."""

    @abstractmethod
    def render(self) -> str:
        """Render this node to a Brave Search query string."""

    def __bool__(self) -> bool:
        return bool(self.render())


@dataclass(frozen=True, slots=True)
class Term(Node):
    """A plain search term."""

    value: str

    def render(self) -> str:
        return _format_term(self.value)


@dataclass(frozen=True, slots=True)
class Phrase(Node):
    """An exact phrase match wrapped in double quotes."""

    value: str

    def render(self) -> str:
        value = self.value
        escaped = (
            ""
            if not value
            else value.replace("\\", "\\\\").replace('"', '\\"')
        )
        return f'"{escaped}"'


@dataclass(frozen=True, slots=True)
class Include(Node):
    """Force inclusion of a term (+term)."""

    value: str

    def render(self) -> str:
        return f"+{_format_term(self.value)}"


@dataclass(frozen=True, slots=True)
class Exclude(Node):
    """Exclude a term (-term)."""

    value: str

    def render(self) -> str:
        return f"-{_format_term(self.value)}"


@dataclass(frozen=True, slots=True)
class Field(Node):
    """A field operator such as site:, lang:, or filetype:."""

    operator: FieldOperator
    value: str

    def render(self) -> str:
        return f"{self.operator.value}:{_format_operand(self.value)}"


@dataclass(frozen=True, slots=True)
class Raw(Node):
    """A pre-formatted query fragment for advanced use cases."""

    value: str

    def render(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Sequence(Node):
    """A space-separated sequence of query parts."""

    parts: tuple[Node, ...]

    def render(self) -> str:
        rendered = [part.render() for part in self.parts if part.render()]
        return " ".join(rendered)


@dataclass(frozen=True, slots=True)
class BinaryLogical(Node):
    """A binary logical expression (AND / OR)."""

    operator: LogicalOperator
    left: Node
    right: Node

    def render(self) -> str:
        left = self.left.render()
        right = self.right.render()
        op = self.operator.value
        if isinstance(self.left, BinaryLogical) and self.left.operator != self.operator:
            left = f"({left})"
        if (
            isinstance(self.right, BinaryLogical)
            and self.right.operator != self.operator
        ):
            right = f"({right})"
        return f"{left} {op} {right}"


@dataclass(frozen=True, slots=True)
class Not(Node):
    """A NOT logical expression."""

    operand: Node

    def render(self) -> str:
        operand = self.operand.render()
        if isinstance(self.operand, BinaryLogical):
            operand = f"({operand})"
        return f"{LogicalOperator.NOT.value} {operand}"


def empty_node() -> Sequence:
    """Return an empty sequence node."""
    return Sequence(())
