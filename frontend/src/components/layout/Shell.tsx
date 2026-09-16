import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  HelpCircle,
  Moon,
  Sparkles,
  Sun,
  ShieldCheck,
  User,
  Clock,
  Download,
} from 'lucide-react';

interface ShellProps {
  children: React.ReactNode;
  activeNav?: 'national-overview' | 'watchlist' | 'assistant';
  onNavigate?: (screen: 'national-overview' | 'watchlist' | 'assistant') => void;
  activeWarningsCount?: number;
  reportMonth?: string;
}

export const Shell: React.FC<ShellProps> = ({
  children,
  activeNav = 'national-overview',
  onNavigate,
  activeWarningsCount = 311,
  reportMonth = 'July 2026',
}) => {
  const [textScale, setTextScale] = useState<'sm' | 'base' | 'lg'>('base');
  const [highContrast, setHighContrast] = useState<boolean>(false);

  useEffect(() => {
    document.body.classList.remove('text-scale-sm', 'text-scale-base', 'text-scale-lg');
    document.body.classList.add(`text-scale-${textScale}`);
  }, [textScale]);

  useEffect(() => {
    if (highContrast) {
      document.body.classList.add('high-contrast');
    } else {
      document.body.classList.remove('high-contrast');
    }
  }, [highContrast]);

  return (
    <div className="min-h-screen bg-bg-page flex">
      {/* LEFT NAVIGATION RAIL (240px) */}
      <aside className="w-60 bg-bg-surface border-r border-border-hairline fixed top-0 bottom-0 left-0 z-50 flex flex-col justify-between select-none">
        <div className="flex flex-col">
          {/* Header Brand */}
          <div className="h-14 px-4 flex items-center gap-3 border-b border-border-hairline bg-bg-surface">
            <div className="w-8 h-8 rounded bg-brand-primary flex items-center justify-center shrink-0">
              <Activity className="w-4 h-4 text-white" />
            </div>
            <div className="flex flex-col min-w-0 leading-tight">
              <span className="text-[15px] font-bold tracking-tight text-brand-primary truncate">PAIMANA</span>
              <span className="text-[10px] text-text-muted truncate">MoSPI IPMD Risk Cockpit</span>
            </div>
          </div>

          <div className="px-3 py-2">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-text-muted px-2 py-1 block">
              Monitoring Modules
            </span>
          </div>

          <nav className="flex flex-col gap-1 px-2">
            <button
              type="button"
              onClick={() => onNavigate?.('national-overview')}
              className={`w-full flex items-center justify-between px-3 py-2 rounded text-[13px] font-medium transition-colors text-left ${
                activeNav === 'national-overview'
                  ? 'bg-brand-primary text-white font-semibold'
                  : 'text-text-secondary hover:bg-bg-subtle hover:text-text-primary'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Activity className="w-4 h-4 shrink-0" />
                <span className="truncate">National Overview</span>
              </div>
            </button>

            <button
              type="button"
              onClick={() => onNavigate?.('watchlist')}
              className={`w-full flex items-center justify-between px-3 py-2 rounded text-[13px] font-medium transition-colors text-left ${
                activeNav === 'watchlist'
                  ? 'bg-brand-primary text-white font-semibold'
                  : 'text-text-secondary hover:bg-bg-subtle hover:text-text-primary'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <AlertTriangle className="w-4 h-4 text-risk-critical shrink-0" />
                <span className="truncate">Early-Warning Watchlist</span>
              </div>
              <span className="bg-risk-critical-bg text-risk-critical text-[10px] font-bold px-1.5 py-0.5 rounded tabular-nums">
                {activeWarningsCount}
              </span>
            </button>

            <button
              type="button"
              onClick={() => onNavigate?.('assistant')}
              className={`w-full flex items-center justify-between px-3 py-2 rounded text-[13px] font-medium transition-colors text-left ${
                activeNav === 'assistant'
                  ? 'bg-brand-primary text-white font-semibold'
                  : 'text-text-secondary hover:bg-bg-subtle hover:text-text-primary'
              }`}
            >
              <div className="flex items-center gap-2.5 min-w-0">
                <Sparkles className="w-4 h-4 text-brand-accent shrink-0" />
                <span className="truncate">Analyst Assistant</span>
              </div>
              <span className="bg-blue-100 text-brand-primary text-[9px] font-bold px-1 py-0.5 rounded uppercase">
                Query
              </span>
            </button>
          </nav>
        </div>

        {/* User Lineage & Validation Status */}
        <div className="flex flex-col border-t border-border-hairline bg-bg-surface">
          <div className="px-3 py-2 bg-bg-subtle/70 border-b border-border-hairline flex items-center justify-between text-[11px]">
            <span className="flex items-center gap-1.5 text-text-muted truncate">
              <span className="w-1.5 h-1.5 rounded-full bg-risk-low shrink-0"></span>
              Pipeline: 2026-07 • Calibrated
            </span>
            <ShieldCheck className="w-3.5 h-3.5 text-brand-primary shrink-0" />
          </div>
          <div className="p-3 flex items-center gap-2.5">
            <div className="w-8 h-8 rounded bg-brand-primary flex items-center justify-center text-white shrink-0">
              <User className="w-4 h-4" />
            </div>
            <div className="flex flex-col min-w-0 leading-tight">
              <span className="text-[13px] font-semibold text-text-primary truncate">V. Ramanathan</span>
              <span className="text-[11px] text-text-muted truncate">Senior Analyst, IPMD</span>
            </div>
          </div>
        </div>
      </aside>

      {/* MAIN CONTENT AREA */}
      <div className="pl-60 flex-1 flex flex-col min-w-0">
        {/* TOP BAR */}
        <header className="h-14 bg-bg-surface border-b border-border-hairline fixed top-0 left-60 right-0 z-40 px-6 flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0 text-[13px]">
            <span className="text-text-muted uppercase text-[11px] font-medium tracking-wider">MoSPI IPMD</span>
            <span className="text-text-muted">/</span>
            <span className="font-semibold text-text-primary truncate">National Infrastructure Overview</span>
          </div>

          <div className="flex items-center gap-3">
            {/* Font scaling controls */}
            <div className="flex items-center bg-bg-subtle rounded border border-border-hairline p-0.5 text-[11px] font-semibold text-text-secondary">
              <button
                onClick={() => setTextScale('sm')}
                className={`px-1.5 py-0.5 rounded transition-colors ${
                  textScale === 'sm' ? 'bg-bg-surface text-text-primary shadow-xs' : 'hover:text-text-primary'
                }`}
                title="Decrease font scale"
              >
                A-
              </button>
              <button
                onClick={() => setTextScale('base')}
                className={`px-1.5 py-0.5 rounded transition-colors ${
                  textScale === 'base' ? 'bg-bg-surface text-text-primary shadow-xs' : 'hover:text-text-primary'
                }`}
                title="Default font scale"
              >
                A
              </button>
              <button
                onClick={() => setTextScale('lg')}
                className={`px-1.5 py-0.5 rounded transition-colors ${
                  textScale === 'lg' ? 'bg-bg-surface text-text-primary shadow-xs' : 'hover:text-text-primary'
                }`}
                title="Increase font scale"
              >
                A+
              </button>
            </div>

            {/* High contrast toggle */}
            <button
              onClick={() => setHighContrast(!highContrast)}
              className={`p-1.5 rounded border border-border-hairline transition-colors ${
                highContrast ? 'bg-text-primary text-bg-surface' : 'bg-bg-surface text-text-secondary hover:bg-bg-subtle'
              }`}
              title="Toggle High Contrast"
            >
              {highContrast ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            </button>

            <div className="h-4 w-px bg-border-hairline"></div>

            {/* Freshness pill */}
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-bg-subtle border border-border-hairline text-[11px]">
              <Clock className="w-3.5 h-3.5 text-text-muted" />
              <span className="text-text-secondary">
                Data: <span className="font-semibold text-text-primary">{reportMonth}</span> (Provisional)
              </span>
            </div>

            {/* Export Briefing CTA */}
            <button
              onClick={() => window.print()}
              className="flex items-center gap-1.5 px-2.5 py-1 bg-bg-surface border border-brand-primary text-brand-primary rounded text-[12px] font-semibold hover:bg-brand-primary hover:text-white transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              Export Briefing
            </button>

            <a
              href="#docs"
              className="text-text-muted hover:text-brand-primary transition-colors p-1"
              title="Documentation"
            >
              <HelpCircle className="w-4 h-4" />
            </a>
          </div>
        </header>

        {/* BODY CONTAINER */}
        <main className="pt-14 p-6 min-h-screen">
          {children}
        </main>
      </div>
    </div>
  );
};
