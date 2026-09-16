import React, { useState, useEffect, useMemo } from 'react';
import { Shell } from './components/layout/Shell';
import { RegimeToggle } from './components/national/RegimeToggle';
import { KpiRow } from './components/national/KpiRow';
import { RiskSplitCard } from './components/national/RiskSplitCard';
import { MonthlyTrendChart } from './components/national/MonthlyTrendChart';
import { SectorDistributionCard } from './components/national/SectorDistributionCard';
import { MinistryRankingCard } from './components/national/MinistryRankingCard';
import { WatchlistTable } from './components/national/WatchlistTable';
import { HonestFooter } from './components/national/HonestFooter';
import { fetchNationalSummary, fetchWatchlist } from './api/client';
import type {
  NationalSummaryResponse,
  NationalSubSummary,
  WatchlistResponse,
  RegimeFilter,
  RegimeSectorItem,
  RegimeMinistryItem,
} from './types/api';
import { AlertCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [currentRegime, setCurrentRegime] = useState<RegimeFilter>('non_roads');
  const [nationalData, setNationalData] = useState<NationalSummaryResponse | null>(null);
  const [watchlistData, setWatchlistData] = useState<WatchlistResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [watchlistLoading, setWatchlistLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Initial load: National summary + default non_roads watchlist
  const loadInitialData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [summaryRes, watchlistRes] = await Promise.all([
        fetchNationalSummary(),
        fetchWatchlist({ regime: 'non_roads' }),
      ]);
      setNationalData(summaryRes);
      setWatchlistData(watchlistRes);
    } catch (err: any) {
      console.error('Failed to load PAIMANA data:', err);
      setError(
        err?.message ||
          'Failed to connect to PAIMANA API server (http://127.0.0.1:8000). Ensure the backend service is running.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // When regime toggle flips, re-fetch watchlist synchronously
  const handleRegimeChange = async (regime: RegimeFilter) => {
    setCurrentRegime(regime);
    setWatchlistLoading(true);
    try {
      const watchlistRes = await fetchWatchlist({
        regime: regime === 'combined' ? undefined : regime,
      });
      setWatchlistData(watchlistRes);
    } catch (err: any) {
      console.error(`Failed to update watchlist for regime ${regime}:`, err);
    } finally {
      setWatchlistLoading(false);
    }
  };

  // Derive active summary slice based on currentRegime
  const activeSummary: NationalSubSummary | null = useMemo(() => {
    if (!nationalData) return null;

    if (currentRegime === 'non_roads') {
      return nationalData.non_roads;
    }

    if (currentRegime === 'roads') {
      return nationalData.roads;
    }

    // Combined regime
    const combinedSectors: RegimeSectorItem[] = [
      ...nationalData.non_roads.sectors,
      ...nationalData.roads.sectors,
    ];

    const combinedMinistries: RegimeMinistryItem[] = [
      ...nationalData.non_roads.ministries,
      ...nationalData.roads.ministries,
    ];

    return {
      total_projects: nationalData.total_projects,
      total_cost_cr: nationalData.combined_total_cost_cr,
      total_expenditure_cr: nationalData.combined_total_expenditure_cr,
      avg_risk_score: Number(
        (
          (nationalData.non_roads.avg_risk_score * nationalData.non_roads.total_projects +
            nationalData.roads.avg_risk_score * nationalData.roads.total_projects) /
          nationalData.total_projects
        ).toFixed(1)
      ),
      band_distribution: nationalData.combined_band_distribution,
      active_warnings_count: nationalData.combined_active_warnings,
      transfer_regime: false,
      transfer_regime_note: null,
      sectors: combinedSectors,
      ministries: combinedMinistries,
    };
  }, [nationalData, currentRegime]);

  const regimeTitle = useMemo(() => {
    switch (currentRegime) {
      case 'non_roads':
        return 'Non-Roads Core Validated';
      case 'roads':
        return 'Roads & Highways Transfer Regime';
      case 'combined':
      default:
        return 'Combined Portfolio';
    }
  }, [currentRegime]);

  if (loading) {
    return (
      <Shell>
        <div className="h-96 flex flex-col items-center justify-center gap-3 text-text-muted">
          <RefreshCw className="w-8 h-8 animate-spin text-brand-primary" />
          <p className="text-[14px] font-medium">Loading precomputed PAIMANA risk models...</p>
        </div>
      </Shell>
    );
  }

  if (error || !nationalData || !activeSummary) {
    return (
      <Shell>
        <div className="p-8 bg-red-50 border border-red-200 rounded-lg flex flex-col items-center text-center max-w-xl mx-auto my-12">
          <AlertCircle className="w-10 h-10 text-risk-critical mb-3" />
          <h2 className="text-[16px] font-bold text-red-950 mb-1">Backend Connection Required</h2>
          <p className="text-[13px] text-red-800 mb-4">{error}</p>
          <button
            type="button"
            onClick={loadInitialData}
            className="flex items-center gap-2 px-4 py-2 bg-brand-primary text-white text-[13px] font-semibold rounded hover:bg-brand-primary-hover transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Retry Connection
          </button>
        </div>
      </Shell>
    );
  }

  return (
    <Shell
      activeNav="national-overview"
      activeWarningsCount={activeSummary.active_warnings_count}
      reportMonth={nationalData.report_month}
    >
      <div className="space-y-6">
        {/* Page Header / Triage Banner */}
        <div className="bg-bg-surface p-5 rounded-lg border border-border-hairline shadow-xs flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2.5">
              <h1 className="text-[22px] font-bold text-text-primary tracking-tight">
                National Infrastructure Project Risk Overview
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-blue-50 text-brand-primary text-[11px] font-bold tracking-wide uppercase">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-primary animate-pulse"></span>
                Coverage: 100% IPMD Monitored
              </span>
            </div>
            <p className="text-[13px] text-text-secondary">
              Predictive early-warning surveillance across central sector infrastructure projects (≥ ₹150 Cr threshold).
            </p>
          </div>

          {/* 3-Way Regime Filter */}
          <RegimeToggle
            currentRegime={currentRegime}
            onRegimeChange={handleRegimeChange}
            nonRoadsCount={nationalData.non_roads.total_projects}
            roadsCount={nationalData.roads.total_projects}
            totalCount={nationalData.total_projects}
          />
        </div>

        {/* 5 KPI Stat Cards Row */}
        <KpiRow
          summary={activeSummary}
          combinedBands={nationalData.combined_band_distribution}
          isCombined={currentRegime === 'combined'}
        />

        {/* Second Row: 7 Cols (Risk Split + Trend) & 5 Cols (Sector + Ministry) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Column (7 cols) */}
          <div className="lg:col-span-7 flex flex-col gap-6">
            <RiskSplitCard
              bands={activeSummary.band_distribution}
              totalProjects={activeSummary.total_projects}
              totalCostCr={activeSummary.total_cost_cr}
              regimeTitle={regimeTitle}
            />

            <MonthlyTrendChart
              trendData={nationalData.monthly_trend}
              currentRegime={currentRegime}
            />
          </div>

          {/* Right Column (5 cols) */}
          <div className="lg:col-span-5 flex flex-col gap-6">
            <SectorDistributionCard
              sectors={activeSummary.sectors}
              currentRegime={currentRegime}
            />

            <MinistryRankingCard
              ministries={activeSummary.ministries}
              currentRegime={currentRegime}
            />
          </div>
        </div>

        {/* Third Row: Priority Triage Watchlist */}
        <div className="relative">
          {watchlistLoading && (
            <div className="absolute inset-0 bg-white/60 z-10 flex items-center justify-center rounded-lg">
              <RefreshCw className="w-6 h-6 animate-spin text-brand-primary" />
            </div>
          )}
          <WatchlistTable
            items={watchlistData?.items || []}
            totalActiveWarnings={watchlistData?.total_active_warnings || activeSummary.active_warnings_count}
            reportMonth={nationalData.report_month}
            onSelectProject={(id) => console.log('Selected project dossier:', id)}
          />
        </div>

        {/* Bottom Footnote / Verified Methodology */}
        <HonestFooter />
      </div>
    </Shell>
  );
};

export default App;
