"""SQLite access. One autocommit connection, used only from the event-loop thread."""
import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS programs(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE,
  resolution TEXT NOT NULL DEFAULT 'any' CHECK (resolution IN ('720p','1080p','any')),
  enabled INTEGER NOT NULL DEFAULT 1);
CREATE TABLE IF NOT EXISTS sites(
  id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, url TEXT NOT NULL,
  boards TEXT NOT NULL DEFAULT '[]', enabled INTEGER NOT NULL DEFAULT 1, last_ok_at TEXT);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs(
  id INTEGER PRIMARY KEY, started TEXT NOT NULL, finished TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  matched INTEGER NOT NULL DEFAULT 0, added INTEGER NOT NULL DEFAULT 0, log TEXT NOT NULL DEFAULT '');
CREATE TABLE IF NOT EXISTS downloads(
  info_hash TEXT PRIMARY KEY,
  program_id INTEGER REFERENCES programs(id) ON DELETE SET NULL,
  episode TEXT, title TEXT NOT NULL, site TEXT NOT NULL, added_at TEXT NOT NULL,
  UNIQUE(program_id, episode));
CREATE TABLE IF NOT EXISTS doctor_reports(
  id INTEGER PRIMARY KEY, site_id INTEGER NOT NULL REFERENCES sites(id) ON DELETE CASCADE,
  started TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'running',
  model TEXT NOT NULL, verdict TEXT, report_json TEXT, cost_usd REAL,
  progress TEXT NOT NULL DEFAULT '');
CREATE INDEX IF NOT EXISTS downloads_added_at ON downloads(added_at);
CREATE INDEX IF NOT EXISTS doctor_reports_site ON doctor_reports(site_id, id);
"""

A, B = ["/v-4-16", "/v-2-13", "/v-4-17"], ["/c/4/16", "/c/2/13", "/c/4/17"]
SEED_SITES = [
    ("토렌트썸", "https://torrentsome268.com", A, 1),
    ("토렌트좋다", "https://torrentzota206.com", ["/t/4/16.html", "/t/2/13.html", "/t/4/17.html"], 1),
    ("토렌트티티", "https://torrenttt253.top", B, 1),
    ("토렌트알지", "https://torrentrj274.com", A, 0),
    ("토렌트밤", "https://torrentbam252.top", B, 0),
]
SEED_PROGRAMS = [
    ("라디오스타", "any", 1), ("돌싱포맨", "any", 0), ("PD 수첩", "720p", 0), ("나 혼자 산다", "any", 0),
    ("미운 우리 새끼", "any", 0), ("SBS 스페셜", "720p", 0), ("그것이 알고 싶다", "any", 0),
    ("금쪽 같은", "720p", 0), ("놀면 뭐하니", "any", 1), ("나는 솔로", "any", 0), ("전지적", "any", 0),
    ("유 퀴즈", "any", 0), ("알쓸인잡", "any", 0), ("지구오락실", "any", 0), ("태어난", "any", 0),
    ("애프터시그널", "any", 0), ("사랑은 계속된다", "any", 0),
]
SEED_SETTINGS = [("interval_min", "60"), ("doctor_model", "sonnet")]
RESOLUTIONS = ("720p", "1080p", "any")
MODELS = ("sonnet", "opus")
URL_RE = re.compile(r"^https?://[A-Za-z0-9.-]+(?::\d+)?$")
BOARD_RE = re.compile(r"^/\S*$")


def now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def connect(path: str | Path) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(DDL)
    conn.executemany("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", SEED_SETTINGS)
    if not conn.execute("SELECT 1 FROM programs LIMIT 1").fetchone():
        conn.executemany("INSERT INTO programs(name, resolution, enabled) VALUES (?, ?, ?)", SEED_PROGRAMS)
    if not conn.execute("SELECT 1 FROM sites LIMIT 1").fetchone():
        conn.executemany("INSERT INTO sites(name, url, boards, enabled) VALUES (?, ?, ?, ?)",
                         [(n, u, json.dumps(b), e) for n, u, b, e in SEED_SITES])
    # Anything still 'running' was cut off by a restart.
    conn.execute("UPDATE runs SET status='error', finished=?, log=log || char(10) || 'interrupted by restart' "
                 "WHERE status='running'", (now(),))
    conn.execute("UPDATE doctor_reports SET status='error', progress=progress || 'interrupted by restart' || char(10) "
                 "WHERE status='running'")
    return conn


def _all(conn, sql: str, *args) -> list[dict]:
    return [dict(r) for r in conn.execute(sql, args)]


def _one(conn, sql: str, *args) -> dict | None:
    r = conn.execute(sql, args).fetchone()
    return dict(r) if r else None


def _site(row: dict | None) -> dict | None:
    if row:
        row["boards"] = json.loads(row["boards"])
    return row


# programs
def list_programs(conn, enabled_only: bool = False) -> list[dict]:
    return _all(conn, "SELECT * FROM programs" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY id")


def add_program(conn, name: str, resolution: str) -> int:
    name = name.strip()
    if not name:
        raise ValueError("name is empty")
    if resolution not in RESOLUTIONS:
        raise ValueError(f"bad resolution: {resolution}")
    try:
        return conn.execute("INSERT INTO programs(name, resolution) VALUES (?, ?)", (name, resolution)).lastrowid
    except sqlite3.IntegrityError:
        raise ValueError(f"duplicate name: {name}") from None


def set_program_enabled(conn, id: int, enabled: bool) -> None:
    conn.execute("UPDATE programs SET enabled=? WHERE id=?", (int(enabled), id))


def delete_program(conn, id: int) -> None:
    conn.execute("DELETE FROM programs WHERE id=?", (id,))


# sites
def list_sites(conn, enabled_only: bool = False) -> list[dict]:
    rows = _all(conn, "SELECT * FROM sites" + (" WHERE enabled=1" if enabled_only else "") + " ORDER BY id")
    return [_site(r) for r in rows]


def get_site(conn, id: int) -> dict | None:
    return _site(_one(conn, "SELECT * FROM sites WHERE id=?", id))


def update_site(conn, id: int, *, url: str | None = None, boards: list[str] | None = None,
                enabled: bool | None = None, last_ok_at: str | None = None) -> None:
    fields = {"url": url, "boards": None if boards is None else json.dumps(boards),
              "enabled": None if enabled is None else int(enabled), "last_ok_at": last_ok_at}
    fields = {k: v for k, v in fields.items() if v is not None}
    if fields:
        sets = ", ".join(f"{k}=?" for k in fields)
        conn.execute(f"UPDATE sites SET {sets} WHERE id=?", (*fields.values(), id))


def clean_site_fields(url: str, boards: list[str]) -> tuple[str, list[str]]:
    """Validate a site's url/boards before update_site (web form and Doctor apply)."""
    url = url.strip().rstrip("/")
    boards = [b.strip() for b in boards if b.strip()]
    if not URL_RE.fullmatch(url):
        raise ValueError("bad url")
    if bad := [b for b in boards if not BOARD_RE.fullmatch(b)]:
        raise ValueError(f"bad board: {bad[0]}")
    if not boards:
        raise ValueError("boards empty")
    return url, boards


