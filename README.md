# Equity Drawdown Scanner

Screen equities for significant price drops over configurable lookback horizons. Supports multiple global indices, adjustable thresholds, and detailed stock analysis.

## Features

- **Universe Selection**: S&P 500, Nasdaq 100, Dow 30, FTSE 100, DAX, SMI, Nikkei 225, or custom watchlists
- **Configurable Horizons**: 1D, 1W, 2W, 1M, 3M, 6M, 1Y with trading-day or calendar-day semantics
- **Threshold Scanning**: Find stocks that have fallen by at least X% over the selected period
- **Price Basis**: Adjusted Close (default, split/dividend-adjusted) or unadjusted Close
- **Sortable Results Table**: with sparkline charts, return %, sector, market cap
- **Stock Detail Drawer**: price charts with Recharts, corporate actions, key metadata
- **Advanced Filters**: market cap, min price, sector
- **CSV Export**: download scan results
- **Saved Scans**: persist configurations to localStorage, shareable permalinks

## Architecture

```
├── backend/          # Python FastAPI application
│   ├── app/
│   │   ├── main.py              # FastAPI app entry point
│   │   ├── models/schemas.py    # Pydantic request/response models
│   │   ├── routers/
│   │   │   ├── scan.py          # /v1/scans/drawdowns, /v1/universes
│   │   │   └── detail.py        # /v1/stocks/{ticker}
│   │   └── services/
│   │       ├── analytics_engine.py    # Return computation, threshold filtering
│   │       ├── calendar_service.py    # Trading calendar resolution (exchange_calendars)
│   │       ├── market_data_service.py # Price fetching via yfinance
│   │       └── universe_service.py    # Index constituent lists
│   └── requirements.txt
├── frontend/         # React + TypeScript + Vite
│   └── src/
│       ├── App.tsx
│       ├── api.ts               # API client
│       ├── types.ts             # TypeScript interfaces
│       ├── utils.ts             # Formatting, CSV export
│       └── components/
│           ├── FilterPanel.tsx       # Scan configuration panel
│           ├── ResultsTable.tsx      # Sortable results with sparklines
│           ├── StockDetailDrawer.tsx # Detail view with charts
│           ├── SavedScans.tsx        # Saved scan management
│           └── Sparkline.tsx         # SVG sparkline component
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 8+

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
python3 -m uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend dev server proxies `/v1/*` requests to the backend at `localhost:8000`.

Open http://localhost:5173 in your browser.

## API Reference

### `GET /v1/scans/drawdowns`

Run a drawdown scan.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `universe` | string | `sp500` | Universe ID |
| `as_of` | date | today | As-of date (ISO format) |
| `horizon` | string | `5d` | Horizon: `Nd` (trading days) or `Nc` (calendar days) |
| `threshold_pct` | float | `-20` | Return threshold (negative for drawdowns) |
| `price_basis` | string | `adj_close` | `adj_close` or `close` |
| `min_mkt_cap` | float | — | Minimum market cap (USD) |
| `min_price` | float | — | Minimum end price |
| `sector` | string | — | Sector filter |
| `custom_tickers` | string | — | Comma-separated tickers (for custom universe) |

### `GET /v1/universes`

List available universes.

### `GET /v1/universes/{id}/constituents`

Get constituent list for a universe.

### `GET /v1/stocks/{ticker}?period=3m`

Get detailed stock data with price history and corporate actions.

### `GET /health`

Health check endpoint.

## Return Calculation

```
Return % = (P_end / P_start - 1) × 100
```

A stock is flagged when `Return % ≤ threshold_pct`.

### Session Resolution

- **End session**: most recent completed trading session ≤ as-of date
- **Start session (trading days)**: N sessions before end session
- **Start session (calendar days)**: nearest session ≤ (as-of − N calendar days)

Trading calendars are sourced from `exchange_calendars` per universe.

## Data Source

Market data is provided by [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library. Index constituent lists are scraped from Wikipedia for MVP.

## License

MIT
