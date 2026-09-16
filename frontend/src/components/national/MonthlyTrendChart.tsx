import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';
import { TrendingUp, Info } from 'lucide-react';
import type { MonthlyTrendPoint, RegimeFilter } from '../../types/api';

interface MonthlyTrendChartProps {
  trendData: MonthlyTrendPoint[];
  currentRegime: RegimeFilter;
}

export const MonthlyTrendChart: React.FC<MonthlyTrendChartProps> = ({
  trendData,
  currentRegime,
}) => {
  // Format data for chart
  const formattedData = trendData.map((d) => {
    const [year, month] = d.report_month.split('-');
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const label = `${monthNames[parseInt(month, 10) - 1]} '${year.slice(2)}`;
    
    // Choose active score based on regime
    let activeScore = d.avg_risk_score;
    if (currentRegime === 'non_roads') {
      activeScore = d.non_roads_avg_risk_score ?? d.avg_risk_score;
    } else if (currentRegime === 'roads') {
      activeScore = d.roads_avg_risk_score ?? 0;
    }

    return {
      month: d.report_month,
      displayLabel: label,
      activeScore: Number(activeScore.toFixed(1)),
      nonRoadsScore: Number((d.non_roads_avg_risk_score ?? 11.4).toFixed(1)),
      combinedScore: Number(d.avg_risk_score.toFixed(1)),
      roadsScore: d.roads_avg_risk_score ? Number(d.roads_avg_risk_score.toFixed(1)) : null,
      activeWarnings: currentRegime === 'non_roads' ? d.non_roads_active_warnings : d.active_warnings,
    };
  });

  const latestScore = formattedData[formattedData.length - 1]?.activeScore ?? 0;
  const initialScore = formattedData[0]?.activeScore ?? 0;
  const netDelta = (latestScore - initialScore).toFixed(1);

  return (
    <div className="bg-bg-surface border border-border-hairline rounded-lg p-5 shadow-xs flex flex-col justify-between">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-border-hairline mb-3 gap-2">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-brand-primary" />
            <h2 className="text-[15px] font-bold text-text-primary">
              National Risk Trend — 13-Month Trajectory
            </h2>
          </div>
          <p className="text-[12px] text-text-secondary">
            {currentRegime === 'non_roads'
              ? 'Core Validated Portfolio average risk score (Stationary baseline, N=787)'
              : currentRegime === 'roads'
              ? 'Roads & Highways average risk score (Onboarded Dec 2025 backlog)'
              : 'Combined Portfolio average risk score (Subject to Dec 2025 compositional step)'}
          </p>
        </div>

        <div className="flex items-center gap-3 text-[11px] font-semibold">
          <span className="flex items-center gap-1.5 text-text-primary">
            <span className="w-3 h-1 bg-brand-primary rounded-xs"></span>
            {currentRegime === 'non_roads'
              ? 'Non-Roads Core'
              : currentRegime === 'roads'
              ? 'Roads Transfer'
              : 'Combined Portfolio'}
          </span>
          {currentRegime !== 'non_roads' && (
            <span className="flex items-center gap-1.5 text-text-muted">
              <span className="w-3 h-1 bg-slate-400 border-dashed rounded-xs"></span>
              Non-Roads Baseline (11.4)
            </span>
          )}
        </div>
      </div>

      {/* Composition Trap Warning Note if Combined is active */}
      {currentRegime === 'combined' && (
        <div className="mb-3 px-3 py-2 bg-amber-50/70 border border-amber-200/80 rounded flex items-center gap-2 text-[11px] text-amber-900">
          <Info className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span>
            <strong>Composition Alert:</strong> The upward step at Dec 2025 is an artifact of 1,013 Road projects onboarding mid-window (Simpson&apos;s paradox), not portfolio deterioration.
          </span>
        </div>
      )}

      {/* Chart Area */}
      <div className="w-full h-60 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stop-color={currentRegime === 'roads' ? '#E8730C' : '#0B4DA2'} stopOpacity={0.25} />
                <stop offset="95%" stop-color={currentRegime === 'roads' ? '#E8730C' : '#0B4DA2'} stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#DCE3EC" vertical={false} />
            <XAxis
              dataKey="displayLabel"
              stroke="#8A94A6"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#DCE3EC' }}
            />
            <YAxis
              domain={[0, currentRegime === 'roads' ? 25 : 20]}
              stroke="#8A94A6"
              fontSize={11}
              tickLine={false}
              axisLine={{ stroke: '#DCE3EC' }}
              tickFormatter={(v) => `${v}`}
            />
            <Tooltip
              content={({ active, payload, label }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  return (
                    <div className="bg-bg-surface p-3 border border-border-hairline rounded shadow-md text-[12px]">
                      <div className="font-bold text-text-primary mb-1">{data.month} ({label})</div>
                      <div className="text-brand-primary flex items-center justify-between gap-4">
                        <span>Avg Risk Score:</span>
                        <span className="font-bold tabular-nums">{data.activeScore}</span>
                      </div>
                      {currentRegime === 'combined' && (
                        <div className="text-text-secondary text-[11px] flex items-center justify-between gap-4 mt-0.5">
                          <span>Non-Roads Core:</span>
                          <span className="tabular-nums font-semibold">{data.nonRoadsScore}</span>
                        </div>
                      )}
                      <div className="text-risk-critical flex items-center justify-between gap-4 mt-1">
                        <span>Active Warnings:</span>
                        <span className="font-bold tabular-nums">{data.activeWarnings}</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            {currentRegime === 'combined' && (
              <ReferenceLine
                x="Dec '25"
                stroke="#C6362F"
                strokeDasharray="3 3"
                label={{ value: 'Roads Onboarded', position: 'top', fill: '#C6362F', fontSize: 10 }}
              />
            )}
            <Area
              type="monotone"
              dataKey="activeScore"
              stroke={currentRegime === 'roads' ? '#E8730C' : '#0B4DA2'}
              strokeWidth={2.5}
              fillOpacity={1}
              fill="url(#scoreGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-2 flex items-center justify-between text-[11px] text-text-secondary">
        <span>Window: July 2025 – July 2026 (13 Months Observed)</span>
        <span>
          Net trajectory change:{' '}
          <span className={`font-bold tabular-nums ${Number(netDelta) > 0 ? 'text-risk-critical' : 'text-risk-low'}`}>
            {Number(netDelta) >= 0 ? `+${netDelta}` : netDelta} pts
          </span>
        </span>
      </div>
    </div>
  );
};
