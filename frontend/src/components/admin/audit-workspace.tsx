"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  AlertTriangle,
  Download,
  Eye,
  FileClock,
  Search,
  ShieldAlert,
  ShieldCheck,
  UserRoundCheck,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import {
  CommercialEmpty,
  CommercialLoading,
  CommercialMetric,
  CommercialPageHeader,
  CommercialPager,
  RefreshButton,
  StatusBadge,
} from "@/components/commercial/commercial-ui"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { browserApiRequest } from "@/lib/api/browser"
import { titleCase } from "@/lib/commercial/format"
import type {
  AuditAction,
  AuditLog,
  AuditLogList,
  AuditOutcome,
  AuditSeverity,
  AuditSummary,
} from "@/lib/admin/monitoring-types"

const limit = 50

const auditActions: AuditAction[] = [
  "CREATE",
  "VIEW",
  "UPDATE",
  "DELETE",
  "ACTIVATE",
  "DEACTIVATE",
  "ASSIGN",
  "REMOVE",
  "SUBMIT",
  "CONFIRM",
  "REJECT",
  "CANCEL",
  "COMPLETE",
  "RESOLVE",
  "REOPEN",
  "REVERSE",
  "VOID",
  "LOGIN",
  "LOGIN_FAILED",
  "LOGOUT",
  "TOKEN_REFRESH",
  "PASSWORD_CHANGE",
  "EXPORT",
  "PROCESS",
  "SYNC",
  "SYSTEM",
]

function startOfDay(date: string): string {
  return `${date}T00:00:00.000Z`
}

function endOfDay(date: string): string {
  return `${date}T23:59:59.999Z`
}

