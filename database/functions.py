"""
Database CRUD Functions Module
Provides CRUD operations for rs485_samples and adxl_batches tables
"""

import json
from typing import Optional, List
from .connect import DatabaseConnection
from .models import RS485Sample, ADXLBatch


class RS485SampleCRUD:
    """CRUD operations for rs485_samples table"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create(self, sample: RS485Sample) -> int:
        """Insert a new rs485 sample into the database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rs485_samples 
                (time_local, temp_c, hum_pct, wind_dir_deg, wind_dir_txt, wind_spd_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (sample.time_local, sample.temp_c, sample.hum_pct, 
                  sample.wind_dir_deg, sample.wind_dir_txt, sample.wind_spd_ms,
                  sample.created_at))
            return cursor.lastrowid
    
    def get_by_id(self, sample_id: int) -> Optional[RS485Sample]:
        """Retrieve a sample by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rs485_samples WHERE id = ?", (sample_id,))
            row = cursor.fetchone()
            return RS485Sample.from_row(row) if row else None
    
    def get_latest(self, limit: int = 1) -> List[RS485Sample]:
        """Get the latest samples (ordered by id DESC)"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rs485_samples 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            return [RS485Sample.from_row(row) for row in cursor.fetchall()]
    
    def get_by_time_range(self, start_time: str, end_time: str) -> List[RS485Sample]:
        """Get samples within a time range"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rs485_samples 
                WHERE time_local BETWEEN ? AND ?
                ORDER BY time_local
            """, (start_time, end_time))
            return [RS485Sample.from_row(row) for row in cursor.fetchall()]
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[RS485Sample]:
        """Get all samples with optional pagination"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute("""
                    SELECT * FROM rs485_samples 
                    ORDER BY id DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("SELECT * FROM rs485_samples ORDER BY id DESC")
            return [RS485Sample.from_row(row) for row in cursor.fetchall()]
    
    def update(self, sample_id: int, **kwargs) -> bool:
        """Update a sample by ID with provided fields"""
        allowed_fields = ['time_local', 'temp_c', 'hum_pct', 'wind_dir_deg', 
                         'wind_dir_txt', 'wind_spd_ms']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [sample_id]
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE rs485_samples 
                SET {set_clause}
                WHERE id = ?
            """, values)
            return cursor.rowcount > 0
    
    def delete(self, sample_id: int) -> bool:
        """Delete a sample by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM rs485_samples WHERE id = ?", (sample_id,))
            return cursor.rowcount > 0
    
    def count(self) -> int:
        """Get total count of samples"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM rs485_samples")
            return cursor.fetchone()[0]


class ADXLBatchCRUD:
    """CRUD operations for adxl_batches table"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create(self, batch: ADXLBatch) -> int:
        """Insert a new ADXL batch into the database"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            samples_json = json.dumps(batch.samples)
            cursor.execute("""
                INSERT INTO adxl_batches 
                (chunk_start_us, samples, created_at)
                VALUES (?, ?, ?)
            """, (batch.chunk_start_us, samples_json, batch.created_at))
            return cursor.lastrowid
    
    def get_by_id(self, batch_id: int) -> Optional[ADXLBatch]:
        """Retrieve a batch by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM adxl_batches WHERE id = ?", (batch_id,))
            row = cursor.fetchone()
            return ADXLBatch.from_row(row) if row else None
    
    def get_by_chunk_start(self, chunk_start_us: int) -> Optional[ADXLBatch]:
        """Get batch by chunk start timestamp"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM adxl_batches 
                WHERE chunk_start_us = ?
            """, (chunk_start_us,))
            row = cursor.fetchone()
            return ADXLBatch.from_row(row) if row else None
    
    def get_by_chunk_range(self, start_us: int, end_us: int) -> List[ADXLBatch]:
        """Get batches within a chunk timestamp range"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM adxl_batches 
                WHERE chunk_start_us BETWEEN ? AND ?
                ORDER BY chunk_start_us
            """, (start_us, end_us))
            return [ADXLBatch.from_row(row) for row in cursor.fetchall()]
    
    def get_latest(self, limit: int = 1) -> List[ADXLBatch]:
        """Get the latest batches"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM adxl_batches 
                ORDER BY id DESC 
                LIMIT ?
            """, (limit,))
            return [ADXLBatch.from_row(row) for row in cursor.fetchall()]
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ADXLBatch]:
        """Get all batches with optional pagination"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            if limit:
                cursor.execute("""
                    SELECT * FROM adxl_batches 
                    ORDER BY id DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
            else:
                cursor.execute("SELECT * FROM adxl_batches ORDER BY id DESC")
            return [ADXLBatch.from_row(row) for row in cursor.fetchall()]
    
    def update(self, batch_id: int, **kwargs) -> bool:
        """Update a batch by ID with provided fields"""
        allowed_fields = ['chunk_start_us', 'samples']
        updates = {}
        
        for k, v in kwargs.items():
            if k in allowed_fields:
                if k == 'samples':
                    updates[k] = json.dumps(v)
                else:
                    updates[k] = v
        
        if not updates:
            return False
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [batch_id]
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE adxl_batches 
                SET {set_clause}
                WHERE id = ?
            """, values)
            return cursor.rowcount > 0
    
    def delete(self, batch_id: int) -> bool:
        """Delete a batch by ID"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM adxl_batches WHERE id = ?", (batch_id,))
            return cursor.rowcount > 0
    
    def count(self) -> int:
        """Get total count of batches"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM adxl_batches")
            return cursor.fetchone()[0]
