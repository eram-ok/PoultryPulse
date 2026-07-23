"use client"

import Link from "next/link"
import {
  Activity,
  ArrowLeft,
  Building2,
  CheckCircle2,
  KeyRound,
  LoaderCircle,
  RefreshCw,
  ShieldCheck,
  UsersRound,
} from "lucide-react"
import {
  useCallback,
  useEffect,
  useState,
} from "react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  formatPlatformDate,
  platformFarmRequest,
} from "@/lib/platform-farms/api"
import type {
  PlatformFarmDetail,
  PlatformFarmOnboardingStatus,
} from "@/lib/platform-farms/types"
import type {
  FarmLifecycleStatus,
} from "@/lib/platform-auth/types"

interface PlatformFarmDetailOverviewProps {
  farmId: string
}

function statusClass(
  status: FarmLifecycleStatus,
): string {
  if (status === "ACTIVE") {
    return "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
  }
  if (status === "SUSPENDED") {
    return "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300"
  }
  return "border-destructive/25 bg-destructive/8 text-destructive"
}

export function PlatformFarmDetailOverview({
  farmId,
}: PlatformFarmDetailOverviewProps) {
  const [farm, setFarm] =
    useState<PlatformFarmDetail | null>(null)
  const [onboarding, setOnboarding] =
    useState<PlatformFarmOnboardingStatus | null>(
      null,
    )
  const [loading, setLoading] =
    useState(true)
  const [error, setError] =
    useState<string | null>(null)
  const [refreshKey, setRefreshKey] =
    useState(0)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [farmResponse, onboardingResponse] =
        await Promise.all([
          platformFarmRequest<PlatformFarmDetail>(
            `/platform/farms/${encodeURIComponent(
              farmId,
            )}`,
          ),
          platformFarmRequest<PlatformFarmOnboardingStatus>(
            `/platform/farms/${encodeURIComponent(
              farmId,
            )}/onboarding`,
          ),
        ])

      setFarm(farmResponse)
      setOnboarding(onboardingResponse)
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "The farm workspace could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [farmId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => {
      window.clearTimeout(timer)
    }
  }, [load, refreshKey])

  if (loading && !farm) {
    return (
      <div className="grid min-h-[60vh] place-items-center">
        <LoaderCircle className="size-8 animate-spin text-primary" />
      </div>
    )
  }

  if (!farm) {
    return (
      <div className="mx-auto max-w-xl rounded-3xl border border-destructive/25 bg-destructive/8 p-6">
        <h1 className="text-xl font-semibold">
          Farm unavailable
        </h1>
        <p className="mt-2 text-sm text-destructive">
          {error ??
            "The requested farm could not be loaded."}
        </p>
        <Button
          asChild
          variant="outline"
          className="mt-5 rounded-xl"
        >
          <Link href="/platform/farms">
            <ArrowLeft className="size-4" />
            Farm registry
          </Link>
        </Button>
      </div>
    )
  }

  const invitation = onboarding?.invitation

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 rounded-[28px] border border-border/70 bg-card/74 p-5 shadow-sm backdrop-blur sm:p-7 lg:flex-row lg:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge
              variant="outline"
              className="rounded-full border-primary/25 bg-primary/8 text-primary"
            >
              <Building2 className="mr-1 size-3" />
              {farm.farm_code}
            </Badge>
            <Badge
              variant="outline"
              className={`rounded-full ${statusClass(
                farm.lifecycle_status,
              )}`}
            >
              {farm.lifecycle_status}
            </Badge>
          </div>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            {farm.name}
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
            Platform-safe customer profile, tenant usage,
            lifecycle state, and first-administrator
            onboarding status.
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button
            asChild
            variant="outline"
            className="rounded-xl"
          >
            <Link href="/platform/farms">
              <ArrowLeft className="size-4" />
              Registry
            </Link>
          </Button>
          <Button
            type="button"
            variant="outline"
            className="rounded-xl"
            disabled={loading}
            onClick={() =>
              setRefreshKey((value) => value + 1)
            }
          >
            {loading ? (
              <LoaderCircle className="size-4 animate-spin" />
            ) : (
              <RefreshCw className="size-4" />
            )}
            Refresh
          </Button>
        </div>
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
        {[
          {
            label: "Total users",
            value: farm.total_users,
            icon: UsersRound,
          },
          {
            label: "Active users",
            value: farm.active_users,
            icon: CheckCircle2,
          },
          {
            label: "Recent logins",
            value: farm.recent_login_users,
            icon: Activity,
          },
          {
            label: "Active sessions",
            value: farm.active_refresh_sessions,
            icon: ShieldCheck,
          },
        ].map((item) => {
          const Icon = item.icon
          return (
            <Card
              key={item.label}
              className="rounded-3xl border-border/70 bg-card/82"
            >
              <CardContent className="flex items-center justify-between p-5">
                <div>
                  <p className="text-sm text-muted-foreground">
                    {item.label}
                  </p>
                  <p className="mt-2 text-3xl font-semibold">
                    {item.value}
                  </p>
                </div>
                <div className="grid size-11 place-items-center rounded-2xl bg-primary/10 text-primary">
                  <Icon className="size-5" />
                </div>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader>
            <CardTitle>Farm profile</CardTitle>
            <CardDescription>
              Updated{" "}
              {formatPlatformDate(farm.updated_at)}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            {[
              ["Owner", farm.owner_name],
              ["Telephone", farm.telephone],
              ["Email", farm.email],
              ["District", farm.district],
              ["Address", farm.address],
              ["Timezone", farm.timezone],
              ["Currency", farm.currency_code],
              [
                "Last login",
                formatPlatformDate(
                  farm.last_login_at,
                ),
              ],
            ].map(([label, value]) => (
              <div
                key={label}
                className="rounded-2xl bg-muted/30 p-4"
              >
                <p className="text-xs text-muted-foreground">
                  {label}
                </p>
                <p className="mt-1 break-words font-medium">
                  {value || "Not recorded"}
                </p>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader>
            <CardTitle>Tenant lifecycle</CardTitle>
            <CardDescription>
              Last changed{" "}
              {formatPlatformDate(
                farm.lifecycle_changed_at,
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-border/70 p-4">
              <p className="text-xs text-muted-foreground">
                Current state
              </p>
              <Badge
                variant="outline"
                className={`mt-2 rounded-full ${statusClass(
                  farm.lifecycle_status,
                )}`}
              >
                {farm.lifecycle_status}
              </Badge>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {farm.lifecycle_reason ||
                  (farm.is_active
                    ? "Tenant access is enabled."
                    : "Tenant access is restricted.")}
              </p>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">
                  Suspended
                </p>
                <p className="mt-1 font-medium">
                  {formatPlatformDate(
                    farm.suspended_at,
                  )}
                </p>
              </div>
              <div className="rounded-2xl bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">
                  Deactivated
                </p>
                <p className="mt-1 font-medium">
                  {formatPlatformDate(
                    farm.deactivated_at,
                  )}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <Card className="rounded-3xl border-border/70 bg-card/82">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <KeyRound className="size-5 text-primary" />
            Administrator onboarding
          </CardTitle>
          <CardDescription>
            Read-only status for the first farm
            administrator and invitation delivery.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {[
            [
              "Administrator",
              onboarding?.administrator_username
                ? `@${onboarding.administrator_username}`
                : "Unavailable",
            ],
            [
              "Email",
              onboarding?.administrator_email ??
                "Unavailable",
            ],
            [
              "Activation",
              onboarding?.completed
                ? "Completed"
                : "Pending",
            ],
            [
              "Invitation",
              invitation?.status ??
                (onboarding?.legacy_completed
                  ? "Legacy completed"
                  : "Unavailable"),
            ],
            [
              "Delivery",
              invitation?.delivery_status ??
                "Unavailable",
            ],
            [
              "Attempts",
              String(
                invitation?.delivery_attempt_count ??
                  0,
              ),
            ],
            [
              "Expires",
              formatPlatformDate(
                invitation?.expires_at ?? null,
              ),
            ],
            [
              "Sent",
              formatPlatformDate(
                invitation?.sent_at ?? null,
              ),
            ],
          ].map(([label, value]) => (
            <div
              key={label}
              className="rounded-2xl bg-muted/30 p-4"
            >
              <p className="text-xs text-muted-foreground">
                {label}
              </p>
              <p className="mt-1 break-words font-medium">
                {value}
              </p>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
