import {
  CalendarDays,
  MapPin,
  Plus,
  Sparkles,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import type { DashboardResponse } from "@/lib/api/types"
import type { SessionPayload } from "@/lib/auth/types"

interface DashboardHeaderProps {
  session: SessionPayload
  dashboard: DashboardResponse
}

function greetingForTimezone(timezone: string): string {
  const hour = Number(
    new Intl.DateTimeFormat("en-GB", {
      timeZone: timezone,
      hour: "2-digit",
      hour12: false,
    }).format(new Date()),
  )

  if (hour < 12) {
    return "Good morning"
  }

  if (hour < 18) {
    return "Good afternoon"
  }

  return "Good evening"
}

export function DashboardHeader({
  session,
  dashboard,
}: DashboardHeaderProps) {
  const location =
    session.farm.district ??
    session.farm.timezone
  const formattedDate = new Intl.DateTimeFormat(
    "en-UG",
    {
      timeZone: session.farm.timezone,
      dateStyle: "long",
    },
  ).format(
    new Date(`${dashboard.as_of_date}T12:00:00Z`),
  )

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
          <Badge
            variant="secondary"
            className="rounded-full"
          >
            <MapPin className="mr-1 size-3" />
            {location} · {session.farm.currency_code}
          </Badge>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight sm:text-3xl">
          {greetingForTimezone(session.farm.timezone)},{" "}
          {session.user.first_name}
        </h1>
        <p className="mt-1.5 max-w-2xl text-sm leading-6 text-muted-foreground">
          {dashboard.production.today_total_eggs > 0
            ? `${dashboard.production.today_total_eggs.toLocaleString(
                "en-UG",
              )} eggs are recorded today across ${dashboard.flocks.active_flocks} active flocks.`
            : "Your live farm overview is ready. Record today's operations to populate production insights."}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          className="rounded-xl bg-card/60"
        >
          <CalendarDays className="size-4" />
          {formattedDate}
        </Button>
        {session.permissions.includes(
          "production.create",
        ) ? (
          <Button className="rounded-xl shadow-lg shadow-primary/20">
            <Plus className="size-4" />
            Record activity
            <Sparkles className="size-3.5 opacity-75" />
          </Button>
        ) : null}
      </div>
    </header>
  )
}
