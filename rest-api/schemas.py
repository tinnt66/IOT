"""
Pydantic Models for Request/Response Validation
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class RS485Sample(BaseModel):
    """RS485 sensor reading data"""
    time_local: str
    temp_c: Optional[float] = None
    hum_pct: Optional[float] = None
    wind_dir_deg: Optional[int] = None
    wind_dir_txt: Optional[str] = None
    wind_spd_ms: Optional[float] = None


class ADXLBatchRequest(BaseModel):
    """ADXL accelerometer batch data"""
    device_id: str
    ts: str
    type: str = "adxl_batch"
    fs_hz: int = Field(default=500, description="Sampling frequency in Hz")
    chunk_start_us: int = Field(description="Chunk start timestamp in microseconds")
    samples: List[List[int]] = Field(description="Array of [z1, z2, z3] samples")


class RS485Request(BaseModel):
    """RS485 sensor data request"""
    device_id: str
    ts: str
    type: str = "rs485"
    sample: RS485Sample


class IngestResponse(BaseModel):
    """Response for ingest endpoint"""
    status: str
    message: str
    device_id: str
    timestamp: str
    records_created: Optional[int] = None


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    database: str