function formatDateTime(value: string | null): string {
  if (!value) return "Not recorded"

  return new Intl.DateTimeFormat("en-UG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function jsonText(value: Record<string, unknown> | null): string {
  return value ? JSON.stringify(value, null, 2) : "No data recorded."
}

export function AuditWorkspace() {
  const { session } = useAuth()
  const canExport = session.permissions.includes("audit.export")

  const [items, setItems] = useState<AuditLog[]>([])
  const [summary, setSummary] = useState<AuditSummary | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [action, setAction] = useState("ALL")
  const [outcome, setOutcome] = useState("ALL")
  const [severity, setSeverity] = useState("ALL")
  const [moduleName, setModuleName] = useState("")
  const [search, setSearch] = useState("")
  const [selected, setSelected] = useState<AuditLog | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const query = useMemo(() => {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    })

    if (dateFrom) params.set("date_from", startOfDay(dateFrom))
    if (dateTo) params.set("date_to", endOfDay(dateTo))
    if (action !== "ALL") params.set("action", action)
    if (outcome !== "ALL") params.set("outcome", outcome)
    if (severity !== "ALL") params.set("severity", severity)
    if (moduleName.trim()) params.set("module", moduleName.trim())
    if (search.trim()) params.set("search", search.trim())

    return params.toString()
  }, [
    action,
    dateFrom,
    dateTo,
    moduleName,
    offset,
    outcome,
    search,
    severity,
  ])

  const summaryQuery = useMemo(() => {
    const params = new URLSearchParams()

    if (dateFrom) params.set("date_from", startOfDay(dateFrom))
    if (dateTo) params.set("date_to", endOfDay(dateTo))

    return params.toString()
  }, [dateFrom, dateTo])

  const load = useCallback(async () => {
    if (dateFrom && dateTo && dateFrom > dateTo) {
      toast.error("The audit start date cannot be after the end date.")
      return
    }

    setLoading(true)

    try {
      const [logsResponse, summaryResponse] = await Promise.all([
        browserApiRequest<AuditLogList>(`/audit?${query}`),
        browserApiRequest<AuditSummary>(
          `/audit/summary${summaryQuery ? `?${summaryQuery}` : ""}`,
        ),
      ])

      setItems(logsResponse.items)
      setTotal(logsResponse.total)
      setSummary(summaryResponse)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Audit records could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [dateFrom, dateTo, query, summaryQuery])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  async function openDetails(item: AuditLog) {
    setSelected(item)
    setDetailLoading(true)

    try {
      const response = await browserApiRequest<AuditLog>(
        `/audit/${item.id}`,
      )
      setSelected(response)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Audit details could not be loaded.",
      )
    } finally {
      setDetailLoading(false)
    }
  }

  function resetFilters() {
    setDateFrom("")
    setDateTo("")
    setAction("ALL")
    setOutcome("ALL")
    setSeverity("ALL")
    setModuleName("")
    setSearch("")
    setOffset(0)
  }

  function exportHref(): string {
    const params = new URLSearchParams(query)
    params.delete("offset")
    params.delete("limit")
    return `/api/backend/audit/export.csv?${params}`
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Security and accountability"
        title="Audit trail"
        description="Review user activity, authorization failures, operational changes, request context, record differences, and system events."
        actions={
          <>
            <RefreshButton
              onClick={() => setRefreshKey((current) => current + 1)}
              loading={loading}
            />
            {canExport ? (
              <Button asChild variant="outline" className="rounded-xl">
                <a href={exportHref()}>
                  <Download className="size-4" />
                  Export filtered CSV
                </a>
              </Button>
            ) : null}
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <CommercialMetric
          label="Audit events"
          value={String(summary?.total ?? 0)}
          detail="Events in selected period"
          icon={FileClock}
        />
        <CommercialMetric
          label="Successful"
          value={String(summary?.successful ?? 0)}
          detail="Completed operations"
          icon={ShieldCheck}
        />
        <CommercialMetric
          label="Failed or denied"
          value={String(summary?.failed ?? 0)}
          detail="Failure and permission-denial events"
          icon={ShieldAlert}
        />
        <CommercialMetric
          label="Critical"
          value={String(summary?.critical ?? 0)}
          detail="Critical-severity records"
          icon={AlertTriangle}
        />
        <CommercialMetric
          label="Unique actors"
          value={String(summary?.unique_actors ?? 0)}
          detail="Distinct authenticated users"
          icon={UserRoundCheck}
        />
      </div>

      <Card className="overflow-hidden rounded-2xl">
        <CardContent className="p-0">
          <div className="space-y-3 border-b p-4">
            <div className="grid gap-3 lg:grid-cols-4">
              <div className="relative lg:col-span-2">
                <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
                <Input
                  className="pl-9"
                  value={search}
                  maxLength={150}
                  placeholder="Search descriptions, actors, paths, resources, or errors..."
                  onChange={(event) => {
                    setSearch(event.target.value)
                    setOffset(0)
                  }}
                />
              </div>
              <Input
                value={moduleName}
                maxLength={80}
                placeholder="Module filter"
                onChange={(event) => {
                  setModuleName(event.target.value)
                  setOffset(0)
                }}
              />
              <Button
                variant="outline"
                className="rounded-xl"
                onClick={resetFilters}
              >
                Clear filters
              </Button>
            </div>

            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
              <Input
                type="date"
                value={dateFrom}
                max={dateTo || undefined}
                aria-label="Audit date from"
                onChange={(event) => {
                  setDateFrom(event.target.value)
                  setOffset(0)
                }}
              />
              <Input
                type="date"
                value={dateTo}
                min={dateFrom || undefined}
                aria-label="Audit date to"
                onChange={(event) => {
                  setDateTo(event.target.value)
                  setOffset(0)
                }}
              />
              <Select
                value={action}
                onValueChange={(value) => {
                  setAction(value)
                  setOffset(0)
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All actions</SelectItem>
                  {auditActions.map((value) => (
                    <SelectItem key={value} value={value}>
                      {titleCase(value)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={outcome}
                onValueChange={(value) => {
                  setOutcome(value)
                  setOffset(0)
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All outcomes</SelectItem>
                  {(["SUCCESS", "FAILURE", "DENIED"] as AuditOutcome[]).map(
                    (value) => (
                      <SelectItem key={value} value={value}>
                        {titleCase(value)}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
              <Select
                value={severity}
                onValueChange={(value) => {
                  setSeverity(value)
                  setOffset(0)
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All severities</SelectItem>
                  {(["INFO", "WARNING", "CRITICAL"] as AuditSeverity[]).map(
                    (value) => (
                      <SelectItem key={value} value={value}>
                        {titleCase(value)}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
            </div>
          </div>

          {loading ? (
            <CommercialLoading label="Loading audit events..." />
          ) : items.length === 0 ? (
            <CommercialEmpty
              title="No audit events found"
              description="Change the current filters or perform an audited system action."
            />
          ) : (
            <div className="divide-y">
              {items.map((item) => (
                <div
                  key={item.id}
                  className="grid gap-4 p-4 hover:bg-muted/30 xl:grid-cols-[1.4fr_0.8fr_0.8fr_1fr_auto] xl:items-center"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold">{item.description}</p>
                      <StatusBadge status={item.severity} />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {item.module} Â· {titleCase(item.action)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Actor</p>
                    <p className="font-medium">
                      {item.actor_username ?? "System"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Outcome</p>
                    <StatusBadge status={item.outcome} />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Occurred</p>
                    <p className="text-sm font-medium">
                      {formatDateTime(item.occurred_at)}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="rounded-xl"
                    onClick={() => void openDetails(item)}
                  >
                    <Eye className="size-4" />
                    Details
                  </Button>
                </div>
              ))}
            </div>
          )}

          <CommercialPager
            offset={offset}
            limit={limit}
            total={total}
            onChange={setOffset}
          />
        </CardContent>
      </Card>

      <Dialog
        open={Boolean(selected)}
        onOpenChange={(open) => {
          if (!open) setSelected(null)
        }}
      >
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-5xl">
          <DialogHeader>
            <DialogTitle>Audit-event details</DialogTitle>
            <DialogDescription>
              Request, actor, resource, error, and sanitized change information.
            </DialogDescription>
          </DialogHeader>

          {detailLoading || !selected ? (
            <CommercialLoading label="Loading audit details..." />
          ) : (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
                {[
                  ["Actor", selected.actor_username ?? "System"],
                  ["Action", titleCase(selected.action)],
                  ["Outcome", titleCase(selected.outcome)],
                  ["Severity", titleCase(selected.severity)],
                  ["Module", selected.module],
                  ["Resource type", selected.resource_type ?? "Not recorded"],
                  ["Resource ID", selected.resource_id ?? "Not recorded"],
                  ["Occurred", formatDateTime(selected.occurred_at)],
                  ["Request method", selected.request_method ?? "Not recorded"],
                  ["Request path", selected.request_path ?? "Not recorded"],
                  ["Request ID", selected.request_id ?? "Not recorded"],
                  ["IP address", selected.ip_address ?? "Not recorded"],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="mt-1 break-all text-sm font-medium">
                      {value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="rounded-2xl border p-4">
                <p className="font-semibold">{selected.description}</p>
                {selected.error_message ? (
                  <div className="mt-3 rounded-xl border border-destructive/30 bg-destructive/5 p-3">
                    <p className="text-xs font-medium text-destructive">
                      {selected.error_code ?? "Error"}
                    </p>
                    <p className="mt-1 text-sm">{selected.error_message}</p>
                  </div>
                ) : null}
              </div>

              {[
                ["Changes", selected.changes],
                ["Before values", selected.before_values],
                ["After values", selected.after_values],
                ["Metadata", selected.metadata_json],
              ].map(([label, value]) => (
                <details key={label as string} className="rounded-2xl border p-4">
                  <summary className="cursor-pointer font-semibold">
                    {label as string}
                  </summary>
                  <pre className="mt-3 max-h-80 overflow-auto rounded-xl bg-muted p-4 text-xs leading-5">
                    {jsonText(value as Record<string, unknown> | null)}
                  </pre>
                </details>
              ))}

              {selected.user_agent ? (
                <div className="rounded-xl border p-3">
                  <p className="text-xs text-muted-foreground">User agent</p>
                  <p className="mt-1 break-all text-xs">
                    {selected.user_agent}
                  </p>
                </div>
              ) : null}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
