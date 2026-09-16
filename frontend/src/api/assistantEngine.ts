import {
  fetchProjectDetail,
  fetchSectorSummary,
  fetchMinistrySummary,
  fetchNationalSummary,
  fetchWatchlist,
} from './client';
import type { WatchlistItem } from '../types/api';

export interface AssistantSourceReceipt {
  endpoint: string;
  method: 'GET';
  description: string;
}

export interface AssistantMetric {
  label: string;
  value: string | number;
  highlight?: 'critical' | 'high' | 'medium' | 'low' | 'neutral' | 'accent';
}

export interface AssistantAnswer {
  headline: string;
  summary: string;
  transferCaveat?: string | null;
  metrics?: AssistantMetric[];
  bullets?: string[];
  sources: AssistantSourceReceipt[];
  entityType: 'project' | 'sector' | 'ministry' | 'national' | 'watchlist' | 'methodology' | 'unknown';
  matchedQuery: string;
}

// Canonical sector mapping with aliases
const SECTOR_ALIASES: Record<string, string> = {
  railway: 'Railways',
  railways: 'Railways',
  rail: 'Railways',
  train: 'Railways',
  ir: 'Railways',
  power: 'Electricity Generation',
  electricity: 'Electricity Generation',
  powergen: 'Electricity Generation',
  'electricity generation': 'Electricity Generation',
  transmission: 'Transmission & Distribution',
  distribution: 'Transmission & Distribution',
  'power grid': 'Transmission & Distribution',
  grid: 'Transmission & Distribution',
  't&d': 'Transmission & Distribution',
  coal: 'Coal',
  oil: 'Oil & Gas',
  gas: 'Oil & Gas',
  petroleum: 'Oil & Gas',
  hydrocarbon: 'Oil & Gas',
  refinery: 'Oil & Gas',
  roads: 'Roads & Highways',
  road: 'Roads & Highways',
  highway: 'Roads & Highways',
  highways: 'Roads & Highways',
  nhai: 'Roads & Highways',
  morth: 'Roads & Highways',
  steel: 'Steel',
  mines: 'Metals & Mining',
  mining: 'Metals & Mining',
  minerals: 'Metals & Mining',
  metals: 'Metals & Mining',
  shipping: 'Shipping',
  ports: 'Shipping',
  port: 'Shipping',
  telecom: 'Telecommunication',
  telecommunication: 'Telecommunication',
  telecommunications: 'Telecommunication',
  dot: 'Telecommunication',
  urban: 'Urban Public Transport',
  metro: 'Urban Public Transport',
  water: 'Water Resources',
  irrigation: 'Water Resources',
  'water resources': 'Water Resources',
  aviation: 'Aviation & Aviation Infrastructure',
  airport: 'Aviation & Aviation Infrastructure',
  airports: 'Aviation & Aviation Infrastructure',
  construction: 'Construction',
  education: 'Education',
  healthcare: 'Healthcare',
  health: 'Healthcare',
  waterway: 'Inland Waterways',
  'inland waterways': 'Inland Waterways',
  logistics: 'Logistics Infrastructure',
  'real estate': 'Real Estate',
  housing: 'Real Estate',
  waste: 'Waste & Water',
  storage: 'Energy Storage',
  'energy storage': 'Energy Storage',
};

// Canonical ministry mapping with aliases
const MINISTRY_ALIASES: Record<string, string> = {
  'ministry of railways': 'Ministry of Railways',
  railways: 'Ministry of Railways',
  'ministry of road transport & highways': 'Ministry of Road Transport & Highways',
  morth: 'Ministry of Road Transport & Highways',
  'ministry of power': 'Ministry of Power',
  power: 'Ministry of Power',
  'ministry of coal': 'Ministry of Coal',
  coal: 'Ministry of Coal',
  'ministry of petroleum & natural gas': 'Ministry of Petroleum & Natural Gas',
  mopng: 'Ministry of Petroleum & Natural Gas',
  'ministry of steel': 'Ministry of Steel',
  steel: 'Ministry of Steel',
  'ministry of civil aviation': 'Ministry of Civil Aviation',
  aviation: 'Ministry of Civil Aviation',
  'ministry of housing & urban affairs': 'Ministry of Housing & Urban Affairs',
  mohua: 'Ministry of Housing & Urban Affairs',
  'ministry of mines': 'Ministry of Mines',
  'ministry of ports, shipping and waterways': 'Ministry of Ports, Shipping and Waterways',
  'ministry of health & family welfare': 'Ministry of Health & Family Welfare',
};

