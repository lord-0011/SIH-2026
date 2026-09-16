import React, { useState } from 'react';
import {
  AlertTriangle,
  ArrowDown,
  ArrowUp,
  Search,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import type { WatchlistItem } from '../../types/api';

interface WatchlistTableProps {
  items: WatchlistItem[];
  totalActiveWarnings: number;
  reportMonth: string;
  onSelectProject?: (projectId: string) => void;
}

export const WatchlistTable: React.FC<WatchlistTableProps> = ({
  items,
  totalActiveWarnings,
  onSelectProject,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 8;

  // Filter items
  const filteredItems = items.filter((item) => {
    const q = searchQuery.toLowerCase().trim();
    if (!q) return true;
    return (
      item.project_name.toLowerCase().includes(q) ||
      item.project_id.toLowerCase().includes(q) ||
      item.ministry.toLowerCase().includes(q) ||
      item.sector.toLowerCase().includes(q) ||
      item.triggers_fired.toLowerCase().includes(q)
    );
  });

  const totalPages = Math.max(1, Math.ceil(filteredItems.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIdx = (currentPage - 1) * pageSize;
  const pageItems = filteredItems.slice(startIdx, startIdx + pageSize);

  const getBandBadgeClass = (band: string) => {
    switch (band) {
      case 'CRITICAL':
        return 'bg-risk-critical-bg text-risk-critical';
      case 'HIGH':
        return 'bg-risk-high-bg text-risk-high';
      case 'MEDIUM':
        return 'bg-risk-medium-bg text-risk-medium';
      case 'LOW':
      default:
        return 'bg-risk-low-bg text-risk-low';
    }
  };

  return (
    <div className="bg-bg-surface border border-border-hairline rounded-lg shadow-xs overflow-hidden">
      {/* Table Header Controls */}
      <div className="p-5 border-b border-border-hairline flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-critical animate-pulse"></span>
            <h2 className="text-[16px] font-bold text-text-primary">
              Priority Triage Watchlist — Highest Deterioration Velocity
            </h2>
          </div>
          <p className="text-[12px] text-text-secondary mt-0.5">
            Showing flagged projects with active early-warning signals ({filteredItems.length} matching / {totalActiveWarnings} active alerts)
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="relative">
            <Search className="w-4 h-4 text-text-muted absolute left-2.5 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search project, ID, driver..."
              className="h-8 pl-8 pr-3 bg-bg-surface border border-border-hairline rounded text-[12px] placeholder:text-text-muted focus:outline-none focus:border-brand-primary focus:ring-1 focus:ring-brand-primary w-64"
            />
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-bg-subtle text-text-secondary text-[11px] font-bold uppercase tracking-wider border-b border-border-hairline">
              <th className="py-2.5 px-4">Project Name & ID</th>
              <th className="py-2.5 px-3">Nodal Ministry</th>
              <th className="py-2.5 px-3">Sector</th>
              <th className="py-2.5 px-3 text-right">Risk Score</th>
              <th className="py-2.5 px-3 text-right">MoM Δ</th>
              <th className="py-2.5 px-4">Early-Warning Triggers & Drivers</th>
              <th className="py-2.5 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border-hairline text-[13px] bg-bg-surface">
            {pageItems.length === 0 ? (
              <tr>
                <td colSpan={7} className="py-8 text-center text-text-muted">
                  No early-warning projects match your query.
                </td>
              </tr>
            ) : (
              pageItems.map((row) => {
                const isProvisional = row.data_sufficiency === 'PROVISIONAL';
                const delta = row.score_delta_1m;

                return (
                  <tr
                    key={row.project_id}
                    className={`hover:bg-bg-subtle/80 transition-colors group ${
                      isProvisional ? 'bg-slate-50/50 opacity-90' : ''
                    }`}
                  >
                    {/* Project Name */}
                    <td className="py-3 px-4 min-w-[240px]">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-text-primary group-hover:text-brand-primary transition-colors">
                          {row.project_name}
                        </span>
                        {row.transfer_regime && (
                          <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 bg-amber-100 text-amber-800 rounded">
                            Transfer
                          </span>
                        )}
                        {isProvisional && (
                          <span className="text-[9px] font-semibold uppercase px-1.5 py-0.2 bg-slate-200 text-slate-700 rounded">
                            Provisional
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-text-muted">
                        ID: {row.project_id} • Progress: {row.physical_progress_pct.toFixed(1)}%
                      </div>
                    </td>

                    {/* Ministry */}
                    <td className="py-3 px-3 text-text-secondary whitespace-nowrap">
                      {row.ministry}
                    </td>

                    {/* Sector */}
                    <td className="py-3 px-3 text-text-secondary whitespace-nowrap">
                      {row.sector}
                    </td>

                    {/* Risk Score */}
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      <div className="inline-flex items-center gap-1.5">
                        <span className="font-bold tabular-nums text-[14px]">
                          {row.risk_score.toFixed(1)}
                        </span>
                        <span
                          className={`px-1.5 py-0.5 rounded text-[10px] font-bold uppercase ${getBandBadgeClass(
                            row.risk_band
                          )}`}
                        >
                          {row.risk_band}
                        </span>
                      </div>
                    </td>

                    {/* MoM Delta */}
                    <td className="py-3 px-3 text-right whitespace-nowrap">
                      {delta !== null && delta !== undefined ? (
                        <span
                          className={`inline-flex items-center gap-0.5 font-bold tabular-nums text-[12px] ${
                            delta > 0
                              ? 'text-risk-critical'
                              : delta < 0
                              ? 'text-risk-low'
                              : 'text-text-muted'
                          }`}
                        >
                          {delta > 0 ? (
                            <ArrowUp className="w-3.5 h-3.5" />
                          ) : delta < 0 ? (
                            <ArrowDown className="w-3.5 h-3.5" />
                          ) : null}
                          {delta > 0 ? `+${delta.toFixed(1)}` : delta.toFixed(1)}
                        </span>
                      ) : (
                        <span className="text-text-muted tabular-nums">—</span>
                      )}
                    </td>

                    {/* Drivers / Triggers */}
                    <td className="py-3 px-4 text-text-secondary text-[12px] max-w-xs">
                      <div className="flex flex-wrap gap-1">
                        {row.triggers_fired ? (
                          row.triggers_fired.split(',').map((t, i) => (
                            <span
                              key={i}
                              className="inline-block px-1.5 py-0.5 rounded bg-red-50 text-risk-critical border border-red-100 text-[10px] font-semibold"
                            >
                              {t.trim()}
                            </span>
                          ))
                        ) : (
                          <span className="text-text-muted">Early warning threshold met</span>
                        )}
                      </div>
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <button
                        type="button"
                        onClick={() => onSelectProject?.(row.project_id)}
                        className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-border-hairline hover:border-brand-primary hover:text-brand-primary text-text-primary bg-bg-surface hover:bg-bg-subtle transition-colors text-[11px] font-semibold"
                      >
                        <span>Triage Dossier</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Controls */}
      <div className="bg-bg-subtle/50 px-4 py-3 border-t border-border-hairline flex items-center justify-between text-[11px] text-text-secondary">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-3.5 h-3.5 text-risk-critical" />
          <span>Active deterioration alerts synchronized via IPMD OCMS pipeline.</span>
        </div>

        <div className="flex items-center gap-3">
          <span className="tabular-nums">
            Page {currentPage} of {totalPages} ({filteredItems.length} records)
          </span>
          <div className="flex items-center gap-1">
            <button
              type="button"
              disabled={currentPage <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              className="p-1 rounded border border-border-hairline disabled:opacity-40 hover:bg-bg-surface"
            >
              <ChevronLeft className="w-3.5 h-3.5" />
            </button>
            <button
              type="button"
              disabled={currentPage >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              className="p-1 rounded border border-border-hairline disabled:opacity-40 hover:bg-bg-surface"
            >
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
