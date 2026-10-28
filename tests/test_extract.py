import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
from extract import dedupe, normalize_price, parse_catalogue, parse_detail

CATALOGUE = """
<article class="product_pod"><h3><a href="a-book_1/index.html">A</a></h3></article>
<article class="product_pod"><h3><a href="b-book_2/index.html">B</a></h3></article>
<li class="next"><a href="page-2.html">next</a></li>
"""

DETAIL = """
<article class="product_page">
  <h1>  A Book  </h1>
  <p class="price_color">£51.77</p>
  <p class="availability">  In stock
     (22 available) </p>
  <p class="star-rating Three"></p>
</article>
"""  # no description on purpose


def test_price_normalization():
    assert normalize_price("£51.77") == 51.77
    assert normalize_price("Â£10.00") == 10.0


def test_relative_to_absolute_urls():
    links, nxt = parse_catalogue(CATALOGUE, "https://books.toscrape.com/catalogue/page-1.html")
    assert links[0] == "https://books.toscrape.com/catalogue/a-book_1/index.html"
    assert nxt == "https://books.toscrape.com/catalogue/page-2.html"


def test_missing_description_is_none():
    rec = parse_detail(DETAIL, "https://books.toscrape.com/catalogue/x/index.html",
                       "https://books.toscrape.com/catalogue/page-1.html")
    assert rec["description"] is None
    assert rec["title"] == "A Book"
    assert rec["availability_text"] == "In stock (22 available)"
    assert rec["rating_text"] == "Three"


def test_duplicate_urls_removed():
    assert dedupe(["u1", "u2", "u1"]) == ["u1", "u2"]


def test_malformed_page_raises():
    with pytest.raises(ValueError):
        parse_detail("<html><body>oops</body></html>", "https://x/", "https://x/")

import pytest

from extract import normalize_price


@pytest.mark.parametrize(
    ("price_text", "expected"),
    [
        ("£51.77", 51.77),
        ("£0.99", 0.99),
        ("£1,234.56", 1234.56),
        ("  £12.50  ", 12.50),
    ],
)
def test_normalize_price(price_text, expected):
    assert normalize_price(price_text) == expected


@pytest.mark.parametrize("price_text", [None, "", "£", "unavailable"])
def test_normalize_invalid_price(price_text):
    with pytest.raises(ValueError, match="cannot parse price"):
        normalize_price(price_text)
