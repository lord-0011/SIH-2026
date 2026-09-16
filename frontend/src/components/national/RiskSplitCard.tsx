import React from 'react';
import { PieChart } from 'lucide-react';
import type { BandDistribution } from '../../types/api';

interface RiskSplitCardProps {
  bands: BandDistribution;
  totalProjects: number;
  totalCostCr: number;
  regimeTitle: string;
}

export const RiskSplitCard: React.FC<RiskSplitCardProps> = ({
  bands,
  totalProjects,
  totalCostCr,
  regimeTitle,
}) => {
  const n = totalProjects > 0 ? totalProjects : 1;
  const pLow = ((bands.LOW / n) * 100).toFixed(1);
  const pMed = ((bands.MEDIUM / n) * 100).toFixed(1);
  const pHigh = ((bands.HIGH / n) * 100).toFixed(1);
  const pCrit = ((bands.CRITICAL / n) * 100).toFixed(1);

  // Approximate cost breakdown proportional to band project counts
  const costPerProj = totalProjects > 0 ? (totalCostCr / totalProjects) / 100000 : 0;
  const cLow = (bands.LOW * costPerProj).toFixed(2);
  const cMed = (bands.MEDIUM * costPerProj).toFixed(2);
  const cHigh = (bands.HIGH * costPerProj).toFixed(2);
  const cCrit = (bands.CRITICAL * costPerProj).toFixed(2);

  return (
    <div className="bg-bg-surface border border-border-hairline rounded-lg p-5 shadow-xs">
      <div className="flex items-center justify-between pb-3 border-b border-border-hairline mb-4">
        <div className="flex items-center gap-2">
          <PieChart className="w-5 h-5 text-brand-primary" />
          <h2 className="text-[15px] font-bold text-text-primary">
            Portfolio Risk Split ({regimeTitle} — {totalProjects.toLocaleString()} Projects)
          </h2>
        </div>
        <span className="text-[11px] text-text-muted">Calibrated Band Distribution</span>
      </div>

      {/* Stacked Segmented Bar */}
      <div className="w-full h-7 rounded bg-bg-subtle overflow-hidden flex border border-border-hairline mb-4">
        <div
          className="h-full bg-risk-low flex items-center justify-center text-white text-[11px] font-bold tabular-nums transition-all"
          style={{ width: `${pLow}%` }}
          title={`Low Risk: ${bands.LOW} (${pLow}%)`}
        >
          {Number(pLow) >= 5 ? `${pLow}%` : ''}
        </div>
        <div
          className="h-full bg-risk-medium flex items-center justify-center text-white text-[11px] font-bold tabular-nums transition-all"
          style={{ width: `${pMed}%` }}
          title={`Medium Risk: ${bands.MEDIUM} (${pMed}% )`}
        >
          {Number(pMed) >= 5 ? `${pMed}%` : ''}
        </div>
        <div
          className="h-full bg-risk-high flex items-center justify-center text-white text-[11px] font-bold tabular-nums transition-all"
          style={{ width: `${pHigh}%` }}
          title={`High Risk: ${bands.HIGH} (${pHigh}%)`}
        >
          {Number(pHigh) >= 5 ? `${pHigh}%` : ''}
        </div>
        <div
          className="h-full bg-risk-critical flex items-center justify-center text-white text-[11px] font-bold tabular-nums transition-all"
          style={{ width: `${pCrit}%` }}
          title={`Critical Risk: ${bands.CRITICAL} (${pCrit}%)`}
        >
          {Number(pCrit) >= 4 ? `${pCrit}%` : ''}
        </div>
      </div>

      {/* Detailed Legend Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-1">
        {/* Low */}
        <div className="p-2.5 rounded bg-bg-subtle/50 border border-border-hairline flex flex-col">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-low shrink-0"></span>
            <span className="text-[11px] font-bold uppercase text-text-primary">Low Risk</span>
          </div>
          <span className="text-[14px] font-bold text-text-primary tabular-nums">
            {bands.LOW.toLocaleString()}{' '}
            <span className="text-text-muted font-normal text-[11px]">({pLow}%)</span>
          </span>
          <span className="text-[11px] text-text-secondary mt-0.5">₹ {cLow} L Cr alloc.</span>
        </div>

        {/* Medium */}
        <div className="p-2.5 rounded bg-bg-subtle/50 border border-border-hairline flex flex-col">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-medium shrink-0"></span>
            <span className="text-[11px] font-bold uppercase text-text-primary">Medium</span>
          </div>
          <span className="text-[14px] font-bold text-text-primary tabular-nums">
            {bands.MEDIUM.toLocaleString()}{' '}
            <span className="text-text-muted font-normal text-[11px]">({pMed}%)</span>
          </span>
          <span className="text-[11px] text-text-secondary mt-0.5">₹ {cMed} L Cr alloc.</span>
        </div>

        {/* High */}
        <div className="p-2.5 rounded bg-bg-subtle/50 border border-border-hairline flex flex-col">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-high shrink-0"></span>
            <span className="text-[11px] font-bold uppercase text-text-primary">High</span>
          </div>
          <span className="text-[14px] font-bold text-text-primary tabular-nums">
            {bands.HIGH.toLocaleString()}{' '}
            <span className="text-text-muted font-normal text-[11px]">({pHigh}%)</span>
          </span>
          <span className="text-[11px] text-text-secondary mt-0.5">₹ {cHigh} L Cr alloc.</span>
        </div>

        {/* Critical */}
        <div className="p-2.5 rounded bg-bg-subtle/50 border border-border-hairline flex flex-col">
          <div className="flex items-center gap-1.5 mb-1">
            <span className="w-2.5 h-2.5 rounded-full bg-risk-critical shrink-0"></span>
            <span className="text-[11px] font-bold uppercase text-text-primary">Critical</span>
          </div>
          <span className="text-[14px] font-bold text-text-primary tabular-nums">
            {bands.CRITICAL.toLocaleString()}{' '}
            <span className="text-text-muted font-normal text-[11px]">({pCrit}%)</span>
          </span>
          <span className="text-[11px] text-text-secondary mt-0.5">₹ {cCrit} L Cr alloc.</span>
        </div>
      </div>
    </div>
  );
};
