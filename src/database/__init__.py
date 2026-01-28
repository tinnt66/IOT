"""
Database Package
SQLite database interface for IoT sensor data
"""

from .connect import DatabaseConnection
from .models import RS485Sample, ADXLBatch
from .functions import RS485SampleCRUD, ADXLBatchCRUD


class Database:
    """Main database interface providing access to all CRUD operations"""
    
    def __init__(self, db_path: str = None):
        self.connection = DatabaseConnection(db_path)
        self.rs485_samples = RS485SampleCRUD(self.connection)
        self.adxl_batches = ADXLBatchCRUD(self.connection)
    
    def close(self):
        """Dispose engine (optional)."""
        try:
            self.connection.engine.dispose()
        except Exception:
            pass


__all__ = [
    'Database',
    'DatabaseConnection',
    'RS485Sample',
    'ADXLBatch',
    'RS485SampleCRUD',
    'ADXLBatchCRUD'
]
