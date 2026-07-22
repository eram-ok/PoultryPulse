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
    icon: "bg-primary/14 text-primary",
    line: "bg-primary",
    surface:
      "from-primary/11 via-primary/4 to-transparent",
    ring: "ring-primary/12",
  },
  amber: {
    icon: "bg-warning/16 text-warning-foreground",
    line: "bg-warning",
    surface:
      "from-warning/13 via-warning/4 to-transparent",
    ring: "ring-warning/15",
  },
  blue: {
    icon: "bg-info/14 text-info",
    line: "bg-info",
    surface:
      "from-info/12 via-info/4 to-transparent",
    ring: "ring-info/14",
  },
  violet: {
    icon: "bg-chart-5/14 text-chart-5",
    line: "bg-chart-5",
    surface:
      "from-chart-5/12 via-chart-5/4 to-transparent",
    ring: "ring-chart-5/14",
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
  const min = Math.min(...sparkline, 0)
  const range = Math.max(max - min, 1)

  const IndicatorIcon =
    indicatorTone === "positive"
      ? ArrowUpRight
      : indicatorTone === "negative"
        ? ArrowDownRight
        : ArrowRight

  return (
    <Card
      className={cn(
        "metric-glow group relative h-auto min-w-0 self-start overflow-hidden rounded-[22px] border-border/70 bg-card/88 py-0 ring-1 transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_24px_58px_-42px_rgba(15,95,60,0.45)]",
        styles.ring,
      )}
    >
      <div
        aria-hidden="true"
        className={cn(
          "absolute inset-0 bg-gradient-to-br opacity-80",
          styles.surface,
        )}
      />

      <CardHeader className="relative flex min-w-0 flex-row items-start justify-between gap-3 px-4 pb-1.5 pt-4">
        <CardTitle className="min-w-0 break-words text-sm font-medium leading-5 text-muted-foreground">
          {title}
        </CardTitle>
        <div
          className={cn(
            "grid size-9 shrink-0 place-items-center rounded-xl shadow-sm transition-transform duration-300 group-hover:scale-105",
            styles.icon,
          )}
        >
          <Icon className="size-4.5" />
        </div>
      </CardHeader>

      <CardContent className="relative min-w-0 px-4 pb-4">
        <p className="break-words text-[clamp(1.75rem,2.2vw,2.5rem)] font-semibold leading-none tracking-tight">
          {value}
        </p>

        <div className="mt-3 flex min-w-0 flex-wrap items-center gap-2 text-xs">
          <span
            className={cn(
              "inline-flex shrink-0 items-center gap-1 rounded-full px-2 py-1 font-semibold",
              indicatorTone === "positive" &&
                "bg-primary/10 text-primary",
              indicatorTone === "negative" &&
                "bg-destructive/10 text-destructive",
              indicatorTone === "neutral" &&
                "bg-muted text-muted-foreground",
            )}
          >
            <IndicatorIcon className="size-3.5" />
            <span className="break-words">{indicator}</span>
          </span>
          <span className="min-w-0 break-words leading-4 text-muted-foreground">
            {indicatorLabel}
          </span>
        </div>

        <div className="mt-3 flex h-6 items-end gap-1">
          {sparkline.map((point, index) => {
            const height = 25 + ((point - min) / range) * 75

            return (
              <span
                key={`${point}-${index}`}
                className={cn(
                  "min-w-0 flex-1 rounded-full opacity-55 transition-all duration-300 group-hover:opacity-90",
                  styles.line,
                )}
                style={{ height: `${height}%` }}
              />
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
