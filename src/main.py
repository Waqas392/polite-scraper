import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from extract import normalize_price, parse_catalogue, parse_detail
from fetcher import FetchError, Fetcher
from schema import Book

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
MAX_PAGES = 3
OUTPUT = Path("output")


def discover(fetcher):
    """Follow the site's own 'next' links for 3 catalogue pages."""
    pages, found, url = 0, [], START_URL
    while url and pages < MAX_PAGES:
        html = fetcher.get(url)
        links, next_url = parse_catalogue(html, url)
        found.extend((link, url) for link in links)
        pages += 1
        url = next_url
    return pages, found


def main():
    started = datetime.now(timezone.utc)
    t0 = time.time()
    OUTPUT.mkdir(exist_ok=True)
    fetcher = Fetcher()

    pages, found = discover(fetcher)

    seen, unique = set(), []
    for url, src in found:
        if url not in seen:
            seen.add(url)
            unique.append((url, src))

    if "--fake" in sys.argv:  # Stage 5 proof: one made-up URL
        unique.append(("https://books.toscrape.com/catalogue/this-book-does-not-exist_999/index.html", START_URL))

    print(f"catalogue_pages={pages}, discovered={len(found)}, unique_urls={len(unique)}")

    valid, errors, failed_pages = {}, [], []
    for url, src in unique:
        try:
            html = fetcher.get(url)
            raw = parse_detail(html, url, src)
            raw["price_gbp"] = normalize_price(raw["price_text"])
            book = Book(**raw)
            valid[str(book.product_url)] = book.model_dump(mode="json")
        except FetchError as e:
            failed_pages.append({"url": url, "reason": str(e)})
            print(f"FAILED {e}")
        except (ValidationError, ValueError, TypeError) as e:
            errors.append({"url": url, "reason": str(e)})
            print(f"INVALID {url}: {e}")
        except Exception as e:  # one bad page must not kill the run
            failed_pages.append({"url": url, "reason": f"unexpected: {e!r}"})

    print(f"detail_pages={len(valid) + len(errors)}")

    (OUTPUT / "books.json").write_text(json.dumps(list(valid.values()), indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "errors.json").write_text(json.dumps(errors, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "started_at": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duration_seconds": round(time.time() - t0, 2),
        "pages_fetched": fetcher.pages_fetched,
        "cache_hits": fetcher.cache_hits,
        "valid_records": len(valid),
        "invalid_records": len(errors),
        "failed_pages": len(failed_pages),
        "failures": failed_pages,
        "catalogue_pages": pages,
        "discovered": len(found),
        "unique_urls": len(unique),
    }
    (OUTPUT / "run-report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
