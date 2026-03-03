from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class HorizonType(str, Enum):
    TRADING_DAYS = "trading"
    CALENDAR_DAYS = "calendar"


class PriceBasis(str, Enum):
    ADJ_CLOSE = "adj_close"
    CLOSE = "close"


class UniverseId(str, Enum):
    SP500 = "sp500"
    NASDAQ100 = "nasdaq100"
    DOW30 = "dow30"
    FTSE100 = "ftse100"
    DAX = "dax"
    SMI = "smi"
    STOXX600 = "stoxx600"
    NIKKEI225 = "nikkei225"
    CUSTOM = "custom"


UNIVERSE_LABELS: dict[str, str] = {
    "sp500": "S&P 500",
    "nasdaq100": "Nasdaq 100",
    "dow30": "Dow Jones 30",
    "ftse100": "FTSE 100",
    "dax": "DAX",
    "smi": "SMI",
    "stoxx600": "STOXX Europe 600",
    "nikkei225": "Nikkei 225",
}


UNIVERSE_EXCHANGE_CALENDARS: dict[str, str] = {
    "sp500": "XNYS",
    "nasdaq100": "XNYS",
    "dow30": "XNYS",
    "ftse100": "XLON",
    "dax": "XFRA",
    "smi": "XSWX",
    "stoxx600": "XLON",
    "nikkei225": "XTKS",
}


class ScanRequest(BaseModel):
    universe: str = Field(default="sp500", description="Universe identifier")
    as_of: Optional[date] = Field(default=None, description="As-of date (default: today)")
    horizon: str = Field(default="5d", description="Horizon string, e.g. 5d, 7c, 20d")
    threshold_pct: float = Field(default=-20.0, description="Return threshold (negative)")
    price_basis: PriceBasis = Field(default=PriceBasis.ADJ_CLOSE)
    min_mkt_cap: Optional[float] = Field(default=None, description="Minimum market cap in USD")
    min_price: Optional[float] = Field(default=None, description="Minimum price filter")
    sector: Optional[str] = Field(default=None)
    custom_tickers: Optional[list[str]] = Field(default=None, description="Custom ticker list")


class ScanResultItem(BaseModel):
    ticker: str
    name: str
    return_pct: float
    start_price: float
    end_price: float
    start_date: str
    end_date: str
    currency: str = "USD"
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    avg_volume: Optional[float] = None
    sparkline: list[float] = Field(default_factory=list)
    data_warning: Optional[str] = None


class ScanResponse(BaseModel):
    as_of_session: str
    start_session: str
    universe: str
    universe_label: str
    threshold_pct: float
    price_basis: str
    horizon: str
    total_universe_size: int
    results: list[ScanResultItem]
    excluded: dict[str, int] = Field(default_factory=dict)


class UniverseInfo(BaseModel):
    id: str
    label: str
    description: str
    exchange_calendar: str
    constituent_count: Optional[int] = None


class StockDetail(BaseModel):
    ticker: str
    name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    currency: str = "USD"
    exchange: Optional[str] = None
    prices: list[dict] = Field(default_factory=list)
    corporate_actions: list[dict] = Field(default_factory=list)


class ScanSummary(BaseModel):
    id: int
    universe: str
    as_of_date: str
    horizon: str
    threshold_pct: float
    result_count: int
    created_at: str


class SavedScan(BaseModel):
    id: str
    name: str
    config: ScanRequest
    created_at: str
    last_run: Optional[str] = None
