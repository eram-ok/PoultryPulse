import type { LucideIcon } from "lucide-react"
import { ArrowDownRight, ArrowUpRight } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

const toneStyles = {
  emerald: {
    icon: "bg-primary/12 text-primary",
    line: "bg-primary",
    area: "bg-primary/8",
  },
  amber: {
    icon: "bg-warning/14 text-warning",
    line: "bg-warning",
    area: "bg-warning/8",
  },
  blue: {
    icon: "bg-info/14 text-info",
    line: "bg-info",
    area: "bg-info/8",
  },
  violet: {
    icon: "bg-chart-5/14 text-chart-5",
    line: "bg-chart-5",
    area: "bg-chart-5/8",
  },
} as const

interface KpiCardProps {
  title: string
  value: string
  change: string
  changeLabel: string
  icon: LucideIcon
  tone: keyof typeof toneStyles
  sparkline: number[]
}

export function KpiCard({
  title,
  value,
  change,
  changeLabel,
  icon: Icon,
  tone,
  sparkline,
}: KpiCardProps) {
  const positive = change.startsWith("+")
  const styles = toneStyles[tone]
  const max = Math.max(...sparkline)

  return (
    <Card className="metric-glow overflow-hidden rounded-2xl border-border/70 bg-card/82 py-0 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between px-5 pb-2 pt-5">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div
          className={cn(
            "grid size-10 place-items-center rounded-2xl",
            styles.icon,
          )}
        >
          <Icon className="size-5" />
        </div>
      </CardHeader>
      <CardContent className="px-5 pb-5">
        <p className="font-mono text-2xl font-semibold tracking-tight sm:text-[28px]">
          {value}
        </p>

        <div className="mt-4 flex h-9 items-end gap-1">
          {sparkline.map((point, index) => (
            <span
              key={`${title}-${index}`}
              className={cn(
                "min-w-0 flex-1 rounded-t-sm opacity-80",
                styles.line,
              )}
              style={{
                height: `${Math.max(18, (point / max) * 100)}%`,
              }}
            />
          ))}
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span
            className={cn(
              "inline-flex items-center font-semibold",
              positive ? "text-primary" : "text-destructive",
            )}
          >
            {positive ? (
              <ArrowUpRight className="size-3.5" />
            ) : (
              <ArrowDownRight className="size-3.5" />
            )}
            {change}
          </span>
          <span className="truncate text-muted-foreground">
            {changeLabel}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
