"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  BarChart3,
  Download,
  Egg,
  FileChartColumn,
  RefreshCw,
  TrendingDown,
  TrendingUp,
  Wallet,
  Wheat,
} from "lucide-react"
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import {
  CommercialEmpty,
  CommercialLoading,
  CommercialMetric,
  CommercialPageHeader,
  RefreshButton,
  StatusBadge,
} from "@/components/commercial/commercial-ui"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { browserApiRequest } from "@/lib/api/browser"
import {
  formatDate,
  formatMoney,
  numeric,
  titleCase,
  todayIso,
} from "@/lib/commercial/format"
import type {
  CashFlowReport,
  ComparativeReport,
  ExecutiveSummary,
  PerformanceSummary,
  ProfitabilityReport,
  TrendMetric,
  TrendReport,
} from "@/lib/reports/types"

type ReportsTab =
  | "performance"
  | "trends"
  | "comparison"
  | "executive"
  | "finance"

const allMetrics: TrendMetric[] = [
  "EGG_PRODUCTION",
  "SALES_REVENUE",
  "OPERATING_EXPENSES",
  "FEED_USAGE",
  "BIRD_LOSSES",
]

function subtractDays(isoDate: string, days: number): string {
  const value = new Date(`${isoDate}T12:00:00Z`)
  value.setUTCDate(value.getUTCDate() - days)
  return value.toISOString().slice(0, 10)
}

function formatMetricValue(
  value: string,
  unit: string,
  currency: string,
): string {
  const normalizedUnit = unit.toLowerCase()
  const formatted = numeric(value).toLocaleString("en-UG")

  if (normalizedUnit.includes("currency")) {
    return formatMoney(value, currency)
  }

  if (normalizedUnit === "percent") {
    return `${numeric(value).toFixed(2)}%`
  }

  if (normalizedUnit === "kg") {
    return `${formatted} kg`
  }

  if (normalizedUnit === "eggs" || normalizedUnit === "birds") {
    return `${formatted} ${normalizedUnit}`
  }

  return formatted
}

