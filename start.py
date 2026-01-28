#!/usr/bin/env python3
"""
Project bootstrap script.

1) Create virtual environment (.venv) if missing
2) Install dependencies from requirements.txt
3) Initialize SQLite DB (if missing)

Usage:
  python start.py
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
VENV_DIR = ROOT_DIR / ".venv"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"
ENV_FILE = ROOT_DIR / ".env"


def _venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _run(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def _ensure_venv() -> Path:
    py = _venv_python()
    if py.exists():
        return py

    if VENV_DIR.exists():
        print("⚠️  Detected an existing but broken .venv (missing python). Recreating it...")
        builder = venv.EnvBuilder(with_pip=True, clear=True)
        builder.create(str(VENV_DIR))
        return py

    print("Creating virtual environment in .venv ...")
    builder = venv.EnvBuilder(with_pip=True)
    builder.create(str(VENV_DIR))
    return py


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def _install_deps(venv_py: Path) -> None:
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f"Missing {REQUIREMENTS_FILE}")

    marker = VENV_DIR / ".requirements.sha256"
    want = _sha256_file(REQUIREMENTS_FILE)
    if marker.exists():
        have = marker.read_text(encoding="utf-8", errors="replace").strip()
        if have == want:
            print("Dependencies already installed (requirements.txt unchanged).")
            return

    print("Installing dependencies...")
    _run([str(venv_py), "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REQUIREMENTS_FILE)])
    marker.write_text(want, encoding="utf-8")


def _read_env_db_path() -> str | None:
    # Priority: OS env
    if os.getenv("DB_PATH"):
        return os.getenv("DB_PATH")

    # Then .env file
    if not ENV_FILE.exists():
        return None

    for raw in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != "DB_PATH":
            continue
        value = value.strip().strip('"').strip("'")
        return value or None

    return None


def _resolve_db_path() -> Path:
    db = _read_env_db_path() or "checkpoint/sensors.db"
    p = Path(db)
    if not p.is_absolute():
        p = ROOT_DIR / p
    return p


def _init_db_if_missing(venv_py: Path) -> None:
    db_path = _resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    if db_path.exists():
        print(f"Database already exists: {db_path}")
        return

    print("Initializing database...")
    code = f"""
import sys
from pathlib import Path

root = Path({str(ROOT_DIR)!r})
sys.path.insert(0, str(root / "src"))

from database import Database

db = Database(db_path={str(db_path)!r})
print("✓ Database initialized successfully!")
print("  Location:", db.connection.db_path)
print("\\n📊 Current Statistics:")
print("  RS485 samples:", db.rs485_samples.count())
print("  ADXL batches: ", db.adxl_batches.count())
"""
    _run([str(venv_py), "-c", code])


def main() -> int:
    print("=" * 60)
    print("Project Setup")
    print("=" * 60)

    venv_py = _ensure_venv()
    _install_deps(venv_py)
    _init_db_if_missing(venv_py)

    print("\n✅ Done.")
    print("\nNext:")
    if os.name == "nt":
        print(r"  .venv\Scripts\python.exe main.py")
    else:
        print("  .venv/bin/python main.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