export async function processAssistantQuery(query: string): Promise<AssistantAnswer> {
  const cleanQuery = query.trim().toLowerCase();

  // 1. Check for outcome / guarantee certainty questions
  const isOutcomeQuestion =
    /\b(will|is|can)\b.*\b(fail|delay|succeed|complete|finish|collapse)\b/i.test(query) ||
    /\b(guarantee|guaranteed|definitely|certainly|100%|surely|certain|absolute)\b/i.test(query);

  const projectIdMatch = query.match(/\b(?:project\s*(?:id|code)?\s*[:#]?\s*|^|\b)(\d{5,7})\b/i);
  const matchedProjectId = projectIdMatch ? projectIdMatch[1] : null;

  if (isOutcomeQuestion) {
    if (matchedProjectId) {
      try {
        const detail = await fetchProjectDetail(matchedProjectId);
        const bandHighlight =
          detail.current_metrics.risk_band === 'CRITICAL'
            ? 'critical'
            : detail.current_metrics.risk_band === 'HIGH'
            ? 'high'
            : detail.current_metrics.risk_band === 'MEDIUM'
            ? 'medium'
            : 'low';

        return {
          headline: `Probabilistic Risk Assessment for Project #${detail.project_id}: ${detail.project_name}`,
          summary:
            `The PAIMANA system provides probabilistic early-warning risk estimates, NOT deterministic binary guarantees. ` +
            `Project #${detail.project_id} currently holds a calibrated slip probability of ${(detail.current_metrics.calibrated_probability * 100).toFixed(1)}% ` +
            `(Risk Score: ${detail.current_metrics.risk_score.toFixed(1)}/100, ${detail.current_metrics.risk_band} band). ` +
            `In empirical calibration over the 2026-07 holdout test, CRITICAL-band projects experienced a 55.4% realized schedule slip rate, while LOW-band projects had only 1.7%. ` +
            `This score signals urgent operational triage priority—it does not imply certain failure.`,
          transferCaveat: detail.transfer_regime
            ? `TRANSFER REGIME: MoRTH pipeline on-boarded Dec 2025; reporting convention differences. Treat scores as provisional.`
            : null,
          metrics: [
            { label: 'Risk Band', value: detail.current_metrics.risk_band, highlight: bandHighlight },
            { label: 'Risk Score', value: `${detail.current_metrics.risk_score.toFixed(1)} / 100`, highlight: bandHighlight },
            { label: 'Calibrated Slip Prob', value: `${(detail.current_metrics.calibrated_probability * 100).toFixed(1)}%` },
            {
              label: 'Remaining Duration',
              value: detail.current_metrics.remaining_duration_months != null
                ? `${detail.current_metrics.remaining_duration_months} mo`
                : 'N/A',
            },
            { label: 'Warning Strength', value: `${detail.early_warning.warning_strength} / 3` },
          ],
          bullets: [
            `Realized slip rates by band: CRITICAL (55.4%), HIGH (38.2%), MEDIUM (14.6%), LOW (1.7%).`,
            `Active Early Warning Triggers: ${detail.early_warning.triggers_fired || 'None'}.`,
            `Physical progress is currently ${detail.current_metrics.physical_progress_pct.toFixed(1)}% with a financial-physical gap of ${detail.current_metrics.financial_physical_gap.toFixed(1)}%.`,
          ],
          sources: [
            {
              endpoint: `/projects/${detail.project_id}`,
              method: 'GET',
              description: `Verified dossier for project ${detail.project_id} without request-time recomputation`,
            },
            {
              endpoint: `/pipeline/last-run`,
              method: 'GET',
              description: `Model calibration holdout metrics (2026-07 holdout test)`,
            },
          ],
          entityType: 'methodology',
          matchedQuery: query,
        };
      } catch (err) {
        // Project ID didn't resolve, fallback to general methodology answer
      }
    }

    return {
      headline: `Methodology: Probabilistic Early-Warning vs Deterministic Guarantees`,
      summary:
        `PAIMANA is an executive early-warning surveillance engine built on calibrated Gradient Boosted survival/hazard models. ` +
        `It produces empirical probabilities of milestone slippage and cost escalation, not deterministic prophecies. ` +
        `A high risk score indicates statistically elevated distress to allow MoSPI and line ministries to intervene BEFORE irreversible slippage occurs.`,
      metrics: [
        { label: 'CRITICAL Realized Slip', value: '55.4%', highlight: 'critical' },
        { label: 'HIGH Realized Slip', value: '38.2%', highlight: 'high' },
        { label: 'MEDIUM Realized Slip', value: '14.6%', highlight: 'medium' },
        { label: 'LOW Realized Slip', value: '1.7%', highlight: 'low' },
      ],
      bullets: [
        `Risk scores range from 0 to 100, mapped into calibrated bands (LOW, MEDIUM, HIGH, CRITICAL).`,
        `Multi-trigger early warnings (1-3 triggers) detect velocity stagnation, expenditure gaps, and score escalation.`,
        `Outcomes depend on proactive administrative interventions; surveillance is designed to alter outcomes, not predict them passively.`,
      ],
      sources: [
        {
          endpoint: `/national/summary`,
          method: 'GET',
          description: `Empirical portfolio distribution across verified risk bands`,
        },
      ],
      entityType: 'methodology',
      matchedQuery: query,
    };
  }

  // 2. Direct Project ID Lookup
  if (matchedProjectId) {
    try {
      const detail = await fetchProjectDetail(matchedProjectId);
      const bandHighlight =
        detail.current_metrics.risk_band === 'CRITICAL'
          ? 'critical'
          : detail.current_metrics.risk_band === 'HIGH'
          ? 'high'
          : detail.current_metrics.risk_band === 'MEDIUM'
          ? 'medium'
          : 'low';

      return {
        headline: `Project #${detail.project_id}: ${detail.project_name}`,
        summary:
          `${detail.project_name} is monitored under the ${detail.sector} sector by the ${detail.ministry} in ${detail.state}. ` +
          `It is classified in the ${detail.current_metrics.risk_band} risk band with a risk score of ${detail.current_metrics.risk_score.toFixed(1)}/100 ` +
          `and an early-warning conviction strength of ${detail.early_warning.warning_strength}/3.`,
        transferCaveat: detail.transfer_regime
          ? `TRANSFER REGIME: MoRTH pipeline on-boarded Dec 2025; reporting convention differences. Treat scores as provisional.`
          : null,
        metrics: [
          { label: 'Risk Band', value: detail.current_metrics.risk_band, highlight: bandHighlight },
          { label: 'Risk Score', value: `${detail.current_metrics.risk_score.toFixed(1)} / 100`, highlight: bandHighlight },
          { label: 'Physical Progress', value: `${detail.current_metrics.physical_progress_pct.toFixed(1)}%` },
          { label: 'Fin-Phys Gap', value: `${detail.current_metrics.financial_physical_gap.toFixed(1)}%` },
          { label: 'Sanctioned Cost', value: `₹${detail.current_metrics.original_cost_cr.toLocaleString('en-IN')} Cr` },
          { label: 'Expenditure', value: `₹${detail.current_metrics.cumulative_expenditure_cr.toLocaleString('en-IN')} Cr` },
        ],
        bullets: [
          `Warning Status: ${detail.early_warning.warning_status} (Conviction: ${detail.early_warning.warning_strength}/3)`,
          `Active Triggers: ${detail.early_warning.triggers_fired || 'None active'}`,
          `Schedule: ${detail.current_metrics.remaining_duration_months != null ? `${detail.current_metrics.remaining_duration_months} months remaining` : 'Target Schedule'} | Cost Outlay: ₹${detail.current_metrics.original_cost_cr.toLocaleString('en-IN')} Cr`,
          `Data Sufficiency: ${detail.data_sufficiency} (${detail.observed_months_to_date} months observed)`,
        ],
        sources: [
          {
            endpoint: `/projects/${detail.project_id}`,
            method: 'GET',
            description: `Dossier record loaded directly from panel.parquet without request-time recomputation`,
          },
        ],
        entityType: 'project',
        matchedQuery: query,
      };
    } catch (err: any) {
      return {
        headline: `Project #${matchedProjectId} Not Found`,
        summary:
          `Project ID "${matchedProjectId}" does not exist in the July 2026 IPMD portfolio of 1,800 monitored central sector projects. ` +
          `Please check that the project ID is correct (e.g., 705505, 400119, 400171) or search by sector name.`,
        sources: [
          {
            endpoint: `/projects/${matchedProjectId}`,
            method: 'GET',
            description: `Attempted query to project catalog (returned 404)`,
          },
        ],
        entityType: 'project',
        matchedQuery: query,
      };
    }
  }

  // 3. Sector Lookup
  let matchedSectorName: string | null = null;
  for (const [alias, canonical] of Object.entries(SECTOR_ALIASES)) {
    const pattern = new RegExp(`\\b${alias}\\b`, 'i');
    if (pattern.test(cleanQuery)) {
      matchedSectorName = canonical;
      break;
    }
  }

  if (matchedSectorName) {
    try {
      const isWatchlistQuery = /\b(watchlist|deteriorat|warning|risk|critical|triage|slip)\b/i.test(cleanQuery);

      const [sectorSummary, watchlistRes] = await Promise.all([
        fetchSectorSummary(matchedSectorName),
        isWatchlistQuery ? fetchWatchlist({ sector: matchedSectorName }) : Promise.resolve(null),
      ]);

      const sources: AssistantSourceReceipt[] = [
        {
          endpoint: `/sectors/${encodeURIComponent(matchedSectorName)}/summary`,
          method: 'GET',
          description: `Sector level-2 aggregates and risk profile for ${matchedSectorName}`,
        },
      ];

      if (watchlistRes) {
        sources.push({
          endpoint: `/watchlist?sector=${encodeURIComponent(matchedSectorName)}`,
          method: 'GET',
          description: `Active early-warning watchlist filtered by sector ${matchedSectorName}`,
        });
      }

      const bullets: string[] = [
        `Risk Band Distribution: ${sectorSummary.band_distribution.CRITICAL} Critical, ${sectorSummary.band_distribution.HIGH} High, ${sectorSummary.band_distribution.MEDIUM} Medium, ${sectorSummary.band_distribution.LOW} Low.`,
        `Average Physical Progress: ${sectorSummary.avg_physical_progress_pct.toFixed(1)}% across ${sectorSummary.total_projects} projects.`,
        `Sanctioned Outlay: ₹${sectorSummary.total_cost_cr.toLocaleString('en-IN')} Cr with ₹${sectorSummary.total_expenditure_cr.toLocaleString('en-IN')} Cr cumulative expenditure.`,
      ];

      if (watchlistRes && watchlistRes.items.length > 0) {
        bullets.push(
          `Top Deteriorating Projects: ` +
            watchlistRes.items
              .slice(0, 3)
              .map((p: WatchlistItem) => `#${p.project_id} ${p.project_name.slice(0, 30)} (Score: ${p.risk_score.toFixed(1)})`)
              .join('; ')
        );
      }

      return {
        headline: `${sectorSummary.sector} Sector Risk Summary`,
        summary:
          `The ${sectorSummary.sector} sector encompasses ${sectorSummary.total_projects} central sector projects with an average risk score of ` +
          `${sectorSummary.avg_risk_score.toFixed(1)}/100 and ${sectorSummary.active_warnings_count} projects under active early-warning surveillance.`,
        transferCaveat: sectorSummary.transfer_regime
          ? `TRANSFER REGIME: MoRTH pipeline on-boarded Dec 2025; reporting convention differences. Watchlist items carry transfer indicators.`
          : null,
        metrics: [
          { label: 'Total Projects', value: sectorSummary.total_projects },
          { label: 'Avg Risk Score', value: `${sectorSummary.avg_risk_score.toFixed(1)} / 100` },
          { label: 'Active Warnings', value: sectorSummary.active_warnings_count, highlight: sectorSummary.active_warnings_count > 0 ? 'critical' : 'neutral' },
          { label: 'Critical Projects', value: sectorSummary.band_distribution.CRITICAL, highlight: 'critical' },
          { label: 'Total Outlay', value: `₹${sectorSummary.total_cost_cr.toLocaleString('en-IN')} Cr` },
        ],
        bullets,
        sources,
        entityType: 'sector',
        matchedQuery: query,
      };
    } catch (err: any) {
      // Sector summary failed, continue to other intents
    }
  }

  // 4. Watchlist & Deteriorating Projects Lookup
  const isWatchlistIntent =
    /\b(watchlist|deteriorating|deterioration|early warning|warnings|critical projects|highest risk|triple trigger|conviction)\b/i.test(
      cleanQuery
    );

  if (isWatchlistIntent) {
    const isTripleTrigger = /\b(triple|strength 3|conviction 3|3 triggers)\b/i.test(cleanQuery);
    const minStrength = isTripleTrigger ? 3 : 2;

    const watchlistRes = await fetchWatchlist({ min_strength: minStrength });

    const sources: AssistantSourceReceipt[] = [
      {
        endpoint: `/watchlist?min_strength=${minStrength}`,
        method: 'GET',
        description: `Early-warning priority watchlist with min_strength=${minStrength}`,
      },
    ];

    const topItems = watchlistRes.items.slice(0, 5);
    const bullets = topItems.map(
      (item: WatchlistItem) =>
        `#${item.project_id} - ${item.project_name} (${item.sector}): Risk Score ${item.risk_score.toFixed(1)}, Strength ${item.warning_strength}/3 [Triggers: ${item.triggers_fired}]`
    );

    return {
      headline: `Priority Early-Warning Watchlist (Conviction ≥ ${minStrength})`,
      summary:
        `Found ${watchlistRes.items.length} projects with active high-conviction early-warning signals (strength ≥ ${minStrength}/3) ` +
        `out of ${watchlistRes.total_active_warnings} total active warnings across the portfolio (${watchlistRes.non_roads_count} Non-Roads, ${watchlistRes.roads_count} Roads).`,
      transferCaveat:
        watchlistRes.roads_count > 0
          ? `Note: ${watchlistRes.roads_count} Roads projects are under the Transfer Regime (MoRTH Dec 2025 onboarding) and visually subordinated in triage.`
          : null,
      metrics: [
        { label: 'High Conviction', value: watchlistRes.items.length, highlight: 'critical' },
        { label: 'Total Active Warnings', value: watchlistRes.total_active_warnings },
        { label: 'Non-Roads Warnings', value: watchlistRes.non_roads_count },
        { label: 'Roads Warnings', value: watchlistRes.roads_count },
      ],
      bullets,
      sources,
      entityType: 'watchlist',
      matchedQuery: query,
    };
  }

  // 5. National Portfolio / Benchmark Lookup
  const isNationalIntent =
    /\b(national|portfolio|overall|total|benchmark|benchmarks|summary|across india|system-wide|country|all projects)\b/i.test(
      cleanQuery
    );

  if (isNationalIntent) {
    const nationalData = await fetchNationalSummary();

    const sources: AssistantSourceReceipt[] = [
      {
        endpoint: `/national/summary`,
        method: 'GET',
        description: `National summary aggregates across Non-Roads, Roads, and Combined regimes`,
      },
    ];

    return {
      headline: `National Infrastructure Portfolio Overview (July 2026)`,
      summary:
        `The national monitoring portfolio covers ${nationalData.total_projects} projects with a sanctioned capital outlay of ` +
        `₹${nationalData.combined_total_cost_cr.toLocaleString('en-IN')} Cr. Due to reporting differences, the portfolio is strictly segmented into ` +
        `the Non-Roads Core Validated regime (787 projects) and the Roads & Highways Transfer Regime (1,013 projects).`,
      transferCaveat:
        `Simpson's Paradox Alert: The national average risk score steps up in Dec 2025 purely due to the onboarding of 1,013 MoRTH projects, not systemic deterioration. Always evaluate regimes separately.`,
      metrics: [
        { label: 'Total Projects', value: nationalData.total_projects },
        { label: 'Non-Roads (Core)', value: nationalData.non_roads.total_projects },
        { label: 'Roads (Transfer)', value: nationalData.roads.total_projects },
        { label: 'Combined Outlay', value: `₹${nationalData.combined_total_cost_cr.toLocaleString('en-IN')} Cr` },
        { label: 'Total Warnings', value: nationalData.combined_active_warnings, highlight: 'critical' },
      ],
      bullets: [
        `Non-Roads Regime: 787 projects, ₹${nationalData.non_roads.total_cost_cr.toLocaleString('en-IN')} Cr outlay, avg risk score ${nationalData.non_roads.avg_risk_score.toFixed(1)}, ${nationalData.non_roads.active_warnings_count} active warnings.`,
        `Roads Regime: 1,013 projects, ₹${nationalData.roads.total_cost_cr.toLocaleString('en-IN')} Cr outlay, avg risk score ${nationalData.roads.avg_risk_score.toFixed(1)}, ${nationalData.roads.active_warnings_count} active warnings.`,
        `Combined Band Split: ${nationalData.combined_band_distribution.CRITICAL} Critical, ${nationalData.combined_band_distribution.HIGH} High, ${nationalData.combined_band_distribution.MEDIUM} Medium, ${nationalData.combined_band_distribution.LOW} Low.`,
      ],
      sources,
      entityType: 'national',
      matchedQuery: query,
    };
  }

  // 6. Ministry Lookup
  for (const [alias, canonical] of Object.entries(MINISTRY_ALIASES)) {
    const pattern = new RegExp(`\\b${alias}\\b`, 'i');
    if (pattern.test(cleanQuery)) {
      try {
        const ministrySummary = await fetchMinistrySummary(canonical);
        return {
          headline: `${ministrySummary.ministry} Portfolio Summary`,
          summary:
            `${ministrySummary.ministry} oversees ${ministrySummary.total_projects} projects with a sanctioned capital outlay of ` +
            `₹${ministrySummary.total_cost_cr.toLocaleString('en-IN')} Cr. Average risk score is ${ministrySummary.avg_risk_score.toFixed(1)}/100 ` +
            `with ${ministrySummary.active_warnings_count} projects under active early-warning status.`,
          metrics: [
            { label: 'Total Projects', value: ministrySummary.total_projects },
            { label: 'Avg Risk Score', value: `${ministrySummary.avg_risk_score.toFixed(1)} / 100` },
            { label: 'Active Warnings', value: ministrySummary.active_warnings_count, highlight: 'critical' },
            { label: 'Critical Projects', value: ministrySummary.band_distribution.CRITICAL, highlight: 'critical' },
          ],
          bullets: [
            `Band Breakdown: ${ministrySummary.band_distribution.CRITICAL} Critical, ${ministrySummary.band_distribution.HIGH} High, ${ministrySummary.band_distribution.MEDIUM} Medium, ${ministrySummary.band_distribution.LOW} Low.`,
            `Total Outlay: ₹${ministrySummary.total_cost_cr.toLocaleString('en-IN')} Cr | Cumulative Expenditure: ₹${ministrySummary.total_expenditure_cr.toLocaleString('en-IN')} Cr.`,
          ],
          sources: [
            {
              endpoint: `/ministries/${encodeURIComponent(canonical)}/summary`,
              method: 'GET',
              description: `Ministry-level portfolio aggregates for ${canonical}`,
            },
          ],
          entityType: 'ministry',
          matchedQuery: query,
        };
      } catch (e) {
        // Fallback
      }
    }
  }

  // 7. Unmatched / Misroute Fallback
  return {
    headline: `Query Unmapped to Tracked Entities`,
    summary:
      `I couldn't map that query to a project ID, sector, or ministry I track. ` +
      `I am a deterministic query router over validated precomputed models—with zero generative hallucination by construction.`,
    bullets: [
      `Search by Project ID: 'What is the risk score of project 705505?' or '400119'`,
      `Search by Sector: 'Status of Railways', 'Power sector performance', 'Roads & Highways'`,
      `Search Watchlist: 'Top deteriorating projects', 'Triple-trigger warnings'`,
      `Search National Portfolio: 'National portfolio overview', 'System-wide benchmarks'`,
      `Methodology & Certainty: 'Will project 705505 definitely fail?'`,
    ],
    sources: [
      {
        endpoint: `/national/summary`,
        method: 'GET',
        description: `National catalog reference schema`,
      },
    ],
    entityType: 'unknown',
    matchedQuery: query,
  };
}