export function ReportsWorkspace() {
  const { session } = useAuth()
  const currency = session.farm.currency_code || "UGX"
  const canViewFinance = session.permissions.includes("finance.reports")
  const canViewAlerts = session.permissions.includes("alerts.view")

  const defaultDateTo = todayIso()
  const [tab, setTab] = useState<ReportsTab>("performance")
  const [dateFrom, setDateFrom] = useState(
    subtractDays(defaultDateTo, 29),
  )
  const [dateTo, setDateTo] = useState(defaultDateTo)
  const [selectedMetrics, setSelectedMetrics] =
    useState<TrendMetric[]>(allMetrics)
  const [includeZeroDays, setIncludeZeroDays] = useState(true)
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const [performance, setPerformance] =
    useState<PerformanceSummary | null>(null)
  const [trends, setTrends] = useState<TrendReport | null>(null)
  const [comparison, setComparison] =
    useState<ComparativeReport | null>(null)
  const [executive, setExecutive] =
    useState<ExecutiveSummary | null>(null)
  const [cashFlow, setCashFlow] =
    useState<CashFlowReport | null>(null)
  const [profitability, setProfitability] =
    useState<ProfitabilityReport | null>(null)

  const load = useCallback(async () => {
    if (!dateFrom || !dateTo || dateFrom > dateTo) {
      toast.error("Choose a valid report date range.")
      return
    }

    setLoading(true)

    try {
      const range = `date_from=${dateFrom}&date_to=${dateTo}`

      if (tab === "performance") {
        setPerformance(
          await browserApiRequest<PerformanceSummary>(
            `/reports/performance?${range}`,
          ),
        )
      } else if (tab === "trends") {
        const metricParameters = selectedMetrics
          .map((metric) => `metrics=${encodeURIComponent(metric)}`)
          .join("&")

        setTrends(
          await browserApiRequest<TrendReport>(
            `/reports/trends?${range}&${metricParameters}&include_zero_days=${includeZeroDays}`,
          ),
        )
      } else if (tab === "comparison") {
        setComparison(
          await browserApiRequest<ComparativeReport>(
            `/reports/comparison?${range}`,
          ),
        )
      } else if (tab === "executive") {
        setExecutive(
          await browserApiRequest<ExecutiveSummary>(
            `/reports/executive-summary?${range}&as_of_date=${dateTo}`,
          ),
        )
      } else if (canViewFinance) {
        const [cashResponse, profitabilityResponse] = await Promise.all([
          browserApiRequest<CashFlowReport>(
            `/finance/reports/cash-flow?${range}`,
          ),
          browserApiRequest<ProfitabilityReport>(
            `/finance/reports/profitability?${range}`,
          ),
        ])

        setCashFlow(cashResponse)
        setProfitability(profitabilityResponse)
      }
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Report data could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [
    canViewFinance,
    dateFrom,
    dateTo,
    includeZeroDays,
    selectedMetrics,
    tab,
  ])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  const chartRows = useMemo(() => {
    if (!trends) return []

    const rows = new Map<string, Record<string, string | number>>()

    for (const series of trends.series) {
      for (const point of series.points) {
        const current = rows.get(point.metric_date) ?? {
          date: point.metric_date,
        }

        current[series.metric] = numeric(point.value)
        rows.set(point.metric_date, current)
      }
    }

    return Array.from(rows.values())
  }, [trends])

  function changeTab(value: string) {
    setTab(value as ReportsTab)
  }

  function toggleMetric(metric: TrendMetric) {
    setSelectedMetrics((current) =>
      current.includes(metric)
        ? current.filter((item) => item !== metric)
        : [...current, metric],
    )
  }

  function exportHref(type: "performance" | "trends" | "alerts") {
    const range = `date_from=${dateFrom}&date_to=${dateTo}`

    if (type === "performance") {
      return `/api/backend/reports/exports/performance.csv?${range}`
    }

    if (type === "alerts") {
      return `/api/backend/reports/exports/alerts.csv?as_of_date=${dateTo}`
    }

    const metrics = selectedMetrics
      .map((metric) => `metrics=${encodeURIComponent(metric)}`)
      .join("&")

    return `/api/backend/reports/exports/trends.csv?${range}&${metrics}&include_zero_days=${includeZeroDays}`
  }

  function content() {
    if (loading) {
      return <CommercialLoading label="Loading analytics..." />
    }

    if (tab === "performance") {
      if (!performance) {
        return (
          <CommercialEmpty
            title="Performance report unavailable"
            description="Refresh the page or choose another date range."
          />
        )
      }

      return (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <CommercialMetric
            label="Eggs produced"
            value={performance.total_eggs_produced.toLocaleString("en-UG")}
            detail={`${performance.saleable_eggs_produced.toLocaleString("en-UG")} saleable`}
            icon={Egg}
          />
          <CommercialMetric
            label="Laying rate"
            value={`${numeric(performance.average_laying_percentage).toFixed(2)}%`}
            detail={`${performance.damaged_or_rejected_eggs.toLocaleString("en-UG")} damaged or rejected`}
            icon={BarChart3}
          />
          <CommercialMetric
            label="Feed used"
            value={`${numeric(performance.total_feed_used_kg).toLocaleString("en-UG")} kg`}
            detail={`${numeric(performance.feed_kg_per_100_birds).toFixed(3)} kg per 100 birds`}
            icon={Wheat}
          />
          <CommercialMetric
            label="Estimated profit"
            value={formatMoney(performance.estimated_profit, currency)}
            detail={`${numeric(performance.profit_margin_percent).toFixed(2)}% margin`}
            icon={TrendingUp}
          />

          <Card className="rounded-2xl sm:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Commercial performance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {[
                ["Sales revenue", performance.sales_revenue],
                ["Operating expenses", performance.operating_expenses],
                ["Supplier bill costs", performance.supplier_bill_costs],
                ["Estimated profit", performance.estimated_profit],
              ].map(([label, value]) => (
                <div
                  key={label}
                  className="flex items-center justify-between rounded-xl border p-3"
                >
                  <span className="text-sm text-muted-foreground">
                    {label}
                  </span>
                  <strong>{formatMoney(value, currency)}</strong>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-2xl sm:col-span-2">
            <CardHeader>
              <CardTitle className="text-base">Flock efficiency</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-xl border p-4">
                <p className="text-xs text-muted-foreground">
                  Bird losses
                </p>
                <p className="mt-1 text-2xl font-semibold">
                  {performance.total_bird_losses.toLocaleString("en-UG")}
                </p>
              </div>
              <div className="rounded-xl border p-4">
                <p className="text-xs text-muted-foreground">
                  Mortality rate
                </p>
                <p className="mt-1 text-2xl font-semibold">
                  {numeric(performance.mortality_rate_percent).toFixed(2)}%
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )
    }

    if (tab === "trends") {
      if (!trends || chartRows.length === 0) {
        return (
          <CommercialEmpty
            title="No trend data"
            description="There are no data points for the selected metrics and period."
          />
        )
      }

      return (
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Operational trends</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[430px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartRows}>
                  <CartesianGrid
                    vertical={false}
                    stroke="var(--border)"
                    strokeDasharray="4 6"
                  />
                  <XAxis
                    dataKey="date"
                    tickFormatter={(value: string) =>
                      new Intl.DateTimeFormat("en-UG", {
                        day: "2-digit",
                        month: "short",
                      }).format(new Date(`${value}T12:00:00Z`))
                    }
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                  />
                  <YAxis
                    tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                  />
                  <Tooltip
                    contentStyle={{
                      background: "var(--popover)",
                      border: "1px solid var(--border)",
                      borderRadius: "0.75rem",
                    }}
                  />
                  <Legend />
                  {trends.series.map((series, index) => (
                    <Line
                      key={series.metric}
                      type="monotone"
                      dataKey={series.metric}
                      stroke={`var(--chart-${(index % 5) + 1})`}
                      strokeWidth={2.5}
                      dot={false}
                      activeDot={{ r: 5 }}
                    />
                  ))}
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )
    }

    if (tab === "comparison") {
      if (!comparison) {
        return (
          <CommercialEmpty
            title="Comparison unavailable"
            description="Refresh the report to compare this period with the immediately preceding period."
          />
        )
      }

      return (
        <div className="space-y-4">
          <div className="rounded-2xl border bg-card p-4 text-sm text-muted-foreground">
            Current: {formatDate(comparison.current_date_from)} to{" "}
            {formatDate(comparison.current_date_to)} · Previous:{" "}
            {formatDate(comparison.previous_date_from)} to{" "}
            {formatDate(comparison.previous_date_to)}
          </div>

          <div className="divide-y overflow-hidden rounded-2xl border bg-card">
            {comparison.metrics.map((metric) => (
              <div
                key={metric.metric}
                className="grid gap-4 p-4 lg:grid-cols-[1.4fr_1fr_1fr_1fr] lg:items-center"
              >
                <div>
                  <p className="font-semibold">{metric.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {titleCase(metric.metric)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">
                    Current
                  </p>
                  <p className="font-medium">
                    {formatMetricValue(
                      metric.current_value,
                      metric.unit,
                      currency,
                    )}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">
                    Previous
                  </p>
                  <p className="font-medium">
                    {formatMetricValue(
                      metric.previous_value,
                      metric.unit,
                      currency,
                    )}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  {metric.direction === "INCREASE" ? (
                    <ArrowUpRight className="size-4 text-emerald-600" />
                  ) : metric.direction === "DECREASE" ? (
                    <ArrowDownRight className="size-4 text-destructive" />
                  ) : (
                    <RefreshCw className="size-4 text-muted-foreground" />
                  )}
                  <div>
                    <p className="font-semibold">
                      {metric.percent_change === null
                        ? "New"
                        : `${numeric(metric.percent_change).toFixed(2)}%`}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {titleCase(metric.direction)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )
    }

    if (tab === "executive") {
      if (!executive) {
        return (
          <CommercialEmpty
            title="Executive summary unavailable"
            description="Refresh to generate management highlights and priority alerts."
          />
        )
      }

      return (
        <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
          <Card className="rounded-2xl">
            <CardHeader>
              <CardTitle className="text-base">
                Management highlights
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {executive.highlights.map((highlight, index) => (
                <div
                  key={`${highlight.title}-${index}`}
                  className="rounded-2xl border p-4"
                >
                  <div className="flex items-center gap-2">
                    <StatusBadge status={highlight.severity} />
                    <p className="font-semibold">{highlight.title}</p>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {highlight.message}
                  </p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-2xl">
            <CardHeader>
              <CardTitle className="text-base">
                Operational alerts
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">
                  {executive.alerts.critical} critical
                </Badge>
                <Badge variant="outline">
                  {executive.alerts.warning} warnings
                </Badge>
                <Badge variant="outline">
                  {executive.alerts.info} information
                </Badge>
              </div>

              {executive.alerts.items.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No operational alerts for this reporting date.
                </p>
              ) : (
                executive.alerts.items.slice(0, 8).map((alert) => (
                  <div
                    key={`${alert.alert_type}-${alert.source_id ?? alert.title}`}
                    className="rounded-2xl border p-4"
                  >
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="size-4 text-warning" />
                      <p className="font-semibold">{alert.title}</p>
                    </div>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {alert.message}
                    </p>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      )
    }

    if (!canViewFinance) {
      return (
        <CommercialEmpty
          title="Finance reports restricted"
          description="Your role does not include the finance.reports permission."
        />
      )
    }

    if (!cashFlow || !profitability) {
      return (
        <CommercialEmpty
          title="Finance analytics unavailable"
          description="Refresh the report or choose another period."
        />
      )
    }

    return (
      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Cash flow</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <CommercialMetric
              label="Inflows"
              value={formatMoney(cashFlow.total_inflows, currency)}
              detail="Cash received in period"
              icon={TrendingUp}
            />
            <CommercialMetric
              label="Outflows"
              value={formatMoney(cashFlow.total_outflows, currency)}
              detail="Cash paid in period"
              icon={TrendingDown}
            />
            <CommercialMetric
              label="Net cash flow"
              value={formatMoney(cashFlow.net_cash_flow, currency)}
              detail="Inflows less outflows"
              icon={Wallet}
            />
            <CommercialMetric
              label="Current balance"
              value={formatMoney(cashFlow.current_balance, currency)}
              detail="Running cash-ledger balance"
              icon={Wallet}
            />
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Profitability</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              ["Sales revenue", profitability.sales_revenue],
              ["Operating expenses", profitability.operating_expenses],
              ["Supplier bill costs", profitability.supplier_bill_costs],
              ["Total costs", profitability.total_costs],
              ["Gross profit", profitability.gross_profit],
            ].map(([label, value]) => (
              <div
                key={label}
                className="flex items-center justify-between rounded-xl border p-3"
              >
                <span className="text-sm text-muted-foreground">
                  {label}
                </span>
                <strong>{formatMoney(value, currency)}</strong>
              </div>
            ))}
            <div className="rounded-xl bg-primary/10 p-4">
              <p className="text-xs text-muted-foreground">
                Profit margin
              </p>
              <p className="mt-1 text-2xl font-semibold text-primary">
                {numeric(profitability.profit_margin_percent).toFixed(2)}%
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Management intelligence"
        title="Reports and analytics"
        description="Analyze production, feed, flock losses, sales, expenses, cash flow, profitability, comparisons, and executive priorities."
        actions={
          <>
            <RefreshButton
              onClick={() => setRefreshKey((current) => current + 1)}
              loading={loading}
            />
            <Button asChild variant="outline" className="rounded-xl">
              <a href={exportHref("performance")}>
                <Download className="size-4" />
                Performance CSV
              </a>
            </Button>
            <Button asChild variant="outline" className="rounded-xl">
              <a href={exportHref("trends")}>
                <Download className="size-4" />
                Trends CSV
              </a>
            </Button>
            {canViewAlerts ? (
              <Button asChild variant="outline" className="rounded-xl">
                <a href={exportHref("alerts")}>
                  <Download className="size-4" />
                  Alerts CSV
                </a>
              </Button>
            ) : null}
          </>
        }
      />

      <Card className="rounded-2xl">
        <CardContent className="grid gap-4 p-4 lg:grid-cols-[180px_180px_1fr] lg:items-end">
          <div className="space-y-2">
            <Label htmlFor="report-date-from">Date from</Label>
            <Input
              id="report-date-from"
              type="date"
              value={dateFrom}
              max={dateTo}
              onChange={(event) => setDateFrom(event.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="report-date-to">Date to</Label>
            <Input
              id="report-date-to"
              type="date"
              value={dateTo}
              min={dateFrom}
              max={todayIso()}
              onChange={(event) => setDateTo(event.target.value)}
            />
          </div>
          <Tabs value={tab} onValueChange={changeTab}>
            <TabsList className="h-auto flex-wrap rounded-xl">
              <TabsTrigger value="performance">Performance</TabsTrigger>
              <TabsTrigger value="trends">Trends</TabsTrigger>
              <TabsTrigger value="comparison">Comparison</TabsTrigger>
              <TabsTrigger value="executive">Executive</TabsTrigger>
              <TabsTrigger value="finance">Finance</TabsTrigger>
            </TabsList>
          </Tabs>
        </CardContent>
      </Card>

      {tab === "trends" ? (
        <Card className="rounded-2xl">
          <CardContent className="flex flex-wrap gap-4 p-4">
            {allMetrics.map((metric) => (
              <label
                key={metric}
                className="flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-sm"
              >
                <Checkbox
                  checked={selectedMetrics.includes(metric)}
                  onCheckedChange={() => toggleMetric(metric)}
                />
                {titleCase(metric)}
              </label>
            ))}
            <label className="flex cursor-pointer items-center gap-2 rounded-xl border px-3 py-2 text-sm">
              <Checkbox
                checked={includeZeroDays}
                onCheckedChange={(checked) =>
                  setIncludeZeroDays(checked === true)
                }
              />
              Include zero-value days
            </label>
          </CardContent>
        </Card>
      ) : null}

      {content()}

      <Card className="rounded-2xl border-dashed">
        <CardContent className="flex items-start gap-3 p-4 text-sm text-muted-foreground">
          <FileChartColumn className="mt-0.5 size-5 shrink-0 text-primary" />
          <p>
            Reports are calculated from confirmed production, inventory,
            sales, payments, expenses, supplier bills, feed usage, health,
            and bird-loss records. Draft or reversed records are excluded
            according to backend business rules.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
