import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from schema import Book


def valid_book(**overrides):
    data = {
        "title": "A Test Book",
        "product_url": "https://books.toscrape.com/catalogue/test/index.html",
        "price_text": "£10.00",
        "price_gbp": 10.0,
        "availability_text": "In stock",
        "rating_text": "Three",
        "description": None,
        "source_page": "https://books.toscrape.com/catalogue/page-1.html",
        "fetched_at": "2026-10-28T12:00:00Z",
    }
    data.update(overrides)
    return data


def test_valid_book_is_accepted():
    book = Book(**valid_book())

    assert book.title == "A Test Book"
    assert book.price_gbp == 10.0


@pytest.mark.parametrize("rating", ["Zero", "Six", "", "three"])
def test_invalid_rating_is_rejected(rating):
    with pytest.raises(ValidationError):
        Book(**valid_book(rating_text=rating))


@pytest.mark.parametrize("price", [0, -1, -0.01])
def test_non_positive_price_is_rejected(price):
    with pytest.raises(ValidationError):
        Book(**valid_book(price_gbp=price))


@pytest.mark.parametrize("field", ["product_url", "source_page"])
def test_http_url_is_rejected(field):
    with pytest.raises(ValidationError):
        Book(**valid_book(**{field: "http://example.com/book"}))
