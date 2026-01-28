"""
Flask Application with SocketIO for Real-time IoT Dashboard
"""

import sys
import logging
import threading
import queue
import csv
import json
import atexit
import sqlite3
import time
from collections import deque
from io import StringIO, BytesIO
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, render_template, Response
from typing import Optional, List, Any
from flask_cors import CORS
from flask_socketio import SocketIO, emit

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from database import Database
from database.models import RS485Sample as DB_RS485Sample, ADXLBatch as DB_ADXLBatch

# Import config and middleware (handle both cases)
try:
    from rest_api.config import settings
    from rest_api.middleware import verify_api_key
except ImportError:
    # When running app.py directly
    from config import settings
    from middleware import verify_api_key


# Initialize Flask app
app = Flask(__name__, 
            static_folder='static',
            template_folder='templates')

app.config['SECRET_KEY'] = settings.api_key

# Enable CORS
CORS(app, resources={r"/*": {"origins": settings.allow_origins}})

# Silence Werkzeug request logs (127.0.0.1 - - [...]) unless errors
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Initialize SocketIO (silence socket.io/engine.io logs)
socketio = SocketIO(
    app,
    cors_allowed_origins=settings.allow_origins,
    logger=False,
    engineio_logger=False,
)


# Database instance
def get_database():
    """Get database instance"""
    global _DB_SINGLETON
    if _DB_SINGLETON is None:
        with _DB_SINGLETON_LOCK:
            if _DB_SINGLETON is None:
                db_path = Path(__file__).parent.parent / settings.db_path
                _DB_SINGLETON = Database(db_path=str(db_path))
    return _DB_SINGLETON


_DB_SINGLETON = None
_DB_SINGLETON_LOCK = threading.Lock()


_DB_WRITE_QUEUE_MAXSIZE = 50000
_db_write_queue: queue.Queue = queue.Queue(maxsize=_DB_WRITE_QUEUE_MAXSIZE)
_db_writer_started = False
_db_writer_lock = threading.Lock()
_db_writer_stop = threading.Event()
_db_metrics_lock = threading.Lock()
_db_metrics = {
    'enqueued_rs485': 0,
    'enqueued_adxl_batch': 0,
    'dropped_rs485': 0,
    'dropped_adxl_batch': 0,
    'inserted_rs485': 0,
    'inserted_adxl_batch': 0,
    'last_commit_iso': None,
}


_ADXL_UI_BUFFER_MAXLEN = 3000
_ADXL_UI_EMIT_INTERVAL_S = 0.10
_ADXL_UI_EMIT_MAX_SAMPLES = 500
_adxl_ui_pending = deque(maxlen=_ADXL_UI_BUFFER_MAXLEN)
_adxl_ui_lock = threading.Lock()
_adxl_ui_meta = {
    'device_id': None,
    'timestamp': None,
    'chunk_start_us': None,
    'sample_count': None,
    'fs_hz': None,
    'adxl1': None,
    'adxl2': None,
    'adxl3': None,
}
_adxl_emitter_started = False
_adxl_emitter_lock = threading.Lock()
_adxl_emitter_stop = threading.Event()


