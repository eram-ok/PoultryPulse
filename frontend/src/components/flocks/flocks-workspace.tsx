"use client"

import {
  useEffect,
  useMemo,
  useState,
} from "react"
import {
  Bird,
  CircleDot,
  Home,
  Plus,
  RefreshCcw,
  Search,
  UsersRound,
  Wheat,
} from "lucide-react"

import { useAuth } from "@/components/auth/auth-provider"
import { FlockDetailSheet } from "@/components/flocks/flock-detail-sheet"
import { FlockFormDialog } from "@/components/flocks/flock-form-dialog"
import { PopulationAdjustmentDialog } from "@/components/flocks/population-adjustment-dialog"
import { EmptyState } from "@/components/operational/empty-state"
import { NativeSelect } from "@/components/operational/form-controls"
import { PageHeading } from "@/components/operational/page-heading"
import { PaginationControls } from "@/components/operational/pagination-controls"
import { StatCard } from "@/components/operational/stat-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { browserApiRequest } from "@/lib/api/browser"
import type {
  Flock,
  FlockListResponse,
  FlockProductionStage,
  FlockStatus,
  PoultryHouse,
  PoultryHouseListResponse,
} from "@/lib/api/operations"
import {
  formatDate,
  formatEnum,
  formatMoney,
  formatNumber,
} from "@/lib/operational/format"
import { cn } from "@/lib/utils"

const LIMIT = 20

const statusClasses: Record<FlockStatus, string> = {
  PLANNED:
    "border-cyan-500/20 bg-cyan-500/10 text-cyan-500",
  ACTIVE:
    "border-primary/20 bg-primary/10 text-primary",
  SUSPENDED:
    "border-amber-500/20 bg-amber-500/10 text-amber-500",
  DEPLETED:
    "border-muted-foreground/20 bg-muted text-muted-foreground",
  SOLD:
    "border-violet-500/20 bg-violet-500/10 text-violet-500",
  ARCHIVED:
    "border-muted-foreground/20 bg-muted text-muted-foreground",
}

