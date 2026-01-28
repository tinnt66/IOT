"""
FastAPI REST API Server for IoT Sensor Data
Receives data from Raspberry Pi sensors and stores in SQLite database
"""

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rest_api.config import settings
from rest_api.routes import ingest_router


# Create FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(ingest_router, tags=["Data Ingestion"])


@app.get("/")
async def root():
    """Root endpoint - API information"""
    return {
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "ingest": "POST /ingest",
            "health": "GET /health"
        }
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal server error",
            "detail": str(exc)
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  {settings.api_title:<54}  ║
    ║  Version: {settings.api_version:<47}  ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Server: http://{settings.api_host}:{settings.api_port:<39}  ║
    ║  Docs:   http://{settings.api_host}:{settings.api_port}/docs{' ' * 33}  ║
    ║  ReDoc:  http://{settings.api_host}:{settings.api_port}/redoc{' ' * 32}  ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload
    )

