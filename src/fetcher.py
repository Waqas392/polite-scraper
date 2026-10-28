import hashlib
import time
from pathlib import Path

import requests

USER_AGENT = "FlyRankInternshipA9/1.0 (+https://github.com/Waqas392/polite-scraper)"
TIMEOUT = 8
DELAY = 0.6  # seconds between real requests (>= 0.5)
CACHE_DIR = Path("cache")


class FetchError(Exception):
    pass


class Fetcher:
    def __init__(self):
        CACHE_DIR.mkdir(exist_ok=True)
        self.session = requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.last_request = 0.0
        self.pages_fetched = 0
        self.cache_hits = 0

    def _cache_path(self, url):
        return CACHE_DIR / (hashlib.sha1(url.encode()).hexdigest()[:16] + ".html")

    def _wait(self):
        gap = time.time() - self.last_request
        if gap < DELAY:
            time.sleep(DELAY - gap)

    def get(self, url):
        path = self._cache_path(url)
        if path.exists():
            self.cache_hits += 1
            html = path.read_text(encoding="utf-8")
            print(f"CACHE HIT {url} ({len(html)} bytes)")
            return html

        last_error = None
        for attempt in (1, 2):  # one retry only
            self._wait()
            self.last_request = time.time()
            try:
                resp = self.session.get(url, timeout=TIMEOUT)
            except (requests.Timeout, requests.ConnectionError) as e:
                last_error = f"network error: {e}"
                time.sleep(1.5)
                continue

            if resp.status_code == 200:
                resp.encoding = "utf-8"
                html = resp.text
                path.write_text(html, encoding="utf-8")
                self.pages_fetched += 1
                print(f"FETCH {url} ({len(html)} bytes)")
                return html

            if resp.status_code >= 500:  # retry once on 5xx
                last_error = f"server error {resp.status_code}"
                time.sleep(1.5)
                continue

            raise FetchError(f"{url} -> HTTP {resp.status_code}")  # 403/404: no retry

        raise FetchError(f"{url} -> {last_error}")
