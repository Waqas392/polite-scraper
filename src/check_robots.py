import requests

from fetcher import USER_AGENT

r = requests.get("https://books.toscrape.com/robots.txt", headers={"User-Agent": USER_AGENT}, timeout=10)
print(r.status_code, len(r.text))
print(r.text[:500])
