"use client"

import Link from "next/link"
import {
  Building2,
  ChevronLeft,
  ChevronRight,
  Eye,
  LoaderCircle,
  RefreshCw,
  Search,
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
import { Input } from "@/components/ui/input"
import {
  formatPlatformDate,
  platformFarmRequest,
} from "@/lib/platform-farms/api"
import type {
  PlatformFarmListResponse,
  PlatformFarmSummary,
} from "@/lib/platform-farms/types"
import type {
  FarmLifecycleStatus,
} from "@/lib/platform-auth/types"

const PAGE_SIZE = 10

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

function FarmCard({
  farm,
}: {
  farm: PlatformFarmSummary
}) {
  return (
    <Card className="rounded-3xl border-border/70 bg-card/82">
      <CardHeader className="gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="truncate text-lg">
              {farm.name}
            </CardTitle>
            <Badge
              variant="outline"
              className={`rounded-full ${statusClass(
                farm.lifecycle_status,
              )}`}
            >
              {farm.lifecycle_status}
            </Badge>
          </div>
          <CardDescription className="mt-2">
            {[
              farm.farm_code,
              farm.district,
              farm.currency_code,
            ]
              .filter(Boolean)
              .join(" · ")}
          </CardDescription>
        </div>

        <Button
          asChild
          variant="outline"
          size="sm"
          className="rounded-xl"
        >
          <Link href={`/platform/farms/${farm.id}`}>
            <Eye className="size-4" />
            View farm
          </Link>
        </Button>
      </CardHeader>

      <CardContent className="grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        {[
          ["Owner", farm.owner_name || "Not recorded"],
          [
            "Users",
            `${farm.active_users} active of ${farm.total_users}`,
          ],
          [
            "Active sessions",
            String(farm.active_refresh_sessions),
          ],
          [
            "Last login",
            formatPlatformDate(farm.last_login_at),
          ],
        ].map(([label, value]) => (
          <div
            key={label}
            className="rounded-2xl bg-muted/30 p-3"
          >
            <p className="text-xs text-muted-foreground">
              {label}
            </p>
            <p className="mt-1 truncate font-medium">
              {value}
            </p>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

export function PlatformFarmRegistry() {
  const [farms, setFarms] =
    useState<PlatformFarmSummary[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [searchDraft, setSearchDraft] =
    useState("")
  const [statusDraft, setStatusDraft] =
    useState("")
  const [appliedSearch, setAppliedSearch] =
    useState("")
  const [appliedStatus, setAppliedStatus] =
    useState("")
  const [refreshKey, setRefreshKey] =
    useState(0)
  const [loading, setLoading] =
    useState(true)
  const [error, setError] =
    useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const parameters = new URLSearchParams({
        offset: String(offset),
        limit: String(PAGE_SIZE),
      })

      if (appliedSearch) {
        parameters.set("search", appliedSearch)
      }
      if (appliedStatus) {
        parameters.set("status", appliedStatus)
      }

      const response =
        await platformFarmRequest<PlatformFarmListResponse>(
          `/platform/farms?${parameters.toString()}`,
        )

      setFarms(response.items)
      setTotal(response.total)
    } catch (loadError) {
      setError(
        loadError instanceof Error
          ? loadError.message
          : "The customer-farm registry could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [
    appliedSearch,
    appliedStatus,
    offset,
  ])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => {
      window.clearTimeout(timer)
    }
  }, [load, refreshKey])

  function applyFilters(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setOffset(0)
    setAppliedSearch(searchDraft.trim())
    setAppliedStatus(statusDraft)
    setRefreshKey((value) => value + 1)
  }

  const firstItem =
    total === 0 ? 0 : offset + 1
  const lastItem = Math.min(
    offset + PAGE_SIZE,
    total,
  )

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 rounded-[28px] border border-border/70 bg-card/74 p-5 shadow-sm backdrop-blur sm:p-7 lg:flex-row lg:items-end">
        <div>
          <Badge
            variant="outline"
            className="rounded-full border-primary/25 bg-primary/8 text-primary"
          >
            <Building2 className="mr-1 size-3" />
            Customer tenants
          </Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">
            Farm registry
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
            Search every registered customer farm and
            inspect its profile, usage, lifecycle, and
            onboarding state.
          </p>
        </div>

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
      </section>

      <Card className="rounded-3xl border-border/70 bg-card/82">
        <CardHeader>
          <CardTitle className="text-lg">
            Search and filter
          </CardTitle>
          <CardDescription>
            Match farm name, code, owner, contact, or
            district.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_220px_auto]"
            onSubmit={applyFilters}
          >
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={searchDraft}
                onChange={(event) =>
                  setSearchDraft(event.target.value)
                }
                className="h-11 rounded-xl pl-10"
                placeholder="Search customer farms"
                maxLength={150}
              />
            </div>

            <select
              value={statusDraft}
              onChange={(event) =>
                setStatusDraft(event.target.value)
              }
              className="h-11 rounded-xl border border-input bg-background px-3 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring"
              aria-label="Lifecycle status"
            >
              <option value="">All lifecycle states</option>
              <option value="ACTIVE">Active</option>
              <option value="SUSPENDED">
                Suspended
              </option>
              <option value="DEACTIVATED">
                Deactivated
              </option>
            </select>

            <Button
              type="submit"
              className="h-11 rounded-xl"
            >
              <Search className="size-4" />
              Apply
            </Button>
          </form>
        </CardContent>
      </Card>

      {error ? (
        <div
          role="alert"
          className="rounded-2xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </div>
      ) : null}

      {loading && farms.length === 0 ? (
        <div className="grid min-h-64 place-items-center rounded-3xl border border-border/70 bg-card/70">
          <LoaderCircle className="size-8 animate-spin text-primary" />
        </div>
      ) : farms.length === 0 ? (
        <div className="grid min-h-64 place-items-center rounded-3xl border border-dashed border-border bg-card/55 p-8 text-center">
          <div>
            <Building2 className="mx-auto size-9 text-muted-foreground" />
            <h2 className="mt-4 text-lg font-semibold">
              No farms matched
            </h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Change the search or lifecycle filter.
            </p>
          </div>
        </div>
      ) : (
        <section className="space-y-4">
          {farms.map((farm) => (
            <FarmCard
              key={farm.id}
              farm={farm}
            />
          ))}
        </section>
      )}

      <section className="flex flex-col items-center justify-between gap-3 rounded-2xl border border-border/70 bg-card/70 px-4 py-3 sm:flex-row">
        <p className="text-sm text-muted-foreground">
          Showing {firstItem}–{lastItem} of {total} farms
        </p>

        <div className="flex gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="rounded-xl"
            disabled={offset === 0 || loading}
            onClick={() =>
              setOffset((value) =>
                Math.max(0, value - PAGE_SIZE),
              )
            }
          >
            <ChevronLeft className="size-4" />
            Previous
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="rounded-xl"
            disabled={
              offset + PAGE_SIZE >= total ||
              loading
            }
            onClick={() =>
              setOffset(
                (value) => value + PAGE_SIZE,
              )
            }
          >
            Next
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </section>
    </div>
  )
}
