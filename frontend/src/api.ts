import type { ScanResponse, ScanConfig, UniverseInfo, StockDetail } from './types';

const BASE_URL = '/v1';

export async function runScan(config: ScanConfig): Promise<ScanResponse> {
  const params = new URLSearchParams();
  params.set('universe', config.universe);
  if (config.as_of) params.set('as_of', config.as_of);
  params.set('horizon', config.horizon);
  params.set('threshold_pct', String(config.threshold_pct));
  params.set('price_basis', config.price_basis);
  if (config.min_mkt_cap) params.set('min_mkt_cap', String(config.min_mkt_cap));
  if (config.min_price) params.set('min_price', String(config.min_price));
  if (config.sector) params.set('sector', config.sector);
  if (config.custom_tickers) params.set('custom_tickers', config.custom_tickers);

  const response = await fetch(`${BASE_URL}/scans/drawdowns?${params.toString()}`);
  if (!response.ok) {
    throw new Error(`Scan failed: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchUniverses(): Promise<UniverseInfo[]> {
  const response = await fetch(`${BASE_URL}/universes`);
  if (!response.ok) throw new Error('Failed to fetch universes');
  return response.json();
}

export async function fetchStockDetail(ticker: string, period = '3m'): Promise<StockDetail> {
  const response = await fetch(`${BASE_URL}/stocks/${encodeURIComponent(ticker)}?period=${period}`);
  if (!response.ok) throw new Error('Failed to fetch stock detail');
  return response.json();
}
