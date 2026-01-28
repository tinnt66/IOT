"""
Database Models Module
Defines data models for rs485_samples and adxl_batches tables
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any


class RS485Sample:
    """Model for rs485_samples table"""
    
    def __init__(self, id: Optional[int] = None, time_local: Optional[str] = None,
                 temp_c: Optional[float] = None, hum_pct: Optional[float] = None,
                 wind_dir_deg: Optional[int] = None, wind_dir_txt: Optional[str] = None,
                 wind_spd_ms: Optional[float] = None, created_at: Optional[str] = None):
        self.id = id
        self.time_local = time_local or datetime.now().isoformat()
        self.temp_c = temp_c
        self.hum_pct = hum_pct
        self.wind_dir_deg = wind_dir_deg
        self.wind_dir_txt = wind_dir_txt
        self.wind_spd_ms = wind_spd_ms
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'time_local': self.time_local,
            'temp_c': self.temp_c,
            'hum_pct': self.hum_pct,
            'wind_dir_deg': self.wind_dir_deg,
            'wind_dir_txt': self.wind_dir_txt,
            'wind_spd_ms': self.wind_spd_ms,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'RS485Sample':
        """Create model instance from database row"""
        return cls(
            id=row['id'],
            time_local=row['time_local'],
            temp_c=row['temp_c'],
            hum_pct=row['hum_pct'],
            wind_dir_deg=row['wind_dir_deg'],
            wind_dir_txt=row['wind_dir_txt'],
            wind_spd_ms=row['wind_spd_ms'],
            created_at=row['created_at']
        )
    
    def __repr__(self) -> str:
        return f"<RS485Sample(id={self.id}, temp={self.temp_c}°C, hum={self.hum_pct}%)>"


class ADXLBatch:
    """Model for adxl_batches table"""
    
    def __init__(self, id: Optional[int] = None, chunk_start_us: Optional[int] = None,
                 samples: Optional[Dict[str, Any]] = None, created_at: Optional[str] = None):
        self.id = id
        self.chunk_start_us = chunk_start_us or 0
        self.samples = samples or {}
        self.created_at = created_at or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'chunk_start_us': self.chunk_start_us,
            'samples': self.samples,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_row(cls, row: sqlite3.Row) -> 'ADXLBatch':
        """Create model instance from database row"""
        return cls(
            id=row['id'],
            chunk_start_us=row['chunk_start_us'],
            samples=json.loads(row['samples']) if row['samples'] else {},
            created_at=row['created_at']
        )
    
    def __repr__(self) -> str:
        return f"<ADXLBatch(id={self.id}, chunk_start={self.chunk_start_us})>"
