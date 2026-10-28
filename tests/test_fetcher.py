import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import fetcher
from fetcher import FetchError, Fetcher


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(fetcher, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(fetcher.time, "sleep", lambda _: None)
    instance = Fetcher()
    monkeypatch.setattr(instance, "_wait", lambda: None)
    return instance


def response(status_code, text="page content"):
    return SimpleNamespace(status_code=status_code, text=text, encoding=None)


def test_successful_response_is_cached(client, monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append((url, timeout))
        return response(200, "<html>book</html>")

    monkeypatch.setattr(client.session, "get", fake_get)

    url = "https://example.com/book"
    assert client.get(url) == "<html>book</html>"
    assert client.get(url) == "<html>book</html>"
    assert len(calls) == 1
    assert calls[0][1] == fetcher.TIMEOUT
    assert client.pages_fetched == 1
    assert client.cache_hits == 1


def test_fetcher_sets_user_agent(client):
    assert client.session.headers["User-Agent"] == fetcher.USER_AGENT


def test_http_404_is_not_retried(client, monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return response(404, "Not found")

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(FetchError, match="HTTP 404"):
        client.get("https://example.com/missing")

    assert len(calls) == 1


def test_server_error_is_retried_once(client, monkeypatch):
    results = iter([response(503), response(200, "recovered")])
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return next(results)

    monkeypatch.setattr(client.session, "get", fake_get)

    assert client.get("https://example.com/retry") == "recovered"
    assert len(calls) == 2
    assert client.pages_fetched == 1


def test_timeout_is_retried_once(client, monkeypatch):
    results = iter([
        requests.Timeout("temporary timeout"),
        response(200, "recovered"),
    ])
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        result = next(results)
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(client.session, "get", fake_get)

    assert client.get("https://example.com/timeout") == "recovered"
    assert len(calls) == 2


def test_repeated_server_errors_raise_fetch_error(client, monkeypatch):
    calls = []

    def fake_get(url, timeout):
        calls.append(url)
        return response(503, "Unavailable")

    monkeypatch.setattr(client.session, "get", fake_get)

    with pytest.raises(FetchError, match="server error 503"):
        client.get("https://example.com/unavailable")

    assert len(calls) == 2
    assert client.pages_fetched == 0
