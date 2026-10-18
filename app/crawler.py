"""Pure parsing/matching functions. No I/O."""
import re
from collections.abc import Iterable, Mapping
from html.parser import HTMLParser
from urllib.parse import urljoin

POST_RE = re.compile(r'/(?:v/\d+|torrent/[a-z0-9]+\.html|t/(?!\d+\.html)[A-Za-z0-9]+\.html)$')
EP_RE = re.compile(r'(?<![A-Za-z0-9])E(\d{1,4})(?:\.(\d{6}))?(?!\d)')
MAG_RE = re.compile(r'^magnet:\?xt=urn:(?:btih:)?([0-9A-Fa-f]{40})\b')
HOSTNUM_RE = re.compile(r'^(https?://[^/]*?)(\d+)(\.[^/.]+)/?$')  # "https://torrentsome268.com"


class _Links(HTMLParser):
    """Collects (href, title attr, link text) for every <a href>."""

    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str, str]] = []
        self._cur: list | None = None

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        self._close()
        a = dict(attrs)
        if a.get("href"):
            self._cur = [a["href"].strip(), a.get("title") or "", []]

    def handle_endtag(self, tag):
        if tag == "a":
            self._close()

    def handle_data(self, data):
        if self._cur:
            self._cur[2].append(data)

    def _close(self):
        if self._cur:
            self.links.append((self._cur[0], self._cur[1], "".join(self._cur[2])))
        self._cur = None


def _links(html: str) -> list[tuple[str, str, str]]:
    p = _Links()
    p.feed(html)
    p.close()
    p._close()
    return p.links


def parse_board(html: str, base_url: str) -> list[tuple[str, str]]:
    """(title, absolute post url) in page order, deduped by url (first wins). Sidebar links included."""
    out: dict[str, str] = {}
    for href, title, text in _links(html):
        url = urljoin(base_url, href)
        if url in out or not POST_RE.search(url):
            continue
        title = title.strip() or " ".join(text.split())
        if title:
            out[url] = title
    return [(t, u) for u, t in out.items()]


def match(title: str, program: Mapping) -> bool:
    t = title.lower()
    res = program["resolution"]
    return all(w in t for w in program["name"].lower().split()) and (res == "any" or any(r in t for r in res.split(",")))


def match_program(title: str, programs: Iterable[Mapping]) -> Mapping | None:
    return next((p for p in programs if match(title, p)), None)


def episode_key(title: str) -> str | None:
    m = EP_RE.search(title)
    return (f"E{m[1]}.{m[2]}" if m[2] else f"E{m[1]}") if m else None


def extract_magnets(html: str) -> list[str]:
    """Hashes from <a href="magnet:..."> only; page text has 40-hex poster file names."""
    out: dict[str, None] = {}
    for href, _, _ in _links(html):
        if href.startswith("magnet:") and (m := MAG_RE.match(href)):
            out[m[1].lower()] = None
    return list(out)


def magnet_uri(info_hash: str) -> str:
    return f"magnet:?xt=urn:btih:{info_hash}"


def domain_candidates(url: str, n: int = 5) -> list[str]:
    m = HOSTNUM_RE.match(url.rstrip("/"))
    if not m:
        return []
    pre, num, tld = m.groups()
    return [f"{pre}{int(num) + i}{tld}" for i in range(1, n + 1)]
