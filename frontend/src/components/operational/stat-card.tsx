import type { LucideIcon } from "lucide-react"

import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface StatCardProps {
  label: string
  value: string
  helper: string
  icon: LucideIcon
  tone?: "primary" | "warning" | "danger" | "info"
}

const toneClasses = {
  primary: "bg-primary/12 text-primary",
  warning: "bg-amber-500/12 text-amber-500",
  danger: "bg-red-500/12 text-red-500",
  info: "bg-cyan-500/12 text-cyan-500",
}

export function StatCard({
  label,
  value,
  helper,
  icon: Icon,
  tone = "primary",
}: StatCardProps) {
  return (
    <Card className="rounded-2xl border-border/75 bg-card/70 shadow-sm">
      <CardContent className="flex items-start justify-between gap-4 p-5">
        <div className="min-w-0">
          <p className="text-xs font-medium text-muted-foreground">
            {label}
          </p>
          <p className="mt-2 truncate font-mono text-2xl font-semibold tracking-tight">
            {value}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            {helper}
          </p>
        </div>
        <div
          className={cn(
            "grid size-10 shrink-0 place-items-center rounded-xl",
            toneClasses[tone],
          )}
        >
          <Icon className="size-5" />
        </div>
      </CardContent>
    </Card>
  )
}
