# The Polite Scraper - FlyRank Week 5, Assignment A9

A small Python scraping pipeline that fetches book data, extracts fields, normalizes prices, validates records, caches HTML, and writes JSON output and run reports.

## Target classification

- **Website:** https://books.toscrape.com/
- **Purpose:** Books to Scrape is a demonstration website designed for practising web scraping.
- **Scope:** The first three catalogue pages and their 60 book detail pages.
- **Data collected:** Book title, product URL, displayed price, normalized price in GBP, availability, rating, description, source catalogue page, and fetch timestamp.
- **robots.txt check:** The request to `https://books.toscrape.com/robots.txt` returned HTTP 404. This means no robots.txt file was available at that URL during the check; it does not establish permission for unrestricted scraping. The project is limited to the site's intended practice environment.

I would check the site's rules and terms before adapting this scraper to any other website.

## Requirements and installation

Python 3.10 or newer is required.

Dependencies are listed in `requirements.txt`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Running the project

Run the scraper:

```powershell
python src/main.py
```

Run the simulated broken-URL test:

```powershell
python src/main.py --fake
```

Run the tests:

```powershell
python -m pytest -q
```

The pipeline writes its results to:

- `output/books.json` - validated book records.
- `output/errors.json` - recorded extraction or fetching errors.
- `output/run-report.json` - execution statistics and failures.

The `--fake` option adds a deliberately invalid URL to check whether a failed page is recorded without losing the valid book records.

## Record schema

Each book record contains:

| Field | Description |
|---|---|
| `title` | Book title |
| `product_url` | Absolute URL of the product page |
| `price_text` | Original displayed price |
| `price_gbp` | Normalized numeric price in GBP |
| `availability_text` | Displayed availability |
| `rating_text` | Displayed star rating |
| `description` | Product description, or `null` when unavailable |
| `source_page` | Catalogue page from which the product was discovered |
| `fetched_at` | Timestamp associated with fetching the record |

Pydantic validates the extracted records before they are written to the output file.

## Politeness and error handling

- Uses an identifiable User-Agent.
- Applies request timeouts.
- Checks HTTP responses before parsing pages.
- Waits at least 0.6 seconds between real requests.
- Caches downloaded HTML to avoid unnecessary repeat requests.
- Retries once for eligible timeouts and server errors (5xx).
- Does not retry client errors such as HTTP 403 or 404.
- Records failed pages instead of discarding the successful records.

## Sample run report

A successful cached run produced the following report on 28 October 2026:

```json
{
  "started_at": "2026-10-28T19:15:04Z",
  "duration_seconds": 1.9,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failures": [],
  "catalogue_pages": 3,
  "discovered": 60,
  "unique_urls": 60
}
```

This run used cached HTML, so it made no new page requests. The 63 cache hits correspond to three catalogue pages and 60 product pages. A fresh run with an empty cache may have different timing and request counts.

## Why no browser automation?

The required book information is present in the HTML returned by the website. Requests and Beautiful Soup are sufficient for this task, so browser automation would add complexity without providing a necessary benefit.

## Ethics

This project is restricted to a website intended for scraping practice and collects only the fields required by the assignment. Before scraping another site, I would check its terms, robots.txt guidance, and any applicable access restrictions, and prefer an official API where available. I would not bypass authentication, paywalls, rate limits, or access controls.

## Limitations

The scraper covers only the first three catalogue pages and is not intended to represent the complete catalogue. Website layout changes may break the CSS selectors, and some source descriptions may contain malformed or duplicated text. The scraper preserves extracted source text rather than silently rewriting it.

The run report describes one execution and can vary depending on cache contents, network conditions, and server responses.

