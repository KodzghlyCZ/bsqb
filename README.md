# bsqb

[![CI](https://github.com/KodzghlyCZ/bsqb/actions/workflows/ci.yml/badge.svg)](https://github.com/KodzghlyCZ/bsqb/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/bsqb.svg)](https://pypi.org/project/bsqb/)
[![Python versions](https://img.shields.io/pypi/pyversions/bsqb.svg)](https://pypi.org/project/bsqb/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Sponsor](https://img.shields.io/badge/Sponsor-❤-ea4aaa?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/KodzghlyCZ)

**bsqb** (Brave Search Query Builder) is a type-safe, zero-dependency Python library for constructing [Brave Search](https://search.brave.com) query strings using the official search operators.

It helps you build valid `q` parameters for the [Brave Search API](https://api-dashboard.search.brave.com/app/documentation/web-search) with a fluent API, automatic quoting, and validation against API limits.

## Features

- **Complete operator coverage** — All operators from the [official Brave Search documentation](https://api-dashboard.search.brave.com/documentation/resources/search-operators)
- **Fluent API** — Chain methods for readable, composable queries
- **Type-safe** — Full type hints and `py.typed` marker for mypy/Pylance
- **Zero dependencies** — Lightweight core with no runtime requirements
- **API limit validation** — Enforces the 400 character / 50 word limits on `q`
- **Logical operators** — `AND`, `OR`, `NOT` with Python operators (`&`, `|`, `~`)

## Installation

```bash
pip install bsqb
```

## Quick start

```python
from bsqb import Query

# Basic query with field operators
query = Query("machine learning").filetype("pdf").lang("en")
print(query.build())
# machine learning filetype:pdf lang:en

# Use with the Brave Search API
import urllib.parse
import urllib.request

params = urllib.parse.urlencode({"q": query.build()})
url = f"https://api.search.brave.com/res/v1/web/search?{params}"
request = urllib.request.Request(
    url,
    headers={"X-Subscription-Token": "YOUR_API_KEY"},
)
```

## Supported operators

| Operator | Method | Example output |
| --- | --- | --- |
| Plain term | `Query("term")` | `term` |
| Exact phrase | `.phrase("exact phrase")` | `"exact phrase"` |
| Force include | `.include("term")` | `+term` |
| Exclude | `.exclude("term")` | `-term` |
| File extension | `.ext("pdf")` | `ext:pdf` |
| File type | `.filetype("pdf")` | `filetype:pdf` |
| In title | `.intitle("2023")` | `intitle:2023` |
| In body | `.inbody("keyword")` | `inbody:keyword` |
| In page | `.inpage("keyword")` | `inpage:keyword` |
| Language (ISO 639-1) | `.lang("es")` | `lang:es` |
| Language alias | `.language("es")` | `language:es` |
| Location (ISO 3166-1) | `.loc("gb")` | `loc:gb` |
| Location alias | `.location("gb")` | `location:gb` |
| Site / domain | `.site("example.com")` | `site:example.com` |
| Logical AND | `.and_(other)` or `&` | `term1 AND term2` |
| Logical OR | `.or_(other)` or `\|` | `term1 OR term2` |
| Logical NOT | `.not_(other)` or `~` | `NOT term` |

Operators can be placed anywhere in the query string, matching Brave Search behavior.

Most operator methods accept a single value or a list/tuple of values:

```python
Query("AI startup").exclude(["google", "microsoft", "amazon"])
Query("news").site(["reuters.com", "bloomberg.com"])
```

## Examples

### Official documentation examples

```python
from bsqb import Query

# Academic research
Query("climate change").filetype("pdf").site("edu").intitle("2024").build()
# climate change filetype:pdf site:edu intitle:2024

# Multilingual content
Query("recettes cuisine").loc("ca").lang("fr").build()
# recettes cuisine loc:ca lang:fr

# Competitive analysis
Query("AI startup").exclude(["google", "microsoft", "amazon", "meta"]).build()
# AI startup -google -microsoft -amazon -meta

# Technical documentation
(
    Query("python")
    .phrase("asyncio")
    .intitle("documentation")
    .site("docs.python.org")
    .build()
)
# python "asyncio" intitle:documentation site:docs.python.org
```

### Logical operators

```python
from bsqb import Query, combine_and, combine_or

# AND — visa info in English from UK sites
Query("visa").loc("gb").and_(Query().lang("en")).build()
# visa loc:gb AND lang:en

# OR — travel requirements for Australia or New Zealand
(
    Query("travel requirements")
    .inpage("australia")
    .or_(Query().inpage("new zealand"))
    .build()
)
# travel requirements inpage:australia OR inpage:"new zealand"

# NOT — exclude a domain
Query("brave search").not_(Query().site("brave.com")).build()
# brave search NOT site:brave.com

# Python operators
(Query("coffee") | Query("tea")).exclude("starbucks").build()
# coffee OR tea -starbucks

# Combine multiple queries
combine_and(Query("visa").loc("gb"), Query().lang("en")).build()
combine_or(Query().site("reuters.com"), Query().site("bloomberg.com")).build()
Query("news").site(["reuters.com", "bloomberg.com"]).build()
```

### Advanced usage

```python
from bsqb import Query, phrase, raw, term

# Build from AST nodes
Query.from_nodes(term("python"), phrase("asyncio"), raw("site:docs.python.org"))

# Wrap an existing query string
Query.parse("machine learning filetype:pdf lang:en").build()

# Skip validation for edge cases
Query.parse("...").build(validate=False)
```

## Validation

The Brave Search API enforces these limits on the `q` parameter:

- Maximum **400 characters**
- Maximum **50 words**
- Query cannot be empty

Call `.build()` to validate (default), or `.render()` / `str()` to get the string without validation:

```python
from bsqb import Query, QueryValidationError, EmptyQueryError

query = Query("hello world")

query.render()   # "hello world" — no validation
query.build()    # "hello world" — validates limits

try:
    Query().build()
except EmptyQueryError:
    ...

try:
    Query.parse(" ".join(["word"] * 51)).build()
except QueryValidationError as exc:
    print(exc.query)
```

## Integration with Brave Search API

Search operators are included in the `q` parameter. Set `operators=true` (the default) in API requests:

```python
import urllib.parse
import urllib.request

from bsqb import Query

query = Query("python").phrase("asyncio").filetype("pdf").lang("en")

params = {
    "q": query.build(),
    "count": "10",
    "operators": "true",
}
url = "https://api.search.brave.com/res/v1/web/search?" + urllib.parse.urlencode(params)

request = urllib.request.Request(
    url,
    headers={
        "Accept": "application/json",
        "X-Subscription-Token": "YOUR_API_KEY",
    },
)
```

For POST requests with long queries, pass the built string as the `q` field in the request body.

## Development

```bash
git clone https://github.com/kodzghly/bsqb.git
cd bsqb
python -m pip install -e ".[dev]"

# Run tests
pytest

# Lint and type check
ruff check src tests
mypy src
```

## Publishing to PyPI

This package uses [Hatchling](https://hatch.pypa.io/) as the build backend.

### First-time setup

1. Create accounts on [PyPI](https://pypi.org/account/register/) and [TestPyPI](https://test.pypi.org/account/register/)
2. Enable [2FA](https://pypi.org/help/#twofa) on both accounts
3. Create an API token at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

### Test on TestPyPI

```bash
python -m pip install --upgrade build twine

# Bump version in pyproject.toml and src/bsqb/__init__.py
python -m build

# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Verify installation
pip install --index-url https://test.pypi.org/simple/ bsqb
```

### Publish to PyPI

```bash
python -m build
twine check dist/*
twine upload dist/*
```

### Recommended: publish via GitHub Actions

Add trusted publishing on PyPI for your repository, then create a release workflow triggered by git tags:

```yaml
# .github/workflows/publish.yml
name: Publish

on:
  release:
    types: [published]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build
      - run: python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
```

Create a GitHub release with tag `v0.2.0` to trigger publication.

## References

- [Brave Search Operators (API docs)](https://api-dashboard.search.brave.com/documentation/resources/search-operators)
- [Brave Search Operators (help page)](https://search.brave.com/help/operators)
- [Brave Web Search API](https://api-dashboard.search.brave.com/app/documentation/web-search)

## Support

If **bsqb** is useful to you, consider [sponsoring on GitHub](https://github.com/sponsors/KodzghlyCZ) — it helps keep the project maintained.

## License

MIT — see [LICENSE](LICENSE).
