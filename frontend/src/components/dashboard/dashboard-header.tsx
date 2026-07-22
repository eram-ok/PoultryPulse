import {
  CalendarDays,
  Egg,
  MapPin,
  Sparkles,
  UsersRound,
} from "lucide-react"

import { DashboardActivityMenu } from "@/components/dashboard/dashboard-activity-menu"
import { Badge } from "@/components/ui/badge"
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

  if (hour < 12) return "Good morning"
  if (hour < 18) return "Good afternoon"
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
      dateStyle: "medium",
    },
  ).format(
    new Date(`${dashboard.as_of_date}T12:00:00Z`),
  )

  const layingRate = Number(
    dashboard.production.today_laying_percentage,
  )

  return (
    <header className="relative overflow-hidden rounded-[22px] border border-primary/15 bg-gradient-to-r from-primary via-emerald-700 to-info px-4 py-3.5 text-white shadow-[0_18px_46px_-38px_rgba(10,86,54,0.62)] sm:px-5 lg:px-6">
      <div
        aria-hidden="true"
        className="absolute -right-20 -top-24 size-48 rounded-full bg-white/8 blur-2xl"
      />
      <div
        aria-hidden="true"
        className="surface-grid absolute inset-0 opacity-[0.04]"
      />

      <div className="relative z-10 grid gap-4 xl:grid-cols-[minmax(0,1.15fr)_minmax(360px,0.85fr)] xl:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge className="rounded-full border border-white/15 bg-white/12 px-2.5 py-1 text-[11px] text-white hover:bg-white/16">
              <span className="mr-1.5 size-1.5 rounded-full bg-emerald-200" />
              Farm online
            </Badge>
            <Badge className="rounded-full border border-white/15 bg-white/12 px-2.5 py-1 text-[11px] text-white hover:bg-white/16">
              <MapPin className="mr-1 size-3" />
              {location}
            </Badge>
            <Badge className="rounded-full border border-white/15 bg-white/12 px-2.5 py-1 text-[11px] text-white hover:bg-white/16">
              {session.farm.currency_code}
            </Badge>
          </div>

          <h1 className="mt-2 max-w-full break-words text-[clamp(1.7rem,2.25vw,2.35rem)] font-semibold leading-[1.08] tracking-tight">
            {greetingForTimezone(session.farm.timezone)},{" "}
            {session.user.first_name}
          </h1>

          <p className="mt-1.5 max-w-2xl text-xs leading-5 text-white/76 sm:text-sm">
            {dashboard.production.today_total_eggs > 0
              ? `${dashboard.production.today_total_eggs.toLocaleString(
                  "en-UG",
                )} eggs recorded today across ${dashboard.flocks.active_flocks} active flocks.`
              : "Your farm overview is ready. Record today's operations to populate live insights."}
          </p>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-2 rounded-xl border border-white/15 bg-black/10 px-3 py-2 text-xs text-white/84">
              <CalendarDays className="size-4" />
              {formattedDate}
            </div>
            <div className="flex items-center gap-2 rounded-xl border border-white/15 bg-black/10 px-3 py-2 text-xs text-white/84">
              <Sparkles className="size-4 text-amber-200" />
              Live farm data
            </div>
            <DashboardActivityMenu />
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2.5">
          <div className="min-w-0 rounded-2xl border border-white/15 bg-white/12 p-3 backdrop-blur-md">
            <div className="flex min-w-0 items-center gap-1.5 text-white/72">
              <Egg className="size-3.5 shrink-0" />
              <p className="min-w-0 text-[11px] leading-4">
                Eggs today
              </p>
            </div>
            <p className="mt-1.5 break-words text-[clamp(1.2rem,1.8vw,1.75rem)] font-semibold leading-none">
              {dashboard.production.today_total_eggs.toLocaleString("en-UG")}
            </p>
            <p className="mt-1.5 break-words text-[10px] leading-4 text-white/66">
              {dashboard.production.today_saleable_eggs.toLocaleString("en-UG")} saleable
            </p>
          </div>

          <div className="min-w-0 rounded-2xl border border-white/15 bg-white/12 p-3 backdrop-blur-md">
            <div className="flex min-w-0 items-center gap-1.5 text-white/72">
              <UsersRound className="size-3.5 shrink-0" />
              <p className="min-w-0 text-[11px] leading-4">
                Bird population
              </p>
            </div>
            <p className="mt-1.5 break-words text-[clamp(1.2rem,1.8vw,1.75rem)] font-semibold leading-none">
              {dashboard.flocks.current_bird_population.toLocaleString("en-UG")}
            </p>
            <p className="mt-1.5 break-words text-[10px] leading-4 text-white/66">
              {dashboard.flocks.active_flocks} active flocks
            </p>
          </div>

          <div className="min-w-0 rounded-2xl border border-white/15 bg-white/12 p-3 backdrop-blur-md">
            <div className="flex min-w-0 items-center gap-1.5 text-white/72">
              <Sparkles className="size-3.5 shrink-0" />
              <p className="min-w-0 text-[11px] leading-4">
                Laying rate
              </p>
            </div>
            <p className="mt-1.5 break-words text-[clamp(1.2rem,1.8vw,1.75rem)] font-semibold leading-none">
              {Number.isFinite(layingRate)
                ? `${layingRate.toLocaleString("en-UG", {
                    maximumFractionDigits: 1,
                  })}%`
                : "0%"}
            </p>
            <p className="mt-1.5 break-words text-[10px] leading-4 text-white/66">
              Today&apos;s average
            </p>
          </div>
        </div>
      </div>
    </header>
  )
}
