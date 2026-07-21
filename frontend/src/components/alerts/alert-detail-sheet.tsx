"use client"

import { useEffect, useState } from "react"
import {
  Check,
  CheckCheck,
  CircleDot,
  Clock3,
  Eye,
  EyeOff,
  History,
  RotateCcw,
  ShieldCheck,
  UserRoundCheck,
  X,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { browserApiRequest } from "@/lib/api/browser"
import type {
  AlertEvent,
  AlertEventListResponse,
  PersistentAlert,
} from "@/lib/api/operations"
import {
  formatDateTime,
  formatEnum,
} from "@/lib/operational/format"
import { cn } from "@/lib/utils"

interface AlertDetailSheetProps {
  alert: PersistentAlert | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onChanged: (alert: PersistentAlert) => void
}

type NoteAction = "acknowledge" | "resolve" | "reopen"

const severityClasses = {
  INFO: "bg-cyan-500/12 text-cyan-500 border-cyan-500/20",
  WARNING:
    "bg-amber-500/12 text-amber-500 border-amber-500/20",
  CRITICAL:
    "bg-red-500/12 text-red-500 border-red-500/20",
}

export function AlertDetailSheet({
  alert,
  open,
  onOpenChange,
  onChanged,
}: AlertDetailSheetProps) {
  const { session } = useAuth()
  const [events, setEvents] = useState<AlertEvent[]>([])
  const [loadingEvents, setLoadingEvents] = useState(true)
  const [working, setWorking] = useState(false)
  const [noteAction, setNoteAction] =
    useState<NoteAction | null>(null)
  const [notes, setNotes] = useState("")

  const canAssign =
    session.permissions.includes("alerts.assign")
  const canAcknowledge =
    session.permissions.includes("alerts.acknowledge")
  const canResolve =
    session.permissions.includes("alerts.resolve")

  useEffect(() => {
    if (!open || !alert) {
      return
    }

    const controller = new AbortController()

    browserApiRequest<AlertEventListResponse>(
      `/alerts/${alert.id}/events`,
      { signal: controller.signal },
    )
      .then((payload) => setEvents(payload.items))
      .catch(() => setEvents([]))
      .finally(() => setLoadingEvents(false))

    return () => controller.abort()
  }, [alert, open])

  async function runSimpleAction(
    action:
      | "read"
      | "unread"
      | "dismiss"
      | "restore"
      | "assign",
  ) {
    if (!alert) {
      return
    }

    setWorking(true)

    try {
      const body =
        action === "assign"
          ? JSON.stringify({
              assigned_to: session.user.id,
              notes: "Assigned from the PoultryPulse web workspace.",
            })
          : undefined

      const updated =
        await browserApiRequest<PersistentAlert>(
          `/alerts/${alert.id}/${action}`,
          {
            method: "POST",
            body,
          },
        )

      onChanged(updated)
      toast.success(
        action === "assign"
          ? "Alert assigned to you."
          : `Alert ${action === "read" ? "marked as read" : formatEnum(action).toLowerCase()}.`,
      )
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The alert could not be updated.",
      )
    } finally {
      setWorking(false)
    }
  }

  async function submitNoteAction() {
    if (!alert || !noteAction) {
      return
    }

    setWorking(true)

    try {
      const updated =
        await browserApiRequest<PersistentAlert>(
          `/alerts/${alert.id}/${noteAction}`,
          {
            method: "POST",
            body: JSON.stringify({
              notes: notes.trim() || null,
            }),
          },
        )

      onChanged(updated)
      setNoteAction(null)
      setNotes("")
      toast.success(
        `Alert ${formatEnum(noteAction).toLowerCase()}.`,
      )
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The alert action could not be completed.",
      )
    } finally {
      setWorking(false)
    }
  }

  if (!alert) {
    return null
  }

  return (
    <>
      <Sheet open={open} onOpenChange={onOpenChange}>
        <SheetContent className="w-full border-border/80 sm:max-w-xl">
          <SheetHeader className="border-b border-border/70 px-6 py-5">
            <div className="flex flex-wrap items-center gap-2 pr-8">
              <span
                className={cn(
                  "rounded-full border px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider",
                  severityClasses[alert.severity],
                )}
              >
                {formatEnum(alert.severity)}
              </span>
              <span className="rounded-full border border-border bg-muted/40 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
                {formatEnum(alert.status)}
              </span>
              {!alert.is_read ? (
                <span className="rounded-full bg-primary/12 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wider text-primary">
                  Unread
                </span>
              ) : null}
            </div>
            <SheetTitle className="pr-8 text-xl">
              {alert.title}
            </SheetTitle>
            <SheetDescription className="leading-6">
              {alert.message}
            </SheetDescription>
          </SheetHeader>

          <ScrollArea className="min-h-0 flex-1">
            <div className="space-y-6 px-6 py-5">
              <section className="grid gap-3 sm:grid-cols-2">
                <Detail label="Alert type" value={formatEnum(alert.alert_type)} />
                <Detail label="Source" value={formatEnum(alert.source_module)} />
                <Detail
                  label="First detected"
                  value={formatDateTime(alert.first_detected_at)}
                />
                <Detail
                  label="Last detected"
                  value={formatDateTime(alert.last_detected_at)}
                />
                <Detail
                  label="Occurrences"
                  value={String(alert.occurrence_count)}
                />
                <Detail
                  label="Assignment"
                  value={
                    alert.assigned_to === session.user.id
                      ? "Assigned to you"
                      : alert.assigned_to
                        ? "Assigned to another user"
                        : "Unassigned"
                  }
                />
              </section>

              {alert.resolution_notes ? (
                <section className="rounded-2xl border border-primary/20 bg-primary/8 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-primary">
                    Resolution notes
                  </p>
                  <p className="mt-2 text-sm leading-6">
                    {alert.resolution_notes}
                  </p>
                </section>
              ) : null}

              <section>
                <div className="mb-3 flex items-center gap-2">
                  <History className="size-4 text-primary" />
                  <h3 className="text-sm font-semibold">
                    Alert activity
                  </h3>
                </div>

                {loadingEvents ? (
                  <p className="text-sm text-muted-foreground">
                    Loading alert history…
                  </p>
                ) : events.length === 0 ? (
                  <p className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
                    No alert events have been recorded yet.
                  </p>
                ) : (
                  <div className="space-y-3">
                    {events.map((event) => (
                      <div
                        key={event.id}
                        className="flex gap-3 rounded-xl border border-border/70 bg-muted/15 p-3"
                      >
                        <div className="mt-0.5 grid size-7 shrink-0 place-items-center rounded-full bg-primary/10 text-primary">
                          <CircleDot className="size-3.5" />
                        </div>
                        <div className="min-w-0">
                          <p className="text-sm font-medium">
                            {formatEnum(event.event_type)}
                          </p>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {formatDateTime(event.created_at)}
                          </p>
                          {event.notes ? (
                            <p className="mt-2 text-xs leading-5 text-muted-foreground">
                              {event.notes}
                            </p>
                          ) : null}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </section>
            </div>
          </ScrollArea>

          <div className="border-t border-border/70 p-4">
            <div className="flex flex-wrap gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={working}
                onClick={() =>
                  void runSimpleAction(
                    alert.is_read ? "unread" : "read",
                  )
                }
              >
                {alert.is_read ? (
                  <EyeOff className="size-4" />
                ) : (
                  <Eye className="size-4" />
                )}
                {alert.is_read ? "Mark unread" : "Mark read"}
              </Button>

              <Button
                variant="outline"
                size="sm"
                disabled={working}
                onClick={() =>
                  void runSimpleAction(
                    alert.is_dismissed
                      ? "restore"
                      : "dismiss",
                  )
                }
              >
                {alert.is_dismissed ? (
                  <RotateCcw className="size-4" />
                ) : (
                  <X className="size-4" />
                )}
                {alert.is_dismissed ? "Restore" : "Dismiss"}
              </Button>

              {canAssign &&
              alert.assigned_to !== session.user.id ? (
                <Button
                  variant="outline"
                  size="sm"
                  disabled={working}
                  onClick={() =>
                    void runSimpleAction("assign")
                  }
                >
                  <UserRoundCheck className="size-4" />
                  Assign to me
                </Button>
              ) : null}

              {canAcknowledge &&
              alert.status === "OPEN" ? (
                <Button
                  size="sm"
                  disabled={working}
                  onClick={() =>
                    setNoteAction("acknowledge")
                  }
                >
                  <Check className="size-4" />
                  Acknowledge
                </Button>
              ) : null}

              {canResolve &&
              alert.status !== "RESOLVED" ? (
                <Button
                  size="sm"
                  disabled={working}
                  onClick={() =>
                    setNoteAction("resolve")
                  }
                >
                  <ShieldCheck className="size-4" />
                  Resolve
                </Button>
              ) : null}

              {canResolve &&
              alert.status === "RESOLVED" ? (
                <Button
                  size="sm"
                  disabled={working}
                  onClick={() =>
                    setNoteAction("reopen")
                  }
                >
                  <RotateCcw className="size-4" />
                  Reopen
                </Button>
              ) : null}
            </div>
          </div>
        </SheetContent>
      </Sheet>

      <Dialog
        open={noteAction !== null}
        onOpenChange={(nextOpen) => {
          if (!nextOpen) {
            setNoteAction(null)
            setNotes("")
          }
        }}
      >
        <DialogContent className="rounded-2xl">
          <DialogHeader>
            <DialogTitle>
              {noteAction
                ? `${formatEnum(noteAction)} alert`
                : "Update alert"}
            </DialogTitle>
            <DialogDescription>
              Add an operational note so other farm users can
              understand this decision.
            </DialogDescription>
          </DialogHeader>

          <textarea
            value={notes}
            onChange={(event) =>
              setNotes(event.target.value)
            }
            placeholder="Optional notes…"
            className="border-input bg-background min-h-28 w-full rounded-xl border px-3 py-2 text-sm outline-none focus-visible:border-ring focus-visible:ring-[3px] focus-visible:ring-ring/50"
          />

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setNoteAction(null)
                setNotes("")
              }}
            >
              Cancel
            </Button>
            <Button
              disabled={working}
              onClick={() => void submitNoteAction()}
            >
              {working ? (
                <Clock3 className="size-4 animate-spin" />
              ) : (
                <CheckCheck className="size-4" />
              )}
              Confirm action
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}

function Detail({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-muted/15 p-3">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  )
}
