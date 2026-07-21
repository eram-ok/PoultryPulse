import Link from "next/link"
import {
  ArrowUpRight,
  BellRing,
  CircleAlert,
  Info,
  TriangleAlert,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import type {
  AlertCountsResponse,
  OperationalAlert,
} from "@/lib/api/types"
import { cn } from "@/lib/utils"

interface AlertsPanelProps {
  alerts: OperationalAlert[]
  counts: AlertCountsResponse | null
  canViewAlerts: boolean
}

const severityStyle = {
  CRITICAL: {
    icon: CircleAlert,
    className: "bg-destructive/12 text-destructive",
  },
  WARNING: {
    icon: TriangleAlert,
    className: "bg-warning/12 text-warning",
  },
  INFO: {
    icon: Info,
    className: "bg-info/12 text-info",
  },
} as const

export function AlertsPanel({
  alerts,
  counts,
  canViewAlerts,
}: AlertsPanelProps) {
  const visibleAlerts = alerts.slice(0, 3)
  const activeCount =
    counts?.total_active ?? alerts.length

  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>Operational alerts</CardTitle>
            <CardDescription className="mt-1">
              Live conditions that may need attention.
            </CardDescription>
          </div>
          <Badge
            className={
              activeCount > 0
                ? "rounded-full bg-destructive text-white"
                : "rounded-full bg-primary text-primary-foreground"
            }
          >
            {activeCount} active
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {visibleAlerts.length > 0 ? (
          visibleAlerts.map((alert) => {
            const style = severityStyle[alert.severity]
            const Icon = style.icon

            return (
              <div
                key={`${alert.alert_type}-${alert.source_id ?? alert.title}`}
                className="group rounded-2xl border bg-muted/25 p-4 transition hover:bg-muted/45"
              >
                <div className="flex gap-3">
                  <div
                    className={cn(
                      "grid size-10 shrink-0 place-items-center rounded-2xl",
                      style.className,
                    )}
                  >
                    <Icon className="size-5" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold">
                      {alert.title}
                    </p>
                    <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                      {alert.message}
                    </p>
                    <p className="mt-2 text-[11px] text-muted-foreground">
                      {alert.detected_on} ·{" "}
                      {alert.source_module}
                    </p>
                  </div>
                  <ArrowUpRight className="size-4 text-muted-foreground opacity-0 transition group-hover:opacity-100" />
                </div>
              </div>
            )
          })
        ) : (
          <div className="grid min-h-48 place-items-center rounded-2xl border border-dashed bg-muted/20 text-center">
            <div className="max-w-xs px-5">
              <BellRing className="mx-auto size-6 text-primary" />
              <p className="mt-3 text-sm font-semibold">
                No active operational alerts
              </p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                PoultryPulse has not detected a condition
                requiring attention.
              </p>
            </div>
          </div>
        )}

        {canViewAlerts ? (
          <Button
            asChild
            variant="outline"
            className="w-full rounded-xl"
          >
            <Link href="/alerts">
              <BellRing className="size-4" />
              Open alert centre
            </Link>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  )
}
