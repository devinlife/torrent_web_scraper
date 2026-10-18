"""Transmission RPC over stdlib urllib. Blocking: call via asyncio.to_thread."""
import base64
import http.client
import json
import urllib.error
import urllib.request

from app import config


class TransmissionError(Exception):
    pass


_sid = ""


def rpc(method: str, **arguments) -> dict:
    global _sid
    auth = base64.b64encode(f"{config.TRANSMISSION_USER}:{config.TRANSMISSION_PASSWORD}".encode()).decode()
    body = json.dumps({"method": method, "arguments": arguments}).encode()
    for _ in range(2):
        try:
            req = urllib.request.Request(config.TRANSMISSION_URL, data=body, headers={
                "Authorization": f"Basic {auth}", "Content-Type": "application/json",
                "X-Transmission-Session-Id": _sid})
            with urllib.request.urlopen(req, timeout=10) as r:
                resp = json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 409:
                raise TransmissionError(f"HTTPError {e.code} {e.reason}") from None
            _sid = e.headers.get("X-Transmission-Session-Id", "")  # stale/missing session id -> retry once
            continue
        except (urllib.error.URLError, OSError, ValueError, http.client.HTTPException) as e:
            raise TransmissionError(f"{type(e).__name__}: {getattr(e, 'reason', e)}") from None
        if resp.get("result") != "success":
            raise TransmissionError(f"result: {resp.get('result')}")
        return resp.get("arguments", {})
    raise TransmissionError("409 twice")


def add_magnet(magnet: str) -> str:
    res = rpc("torrent-add", filename=magnet)
    if "torrent-added" in res:
        return "added"
    if "torrent-duplicate" in res:
        return "duplicate"
    raise TransmissionError(f"unexpected torrent-add result: {list(res)}")
