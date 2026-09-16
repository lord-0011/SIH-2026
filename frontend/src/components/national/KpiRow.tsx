import React from 'react';
import {
  FolderKanban,
  AlertTriangle,
  AlertOctagon,
  TrendingUp,
  CreditCard,
} from 'lucide-react';
import type { NationalSubSummary, BandDistribution } from '../../types/api';

interface KpiRowProps {
  summary: NationalSubSummary;
  combinedBands?: BandDistribution;
  isCombined?: boolean;
}

export const KpiRow: React.FC<KpiRowProps> = ({ summary }) => {
  const bands = summary.band_distribution;
  const totalCostLakhCr = (summary.total_cost_cr / 100000).toFixed(2);
  const totalExpLakhCr = (summary.total_expenditure_cr / 100000).toFixed(2);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      {/* Card 1: Total Ongoing Projects */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg p-4 flex flex-col justify-between shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[12px] font-semibold uppercase tracking-wider text-text-secondary">
            Total Ongoing Projects
          </span>
          <FolderKanban className="w-4 h-4 text-text-muted" />
        </div>
        <div className="my-2">
          <div className="text-[28px] font-bold text-text-primary tabular-nums">
            {summary.total_projects.toLocaleString()}
          </div>
        </div>
        <div className="text-[11px] text-text-secondary flex items-center gap-1">
          <span className="font-semibold text-brand-primary">100%</span> IPMD monitored cohort
        </div>
      </div>

      {/* Card 2: High-Risk Projects */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg p-4 flex flex-col justify-between shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[12px] font-semibold uppercase tracking-wider text-text-secondary">
            High-Risk Projects
          </span>
          <AlertTriangle className="w-4 h-4 text-risk-high" />
        </div>
        <div className="my-2">
          <div className="text-[28px] font-bold text-risk-high tabular-nums">
            {bands.HIGH.toLocaleString()}
          </div>
        </div>
        <div className="text-[11px] text-text-secondary">
          <span className="font-semibold text-risk-high">
            {summary.total_projects > 0 ? ((bands.HIGH / summary.total_projects) * 100).toFixed(1) : '0.0'}%
          </span> of active portfolio
        </div>
      </div>

      {/* Card 3: Critical-Risk Projects */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg p-4 flex flex-col justify-between shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[12px] font-semibold uppercase tracking-wider text-text-secondary">
            Critical-Risk Projects
          </span>
          <AlertOctagon className="w-4 h-4 text-risk-critical" />
        </div>
        <div className="my-2">
          <div className="text-[28px] font-bold text-risk-critical tabular-nums">
            {bands.CRITICAL.toLocaleString()}
          </div>
        </div>
        <div className="text-[11px] text-text-secondary">
          <span className="font-semibold text-risk-critical">
            {summary.total_projects > 0 ? ((bands.CRITICAL / summary.total_projects) * 100).toFixed(1) : '0.0'}%
          </span> of active portfolio
        </div>
      </div>

      {/* Card 4: Deteriorating This Month */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg p-4 flex flex-col justify-between shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[12px] font-semibold uppercase tracking-wider text-text-secondary">
            Deteriorating This Month
          </span>
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-risk-critical opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-risk-critical"></span>
          </span>
        </div>
        <div className="my-2 flex items-baseline gap-2">
          <div className="text-[28px] font-bold text-text-primary tabular-nums">
            {summary.active_warnings_count.toLocaleString()}
          </div>
          <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-risk-critical-bg text-risk-critical uppercase">
            Active
          </span>
        </div>
        <div className="text-[11px] font-semibold text-risk-critical flex items-center gap-1">
          <TrendingUp className="w-3.5 h-3.5" />
          Early-Warning Triggered
        </div>
      </div>

      {/* Card 5: Total Capital Outlay */}
      <div className="bg-bg-surface border border-border-hairline rounded-lg p-4 flex flex-col justify-between shadow-xs">
        <div className="flex items-center justify-between">
          <span className="text-[12px] font-semibold uppercase tracking-wider text-text-secondary">
            Total Capital Outlay
          </span>
          <CreditCard className="w-4 h-4 text-text-muted" />
        </div>
        <div className="my-2">
          <div className="text-[28px] font-bold text-text-primary tabular-nums">
            ₹ {totalCostLakhCr} <span className="text-[14px] font-normal text-text-secondary">L Cr</span>
          </div>
        </div>
        <div className="text-[11px] text-text-secondary truncate">
          ₹ {totalExpLakhCr} L Cr cumulative exp
        </div>
      </div>
    </div>
  );
};
