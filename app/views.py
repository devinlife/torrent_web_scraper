"""The one Jinja environment both main.py and doctor.py render with: globals, filters, redirect helper."""
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode

from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

from app import config

LABEL = {"ok": "정상", "partial": "일부 실패", "error": "실패", "running": "실행 중", "done": "완료",
         "domain_moved": "도메인 이전", "blocked": "차단", "site_down": "사이트 다운",
         "cloudflare": "CF 인증 필요", "parser_broken": "파서 고장"}
# ?msg= flash texts: (flash-<kind>, text); {n} is filled by the page (e.g. interval minutes).
FLASH = {"started": ("info", "실행을 시작했습니다. 끝나면 결과가 여기에 나옵니다."),
         "already-running": ("info", "이미 실행 중입니다."),
         "interval": ("ok", "주기를 {n}분으로 바꿨습니다."),
         "applied": ("ok", "설정을 바꿨습니다. 다음 실행에서 확인됩니다.")}


def _d(v) -> datetime | None:
    return datetime.fromisoformat(v) if isinstance(v, str) else v


def dt(v, now: datetime | None = None) -> str:
    if not (d := _d(v)):
        return "-"
    now = now or datetime.now()
    fmt = "%H:%M" if d.date() == now.date() else "%m-%d %H:%M" if d.year == now.year else "%Y-%m-%d %H:%M"
    iso = escape(d.isoformat(timespec="seconds"))
    return Markup(f'<time datetime="{iso}" title="{iso}">{d:{fmt}}</time>')


def ago(v, now: datetime | None = None) -> str:
    if not (d := _d(v)):
        return "-"
    s = int(((now or datetime.now()) - d).total_seconds())
    n, tail = abs(s), "전" if s >= 0 else "후"
    if n < 60:
        return "방금"
    for unit, size in (("일", 86400), ("시간", 3600), ("분", 60)):
        if n >= size:
            return f"{n // size}{unit} {tail}"


def dur(start, end) -> str:
    if not end:
        return "실행 중"
    m, s = divmod(int((_d(end) - _d(start)).total_seconds()), 60)
    return f"{m}분 {s}초" if m else f"{s}초"


HERE = Path(__file__).parent
templates = Jinja2Templates(directory=HERE / "templates")
CSS_V = int((HERE / "static" / "app.css").stat().st_mtime)  # cache-buster; uvicorn --reload watches *.py only
templates.env.globals.update(APP_ENV=config.APP_ENV, LABEL=LABEL, FLASH=FLASH, CSS_V=CSS_V)
templates.env.filters.update(dt=dt, ago=ago, dur=dur)
templates.env.policies["json.dumps_kwargs"] = {"ensure_ascii": False}  # readable confirm() text


def go(path: str, error: str | None = None, msg: str | None = None) -> RedirectResponse:
    q = urlencode({k: v for k, v in (("error", error), ("msg", msg)) if v})
    return RedirectResponse(path + (f"?{q}" if q else ""), status_code=303)
