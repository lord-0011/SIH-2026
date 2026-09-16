import React from 'react';
import { Info, ShieldCheck } from 'lucide-react';

export const HonestFooter: React.FC = () => {
  return (
    <div className="p-4 bg-bg-surface rounded-lg border border-border-hairline flex items-start gap-3 text-text-muted shadow-xs">
      <Info className="w-5 h-5 text-brand-primary shrink-0 mt-0.5" />
      <div className="space-y-1 text-[12px] text-text-secondary leading-relaxed">
        <p>
          <strong className="text-text-primary">Methodology & Empirical Verification: </strong>
          Predictions validated on 116 held-out historical IPMD outcomes (PR-AUC: 0.466, ROC-AUC: 0.853). 
          Risk scores represent calibrated triage early-warning signals (top-risk 6% CRITICAL band realized slip rate: 55.4%, a 6.56x lift over the 8.45% base rate), not statutory audits.
        </p>
        <p className="text-[11px] text-text-muted flex items-center gap-1">
          <ShieldCheck className="w-3.5 h-3.5 text-risk-low inline" />
          Zero request-time recomputation guarantee. All financial figures denote sanctioned capital outlays unless marked revised.
        </p>
      </div>
    </div>
  );
};
