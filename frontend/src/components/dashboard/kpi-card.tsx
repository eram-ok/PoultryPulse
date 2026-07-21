import type { LucideIcon } from "lucide-react"
import {
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
} from "lucide-react"

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
  },
  amber: {
    icon: "bg-warning/14 text-warning",
    line: "bg-warning",
  },
  blue: {
    icon: "bg-info/14 text-info",
    line: "bg-info",
  },
  violet: {
    icon: "bg-chart-5/14 text-chart-5",
    line: "bg-chart-5",
  },
} as const

interface KpiCardProps {
  title: string
  value: string
  indicator: string
  indicatorLabel: string
  indicatorTone: "positive" | "negative" | "neutral"
  icon: LucideIcon
  tone: keyof typeof toneStyles
  sparkline: number[]
}

export function KpiCard({
  title,
  value,
  indicator,
  indicatorLabel,
  indicatorTone,
  icon: Icon,
  tone,
  sparkline,
}: KpiCardProps) {
  const styles = toneStyles[tone]
  const max = Math.max(...sparkline, 1)
  const TrendIcon =
    indicatorTone === "positive"
      ? ArrowUpRight
      : indicatorTone === "negative"
        ? ArrowDownRight
        : ArrowRight

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
                height: `${Math.max(
                  12,
                  (Math.max(point, 0) / max) * 100,
                )}%`,
              }}
            />
          ))}
        </div>

        <div className="mt-3 flex items-center gap-1.5 text-xs">
          <span
            className={cn(
              "inline-flex items-center font-semibold",
              indicatorTone === "positive" &&
                "text-primary",
              indicatorTone === "negative" &&
                "text-destructive",
              indicatorTone === "neutral" &&
                "text-muted-foreground",
            )}
          >
            <TrendIcon className="size-3.5" />
            {indicator}
          </span>
          <span className="truncate text-muted-foreground">
            {indicatorLabel}
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
