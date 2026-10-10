export interface ConfidenceParts {
  source_reliability?: number
  corroboration?: number
  sentiment_agreement?: number
  self_consistency?: number
  claim_certainty?: number
  hype_penalty_applied?: number
  [key: string]: number | undefined
}

export interface Signal {
  signal_id: string
  timestamp: string
  source: string
  source_type: 'news' | 'social'
  headline: string
  entity: string
  ticker?: string | null
  sector?: string | null
  country?: string | null
  themes: string[]
  sentiment_score: number
  event_class: string
  impact_score: number
  calibrated_move_pct?: number | null
  calibrated_low_pct?: number | null
  calibrated_high_pct?: number | null
  calibrated_explanation?: string | null
  confidence: number
  rationale: string
  trigger_eligible: boolean
  finbert_sentiment?: number | null
  confidence_parts?: ConfidenceParts
  model_versions: Record<string, string>
  // UI runtime state
  outcome_type?: 'stress_result' | 'suppressed' | 'merged'
  suppression_reason?: string
  merged_into?: string
}

export interface PositionImpact {
  position_id: string
  counterparty: string
  asset_type: string
  sector: string
  country: string
  market_value: number
  pnl: number
  pnl_pct: number
  theme?: string | null
  tag?: string | null
  rule_source?: 'measured' | 'assumed' | null
  why: string
}

export interface WaterfallItem {
  label: string
  position_id?: string | null
  pnl: number
}

export interface StressResult {
  scenario_id: string
  lead_signal_id?: string | null
  corroborating_signal_ids: string[]
  themes: string[]
  severity_scale: number
  headline_move_pct: number
  total_before: number
  total_after: number
  pnl_abs: number
  pnl_pct: number
  naive_pnl_abs: number
  naive_pnl_pct: number
  positions_hit: number
  by_asset_type: Record<string, number>
  by_sector: Record<string, number>
  by_country: Record<string, number>
  top_losers: PositionImpact[]
  top_winners: PositionImpact[]
  waterfall: WaterfallItem[]
  positions: PositionImpact[]
}

export interface Position {
  position_id: string
  asset_type: string
  subtype: string
  counterparty: string
  ticker: string
  sector: string
  country: string
  region: string
  rating: string
  market_value: number
  notional: number
  duration: number
  maturity_years: number
  delta: number
  collateral_pct: number
  tags: string[]
  synthetic: boolean
}

export interface PortfolioData {
  synthetic: boolean
  total_market_value: number
  n_positions: number
  by_asset_type: Record<string, number>
  by_sector: Record<string, number>
  by_country: Record<string, number>
  by_tag: Record<string, number>
  positions: Position[]
}

export interface BucketStat {
  bucket: string
  impact_range: string
  n: number
  median_car_pct: number
  p25_pct: number
  p75_pct: number
  iqr_pct: number
}

export interface CalibrationCurvePoint {
  impact: number
  move_pct: number
  low_pct: number
  high_pct: number
}

export interface CalibrationPoint {
  event_id: string
  event_date: string
  affected_ticker: string
  engine_impact: number
  realized_car: number
  abs_car: number
}

export interface CalibrationData {
  fit: {
    n_events: number
    model_type: string
    slope: number
    intercept: number
    r_squared: number
    spearman_rho: number
    spearman_pvalue: number
    loo_mae_linear: number
    loo_mae_isotonic: number
    residual_std: number
    bootstrap_slope_80_ci: [number, number]
  }
  buckets: BucketStat[]
  points: CalibrationPoint[]
  curve: CalibrationCurvePoint[]
}

export interface Preset {
  id: string
  label: string
  text: string
  source: string
  source_type: string
}

export interface HealthInfo {
  status: string
  service: string
  mode: string
  offline_mode: boolean
  signal_count: number
  extractors: {
    llm: number
    'rules-fallback': number
  }
  all_fallback: boolean
  data_versions: {
    signals_sha?: string | null
    portfolio_positions?: number
    portfolio_sha?: string | null
    shock_table_rows?: number
    calibration_events?: number | null
  }
}
