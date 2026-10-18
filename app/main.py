"""FastAPI app: lifespan wiring and the plain-HTML screens."""
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from http import HTTPStatus
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app import config, db, doctor
from app.browser import Browser
from app.scheduler import Scheduler
from app.views import go, templates

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("APP_ENV=%s dry_run=%s db=%s", config.APP_ENV, config.DRY_RUN, config.DB_PATH)
    conn = db.connect(config.DB_PATH)
    browser = Browser()
    await browser.start()
    sched = Scheduler(conn, browser)
    sched.start()
    app.state.db, app.state.browser, app.state.scheduler = conn, browser, sched
    yield
    for t in list(doctor._tasks):
        t.cancel()
    await asyncio.gather(*doctor._tasks, return_exceptions=True)
    await sched.stop()
    await browser.stop()
    conn.close()


app = FastAPI(lifespan=lifespan)
app.include_router(doctor.router)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


def page(request: Request, name: str, status_code: int = 200, **ctx):
    return templates.TemplateResponse(request, name, ctx, status_code=status_code)


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    default = exc.detail == HTTPStatus(exc.status_code).phrase  # Starlette's English default, e.g. "Not Found"
    msg = ("페이지를 찾을 수 없습니다." if exc.status_code == 404 else "요청을 처리할 수 없습니다.") if default else exc.detail
    return page(request, "error.html", exc.status_code, code=exc.status_code, message=msg)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return page(request, "error.html", 422, code=422, message="입력값이 올바르지 않습니다.")


def stale_before(conn) -> str:
    """A site with no success since this time (3 intervals ago) is flagged."""
    stale = datetime.now() - timedelta(minutes=3 * int(db.get_setting(conn, "interval_min", "60")))
    return stale.isoformat(timespec="seconds")


# dashboard
@app.get("/")
async def index(request: Request, msg: str | None = None):
    conn, sched = request.app.state.db, request.app.state.scheduler
    nxt, now = sched.next_run_at, datetime.now()
    sites, cut = db.list_sites(conn, enabled_only=True), stale_before(conn)
    stale = [] if config.APP_ENV == "dev" else [s for s in sites if (s["last_ok_at"] or "") < cut]  # dev never sets it
    return page(request, "index.html", next_run_at=nxt, running=sched.running or msg == "started",
                due=bool(nxt and nxt <= now), interval_min=db.get_setting(conn, "interval_min", "60"), msg=msg,
                runs=db.list_runs(conn, 10), downloads=db.list_downloads(conn, 20),
                day_ago=(now - timedelta(days=1)).isoformat(timespec="seconds"),
                sites=sites, stale_sites=stale, programs=db.list_programs(conn))


@app.post("/run-now")
async def run_now(request: Request):
    ok = request.app.state.scheduler.trigger_now()
    return RedirectResponse("/?msg=started" if ok else "/?msg=already-running", status_code=303)


@app.post("/settings/interval")
async def set_interval(request: Request, minutes: int = Form(ge=1, le=1440)):
    request.app.state.scheduler.set_interval(minutes)
    return go("/", msg="interval")


@app.post("/settings/doctor-model")
async def set_doctor_model(request: Request, model: str = Form()):
    if model not in db.MODELS:
        raise HTTPException(400, "모델은 sonnet 또는 opus만 됩니다.")
    db.set_setting(request.app.state.db, "doctor_model", model)
    return go("/sites", msg="model")


@app.get("/runs/{id}")
async def run_detail(request: Request, id: int):
    run = db.get_run(request.app.state.db, id)
    if not run:
        raise HTTPException(404, "실행 기록이 없습니다.")
    return page(request, "run.html", run=run)


# programs
@app.get("/programs")
async def programs(request: Request, error: str | None = None, msg: str | None = None):
    return page(request, "programs.html", programs=db.list_programs(request.app.state.db), error=error, msg=msg)


@app.post("/programs")
async def add_program(request: Request, name: str = Form(), resolution: str = Form()):
    try:
        db.add_program(request.app.state.db, name, resolution)
    except ValueError as e:
        return go("/programs", str(e))
    return go("/programs", msg="added")


@app.post("/programs/{id}/enabled")
async def program_enabled(request: Request, id: int, enabled: str = Form()):
    db.set_program_enabled(request.app.state.db, id, enabled == "1")
    return go("/programs")


@app.post("/programs/{id}/delete")
async def program_delete(request: Request, id: int):
    db.delete_program(request.app.state.db, id)
    return go("/programs")


# sites
@app.get("/sites")
async def sites(request: Request, error: str | None = None, msg: str | None = None):
    conn = request.app.state.db
    return page(request, "sites.html", sites=db.list_sites(conn), reports=db.latest_doctor_report_per_site(conn),
                stale_before=stale_before(conn), interval_min=db.get_setting(conn, "interval_min", "60"),
                doctor_model=db.get_setting(conn, "doctor_model", "sonnet"), error=error, msg=msg)


@app.post("/sites/{id}/enabled")
async def site_enabled(request: Request, id: int, enabled: str = Form()):
    db.update_site(request.app.state.db, id, enabled=enabled == "1")
    return go("/sites")


@app.post("/sites/{id}")
async def site_edit(request: Request, id: int, url: str = Form(), boards: str = Form("")):
    try:
        url, lines = db.clean_site_fields(url, boards.splitlines())
    except ValueError as e:
        return go("/sites", str(e))
    db.update_site(request.app.state.db, id, url=url, boards=lines)
    return go("/sites", msg="applied")
