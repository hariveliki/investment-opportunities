"""Cache service for scan results backed by SQLite."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import select

from app.db.engine import async_session
from app.db.models import ScanCacheRow
from app.models.schemas import ScanRequest, ScanResponse

logger = logging.getLogger(__name__)

CACHE_TTL_HOURS = 4


def compute_request_hash(request: ScanRequest) -> str:
    """Return a deterministic SHA-256 hash for a scan request.

    Normalises ``as_of=None`` to today's date and sorts ``custom_tickers``
    so that logically identical requests produce the same hash.
    """
    data = request.model_dump()
    if data["as_of"] is None:
        data["as_of"] = date.today().isoformat()
    else:
        data["as_of"] = str(data["as_of"])
    if data.get("custom_tickers"):
        data["custom_tickers"] = sorted(data["custom_tickers"])
    canonical = json.dumps(data, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


async def get_cached_scan(request: ScanRequest) -> Optional[ScanResponse]:
    """Return a cached response if a fresh one exists, else ``None``.

    Historical scans (as_of in the past) are cached indefinitely.
    Today's scans expire after ``CACHE_TTL_HOURS``.
    """
    req_hash = compute_request_hash(request)
    async with async_session() as session:
        row = (
            await session.execute(
                select(ScanCacheRow).where(ScanCacheRow.request_hash == req_hash)
            )
        ).scalar_one_or_none()

        if row is None:
            return None

        as_of = request.as_of or date.today()
        is_today = as_of == date.today()
        if is_today:
            age = datetime.utcnow() - row.created_at
            if age > timedelta(hours=CACHE_TTL_HOURS):
                logger.info("Cache expired for hash=%s (age=%s)", req_hash[:12], age)
                return None

        logger.info("Cache hit for hash=%s", req_hash[:12])
        return ScanResponse.model_validate_json(row.response_json)


async def store_scan(request: ScanRequest, response: ScanResponse) -> None:
    """Upsert the scan result into the cache."""
    req_hash = compute_request_hash(request)
    request_json = request.model_dump_json()
    response_json = response.model_dump_json()
    as_of = request.as_of or date.today()

    async with async_session() as session:
        existing = (
            await session.execute(
                select(ScanCacheRow).where(ScanCacheRow.request_hash == req_hash)
            )
        ).scalar_one_or_none()

        if existing:
            existing.response_json = response_json
            existing.request_json = request_json
            existing.created_at = datetime.utcnow()
            existing.result_count = len(response.results)
        else:
            session.add(
                ScanCacheRow(
                    request_hash=req_hash,
                    request_json=request_json,
                    response_json=response_json,
                    as_of_date=as_of.isoformat(),
                    universe=request.universe,
                    horizon=request.horizon,
                    threshold_pct=request.threshold_pct,
                    result_count=len(response.results),
                )
            )
        await session.commit()
    logger.info("Stored scan result hash=%s (%d results)", req_hash[:12], len(response.results))


async def list_past_scans(
    limit: int = 50, universe: Optional[str] = None
) -> list[dict]:
    """Return summary dicts of past cached scans, newest first."""
    async with async_session() as session:
        stmt = select(ScanCacheRow).order_by(ScanCacheRow.created_at.desc())
        if universe:
            stmt = stmt.where(ScanCacheRow.universe == universe)
        stmt = stmt.limit(limit)
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": row.id,
                "universe": row.universe,
                "as_of_date": row.as_of_date,
                "horizon": row.horizon,
                "threshold_pct": row.threshold_pct,
                "result_count": row.result_count,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]


async def get_scan_by_id(scan_id: int) -> Optional[dict]:
    """Retrieve full cached result by DB row id."""
    async with async_session() as session:
        row = await session.get(ScanCacheRow, scan_id)
        if row is None:
            return None
        return {
            "id": row.id,
            "request": json.loads(row.request_json),
            "response": json.loads(row.response_json),
            "created_at": row.created_at.isoformat(),
        }
