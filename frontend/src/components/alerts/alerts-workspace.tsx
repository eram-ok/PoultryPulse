"use client"

import {
  useEffect,
  useMemo,
  useState,
} from "react"
import {
  AlertTriangle,
  Bell,
  BellRing,
  CircleCheck,
  Eye,
  RefreshCcw,
  Search,
  ShieldAlert,
  UserCheck,
} from "lucide-react"
import { toast } from "sonner"

import { AlertDetailSheet } from "@/components/alerts/alert-detail-sheet"
import { useAuth } from "@/components/auth/auth-provider"
import { EmptyState } from "@/components/operational/empty-state"
import {
  NativeSelect,
} from "@/components/operational/form-controls"
import { PageHeading } from "@/components/operational/page-heading"
import { PaginationControls } from "@/components/operational/pagination-controls"
import { StatCard } from "@/components/operational/stat-card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
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
  AlertCounts,
  AlertRefreshResponse,
  AlertSeverity,
  AlertStatus,
  PersistentAlert,
  PersistentAlertListResponse,
} from "@/lib/api/operations"
import {
  formatDateTime,
  formatEnum,
} from "@/lib/operational/format"
import { cn } from "@/lib/utils"

const LIMIT = 20

const severityClasses = {
  INFO: "border-cyan-500/20 bg-cyan-500/10 text-cyan-500",
  WARNING:
    "border-amber-500/20 bg-amber-500/10 text-amber-500",
  CRITICAL:
    "border-red-500/20 bg-red-500/10 text-red-500",
}

