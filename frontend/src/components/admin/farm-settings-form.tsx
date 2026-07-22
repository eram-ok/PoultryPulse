"use client"

import { useState } from "react"
import {
  AlertTriangle,
  Boxes,
  CreditCard,
  Percent,
  RefreshCw,
  Save,
  ShieldCheck,
  Timer,
} from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { browserApiRequest } from "@/lib/api/browser"
import type { FarmSettings } from "@/lib/auth/types"

interface FarmSettingsForm {
  eggs_per_tray: string
  low_production_threshold: string
  mortality_alert_threshold: string
  vaccination_reminder_days: string
  session_timeout_minutes: string
  allow_negative_stock: boolean
  allow_customer_credit: boolean
  maximum_discount_percentage: string
}

function initialSettings(settings: FarmSettings): FarmSettingsForm {
  return {
    eggs_per_tray: String(settings.eggs_per_tray),
    low_production_threshold: settings.low_production_threshold,
    mortality_alert_threshold: settings.mortality_alert_threshold,
    vaccination_reminder_days: String(
      settings.vaccination_reminder_days,
    ),
    session_timeout_minutes: String(settings.session_timeout_minutes),
    allow_negative_stock: settings.allow_negative_stock,
    allow_customer_credit: settings.allow_customer_credit,
    maximum_discount_percentage: settings.maximum_discount_percentage,
  }
}

function percentage(value: string): boolean {
  const number = Number(value)
  return Number.isFinite(number) && number >= 0 && number <= 100
}

