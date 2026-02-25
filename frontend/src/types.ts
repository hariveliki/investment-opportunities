export interface ScanResultItem {
  ticker: string;
  name: string;
  return_pct: number;
  start_price: number;
  end_price: number;
  start_date: string;
  end_date: string;
  currency: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  avg_volume: number | null;
  sparkline: number[];
  data_warning: string | null;
}

export interface ScanResponse {
  as_of_session: string;
  start_session: string;
  universe: string;
  universe_label: string;
  threshold_pct: number;
  price_basis: string;
  horizon: string;
  total_universe_size: number;
  results: ScanResultItem[];
  excluded: Record<string, number>;
}

export interface UniverseInfo {
  id: string;
  label: string;
  description: string;
  exchange_calendar: string;
  constituent_count: number | null;
}

export interface StockDetail {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  currency: string;
  exchange: string | null;
  prices: PriceBar[];
  corporate_actions: CorporateAction[];
}

export interface PriceBar {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CorporateAction {
  date: string;
  type: string;
  value: string | number;
}

export interface ScanConfig {
  universe: string;
  as_of: string;
  horizon: string;
  threshold_pct: number;
  price_basis: string;
  min_mkt_cap: number | null;
  min_price: number | null;
  sector: string | null;
  custom_tickers: string;
}

export interface SavedScan {
  id: string;
  name: string;
  config: ScanConfig;
  created_at: string;
}