export function AlertsWorkspace() {
  const { session } = useAuth()
  const [alerts, setAlerts] = useState<PersistentAlert[]>([])
  const [counts, setCounts] = useState<AlertCounts | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [debouncedSearch, setDebouncedSearch] = useState("")
  const [status, setStatus] = useState<AlertStatus | "">("")
  const [severity, setSeverity] =
    useState<AlertSeverity | "">("")
  const [unreadOnly, setUnreadOnly] = useState(false)
  const [assignedToMe, setAssignedToMe] = useState(false)
  const [includeDismissed, setIncludeDismissed] =
    useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selected, setSelected] =
    useState<PersistentAlert | null>(null)
  const [reloadVersion, setReloadVersion] = useState(0)

  const canRefresh =
    session.permissions.includes("alerts.refresh")

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
      assigned_to_me: String(assignedToMe),
      unread_only: String(unreadOnly),
      include_dismissed: String(includeDismissed),
    })

    if (debouncedSearch) {
      parameters.set("search", debouncedSearch)
    }
    if (status) {
      parameters.set("status", status)
    }
    if (severity) {
      parameters.set("severity", severity)
    }

    return parameters.toString()
  }, [
    assignedToMe,
    debouncedSearch,
    includeDismissed,
    offset,
    severity,
    status,
    unreadOnly,
  ])

  useEffect(() => {
    const controller = new AbortController()

    async function load() {
      try {
        const [list, countPayload] = await Promise.all([
          browserApiRequest<PersistentAlertListResponse>(
            `/alerts?${query}`,
            { signal: controller.signal },
          ),
          browserApiRequest<AlertCounts>("/alerts/counts", {
            signal: controller.signal,
          }),
        ])

        if (controller.signal.aborted) {
          return
        }

        setAlerts(list.items)
        setTotal(list.total)
        setCounts(countPayload)
        setError(null)
      } catch (caught) {
        if (controller.signal.aborted) {
          return
        }

        setError(
          caught instanceof Error
            ? caught.message
            : "Alerts could not be loaded.",
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

  async function refreshAlerts() {
    setRefreshing(true)

    try {
      const result =
        await browserApiRequest<AlertRefreshResponse>(
          "/alerts/refresh",
          {
            method: "POST",
            body: JSON.stringify({
              as_of_date: null,
              send_now: true,
            }),
          },
        )

      toast.success(
        `Alert refresh completed: ${result.created_count} created, ${result.updated_count} updated.`,
      )
      setReloadVersion((current) => current + 1)
    } catch (caught) {
      toast.error(
        caught instanceof Error
          ? caught.message
          : "Alerts could not be refreshed.",
      )
    } finally {
      setRefreshing(false)
    }
  }

  function updateAlert(updated: PersistentAlert) {
    setSelected(updated)
    setAlerts((current) =>
      current.map((item) =>
        item.id === updated.id ? updated : item,
      ),
    )
    setReloadVersion((current) => current + 1)
  }

  if (error && !loading) {
    return (
      <div className="space-y-8">
        <PageHeading
          icon={BellRing}
          eyebrow="Notification centre"
          title="Operational alerts"
          description="Review issues, reminders, assignments, and resolution activity across the farm."
        />
        <Card className="rounded-3xl">
          <CardContent className="flex min-h-80 flex-col items-center justify-center p-8 text-center">
            <ShieldAlert className="size-10 text-destructive" />
            <h2 className="mt-4 text-xl font-semibold">
              Alerts are temporarily unavailable
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
              <RefreshCcw className="size-4" />
              Try again
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <PageHeading
        icon={BellRing}
        eyebrow="Notification centre"
        title="Operational alerts"
        description="Prioritise farm issues, assign ownership, record decisions, and maintain a clear resolution history."
        actions={
          canRefresh ? (
            <Button
              className="rounded-xl"
              disabled={refreshing}
              onClick={() => void refreshAlerts()}
            >
              <RefreshCcw
                className={cn(
                  "size-4",
                  refreshing && "animate-spin",
                )}
              />
              Refresh alerts
            </Button>
          ) : null
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          label="Active alerts"
          value={String(counts?.total_active ?? 0)}
          helper="Across all farm operations"
          icon={Bell}
        />
        <StatCard
          label="Unread"
          value={String(counts?.unread ?? 0)}
          helper="Require your review"
          icon={Eye}
          tone="info"
        />
        <StatCard
          label="Critical"
          value={String(counts?.critical ?? 0)}
          helper="Highest operational priority"
          icon={AlertTriangle}
          tone="danger"
        />
        <StatCard
          label="Acknowledged"
          value={String(counts?.acknowledged ?? 0)}
          helper="Being actively handled"
          icon={CircleCheck}
          tone="warning"
        />
        <StatCard
          label="Assigned to me"
          value={String(counts?.assigned_to_me ?? 0)}
          helper="Your current workload"
          icon={UserCheck}
        />
      </div>

      <Card className="overflow-hidden rounded-3xl border-border/75 bg-card/70">
        <div className="border-b border-border/70 p-4 sm:p-5">
          <div className="grid gap-3 lg:grid-cols-[minmax(240px,1fr)_repeat(2,minmax(150px,180px))]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={search}
                onChange={(event) =>
                  setSearch(event.target.value)
                }
                placeholder="Search alert title or message…"
                className="h-10 rounded-xl pl-9"
              />
            </div>

            <NativeSelect
              value={status}
              onChange={(event) => {
                setStatus(
                  event.target.value as AlertStatus | "",
                )
                setOffset(0)
              }}
              className="h-10 rounded-xl"
              aria-label="Filter by alert status"
            >
              <option value="">All statuses</option>
              <option value="OPEN">Open</option>
              <option value="ACKNOWLEDGED">
                Acknowledged
              </option>
              <option value="RESOLVED">Resolved</option>
            </NativeSelect>

            <NativeSelect
              value={severity}
              onChange={(event) => {
                setSeverity(
                  event.target.value as AlertSeverity | "",
                )
                setOffset(0)
              }}
              className="h-10 rounded-xl"
              aria-label="Filter by alert severity"
            >
              <option value="">All severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Information</option>
            </NativeSelect>
          </div>

          <div className="mt-3 flex flex-wrap gap-2">
            <FilterToggle
              active={unreadOnly}
              onClick={() => {
                setUnreadOnly((current) => !current)
                setOffset(0)
              }}
            >
              Unread only
            </FilterToggle>
            <FilterToggle
              active={assignedToMe}
              onClick={() => {
                setAssignedToMe((current) => !current)
                setOffset(0)
              }}
            >
              Assigned to me
            </FilterToggle>
            <FilterToggle
              active={includeDismissed}
              onClick={() => {
                setIncludeDismissed((current) => !current)
                setOffset(0)
              }}
            >
              Include dismissed
            </FilterToggle>
          </div>
        </div>

        {loading ? (
          <div className="space-y-3 p-5">
            {Array.from({ length: 6 }).map((_, index) => (
              <Skeleton
                key={index}
                className="h-16 rounded-xl"
              />
            ))}
          </div>
        ) : alerts.length === 0 ? (
          <div className="p-5">
            <EmptyState
              icon={CircleCheck}
              title="No alerts match these filters"
              description="The farm has no matching operational issues. Change the filters or refresh alert detection."
              actionLabel={
                canRefresh ? "Refresh alert detection" : undefined
              }
              onAction={
                canRefresh
                  ? () => void refreshAlerts()
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
                      Alert
                    </TableHead>
                    <TableHead>Severity</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Source</TableHead>
                    <TableHead>Last detected</TableHead>
                    <TableHead className="pr-5 text-right">
                      Occurrences
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow
                      key={alert.id}
                      className="cursor-pointer"
                      onClick={() => setSelected(alert)}
                    >
                      <TableCell className="max-w-md pl-5">
                        <div className="flex items-start gap-3">
                          <span
                            className={cn(
                              "mt-1 size-2 shrink-0 rounded-full",
                              alert.is_read
                                ? "bg-muted-foreground/25"
                                : "bg-primary",
                            )}
                          />
                          <div className="min-w-0">
                            <p className="truncate font-medium">
                              {alert.title}
                            </p>
                            <p className="mt-1 truncate text-xs text-muted-foreground">
                              {alert.message}
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={cn(
                            "rounded-full",
                            severityClasses[alert.severity],
                          )}
                        >
                          {formatEnum(alert.severity)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {formatEnum(alert.status)}
                      </TableCell>
                      <TableCell>
                        {formatEnum(alert.source_module)}
                      </TableCell>
                      <TableCell>
                        {formatDateTime(alert.last_detected_at)}
                      </TableCell>
                      <TableCell className="pr-5 text-right font-mono">
                        {alert.occurrence_count}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            <div className="space-y-3 p-4 lg:hidden">
              {alerts.map((alert) => (
                <button
                  type="button"
                  key={alert.id}
                  onClick={() => setSelected(alert)}
                  className="w-full rounded-2xl border border-border/75 bg-background/50 p-4 text-left transition hover:border-primary/30 hover:bg-primary/5"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-medium">{alert.title}</p>
                      <p className="mt-1 line-clamp-2 text-xs leading-5 text-muted-foreground">
                        {alert.message}
                      </p>
                    </div>
                    {!alert.is_read ? (
                      <span className="mt-1 size-2 shrink-0 rounded-full bg-primary" />
                    ) : null}
                  </div>
                  <div className="mt-3 flex flex-wrap items-center gap-2">
                    <Badge
                      variant="outline"
                      className={cn(
                        "rounded-full",
                        severityClasses[alert.severity],
                      )}
                    >
                      {formatEnum(alert.severity)}
                    </Badge>
                    <Badge
                      variant="secondary"
                      className="rounded-full"
                    >
                      {formatEnum(alert.status)}
                    </Badge>
                    <span className="text-[11px] text-muted-foreground">
                      {formatDateTime(alert.last_detected_at)}
                    </span>
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

      <AlertDetailSheet
        alert={selected}
        open={selected !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setSelected(null)
          }
        }}
        onChanged={updateAlert}
      />
    </div>
  )
}

function FilterToggle({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={active ? "default" : "outline"}
      className="rounded-full"
      onClick={onClick}
    >
      {children}
    </Button>
  )
}
