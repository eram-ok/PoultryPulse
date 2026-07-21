import {
  Activity,
  AlertTriangle,
  Bird,
  Syringe,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type {
  DashboardFlockSummary,
  DashboardHealthSummary,
} from "@/lib/api/types"
import {
  formatNumber,
  formatPercent,
  toNumber,
} from "@/lib/utils"

interface FlockHealthCardProps {
  flocks: DashboardFlockSummary
  health: DashboardHealthSummary
}

export function FlockHealthCard({
  flocks,
  health,
}: FlockHealthCardProps) {
  const mortality = toNumber(
    flocks.mortality_rate_last_7_days,
  )
  const healthScore = Math.max(
    0,
    Math.min(
      100,
      100 -
        mortality * 10 -
        health.critical_health_incidents * 15 -
        health.overdue_vaccinations * 5,
    ),
  )

  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Flock health</CardTitle>
            <CardDescription className="mt-1">
              Live population, mortality, and health
              indicators.
            </CardDescription>
          </div>
          <div className="grid size-10 place-items-center rounded-2xl bg-info/10 text-info">
            <Activity className="size-5" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="rounded-2xl border bg-muted/28 p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-sm font-semibold">
                Current population
              </p>
              <p className="mt-1 font-mono text-2xl font-semibold">
                {formatNumber(
                  flocks.current_bird_population,
                )}
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                {flocks.active_flocks} active flocks
              </p>
            </div>
            <Bird className="size-5 text-primary" />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border bg-card/55 p-3.5">
            <AlertTriangle className="size-4 text-warning" />
            <p className="mt-3 text-xs text-muted-foreground">
              Seven-day losses
            </p>
            <p className="mt-1 font-mono text-lg font-semibold">
              {formatNumber(flocks.losses_last_7_days)}
            </p>
          </div>
          <div className="rounded-2xl border bg-card/55 p-3.5">
            <Syringe className="size-4 text-info" />
            <p className="mt-3 text-xs text-muted-foreground">
              Vaccinations due
            </p>
            <p className="mt-1 font-mono text-lg font-semibold">
              {health.vaccinations_due_next_7_days}
            </p>
          </div>
        </div>

        <div>
          <div className="mb-2 flex items-center justify-between gap-3 text-xs">
            <span className="text-muted-foreground">
              Operational health score
            </span>
            <Badge
              variant="outline"
              className={
                healthScore >= 85
                  ? "rounded-full border-primary/30 bg-primary/8 text-primary"
                  : "rounded-full border-warning/30 bg-warning/8 text-warning"
              }
            >
              {Math.round(healthScore)}%
            </Badge>
          </div>
          <Progress
            value={healthScore}
            className="h-2"
          />
          <p className="mt-2 text-[11px] text-muted-foreground">
            Mortality: {formatPercent(mortality)} · Open
            incidents: {health.open_health_incidents}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
