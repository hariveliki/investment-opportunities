"""Detail router: stock detail endpoints."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Query

from app.models.schemas import StockDetail
from app.services import market_data_service

router = APIRouter(prefix="/v1", tags=["detail"])


@router.get("/stocks/{ticker}", response_model=StockDetail)
async def get_stock_detail(
    ticker: str,
    period: str = Query(default="3m", description="Chart period: 1m, 3m, 6m, 1y"),
):
    today = date.today()
    period_days = {"1m": 30, "3m": 90, "6m": 180, "1y": 365}
    days = period_days.get(period, 90)
    start_date = today - timedelta(days=days)

    detail = market_data_service.get_ticker_detail(ticker, start_date, today)
    return StockDetail(**detail)
