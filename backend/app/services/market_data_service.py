"""Market data service: fetches price data via yfinance."""

from __future__ import annotations

import logging
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

_INFO_CACHE: dict[str, dict] = {}


def fetch_prices(
    tickers: list[str],
    start_date: date,
    end_date: date,
    price_basis: str = "adj_close",
) -> pd.DataFrame:
    """Fetch daily price data for a list of tickers.

    Returns a DataFrame indexed by date with ticker columns.
    """
    fetch_start = start_date - timedelta(days=5)
    fetch_end = end_date + timedelta(days=2)

    try:
        data = yf.download(
            tickers,
            start=fetch_start.isoformat(),
            end=fetch_end.isoformat(),
            auto_adjust=True if price_basis == "adj_close" else False,
            progress=False,
            threads=True,
        )
    except Exception as e:
        logger.error(f"yfinance download error: {e}")
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    if price_basis == "adj_close":
        if "Close" in data.columns or (isinstance(data.columns, pd.MultiIndex) and "Close" in data.columns.get_level_values(0)):
            if isinstance(data.columns, pd.MultiIndex):
                prices = data["Close"]
            else:
                prices = data[["Close"]] if len(tickers) == 1 else data["Close"]
        else:
            prices = data
    else:
        if isinstance(data.columns, pd.MultiIndex) and "Close" in data.columns.get_level_values(0):
            prices = data["Close"]
        elif "Close" in data.columns:
            prices = data[["Close"]] if len(tickers) == 1 else data["Close"]
        else:
            prices = data

    if isinstance(prices, pd.Series):
        prices = prices.to_frame(name=tickers[0])

    if len(tickers) == 1 and len(prices.columns) == 1:
        prices.columns = [tickers[0]]

    return prices


def fetch_sparkline_data(
    tickers: list[str],
    start_date: date,
    end_date: date,
) -> dict[str, list[float]]:
    """Fetch daily close prices for sparkline rendering."""
    prices = fetch_prices(tickers, start_date, end_date)
    if prices.empty:
        return {}

    result = {}
    for ticker in tickers:
        if ticker in prices.columns:
            series = prices[ticker].dropna()
            if len(series) > 0:
                result[ticker] = [round(float(v), 2) for v in series.values]
    return result


def get_ticker_info(ticker: str) -> dict:
    """Get metadata for a single ticker (cached)."""
    if ticker in _INFO_CACHE:
        return _INFO_CACHE[ticker]

    try:
        tk = yf.Ticker(ticker)
        info = tk.info or {}
        result = {
            "name": info.get("longName") or info.get("shortName") or ticker,
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency", "USD"),
            "exchange": info.get("exchange"),
            "avg_volume": info.get("averageVolume"),
        }
        _INFO_CACHE[ticker] = result
        return result
    except Exception as e:
        logger.warning(f"Failed to get info for {ticker}: {e}")
        return {"name": ticker, "currency": "USD"}


def get_ticker_detail(ticker: str, start_date: date, end_date: date) -> dict:
    """Get detailed data for the detail view."""
    tk = yf.Ticker(ticker)

    info = get_ticker_info(ticker)

    hist = tk.history(start=start_date.isoformat(), end=end_date.isoformat())
    prices = []
    if not hist.empty:
        for idx, row in hist.iterrows():
            prices.append({
                "date": idx.strftime("%Y-%m-%d"),
                "open": round(float(row.get("Open", 0)), 2),
                "high": round(float(row.get("High", 0)), 2),
                "low": round(float(row.get("Low", 0)), 2),
                "close": round(float(row.get("Close", 0)), 2),
                "volume": int(row.get("Volume", 0)),
            })

    actions = []
    try:
        splits = tk.splits
        if splits is not None and not splits.empty:
            for idx, val in splits.items():
                actions.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "type": "split",
                    "value": str(val),
                })
        divs = tk.dividends
        if divs is not None and not divs.empty:
            for idx, val in divs.items():
                actions.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "type": "dividend",
                    "value": round(float(val), 4),
                })
    except Exception:
        pass

    return {
        "ticker": ticker,
        "name": info.get("name", ticker),
        "sector": info.get("sector"),
        "industry": info.get("industry"),
        "market_cap": info.get("market_cap"),
        "currency": info.get("currency", "USD"),
        "exchange": info.get("exchange"),
        "prices": prices,
        "corporate_actions": sorted(actions, key=lambda x: x["date"], reverse=True),
    }
