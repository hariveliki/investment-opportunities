import { useState, useEffect } from 'react';
import type { ScanConfig, UniverseInfo } from '../types';
import { fetchUniverses } from '../api';
import { ChevronDown, ChevronUp, Search, Save, Settings2 } from 'lucide-react';

const HORIZON_PRESETS = [
  { label: '1 Day', value: '1d' },
  { label: '1 Week', value: '5d' },
  { label: '2 Weeks', value: '10d' },
  { label: '1 Month', value: '20d' },
  { label: '3 Months', value: '60d' },
  { label: '6 Months', value: '126d' },
  { label: '1 Year', value: '252d' },
];

const THRESHOLD_PRESETS = [-5, -10, -15, -20, -25, -30, -40, -50];

interface FilterPanelProps {
  config: ScanConfig;
  onChange: (config: ScanConfig) => void;
  onScan: () => void;
  onSave: () => void;
  isLoading: boolean;
}

export function FilterPanel({ config, onChange, onScan, onSave, isLoading }: FilterPanelProps) {
  const [universes, setUniverses] = useState<UniverseInfo[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [customHorizon, setCustomHorizon] = useState('');
  const [horizonType, setHorizonType] = useState<'d' | 'c'>('d');

  useEffect(() => {
    fetchUniverses().then(setUniverses).catch(console.error);
  }, []);

  const update = (partial: Partial<ScanConfig>) => {
    onChange({ ...config, ...partial });
  };

  const handleCustomHorizon = () => {
    const val = parseInt(customHorizon, 10);
    if (!isNaN(val) && val > 0) {
      update({ horizon: `${val}${horizonType}` });
    }
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5 space-y-5">
      <div className="flex items-center gap-2 mb-1">
        <Settings2 size={18} className="text-blue-600" />
        <h2 className="text-base font-semibold text-slate-800">Scan Configuration</h2>
      </div>

      {/* Universe */}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1.5">Universe</label>
        <select
          value={config.universe}
          onChange={(e) => update({ universe: e.target.value, custom_tickers: '' })}
          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          {universes.map((u) => (
            <option key={u.id} value={u.id}>
              {u.label} {u.constituent_count ? `(${u.constituent_count})` : ''}
            </option>
          ))}
        </select>
      </div>

      {config.universe === 'custom' && (
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-1.5">Tickers (comma-separated)</label>
          <input
            type="text"
            value={config.custom_tickers}
            onChange={(e) => update({ custom_tickers: e.target.value })}
            placeholder="AAPL, MSFT, GOOG"
            className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      {/* As-of Date */}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1.5">As-of Date</label>
        <input
          type="date"
          value={config.as_of}
          onChange={(e) => update({ as_of: e.target.value })}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      {/* Horizon */}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1.5">Lookback Horizon</label>
        <div className="grid grid-cols-4 gap-1.5 mb-2">
          {HORIZON_PRESETS.map((h) => (
            <button
              key={h.value}
              onClick={() => update({ horizon: h.value })}
              className={`px-2 py-1.5 rounded-md text-xs font-medium transition-colors ${
                config.horizon === h.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {h.label}
            </button>
          ))}
        </div>
        <div className="flex gap-2 items-center">
          <input
            type="number"
            value={customHorizon}
            onChange={(e) => setCustomHorizon(e.target.value)}
            placeholder="Custom"
            min="1"
            className="w-20 rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <select
            value={horizonType}
            onChange={(e) => setHorizonType(e.target.value as 'd' | 'c')}
            className="rounded-lg border border-slate-300 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="d">Trading Days</option>
            <option value="c">Calendar Days</option>
          </select>
          <button
            onClick={handleCustomHorizon}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition-colors"
          >
            Set
          </button>
        </div>
      </div>

      {/* Threshold */}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1.5">
          Drop Threshold: <span className="font-bold text-red-600">{config.threshold_pct}%</span>
        </label>
        <input
          type="range"
          min="-80"
          max="-1"
          step="1"
          value={config.threshold_pct}
          onChange={(e) => update({ threshold_pct: Number(e.target.value) })}
          className="w-full accent-red-600"
        />
        <div className="flex flex-wrap gap-1.5 mt-2">
          {THRESHOLD_PRESETS.map((t) => (
            <button
              key={t}
              onClick={() => update({ threshold_pct: t })}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                config.threshold_pct === t
                  ? 'bg-red-600 text-white'
                  : 'bg-red-50 text-red-700 hover:bg-red-100'
              }`}
            >
              {t}%
            </button>
          ))}
        </div>
      </div>

      {/* Price Basis */}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1.5">Price Basis</label>
        <div className="flex gap-2">
          {[
            { label: 'Adjusted Close', value: 'adj_close' },
            { label: 'Close', value: 'close' },
          ].map((b) => (
            <button
              key={b.value}
              onClick={() => update({ price_basis: b.value })}
              className={`flex-1 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                config.price_basis === b.value
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {b.label}
            </button>
          ))}
        </div>
        {config.price_basis === 'close' && (
          <p className="mt-1.5 text-xs text-amber-600 bg-amber-50 p-2 rounded">
            Unadjusted returns may reflect splits and other corporate actions.
          </p>
        )}
      </div>

      {/* Advanced Filters */}
      <div>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-1 text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
        >
          {showAdvanced ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          Advanced Filters
        </button>
        {showAdvanced && (
          <div className="mt-3 space-y-3 pt-3 border-t border-slate-100">
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Min Market Cap (USD)</label>
              <select
                value={config.min_mkt_cap ?? ''}
                onChange={(e) => update({ min_mkt_cap: e.target.value ? Number(e.target.value) : null })}
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">No filter</option>
                <option value="100000000">$100M+</option>
                <option value="1000000000">$1B+</option>
                <option value="10000000000">$10B+</option>
                <option value="100000000000">$100B+</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Min Price ($)</label>
              <input
                type="number"
                value={config.min_price ?? ''}
                onChange={(e) => update({ min_price: e.target.value ? Number(e.target.value) : null })}
                placeholder="e.g. 5"
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-500 mb-1">Sector</label>
              <input
                type="text"
                value={config.sector ?? ''}
                onChange={(e) => update({ sector: e.target.value || null })}
                placeholder="e.g. Technology"
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex gap-2 pt-2">
        <button
          onClick={onScan}
          disabled={isLoading}
          className="flex-1 flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-semibold py-2.5 px-4 rounded-lg transition-colors"
        >
          {isLoading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <Search size={16} />
          )}
          {isLoading ? 'Scanning...' : 'Run Scan'}
        </button>
        <button
          onClick={onSave}
          className="flex items-center gap-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-medium py-2.5 px-3 rounded-lg transition-colors"
          title="Save scan configuration"
        >
          <Save size={16} />
        </button>
      </div>
    </div>
  );
}
