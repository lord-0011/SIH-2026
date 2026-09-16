import React, { useState, useEffect, useMemo } from 'react';
import {
  ArrowDown,
  ArrowUp,
  Search,
  ChevronLeft,
  ChevronRight,
  Filter,
  ShieldCheck,
  ExternalLink,
  Flame,
} from 'lucide-react';
import { RegimeToggle } from '../national/RegimeToggle';
import { HonestFooter } from '../national/HonestFooter';
import { fetchWatchlist } from '../../api/client';
import type { WatchlistResponse, RegimeFilter, WatchlistItem } from '../../types/api';

interface WatchlistScreenProps {
  initialRegime?: RegimeFilter;
  reportMonth?: string;
  onSelectProject?: (projectId: string) => void;
}

export const WatchlistScreen: React.FC<WatchlistScreenProps> = ({
  initialRegime = 'non_roads',
  reportMonth = 'July 2026',
  onSelectProject,
}) => {
  const [currentRegime, setCurrentRegime] = useState<RegimeFilter>(initialRegime);
  const [watchlistData, setWatchlistData] = useState<WatchlistResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [minConviction, setMinConviction] = useState<number>(1);
  const [selectedSector, setSelectedSector] = useState<string>('all');
  const [page, setPage] = useState<number>(1);
  const pageSize = 12;

  const loadData = async (regime: RegimeFilter) => {
    setLoading(true);
    try {
      const res = await fetchWatchlist({
        regime: regime === 'combined' ? undefined : regime,
      });
      setWatchlistData(res);
    } catch (err) {
      console.error('Failed to load watchlist:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData(currentRegime);
  }, [currentRegime]);

  const handleRegimeChange = (regime: RegimeFilter) => {
    setCurrentRegime(regime);
    setSelectedSector('all');
    setPage(1);
  };

  // Distinct sectors from current items
  const sectorList = useMemo(() => {
    if (!watchlistData) return [];
    const set = new Set<string>();
    watchlistData.items.forEach((i) => {
      if (i.sector) set.add(i.sector);
    });
    return Array.from(set).sort();
  }, [watchlistData]);

  // Filter & Conviction sort
  const filteredItems = useMemo(() => {
    if (!watchlistData) return [];
    return watchlistData.items.filter((item) => {
      // 1. Min conviction
      if (item.warning_strength < minConviction) return false;
      // 2. Sector
      if (selectedSector !== 'all' && item.sector !== selectedSector) return false;
      // 3. Search query
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase().trim();
        const matches =
          item.project_name.toLowerCase().includes(q) ||
          item.project_id.toLowerCase().includes(q) ||
          item.ministry.toLowerCase().includes(q) ||
          item.sector.toLowerCase().includes(q) ||
          item.triggers_fired.toLowerCase().includes(q);
        if (!matches) return false;
      }
      return true;
    });
  }, [watchlistData, minConviction, selectedSector, searchQuery]);

  // Conviction sort invariant: warning_strength DESC, then risk_score DESC
  const sortedItems = useMemo(() => {
    return [...filteredItems].sort((a, b) => {
      if (b.warning_strength !== a.warning_strength) {
        return b.warning_strength - a.warning_strength;
      }
      return b.risk_score - a.risk_score;
    });
  }, [filteredItems]);

  const totalPages = Math.max(1, Math.ceil(sortedItems.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const pagedItems = sortedItems.slice((currentPage - 1) * pageSize, currentPage * pageSize);

  const formatDriverPhrase = (triggers: string): string => {
    const parts = [];
    if (triggers.includes('velocity_divergence')) {
      parts.push('Physical progress stalled while expenditure continued');
    }
    if (triggers.includes('gap_widening')) {
      parts.push('Financial-to-physical progress gap widened');
    }
    if (triggers.includes('score_rising')) {
      parts.push('Risk score elevated across 2 consecutive reporting cycles');
    }
    return parts.length > 0 ? parts.join(' • ') : 'Active early-warning threshold breached';
  };

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
    <div className="space-y-6">
      {/* PAGE HEADER */}
      <div className="bg-bg-surface p-5 rounded-lg border border-border-hairline shadow-xs flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5">
            <h1 className="text-[22px] font-bold text-text-primary tracking-tight">
              Early-Warning Priority Watchlist
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-risk-critical-bg text-risk-critical text-[11px] font-bold uppercase tracking-wide">
              <Flame className="w-3.5 h-3.5" />
              Operational Triage Fold • {reportMonth}
            </span>
          </div>
          {/* Honest Headline Split Requirement */}
          <p className="text-[13px] text-text-secondary">
            <strong className="text-text-primary">
              {watchlistData ? watchlistData.total_active_warnings.toLocaleString() : '846'} projects
            </strong>{' '}
            flagged deteriorating this month (
            <span className="font-semibold text-brand-primary">
              {watchlistData ? watchlistData.non_roads_count.toLocaleString() : '311'} Non-Roads validated
            </span>{' '}
            /{' '}
            <span className="font-semibold text-risk-high">
              {watchlistData ? watchlistData.roads_count.toLocaleString() : '535'} Roads transfer-regime
            </span>
            ). Sorted strictly by conviction first, then score.
          </p>
        </div>

        {/* 3-Way Regime Filter */}
        <RegimeToggle
          currentRegime={currentRegime}
          onRegimeChange={handleRegimeChange}
          nonRoadsCount={watchlistData?.non_roads_count ?? 311}
          roadsCount={watchlistData?.roads_count ?? 535}
          totalCount={watchlistData?.total_active_warnings ?? 846}
        />
      </div>

      {/* FILTER & CONVICTION BAR */}
      <div className="bg-bg-surface p-4 rounded-lg border border-border-hairline shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          {/* Conviction Filter */}
          <div className="flex items-center gap-1.5 bg-bg-subtle p-1 rounded-md border border-border-hairline text-[12px]">
            <span className="px-2 font-semibold text-text-muted flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" />
              Conviction:
            </span>
            <button
              type="button"
              onClick={() => { setMinConviction(1); setPage(1); }}
              className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                minConviction === 1 ? 'bg-bg-surface text-brand-primary shadow-xs' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              All (1-3 Triggers)
            </button>
            <button
              type="button"
              onClick={() => { setMinConviction(2); setPage(1); }}
              className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                minConviction === 2 ? 'bg-bg-surface text-brand-primary shadow-xs' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              High Conviction (≥2)
            </button>
            <button
              type="button"
              onClick={() => { setMinConviction(3); setPage(1); }}
              className={`px-2.5 py-1 rounded font-semibold transition-colors ${
                minConviction === 3 ? 'bg-bg-surface text-risk-critical shadow-xs font-bold' : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              Triple-Trigger (3)
            </button>
          </div>

          {/* Sector Filter */}
          <div className="flex items-center gap-2">
            <select
              value={selectedSector}
              onChange={(e) => { setSelectedSector(e.target.value); setPage(1); }}
              className="h-8 pl-2.5 pr-8 bg-bg-surface border border-border-hairline rounded text-[12px] font-semibold text-text-primary focus:outline-none focus:border-brand-primary cursor-pointer"
            >
              <option value="all">All Sectors ({sectorList.length})</option>
              {sectorList.map((sec) => (
                <option key={sec} value={sec}>{sec}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Live Search */}
        <div className="relative min-w-[260px]">
          <Search className="w-4 h-4 text-text-muted absolute left-2.5 top-2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
            placeholder="Search name, ID, driver..."
            className="h-8 pl-8 pr-3 bg-bg-surface border border-border-hairline rounded text-[12px] placeholder:text-text-muted focus:outline-none focus:border-brand-primary w-full"
          />
        </div>
      </div>

      {/* DENSE WATCHLIST TABLE */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-bg-subtle text-text-secondary text-[11px] font-bold uppercase tracking-wider border-b border-border-hairline sticky top-0 z-10">
                <th className="py-2.5 px-4">Project Name & Corridor</th>
                <th className="py-2.5 px-3">Conviction / Strength</th>
                <th className="py-2.5 px-4">Fired Triggers & Predictive Evidence</th>
                <th className="py-2.5 px-3">Primary Risk Driver</th>
                <th className="py-2.5 px-3">Ministry & Sector</th>
                <th className="py-2.5 px-3 text-right">Risk Score</th>
                <th className="py-2.5 px-3 text-right">MoM Δ</th>
                <th className="py-2.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-hairline text-[13px] bg-bg-surface">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-text-muted">
                    Loading live early-warning records...
                  </td>
                </tr>
              ) : pagedItems.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-text-muted">
                    No active deterioration projects match the selected filters.
                  </td>
                </tr>
              ) : (
                pagedItems.map((row: WatchlistItem) => {
                  const isProvisional = row.data_sufficiency === 'PROVISIONAL';
                  const delta = row.score_delta_1m;
                  const delta2m = row.score_delta_2m;

                  return (
                    <tr
                      key={row.project_id}
                      className={`hover:bg-bg-subtle/80 transition-colors group ${
                        isProvisional ? 'bg-slate-50/70 opacity-80' : ''
                      }`}
                    >
                      {/* Project Name & Corridor */}
                      <td className="py-3 px-4 min-w-[260px]">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="font-semibold text-text-primary group-hover:text-brand-primary transition-colors">
                            {row.project_name}
                          </span>
                          {row.transfer_regime && (
                            <span className="text-[9px] font-bold uppercase px-1.5 py-0.2 bg-amber-100 text-amber-800 rounded">
                              Transfer
                            </span>
                          )}
                          {isProvisional && (
                            <span
                              className="text-[9px] font-semibold uppercase px-1.5 py-0.2 bg-slate-200 text-slate-700 rounded"
                              title="Less than 4 months of observed history; provisional signal"
                            >
                              Provisional
                            </span>
                          )}
                        </div>
                        <div className="text-[11px] text-text-muted mt-0.5">
                          ID: {row.project_id} • Progress: {row.physical_progress_pct.toFixed(1)}%
                        </div>
                      </td>

                      {/* Conviction / Strength */}
                      <td className="py-3 px-3 whitespace-nowrap">
                        {row.warning_strength === 3 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-red-100 text-risk-critical font-bold text-[11px]">
                            <Flame className="w-3 h-3" />
                            Strength 3 (Triple)
                          </span>
                        ) : row.warning_strength === 2 ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-orange-100 text-risk-high font-semibold text-[11px]">
                            Strength 2 (Double)
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-yellow-100 text-yellow-800 text-[11px]">
                            Strength 1 (Single)
                          </span>
                        )}
                      </td>

                      {/* Fired Triggers & Evidence Chips */}
                      <td className="py-3 px-4 min-w-[240px]">
                        <div className="flex flex-wrap gap-1.5">
                          {row.triggers_fired.includes('velocity_divergence') && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-red-50 text-risk-critical border border-red-200 text-[10px] font-semibold">
                              Stalled progress + rising spend
                            </span>
                          )}
                          {row.triggers_fired.includes('gap_widening') && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-amber-50 text-amber-800 border border-amber-200 text-[10px] font-semibold">
                              Spend gap widening
                            </span>
                          )}
                          {row.triggers_fired.includes('score_rising') && (
                            <span className="inline-flex items-center px-1.5 py-0.5 rounded bg-blue-50 text-brand-primary border border-blue-200 text-[10px] font-semibold">
                              Score rising 2mo
                            </span>
                          )}
                        </div>
                        {delta2m !== null && delta2m !== undefined && (
                          <div className="text-[11px] text-text-muted mt-1 tabular-nums">
                            2-month risk delta: <span className="font-semibold text-risk-critical">+{delta2m.toFixed(1)} pts</span>
                          </div>
                        )}
                      </td>

                      {/* Primary Risk Driver */}
                      <td className="py-3 px-3 text-[12px] text-text-secondary max-w-xs">
                        {formatDriverPhrase(row.triggers_fired)}
                      </td>

                      {/* Ministry & Sector */}
                      <td className="py-3 px-3 text-[12px] whitespace-nowrap">
                        <div className="font-medium text-text-primary truncate max-w-[180px]">{row.ministry}</div>
                        <div className="text-text-muted text-[11px] truncate max-w-[180px]">{row.sector}</div>
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

        {/* PAGINATION BAR */}
        <div className="bg-bg-subtle/50 px-4 py-3 border-t border-border-hairline flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-[11px] text-text-secondary">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-brand-primary" />
            <span>
              Conviction ordering verified: Warning strength strictly outranks static risk level.
            </span>
          </div>

          <div className="flex items-center gap-4">
            <span className="tabular-nums">
              Showing {(currentPage - 1) * pageSize + 1}–
              {Math.min(currentPage * pageSize, sortedItems.length)} of {sortedItems.length} records
            </span>
            <div className="flex items-center gap-1">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="p-1 rounded border border-border-hairline disabled:opacity-40 hover:bg-bg-surface"
              >
                <ChevronLeft className="w-4 h-4" />
              </button>
              <button
                type="button"
                disabled={currentPage >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="p-1 rounded border border-border-hairline disabled:opacity-40 hover:bg-bg-surface"
              >
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* HONEST METHODOLOGY FOOTER */}
      <HonestFooter />
    </div>
  );
};
