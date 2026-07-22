"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Activity,
  Clock3,
  Eye,
  Play,
  RefreshCw,
  ServerCog,
  TimerReset,
  Workflow,
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
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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
  BackgroundJobDefinition,
  BackgroundJobDefinitionList,
  BackgroundJobRun,
  BackgroundJobRunList,
  BackgroundJobStatus,
} from "@/lib/admin/monitoring-types"

const limit = 50

function formatDateTime(value: string | null): string {
  if (!value) return "Not recorded"

  return new Intl.DateTimeFormat("en-UG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function intervalLabel(seconds: number): string {
  if (seconds % 86400 === 0) {
    return `${seconds / 86400} day(s)`
  }
  if (seconds % 3600 === 0) {
    return `${seconds / 3600} hour(s)`
  }
  if (seconds % 60 === 0) {
    return `${seconds / 60} minute(s)`
  }
  return `${seconds} second(s)`
}

function jsonText(value: Record<string, unknown> | null): string {
  return value ? JSON.stringify(value, null, 2) : "No result payload."
}

export function JobsWorkspace() {
  const { session } = useAuth()
  const canRun = session.permissions.includes("audit.manage")

  const [definitions, setDefinitions] =
    useState<BackgroundJobDefinition[]>([])
  const [runs, setRuns] = useState<BackgroundJobRun[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [jobName, setJobName] = useState("ALL")
  const [status, setStatus] = useState("ALL")
  const [selected, setSelected] = useState<BackgroundJobRun | null>(null)
  const [detailLoading, setDetailLoading] = useState(false)
  const [runningJob, setRunningJob] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const query = useMemo(() => {
    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    })

    if (jobName !== "ALL") params.set("job_name", jobName)
    if (status !== "ALL") params.set("status", status)

    return params.toString()
  }, [jobName, offset, status])

  const load = useCallback(async () => {
    setLoading(true)

    try {
      const [definitionResponse, runResponse] = await Promise.all([
        browserApiRequest<BackgroundJobDefinitionList>(
          "/jobs/definitions",
        ),
        browserApiRequest<BackgroundJobRunList>(
          `/jobs/runs?${query}`,
        ),
      ])

      setDefinitions(definitionResponse.items)
      setRuns(runResponse.items)
      setTotal(runResponse.total)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Background-job monitoring could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [query])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  const metrics = useMemo(
    () => ({
      enabled: definitions.filter((item) => item.enabled).length,
      perFarm: definitions.filter((item) => item.per_farm).length,
      failures: runs.filter((item) => item.status === "FAILURE").length,
      running: runs.filter((item) => item.status === "RUNNING").length,
    }),
    [definitions, runs],
  )

  async function runNow(definition: BackgroundJobDefinition) {
    if (!definition.per_farm) {
      toast.error(
        "Global maintenance jobs can only be run from the administrative command line.",
      )
      return
    }

    setRunningJob(definition.name)

    try {
      const response = await browserApiRequest<BackgroundJobRun>(
        `/jobs/${encodeURIComponent(definition.name)}/run`,
        { method: "POST" },
      )
      toast.success(
        `${titleCase(definition.name)} finished with status ${response.status}.`,
      )
      setSelected(response)
      setRefreshKey((current) => current + 1)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The background job could not be run.",
      )
    } finally {
      setRunningJob(null)
    }
  }

  async function openDetails(run: BackgroundJobRun) {
    setSelected(run)
    setDetailLoading(true)

    try {
      const response = await browserApiRequest<BackgroundJobRun>(
        `/jobs/runs/${run.id}`,
      )
      setSelected(response)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Job-run details could not be loaded.",
      )
    } finally {
      setDetailLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="System operations"
        title="Background jobs"
        description="Inspect scheduler definitions and execution history, diagnose failures, and manually run eligible farm-scoped jobs."
        actions={
          <RefreshButton
            onClick={() => setRefreshKey((current) => current + 1)}
            loading={loading}
          />
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CommercialMetric
          label="Job definitions"
          value={String(definitions.length)}
          detail={`${metrics.enabled} currently enabled`}
          icon={Workflow}
        />
        <CommercialMetric
          label="Farm-scoped jobs"
          value={String(metrics.perFarm)}
          detail="Eligible for farm-context execution"
          icon={ServerCog}
        />
        <CommercialMetric
          label="Running on page"
          value={String(metrics.running)}
          detail="Executions still in progress"
          icon={RefreshCw}
        />
        <CommercialMetric
          label="Failures on page"
          value={String(metrics.failures)}
          detail="Runs requiring review"
          icon={Activity}
        />
      </div>

      <Card className="rounded-2xl">
        <CardContent className="p-4">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
              <TimerReset className="size-5" />
            </div>
            <div>
              <p className="font-semibold">Job definitions</p>
              <p className="text-sm text-muted-foreground">
                Availability and configured execution intervals
              </p>
            </div>
          </div>

          {loading ? (
            <CommercialLoading label="Loading job definitions..." />
          ) : (
            <div className="grid gap-4 xl:grid-cols-3">
              {definitions.map((definition) => (
                <div
                  key={definition.name}
                  className="rounded-2xl border p-4"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold">
                      {titleCase(definition.name)}
                    </p>
                    <StatusBadge
                      status={definition.enabled ? "ACTIVE" : "INACTIVE"}
                    />
                  </div>
                  <div className="mt-4 space-y-2 text-sm">
                    <div className="flex justify-between gap-3">
                      <span className="text-muted-foreground">Scope</span>
                      <span className="font-medium">
                        {definition.per_farm ? "Per farm" : "Global"}
                      </span>
                    </div>
                    <div className="flex justify-between gap-3">
                      <span className="text-muted-foreground">Interval</span>
                      <span className="font-medium">
                        {intervalLabel(definition.interval_seconds)}
                      </span>
                    </div>
                  </div>

                  {canRun ? (
                    <Button
                      className="mt-4 w-full rounded-xl"
                      variant={definition.per_farm ? "default" : "outline"}
                      disabled={
                        !definition.per_farm ||
                        runningJob === definition.name
                      }
                      onClick={() => void runNow(definition)}
                    >
                      <Play className="size-4" />
                      {runningJob === definition.name
                        ? "Running..."
                        : definition.per_farm
                          ? "Run now"
                          : "CLI only"}
                    </Button>
                  ) : null}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="overflow-hidden rounded-2xl">
        <CardContent className="p-0">
          <div className="grid gap-3 border-b p-4 sm:grid-cols-2">
            <Select
              value={jobName}
              onValueChange={(value) => {
                setJobName(value)
                setOffset(0)
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All job definitions</SelectItem>
                {definitions.map((definition) => (
                  <SelectItem
                    key={definition.name}
                    value={definition.name}
                  >
                    {titleCase(definition.name)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={status}
              onValueChange={(value) => {
                setStatus(value)
                setOffset(0)
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All run statuses</SelectItem>
                {(["RUNNING", "SUCCESS", "FAILURE"] as BackgroundJobStatus[]).map(
                  (value) => (
                    <SelectItem key={value} value={value}>
                      {titleCase(value)}
                    </SelectItem>
                  ),
                )}
              </SelectContent>
            </Select>
          </div>

          {loading ? (
            <CommercialLoading label="Loading job-run history..." />
          ) : runs.length === 0 ? (
            <CommercialEmpty
              title="No job runs found"
              description="Change the filters or run an eligible farm-scoped job."
            />
          ) : (
            <div className="divide-y">
              {runs.map((run) => (
                <div
                  key={run.id}
                  className="grid gap-4 p-4 hover:bg-muted/30 xl:grid-cols-[1.2fr_0.8fr_1fr_0.8fr_auto] xl:items-center"
                >
                  <div>
                    <p className="font-semibold">
                      {titleCase(run.job_name)}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      Worker: {run.worker_id}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Status</p>
                    <StatusBadge status={run.status} />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Started</p>
                    <p className="text-sm font-medium">
                      {formatDateTime(run.started_at)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Duration</p>
                    <p className="font-medium">
                      {run.duration_ms === null
                        ? "Running"
                        : `${run.duration_ms.toLocaleString("en-UG")} ms`}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    className="rounded-xl"
                    onClick={() => void openDetails(run)}
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
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>Background-job run</DialogTitle>
            <DialogDescription>
              Execution status, trigger, worker, timing, result, and error details.
            </DialogDescription>
          </DialogHeader>

          {detailLoading || !selected ? (
            <CommercialLoading label="Loading job-run details..." />
          ) : (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  ["Job", titleCase(selected.job_name)],
                  ["Status", titleCase(selected.status)],
                  ["Trigger", titleCase(selected.trigger)],
                  ["Worker", selected.worker_id],
                  ["Started", formatDateTime(selected.started_at)],
                  ["Completed", formatDateTime(selected.completed_at)],
                  [
                    "Duration",
                    selected.duration_ms === null
                      ? "Not completed"
                      : `${selected.duration_ms.toLocaleString("en-UG")} ms`,
                  ],
                  ["Scheduled for", formatDateTime(selected.scheduled_for)],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-xl border p-3">
                    <p className="text-xs text-muted-foreground">{label}</p>
                    <p className="mt-1 break-all text-sm font-medium">
                      {value}
                    </p>
                  </div>
                ))}
              </div>

              {selected.error_message ? (
                <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4">
                  <p className="font-semibold text-destructive">
                    {selected.error_type ?? "Job failure"}
                  </p>
                  <p className="mt-2 text-sm leading-6">
                    {selected.error_message}
                  </p>
                </div>
              ) : null}

              <div className="rounded-2xl border p-4">
                <div className="mb-3 flex items-center gap-2">
                  <Clock3 className="size-4 text-primary" />
                  <p className="font-semibold">Result payload</p>
                </div>
                <pre className="max-h-96 overflow-auto rounded-xl bg-muted p-4 text-xs leading-5">
                  {jsonText(selected.result_json)}
                </pre>
              </div>

              <Badge variant="outline">
                Run ID: {selected.id}
              </Badge>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
