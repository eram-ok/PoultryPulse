import {
  ArrowUpRight,
  BellRing,
  CheckCircle2,
  Clock3,
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
import { operationalAlerts } from "@/lib/demo-data"
import { cn } from "@/lib/utils"

const severityStyles = {
  warning: {
    icon: TriangleAlert,
    className: "bg-warning/12 text-warning",
  },
  success: {
    icon: CheckCircle2,
    className: "bg-primary/12 text-primary",
  },
} as const

export function AlertsPanel() {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <div>
            <CardTitle>Operational alerts</CardTitle>
            <CardDescription className="mt-1">
              Items that may need attention.
            </CardDescription>
          </div>
          <Badge className="rounded-full bg-destructive text-white">
            2 active
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {operationalAlerts.map((alert) => {
          const severity =
            severityStyles[
              alert.severity as keyof typeof severityStyles
            ]
          const Icon = severity.icon

          return (
            <div
              key={alert.title}
              className="group rounded-2xl border bg-muted/25 p-4 transition hover:bg-muted/45"
            >
              <div className="flex gap-3">
                <div
                  className={cn(
                    "grid size-10 shrink-0 place-items-center rounded-2xl",
                    severity.className,
                  )}
                >
                  <Icon className="size-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-semibold">
                    {alert.title}
                  </p>
                  <p className="mt-1 text-xs leading-5 text-muted-foreground">
                    {alert.detail}
                  </p>
                  <p className="mt-2 flex items-center gap-1 text-[11px] text-muted-foreground">
                    <Clock3 className="size-3" />
                    {alert.time}
                  </p>
                </div>
                <ArrowUpRight className="size-4 text-muted-foreground opacity-0 transition group-hover:opacity-100" />
              </div>
            </div>
          )
        })}

        <Button variant="outline" className="w-full rounded-xl">
          <BellRing className="size-4" />
          Open alert centre
        </Button>
      </CardContent>
    </Card>
  )
}
