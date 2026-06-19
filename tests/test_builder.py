"""Tests for the Query builder."""

from __future__ import annotations

import pytest

from bsqb import (
    EmptyQueryError,
    Query,
    QueryValidationError,
    combine_and,
    combine_or,
    phrase,
    raw,
    term,
)
from bsqb.operators import MAX_QUERY_CHARACTERS, MAX_QUERY_WORDS


class TestBasicTerms:
    def test_single_term(self) -> None:
        assert str(Query("machine learning")) == "machine learning"

    def test_multiple_initial_terms(self) -> None:
        assert str(Query("machine", "learning")) == "machine learning"

    def test_empty_query(self) -> None:
        assert str(Query()) == ""
        with pytest.raises(EmptyQueryError):
            Query().build()

    def test_term_method(self) -> None:
        assert str(Query().term("python")) == "python"

    def test_phrase(self) -> None:
        q = Query("harry potter").phrase("order of the phoenix")
        assert q.render() == 'harry potter "order of the phoenix"'

    def test_phrase_helper(self) -> None:
        assert str(Query.from_nodes(phrase("exact phrase"))) == '"exact phrase"'

    def test_phrase_escapes_quotes(self) -> None:
        assert str(Query().phrase('say "hello"')) == r'"say \"hello\""'

    def test_term_with_spaces(self) -> None:
        assert str(Query("new zealand")) == "new zealand"


class TestInclusionExclusion:
    def test_include(self) -> None:
        assert str(Query("gpu").include("freesync")) == "gpu +freesync"

    def test_exclude(self) -> None:
        assert str(Query("office").exclude("microsoft")) == "office -microsoft"

    def test_multiple_exclusions(self) -> None:
        q = Query("AI startup").exclude("google").exclude("microsoft")
        assert q.render() == "AI startup -google -microsoft"


class TestFieldOperators:
    def test_ext(self) -> None:
        assert str(Query("manual").ext("pdf")) == "manual ext:pdf"

    def test_ext_strips_dot(self) -> None:
        assert str(Query().ext(".pdf")) == "ext:pdf"

    def test_filetype(self) -> None:
        q = Query("evaluation of age cognitive changes").filetype("pdf")
        assert q.render() == "evaluation of age cognitive changes filetype:pdf"

    def test_intitle(self) -> None:
        q = Query("seo conference").intitle("2023")
        assert str(q) == "seo conference intitle:2023"

    def test_inbody(self) -> None:
        q = Query("nvidia 1080 ti").inbody("founders edition")
        assert q.render() == 'nvidia 1080 ti inbody:"founders edition"'

    def test_inpage(self) -> None:
        q = Query("oscars 2024").inpage("best costume design")
        assert q.render() == 'oscars 2024 inpage:"best costume design"'

    def test_lang(self) -> None:
        assert str(Query("visas").lang("ES")) == "visas lang:es"

    def test_language_alias(self) -> None:
        assert str(Query("visas").language("es")) == "visas language:es"

    def test_loc(self) -> None:
        assert str(Query("niagara falls").loc("CA")) == "niagara falls loc:ca"

    def test_location_alias(self) -> None:
        assert str(Query("niagara falls").location("ca")) == "niagara falls location:ca"

    def test_site(self) -> None:
        assert str(Query("goggles").site("brave.com")) == "goggles site:brave.com"

    def test_site_normalizes_url(self) -> None:
        assert str(Query().site("https://www.github.com/")) == "site:github.com"


