"""Universe service: provides index constituent lists."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


_CONSTITUENT_CACHE: dict[str, list[str]] = {}


def _scrape_sp500() -> list[str]:
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df["Symbol"].tolist()
    return [t.replace(".", "-") for t in tickers]


def _scrape_nasdaq100() -> list[str]:
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    for t in tables:
        if "Ticker" in t.columns:
            return t["Ticker"].tolist()
        if "Symbol" in t.columns:
            return t["Symbol"].tolist()
    return []


def _scrape_dow30() -> list[str]:
    url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
    tables = pd.read_html(url)
    for t in tables:
        if "Symbol" in t.columns:
            return t["Symbol"].tolist()
    return []


def _scrape_ftse100() -> list[str]:
    url = "https://en.wikipedia.org/wiki/FTSE_100_Index"
    tables = pd.read_html(url)
    for t in tables:
        cols = [c for c in t.columns if "ticker" in c.lower() or "epic" in c.lower()]
        if cols:
            tickers = t[cols[0]].tolist()
            return [f"{tk}.L" for tk in tickers if isinstance(tk, str)]
    return []


def _scrape_dax() -> list[str]:
    url = "https://en.wikipedia.org/wiki/DAX"
    tables = pd.read_html(url)
    for t in tables:
        cols = [c for c in t.columns if "ticker" in c.lower() or "symbol" in c.lower()]
        if cols:
            return t[cols[0]].tolist()
    return []


_STATIC_SMI = [
    "ABBN.SW", "ADEN.SW", "CSGN.SW", "GEBN.SW", "GIVN.SW",
    "HOLN.SW", "KNIN.SW", "LONN.SW", "NESN.SW", "NOVN.SW",
    "PGHN.SW", "RIHN.SW", "ROG.SW", "SCMN.SW", "SGSN.SW",
    "SIKA.SW", "SLHN.SW", "SREN.SW", "UBSG.SW", "ZURN.SW",
]

_STATIC_NIKKEI_SAMPLE = [
    "7203.T", "6758.T", "9984.T", "6861.T", "8306.T",
    "9433.T", "6501.T", "7267.T", "4502.T", "6902.T",
    "7751.T", "8035.T", "6954.T", "4063.T", "9432.T",
    "6367.T", "7974.T", "8058.T", "2802.T", "4503.T",
]


_SCRAPERS: dict[str, callable] = {
    "sp500": _scrape_sp500,
    "nasdaq100": _scrape_nasdaq100,
    "dow30": _scrape_dow30,
    "ftse100": _scrape_ftse100,
    "dax": _scrape_dax,
}


def get_constituents(universe_id: str, custom_tickers: Optional[list[str]] = None) -> list[str]:
    """Return list of ticker symbols for the given universe."""
    if universe_id == "custom" and custom_tickers:
        return custom_tickers

    if universe_id in _CONSTITUENT_CACHE:
        return _CONSTITUENT_CACHE[universe_id]

    if universe_id == "smi":
        _CONSTITUENT_CACHE[universe_id] = _STATIC_SMI
        return _STATIC_SMI

    if universe_id == "nikkei225":
        _CONSTITUENT_CACHE[universe_id] = _STATIC_NIKKEI_SAMPLE
        return _STATIC_NIKKEI_SAMPLE

    scraper = _SCRAPERS.get(universe_id)
    if scraper:
        try:
            tickers = scraper()
            if tickers:
                _CONSTITUENT_CACHE[universe_id] = tickers
                logger.info(f"Loaded {len(tickers)} constituents for {universe_id}")
                return tickers
        except Exception as e:
            logger.error(f"Failed to scrape {universe_id}: {e}")

    return _CONSTITUENT_CACHE.get(universe_id, [])


def clear_cache():
    _CONSTITUENT_CACHE.clear()
