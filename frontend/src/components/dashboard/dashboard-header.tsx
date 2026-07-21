import {
  CalendarDays,
  CloudSun,
  Plus,
  Sparkles,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"

export function DashboardHeader() {
  return (
    <header className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge
            variant="outline"
            className="rounded-full border-primary/25 bg-primary/8 text-primary"
          >
            <span className="mr-1.5 size-1.5 rounded-full bg-primary" />
            Farm online
          </Badge>
          <Badge variant="secondary" className="rounded-full">
            <CloudSun className="mr-1 size-3" />
            24°C · Mukono
          </Badge>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          Good evening, PoultryPulse Admin
        </h1>
        <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
          Your flocks are stable and today&apos;s egg collection is tracking
          above the seven-day average.
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button variant="outline" className="rounded-xl bg-card/60">
          <CalendarDays className="size-4" />
          21 July 2026
        </Button>
        <Button className="rounded-xl shadow-lg shadow-primary/20">
          <Plus className="size-4" />
          Record activity
          <Sparkles className="size-3.5 opacity-75" />
        </Button>
      </div>
    </header>
  )
}
