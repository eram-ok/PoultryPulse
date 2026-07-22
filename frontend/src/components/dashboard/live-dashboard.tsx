"use client"

import {
  useCallback,
  useEffect,
  useState,
} from "react"
import {
  Bird,
  CircleDollarSign,
  Egg,
  Gauge,
} from "lucide-react"

import { useAuth } from "@/components/auth/auth-provider"
import { AlertsPanel } from "@/components/dashboard/alerts-panel"
import { DashboardError } from "@/components/dashboard/dashboard-error"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DashboardLoading } from "@/components/dashboard/dashboard-loading"
import { FeedStockChart } from "@/components/dashboard/feed-stock-chart"
import { FlockHealthCard } from "@/components/dashboard/flock-health-card"
import { InventoryOverview } from "@/components/dashboard/inventory-overview"
import { KpiCard } from "@/components/dashboard/kpi-card"
import {
  ProductionTrendChart,
  type ProductionTrendPoint,
} from "@/components/dashboard/production-trend-chart"
import {
  RecentActivity,
  type OperationalSummaryItem,
} from "@/components/dashboard/recent-activity"
import {
  BrowserApiError,
  browserApiRequest,
} from "@/lib/api/browser"
import type {
  AlertCountsResponse,
  DashboardResponse,
  OperationalAlertListResponse,
  TrendReportResponse,
} from "@/lib/api/types"
import {
  formatCurrency,
  formatNumber,
  formatPercent,
  toNumber,
} from "@/lib/utils"

interface DashboardState {
  dashboard: DashboardResponse
  trends: TrendReportResponse | null
  alerts: OperationalAlertListResponse | null
  counts: AlertCountsResponse | null
}

function subtractDays(
  isoDate: string,
  days: number,
): string {
  const date = new Date(`${isoDate}T12:00:00Z`)
  date.setUTCDate(date.getUTCDate() - days)
  return date.toISOString().slice(0, 10)
}

function formatDay(isoDate: string): string {
  return new Intl.DateTimeFormat("en-UG", {
    weekday: "short",
    timeZone: "UTC",
  }).format(new Date(`${isoDate}T12:00:00Z`))
}