def _db_writer_loop():
    db = get_database()
    conn = sqlite3.connect(db.connection.db_path, timeout=30)
    try:
        cur = conn.cursor()
        try:
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA synchronous=NORMAL")
        except Exception:
            pass

        rs485_sql = """
            INSERT INTO rs485_samples
            (time_local, temp_c, hum_pct, wind_dir_deg, wind_dir_txt, wind_spd_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """

        adxl_sql = """
            INSERT INTO adxl_batches
            (chunk_start_us, samples, created_at)
            VALUES (?, ?, ?)
        """

        rs485_buf: list[tuple] = []
        adxl_buf: list[tuple] = []
        last_commit = time.monotonic()

        def flush():
            nonlocal last_commit
            if not rs485_buf and not adxl_buf:
                return
            try:
                if rs485_buf:
                    cur.executemany(rs485_sql, rs485_buf)
                if adxl_buf:
                    cur.executemany(adxl_sql, adxl_buf)
                conn.commit()
                with _db_metrics_lock:
                    _db_metrics['inserted_rs485'] += len(rs485_buf)
                    _db_metrics['inserted_adxl_batch'] += len(adxl_buf)
                    _db_metrics['last_commit_iso'] = datetime.now().isoformat()
            except Exception:
                try:
                    conn.rollback()
                except Exception:
                    pass
            finally:
                rs485_buf.clear()
                adxl_buf.clear()
                last_commit = time.monotonic()

        while not _db_writer_stop.is_set():
            try:
                item = _db_write_queue.get(timeout=0.25)
            except queue.Empty:
                flush()
                continue

            drained = [item]
            for _ in range(256):
                try:
                    drained.append(_db_write_queue.get_nowait())
                except queue.Empty:
                    break

            try:
                for it in drained:
                    item_type = it.get('type')
                    payload = it.get('payload')

                    if item_type == 'rs485':
                        rs485_buf.append((
                            payload.time_local,
                            payload.temp_c,
                            payload.hum_pct,
                            payload.wind_dir_deg,
                            payload.wind_dir_txt,
                            payload.wind_spd_ms,
                            payload.created_at,
                        ))
                    elif item_type == 'adxl_batch':
                        adxl_buf.append((
                            payload.chunk_start_us,
                            json.dumps(payload.samples),
                            payload.created_at,
                        ))

                now = time.monotonic()
                if (len(rs485_buf) + len(adxl_buf)) >= 500 or (now - last_commit) >= 0.5:
                    flush()
            finally:
                for _ in drained:
                    _db_write_queue.task_done()

            # Yield CPU to prioritize realtime/websocket processing
            time.sleep(0.002)

        flush()
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _start_db_writer_once():
    global _db_writer_started
    if _db_writer_started:
        return
    with _db_writer_lock:
        if _db_writer_started:
            return
        _db_writer_started = True
        t = threading.Thread(target=_db_writer_loop, name='sqlite-writer', daemon=True)
        t.start()


atexit.register(_db_writer_stop.set)
atexit.register(_adxl_emitter_stop.set)


def _adxl_emitter_loop():
    last_emit = 0.0
    while not _adxl_emitter_stop.is_set():
        time.sleep(_ADXL_UI_EMIT_INTERVAL_S)
        if _adxl_emitter_stop.is_set():
            break

        now = time.monotonic()
        if now - last_emit < _ADXL_UI_EMIT_INTERVAL_S:
            continue

        samples_chunk = []
        meta_snapshot = None
        with _adxl_ui_lock:
            if not _adxl_ui_pending:
                continue

            for _ in range(min(_ADXL_UI_EMIT_MAX_SAMPLES, len(_adxl_ui_pending))):
                try:
                    samples_chunk.append(_adxl_ui_pending.popleft())
                except IndexError:
                    break

            meta_snapshot = dict(_adxl_ui_meta)

        if not samples_chunk:
            continue

        try:
            socketio.emit('adxl_data', {
                **meta_snapshot,
                'id': None,
                'samples': samples_chunk,
            }, namespace='/')
        except Exception:
            pass
        else:
            with _db_metrics_lock:
                _db_metrics['ws_adxl_emits'] = (_db_metrics.get('ws_adxl_emits') or 0) + 1
                _db_metrics['ws_adxl_samples_sent'] = (_db_metrics.get('ws_adxl_samples_sent') or 0) + len(samples_chunk)

        last_emit = now


def _start_adxl_emitter_once():
    global _adxl_emitter_started
    if _adxl_emitter_started:
        return
    with _adxl_emitter_lock:
        if _adxl_emitter_started:
            return
        _adxl_emitter_started = True
        t = threading.Thread(target=_adxl_emitter_loop, name='adxl-ui-emitter', daemon=True)
        t.start()


@app.before_request
def _ensure_db_writer_started():
    _start_db_writer_once()
    _start_adxl_emitter_once()


# ============================================================================
# WEB ROUTES
# ============================================================================

@app.route('/')
def index():
    """Serve the real-time dashboard"""
    return render_template('index.html')


@app.route('/api')
def api_info():
    """API information"""
    return jsonify({
        "service": settings.api_title,
        "version": settings.api_version,
        "status": "running",
        "endpoints": {
            "dashboard": "GET /",
            "api_info": "GET /api",
            "ingest": "POST /ingest",
            "health": "GET /health"
        }
    })


