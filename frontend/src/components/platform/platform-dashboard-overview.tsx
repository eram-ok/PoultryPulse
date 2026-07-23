"use client"

import {
  useCallback,
  useEffect,
  useState,
} from "react"
import {
  Activity,
  Building2,
  CirclePause,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react"

import {
  usePlatformAuth,
} from "@/components/platform/platform-auth-provider"
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
  FarmLifecycleStatus,
  PlatformFarmListResponse,
} from "@/lib/platform-auth/types"

interface DashboardCounts {
  total: number
  active: number
  suspended: number
  deactivated: number
}

async function countFarms(
  status?: FarmLifecycleStatus,
): Promise<number> {
  const parameters = new URLSearchParams({
    offset: "0",
    limit: "1",
  })

  if (status) {
    parameters.set("status", status)
  }

  const response = await fetch(
    `/api/platform/backend/platform/farms?${parameters.toString()}`,
    {
      credentials: "same-origin",
      cache: "no-store",
    },
  )

  if (!response.ok) {
    throw new Error(
      "The platform farm summary could not be loaded.",
    )
  }

  const payload =
    (await response.json()) as
      PlatformFarmListResponse

  return payload.total
}

export function PlatformDashboardOverview() {
  const { session } = usePlatformAuth()
  const [counts, setCounts] =
    useState<DashboardCounts | null>(null)
  const [error, setError] =
    useState<string | null>(null)
  const [loading, setLoading] =
    useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [
        total,
        active,
        suspended,
        deactivated,
      ] = await Promise.all([
        countFarms(),
        countFarms("ACTIVE"),
        countFarms("SUSPENDED"),
        countFarms("DEACTIVATED"),
      ])

      setCounts({
        total,
        active,
        suspended,
        deactivated,
      })
    } catch {
      setError(
        "PoultryPulse could not load the platform overview.",
      )
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => {
      window.clearTimeout(timer)
    }
  }, [load])

  const cards = [
    {
      label: "Registered farms",
      value: counts?.total ?? 0,
      icon: Building2,
      detail: "All customer tenants",
    },
    {
      label: "Active farms",
      value: counts?.active ?? 0,
      icon: Activity,
      detail: "Currently enabled",
    },
    {
      label: "Suspended farms",
      value: counts?.suspended ?? 0,
      icon: CirclePause,
      detail: "Access restricted",
    },
    {
      label: "Deactivated farms",
      value: counts?.deactivated ?? 0,
      icon: ShieldCheck,
      detail: "Lifecycle closed",
    },
  ]

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 rounded-[28px] border border-border/70 bg-card/72 p-5 shadow-sm backdrop-blur sm:p-7 lg:flex-row lg:items-end">
        <div>
          <Badge
            variant="outline"
            className="rounded-full border-primary/25 bg-primary/8 text-primary"
          >
            Platform command centre
          </Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Customer-farm overview
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
            Review the tenant estate through a platform
            identity that remains separate from every farm
            user account.
          </p>
        </div>

        <Button
          type="button"
          variant="outline"
          className="rounded-xl"
          disabled={loading}
          onClick={() => void load()}
        >
          {loading ? (
            <LoaderCircle className="size-4 animate-spin" />
          ) : (
            <RefreshCw className="size-4" />
          )}
          Refresh overview
        </Button>
      </section>

      {error ? (
        <div
          role="alert"
          className="rounded-2xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </div>
      ) : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map((card) => {
          const Icon = card.icon

          return (
            <Card
              key={card.label}
              className="rounded-3xl border-border/70 bg-card/80"
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0">
                <div>
                  <CardDescription>
                    {card.label}
                  </CardDescription>
                  <CardTitle className="mt-2 text-3xl">
                    {loading ? "—" : card.value}
                  </CardTitle>
                </div>
                <div className="grid size-11 place-items-center rounded-2xl bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-muted-foreground">
                  {card.detail}
                </p>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        <Card className="rounded-3xl border-border/70 bg-card/80">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <UserRoundCheck className="size-5 text-primary" />
              Authenticated platform identity
            </CardTitle>
            <CardDescription>
              This session is not a farm-user session.
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl bg-muted/35 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                Administrator
              </p>
              <p className="mt-2 font-semibold">
                {session.user.full_name}
              </p>
              <p className="text-sm text-muted-foreground">
                @{session.user.username}
              </p>
            </div>
            <div className="rounded-2xl bg-muted/35 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                Authority
              </p>
              <p className="mt-2 font-semibold">
                Platform super administrator
              </p>
              <p className="text-sm text-muted-foreground">
                Cross-farm governance boundary
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-border/70 bg-card/80">
          <CardHeader>
            <CardTitle className="text-lg">
              Administration foundation
            </CardTitle>
            <CardDescription>
              The platform boundary is ready for the farm
              registry and lifecycle workspace.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {[
              "Separate HttpOnly platform cookies",
              "Platform-only authenticated API proxy",
              "Automatic refresh-token rotation",
              "Super-administrator route enforcement",
            ].map((item) => (
              <div
                key={item}
                className="flex items-center gap-3 rounded-xl border border-border/65 px-3 py-2.5"
              >
                <ShieldCheck className="size-4 text-primary" />
                {item}
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </div>
  )
}
