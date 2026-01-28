from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, render_template

from .config import settings
from .services.db import get_database


bp = Blueprint("web_routes", __name__)


@bp.get("/")
def index():
    return render_template("realtime.html", active_page="realtime", title="Sensor Dashboard")


@bp.get("/realtime")
def realtime():
    return render_template("realtime.html", active_page="realtime", title="Realtime Data")


@bp.get("/database")
def database():
    return render_template("database.html", active_page="database", title="Database")


@bp.get("/api")
def api_info():
    return jsonify(
        {
            "service": settings.api_title,
            "version": settings.api_version,
            "status": "running",
            "endpoints": {
                "dashboard": "GET /",
                "api_info": "GET /api",
                "ingest": "POST /ingest",
                "health": "GET /health",
            },
        }
    )


@bp.get("/health")
def health_check():
    try:
        db = get_database()
        rs485_count = db.rs485_samples.count()
        adxl_count = db.adxl_batches.count()

        return jsonify(
            {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "stats": {
                    "rs485_samples": rs485_count,
                    "adxl_batches": adxl_count,
                },
            }
        )
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503
