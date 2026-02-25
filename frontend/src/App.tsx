import { useState, useCallback, useEffect } from 'react';
import type { ScanConfig, ScanResponse } from './types';
import { runScan } from './api';
import { FilterPanel } from './components/FilterPanel';
import { ResultsTable } from './components/ResultsTable';
import { StockDetailDrawer } from './components/StockDetailDrawer';
import { SavedScans } from './components/SavedScans';
import { TrendingDown, AlertCircle } from 'lucide-react';

function getDefaultConfig(): ScanConfig {
  const params = new URLSearchParams(window.location.search);
  return {
    universe: params.get('universe') || 'sp500',
    as_of: params.get('as_of') || new Date().toISOString().split('T')[0],
    horizon: params.get('horizon') || '5d',
    threshold_pct: Number(params.get('threshold_pct')) || -20,
    price_basis: params.get('price_basis') || 'adj_close',
    min_mkt_cap: params.get('min_mkt_cap') ? Number(params.get('min_mkt_cap')) : null,
    min_price: params.get('min_price') ? Number(params.get('min_price')) : null,
    sector: params.get('sector') || null,
    custom_tickers: params.get('custom_tickers') || '',
  };
}

export default function App() {
  const [config, setConfig] = useState<ScanConfig>(getDefaultConfig);
  const [response, setResponse] = useState<ScanResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedTicker, setSelectedTicker] = useState<string | null>(null);
  const [saveTrigger, setSaveTrigger] = useState(0);

  const handleScan = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await runScan(config);
      setResponse(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIsLoading(false);
    }
  }, [config]);

  const handleSave = useCallback(() => {
    setSaveTrigger((prev) => prev + 1);
  }, []);

  const handleLoadScan = useCallback((loadedConfig: ScanConfig) => {
    setConfig(loadedConfig);
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has('universe') || params.has('horizon')) {
      handleScan();
    }
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-[1440px] mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-lg flex items-center justify-center">
              <TrendingDown size={20} className="text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-800 leading-tight">Equity Drawdown Scanner</h1>
              <p className="text-xs text-slate-400">Screen for significant price drops across global indices</p>
            </div>
          </div>
          <div className="text-xs text-slate-400">
            Data via Yahoo Finance | Adjusted close prices
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1440px] mx-auto px-6 py-6">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl flex items-center gap-3 text-sm text-red-700">
            <AlertCircle size={18} />
            <span>{error}</span>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600">
              Dismiss
            </button>
          </div>
        )}

        <div className="flex gap-6">
          {/* Left panel */}
          <aside className="w-80 shrink-0 space-y-4">
            <FilterPanel
              config={config}
              onChange={setConfig}
              onScan={handleScan}
              onSave={handleSave}
              isLoading={isLoading}
            />
            <SavedScans
              currentConfig={config}
              onLoad={handleLoadScan}
              saveTrigger={saveTrigger}
            />
          </aside>

          {/* Right panel */}
          <section className="flex-1 min-w-0">
            <ResultsTable
              response={response}
              onSelectStock={setSelectedTicker}
            />
          </section>
        </div>
      </main>

      {/* Stock Detail Drawer */}
      <StockDetailDrawer
        ticker={selectedTicker}
        onClose={() => setSelectedTicker(null)}
      />
    </div>
  );
}
