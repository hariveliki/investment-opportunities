import { useState, useEffect } from 'react';
import type { SavedScan, ScanConfig } from '../types';
import { Bookmark, Trash2, Play, Copy, Check } from 'lucide-react';

const STORAGE_KEY = 'equity-scanner-saved-scans';

function loadScans(): SavedScan[] {
  try {
    const data = localStorage.getItem(STORAGE_KEY);
    return data ? JSON.parse(data) : [];
  } catch {
    return [];
  }
}

function saveScans(scans: SavedScan[]): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(scans));
}

interface SavedScansProps {
  currentConfig: ScanConfig;
  onLoad: (config: ScanConfig) => void;
  saveTrigger: number;
}

export function SavedScans({ currentConfig, onLoad, saveTrigger }: SavedScansProps) {
  const [scans, setScans] = useState<SavedScan[]>(loadScans());
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [saveName, setSaveName] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (saveTrigger > 0) {
      setShowSaveDialog(true);
      setSaveName('');
    }
  }, [saveTrigger]);

  const handleSave = () => {
    if (!saveName.trim()) return;
    const newScan: SavedScan = {
      id: Date.now().toString(),
      name: saveName.trim(),
      config: { ...currentConfig },
      created_at: new Date().toISOString(),
    };
    const updated = [newScan, ...scans];
    setScans(updated);
    saveScans(updated);
    setShowSaveDialog(false);
    setSaveName('');
  };

  const handleDelete = (id: string) => {
    const updated = scans.filter((s) => s.id !== id);
    setScans(updated);
    saveScans(updated);
  };

  const handleCopyLink = (scan: SavedScan) => {
    const params = new URLSearchParams();
    Object.entries(scan.config).forEach(([key, value]) => {
      if (value != null && value !== '') params.set(key, String(value));
    });
    const url = `${window.location.origin}?${params.toString()}`;
    navigator.clipboard.writeText(url);
    setCopiedId(scan.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (scans.length === 0 && !showSaveDialog) return null;

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-5">
      <div className="flex items-center gap-2 mb-3">
        <Bookmark size={16} className="text-blue-600" />
        <h3 className="text-sm font-semibold text-slate-700">Saved Scans</h3>
      </div>

      {showSaveDialog && (
        <div className="mb-3 p-3 bg-blue-50 rounded-lg">
          <input
            type="text"
            value={saveName}
            onChange={(e) => setSaveName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSave()}
            placeholder="Name this scan..."
            autoFocus
            className="w-full rounded-md border border-blue-200 px-3 py-1.5 text-sm mb-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!saveName.trim()}
              className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white text-xs font-medium py-1.5 rounded-md transition-colors"
            >
              Save
            </button>
            <button
              onClick={() => setShowSaveDialog(false)}
              className="flex-1 bg-slate-200 hover:bg-slate-300 text-slate-600 text-xs font-medium py-1.5 rounded-md transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="space-y-1.5 max-h-60 overflow-y-auto">
        {scans.map((scan) => (
          <div
            key={scan.id}
            className="flex items-center justify-between p-2.5 rounded-lg hover:bg-slate-50 group transition-colors"
          >
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-slate-700 truncate">{scan.name}</div>
              <div className="text-xs text-slate-400">
                {scan.config.universe} | {scan.config.horizon} | {scan.config.threshold_pct}%
              </div>
            </div>
            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => onLoad(scan.config)}
                className="p-1 rounded hover:bg-blue-100 text-blue-500"
                title="Load scan"
              >
                <Play size={13} />
              </button>
              <button
                onClick={() => handleCopyLink(scan)}
                className="p-1 rounded hover:bg-slate-200 text-slate-400"
                title="Copy link"
              >
                {copiedId === scan.id ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
              </button>
              <button
                onClick={() => handleDelete(scan.id)}
                className="p-1 rounded hover:bg-red-100 text-red-400"
                title="Delete"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
