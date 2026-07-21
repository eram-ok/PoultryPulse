import {
  Bird,
  CircleDollarSign,
  Egg,
  Gauge,
} from "lucide-react"

import { AlertsPanel } from "@/components/dashboard/alerts-panel"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { FeedStockChart } from "@/components/dashboard/feed-stock-chart"
import { FlockHealthCard } from "@/components/dashboard/flock-health-card"
import { InventoryOverview } from "@/components/dashboard/inventory-overview"
import { KpiCard } from "@/components/dashboard/kpi-card"
import { ProductionTrendChart } from "@/components/dashboard/production-trend-chart"
import { RecentActivity } from "@/components/dashboard/recent-activity"

export const metadata = {
  title: "Dashboard",
}

export default function DashboardPage() {
  return (
    <div className="space-y-6 pb-24 lg:pb-8">
      <DashboardHeader />

      <section
        aria-label="Farm performance overview"
        className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4"
      >
        <KpiCard
          title="Eggs collected today"
          value="8,460"
          change="+6.8%"
          changeLabel="from yesterday"
          icon={Egg}
          tone="emerald"
          sparkline={[34, 38, 35, 44, 48, 52, 58]}
        />
        <KpiCard
          title="Production rate"
          value="87.4%"
          change="+2.1%"
          changeLabel="seven-day average"
          icon={Gauge}
          tone="amber"
          sparkline={[63, 66, 64, 70, 73, 77, 81]}
        />
        <KpiCard
          title="Active birds"
          value="9,684"
          change="-0.3%"
          changeLabel="mortality adjusted"
          icon={Bird}
          tone="blue"
          sparkline={[82, 81, 81, 80, 80, 79, 79]}
        />
        <KpiCard
          title="Revenue this month"
          value="UGX 18.6M"
          change="+12.4%"
          changeLabel="versus last month"
          icon={CircleDollarSign}
          tone="violet"
          sparkline={[24, 29, 31, 36, 39, 45, 52]}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,0.85fr)]">
        <ProductionTrendChart />
        <AlertsPanel />
      </section>

      <section className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
        <FeedStockChart />
        <InventoryOverview />
        <FlockHealthCard />
      </section>

      <RecentActivity />
    </div>
  )
}
