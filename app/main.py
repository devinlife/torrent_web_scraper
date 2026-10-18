"""FastAPI app: lifespan wiring and the plain-HTML screens."""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from app import config, db, doctor
from app.browser import Browser
from app.scheduler import Scheduler

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
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.globals["APP_ENV"] = config.APP_ENV


def go(path: str, error: str | None = None) -> RedirectResponse:
    return RedirectResponse(path + (f"?error={quote(error)}" if error else ""), status_code=303)


def page(request: Request, name: str, **ctx):
    return templates.TemplateResponse(request, name, ctx)


# dashboard
@app.get("/")
async def index(request: Request, msg: str | None = None):
    conn, sched = request.app.state.db, request.app.state.scheduler
    return page(request, "index.html", next_run_at=sched.next_run_at, running=sched.running,
                interval_min=db.get_setting(conn, "interval_min", "60"), msg=msg,
                runs=db.list_runs(conn, 10), downloads=db.list_downloads(conn, 20))


@app.post("/run-now")
async def run_now(request: Request):
    ok = request.app.state.scheduler.trigger_now()
    return RedirectResponse("/" if ok else "/?msg=already-running", status_code=303)


@app.post("/settings/interval")
async def set_interval(request: Request, minutes: int = Form(ge=1, le=1440)):
    request.app.state.scheduler.set_interval(minutes)
    return go("/")


@app.post("/settings/doctor-model")
async def set_doctor_model(request: Request, model: str = Form()):
    if model not in db.MODELS:
        raise HTTPException(400, "model must be sonnet or opus")
    db.set_setting(request.app.state.db, "doctor_model", model)
    return go("/sites")


@app.get("/runs/{id}")
async def run_detail(request: Request, id: int):
    run = db.get_run(request.app.state.db, id)
    if not run:
        raise HTTPException(404, "run not found")
    return page(request, "run.html", run=run)


# programs
@app.get("/programs")
async def programs(request: Request, error: str | None = None):
    return page(request, "programs.html", programs=db.list_programs(request.app.state.db), error=error)


@app.post("/programs")
async def add_program(request: Request, name: str = Form(), resolution: str = Form()):
    try:
        db.add_program(request.app.state.db, name, resolution)
    except ValueError as e:
        return go("/programs", str(e))
    return go("/programs")


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
async def sites(request: Request, error: str | None = None):
    conn = request.app.state.db
    return page(request, "sites.html", sites=db.list_sites(conn), reports=db.latest_doctor_report_per_site(conn),
                doctor_model=db.get_setting(conn, "doctor_model", "sonnet"), error=error)


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
    return go("/sites")
