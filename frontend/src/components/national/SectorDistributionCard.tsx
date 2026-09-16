import React from 'react';
import { Layers } from 'lucide-react';
import type { RegimeSectorItem, RegimeFilter } from '../../types/api';

interface SectorDistributionCardProps {
  sectors: RegimeSectorItem[];
  currentRegime: RegimeFilter;
}

export const SectorDistributionCard: React.FC<SectorDistributionCardProps> = ({
  sectors,
  currentRegime,
}) => {
  // Sort sectors by active_warnings desc, then total_projects desc
  const sortedSectors = [...sectors].sort((a, b) => b.active_warnings - a.active_warnings || b.total_projects - a.total_projects);

  return (
    <div className="bg-bg-surface border border-border-hairline rounded-lg p-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-border-hairline mb-3">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-brand-primary" />
          <h2 className="text-[15px] font-bold text-text-primary">
            Risk Distribution by Sector
          </h2>
        </div>
        <span className="text-[11px] text-text-muted">
          High + Critical Count • {currentRegime === 'non_roads' ? 'Non-Roads' : currentRegime === 'roads' ? 'Roads' : 'All Sectors'}
        </span>
      </div>

      <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
        {sortedSectors.length === 0 ? (
          <div className="text-center py-6 text-text-muted text-[13px]">
            No sector records for the active regime slice.
          </div>
        ) : (
          sortedSectors.map((s) => {
            const isRoad = s.sector.toLowerCase().includes('road');
            const totalHighCritical = s.critical_count + s.high_count;
            const highCritPct = s.total_projects > 0 ? (totalHighCritical / s.total_projects) * 100 : 0;
            const critPct = s.total_projects > 0 ? (s.critical_count / s.total_projects) * 100 : 0;
            const otherPct = Math.max(0, 100 - highCritPct);

            return (
              <div key={s.sector} className="space-y-1 group">
                <div className="flex items-center justify-between text-[13px]">
                  <div className="flex items-center gap-1.5 min-w-0">
                    <span className="font-semibold text-text-primary group-hover:text-brand-primary transition-colors truncate">
                      {s.sector}
                    </span>
                    {isRoad && (
                      <span className="text-[9px] font-bold uppercase px-1 py-0.2 bg-amber-100 text-amber-800 rounded">
                        Transfer Regime
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <span className="text-[11px] font-semibold text-risk-critical tabular-nums">
                      {s.critical_count} <span className="text-text-muted font-normal">crit</span>
                    </span>
                    <span className="text-[11px] text-text-muted tabular-nums">
                      / {s.total_projects} total
                    </span>
                  </div>
                </div>

                {/* Progress Mini Bar */}
                <div className="h-2 w-full bg-bg-subtle rounded overflow-hidden flex">
                  <div
                    className="bg-risk-critical h-full transition-all"
                    style={{ width: `${critPct}%` }}
                    title={`Critical: ${s.critical_count}`}
                  />
                  <div
                    className="bg-risk-high h-full transition-all"
                    style={{ width: `${highCritPct - critPct}%` }}
                    title={`High: ${s.high_count}`}
                  />
                  <div
                    className="bg-risk-low h-full opacity-60 transition-all"
                    style={{ width: `${otherPct}%` }}
                    title={`Low/Medium: ${s.total_projects - totalHighCritical}`}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
