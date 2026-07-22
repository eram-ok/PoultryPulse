export type TrendMetric =
  | "EGG_PRODUCTION"
  | "SALES_REVENUE"
  | "OPERATING_EXPENSES"
  | "FEED_USAGE"
  | "BIRD_LOSSES"

export interface PerformanceSummary {
  date_from: string
  date_to: string
  total_eggs_produced: number
  saleable_eggs_produced: number
  damaged_or_rejected_eggs: number
  average_laying_percentage: string
  total_feed_used_kg: string
  feed_kg_per_100_birds: string
  total_bird_losses: number
  mortality_rate_percent: string
  sales_revenue: string
  operating_expenses: string
  supplier_bill_costs: string
  estimated_profit: string
  profit_margin_percent: string
}

export interface TrendPoint {
  metric_date: string
  value: string
}

export interface TrendSeries {
  metric: TrendMetric
  points: TrendPoint[]
}

export interface TrendReport {
  date_from: string
  date_to: string
  series: TrendSeries[]
}

export interface ComparisonMetric {
  metric: string
  label: string
  unit: string
  current_value: string
  previous_value: string
  absolute_change: string
  percent_change: string | null
  direction: "INCREASE" | "DECREASE" | "UNCHANGED"
}

export interface ComparativeReport {
  current_date_from: string
  current_date_to: string
  previous_date_from: string
  previous_date_to: string
  metrics: ComparisonMetric[]
}

export type AlertSeverity = "INFO" | "WARNING" | "CRITICAL"

export interface OperationalAlert {
  alert_type: string
  severity: AlertSeverity
  title: string
  message: string
  source_module: string
  source_id: string | null
  action_path: string | null
  detected_on: string
}

export interface OperationalAlertList {
  items: OperationalAlert[]
  total: number
  critical: number
  warning: number
  info: number
}

export interface ExecutiveHighlight {
  severity: AlertSeverity
  title: string
  message: string
}

export interface ExecutiveSummary {
  date_from: string
  date_to: string
  performance: PerformanceSummary
  alerts: OperationalAlertList
  highlights: ExecutiveHighlight[]
}

export interface CashFlowReport {
  date_from: string | null
  date_to: string | null
  total_inflows: string
  total_outflows: string
  net_cash_flow: string
  current_balance: string
  inflows_by_type: Record<string, string>
  outflows_by_type: Record<string, string>
}

export interface ProfitabilityReport {
  date_from: string | null
  date_to: string | null
  sales_revenue: string
  operating_expenses: string
  supplier_bill_costs: string
  total_costs: string
  gross_profit: string
  profit_margin_percent: string
  expenses_by_category: Record<string, string>
}
