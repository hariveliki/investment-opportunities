"""Scan router: drawdown scan endpoints."""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import (
    PriceBasis,
    ScanRequest,
    ScanResponse,
    UNIVERSE_LABELS,
    UNIVERSE_EXCHANGE_CALENDARS,
    UniverseInfo,
)
from app.services import analytics_engine, universe_service

router = APIRouter(prefix="/v1", tags=["scans"])


@router.get("/scans/drawdowns", response_model=ScanResponse)
async def scan_drawdowns(
    universe: str = Query(default="sp500", description="Universe ID"),
    as_of: Optional[date] = Query(default=None, description="As-of date"),
    horizon: str = Query(default="5d", description="Horizon (e.g. 5d, 7c)"),
    threshold_pct: float = Query(default=-20.0, description="Return threshold %"),
    price_basis: PriceBasis = Query(default=PriceBasis.ADJ_CLOSE),
    min_mkt_cap: Optional[float] = Query(default=None),
    min_price: Optional[float] = Query(default=None),
    sector: Optional[str] = Query(default=None),
    custom_tickers: Optional[str] = Query(default=None, description="Comma-separated tickers"),
):
    request = ScanRequest(
        universe=universe,
        as_of=as_of,
        horizon=horizon,
        threshold_pct=threshold_pct,
        price_basis=price_basis,
        min_mkt_cap=min_mkt_cap,
        min_price=min_price,
        sector=sector,
        custom_tickers=custom_tickers.split(",") if custom_tickers else None,
    )
    return await analytics_engine.run_scan(request)


@router.get("/universes", response_model=list[UniverseInfo])
async def list_universes():
    universes = []
    for uid, label in UNIVERSE_LABELS.items():
        exchange = UNIVERSE_EXCHANGE_CALENDARS.get(uid, "XNYS")
        try:
            constituents = universe_service.get_constituents(uid)
            count = len(constituents)
        except Exception:
            count = None
        universes.append(UniverseInfo(
            id=uid,
            label=label,
            description=f"{label} index constituents",
            exchange_calendar=exchange,
            constituent_count=count,
        ))
    universes.append(UniverseInfo(
        id="custom",
        label="Custom Watchlist",
        description="User-defined list of tickers",
        exchange_calendar="XNYS",
        constituent_count=None,
    ))
    return universes


@router.get("/universes/{universe_id}/constituents")
async def get_constituents(universe_id: str, as_of: Optional[date] = None):
    tickers = universe_service.get_constituents(universe_id)
    return {
        "universe": universe_id,
        "as_of": (as_of or date.today()).isoformat(),
        "constituents": tickers,
        "count": len(tickers),
    }