class TestLogicalOperators:
    def test_and(self) -> None:
        q = Query("visa").loc("gb").and_(Query().lang("en"))
        assert q.render() == "visa loc:gb AND lang:en"

    def test_or(self) -> None:
        q = Query("travel requirements").inpage("australia").or_(
            Query().inpage("new zealand")
        )
        assert q.render() == (
            'travel requirements inpage:australia OR inpage:"new zealand"'
        )

    def test_not(self) -> None:
        q = Query("brave search").not_(Query().site("brave.com"))
        assert q.render() == "brave search NOT site:brave.com"

    def test_invert_operator(self) -> None:
        q = ~Query().site("brave.com")
        assert q.render() == "NOT site:brave.com"

    def test_ampersand_operator(self) -> None:
        q = Query("visa").loc("gb") & Query().lang("en")
        assert q.render() == "visa loc:gb AND lang:en"

    def test_pipe_operator(self) -> None:
        q = Query("coffee") | Query("tea")
        assert q.render() == "coffee OR tea"

    def test_complex_or_chain(self) -> None:
        q = (
            Query("electric vehicles")
            .site("reuters.com")
            .or_(Query().site("bloomberg.com"))
            .term("2025")
        )
        expected = "electric vehicles site:reuters.com OR site:bloomberg.com 2025"
        assert q.render() == expected


class TestCombineHelpers:
    def test_combine_and(self) -> None:
        q = combine_and(Query("visa").loc("gb"), Query().lang("en"))
        assert q.render() == "visa loc:gb AND lang:en"

    def test_combine_or(self) -> None:
        q = combine_or(Query("coffee"), Query("tea"))
        assert q.render() == "coffee OR tea"


class TestDocumentationExamples:
    def test_academic_research(self) -> None:
        q = Query("climate change").filetype("pdf").site("edu").intitle("2024")
        assert q.render() == "climate change filetype:pdf site:edu intitle:2024"

    def test_multilingual_content(self) -> None:
        q = Query("recettes cuisine").loc("ca").lang("fr")
        assert q.render() == "recettes cuisine loc:ca lang:fr"

    def test_competitive_analysis(self) -> None:
        q = (
            Query("AI startup")
            .exclude("google")
            .exclude("microsoft")
            .exclude("amazon")
            .exclude("meta")
        )
        assert q.render() == "AI startup -google -microsoft -amazon -meta"

    def test_technical_documentation(self) -> None:
        q = (
            Query("python")
            .phrase("asyncio")
            .intitle("documentation")
            .site("docs.python.org")
        )
        expected = 'python "asyncio" intitle:documentation site:docs.python.org'
        assert q.render() == expected

    def test_api_example(self) -> None:
        q = Query("machine learning").filetype("pdf").lang("en")
        assert q.render() == "machine learning filetype:pdf lang:en"


class TestRawAndParse:
    def test_raw_fragment(self) -> None:
        assert str(Query().raw("filetype:pdf")) == "filetype:pdf"

    def test_raw_helper(self) -> None:
        assert str(Query.from_nodes(raw("custom:query"))) == "custom:query"

    def test_parse(self) -> None:
        q = Query.parse("machine learning filetype:pdf lang:en")
        assert q.render() == "machine learning filetype:pdf lang:en"

    def test_parse_empty(self) -> None:
        assert str(Query.parse("  ")) == ""


class TestValidation:
    def test_build_validates_by_default(self) -> None:
        q = Query("hello")
        assert q.build() == "hello"

    def test_build_skips_validation(self) -> None:
        long_query = " ".join(["word"] * (MAX_QUERY_WORDS + 1))
        q = Query.parse(long_query)
        assert q.build(validate=False) == long_query

    def test_character_limit(self) -> None:
        q = Query.parse("x" * (MAX_QUERY_CHARACTERS + 1))
        with pytest.raises(QueryValidationError, match="characters"):
            q.build()

    def test_word_limit(self) -> None:
        q = Query.parse(" ".join(["word"] * (MAX_QUERY_WORDS + 1)))
        with pytest.raises(QueryValidationError, match="words"):
            q.build()


class TestEquality:
    def test_equal_queries(self) -> None:
        assert Query("a").filetype("pdf") == Query("a").filetype("pdf")

    def test_hashable(self) -> None:
        queries = {Query("test"), Query("test"), Query("other")}
        assert len(queries) == 2


class TestNodeHelpers:
    def test_term_helper(self) -> None:
        assert str(Query.from_nodes(term("hello"))) == "hello"

    def test_repr(self) -> None:
        assert repr(Query("test")) == "Query('test')"

    def test_bool(self) -> None:
        assert Query("x")
        assert not Query()
