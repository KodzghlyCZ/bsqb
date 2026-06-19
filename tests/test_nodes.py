"""Tests for AST node rendering."""

from __future__ import annotations

from bsqb.nodes import (
    BinaryLogical,
    Exclude,
    Field,
    Include,
    Not,
    Phrase,
    Raw,
    Sequence,
    Term,
)
from bsqb.operators import FieldOperator, LogicalOperator


class TestNodeRendering:
    def test_field_with_spaces(self) -> None:
        node = Field(FieldOperator.INBODY, "founders edition")
        assert node.render() == 'inbody:"founders edition"'

    def test_binary_logical_parentheses(self) -> None:
        left = BinaryLogical(
            LogicalOperator.OR,
            Term("a"),
            Term("b"),
        )
        right = Term("c")
        node = BinaryLogical(LogicalOperator.AND, left, right)
        assert node.render() == "(a OR b) AND c"

    def test_not_with_binary_operand(self) -> None:
        operand = BinaryLogical(LogicalOperator.OR, Term("a"), Term("b"))
        assert Not(operand).render() == "NOT (a OR b)"

    def test_sequence_skips_empty(self) -> None:
        assert Sequence((Term(""), Term("hello"))).render() == "hello"

    def test_include_exclude(self) -> None:
        assert Include("term").render() == "+term"
        assert Exclude("term").render() == "-term"

    def test_raw(self) -> None:
        assert Raw("custom fragment").render() == "custom fragment"

    def test_phrase(self) -> None:
        assert Phrase("exact").render() == '"exact"'
