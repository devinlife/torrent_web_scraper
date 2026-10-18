from pathlib import Path

import pytest

from app import crawler, doctor

FIX = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("url", ["http://127.0.0.1/", "http://localhost:8080/", "http://host.docker.internal/",
                                 "http://2130706433/", "http://0x7f.1/", "file:///etc/passwd", "http://[::1]/"])
def test_public_http_url_rejects(url):
    assert not doctor._public_http_url(url)


def test_public_http_url_accepts():
    assert doctor._public_http_url("https://torrentsome268.com/v-4-16")


def test_trim_html_keeps_posts():
    raw = (FIX / "torrentrj" / "board.html").read_text()
    seen = doctor._trim_html(raw)[:15000]  # browse sends the model at most 15000 chars
    assert "<script" not in seen and len(seen) <= 15000 < len(raw)
    assert len(crawler.parse_board(seen, "https://torrentrj274.com/v-4-16")) >= 20


def test_browse_retries_resets_spaced(monkeypatch):
    import asyncio

    from app.browser import FetchResult
    results = [FetchResult(0, "u", "", "net::ERR_CONNECTION_CLOSED")] * 2 + [
        FetchResult(200, "https://a.com/b", "<title>B</title><body>x</body>", None)]

    class FakeBrowser:
        async def fetch(self, url, **kw):
            return results.pop(0)

    sleeps = []

    async def fake_sleep(s):
        sleeps.append(s)
    monkeypatch.setattr(doctor.asyncio, "sleep", fake_sleep)
    browse = doctor.build_tools(None, FakeBrowser(), {"boards": []})[1]
    text = asyncio.run(browse.handler({"url": "https://a.com/b"}))["content"][0]["text"]
    assert "attempts: 1 ERR_CONNECTION_CLOSED, 2 ERR_CONNECTION_CLOSED, 3 status 200" in text
    assert "transient: yes" in text and "status: 200" in text and sleeps == [5, 10]
