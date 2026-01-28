"""
Simulate IoT sensor POST requests to the server (/ingest).

No external dependencies (uses urllib from stdlib).
"""

from __future__ import annotations

import argparse
import json
import random
import time
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _iso_utc_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


_WIND_DIR_16 = [
    "N",
    "NNE",
    "NE",
    "ENE",
    "E",
    "ESE",
    "SE",
    "SSE",
    "S",
    "SSW",
    "SW",
    "WSW",
    "W",
    "WNW",
    "NW",
    "NNW",
]


def _wind_dir_txt(deg: int) -> str:
    deg = deg % 360
    idx = int((deg + 11.25) // 22.5) % 16
    return _WIND_DIR_16[idx]


def _post_json(url: str, api_key: str, payload: dict[str, Any], timeout_s: float) -> tuple[int, str]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = Request(
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        },
    )
    try:
        with urlopen(req, timeout=timeout_s) as resp:
            return int(resp.status), resp.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        return int(e.code), e.read().decode("utf-8", errors="replace")
    except URLError as e:
        return 0, f"URLError: {e}"


@dataclass(frozen=True)
class Ranges:
    temp_c_min: float
    temp_c_max: float
    hum_min: float
    hum_max: float
    wind_spd_min: float
    wind_spd_max: float
    adxl_min: int
    adxl_max: int


def _rs485_payload(device_id: str, now: datetime, ranges: Ranges) -> dict[str, Any]:
    wind_dir_deg = random.randint(0, 359)
    return {
        "device_id": device_id,
        "ts": _iso_utc_z(now),
        "type": "rs485",
        "sample": {
            "time_local": now.strftime("%Y-%m-%d %H:%M:%S"),
            "temp_c": round(random.uniform(ranges.temp_c_min, ranges.temp_c_max), 2),
            "hum_pct": round(random.uniform(ranges.hum_min, ranges.hum_max), 2),
            "wind_dir_deg": wind_dir_deg,
            "wind_dir_txt": _wind_dir_txt(wind_dir_deg),
            "wind_spd_ms": round(random.uniform(ranges.wind_spd_min, ranges.wind_spd_max), 2),
        },
    }


def _adxl_payload(device_id: str, now: datetime, fs_hz: int, sample_count: int, ranges: Ranges) -> dict[str, Any]:
    chunk_start_us = int(now.timestamp() * 1_000_000)
    samples = [
        [
            random.randint(ranges.adxl_min, ranges.adxl_max),
            random.randint(ranges.adxl_min, ranges.adxl_max),
            random.randint(ranges.adxl_min, ranges.adxl_max),
        ]
        for _ in range(sample_count)
    ]
    return {
        "device_id": device_id,
        "ts": _iso_utc_z(now),
        "type": "adxl_batch",
        "fs_hz": fs_hz,
        "chunk_start_us": chunk_start_us,
        "samples": samples,
    }


def _sleep_until(stop: threading.Event, target_t: float) -> None:
    while not stop.is_set():
        remaining = target_t - time.monotonic()
        if remaining <= 0:
            return
        stop.wait(timeout=min(0.25, remaining))


