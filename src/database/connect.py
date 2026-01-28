"""
Database Connection Management Module
Handles SQLite database connections and ORM initialization
"""

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


def get_db_path() -> str:
    """Get database path from environment variable or use default"""
    root_dir = Path(__file__).resolve().parents[2]
    # Try to load from .env file in project root
    env_path = root_dir / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                if line.startswith('DB_PATH='):
                    db_name = line.split('=', 1)[1].strip()
                    p = Path(db_name)
                    if not p.is_absolute():
                        p = root_dir / p
                    p.parent.mkdir(parents=True, exist_ok=True)
                    return str(p)
    
    # Default fallback
    p = root_dir / "checkpoint" / "sensors.db"
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)



class DatabaseConnection:
    """Manages SQLAlchemy engine + session factory"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )
        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False, expire_on_commit=False)
        self._init_database()
    
    @contextmanager
    def get_session(self) -> Iterator[Session]:
        """Context manager for ORM sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def _init_database(self):
        """Initialize database tables/indexes"""
        Base.metadata.create_all(bind=self.engine)
