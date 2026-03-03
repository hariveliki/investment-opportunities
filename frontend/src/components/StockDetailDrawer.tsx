import { useState, useEffect } from 'react';
import type { StockDetail } from '../types';
import { fetchStockDetail } from '../api';
import { formatNumber, formatMarketCap } from '../utils';
import { X, TrendingDown, AlertTriangle, Building2 } from 'lucide-react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from 'recharts';

interface StockDetailDrawerProps {
  ticker: string | null;
  onClose: () => void;
}

export function StockDetailDrawer({ ticker, onClose }: StockDetailDrawerProps) {
  const [detail, setDetail] = useState<StockDetail | null>(null);
  const [period, setPeriod] = useState('3m');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!ticker) {
      setDetail(null);
      return;
    }
    setLoading(true);
    fetchStockDetail(ticker, period)
      .then(setDetail)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [ticker, period]);

  if (!ticker) return null;

  const chartData = detail?.prices.map((p) => ({
    date: p.date.slice(5),
    close: p.close,
    volume: p.volume,
  })) ?? [];

  const priceStart = chartData.length > 0 ? chartData[0].close : 0;
  const priceEnd = chartData.length > 0 ? chartData[chartData.length - 1].close : 0;
  const periodReturn = priceStart > 0 ? ((priceEnd / priceStart) - 1) * 100 : 0;
  const isDown = periodReturn < 0;

  return (
    <div className="fixed inset-0 z-50 flex">
      <div className="flex-1 bg-black/30 backdrop-blur-sm" onClick={onClose} />
      <div className="w-full max-w-xl bg-white shadow-2xl overflow-y-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-800">{ticker}</h2>
            {detail && <p className="text-sm text-slate-500">{detail.name}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors"
          >
            <X size={20} />
          </button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : detail ? (
          <div className="p-5 space-y-6">
            {/* Key Stats */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-50 rounded-lg p-3">
                <div className="text-xs text-slate-500 mb-1">Sector</div>
                <div className="text-sm font-medium text-slate-700 flex items-center gap-1">
                  <Building2 size={13} />
                  {detail.sector ?? '—'}
                </div>
              </div>
              <div className="bg-slate-50 rounded-lg p-3">
                <div className="text-xs text-slate-500 mb-1">Market Cap</div>
                <div className="text-sm font-medium text-slate-700">{formatMarketCap(detail.market_cap)}</div>
              </div>
              <div className={`rounded-lg p-3 ${isDown ? 'bg-red-50' : 'bg-green-50'}`}>
                <div className="text-xs text-slate-500 mb-1">Period Return</div>
                <div className={`text-sm font-bold flex items-center gap-1 ${isDown ? 'text-red-600' : 'text-green-600'}`}>
                  <TrendingDown size={13} />
                  {formatNumber(periodReturn)}%
                </div>
              </div>
            </div>

            {/* Period selector */}
            <div className="flex gap-2">
              {['1m', '3m', '6m', '1y'].map((p) => (
                <button
                  key={p}
                  onClick={() => setPeriod(p)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    period === p
                      ? 'bg-blue-600 text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {p.toUpperCase()}
                </button>
              ))}
            </div>

            {/* Price Chart */}
            {chartData.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-3">Price Chart</h3>
                <div className="h-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <defs>
                        <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={isDown ? '#dc2626' : '#16a34a'} stopOpacity={0.15} />
                          <stop offset="95%" stopColor={isDown ? '#dc2626' : '#16a34a'} stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 10, fill: '#94a3b8' }}
                        tickLine={false}
                        axisLine={{ stroke: '#e2e8f0' }}
                        interval="preserveStartEnd"
                      />
                      <YAxis
                        tick={{ fontSize: 10, fill: '#94a3b8' }}
                        tickLine={false}
                        axisLine={false}
                        domain={['auto', 'auto']}
                        tickFormatter={(v: number) => `$${v.toFixed(0)}`}
                      />
                      <Tooltip
                        contentStyle={{
                          background: '#fff',
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                        formatter={(value) => [`$${Number(value ?? 0).toFixed(2)}`, 'Close']}
                      />
                      <Area
                        type="monotone"
                        dataKey="close"
                        stroke={isDown ? '#dc2626' : '#16a34a'}
                        strokeWidth={2}
                        fill="url(#colorClose)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {/* Corporate Actions */}
            {detail.corporate_actions.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1.5">
                  <AlertTriangle size={14} className="text-amber-500" />
                  Corporate Actions
                </h3>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {detail.corporate_actions.slice(0, 20).map((action, i) => (
                    <div key={i} className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2 text-xs">
                      <span className="text-slate-500">{action.date}</span>
                      <span className={`font-medium capitalize ${action.type === 'split' ? 'text-purple-600' : 'text-blue-600'}`}>
                        {action.type}
                      </span>
                      <span className="text-slate-700">{String(action.value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="text-xs text-slate-400 pt-4 border-t border-slate-100">
              <p>Exchange: {detail.exchange ?? 'N/A'} | Currency: {detail.currency}</p>
              <p>Industry: {detail.industry ?? 'N/A'}</p>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center py-20 text-slate-400">
            No data available
          </div>
        )}
      </div>
    </div>
  );
}
