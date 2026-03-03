"""ORM models for scan cache."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ScanCacheRow(Base):
    __tablename__ = "scan_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    request_json: Mapped[str] = mapped_column(Text, nullable=False)
    response_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )
    as_of_date: Mapped[str] = mapped_column(String(10), nullable=False)
    universe: Mapped[str] = mapped_column(String(32), nullable=False)
    horizon: Mapped[str] = mapped_column(String(10), nullable=False)
    threshold_pct: Mapped[float] = mapped_column(Float, nullable=False)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    __table_args__ = (
        Index("ix_scan_cache_request_hash", "request_hash"),
    )
