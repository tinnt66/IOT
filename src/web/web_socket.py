from __future__ import annotations

from datetime import datetime

from flask_socketio import emit

from .extensions import socketio
from .services.db import get_database


def register_handlers() -> None:
    @socketio.on("connect")
    def handle_connect():
        emit(
            "connection_response",
            {"status": "connected", "message": "Welcome to IoT Dashboard", "timestamp": datetime.now().isoformat()},
        )

    @socketio.on("disconnect")
    def handle_disconnect():
        return

    @socketio.on("request_stats")
    def handle_stats_request():
        try:
            db = get_database()
            emit(
                "stats_update",
                {
                    "rs485_count": db.rs485_samples.count(),
                    "adxl_count": db.adxl_batches.count(),
                    "timestamp": datetime.now().isoformat(),
                },
            )
        except Exception as e:
            emit("error", {"message": str(e)})

