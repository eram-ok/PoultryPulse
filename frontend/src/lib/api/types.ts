export interface DashboardProductionSummary {
  today_total_eggs: number
  today_saleable_eggs: number
  today_damaged_or_rejected: number
  today_birds_present: number
  today_laying_percentage: string
  month_total_eggs: number
  month_average_laying_percentage: string
}

export interface DashboardInventorySummary {
  total_eggs_in_stock: number
  saleable_eggs_in_stock: number
  total_feed_kg: string
  low_stock_feed_items: number
}

export interface DashboardFlockSummary {
  active_flocks: number
  current_bird_population: number
  losses_last_7_days: number
  mortality_rate_last_7_days: string
}

export interface DashboardHealthSummary {
  open_health_incidents: number
  critical_health_incidents: number
  vaccinations_due_next_7_days: number
  overdue_vaccinations: number
}

export interface DashboardSalesSummary {
  month_sales_revenue: string
  month_amount_received: string
  outstanding_customer_balance: string
  customers_over_credit_limit: number
}

export interface DashboardFinanceSummary {
  current_cash_balance: string
  month_operating_expenses: string
  outstanding_supplier_payables: string
  overdue_supplier_bills: number
  month_net_cash_flow: string
}

export interface DashboardResponse {
  as_of_date: string
  production: DashboardProductionSummary
  inventory: DashboardInventorySummary
  flocks: DashboardFlockSummary
  health: DashboardHealthSummary
  sales: DashboardSalesSummary
  finance: DashboardFinanceSummary
  active_alert_count: number
  critical_alert_count: number
}

export type TrendMetric =
  | "EGG_PRODUCTION"
  | "SALES_REVENUE"
  | "OPERATING_EXPENSES"
  | "FEED_USAGE"
  | "BIRD_LOSSES"

export interface TrendPoint {
  metric_date: string
  value: string
}

export interface TrendSeries {
  metric: TrendMetric
  points: TrendPoint[]
}

export interface TrendReportResponse {
  date_from: string
  date_to: string
  series: TrendSeries[]
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

export interface OperationalAlertListResponse {
  items: OperationalAlert[]
  total: number
  critical: number
  warning: number
  info: number
}

export interface AlertCountsResponse {
  total_active: number
  unread: number
  open: number
  acknowledged: number
  critical: number
  assigned_to_me: number
}
