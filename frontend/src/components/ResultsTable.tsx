import { useState, useMemo } from 'react';
import type { ScanResponse } from '../types';
import { Sparkline } from './Sparkline';
import { formatNumber, formatMarketCap, returnColor, exportToCsv } from '../utils';
import { ArrowUpDown, ArrowDown, ArrowUp, Download, AlertTriangle, Info } from 'lucide-react';

type SortField = 'return_pct' | 'ticker' | 'name' | 'market_cap' | 'end_price' | 'sector';
type SortDir = 'asc' | 'desc';

interface ResultsTableProps {
  response: ScanResponse | null;
  onSelectStock: (ticker: string) => void;
}

export function ResultsTable({ response, onSelectStock }: ResultsTableProps) {
  const [sortField, setSortField] = useState<SortField>('return_pct');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir(field === 'return_pct' ? 'asc' : 'desc');
    }
  };

  const sorted = useMemo(() => {
    if (!response) return [];
    const items = [...response.results];
    items.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'return_pct':
          cmp = a.return_pct - b.return_pct;
          break;
        case 'ticker':
          cmp = a.ticker.localeCompare(b.ticker);
          break;
        case 'name':
          cmp = a.name.localeCompare(b.name);
          break;
        case 'market_cap':
          cmp = (a.market_cap ?? 0) - (b.market_cap ?? 0);
          break;
        case 'end_price':
          cmp = a.end_price - b.end_price;
          break;
        case 'sector':
          cmp = (a.sector ?? '').localeCompare(b.sector ?? '');
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return items;
  }, [response, sortField, sortDir]);

  if (!response) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-12 text-center">
        <div className="text-slate-400 mb-2">
          <Info size={40} className="mx-auto" />
        </div>
        <p className="text-slate-500 text-sm">Configure your scan parameters and click "Run Scan" to find drawdowns.</p>
      </div>
    );
  }

  const totalExcluded = Object.values(response.excluded).reduce((a, b) => a + b, 0);

  const handleExport = () => {
    exportToCsv(
      sorted.map((r) => ({
        Ticker: r.ticker,
        Name: r.name,
        'Return %': r.return_pct,
        'Start Price': r.start_price,
        'End Price': r.end_price,
        'Start Date': r.start_date,
        'End Date': r.end_date,
        Currency: r.currency,
        Sector: r.sector ?? '',
        Industry: r.industry ?? '',
        'Market Cap': r.market_cap ?? '',
        'Avg Volume': r.avg_volume ?? '',
      })),
      `drawdown-scan-${response.universe}-${response.as_of_session}.csv`
    );
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) return <ArrowUpDown size={12} className="text-slate-300" />;
    return sortDir === 'asc' ? <ArrowUp size={12} className="text-blue-600" /> : <ArrowDown size={12} className="text-blue-600" />;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200">
      {/* Stats Bar */}
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
        <div className="flex items-center gap-4 text-sm">
          <span className="font-semibold text-slate-800">
            {response.results.length} <span className="font-normal text-slate-500">matches</span>
          </span>
          <span className="text-slate-400">|</span>
          <span className="text-slate-500">
            {response.total_universe_size} in universe
          </span>
          {totalExcluded > 0 && (
            <>
              <span className="text-slate-400">|</span>
              <span className="text-amber-600 flex items-center gap-1">
                <AlertTriangle size={13} />
                {totalExcluded} excluded
              </span>
            </>
          )}
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">
            {response.start_session} to {response.as_of_session}
          </span>
          <button
            onClick={handleExport}
            className="flex items-center gap-1.5 text-sm text-slate-600 hover:text-blue-600 transition-colors"
          >
            <Download size={14} />
            CSV
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50/50">
              <Th field="ticker" label="Ticker" sortField={sortField} sortDir={sortDir} onSort={toggleSort} SortIcon={SortIcon} />
              <Th field="name" label="Company" sortField={sortField} sortDir={sortDir} onSort={toggleSort} SortIcon={SortIcon} />
              <Th field="return_pct" label="Return %" sortField={sortField} sortDir={sortDir} onSort={toggleSort} SortIcon={SortIcon} align="right" />
              <th className="px-4 py-2.5 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">Trend</th>
              <Th field="end_price" label="End Price" sortField={sortField} sortDir={sortDir} onSort={toggleSort} SortIcon={SortIcon} align="right" />
              <th className="px-4 py-2.5 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">Start Price</th>
              <Th field="sector" label="Sector" sortField={sortField} sortDir={sortDir} onSort={toggleSort} SortIcon={SortIcon} />
              <Th field="market_cap" label="Mkt Cap" sortField={sortField} sortDir={sortDir} onSort={toggleSort} SortIcon={SortIcon} align="right" />
            </tr>
          </thead>
          <tbody>
            {sorted.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-400">
                  No stocks match the current criteria.
                </td>
              </tr>
            ) : (
              sorted.map((item) => (
                <tr
                  key={item.ticker}
                  onClick={() => onSelectStock(item.ticker)}
                  className="border-b border-slate-50 hover:bg-blue-50/50 cursor-pointer transition-colors"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-800">{item.ticker}</span>
                      {item.data_warning && (
                        <span title={item.data_warning}><AlertTriangle size={13} className="text-amber-500" /></span>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-600 max-w-[200px] truncate">{item.name}</td>
                  <td className="px-4 py-3 text-right">
                    <span
                      className="inline-block font-bold px-2 py-0.5 rounded text-xs"
                      style={{
                        color: returnColor(item.return_pct),
                        backgroundColor: `${returnColor(item.return_pct)}12`,
                      }}
                    >
                      {item.return_pct > 0 ? '+' : ''}{formatNumber(item.return_pct)}%
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <Sparkline data={item.sparkline} />
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-slate-700">{formatNumber(item.end_price)}</td>
                  <td className="px-4 py-3 text-right font-mono text-slate-400">{formatNumber(item.start_price)}</td>
                  <td className="px-4 py-3 text-slate-500 text-xs">{item.sector ?? '—'}</td>
                  <td className="px-4 py-3 text-right text-slate-500 text-xs">{formatMarketCap(item.market_cap)}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

interface ThProps {
  field: SortField;
  label: string;
  sortField: SortField;
  sortDir: SortDir;
  onSort: (field: SortField) => void;
  SortIcon: React.ComponentType<{ field: SortField }>;
  align?: 'left' | 'right';
}

function Th({ field, label, onSort, SortIcon, align = 'left' }: ThProps) {
  return (
    <th
      className={`px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wider cursor-pointer hover:text-slate-700 select-none ${
        align === 'right' ? 'text-right' : 'text-left'
      }`}
      onClick={() => onSort(field)}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        <SortIcon field={field} />
      </span>
    </th>
  );
}
