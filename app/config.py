import os
from pathlib import Path

DATA_DIR: Path = Path(os.environ.get("DATA_DIR", "./data"))
DB_PATH: Path = DATA_DIR / "app.db"
TRANSMISSION_URL: str = os.environ.get("TRANSMISSION_URL", "")
TRANSMISSION_USER: str = os.environ.get("TRANSMISSION_USER", "")
TRANSMISSION_PASSWORD: str = os.environ.get("TRANSMISSION_PASSWORD", "")
