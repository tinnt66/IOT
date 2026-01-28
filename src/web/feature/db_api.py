from __future__ import annotations

import csv
from io import BytesIO, StringIO
from typing import Any, List, Optional

from flask import Blueprint, Response, jsonify, request

from ..flows import db_writer
from ..services.db import get_database


bp = Blueprint("feature_db_api", __name__)


def _clamp_int(value: Optional[str], default: int, min_value: int, max_value: int) -> int:
    try:
        n = int(value) if value is not None else default
    except Exception:
        n = default
    return max(min_value, min(max_value, n))


def _get_range_args():
    start = request.args.get("start") or None
    end = request.args.get("end") or None
    return start, end


def _query_rs485(start: Optional[str], end: Optional[str], limit: int, offset: int):
    db = get_database()
    items = db.rs485_samples.get_by_created_at_range(start=start, end=end, limit=limit, offset=offset)
    return [it.to_dict() for it in items]


def _query_adxl(start: Optional[str], end: Optional[str], limit: int, offset: int):
    db = get_database()
    batches = db.adxl_batches.get_by_created_at_range(start=start, end=end, limit=limit, offset=offset)

    items = []
    for b in batches:
        sample_obj = b.samples if isinstance(b.samples, dict) else {}
        data = sample_obj.get("data") if isinstance(sample_obj, dict) else None
        items.append(
            {
                "id": b.id,
                "chunk_start_us": b.chunk_start_us,
                "fs_hz": sample_obj.get("fs_hz") if isinstance(sample_obj, dict) else None,
                "sample_count": len(data) if isinstance(data, list) else None,
                "created_at": b.created_at,
            }
        )
    return items


@bp.get("/api/db/rs485")
def api_db_rs485():
    start, end = _get_range_args()
    limit = _clamp_int(request.args.get("limit"), default=200, min_value=1, max_value=1000)
    offset = _clamp_int(request.args.get("offset"), default=0, min_value=0, max_value=1_000_000_000)
    items = _query_rs485(start, end, limit=limit, offset=offset)
    return jsonify({"items": items})


@bp.get("/api/db/adxl")
def api_db_adxl():
    start, end = _get_range_args()
    limit = _clamp_int(request.args.get("limit"), default=200, min_value=1, max_value=1000)
    offset = _clamp_int(request.args.get("offset"), default=0, min_value=0, max_value=1_000_000_000)
    items = _query_adxl(start, end, limit=limit, offset=offset)
    return jsonify({"items": items})


@bp.get("/api/metrics")
def api_metrics():
    metrics = {}
    metrics.update(db_writer.get_metrics_snapshot())
    return jsonify(metrics)


@bp.get("/api/export/rs485.csv")
def export_rs485_csv():
    start, end = _get_range_args()
    items = _query_rs485(start, end, limit=1000, offset=0)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["id", "time_local", "temp_c", "hum_pct", "wind_dir_deg", "wind_dir_txt", "wind_spd_ms", "created_at"]
    )
    for d in items:
        writer.writerow(
            [
                d.get("id"),
                d.get("time_local"),
                d.get("temp_c"),
                d.get("hum_pct"),
                d.get("wind_dir_deg"),
                d.get("wind_dir_txt"),
                d.get("wind_spd_ms"),
                d.get("created_at"),
            ]
        )

    resp = Response(buf.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = 'attachment; filename="rs485.csv"'
    return resp


@bp.get("/api/export/adxl.csv")
def export_adxl_csv():
    start, end = _get_range_args()
    items = _query_adxl(start, end, limit=1000, offset=0)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "chunk_start_us", "fs_hz", "sample_count", "created_at"])
    for d in items:
        writer.writerow([d.get("id"), d.get("chunk_start_us"), d.get("fs_hz"), d.get("sample_count"), d.get("created_at")])

    resp = Response(buf.getvalue(), mimetype="text/csv; charset=utf-8")
    resp.headers["Content-Disposition"] = 'attachment; filename="adxl.csv"'
    return resp


def _xlsx_response(filename: str, headers: List[str], rows: List[List[Any]]):
    try:
        from openpyxl import Workbook
    except Exception:
        return jsonify({"status": "error", "message": "Excel export requires openpyxl. Install it and restart the server."}), 500

    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    resp = Response(out.getvalue(), mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp


@bp.get("/api/export/rs485.xlsx")
def export_rs485_xlsx():
    start, end = _get_range_args()
    items = _query_rs485(start, end, limit=1000, offset=0)
    rows = [
        [
            d.get("id"),
            d.get("time_local"),
            d.get("temp_c"),
            d.get("hum_pct"),
            d.get("wind_dir_deg"),
            d.get("wind_dir_txt"),
            d.get("wind_spd_ms"),
            d.get("created_at"),
        ]
        for d in items
    ]
    return _xlsx_response(
        filename="rs485.xlsx",
        headers=["id", "time_local", "temp_c", "hum_pct", "wind_dir_deg", "wind_dir_txt", "wind_spd_ms", "created_at"],
        rows=rows,
    )


@bp.get("/api/export/adxl.xlsx")
def export_adxl_xlsx():
    start, end = _get_range_args()
    items = _query_adxl(start, end, limit=1000, offset=0)
    rows = [[d.get("id"), d.get("chunk_start_us"), d.get("fs_hz"), d.get("sample_count"), d.get("created_at")] for d in items]
    return _xlsx_response(filename="adxl.xlsx", headers=["id", "chunk_start_us", "fs_hz", "sample_count", "created_at"], rows=rows)
