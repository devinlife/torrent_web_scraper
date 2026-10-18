import asyncio

from app import browser as B


class FakePage:
    url = ""

    async def goto(self, url, **kw):
        self.url = url
        return type("R", (), {"status": 200})()

    async def wait_for_timeout(self, ms): pass
    async def content(self): return "<html></html>"
    async def close(self): pass


class FakeCtx:
    async def new_page(self): return FakePage()


def test_same_host_is_paced(monkeypatch):
    clock, sleeps = [100.0], []

    async def fake_sleep(s):
        sleeps.append(s)
        clock[0] += s
    monkeypatch.setattr(B.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(B.asyncio, "sleep", fake_sleep)
    monkeypatch.setattr(B.random, "uniform", lambda a, b: 3.0)

    b = B.Browser(settle_ms=0)
    b._ctx, b._browser = FakeCtx(), type("Br", (), {"is_connected": lambda self: True})()

    async def go():
        await b.fetch("https://a.com/1")
        await b.fetch("https://b.com/1")  # other host: no wait
        clock[0] += 1
        await b.fetch("https://a.com/2")  # a.com finished ~1 s ago: wait the remaining 2 s
        clock[0] += 10
        await b.fetch("https://a.com/3")  # gap already elapsed
    asyncio.run(go())
    assert sleeps == [2.0]