export function FarmSettingsForm({
  farmId,
  settings,
  canUpdate,
  onSaved,
}: {
  farmId: string
  settings: FarmSettings
  canUpdate: boolean
  onSaved: (settings: FarmSettings) => void
}) {
  const [form, setForm] = useState<FarmSettingsForm>(() =>
    initialSettings(settings),
  )
  const [saving, setSaving] = useState(false)

  function reset() {
    setForm(initialSettings(settings))
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const eggsPerTray = Number(form.eggs_per_tray)
    const vaccinationDays = Number(form.vaccination_reminder_days)
    const sessionTimeout = Number(form.session_timeout_minutes)

    if (
      !Number.isInteger(eggsPerTray) ||
      eggsPerTray < 1 ||
      eggsPerTray > 100
    ) {
      toast.error("Eggs per tray must be a whole number from 1 to 100.")
      return
    }

    if (
      !percentage(form.low_production_threshold) ||
      !percentage(form.mortality_alert_threshold) ||
      !percentage(form.maximum_discount_percentage)
    ) {
      toast.error("All percentage values must be between 0 and 100.")
      return
    }

    if (
      !Number.isInteger(vaccinationDays) ||
      vaccinationDays < 0 ||
      vaccinationDays > 365
    ) {
      toast.error(
        "Vaccination reminder days must be a whole number from 0 to 365.",
      )
      return
    }

    if (
      !Number.isInteger(sessionTimeout) ||
      sessionTimeout < 1 ||
      sessionTimeout > 1440
    ) {
      toast.error(
        "Session timeout must be a whole number from 1 to 1440 minutes.",
      )
      return
    }

    setSaving(true)

    try {
      const updated = await browserApiRequest<FarmSettings>(
        `/farms/${farmId}/settings`,
        {
          method: "PATCH",
          body: JSON.stringify({
            eggs_per_tray: eggsPerTray,
            low_production_threshold: form.low_production_threshold,
            mortality_alert_threshold: form.mortality_alert_threshold,
            vaccination_reminder_days: vaccinationDays,
            session_timeout_minutes: sessionTimeout,
            allow_negative_stock: form.allow_negative_stock,
            allow_customer_credit: form.allow_customer_credit,
            maximum_discount_percentage:
              form.maximum_discount_percentage,
          }),
        },
      )

      toast.success("Operational farm settings updated.")
      onSaved(updated)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Farm settings could not be updated.",
      )
    } finally {
      setSaving(false)
    }
  }

  const numericFields = [
    {
      id: "eggs-per-tray",
      label: "Eggs per tray",
      description: "Default conversion used by inventory and sales.",
      icon: Boxes,
      value: form.eggs_per_tray,
      min: "1",
      max: "100",
      step: "1",
      update: (value: string) =>
        setForm((current) => ({
          ...current,
          eggs_per_tray: value,
        })),
    },
    {
      id: "low-production-threshold",
      label: "Low-production threshold (%)",
      description: "Laying rate below which production alerts are raised.",
      icon: AlertTriangle,
      value: form.low_production_threshold,
      min: "0",
      max: "100",
      step: "0.01",
      update: (value: string) =>
        setForm((current) => ({
          ...current,
          low_production_threshold: value,
        })),
    },
    {
      id: "mortality-threshold",
      label: "Mortality alert threshold (%)",
      description: "Mortality percentage that triggers an alert.",
      icon: ShieldCheck,
      value: form.mortality_alert_threshold,
      min: "0",
      max: "100",
      step: "0.01",
      update: (value: string) =>
        setForm((current) => ({
          ...current,
          mortality_alert_threshold: value,
        })),
    },
    {
      id: "vaccination-reminder",
      label: "Vaccination reminder days",
      description: "How early upcoming vaccinations are surfaced.",
      icon: AlertTriangle,
      value: form.vaccination_reminder_days,
      min: "0",
      max: "365",
      step: "1",
      update: (value: string) =>
        setForm((current) => ({
          ...current,
          vaccination_reminder_days: value,
        })),
    },
    {
      id: "session-timeout",
      label: "Session timeout (minutes)",
      description: "Configured farm session-duration preference.",
      icon: Timer,
      value: form.session_timeout_minutes,
      min: "1",
      max: "1440",
      step: "1",
      update: (value: string) =>
        setForm((current) => ({
          ...current,
          session_timeout_minutes: value,
        })),
    },
    {
      id: "maximum-discount",
      label: "Maximum discount (%)",
      description: "Maximum permitted invoice discount for the farm.",
      icon: Percent,
      value: form.maximum_discount_percentage,
      min: "0",
      max: "100",
      step: "0.01",
      update: (value: string) =>
        setForm((current) => ({
          ...current,
          maximum_discount_percentage: value,
        })),
    },
  ]

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <CardTitle className="text-base">Operational settings</CardTitle>
        <p className="text-sm text-muted-foreground">
          Farm-specific defaults, alerts, session policy, stock control,
          customer credit, and sales limits.
        </p>
      </CardHeader>

      <CardContent>
        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 lg:grid-cols-2">
            {numericFields.map((field) => {
              const Icon = field.icon

              return (
                <div
                  key={field.id}
                  className="rounded-2xl border p-4"
                >
                  <div className="flex items-start gap-3">
                    <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
                      <Icon className="size-4" />
                    </div>
                    <div className="min-w-0 flex-1 space-y-2">
                      <Label htmlFor={field.id}>{field.label}</Label>
                      <Input
                        id={field.id}
                        type="number"
                        min={field.min}
                        max={field.max}
                        step={field.step}
                        value={field.value}
                        disabled={!canUpdate}
                        onChange={(event) =>
                          field.update(event.target.value)
                        }
                      />
                      <p className="text-xs leading-5 text-muted-foreground">
                        {field.description}
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          <div className="grid gap-4 lg:grid-cols-2">
            <label className="flex cursor-pointer items-start gap-3 rounded-2xl border p-4">
              <Checkbox
                checked={form.allow_customer_credit}
                disabled={!canUpdate}
                onCheckedChange={(checked) =>
                  setForm((current) => ({
                    ...current,
                    allow_customer_credit: checked === true,
                  }))
                }
              />
              <span>
                <span className="flex items-center gap-2 font-medium">
                  <CreditCard className="size-4 text-primary" />
                  Allow customer credit
                </span>
                <span className="mt-1 block text-xs leading-5 text-muted-foreground">
                  Allows eligible invoices to be issued on credit rather than
                  requiring immediate full payment.
                </span>
              </span>
            </label>

            <label className="flex cursor-pointer items-start gap-3 rounded-2xl border p-4">
              <Checkbox
                checked={form.allow_negative_stock}
                disabled={!canUpdate}
                onCheckedChange={(checked) =>
                  setForm((current) => ({
                    ...current,
                    allow_negative_stock: checked === true,
                  }))
                }
              />
              <span>
                <span className="flex items-center gap-2 font-medium">
                  <Boxes className="size-4 text-primary" />
                  Allow negative stock
                </span>
                <span className="mt-1 block text-xs leading-5 text-muted-foreground">
                  Permits transactions to move stock below zero. Keep disabled
                  unless the farm has a controlled operational reason.
                </span>
              </span>
            </label>
          </div>

          {form.allow_negative_stock ? (
            <div className="rounded-2xl border border-warning/40 bg-warning/10 p-4">
              <p className="font-medium text-warning-foreground">
                Negative-stock control is enabled
              </p>
              <p className="mt-1 text-sm leading-6 text-muted-foreground">
                This may allow sales or adjustments that exceed recorded
                inventory. Review stock reconciliation procedures before saving.
              </p>
            </div>
          ) : null}

          {canUpdate ? (
            <div className="flex flex-wrap justify-end gap-2">
              <Button type="button" variant="outline" onClick={reset}>
                <RefreshCw className="size-4" />
                Reset
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="size-4" />
                {saving ? "Saving..." : "Save operational settings"}
              </Button>
            </div>
          ) : (
            <p className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
              Your role can view operational settings but cannot update them.
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
