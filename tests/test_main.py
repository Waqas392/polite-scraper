import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import pytest
import main
from fetcher import FetchError


FAKE_URL = (
    "https://books.toscrape.com/catalogue/"
    "this-book-does-not-exist_999/index.html"
)


class FakeFetcher:
    def __init__(self):
        self.pages_fetched = 0
        self.cache_hits = 0

    def get(self, url):
        if url == FAKE_URL:
            raise FetchError(f"{url} -> HTTP 404")
        return "mock page"


@pytest.fixture
def run_fake_pipeline(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "OUTPUT", tmp_path)
    monkeypatch.setattr(main, "Fetcher", FakeFetcher)
    monkeypatch.setattr(sys, "argv", ["main.py", "--fake"])

    def fake_catalogue(html, url):
        page_number = int(url.rsplit("page-", 1)[1].split(".")[0])
        links = [
            f"https://books.toscrape.com/catalogue/book-{page_number}-{i}.html"
            for i in range(20)
        ]
        next_url = (
            f"https://books.toscrape.com/catalogue/page-{page_number + 1}.html"
            if page_number < 3
            else None
        )
        return links, next_url

    def fake_detail(html, url, source_page):
        return {
            "title": url.rsplit("/", 1)[-1],
            "product_url": url,
            "price_text": "£12.50",
            "price_gbp": 12.5,
            "availability_text": "In stock",
            "rating_text": "Three",
            "description": None,
            "source_page": source_page,
            "fetched_at": "2026-10-28T12:00:00Z",
        }

    monkeypatch.setattr(main, "parse_catalogue", fake_catalogue)
    monkeypatch.setattr(main, "parse_detail", fake_detail)
    monkeypatch.setattr(main, "normalize_price", lambda price: 12.5)

    main.main()

    return tmp_path


def test_fake_failure_preserves_valid_records(run_fake_pipeline):
    books = json.loads((run_fake_pipeline / "books.json").read_text(encoding="utf-8"))
    report = json.loads((run_fake_pipeline / "run-report.json").read_text(encoding="utf-8"))

    assert len(books) == 60
    assert report["valid_records"] == 60
    assert report["invalid_records"] == 0
    assert report["failed_pages"] == 1
    assert report["catalogue_pages"] == 3
    assert report["discovered"] == 60
    assert report["unique_urls"] == 61
    assert report["failures"][0]["url"] == FAKE_URL


def test_fake_failure_does_not_create_validation_errors(run_fake_pipeline):
    errors = json.loads((run_fake_pipeline / "errors.json").read_text(encoding="utf-8"))
    assert errors == []
