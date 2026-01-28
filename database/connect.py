"""
Database Connection Management Module
Handles SQLite database connections and initialization
"""

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path


def get_db_path() -> str:
    """Get database path from environment variable or use default"""
    # Try to load from .env file in project root
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                if line.startswith('DB_PATH='):
                    db_name = line.split('=', 1)[1].strip()
                    # Return absolute path relative to project root
                    return str(Path(__file__).parent.parent / db_name)
    
    # Default fallback
    return str(Path(__file__).parent.parent / 'sensors.db')



class DatabaseConnection:
    """Manages SQLite database connections"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or get_db_path()
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize database and create tables if they don't exist"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create rs485_samples table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rs485_samples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time_local TEXT NOT NULL,
                    temp_c REAL,
                    hum_pct REAL,
                    wind_dir_deg INTEGER,
                    wind_dir_txt TEXT,
                    wind_spd_ms REAL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Create indexes for rs485_samples
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS rs485_samples_id_desc_idx
                ON rs485_samples (id DESC)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS rs485_samples_time_local_idx
                ON rs485_samples (time_local)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS rs485_samples_created_at_idx
                ON rs485_samples (created_at)
            """)
            
            # Create adxl_batches table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS adxl_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chunk_start_us INTEGER NOT NULL,
                    samples TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                )
            """)
            
            # Create indexes for adxl_batches
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS adxl_batches_id_idx
                ON adxl_batches (id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS adxl_batches_created_at_idx
                ON adxl_batches (created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS adxl_batches_chunk_start_us_idx
                ON adxl_batches (chunk_start_us)
            """)
            
            conn.commit()
