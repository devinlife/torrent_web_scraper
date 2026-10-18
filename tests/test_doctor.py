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


def test_user_prompt_dates_crawl_lines(tmp_path):
    from app import db
    conn = db.connect(tmp_path / "app.db")
    site = db.list_sites(conn)[0]
    rid = db.create_run(conn)
    db.finish_run(conn, rid, "done", 0, 0, f"21:53:50 site {site['name']}: /b -> 20 posts\n21:53:51 site other: x")
    p = doctor._user_prompt(conn, site)
    started = db.get_run(conn, rid)["started"]
    assert f"run started {started}:\n21:53:50 site {site['name']}: /b -> 20 posts" in p
    assert "site other" not in p and "now: " in p


def test_dns_tls_notes_real_sni_failure(monkeypatch):
    import contextlib
    import socket
    import ssl

    class Ctx:
        check_hostname, verify_mode = True, None

        def wrap_socket(self, s, server_hostname):
            if server_hostname == "a.com":
                raise ConnectionResetError(54, "reset")
            return contextlib.nullcontext(type("T", (), {"version": lambda self: "TLSv1.3"})())
    monkeypatch.setattr(socket, "getaddrinfo", lambda *a, **k: [(socket.AF_INET, 0, 0, "", ("1.2.3.4", 443))])
    class Sock(contextlib.nullcontext):
        def close(self):
            pass
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: Sock())
    monkeypatch.setattr(ssl, "create_default_context", Ctx)
    out = doctor._dns_tls("a.com")
    assert out[-3].startswith("tls sni=a.com: FAIL") and out[-2] == "tls sni=www.google.com: ok TLSv1.3"
    assert out[-1].startswith("note: this stdlib TLS probe cannot use ECH")


def test_transient_verdict_has_label():
    from app.views import LABEL
    assert set(doctor.SCHEMA["properties"]["verdict"]["enum"]) <= set(LABEL)
    assert LABEL["transient"] == "일시 장애"
