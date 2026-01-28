"""
SQLite ORM models (SQLAlchemy).

Goal: avoid hand-written SQL in the codebase.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import BigInteger, Float, Integer, String, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


def _now_iso() -> str:
    return datetime.now().isoformat()


class Base(DeclarativeBase):
    pass


class RS485Sample(Base):
    __tablename__ = "rs485_samples"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    time_local: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)
    temp_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    hum_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    wind_dir_deg: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wind_dir_txt: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    wind_spd_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "time_local": self.time_local,
            "temp_c": self.temp_c,
            "hum_pct": self.hum_pct,
            "wind_dir_deg": self.wind_dir_deg,
            "wind_dir_txt": self.wind_dir_txt,
            "wind_spd_ms": self.wind_spd_ms,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"<RS485Sample(id={self.id}, temp={self.temp_c}°C, hum={self.hum_pct}%)>"


Index("rs485_samples_id_idx", RS485Sample.id)
Index("rs485_samples_time_local_idx", RS485Sample.time_local)
Index("rs485_samples_created_at_idx", RS485Sample.created_at)


class ADXLBatch(Base):
    __tablename__ = "adxl_batches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chunk_start_us: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    samples: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[str] = mapped_column(String, nullable=False, default=_now_iso)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "chunk_start_us": self.chunk_start_us,
            "samples": self.samples,
            "created_at": self.created_at,
        }

    def __repr__(self) -> str:
        return f"<ADXLBatch(id={self.id}, chunk_start={self.chunk_start_us})>"


Index("adxl_batches_id_idx", ADXLBatch.id)
Index("adxl_batches_created_at_idx", ADXLBatch.created_at)
Index("adxl_batches_chunk_start_us_idx", ADXLBatch.chunk_start_us)
