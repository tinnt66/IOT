"""
Data Ingestion Endpoint
Receives sensor data from IoT devices
"""

import sys
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Union

# Add parent directory to path to import database module
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from database import Database
from database.models import RS485Sample as DB_RS485Sample, ADXLBatch as DB_ADXLBatch
from rest_api.schemas import RS485Request, ADXLBatchRequest, IngestResponse
from rest_api.middleware import verify_api_key
from rest_api.config import settings


router = APIRouter()


def get_database():
    """Dependency to get database instance"""
    # Use absolute path from project root
    db_path = Path(__file__).parent.parent.parent / settings.db_path
    return Database(db_path=str(db_path))



@router.post("/ingest", response_model=IngestResponse)
async def ingest_data(
    request: Union[RS485Request, ADXLBatchRequest],
    api_key: str = Depends(verify_api_key),
    db: Database = Depends(get_database)
):
    """
    Ingest sensor data from IoT devices
    
    Accepts two types of data:
    - RS485: Temperature, humidity, wind sensors (1 sample/request)
    - ADXL Batch: Accelerometer data (batch of samples)
    
    Headers:
        X-API-Key: API authentication key
        
    Body:
        device_id: Device identifier
        ts: ISO timestamp
        type: "rs485" or "adxl_batch"
        sample (for RS485): Sensor readings
        samples (for ADXL): Batch of accelerometer readings
    """
    try:
        records_created = 0
        
        # Handle RS485 data
        if isinstance(request, RS485Request) or request.type == "rs485":
            sample_data = request.sample if hasattr(request, 'sample') else request.dict().get('sample', {})
            
            # Create database model
            db_sample = DB_RS485Sample(
                time_local=sample_data.get('time_local'),
                temp_c=sample_data.get('temp_c'),
                hum_pct=sample_data.get('hum_pct'),
                wind_dir_deg=sample_data.get('wind_dir_deg'),
                wind_dir_txt=sample_data.get('wind_dir_txt'),
                wind_spd_ms=sample_data.get('wind_spd_ms'),
                created_at=datetime.now().isoformat()
            )
            
            # Insert into database
            sample_id = db.rs485_samples.create(db_sample)
            records_created = 1
            
            return IngestResponse(
                status="success",
                message=f"RS485 sample stored with ID {sample_id}",
                device_id=request.device_id,
                timestamp=request.ts,
                records_created=records_created
            )
        
        # Handle ADXL batch data
        elif isinstance(request, ADXLBatchRequest) or request.type == "adxl_batch":
            # Create database model
            db_batch = DB_ADXLBatch(
                chunk_start_us=request.chunk_start_us,
                samples={
                    "fs_hz": request.fs_hz,
                    "data": request.samples
                },
                created_at=datetime.now().isoformat()
            )
            
            # Insert into database
            batch_id = db.adxl_batches.create(db_batch)
            records_created = len(request.samples)
            
            return IngestResponse(
                status="success",
                message=f"ADXL batch stored with ID {batch_id}, {records_created} samples",
                device_id=request.device_id,
                timestamp=request.ts,
                records_created=records_created
            )
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown data type: {request.type}"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store data: {str(e)}"
        )


@router.get("/health")
async def health_check(db: Database = Depends(get_database)):
    """
    Health check endpoint
    
    Returns service status and database connectivity
    """
    try:
        # Test database connectivity
        rs485_count = db.rs485_samples.count()
        adxl_count = db.adxl_batches.count()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "stats": {
                "rs485_samples": rs485_count,
                "adxl_batches": adxl_count
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error: {str(e)}"
        )
