import os
from pathlib import Path

# dev runs every crawl as a dry run (no Transmission adds, no site URL changes); only prod downloads.
APP_ENV: str = os.environ.get("APP_ENV", "dev")
if APP_ENV not in ("dev", "prod"):
    raise RuntimeError(f"APP_ENV must be dev or prod, got {APP_ENV!r}")
DRY_RUN: bool = APP_ENV != "prod"
DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "./data/dev"))
DB_PATH: Path = DATA_DIR / "app.db"
TRANSMISSION_URL: str = os.environ.get("TRANSMISSION_URL", "")
TRANSMISSION_USER: str = os.environ.get("TRANSMISSION_USER", "")
TRANSMISSION_PASSWORD: str = os.environ.get("TRANSMISSION_PASSWORD", "")
