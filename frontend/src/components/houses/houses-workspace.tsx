"use client"

import {
  useEffect,
  useMemo,
  useState,
} from "react"
import {
  Building2,
  CircleCheck,
  Construction,
  Home,
  MapPin,
  Pencil,
  Plus,
  Power,
  RefreshCcw,
  Search,
  UsersRound,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import { HouseFormDialog } from "@/components/houses/house-form-dialog"
import { EmptyState } from "@/components/operational/empty-state"
import { NativeSelect } from "@/components/operational/form-controls"
import { PageHeading } from "@/components/operational/page-heading"
import { PaginationControls } from "@/components/operational/pagination-controls"
import { StatCard } from "@/components/operational/stat-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
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
  PoultryHouse,
  PoultryHouseListResponse,
  PoultryHouseStatus,
} from "@/lib/api/operations"
import {
  formatEnum,
  formatNumber,
} from "@/lib/operational/format"
import { cn } from "@/lib/utils"

const LIMIT = 20

const statusClasses: Record<PoultryHouseStatus, string> = {
  ACTIVE:
    "border-primary/20 bg-primary/10 text-primary",
  INACTIVE:
    "border-muted-foreground/20 bg-muted text-muted-foreground",
  UNDER_MAINTENANCE:
    "border-amber-500/20 bg-amber-500/10 text-amber-500",
  CLOSED:
    "border-red-500/20 bg-red-500/10 text-red-500",
}

