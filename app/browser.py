"""One shared headless Chromium. --headless=new is required: it keeps Chrome's ECH, which gets past SNI resets."""
import asyncio
import random
import re
import time
from contextlib import suppress
from dataclasses import dataclass
from urllib.parse import urlsplit

from playwright.async_api import Error, TimeoutError, async_playwright


@dataclass(frozen=True)
class FetchResult:
    status: int  # final HTTP status; 0 when navigation failed
    final_url: str  # page.url after redirects; the request url on failure
    html: str  # page.content(); "" on failure
    error: str | None  # None on success, e.g. "net::ERR_CONNECTION_CLOSED", "timeout", "no response"

    @property
    def ok(self) -> bool:
        return self.error is None and 200 <= self.status < 400


def _err(e: Error) -> str:
    if m := re.search(r"net::ERR_[A-Z_]+", str(e)):
        return m[0]
    if isinstance(e, TimeoutError):
        return "timeout"
    return str(e).split("\n", 1)[0][:200]


class Browser:
    # ponytail: one global lock, one page at a time; ~3 s/page is fine for ~15 pages/run.
    def __init__(self, settle_ms: int = 2000, gap_s: tuple[float, float] = (2.0, 5.0)) -> None:
        self.settle_ms, self.gap_s = settle_ms, gap_s
        self._last: dict[str, float] = {}  # host -> monotonic time its last fetch finished
        self._lock = asyncio.Lock()
        self._pw = self._browser = self._ctx = None

    async def start(self) -> None:
        self._ctx = None  # stays None if launch fails, so the next fetch retries
        if self._pw is None:
            self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(headless=False, args=["--headless=new", "--no-sandbox"])
        self._ctx = await self._browser.new_context(locale="ko-KR")

    async def stop(self) -> None:
        for obj in (self._ctx, self._browser, self._pw):
            if obj is not None:
                with suppress(Exception):
                    await (obj.stop() if obj is self._pw else obj.close())
        self._pw = self._browser = self._ctx = None

    async def fetch(self, url: str, *, timeout_ms: int = 30000, retries: int = 2) -> FetchResult:
        """Never raises for navigation failures; callers branch on .ok."""
        host = urlsplit(url).hostname or ""
        # ponytail: pacing sleeps inside the lock (one page at a time anyway), so it also stalls
        # other hosts; move it out with per-host reservations if concurrent fetches start to matter.
        async with self._lock:
            if (wait := self._last.get(host, -1e9) + random.uniform(*self.gap_s) - time.monotonic()) > 0:
                await asyncio.sleep(wait)  # be gentle: 2-5 s between requests to the same host
            try:
                return await self._fetch(url, timeout_ms, retries)
            finally:
                self._last[host] = time.monotonic()

    async def _fetch(self, url: str, timeout_ms: int, retries: int) -> FetchResult:
        if self._ctx is None or self._browser is None or not self._browser.is_connected():
            try:
                if self._browser is not None:  # crashed: drop the dead browser, keep playwright
                    with suppress(Error):
                        await self._browser.close()
                await self.start()
            except Error as e:
                return FetchResult(0, url, "", _err(e))
        error = ""
        for attempt in range(1 + retries):
            if attempt:
                await asyncio.sleep(2)
            page = None
            try:
                page = await self._ctx.new_page()
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                await page.wait_for_timeout(self.settle_ms)
                return FetchResult(resp.status if resp else 0, page.url, await page.content(),
                                   None if resp else "no response")
            except Error as e:
                error = _err(e)
            finally:
                if page is not None:
                    with suppress(Error):
                        await page.close()
        return FetchResult(0, url, "", error)