export function LiveDashboard() {
  const { session } = useAuth()
  const [state, setState] =
    useState<DashboardState | null>(null)
  const [error, setError] = useState<string | null>(
    null,
  )
  const [requestVersion, setRequestVersion] =
    useState(0)

  const loadDashboard = useCallback(
    async (signal: AbortSignal) => {
      try {
        const dashboard =
          await browserApiRequest<DashboardResponse>(
            "/reports/dashboard",
            { signal },
          )

        const canViewReports =
          session.permissions.includes("reports.view")
        const canViewAlerts =
          session.permissions.includes("alerts.view")
        const dateTo = dashboard.as_of_date
        const dateFrom = subtractDays(dateTo, 6)

        const [trends, alerts, counts] =
          await Promise.all([
            canViewReports
              ? browserApiRequest<TrendReportResponse>(
                  `/reports/trends?date_from=${dateFrom}&date_to=${dateTo}&metrics=EGG_PRODUCTION&include_zero_days=true`,
                  { signal },
                )
              : Promise.resolve(null),
            canViewAlerts
              ? browserApiRequest<OperationalAlertListResponse>(
                  `/reports/alerts?as_of_date=${dateTo}`,
                  { signal },
                )
              : Promise.resolve(null),
            canViewAlerts
              ? browserApiRequest<AlertCountsResponse>(
                  "/alerts/counts",
                  { signal },
                )
              : Promise.resolve(null),
          ])

        setState({
          dashboard,
          trends,
          alerts,
          counts,
        })
      } catch (caught) {
        if (
          caught instanceof DOMException &&
          caught.name === "AbortError"
        ) {
          return
        }

        if (caught instanceof BrowserApiError) {
          if (caught.status === 403) {
            setError(
              "Your account does not have permission to view the farm dashboard.",
            )
            return
          }

          setError(caught.message)
          return
        }

        setError(
          "PoultryPulse could not load live farm data. Confirm that the backend and PostgreSQL are running.",
        )
      }
    },
    [session.permissions],
  )

  useEffect(() => {
    const controller = new AbortController()
    // The state updates occur after asynchronous API responses.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadDashboard(controller.signal)

    return () => controller.abort()
  }, [loadDashboard, requestVersion])

  if (error) {
    return (
      <DashboardError
        message={error}
        onRetry={() => {
          setError(null)
          setState(null)
          setRequestVersion(
            (current) => current + 1,
          )
        }}
      />
    )
  }

  if (!state) {
    return <DashboardLoading />
  }

  const {
    dashboard,
    trends,
    alerts,
    counts,
  } = state
  const eggSeries = trends?.series.find(
    (series) =>
      series.metric === "EGG_PRODUCTION",
  )
  const productionThresholdPercent = toNumber(
    session.farm.settings
      ?.low_production_threshold ??
      dashboard.production
        .month_average_laying_percentage,
  )
  const targetEggs = Math.max(
    0,
    Math.round(
      (dashboard.production.today_birds_present *
        productionThresholdPercent) /
        100,
    ),
  )
  const productionPoints: ProductionTrendPoint[] =
    eggSeries?.points.map((point) => ({
      day: formatDay(point.metric_date),
      eggs: toNumber(point.value),
      target: targetEggs,
    })) ?? [
      {
        day: formatDay(dashboard.as_of_date),
        eggs:
          dashboard.production.today_total_eggs,
        target: targetEggs,
      },
    ]
  const productionValues = productionPoints.map(
    (point) => point.eggs,
  )
  const productionTotal = productionValues.reduce(
    (sum, value) => sum + value,
    0,
  )
  const productionAverage =
    productionValues.length > 0
      ? productionTotal / productionValues.length
      : 0
  const targetAttainment =
    targetEggs > 0 && productionValues.length > 0
      ? (productionTotal /
          (targetEggs * productionValues.length)) *
        100
      : 0
  const saleableRate =
    dashboard.production.today_total_eggs > 0
      ? (dashboard.production.today_saleable_eggs /
          dashboard.production.today_total_eggs) *
        100
      : 0
  const netCashFlow = toNumber(
    dashboard.finance.month_net_cash_flow,
  )
  const revenue = toNumber(
    dashboard.sales.month_sales_revenue,
  )
  const received = toNumber(
    dashboard.sales.month_amount_received,
  )
  const losses = dashboard.flocks.losses_last_7_days
  const alertItems = alerts?.items ?? []
  const canViewAlerts =
    session.permissions.includes("alerts.view")

  const summaryItems: OperationalSummaryItem[] = [
    {
      event: "Egg production",
      module: "Production",
      value: formatNumber(
        dashboard.production.today_total_eggs,
      ),
      detail: `${formatPercent(
        toNumber(
          dashboard.production
            .today_laying_percentage,
        ),
      )} laying rate`,
      status:
        dashboard.production.today_total_eggs > 0
          ? "Recorded"
          : "Attention",
    },
    {
      event: "Feed inventory",
      module: "Feed",
      value: `${formatNumber(
        toNumber(dashboard.inventory.total_feed_kg),
        1,
      )} kg`,
      detail: `${dashboard.inventory.low_stock_feed_items} low-stock items`,
      status:
        dashboard.inventory.low_stock_feed_items > 0
          ? "Attention"
          : "Healthy",
    },
    {
      event: "Flock health",
      module: "Health",
      value: `${dashboard.health.open_health_incidents} open`,
      detail: `${dashboard.health.overdue_vaccinations} overdue vaccinations`,
      status:
        dashboard.health.critical_health_incidents >
          0 ||
        dashboard.health.overdue_vaccinations > 0
          ? "Attention"
          : "Healthy",
    },
    {
      event: "Net cash flow",
      module: "Finance",
      value: formatCurrency(
        netCashFlow,
        session.farm.currency_code,
      ),
      detail: `${dashboard.finance.overdue_supplier_bills} overdue supplier bills`,
      status:
        netCashFlow >= 0 ? "Healthy" : "Attention",
    },
  ]

  return (
    <div className="space-y-7 pb-24 lg:pb-10">
      <DashboardHeader
        session={session}
        dashboard={dashboard}
      />

      <section
        aria-label="Farm performance overview"
        className="grid items-start gap-4 sm:grid-cols-2 xl:grid-cols-4 2xl:gap-5"
      >
        <KpiCard
          title="Eggs collected today"
          value={formatNumber(
            dashboard.production.today_total_eggs,
          )}
          indicator={formatPercent(saleableRate)}
          indicatorLabel="saleable output"
          indicatorTone={
            saleableRate >= 95
              ? "positive"
              : "neutral"
          }
          icon={Egg}
          tone="emerald"
          sparkline={
            productionValues.length > 0
              ? productionValues
              : [0]
          }
        />
        <KpiCard
          title="Production rate"
          value={formatPercent(
            toNumber(
              dashboard.production
                .today_laying_percentage,
            ),
          )}
          indicator={formatPercent(
            toNumber(
              dashboard.production
                .month_average_laying_percentage,
            ),
          )}
          indicatorLabel="monthly average"
          indicatorTone={
            toNumber(
              dashboard.production
                .today_laying_percentage,
            ) >= productionThresholdPercent
              ? "positive"
              : "negative"
          }
          icon={Gauge}
          tone="amber"
          sparkline={[
            toNumber(
              dashboard.production
                .month_average_laying_percentage,
            ),
            toNumber(
              dashboard.production
                .today_laying_percentage,
            ),
          ]}
        />
        <KpiCard
          title="Active birds"
          value={formatNumber(
            dashboard.flocks
              .current_bird_population,
          )}
          indicator={formatNumber(losses)}
          indicatorLabel="losses in seven days"
          indicatorTone={
            losses > 0 ? "negative" : "positive"
          }
          icon={Bird}
          tone="blue"
          sparkline={[
            dashboard.flocks
              .current_bird_population + losses,
            dashboard.flocks
              .current_bird_population,
          ]}
        />
        <KpiCard
          title="Revenue this month"
          value={formatCurrency(
            revenue,
            session.farm.currency_code,
          )}
          indicator={formatCurrency(
            netCashFlow,
            session.farm.currency_code,
          )}
          indicatorLabel="net cash flow"
          indicatorTone={
            netCashFlow >= 0
              ? "positive"
              : "negative"
          }
          icon={CircleDollarSign}
          tone="violet"
          sparkline={[received, revenue]}
        />
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,0.85fr)]">
        <ProductionTrendChart
          data={productionPoints}
          total={productionTotal}
          average={productionAverage}
          targetAttainment={targetAttainment}
        />
        <AlertsPanel
          alerts={alertItems}
          counts={counts}
          canViewAlerts={canViewAlerts}
        />
      </section>

      <section className="grid gap-5 lg:grid-cols-2 xl:grid-cols-3">
        <FeedStockChart
          totalFeedKg={toNumber(
            dashboard.inventory.total_feed_kg,
          )}
          lowStockItems={
            dashboard.inventory
              .low_stock_feed_items
          }
        />
        <InventoryOverview
          totalEggs={
            dashboard.inventory.total_eggs_in_stock
          }
          saleableEggs={
            dashboard.inventory
              .saleable_eggs_in_stock
          }
          damagedToday={
            dashboard.production
              .today_damaged_or_rejected
          }
          canViewInventory={session.permissions.includes(
            "eggs.view",
          )}
        />
        <FlockHealthCard
          flocks={dashboard.flocks}
          health={dashboard.health}
        />
      </section>

      <RecentActivity
        items={summaryItems}
        canViewAudit={session.permissions.includes(
          "audit.view",
        )}
      />
    </div>
  )
}