# settings
def get_setting(conn, key: str, default: str | None = None) -> str | None:
    r = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    return r[0] if r else default


def set_setting(conn, key: str, value: str) -> None:
    conn.execute("INSERT INTO settings(key, value) VALUES (?, ?) "
                 "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, value))


# runs
def create_run(conn) -> int:
    return conn.execute("INSERT INTO runs(started) VALUES (?)", (now(),)).lastrowid


def finish_run(conn, id: int, status: str, matched: int, added: int, log: str) -> None:
    conn.execute("UPDATE runs SET finished=?, status=?, matched=?, added=?, log=? WHERE id=?",
                 (now(), status, matched, added, log, id))


def list_runs(conn, limit: int = 20) -> list[dict]:
    return _all(conn, "SELECT * FROM runs ORDER BY id DESC LIMIT ?", limit)


def get_run(conn, id: int) -> dict | None:
    return _one(conn, "SELECT * FROM runs WHERE id=?", id)


# downloads
def download_exists(conn, info_hash: str) -> bool:
    return conn.execute("SELECT 1 FROM downloads WHERE info_hash=?", (info_hash,)).fetchone() is not None


def episode_exists(conn, program_id: int, episode: str) -> bool:
    return conn.execute("SELECT 1 FROM downloads WHERE program_id=? AND episode=?",
                        (program_id, episode)).fetchone() is not None


def add_download(conn, info_hash: str, program_id: int, episode: str | None, title: str, site: str) -> bool:
    try:
        conn.execute("INSERT INTO downloads(info_hash, program_id, episode, title, site, added_at) "
                     "VALUES (?, ?, ?, ?, ?, ?)", (info_hash, program_id, episode, title, site, now()))
        return True
    except sqlite3.IntegrityError:
        return False


def list_downloads(conn, limit: int = 50) -> list[dict]:
    return _all(conn, "SELECT d.*, p.name AS program_name FROM downloads d "
                      "LEFT JOIN programs p ON p.id = d.program_id ORDER BY d.added_at DESC LIMIT ?", limit)


# doctor reports
def create_doctor_report(conn, site_id: int, model: str) -> int:
    return conn.execute("INSERT INTO doctor_reports(site_id, started, model) VALUES (?, ?, ?)",
                        (site_id, now(), model)).lastrowid


def append_doctor_progress(conn, id: int, line: str) -> None:
    conn.execute("UPDATE doctor_reports SET progress = progress || ? || char(10) WHERE id=?", (line, id))


def finish_doctor_report(conn, id: int, status: str, verdict: str | None,
                         report_json: str | None, cost_usd: float | None) -> None:
    conn.execute("UPDATE doctor_reports SET status=?, verdict=?, report_json=?, cost_usd=? WHERE id=?",
                 (status, verdict, report_json, cost_usd, id))


def get_doctor_report(conn, id: int) -> dict | None:
    return _one(conn, "SELECT r.*, s.name AS site_name FROM doctor_reports r "
                      "JOIN sites s ON s.id = r.site_id WHERE r.id=?", id)


def latest_doctor_report_per_site(conn) -> dict[int, dict]:
    rows = _all(conn, "SELECT * FROM doctor_reports WHERE id IN "
                      "(SELECT MAX(id) FROM doctor_reports GROUP BY site_id)")
    return {r["site_id"]: r for r in rows}