export function FlocksWorkspace() {
  const { session } = useAuth()
  const [flocks, setFlocks] = useState<Flock[]>([])
  const [houses, setHouses] = useState<PoultryHouse[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [status, setStatus] = useState<FlockStatus | "">("")
  const [stage, setStage] =
    useState<FlockProductionStage | "">("")
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] = useState<Flock | null>(null)
  const [selected, setSelected] = useState<Flock | null>(null)
  const [adjusting, setAdjusting] = useState<Flock | null>(null)
  const [reloadVersion, setReloadVersion] = useState(0)

  const canViewHouses =
    session.permissions.includes("houses.view")
  const canCreate =
    session.permissions.includes("flocks.create") &&
    canViewHouses
  const canUpdate =
    session.permissions.includes("flocks.update") &&
    canViewHouses
  const canAdjust = session.permissions.includes(
    "flocks.population.adjust",
  )

  useEffect(() => {
    const timer = window.setTimeout(
      () => {
        setDebouncedSearch(search.trim())
        setOffset(0)
      },
      300,
    )
    return () => window.clearTimeout(timer)
  }, [search])

  const query = useMemo(() => {
    const parameters = new URLSearchParams({
      offset: String(offset),
      limit: String(LIMIT),
    })

    if (debouncedSearch) {
      parameters.set("search", debouncedSearch)
    }
    if (status) {
      parameters.set("status", status)
    }
    if (stage) {
      parameters.set("production_stage", stage)
    }

    return parameters.toString()
  }, [debouncedSearch, offset, stage, status])

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const [flockPayload, housePayload] =
          await Promise.all([
            browserApiRequest<FlockListResponse>(
              `/flocks?${query}`,
              { signal: controller.signal },
            ),
            canViewHouses
              ? browserApiRequest<PoultryHouseListResponse>(
                  "/houses?offset=0&limit=100",
                  { signal: controller.signal },
                )
              : Promise.resolve<PoultryHouseListResponse>({
                  items: [],
                  total: 0,
                  offset: 0,
                  limit: 100,
                }),
          ])

        if (controller.signal.aborted) {
          return
        }

        setFlocks(flockPayload.items)
        setTotal(flockPayload.total)
        setHouses(housePayload.items)
        setError(null)
      } catch (caught) {
        if (controller.signal.aborted) {
          return
        }

        setError(
          caught instanceof Error
            ? caught.message
            : "Flocks could not be loaded.",
        )
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => controller.abort()
  }, [canViewHouses, query, reloadVersion])

  function handleSaved(saved: Flock) {
    setFlocks((current) => {
      const exists = current.some(
        (item) => item.id === saved.id,
      )

      return exists
        ? current.map((item) =>
            item.id === saved.id ? saved : item,
          )
        : [saved, ...current]
    })
    setEditing(null)
    setReloadVersion((current) => current + 1)
  }

  const summary = useMemo(
    () => ({
      active: flocks.filter((item) => item.status === "ACTIVE")
        .length,
      birds: flocks.reduce(
        (sum, item) => sum + item.current_population,
        0,
      ),
      laying: flocks.filter(
        (item) => item.production_stage === "LAYING",
      ).length,
      planned: flocks.filter(
        (item) => item.status === "PLANNED",
      ).length,
    }),
    [flocks],
  )

  if (error && !loading) {
    return (
      <div className="space-y-8">
        <PageHeading
          icon={Bird}
          eyebrow="Farm operations"
          title="Flocks"
          description="Manage bird placements, stages, populations, and house assignments."
        />
        <Card className="flex min-h-80 flex-col items-center justify-center rounded-3xl p-8 text-center">
          <RefreshCcw className="size-10 text-destructive" />
          <h2 className="mt-4 text-xl font-semibold">
            Flocks are temporarily unavailable
          </h2>
          <p className="mt-2 max-w-md text-sm text-muted-foreground">
            {error}
          </p>
          <Button
            className="mt-5 rounded-xl"
            onClick={() =>
              setReloadVersion((current) => current + 1)
            }
          >
            Try again
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <PageHeading
        icon={Bird}
        eyebrow="Farm operations"
        title="Flocks"
        description="Track flock placements, production stages, populations, housing, and commercial context."
        actions={
          canCreate ? (
            <Button
              className="rounded-xl"
              onClick={() => setCreateOpen(true)}
              disabled={houses.length === 0}
            >
              <Plus className="size-4" />
              Register flock
            </Button>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Visible flocks"
          value={formatNumber(total)}
          helper="Matching the current filters"
          icon={Bird}
        />
        <StatCard
          label="Active birds"
          value={formatNumber(summary.birds)}
          helper={`${summary.active} active flocks on this page`}
          icon={UsersRound}
          tone="info"
        />
        <StatCard
          label="Laying flocks"
          value={formatNumber(summary.laying)}
          helper="Currently in production"
          icon={Wheat}
          tone="warning"
        />
        <StatCard
          label="Planned flocks"
          value={formatNumber(summary.planned)}
          helper="Awaiting placement"
          icon={CircleDot}
        />
      </div>

      {canCreate && houses.length === 0 && !loading ? (
        <Card className="rounded-2xl border-amber-500/25 bg-amber-500/8 p-4 text-sm text-amber-600 dark:text-amber-400">
          Register at least one poultry house before creating a
          flock.
        </Card>
      ) : null}

      <Card className="overflow-hidden rounded-3xl border-border/75 bg-card/70">
        <div className="grid gap-3 border-b border-border/70 p-4 sm:p-5 lg:grid-cols-[minmax(240px,1fr)_180px_180px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search flock code, name, or breed…"
              className="h-10 rounded-xl pl-9"
            />
          </div>

          <NativeSelect
            value={status}
            onChange={(event) => {
              setStatus(event.target.value as FlockStatus | "")
              setOffset(0)
            }}
            className="h-10 rounded-xl"
          >
            <option value="">All statuses</option>
            <option value="PLANNED">Planned</option>
            <option value="ACTIVE">Active</option>
            <option value="SUSPENDED">Suspended</option>
            <option value="DEPLETED">Depleted</option>
            <option value="SOLD">Sold</option>
            <option value="ARCHIVED">Archived</option>
          </NativeSelect>

          <NativeSelect
            value={stage}
            onChange={(event) => {
              setStage(
                event.target.value as
                  | FlockProductionStage
                  | "",
              )
              setOffset(0)
            }}
            className="h-10 rounded-xl"
          >
            <option value="">All stages</option>
            <option value="BROODING">Brooding</option>
            <option value="GROWING">Growing</option>
            <option value="POINT_OF_LAY">Point of lay</option>
            <option value="LAYING">Laying</option>
            <option value="MOLTING">Molting</option>
            <option value="DEPLETED">Depleted</option>
            <option value="SOLD">Sold</option>
          </NativeSelect>
        </div>

        {loading ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton
                key={index}
                className="h-20 rounded-xl"
              />
            ))}
          </div>
        ) : flocks.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={Bird}
              title="No flocks match these filters"
              description="Register your first flock or change the search and operational filters."
              actionLabel={
                canCreate && houses.length > 0
                  ? "Register flock"
                  : undefined
              }
              onAction={
                canCreate && houses.length > 0
                  ? () => setCreateOpen(true)
                  : undefined
              }
            />
          </div>
        ) : (
          <>
            <div className="hidden lg:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-5">
                      Flock
                    </TableHead>
                    <TableHead>House</TableHead>
                    <TableHead>Population</TableHead>
                    <TableHead>Stage</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="pr-5">
                      Arrival
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {flocks.map((flock) => (
                    <TableRow
                      key={flock.id}
                      className="cursor-pointer"
                      onClick={() => setSelected(flock)}
                    >
                      <TableCell className="pl-5">
                        <div>
                          <p className="font-medium">
                            {flock.name}
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {flock.flock_code} · {flock.breed}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Home className="size-4 text-muted-foreground" />
                          <span>{flock.house_code}</span>
                        </div>
                      </TableCell>
                      <TableCell className="min-w-40">
                        <p className="font-mono font-medium">
                          {formatNumber(flock.current_population)}
                        </p>
                        <Progress
                          value={Math.min(
                            100,
                            (flock.current_population /
                              Math.max(1, flock.house_capacity)) *
                              100,
                          )}
                          className="mt-2 h-1.5"
                        />
                      </TableCell>
                      <TableCell>
                        {formatEnum(flock.production_stage)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            "rounded-full",
                            statusClasses[flock.status],
                          )}
                        >
                          {formatEnum(flock.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="pr-5">
                        {formatDate(flock.arrival_date)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="grid gap-3 p-4 md:grid-cols-2 lg:hidden">
              {flocks.map((flock) => (
                <button
                  type="button"
                  key={flock.id}
                  onClick={() => setSelected(flock)}
                  className="rounded-2xl border border-border/75 bg-background/50 p-4 text-left transition hover:border-primary/30 hover:bg-primary/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{flock.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {flock.flock_code} · {flock.breed}
                      </p>
                    </div>
                    <Badge
                      variant="outline"
                      className={cn(
                        "rounded-full",
                        statusClasses[flock.status],
                      )}
                    >
                      {formatEnum(flock.status)}
                    </Badge>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p className="text-muted-foreground">
                        Population
                      </p>
                      <p className="mt-1 font-mono text-sm font-semibold">
                        {formatNumber(flock.current_population)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">
                        House
                      </p>
                      <p className="mt-1 text-sm font-semibold">
                        {flock.house_code}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">
                        Stage
                      </p>
                      <p className="mt-1 text-sm">
                        {formatEnum(flock.production_stage)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">
                        Cost
                      </p>
                      <p className="mt-1 text-sm">
                        {formatMoney(
                          flock.purchase_cost,
                          session.farm.currency_code,
                        )}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <PaginationControls
              offset={offset}
              limit={LIMIT}
              total={total}
              onOffsetChange={setOffset}
            />
          </>
        )}
      </Card>

      <FlockFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        houses={houses.filter(
          (house) => house.status === "ACTIVE",
        )}
        onSaved={handleSaved}
      />

      <FlockFormDialog
        open={editing !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setEditing(null)
          }
        }}
        flock={editing}
        houses={houses}
        onSaved={handleSaved}
      />

      <FlockDetailSheet
        flock={selected}
        open={selected !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setSelected(null)
          }
        }}
        canAdjust={canAdjust}
        canEdit={canUpdate}
        onAdjust={() => {
          if (selected) {
            setAdjusting(selected)
            setSelected(null)
          }
        }}
        onEdit={() => {
          if (selected) {
            setEditing(selected)
            setSelected(null)
          }
        }}
      />

      <PopulationAdjustmentDialog
        flock={adjusting}
        open={adjusting !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setAdjusting(null)
          }
        }}
        onSaved={() => {
          setAdjusting(null)
          setReloadVersion((current) => current + 1)
        }}
      />
    </div>
  )
}