@app.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        db = get_database()
        rs485_count = db.rs485_samples.count()
        adxl_count = db.adxl_batches.count()
        
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "stats": {
                "rs485_samples": rs485_count,
                "adxl_batches": adxl_count
            }
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 503


# ============================================================================
# DATABASE QUERY + EXPORT ROUTES
# ============================================================================


def _clamp_int(value: Optional[str], default: int, min_value: int, max_value: int) -> int:
    try:
        n = int(value) if value is not None else default
    except Exception:
        n = default
    return max(min_value, min(max_value, n))


def _get_range_args():
    start = request.args.get('start') or None
    end = request.args.get('end') or None
    return start, end


def _query_rs485(start: Optional[str], end: Optional[str], limit: int, offset: int):
    db = get_database()
    sql = "SELECT * FROM rs485_samples"
    where = []
    params = []
    if start:
        where.append("datetime(created_at) >= datetime(?)")
        params.append(start)
    if end:
        where.append("datetime(created_at) <= datetime(?)")
        params.append(end)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with db.connection.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]


def _query_adxl(start: Optional[str], end: Optional[str], limit: int, offset: int):
    db = get_database()
    sql = "SELECT id, chunk_start_us, samples, created_at FROM adxl_batches"
    where = []
    params = []
    if start:
        where.append("datetime(created_at) >= datetime(?)")
        params.append(start)
    if end:
        where.append("datetime(created_at) <= datetime(?)")
        params.append(end)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    items = []
    with db.connection.get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        for row in cur.fetchall():
            try:
                sample_obj = json.loads(row['samples']) if row['samples'] else {}
            except Exception:
                sample_obj = {}

            data = sample_obj.get('data') if isinstance(sample_obj, dict) else None
            items.append({
                'id': row['id'],
                'chunk_start_us': row['chunk_start_us'],
                'fs_hz': sample_obj.get('fs_hz') if isinstance(sample_obj, dict) else None,
                'sample_count': len(data) if isinstance(data, list) else None,
                'created_at': row['created_at'],
            })

    return items


@app.route('/api/db/rs485')
def api_db_rs485():
    start, end = _get_range_args()
    limit = _clamp_int(request.args.get('limit'), default=200, min_value=1, max_value=1000)
    offset = _clamp_int(request.args.get('offset'), default=0, min_value=0, max_value=1_000_000_000)
    items = _query_rs485(start, end, limit=limit, offset=offset)
    return jsonify({'items': items})


@app.route('/api/db/adxl')
def api_db_adxl():
    start, end = _get_range_args()
    limit = _clamp_int(request.args.get('limit'), default=200, min_value=1, max_value=1000)
    offset = _clamp_int(request.args.get('offset'), default=0, min_value=0, max_value=1_000_000_000)
    items = _query_adxl(start, end, limit=limit, offset=offset)
    return jsonify({'items': items})


@app.route('/api/metrics')
def api_metrics():
    with _db_metrics_lock:
        metrics = dict(_db_metrics)
    metrics.update({
        'db_writer_started': _db_writer_started,
        'db_queue_size': _db_write_queue.qsize(),
        'db_queue_max': _DB_WRITE_QUEUE_MAXSIZE,
        'adxl_emitter_started': _adxl_emitter_started,
        'adxl_ui_pending': len(_adxl_ui_pending),
        'adxl_ui_emit_interval_s': _ADXL_UI_EMIT_INTERVAL_S,
        'adxl_ui_emit_max_samples': _ADXL_UI_EMIT_MAX_SAMPLES,
    })
    return jsonify(metrics)


@app.route('/api/export/rs485.csv')
def export_rs485_csv():
    start, end = _get_range_args()
    items = _query_rs485(start, end, limit=1000, offset=0)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(['id', 'time_local', 'temp_c', 'hum_pct', 'wind_dir_deg', 'wind_dir_txt', 'wind_spd_ms', 'created_at'])
    for d in items:
        writer.writerow([
            d.get('id'),
            d.get('time_local'),
            d.get('temp_c'),
            d.get('hum_pct'),
            d.get('wind_dir_deg'),
            d.get('wind_dir_txt'),
            d.get('wind_spd_ms'),
            d.get('created_at'),
        ])

    resp = Response(buf.getvalue(), mimetype='text/csv; charset=utf-8')
    resp.headers['Content-Disposition'] = 'attachment; filename="rs485.csv"'
    return resp


