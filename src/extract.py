import re
from datetime import datetime, timezone
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_catalogue(html, page_url):
    """Return (absolute book urls, absolute next-page url or None)."""
    soup = BeautifulSoup(html, "html.parser")
    links = [urljoin(page_url, a["href"]) for a in soup.select("article.product_pod h3 a")]
    nxt = soup.select_one("li.next a")
    return links, (urljoin(page_url, nxt["href"]) if nxt else None)


def parse_detail(html, product_url, source_page):
    soup = BeautifulSoup(html, "html.parser")
    product = soup.select_one("article.product_page")
    if product is None:
        raise ValueError("product area not found")

    title = product.select_one("h1")
    price = product.select_one("p.price_color")
    avail = product.select_one("p.availability")
    rating = product.select_one("p.star-rating")

    description = None
    header = soup.select_one("#product_description")

    if header is not None:
        paragraph = header.find_next_sibling("p")
        if paragraph is not None:
            description = paragraph.get_text(" ", strip=True) or None

    rating_text = None
    if rating is not None:
        classes = [c for c in rating.get("class", []) if c != "star-rating"]
        rating_text = classes[0] if classes else None

    return {
        "title": title.get_text(strip=True) if title else None,
        "product_url": product_url,
        "price_text": price.get_text(strip=True) if price else None,
        "availability_text": " ".join(avail.get_text().split()) if avail else None,
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def normalize_price(price_text):
    cleaned = re.sub(r"[^\d.]", "", price_text or "")
    if not cleaned:
        raise ValueError(f"cannot parse price from {price_text!r}")
    return float(cleaned)


def dedupe(urls):
    return list(dict.fromkeys(urls))
