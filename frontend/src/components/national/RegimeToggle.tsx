import React from 'react';
import { AlertCircle, AlertTriangle, CheckCircle2 } from 'lucide-react';
import type { RegimeFilter } from '../../types/api';

interface RegimeToggleProps {
  currentRegime: RegimeFilter;
  onRegimeChange: (regime: RegimeFilter) => void;
  nonRoadsCount?: number;
  roadsCount?: number;
  totalCount?: number;
}

export const RegimeToggle: React.FC<RegimeToggleProps> = ({
  currentRegime,
  onRegimeChange,
  nonRoadsCount = 787,
  roadsCount = 1013,
  totalCount = 1800,
}) => {
  return (
    <div className="space-y-3">
      {/* 3-Way Segmented Control */}
      <div className="inline-flex p-1 bg-bg-subtle border border-border-hairline rounded-lg shadow-xs">
        <button
          type="button"
          onClick={() => onRegimeChange('non_roads')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-[13px] font-semibold transition-all ${
            currentRegime === 'non_roads'
              ? 'bg-bg-surface text-brand-primary shadow-xs border border-border-hairline'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          <span>Non-Roads (Core Validated)</span>
          <span className={`text-[11px] px-1.5 py-0.5 rounded font-bold tabular-nums ${
            currentRegime === 'non_roads' ? 'bg-blue-50 text-brand-primary' : 'bg-bg-surface/70 text-text-muted'
          }`}>
            N={nonRoadsCount.toLocaleString()}
          </span>
        </button>

        <button
          type="button"
          onClick={() => onRegimeChange('roads')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-[13px] font-semibold transition-all ${
            currentRegime === 'roads'
              ? 'bg-bg-surface text-risk-high shadow-xs border border-border-hairline'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          <span>Roads & Highways (Transfer Regime)</span>
          <span className={`text-[11px] px-1.5 py-0.5 rounded font-bold tabular-nums ${
            currentRegime === 'roads' ? 'bg-amber-50 text-risk-high' : 'bg-bg-surface/70 text-text-muted'
          }`}>
            N={roadsCount.toLocaleString()}
          </span>
        </button>

        <button
          type="button"
          onClick={() => onRegimeChange('combined')}
          className={`flex items-center gap-2 px-3.5 py-1.5 rounded-md text-[13px] font-semibold transition-all ${
            currentRegime === 'combined'
              ? 'bg-bg-surface text-text-primary shadow-xs border border-border-hairline'
              : 'text-text-secondary hover:text-text-primary'
          }`}
        >
          <span>Combined Portfolio (All Sectors)</span>
          <span className={`text-[11px] px-1.5 py-0.5 rounded font-bold tabular-nums ${
            currentRegime === 'combined' ? 'bg-slate-100 text-text-primary' : 'bg-bg-surface/70 text-text-muted'
          }`}>
            N={totalCount.toLocaleString()}
          </span>
        </button>
      </div>

      {/* Synchronous Caveat Banners */}
      {currentRegime === 'roads' && (
        <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2.5 text-amber-900 text-[12px] animate-fadeIn">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-bold">Transfer Regime Caveat: </span>
            Roads & Highways projects were onboarded in Dec 2025 with expired backlog dates and reporting gaps. 
            Interpret scores with caution; high risk ratings reflect historical reporting latency rather than confirmed structural failure.
          </div>
        </div>
      )}

      {currentRegime === 'combined' && (
        <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg flex items-start gap-2.5 text-blue-900 text-[12px] animate-fadeIn">
          <AlertCircle className="w-4 h-4 text-brand-primary shrink-0 mt-0.5" />
          <div className="leading-relaxed">
            <span className="font-bold">Combined Portfolio Advisory: </span>
            Includes 1,013 Road Transport projects onboarded in Dec 2025 under the transfer regime. 
            National headline validated benchmarks are derived from the Non-Roads core to prevent Simpson&apos;s paradox composition distortion.
          </div>
        </div>
      )}

      {currentRegime === 'non_roads' && (
        <div className="p-2.5 bg-green-50/60 border border-green-200/80 rounded-lg flex items-center gap-2 text-green-900 text-[12px] animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 text-risk-low shrink-0" />
          <span>
            <strong className="font-semibold">Core Validated Benchmark:</strong> 13-month stationary monitoring baseline across Railways, Power, Petroleum, Urban Dev & other non-road sectors.
          </span>
        </div>
      )}
    </div>
  );
};
