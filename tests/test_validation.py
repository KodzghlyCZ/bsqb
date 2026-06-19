"""Tests for query validation."""

from __future__ import annotations

import pytest

from bsqb import EmptyQueryError, QueryValidationError, count_words, validate_query
from bsqb.operators import MAX_QUERY_CHARACTERS, MAX_QUERY_WORDS


class TestCountWords:
    def test_simple(self) -> None:
        assert count_words("hello world") == 2

    def test_quoted_phrase(self) -> None:
        assert count_words('"order of the phoenix"') == 4

    def test_operators(self) -> None:
        assert count_words("visa loc:gb AND lang:en") == 4


class TestValidateQuery:
    def test_valid_query(self) -> None:
        query = "machine learning filetype:pdf"
        assert validate_query(query) == query

    def test_strips_whitespace(self) -> None:
        assert validate_query("  hello  ") == "hello"

    def test_empty_raises(self) -> None:
        with pytest.raises(EmptyQueryError):
            validate_query("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(EmptyQueryError):
            validate_query("   ")

    def test_character_limit(self) -> None:
        query = "x" * (MAX_QUERY_CHARACTERS + 1)
        with pytest.raises(QueryValidationError) as exc_info:
            validate_query(query)
        assert exc_info.value.query == query

    def test_word_limit(self) -> None:
        query = " ".join(["word"] * (MAX_QUERY_WORDS + 1))
        with pytest.raises(QueryValidationError) as exc_info:
            validate_query(query)
        assert exc_info.value.query == query

    def test_at_limits(self) -> None:
        chars = "x" * MAX_QUERY_CHARACTERS
        assert validate_query(chars) == chars
        words = " ".join(["w"] * MAX_QUERY_WORDS)
        assert validate_query(words) == words
