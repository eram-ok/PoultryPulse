"use client"

import { useEffect, useState } from "react"
import {
  Bird,
  CalendarDays,
  Home,
  Scale,
  TrendingDown,
  TrendingUp,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import { Skeleton } from "@/components/ui/skeleton"
import { browserApiRequest } from "@/lib/api/browser"
import type {
  Flock,
  PopulationSummary,
  PopulationTransaction,
  PopulationTransactionListResponse,
} from "@/lib/api/operations"
import {
  formatDate,
  formatDateTime,
  formatEnum,
  formatNumber,
} from "@/lib/operational/format"

interface FlockDetailSheetProps {
  flock: Flock | null
  open: boolean
  onOpenChange: (open: boolean) => void
  canAdjust: boolean
  canEdit: boolean
  onAdjust: () => void
  onEdit: () => void
}

export function FlockDetailSheet({
  flock,
  open,
  onOpenChange,
  canAdjust,
  canEdit,
  onAdjust,
  onEdit,
}: FlockDetailSheetProps) {
  const [summary, setSummary] =
    useState<PopulationSummary | null>(null)
  const [transactions, setTransactions] =
    useState<PopulationTransaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!open || !flock) {
      return
    }

    const controller = new AbortController()

    Promise.all([
      browserApiRequest<PopulationSummary>(
        `/flocks/${flock.id}/population`,
        { signal: controller.signal },
      ),
      browserApiRequest<PopulationTransactionListResponse>(
        `/flocks/${flock.id}/population-transactions?offset=0&limit=20`,
        { signal: controller.signal },
      ),
    ])
      .then(([population, ledger]) => {
        setSummary(population)
        setTransactions(ledger.items)
      })
      .catch(() => {
        setSummary(null)
        setTransactions([])
      })
      .finally(() => setLoading(false))

    return () => controller.abort()
  }, [flock, open])

  if (!flock) {
    return null
  }

  const occupancy = summary
    ? Math.min(
        100,
        (summary.house_occupancy /
          Math.max(1, summary.house_capacity)) *
          100,
      )
    : 0

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full border-border/80 sm:max-w-xl">
        <SheetHeader className="border-b border-border/70 px-6 py-5">
          <div className="mb-1 flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-primary">
            <Bird className="size-4" />
            {flock.flock_code}
          </div>
          <SheetTitle className="text-xl">
            {flock.name}
          </SheetTitle>
          <SheetDescription>
            {flock.breed} · {formatEnum(flock.production_stage)} ·{" "}
            {formatEnum(flock.status)}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="min-h-0 flex-1">
          <div className="space-y-6 px-6 py-5">
            {loading ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {Array.from({ length: 4 }).map((_, index) => (
                  <Skeleton
                    key={index}
                    className="h-24 rounded-xl"
                  />
                ))}
              </div>
            ) : (
              <>
                <section className="grid gap-3 sm:grid-cols-2">
                  <DetailCard
                    icon={Bird}
                    label="Current population"
                    value={formatNumber(
                      summary?.current_population ??
                        flock.current_population,
                    )}
                  />
                  <DetailCard
                    icon={Home}
                    label="Assigned house"
                    value={`${flock.house_code} · ${flock.house_name}`}
                  />
                  <DetailCard
                    icon={CalendarDays}
                    label="Arrival date"
                    value={formatDate(flock.arrival_date)}
                  />
                  <DetailCard
                    icon={Scale}
                    label="Initial population"
                    value={formatNumber(flock.initial_population)}
                  />
                </section>

                <section className="rounded-2xl border border-border/70 bg-muted/15 p-4">
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <p className="text-sm font-semibold">
                        House occupancy
                      </p>
                      <p className="mt-1 text-xs text-muted-foreground">
                        {formatNumber(
                          summary?.house_occupancy ??
                            flock.current_population,
                        )}{" "}
                        of {formatNumber(flock.house_capacity)} birds
                      </p>
                    </div>
                    <p className="font-mono text-lg font-semibold">
                      {occupancy.toFixed(0)}%
                    </p>
                  </div>
                  <Progress
                    value={occupancy}
                    className="mt-4 h-2.5"
                  />
                  <p className="mt-2 text-xs text-muted-foreground">
                    {formatNumber(
                      summary?.available_house_capacity ??
                        Math.max(
                          0,
                          flock.house_capacity -
                            flock.current_population,
                        ),
                    )}{" "}
                    spaces remain in this house.
                  </p>
                </section>

                <section>
                  <div className="mb-3 flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-semibold">
                        Population ledger
                      </h3>
                      <p className="mt-1 text-xs text-muted-foreground">
                        Latest 20 population movements.
                      </p>
                    </div>
                    {canAdjust ? (
                      <Button
                        size="sm"
                        className="rounded-xl"
                        onClick={onAdjust}
                      >
                        <Scale className="size-4" />
                        Adjust
                      </Button>
                    ) : null}
                  </div>

                  {transactions.length === 0 ? (
                    <div className="rounded-xl border border-dashed p-5 text-sm text-muted-foreground">
                      No population movements have been recorded.
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {transactions.map((item) => {
                        const positive =
                          item.signed_quantity >= 0

                        return (
                          <div
                            key={item.id}
                            className="flex items-center gap-3 rounded-xl border border-border/70 bg-background/45 p-3"
                          >
                            <div
                              className={
                                positive
                                  ? "grid size-8 place-items-center rounded-full bg-primary/10 text-primary"
                                  : "grid size-8 place-items-center rounded-full bg-red-500/10 text-red-500"
                              }
                            >
                              {positive ? (
                                <TrendingUp className="size-4" />
                              ) : (
                                <TrendingDown className="size-4" />
                              )}
                            </div>
                            <div className="min-w-0 flex-1">
                              <p className="text-sm font-medium">
                                {formatEnum(item.transaction_type)}
                              </p>
                              <p className="truncate text-xs text-muted-foreground">
                                {item.description ||
                                  formatDateTime(item.created_at)}
                              </p>
                            </div>
                            <p
                              className={
                                positive
                                  ? "font-mono text-sm font-semibold text-primary"
                                  : "font-mono text-sm font-semibold text-red-500"
                              }
                            >
                              {positive ? "+" : ""}
                              {formatNumber(item.signed_quantity)}
                            </p>
                          </div>
                        )
                      })}
                    </div>
                  )}
                </section>
              </>
            )}
          </div>
        </ScrollArea>

        {canEdit || canAdjust ? (
          <div className="flex flex-wrap gap-2 border-t border-border/70 p-4">
            {canEdit ? (
              <Button
                variant="outline"
                className="rounded-xl"
                onClick={onEdit}
              >
                Edit flock
              </Button>
            ) : null}
            {canAdjust ? (
              <Button
                className="rounded-xl"
                onClick={onAdjust}
              >
                <Scale className="size-4" />
                Adjust population
              </Button>
            ) : null}
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}

function DetailCard({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Bird
  label: string
  value: string
}) {
  return (
    <div className="rounded-xl border border-border/70 bg-muted/15 p-4">
      <Icon className="size-4 text-primary" />
      <p className="mt-3 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  )
}
