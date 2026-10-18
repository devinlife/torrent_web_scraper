import asyncio
from pathlib import Path

from app import config, db
from app.browser import FetchResult
from app.scheduler import run_once

FIX = Path(__file__).parent / "fixtures"
HASH = "4e4d86cbee91db107def6d3fd24271afd28130e2"
PAGES = {
    "https://torrentsome268.com/v-4-16": "torrentsome/board.html",
    "https://torrentsome268.com/v/311439": "torrentsome/detail.html",
    "https://torrentzota206.com/t/4/16.html": "torrentzota/board.html",
    "https://torrentzota206.com/torrent/r6o77rg.html": "torrentzota/detail.html",
}
DETAILS = {"https://torrentsome268.com/v/311439", "https://torrentzota206.com/torrent/r6o77rg.html"}


DOWN = FetchResult(0, "", "", "net::ERR_CONNECTION_CLOSED")


class FakeBrowser:
    def __init__(self, script: dict[str, list] | None = None):
        self.urls: list[str] = []
        self.script = script or {}  # url -> results returned in order, the last one repeating

    async def fetch(self, url, **kw):
        self.urls.append(url)
        if seq := self.script.get(url):
            r = seq.pop(0) if len(seq) > 1 else seq[0]
            return FetchResult(200, url, (FIX / r).read_text(encoding="utf-8"), None) if isinstance(r, str) else r
        if url in PAGES:
            return FetchResult(200, url, (FIX / PAGES[url]).read_text(encoding="utf-8"), None)
        return FetchResult(0, url, "", "net::ERR_NAME_NOT_RESOLVED")


def test_run_once_adds_once(tmp_path):
    conn = db.connect(tmp_path / "app.db")
    db.update_site(conn, 1, boards=["/v-4-16"])
    db.update_site(conn, 2, boards=["/t/4/16.html"])
    db.update_site(conn, 3, enabled=False)
    calls: list[str] = []
    add = lambda m: calls.append(m) or "added"  # noqa: E731

    b = FakeBrowser()
    run = db.get_run(conn, asyncio.run(run_once(conn, b, add_magnet=add)))
    assert (run["status"], run["added"]) == ("ok", 1), run["log"]
    assert calls == [f"magnet:?xt=urn:btih:{HASH}"]
    assert "skip: episode exists" in run["log"]  # zota's copy never hits the detail page
    assert "https://torrentzota206.com/torrent/r6o77rg.html" not in b.urls

    b = FakeBrowser()
    run = db.get_run(conn, asyncio.run(run_once(conn, b, add_magnet=add)))
    assert run["added"] == 0 and len(calls) == 1
    assert not DETAILS & set(b.urls)


def _moved_site(tmp_path):
    conn = db.connect(tmp_path / "app.db")
    db.update_site(conn, 1, url="https://torrentsome266.com", boards=["/v-4-16"])  # 268 is the +2 candidate
    for i in (2, 3):
        db.update_site(conn, i, enabled=False)
    return conn


def test_domain_probe_moves_site(tmp_path):
    conn = _moved_site(tmp_path)
    run = db.get_run(conn, asyncio.run(run_once(conn, FakeBrowser(), add_magnet=lambda m: "added")))
    assert "domain moved https://torrentsome266.com -> https://torrentsome268.com" in run["log"]
    assert run["added"] == 1 and run["status"] == "ok", run["log"]
    assert db.get_site(conn, 1)["url"] == "https://torrentsome268.com"


def test_domain_probe_dry_run_changes_nothing(tmp_path):
    conn = _moved_site(tmp_path)
    run = db.get_run(conn, asyncio.run(run_once(conn, FakeBrowser(), dry_run=True)))
    assert "would move https://torrentsome266.com -> https://torrentsome268.com (dry-run)" in run["log"]
    assert "dry-run: would add " + HASH in run["log"] and run["status"] == "ok"
    assert db.get_site(conn, 1)["url"] == "https://torrentsome266.com"
    assert not db.get_site(conn, 1)["last_ok_at"]


def test_domain_probe_original_recovers(tmp_path):
    conn = _moved_site(tmp_path)
    b = FakeBrowser({"https://torrentsome266.com/v-4-16": [DOWN, "torrentsome/board.html"]})
    run = db.get_run(conn, asyncio.run(run_once(conn, b, add_magnet=lambda m: "added")))
    assert "/v-4-16 recovered, not moving" in run["log"], run["log"]
    assert "domain moved" not in run["log"]
    assert db.get_site(conn, 1)["url"] == "https://torrentsome266.com"


def test_transmission_unconfigured_is_partial(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "TRANSMISSION_URL", "")  # real add_magnet: Request("") raises ValueError
    conn = db.connect(tmp_path / "app.db")
    db.update_site(conn, 1, boards=["/v-4-16"])
    for i in (2, 3):
        db.update_site(conn, i, enabled=False)
    run = db.get_run(conn, asyncio.run(run_once(conn, FakeBrowser())))
    assert run["status"] == "partial" and "transmission FAIL" in run["log"], run["log"]
    assert db.list_downloads(conn) == []


def test_failed_later_board_is_partial(tmp_path):
    conn = db.connect(tmp_path / "app.db")
    db.update_site(conn, 1, boards=["/v-4-16", "/v-2-13"])  # the fake browser only knows /v-4-16
    for i in (2, 3):
        db.update_site(conn, i, enabled=False)
    run = db.get_run(conn, asyncio.run(run_once(conn, FakeBrowser(), add_magnet=lambda m: "added")))
    assert run["status"] == "partial", run["log"]
    assert db.get_site(conn, 1)["last_ok_at"]
