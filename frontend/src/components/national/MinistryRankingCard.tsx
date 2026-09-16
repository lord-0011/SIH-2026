import React from 'react';
import { Landmark } from 'lucide-react';
import type { RegimeMinistryItem, RegimeFilter } from '../../types/api';

interface MinistryRankingCardProps {
  ministries: RegimeMinistryItem[];
  currentRegime: RegimeFilter;
}

export const MinistryRankingCard: React.FC<MinistryRankingCardProps> = ({
  ministries,
}) => {
  // Sort by active warnings descending, then avg_risk_score descending
  const sortedMinistries = [...ministries]
    .sort((a, b) => b.active_warnings - a.active_warnings || b.avg_risk_score - a.avg_risk_score)
    .slice(0, 8); // Top 8

  return (
    <div className="bg-bg-surface border border-border-hairline rounded-lg p-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-border-hairline mb-3">
        <div>
          <div className="flex items-center gap-2">
            <Landmark className="w-5 h-5 text-brand-primary" />
            <h2 className="text-[15px] font-bold text-text-primary">
              Ministry Escalation Index
            </h2>
          </div>
          <p className="text-[12px] text-text-secondary">Ranked by aggregate project deterioration alerts</p>
        </div>
        <span className="px-2 py-0.5 rounded bg-bg-subtle text-text-secondary text-[11px] font-bold">
          Top Escalations
        </span>
      </div>

      <div className="divide-y divide-border-hairline max-h-80 overflow-y-auto pr-1">
        {sortedMinistries.length === 0 ? (
          <div className="text-center py-6 text-text-muted text-[13px]">
            No ministry records for the active slice.
          </div>
        ) : (
          sortedMinistries.map((m, idx) => {
            const isRoad = m.ministry.toLowerCase().includes('road');
            const isCrit = m.avg_risk_score >= 40 || m.critical_count > 10;
            const isHigh = m.avg_risk_score >= 20 || m.critical_count > 5;

            return (
              <div key={m.ministry} className="py-2.5 flex items-center justify-between group">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="w-5 text-center text-[12px] font-bold text-text-muted">
                    {idx + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[13px] font-semibold text-text-primary group-hover:text-brand-primary transition-colors truncate">
                        {m.ministry}
                      </span>
                      {isRoad && (
                        <span className="text-[9px] font-bold uppercase px-1 py-0.2 bg-amber-100 text-amber-800 rounded">
                          Transfer
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] text-text-muted truncate">
                      {m.total_projects} projects • {m.critical_count} critical
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2.5 shrink-0">
                  <span className="text-[11px] text-risk-critical font-bold tabular-nums">
                    {m.active_warnings} alerts
                  </span>
                  <span
                    className={`px-2 py-0.5 rounded text-[12px] font-bold tabular-nums ${
                      isCrit
                        ? 'bg-risk-critical-bg text-risk-critical'
                        : isHigh
                        ? 'bg-risk-high-bg text-risk-high'
                        : 'bg-bg-subtle text-text-secondary'
                    }`}
                  >
                    {m.avg_risk_score.toFixed(1)}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
