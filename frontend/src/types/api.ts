export type RiskBand = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface BandDistribution {
  LOW: number;
  MEDIUM: number;
  HIGH: number;
  CRITICAL: number;
}

export interface RegimeSectorItem {
  sector: string;
  total_projects: number;
  avg_risk_score: number;
  critical_count: number;
  high_count: number;
  active_warnings: number;
}

export interface RegimeMinistryItem {
  ministry: string;
  total_projects: number;
  avg_risk_score: number;
  critical_count: number;
  active_warnings: number;
}

export interface NationalSubSummary {
  total_projects: number;
  total_cost_cr: number;
  total_expenditure_cr: number;
  avg_risk_score: number;
  band_distribution: BandDistribution;
  active_warnings_count: number;
  transfer_regime: boolean;
  transfer_regime_note?: string | null;
  sectors: RegimeSectorItem[];
  ministries: RegimeMinistryItem[];
}

export interface MonthlyTrendPoint {
  report_month: string;
  total_projects: number;
  avg_risk_score: number;
  critical_count: number;
  active_warnings: number;
  non_roads_avg_risk_score?: number;
  non_roads_critical_count?: number;
  non_roads_active_warnings?: number;
  roads_avg_risk_score?: number;
  roads_critical_count?: number;
  roads_active_warnings?: number;
}

export interface NationalSummaryResponse {
  report_month: string;
  total_projects: number;
  combined_total_cost_cr: number;
  combined_total_expenditure_cr: number;
  non_roads: NationalSubSummary;
  roads: NationalSubSummary;
  combined_band_distribution: BandDistribution;
  combined_active_warnings: number;
  monthly_trend: MonthlyTrendPoint[];
}

export interface WatchlistItem {
  project_id: string;
  project_name: string;
  ministry: string;
  sector: string;
  is_road: boolean;
  transfer_regime: boolean;
  data_sufficiency: string;
  risk_score: number;
  risk_band: RiskBand;
  warning_strength: number;
  triggers_fired: string;
  score_delta_1m?: number | null;
  score_delta_2m?: number | null;
  gap_delta_1m?: number | null;
  progress_velocity_3mo?: number | null;
  exp_velocity_3mo?: number | null;
  physical_progress_pct: number;
}

export interface WatchlistResponse {
  report_month: string;
  total_active_warnings: number;
  non_roads_count: number;
  roads_count: number;
  items: WatchlistItem[];
}

export interface PipelineLastRun {
  status: string;
  version: string;
  timestamp: string;
  records_processed: number;
  latest_month: string;
}

export type RegimeFilter = "non_roads" | "roads" | "combined";
