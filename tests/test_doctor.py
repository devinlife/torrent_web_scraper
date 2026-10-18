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