@app.route('/api/export/adxl.csv')
def export_adxl_csv():
    start, end = _get_range_args()
    items = _query_adxl(start, end, limit=1000, offset=0)

    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(['id', 'chunk_start_us', 'fs_hz', 'sample_count', 'created_at'])
    for d in items:
        writer.writerow([
            d.get('id'),
            d.get('chunk_start_us'),
            d.get('fs_hz'),
            d.get('sample_count'),
            d.get('created_at'),
        ])

    resp = Response(buf.getvalue(), mimetype='text/csv; charset=utf-8')
    resp.headers['Content-Disposition'] = 'attachment; filename="adxl.csv"'
    return resp


def _xlsx_response(filename: str, headers: List[str], rows: List[List[Any]]):
    try:
        from openpyxl import Workbook
    except Exception:
        return jsonify({
            "status": "error",
            "message": "Excel export requires openpyxl. Install it and restart the server."
        }), 500

    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    resp = Response(out.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    resp.headers['Content-Disposition'] = f'attachment; filename=\"{filename}\"'
    return resp


@app.route('/api/export/rs485.xlsx')
def export_rs485_xlsx():
    start, end = _get_range_args()
    items = _query_rs485(start, end, limit=1000, offset=0)
    rows = [
        [
            d.get('id'),
            d.get('time_local'),
            d.get('temp_c'),
            d.get('hum_pct'),
            d.get('wind_dir_deg'),
            d.get('wind_dir_txt'),
            d.get('wind_spd_ms'),
            d.get('created_at'),
        ]
        for d in items
    ]
    return _xlsx_response(
        filename='rs485.xlsx',
        headers=['id', 'time_local', 'temp_c', 'hum_pct', 'wind_dir_deg', 'wind_dir_txt', 'wind_spd_ms', 'created_at'],
        rows=rows,
    )


@app.route('/api/export/adxl.xlsx')
def export_adxl_xlsx():
    start, end = _get_range_args()
    items = _query_adxl(start, end, limit=1000, offset=0)
    rows = [
        [d.get('id'), d.get('chunk_start_us'), d.get('fs_hz'), d.get('sample_count'), d.get('created_at')]
        for d in items
    ]
    return _xlsx_response(
        filename='adxl.xlsx',
        headers=['id', 'chunk_start_us', 'fs_hz', 'sample_count', 'created_at'],
        rows=rows,
    )


# ============================================================================
# API ROUTES
# ============================================================================

@app.route('/ingest', methods=['POST'])
def ingest_data():
    """
    Ingest sensor data from IoT devices
    Stores in database and broadcasts to connected clients via WebSocket
    """
    # Verify API key
    api_key = request.headers.get('X-API-Key')
    if not verify_api_key(api_key):
        return jsonify({
            "status": "error",
            "message": "Invalid API Key"
        }), 401
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No data provided"
            }), 400
        
        device_id = data.get('device_id')
        data_type = data.get('type')
        timestamp = data.get('ts')
        
        records_created = 0
        
        # Handle RS485 data
        if data_type == 'rs485':
            sample_data = data.get('sample', {})
            
            db_sample = DB_RS485Sample(
                time_local=sample_data.get('time_local'),
                temp_c=sample_data.get('temp_c'),
                hum_pct=sample_data.get('hum_pct'),
                wind_dir_deg=sample_data.get('wind_dir_deg'),
                wind_dir_txt=sample_data.get('wind_dir_txt'),
                wind_spd_ms=sample_data.get('wind_spd_ms'),
                created_at=datetime.now().isoformat()
            )

            queued = True
            try:
                _db_write_queue.put_nowait({'type': 'rs485', 'payload': db_sample})
                records_created = 1
                with _db_metrics_lock:
                    _db_metrics['enqueued_rs485'] += 1
            except queue.Full:
                queued = False
                with _db_metrics_lock:
                    _db_metrics['dropped_rs485'] += 1
            
            # Broadcast to WebSocket clients
            socketio.emit('rs485_data', {
                'device_id': device_id,
                'timestamp': timestamp,
                'data': sample_data,
                'id': None
            }, namespace='/')
            
            return jsonify({
                "status": "success",
                "message": "RS485 sample queued for storage" if queued else "RS485 storage queue is full (dropped from DB)",
                "db_queued": queued,
                "device_id": device_id,
                "timestamp": timestamp,
                "records_created": records_created
            })
        
        # Handle ADXL batch data
        elif data_type == 'adxl_batch':
            chunk_start_us = data.get('chunk_start_us')
            samples = data.get('samples', [])
            fs_hz = data.get('fs_hz', 500)
            samples_for_ui = samples[-1500:] if isinstance(samples, list) else []
            
            db_batch = DB_ADXLBatch(
                chunk_start_us=chunk_start_us,
                samples={
                    "fs_hz": fs_hz,
                    "data": samples
                },
                created_at=datetime.now().isoformat()
            )

            queued = True
            try:
                _db_write_queue.put_nowait({'type': 'adxl_batch', 'payload': db_batch})
                records_created = len(samples)
                with _db_metrics_lock:
                    _db_metrics['enqueued_adxl_batch'] += 1
            except queue.Full:
                queued = False
                with _db_metrics_lock:
                    _db_metrics['dropped_adxl_batch'] += 1
            
            # Extract latest values for each ADXL sensor (Z-axis)
            # samples format: [[z1, z2, z3], [z1, z2, z3], ...]
            adxl1_value = samples[-1][0] if samples and len(samples[-1]) > 0 else None
            adxl2_value = samples[-1][1] if samples and len(samples[-1]) > 1 else None
            adxl3_value = samples[-1][2] if samples and len(samples[-1]) > 2 else None

            # Queue samples for UI emission (best-effort, throttled)
            with _adxl_ui_lock:
                _adxl_ui_pending.extend(samples_for_ui)
                _adxl_ui_meta.update({
                    'device_id': device_id,
                    'timestamp': timestamp,
                    'chunk_start_us': chunk_start_us,
                    'sample_count': records_created,
                    'fs_hz': fs_hz,
                    'adxl1': adxl1_value,
                    'adxl2': adxl2_value,
                    'adxl3': adxl3_value,
                })
            
            return jsonify({
                "status": "success",
                "message": f"ADXL batch queued for storage ({records_created} samples)" if queued else "ADXL storage queue is full (dropped from DB)",
                "db_queued": queued,
                "device_id": device_id,
                "timestamp": timestamp,
                "records_created": records_created
            })
        
        else:
            return jsonify({
                "status": "error",
                "message": f"Unknown data type: {data_type}"
            }), 400
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to store data: {str(e)}"
        }), 500


