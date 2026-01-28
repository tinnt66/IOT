from __future__ import annotations

import queue
import threading
import time
from datetime import datetime

from database.models import ADXLBatch as DB_ADXLBatch
from database.models import RS485Sample as DB_RS485Sample

from ..services.db import get_database


DB_WRITE_QUEUE_MAXSIZE = 50000
DB_COMMIT_INTERVAL_S = 1.0
DB_MAX_BATCH_ITEMS = 5000

_db_write_queue: queue.Queue = queue.Queue(maxsize=DB_WRITE_QUEUE_MAXSIZE)
_db_writer_started = False
_db_writer_lock = threading.Lock()
_db_writer_stop = threading.Event()

_metrics_lock = threading.Lock()
_metrics = {
    "enqueued_rs485": 0,
    "enqueued_adxl_batch": 0,
    "dropped_rs485": 0,
    "dropped_adxl_batch": 0,
    "inserted_rs485": 0,
    "inserted_adxl_batch": 0,
    "last_commit_iso": None,
}


def get_metrics_snapshot() -> dict:
    with _metrics_lock:
        out = dict(_metrics)
    out.update(
        {
            "db_writer_started": _db_writer_started,
            "db_queue_size": _db_write_queue.qsize(),
            "db_queue_max": DB_WRITE_QUEUE_MAXSIZE,
        }
    )
    return out


def stop() -> None:
    _db_writer_stop.set()


def start_once() -> None:
    global _db_writer_started
    if _db_writer_started:
        return
    with _db_writer_lock:
        if _db_writer_started:
            return
        _db_writer_started = True
        t = threading.Thread(target=_db_writer_loop, name="sqlite-writer", daemon=True)
        t.start()


def enqueue_rs485(sample: DB_RS485Sample) -> bool:
    try:
        _db_write_queue.put_nowait({"type": "rs485", "payload": sample})
        with _metrics_lock:
            _metrics["enqueued_rs485"] += 1
        return True
    except queue.Full:
        with _metrics_lock:
            _metrics["dropped_rs485"] += 1
        return False


def enqueue_adxl_batch(batch: DB_ADXLBatch) -> bool:
    try:
        _db_write_queue.put_nowait({"type": "adxl_batch", "payload": batch})
        with _metrics_lock:
            _metrics["enqueued_adxl_batch"] += 1
        return True
    except queue.Full:
        with _metrics_lock:
            _metrics["dropped_adxl_batch"] += 1
        return False


def _db_writer_loop() -> None:
    db = get_database()
    rs485_buf: list[DB_RS485Sample] = []
    adxl_buf: list[DB_ADXLBatch] = []
    last_commit = time.monotonic()

    def flush() -> None:
        nonlocal last_commit
        if not rs485_buf and not adxl_buf:
            return
        try:
            with db.connection.get_session() as s:
                if rs485_buf:
                    s.add_all(rs485_buf)
                if adxl_buf:
                    s.add_all(adxl_buf)
                # commit happens in context manager
            with _metrics_lock:
                _metrics["inserted_rs485"] += len(rs485_buf)
                _metrics["inserted_adxl_batch"] += len(adxl_buf)
                _metrics["last_commit_iso"] = datetime.now().isoformat()
        except Exception:
            pass
        finally:
            rs485_buf.clear()
            adxl_buf.clear()
            last_commit = time.monotonic()

    while not _db_writer_stop.is_set():
        now = time.monotonic()
        if (rs485_buf or adxl_buf) and (now - last_commit) >= DB_COMMIT_INTERVAL_S:
            flush()
            continue

        try:
            item = _db_write_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        drained = [item]
        for _ in range(512):
            try:
                drained.append(_db_write_queue.get_nowait())
            except queue.Empty:
                break

        try:
            for it in drained:
                item_type = it.get("type")
                payload = it.get("payload")

                if item_type == "rs485":
                    rs485_buf.append(payload)
                elif item_type == "adxl_batch":
                    adxl_buf.append(payload)

            if (len(rs485_buf) + len(adxl_buf)) >= DB_MAX_BATCH_ITEMS:
                flush()
        finally:
            for _ in drained:
                _db_write_queue.task_done()

        time.sleep(0.001)

    flush()
