"""Brave Search operator definitions based on official documentation."""

from __future__ import annotations

from enum import Enum


class FieldOperator(str, Enum):
    """Field operators supported by Brave Search."""

    EXT = "ext"
    FILETYPE = "filetype"
    INTITLE = "intitle"
    INBODY = "inbody"
    INPAGE = "inpage"
    LANG = "lang"
    LANGUAGE = "language"
    LOC = "loc"
    LOCATION = "location"
    SITE = "site"


class LogicalOperator(str, Enum):
    """Logical operators supported by Brave Search (must be uppercase)."""

    AND = "AND"
    OR = "OR"
    NOT = "NOT"


# Brave Search API query limits.
MAX_QUERY_CHARACTERS = 400
MAX_QUERY_WORDS = 50