# ============================================================================
# WEBSOCKET EVENTS
# ============================================================================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connection_response', {
        'status': 'connected',
        'message': 'Welcome to IoT Dashboard',
        'timestamp': datetime.now().isoformat()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    return


@socketio.on('request_stats')
def handle_stats_request():
    """Send current statistics to client"""
    try:
        db = get_database()
        emit('stats_update', {
            'rs485_count': db.rs485_samples.count(),
            'adxl_count': db.adxl_batches.count(),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        emit('error', {'message': str(e)})


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(e):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "message": "Resource not found"
    }), 404


@app.errorhandler(500)
def internal_error(e):
    """Handle 500 errors"""
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "detail": str(e)
    }), 500


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print(f"""
    ╔══════════════════════════════════════════════════════════╗
    ║  {settings.api_title:<54}  ║
    ║  Version: {settings.api_version:<47}  ║
    ╠══════════════════════════════════════════════════════════╣
    ║  Dashboard: http://{settings.api_host}:{settings.api_port}/{' ' * 31}  ║
    ║  API Info:  http://{settings.api_host}:{settings.api_port}/api{' ' * 27}  ║
    ║  Health:    http://{settings.api_host}:{settings.api_port}/health{' ' * 24}  ║
    ╠══════════════════════════════════════════════════════════╣
    ║  WebSocket: Enabled (Real-time updates){' ' * 19}  ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    
    socketio.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        debug=settings.api_reload,
        allow_unsafe_werkzeug=True  # For development only
    )
