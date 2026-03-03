"""Analytics engine: computes returns and applies filters."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

import numpy as np
import pandas as pd

from app.models.schemas import PriceBasis, ScanRequest, ScanResponse, ScanResultItem, UNIVERSE_LABELS
from app.services import calendar_service, market_data_service, universe_service

logger = logging.getLogger(__name__)

BATCH_SIZE = 50


async def run_scan(request: ScanRequest) -> ScanResponse:
    """Execute a drawdown scan and return results."""
    as_of = request.as_of or date.today()
    universe_id = request.universe

    tickers = universe_service.get_constituents(universe_id, request.custom_tickers)
    if not tickers:
        return ScanResponse(
            as_of_session=as_of.isoformat(),
            start_session=as_of.isoformat(),
            universe=universe_id,
            universe_label=UNIVERSE_LABELS.get(universe_id, universe_id),
            threshold_pct=request.threshold_pct,
            price_basis=request.price_basis.value,
            horizon=request.horizon,
            total_universe_size=0,
            results=[],
            excluded={"no_constituents": 1},
        )

    total_universe_size = len(tickers)

    start_session, end_session = calendar_service.resolve_sessions(
        universe_id, as_of, request.horizon
    )

    all_results: list[ScanResultItem] = []
    insufficient_data_count = 0
    ipo_within_window_count = 0
    data_anomaly_count = 0

    for i in range(0, len(tickers), BATCH_SIZE):
        batch = tickers[i : i + BATCH_SIZE]

        prices = market_data_service.fetch_prices(
            batch,
            start_session,
            end_session,
            request.price_basis.value,
        )

        if prices.empty:
            insufficient_data_count += len(batch)
            continue

        sparkline_data = {}
        for ticker in batch:
            if ticker in prices.columns:
                series = prices[ticker].dropna()
                if len(series) > 0:
                    sparkline_data[ticker] = [round(float(v), 2) for v in series.values]

        for ticker in batch:
            if ticker not in prices.columns:
                insufficient_data_count += 1
                continue

            series = prices[ticker].dropna()
            if len(series) < 2:
                insufficient_data_count += 1
                continue

            start_ts = pd.Timestamp(start_session)
            end_ts = pd.Timestamp(end_session)

            valid_start = series.index[series.index <= end_ts]
            valid_end = series.index[series.index <= end_ts]

            start_idx = series.index.searchsorted(start_ts)
            if start_idx >= len(series):
                start_idx = len(series) - 1
            if start_idx > 0 and series.index[start_idx] > start_ts:
                start_idx = max(0, start_idx - 1)
            elif start_idx == 0 and series.index[0] > start_ts:
                if (series.index[0] - start_ts).days > 5:
                    ipo_within_window_count += 1
                    continue

            end_idx = series.index.searchsorted(end_ts, side="right") - 1
            if end_idx < 0:
                insufficient_data_count += 1
                continue

            start_price = float(series.iloc[start_idx])
            end_price = float(series.iloc[end_idx])
            actual_start_date = series.index[start_idx].date()
            actual_end_date = series.index[end_idx].date()

            if start_price <= 0:
                insufficient_data_count += 1
                continue

            return_pct = ((end_price / start_price) - 1) * 100

            warning = None
            if abs(return_pct) > 80:
                warning = "Possible data anomaly: extreme return may reflect corporate action"
                data_anomaly_count += 1

            if request.min_price and end_price < request.min_price:
                continue

            if return_pct <= request.threshold_pct:
                info = market_data_service.get_ticker_info(ticker)

                if request.min_mkt_cap and info.get("market_cap"):
                    if info["market_cap"] < request.min_mkt_cap:
                        continue

                if request.sector and info.get("sector"):
                    if info["sector"].lower() != request.sector.lower():
                        continue

                all_results.append(ScanResultItem(
                    ticker=ticker,
                    name=info.get("name", ticker),
                    return_pct=round(return_pct, 2),
                    start_price=round(start_price, 2),
                    end_price=round(end_price, 2),
                    start_date=actual_start_date.isoformat(),
                    end_date=actual_end_date.isoformat(),
                    currency=info.get("currency", "USD"),
                    sector=info.get("sector"),
                    industry=info.get("industry"),
                    market_cap=info.get("market_cap"),
                    avg_volume=info.get("avg_volume"),
                    sparkline=sparkline_data.get(ticker, []),
                    data_warning=warning,
                ))

    all_results.sort(key=lambda r: r.return_pct)

    return ScanResponse(
        as_of_session=end_session.isoformat(),
        start_session=start_session.isoformat(),
        universe=universe_id,
        universe_label=UNIVERSE_LABELS.get(universe_id, universe_id),
        threshold_pct=request.threshold_pct,
        price_basis=request.price_basis.value,
        horizon=request.horizon,
        total_universe_size=total_universe_size,
        results=all_results,
        excluded={
            "insufficient_data": insufficient_data_count,
            "ipo_within_window": ipo_within_window_count,
            "data_anomaly": data_anomaly_count,
        },
    )