def main() -> int:
    p = argparse.ArgumentParser(description="Simulate random IoT sensor POST requests to /ingest.")
    p.add_argument("--url", default="http://127.0.0.1:8080/ingest", help="Ingest endpoint URL.")
    p.add_argument("--api-key", default="iotserver", help="API key (X-API-Key header).")
    p.add_argument("--device-id", default="sim-raspi-01", help="Device id to send.")
    p.add_argument("--mode", choices=["rs485", "adxl", "both"], default="both", help="Which payloads to send.")
    p.add_argument("--count", type=int, default=0, help="How many cycles to send (0 = run forever).")
    p.add_argument("--interval", type=float, default=1.0, help="Seconds between RS485 cycles (mode=rs485/both).")
    p.add_argument("--timeout", type=float, default=5.0, help="HTTP timeout seconds.")
    p.add_argument("--quiet", action="store_true", help="Disable per-request logging.")

    p.add_argument(
        "--adxl-every",
        type=int,
        default=1,
        help="Send ADXL batch every N ADXL intervals (mode=adxl/both).",
    )
    p.add_argument(
        "--adxl-batch-ms",
        type=float,
        default=100.0,
        help="ADXL batch duration in ms (used to pace ADXL in mode=adxl, and to size samples if --adxl-samples is omitted).",
    )
    p.add_argument("--adxl-samples", type=int, default=0, help="Samples per ADXL batch (0 = derive from fs_hz * batch_ms).")
    p.add_argument("--adxl-fs", type=int, default=500, help="ADXL sample rate (fs_hz).")

    p.add_argument("--temp-min", type=float, default=20.0)
    p.add_argument("--temp-max", type=float, default=35.0)
    p.add_argument("--hum-min", type=float, default=40.0)
    p.add_argument("--hum-max", type=float, default=90.0)
    p.add_argument("--wind-min", type=float, default=0.0)
    p.add_argument("--wind-max", type=float, default=15.0)
    p.add_argument("--adxl-min", type=int, default=-1000)
    p.add_argument("--adxl-max", type=int, default=1000)

    args = p.parse_args()

    if args.adxl_every < 1:
        print("--adxl-every must be >= 1")
        return 2
    if args.adxl_batch_ms <= 0:
        print("--adxl-batch-ms must be > 0")
        return 2
    if args.adxl_samples < 0:
        print("--adxl-samples must be >= 0")
        return 2

    ranges = Ranges(
        temp_c_min=min(args.temp_min, args.temp_max),
        temp_c_max=max(args.temp_min, args.temp_max),
        hum_min=min(args.hum_min, args.hum_max),
        hum_max=max(args.hum_min, args.hum_max),
        wind_spd_min=min(args.wind_min, args.wind_max),
        wind_spd_max=max(args.wind_min, args.wind_max),
        adxl_min=min(args.adxl_min, args.adxl_max),
        adxl_max=max(args.adxl_min, args.adxl_max),
    )

    adxl_interval_s = max(0.001, args.adxl_batch_ms / 1000.0)
    if args.adxl_samples == 0:
        derived = int(round(args.adxl_fs * adxl_interval_s))
        adxl_samples = max(1, derived)
    else:
        adxl_samples = max(1, int(args.adxl_samples))

    rs485_interval_s = max(0.001, float(args.interval))

    stop = threading.Event()
    print_lock = threading.Lock()
    count_lock = threading.Lock()
    sent = {"rs485": 0, "adxl": 0}

    def log(msg: str) -> None:
        if args.quiet:
            return
        with print_lock:
            print(msg)

    def inc(kind: str) -> int:
        with count_lock:
            sent[kind] += 1
            return sent[kind]

    def get(kind: str) -> int:
        with count_lock:
            return sent[kind]

    def maybe_stop_due_to_count() -> None:
        if not args.count:
            return
        with count_lock:
            if args.mode == "adxl" and sent["adxl"] >= args.count:
                stop.set()
            if args.mode in {"rs485", "both"} and sent["rs485"] >= args.count:
                stop.set()

    def rs485_worker() -> None:
        next_t = time.monotonic()
        while not stop.is_set():
            _sleep_until(stop, next_t)
            if stop.is_set():
                break

            now_dt = datetime.now()
            payload = _rs485_payload(args.device_id, now_dt, ranges)
            status, body = _post_json(args.url, args.api_key, payload, timeout_s=args.timeout)
            n = inc("rs485")
            log(f"[rs485 #{n}] -> {status} {body[:200]}")
            maybe_stop_due_to_count()

            next_t += rs485_interval_s
            # Prevent runaway drift if the request took too long
            next_t = max(next_t, time.monotonic())

    def adxl_worker() -> None:
        tick = 0
        next_t = time.monotonic()
        while not stop.is_set():
            _sleep_until(stop, next_t)
            if stop.is_set():
                break

            tick += 1
            if tick % args.adxl_every != 0:
                next_t += adxl_interval_s
                next_t = max(next_t, time.monotonic())
                continue

            now_dt = datetime.now()
            payload = _adxl_payload(args.device_id, now_dt, args.adxl_fs, adxl_samples, ranges)
            status, body = _post_json(args.url, args.api_key, payload, timeout_s=args.timeout)
            n = inc("adxl")
            log(f"[adxl_batch #{n}] ({adxl_samples} @ {args.adxl_fs}Hz) -> {status} {body[:200]}")
            maybe_stop_due_to_count()

            next_t += adxl_interval_s
            next_t = max(next_t, time.monotonic())

    threads: list[threading.Thread] = []
    if args.mode in {"rs485", "both"}:
        threads.append(threading.Thread(target=rs485_worker, name="rs485-sim", daemon=True))
    if args.mode in {"adxl", "both"}:
        threads.append(threading.Thread(target=adxl_worker, name="adxl-sim", daemon=True))

    for t in threads:
        t.start()

    try:
        while any(t.is_alive() for t in threads):
            if stop.is_set():
                break
            time.sleep(0.1)
    except KeyboardInterrupt:
        stop.set()
        log("Stopping...")
    finally:
        stop.set()
        for t in threads:
            t.join(timeout=2.0)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
