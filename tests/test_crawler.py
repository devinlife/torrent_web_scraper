import re
from pathlib import Path

import pytest

from app import crawler as c

FIX = Path(__file__).parent / "fixtures"
SITES = {  # key: (board base_url, expected unique posts, E348 url)
    "torrentsome": ("https://torrentsome268.com/v-4-16", 42, "https://torrentsome268.com/v/311439"),
    "torrentrj": ("https://torrentrj274.com/v-4-16", 37, "https://torrentrj274.com/v/311439"),
    "torrentzota": ("https://torrentzota206.com/t/4/16.html", 49, "https://torrentzota206.com/torrent/r6o77rg.html"),
    "torrenttt": ("https://torrenttt253.top/c/4", 50, "https://torrenttt253.top/t/mP9XVQ.html"),
    "torrentbam": ("https://torrentbam252.top/c/4", 30, "https://torrentbam252.top/t/1BeK5b.html"),
}
HASH = "4e4d86cbee91db107def6d3fd24271afd28130e2"
E348 = "놀면 뭐하니.E348.261017.720p-NEXT"


def fixture(site: str, page: str) -> str:
    return (FIX / site / f"{page}.html").read_text(encoding="utf-8")


def posts(site: str) -> list[tuple[str, str]]:
    return c.parse_board(fixture(site, "board"), SITES[site][0])


@pytest.mark.parametrize("site", SITES)
def test_parse_board(site):
    ps = posts(site)
    assert len(ps) == SITES[site][1] >= 20
    urls = [u for _, u in ps]
    assert len(set(urls)) == len(urls)
    assert all(u.startswith("https://") and c.POST_RE.search(u) for u in urls)
    assert all(t and not t.startswith(("[", "예능·오락 ")) for t, _ in ps)


@pytest.mark.parametrize("site", SITES)
def test_e348_found(site):
    assert (E348, SITES[site][2]) in posts(site)


@pytest.mark.parametrize("site", SITES)
def test_dry_match(site):
    progs = [{"name": "라디오스타", "resolution": "any"}, {"name": "놀면 뭐하니", "resolution": "any"}]
    assert [t for t, _ in posts(site) if c.match_program(t, progs)] == [E348]


def test_zota_category_excluded():
    assert 'href="/t/4.html"' in fixture("torrentzota", "board")
    assert not any(re.search(r"/t/\d+\.html$", u) for _, u in posts("torrentzota"))


@pytest.mark.parametrize("site", SITES)
def test_detail_hash(site):
    assert c.extract_magnets(fixture(site, "detail")) == [HASH]
    assert c.magnet_uri(HASH) == "magnet:?xt=urn:btih:" + HASH


@pytest.mark.parametrize("site,poster", [("torrentsome", "a916eee9d8200653ab4ea1bffb069ab218c71eb7"),
                                         ("torrentzota", "41f6229507a4be8a23ee81b3c0f42599ae2b849a")])
def test_poster_hex_ignored(site, poster):
    html = fixture(site, "detail")
    assert poster in html and poster not in c.extract_magnets(html)


@pytest.mark.parametrize("title,key", [
    ("런닝맨.E823.261011.720p-NEXT", "E823.261011"),
    ("영화가 좋다.E1026.261017.720p-NEXT", "E1026.261017"),
    ("접속 무비월드.E00.261017.720p-NEXT", "E00.261017"),
    ("100일의 거짓말 E01 1080p WEB H264-KBBQ", "E01"),
    ("그것이 알고 싶다.E1508.261017.720p-NEXT", "E1508.261017"),
    ("신인감독 김연경 2.E01.261011.720p-NEXT", "E01.261011"),
    ("우주떡집.최종.E12.1080p.H264.AAC.VIU.WEB-DL-LoveBug", "E12"),
    ("연애박사.Between Steps.E04.1080p.DSNP.WEB-DL.AAC.2.0-Sniper", "E04"),
    ("냉장고를 부탁해 since 2014.E92.261011.720p-NEXT", "E92.261011"),
    ("놀면 뭐하니.E348.261017.720p-NEXT", "E348.261017"),
    ("호프 Hope (2026) (1080p AMZN WEB-DL x265 10bit EAC3 5.1 Korean Silence)", None),
    ("벅스(Bugs) 2026년 10월 01일 실시간 TOP 100 [FLAC+MP3]", None),
])
def test_episode_key(title, key):
    assert c.episode_key(title) == key


def test_match():
    pd = "PD 수첩.E1234.261014.720p-NEXT"
    assert c.match(pd, {"name": "pd 수첩", "resolution": "720p"})
    assert not c.match(pd, {"name": "pd 수첩", "resolution": "1080p"})
    assert c.match("전지적 참견 시점.E421.261017.720p-NEXT", {"name": "전지적", "resolution": "any"})
    assert not c.match("놀면 뭐 하니.E348.261017.720p-NEXT", {"name": "놀면 뭐하니", "resolution": "any"})
    a, b = {"name": "놀면", "resolution": "any"}, {"name": "놀면 뭐하니", "resolution": "any"}
    assert c.match_program(E348, [a, b]) is a
    assert c.match_program(E348, [b, a]) is b
    assert c.match_program("런닝맨.E823", [a, b]) is None


def test_domain_candidates():
    assert c.domain_candidates("https://torrentsome268.com/") == [
        f"https://torrentsome{n}.com" for n in range(269, 274)]
    assert c.domain_candidates("https://torrenttt253.top") == [f"https://torrenttt{n}.top" for n in range(254, 259)]
    assert c.domain_candidates("https://example.com") == []
