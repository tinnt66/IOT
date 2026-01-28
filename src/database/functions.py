"""
Database CRUD Functions Module
Provides ORM CRUD operations for rs485_samples and adxl_batches tables
"""

from typing import Optional, List
from .connect import DatabaseConnection
from .models import RS485Sample, ADXLBatch
from sqlalchemy import select, func, update as sa_update, delete as sa_delete


class RS485SampleCRUD:
    """CRUD operations for rs485_samples table"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create(self, sample: RS485Sample) -> int:
        """Insert a new rs485 sample into the database"""
        with self.db.get_session() as s:
            s.add(sample)
            s.flush()
            return int(sample.id)
    
    def get_by_id(self, sample_id: int) -> Optional[RS485Sample]:
        """Retrieve a sample by ID"""
        with self.db.get_session() as s:
            return s.get(RS485Sample, sample_id)
    
    def get_latest(self, limit: int = 1) -> List[RS485Sample]:
        """Get the latest samples (ordered by id DESC)"""
        with self.db.get_session() as s:
            stmt = select(RS485Sample).order_by(RS485Sample.id.desc()).limit(limit)
            return list(s.scalars(stmt).all())
    
    def get_by_time_range(self, start_time: str, end_time: str) -> List[RS485Sample]:
        """Get samples within a time range"""
        with self.db.get_session() as s:
            stmt = (
                select(RS485Sample)
                .where(RS485Sample.time_local >= start_time)
                .where(RS485Sample.time_local <= end_time)
                .order_by(RS485Sample.time_local.asc())
            )
            return list(s.scalars(stmt).all())
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[RS485Sample]:
        """Get all samples with optional pagination"""
        with self.db.get_session() as s:
            stmt = select(RS485Sample).order_by(RS485Sample.id.desc())
            if limit:
                stmt = stmt.limit(limit).offset(offset)
            return list(s.scalars(stmt).all())

    def get_by_created_at_range(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[RS485Sample]:
        """Get samples filtered by created_at (ISO string compare)."""
        with self.db.get_session() as s:
            stmt = select(RS485Sample).order_by(RS485Sample.id.desc())
            if start:
                stmt = stmt.where(RS485Sample.created_at >= start)
            if end:
                stmt = stmt.where(RS485Sample.created_at <= end)
            stmt = stmt.limit(limit).offset(offset)
            return list(s.scalars(stmt).all())
    
    def update(self, sample_id: int, **kwargs) -> bool:
        """Update a sample by ID with provided fields"""
        allowed_fields = ['time_local', 'temp_c', 'hum_pct', 'wind_dir_deg', 
                         'wind_dir_txt', 'wind_spd_ms']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        with self.db.get_session() as s:
            stmt = sa_update(RS485Sample).where(RS485Sample.id == sample_id).values(**updates)
            res = s.execute(stmt)
            return (res.rowcount or 0) > 0
    
    def delete(self, sample_id: int) -> bool:
        """Delete a sample by ID"""
        with self.db.get_session() as s:
            stmt = sa_delete(RS485Sample).where(RS485Sample.id == sample_id)
            res = s.execute(stmt)
            return (res.rowcount or 0) > 0
    
    def count(self) -> int:
        """Get total count of samples"""
        with self.db.get_session() as s:
            return int(s.scalar(select(func.count()).select_from(RS485Sample)) or 0)


class ADXLBatchCRUD:
    """CRUD operations for adxl_batches table"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def create(self, batch: ADXLBatch) -> int:
        """Insert a new ADXL batch into the database"""
        with self.db.get_session() as s:
            s.add(batch)
            s.flush()
            return int(batch.id)
    
    def get_by_id(self, batch_id: int) -> Optional[ADXLBatch]:
        """Retrieve a batch by ID"""
        with self.db.get_session() as s:
            return s.get(ADXLBatch, batch_id)
    
    def get_by_chunk_start(self, chunk_start_us: int) -> Optional[ADXLBatch]:
        """Get batch by chunk start timestamp"""
        with self.db.get_session() as s:
            stmt = select(ADXLBatch).where(ADXLBatch.chunk_start_us == chunk_start_us).limit(1)
            return s.scalars(stmt).first()
    
    def get_by_chunk_range(self, start_us: int, end_us: int) -> List[ADXLBatch]:
        """Get batches within a chunk timestamp range"""
        with self.db.get_session() as s:
            stmt = (
                select(ADXLBatch)
                .where(ADXLBatch.chunk_start_us >= start_us)
                .where(ADXLBatch.chunk_start_us <= end_us)
                .order_by(ADXLBatch.chunk_start_us.asc())
            )
            return list(s.scalars(stmt).all())
    
    def get_latest(self, limit: int = 1) -> List[ADXLBatch]:
        """Get the latest batches"""
        with self.db.get_session() as s:
            stmt = select(ADXLBatch).order_by(ADXLBatch.id.desc()).limit(limit)
            return list(s.scalars(stmt).all())
    
    def get_all(self, limit: Optional[int] = None, offset: int = 0) -> List[ADXLBatch]:
        """Get all batches with optional pagination"""
        with self.db.get_session() as s:
            stmt = select(ADXLBatch).order_by(ADXLBatch.id.desc())
            if limit:
                stmt = stmt.limit(limit).offset(offset)
            return list(s.scalars(stmt).all())

    def get_by_created_at_range(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: int = 200,
        offset: int = 0,
    ) -> List[ADXLBatch]:
        """Get batches filtered by created_at (ISO string compare)."""
        with self.db.get_session() as s:
            stmt = select(ADXLBatch).order_by(ADXLBatch.id.desc())
            if start:
                stmt = stmt.where(ADXLBatch.created_at >= start)
            if end:
                stmt = stmt.where(ADXLBatch.created_at <= end)
            stmt = stmt.limit(limit).offset(offset)
            return list(s.scalars(stmt).all())
    
    def update(self, batch_id: int, **kwargs) -> bool:
        """Update a batch by ID with provided fields"""
        allowed_fields = ['chunk_start_us', 'samples']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not updates:
            return False
        
        with self.db.get_session() as s:
            stmt = sa_update(ADXLBatch).where(ADXLBatch.id == batch_id).values(**updates)
            res = s.execute(stmt)
            return (res.rowcount or 0) > 0
    
    def delete(self, batch_id: int) -> bool:
        """Delete a batch by ID"""
        with self.db.get_session() as s:
            stmt = sa_delete(ADXLBatch).where(ADXLBatch.id == batch_id)
            res = s.execute(stmt)
            return (res.rowcount or 0) > 0
    
    def count(self) -> int:
        """Get total count of batches"""
        with self.db.get_session() as s:
            return int(s.scalar(select(func.count()).select_from(ADXLBatch)) or 0)