export function HousesWorkspace() {
  const { session } = useAuth()
  const [houses, setHouses] = useState<PoultryHouse[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [status, setStatus] =
    useState<PoultryHouseStatus | "">("")
  const [loading, setLoading] = useState(true)
  const [workingId, setWorkingId] =
    useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [editing, setEditing] =
    useState<PoultryHouse | null>(null)
  const [reloadVersion, setReloadVersion] = useState(0)

  const canCreate =
    session.permissions.includes("houses.create")
  const canUpdate =
    session.permissions.includes("houses.update")

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

    return parameters.toString()
  }, [debouncedSearch, offset, status])

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const payload =
          await browserApiRequest<PoultryHouseListResponse>(
            `/houses?${query}`,
            { signal: controller.signal },
          )

        if (controller.signal.aborted) {
          return
        }

        setHouses(payload.items)
        setTotal(payload.total)
        setError(null)
      } catch (caught) {
        if (controller.signal.aborted) {
          return
        }

        setError(
          caught instanceof Error
            ? caught.message
            : "Poultry houses could not be loaded.",
        )
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void load()

    return () => controller.abort()
  }, [query, reloadVersion])

  function handleSaved(saved: PoultryHouse) {
    setHouses((current) => {
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

  async function toggleHouse(house: PoultryHouse) {
    const action =
      house.status === "ACTIVE"
        ? "deactivate"
        : "activate"

    setWorkingId(house.id)

    try {
      const updated =
        await browserApiRequest<PoultryHouse>(
          `/houses/${house.id}/${action}`,
          { method: "POST" },
        )

      handleSaved(updated)
      toast.success(
        `Poultry house ${action === "activate" ? "activated" : "deactivated"}.`,
      )
    } catch (caught) {
      toast.error(
        caught instanceof Error
          ? caught.message
          : "The house status could not be changed.",
      )
    } finally {
      setWorkingId(null)
    }
  }

  const summary = useMemo(
    () => ({
      active: houses.filter(
        (item) => item.status === "ACTIVE",
      ).length,
      maintenance: houses.filter(
        (item) => item.status === "UNDER_MAINTENANCE",
      ).length,
      capacity: houses.reduce(
        (sum, item) => sum + item.capacity,
        0,
      ),
    }),
    [houses],
  )

  if (error && !loading) {
    return (
      <div className="space-y-8">
        <PageHeading
          icon={Home}
          eyebrow="Farm operations"
          title="Poultry houses"
          description="Manage farm housing, capacity, locations, and operational availability."
        />
        <Card className="flex min-h-80 flex-col items-center justify-center rounded-3xl p-8 text-center">
          <RefreshCcw className="size-10 text-destructive" />
          <h2 className="mt-4 text-xl font-semibold">
            Houses are temporarily unavailable
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
        icon={Home}
        eyebrow="Farm operations"
        title="Poultry houses"
        description="Maintain reliable housing records so flock placement, capacity checks, and operational planning stay accurate."
        actions={
          canCreate ? (
            <Button
              className="rounded-xl"
              onClick={() => setCreateOpen(true)}
            >
              <Plus className="size-4" />
              Add house
            </Button>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Registered houses"
          value={formatNumber(total)}
          helper="Matching current filters"
          icon={Building2}
        />
        <StatCard
          label="Active houses"
          value={formatNumber(summary.active)}
          helper="Available for flock placement"
          icon={CircleCheck}
          tone="info"
        />
        <StatCard
          label="Visible capacity"
          value={formatNumber(summary.capacity)}
          helper="Bird spaces on this page"
          icon={UsersRound}
        />
        <StatCard
          label="Maintenance"
          value={formatNumber(summary.maintenance)}
          helper="Temporarily unavailable"
          icon={Construction}
          tone="warning"
        />
      </div>

      <Card className="overflow-hidden rounded-3xl border-border/75 bg-card/70">
        <div className="grid gap-3 border-b border-border/70 p-4 sm:p-5 lg:grid-cols-[minmax(240px,1fr)_200px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
              placeholder="Search house code, name, or location…"
              className="h-10 rounded-xl pl-9"
            />
          </div>

          <NativeSelect
            value={status}
            onChange={(event) => {
              setStatus(
                event.target.value as
                  | PoultryHouseStatus
                  | "",
              )
              setOffset(0)
            }}
            className="h-10 rounded-xl"
          >
            <option value="">All statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="UNDER_MAINTENANCE">
              Under maintenance
            </option>
            <option value="CLOSED">Closed</option>
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
        ) : houses.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={Home}
              title="No poultry houses match these filters"
              description="Add the first poultry house or change the current status and search filters."
              actionLabel={canCreate ? "Add house" : undefined}
              onAction={
                canCreate
                  ? () => setCreateOpen(true)
                  : undefined
              }
            />
          </div>
        ) : (
          <>
            <div className="hidden md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="pl-5">
                      House
                    </TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Capacity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="pr-5 text-right">
                      Actions
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {houses.map((house) => (
                    <TableRow key={house.id}>
                      <TableCell className="pl-5">
                        <div>
                          <p className="font-medium">
                            {house.name}
                          </p>
                          <p className="mt-1 text-xs text-muted-foreground">
                            {house.house_code}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <MapPin className="size-4" />
                          <span>
                            {house.location || "Not recorded"}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell className="font-mono font-medium">
                        {formatNumber(house.capacity)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            "rounded-full",
                            statusClasses[house.status],
                          )}
                        >
                          {formatEnum(house.status)}
                        </Badge>
                      </TableCell>
                      <TableCell className="pr-5">
                        <div className="flex justify-end gap-2">
                          {canUpdate ? (
                            <>
                              <Button
                                size="icon-sm"
                                variant="outline"
                                className="rounded-lg"
                                onClick={() => setEditing(house)}
                                aria-label={`Edit ${house.name}`}
                              >
                                <Pencil className="size-4" />
                              </Button>
                              <Button
                                size="icon-sm"
                                variant="outline"
                                className="rounded-lg"
                                disabled={workingId === house.id}
                                onClick={() =>
                                  void toggleHouse(house)
                                }
                                aria-label={
                                  house.status === "ACTIVE"
                                    ? `Deactivate ${house.name}`
                                    : `Activate ${house.name}`
                                }
                              >
                                <Power className="size-4" />
                              </Button>
                            </>
                          ) : null}
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="grid gap-3 p-4 md:hidden">
              {houses.map((house) => (
                <div
                  key={house.id}
                  className="rounded-2xl border border-border/75 bg-background/50 p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium">{house.name}</p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {house.house_code}
                      </p>
                    </div>
                    <Badge
                      variant="outline"
                      className={cn(
                        "rounded-full",
                        statusClasses[house.status],
                      )}
                    >
                      {formatEnum(house.status)}
                    </Badge>
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-3 text-xs">
                    <div>
                      <p className="text-muted-foreground">
                        Capacity
                      </p>
                      <p className="mt-1 font-mono text-sm font-semibold">
                        {formatNumber(house.capacity)}
                      </p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">
                        Location
                      </p>
                      <p className="mt-1 truncate text-sm">
                        {house.location || "Not recorded"}
                      </p>
                    </div>
                  </div>
                  {canUpdate ? (
                    <div className="mt-4 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 rounded-xl"
                        onClick={() => setEditing(house)}
                      >
                        <Pencil className="size-4" />
                        Edit
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 rounded-xl"
                        disabled={workingId === house.id}
                        onClick={() => void toggleHouse(house)}
                      >
                        <Power className="size-4" />
                        {house.status === "ACTIVE"
                          ? "Deactivate"
                          : "Activate"}
                      </Button>
                    </div>
                  ) : null}
                </div>
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

      <HouseFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        onSaved={handleSaved}
      />

      <HouseFormDialog
        open={editing !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setEditing(null)
          }
        }}
        house={editing}
        onSaved={handleSaved}
      />
    </div>
  )
}
