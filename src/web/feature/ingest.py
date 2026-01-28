from __future__ import annotations

from datetime import datetime

from flask import Blueprint, jsonify, request

from database.models import ADXLBatch as DB_ADXLBatch
from database.models import RS485Sample as DB_RS485Sample

from ..extensions import socketio
from ..flows import db_writer
from ..middleware import verify_api_key


bp = Blueprint("feature_ingest", __name__)


@bp.post("/ingest")
def ingest_data():
    api_key = request.headers.get("X-API-Key")
    if not verify_api_key(api_key):
        return jsonify({"status": "error", "message": "Invalid API Key"}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        device_id = data.get("device_id")
        data_type = data.get("type")
        timestamp = data.get("ts")

        records_created = 0

        if data_type == "rs485":
            sample_data = data.get("sample", {})
            db_sample = DB_RS485Sample(
                time_local=sample_data.get("time_local") or datetime.now().isoformat(),
                temp_c=sample_data.get("temp_c"),
                hum_pct=sample_data.get("hum_pct"),
                wind_dir_deg=sample_data.get("wind_dir_deg"),
                wind_dir_txt=sample_data.get("wind_dir_txt"),
                wind_spd_ms=sample_data.get("wind_spd_ms"),
                created_at=datetime.now().isoformat(),
            )

            socketio.emit(
                "rs485_data",
                {"device_id": device_id, "timestamp": timestamp, "data": sample_data, "id": None},
                namespace="/",
            )

            queued = db_writer.enqueue_rs485(db_sample)
            records_created = 1 if queued else 0

            return jsonify(
                {
                    "status": "success",
                    "message": "RS485 sample queued for storage" if queued else "RS485 storage queue is full (dropped from DB)",
                    "db_queued": queued,
                    "device_id": device_id,
                    "timestamp": timestamp,
                    "records_created": records_created,
                }
            ), 202

        if data_type == "adxl_batch":
            chunk_start_us = data.get("chunk_start_us")
            samples = data.get("samples", [])
            fs_hz = data.get("fs_hz", 500)

            db_batch = DB_ADXLBatch(
                chunk_start_us=int(chunk_start_us or 0),
                samples={"fs_hz": fs_hz, "data": samples},
                created_at=datetime.now().isoformat(),
            )

            adxl1_value = samples[-1][0] if samples and len(samples[-1]) > 0 else None
            adxl2_value = samples[-1][1] if samples and len(samples[-1]) > 1 else None
            adxl3_value = samples[-1][2] if samples and len(samples[-1]) > 2 else None

            ws_samples = samples if isinstance(samples, list) else []
            # Keep WS payload bounded (UI only needs recent points for charts)
            max_ws_samples = 500
            if len(ws_samples) > max_ws_samples:
                ws_samples = ws_samples[-max_ws_samples:]

            socketio.emit(
                "adxl_data",
                {
                    "device_id": device_id,
                    "timestamp": timestamp,
                    "chunk_start_us": chunk_start_us,
                    "sample_count": len(samples) if isinstance(samples, list) else 0,
                    "fs_hz": fs_hz,
                    "adxl1": adxl1_value,
                    "adxl2": adxl2_value,
                    "adxl3": adxl3_value,
                    "id": None,
                    "samples": ws_samples,
                },
                namespace="/",
            )

            queued = db_writer.enqueue_adxl_batch(db_batch)
            records_created = len(samples) if queued else 0

            return jsonify(
                {
                    "status": "success",
                    "message": f"ADXL batch queued for storage ({records_created} samples)"
                    if queued
                    else "ADXL storage queue is full (dropped from DB)",
                    "db_queued": queued,
                    "device_id": device_id,
                    "timestamp": timestamp,
                    "records_created": records_created,
                }
            ), 202

        return jsonify({"status": "error", "message": f"Unknown data type: {data_type}"}), 400

    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to store data: {str(e)}"}), 500
