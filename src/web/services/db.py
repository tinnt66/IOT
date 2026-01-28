from __future__ import annotations

import threading
from pathlib import Path

from database import Database

from ..config import settings


_ROOT_DIR = Path(__file__).resolve().parents[3]

_DB_SINGLETON: Database | None = None
_DB_SINGLETON_LOCK = threading.Lock()


def resolve_db_path() -> Path:
    db_path = Path(settings.db_path)
    if not db_path.is_absolute():
        db_path = _ROOT_DIR / db_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def get_database() -> Database:
    global _DB_SINGLETON
    if _DB_SINGLETON is None:
        with _DB_SINGLETON_LOCK:
            if _DB_SINGLETON is None:
                _DB_SINGLETON = Database(db_path=str(resolve_db_path()))
    return _DB_SINGLETON

