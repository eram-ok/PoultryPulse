"use client"

import Link from "next/link"
import { ArrowLeft, Building2, LoaderCircle, RotateCcw, Save, ShieldCheck, UserRoundPlus } from "lucide-react"
import { useRef, useState, useTransition } from "react"

import { OneTimeSetupUrl } from "@/components/platform/one-time-setup-url"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  jsonRequestInit,
  numberValue,
  optionalText,
  platformFarmRequest,
  requiredText,
} from "@/lib/platform-farms/api"
import type { PlatformFarmCreatePayload, PlatformFarmCreateResponse } from "@/lib/platform-farms/types"

function idempotencyKey(): string {
  return `farm-onboarding-${crypto.randomUUID()}`
}

function TextField(props: {
  name: string
  label: string
  type?: string
  required?: boolean
  placeholder?: string
  defaultValue?: string
  minLength?: number
  maxLength?: number
  pattern?: string
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={props.name} className="text-sm font-medium">{props.label}</label>
      <Input
        id={props.name}
        name={props.name}
        type={props.type ?? "text"}
        required={props.required}
        placeholder={props.placeholder}
        defaultValue={props.defaultValue}
        minLength={props.minLength}
        maxLength={props.maxLength}
        pattern={props.pattern}
        className="h-11 rounded-xl"
      />
    </div>
  )
}

function NumberField(props: {
  name: string
  label: string
  value: string
  min: string
  max: string
  step: string
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={props.name} className="text-sm font-medium">{props.label}</label>
      <Input
        id={props.name}
        name={props.name}
        type="number"
        required
        defaultValue={props.value}
        min={props.min}
        max={props.max}
        step={props.step}
        className="h-11 rounded-xl"
      />
    </div>
  )
}

export function PlatformFarmCreateWorkspace() {
  const [result, setResult] = useState<PlatformFarmCreateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, startTransition] = useTransition()
  const requestKey = useRef<string | null>(null)

  function reset() {
    requestKey.current = null
    setResult(null)
    setError(null)
  }

  function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    const form = new FormData(event.currentTarget)

    const payload: PlatformFarmCreatePayload = {
      farm_code: requiredText(form.get("farm_code")),
      name: requiredText(form.get("name")),
      owner_name: optionalText(form.get("owner_name")),
      telephone: optionalText(form.get("telephone")),
      email: optionalText(form.get("email")),
      district: optionalText(form.get("district")),
      address: optionalText(form.get("address")),
      logo_url: optionalText(form.get("logo_url")),
      timezone: requiredText(form.get("timezone")) || "Africa/Kampala",
      currency_code: (requiredText(form.get("currency_code")) || "UGX").toUpperCase(),
      settings: {
        eggs_per_tray: numberValue(form.get("eggs_per_tray"), 30),
        low_production_threshold: numberValue(form.get("low_production_threshold"), 70),
        mortality_alert_threshold: numberValue(form.get("mortality_alert_threshold"), 1),
        vaccination_reminder_days: numberValue(form.get("vaccination_reminder_days"), 3),
        session_timeout_minutes: numberValue(form.get("session_timeout_minutes"), 60),
        allow_negative_stock: form.get("allow_negative_stock") === "on",
        allow_customer_credit: form.get("allow_customer_credit") === "on",
        maximum_discount_percentage: numberValue(form.get("maximum_discount_percentage"), 0),
      },
      first_administrator: {
        username: requiredText(form.get("administrator_username")).toLowerCase(),
        email: requiredText(form.get("administrator_email")),
        telephone: optionalText(form.get("administrator_telephone")),
        first_name: requiredText(form.get("administrator_first_name")),
        last_name: requiredText(form.get("administrator_last_name")),
      },
    }

    requestKey.current ??= idempotencyKey()

    startTransition(async () => {
      try {
        const response = await platformFarmRequest<PlatformFarmCreateResponse>(
          "/platform/farms",
          jsonRequestInit("POST", payload, { "Idempotency-Key": requestKey.current ?? "" }),
        )
        setResult(response)
      } catch (requestError) {
        setError(requestError instanceof Error ? requestError.message : "The customer farm could not be registered.")
      }
    })
  }

  if (result) {
    return (
      <div className="mx-auto max-w-4xl space-y-6">
        <section className="rounded-[28px] border border-emerald-500/25 bg-emerald-500/8 p-6 sm:p-8">
          <div className="grid size-12 place-items-center rounded-2xl bg-emerald-500/15 text-emerald-700 dark:text-emerald-300">
            <ShieldCheck className="size-6" />
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-tight">Farm registered</h1>
          <p className="mt-3 text-sm leading-6 text-muted-foreground">
            {result.farm.name} was created with farm code {result.farm.farm_code}. The first administrator remains inactive until the invitation is accepted.
          </p>
        </section>

        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader>
            <CardTitle>First administrator</CardTitle>
            <CardDescription>
              {result.administrator.first_name} {result.administrator.last_name} · @{result.administrator.username}
            </CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-3">
            {[
              ["Invitation", result.invitation.status],
              ["Delivery", result.invitation.delivery_status],
              ["Account", "Awaiting activation"],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-muted/30 p-4">
                <p className="text-xs text-muted-foreground">{label}</p>
                <p className="mt-1 font-semibold">{value}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {result.setup_url ? (
          <OneTimeSetupUrl url={result.setup_url} />
        ) : (
          <div className="rounded-2xl border border-border/70 bg-card/72 p-4 text-sm leading-6 text-muted-foreground">
            The secret setup URL was not returned because this was an idempotent replay. Reissue the invitation from the farm workspace when necessary.
          </div>
        )}

        <div className="flex flex-wrap gap-2">
          <Button asChild className="rounded-xl"><Link href={`/platform/farms/${result.farm.id}`}>Open farm workspace</Link></Button>
          <Button asChild variant="outline" className="rounded-xl"><Link href="/platform/farms">Return to registry</Link></Button>
          <Button type="button" variant="ghost" className="rounded-xl" onClick={reset}>
            <RotateCcw className="size-4" /> Register another farm
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 rounded-[28px] border border-border/70 bg-card/74 p-5 shadow-sm backdrop-blur sm:p-7 lg:flex-row lg:items-end">
        <div>
          <Badge variant="outline" className="rounded-full border-primary/25 bg-primary/8 text-primary">
            <Building2 className="mr-1 size-3" /> Secure onboarding
          </Badge>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Register customer farm</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
            Create the isolated farm tenant, default operating settings, and first administrator invitation in one atomic request.
          </p>
        </div>
        <Button asChild variant="outline" className="rounded-xl">
          <Link href="/platform/farms"><ArrowLeft className="size-4" /> Farm registry</Link>
        </Button>
      </section>

      <form className="space-y-6" onSubmit={submit}>
        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Building2 className="size-5 text-primary" /> Farm profile</CardTitle>
            <CardDescription>Customer identity, location, contact, and regional settings.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <TextField name="farm_code" label="Farm code" placeholder="PP-FARM-002" required maxLength={30} />
            <TextField name="name" label="Farm name" placeholder="Customer farm name" required maxLength={150} />
            <TextField name="owner_name" label="Owner name" placeholder="Farm owner" maxLength={150} />
            <TextField name="telephone" label="Farm telephone" placeholder="+256…" maxLength={30} />
            <TextField name="email" label="Farm email" type="email" placeholder="farm@example.com" />
            <TextField name="district" label="District" placeholder="Mukono" maxLength={100} />
            <TextField name="timezone" label="Timezone" defaultValue="Africa/Kampala" required maxLength={50} />
            <TextField name="currency_code" label="Currency" defaultValue="UGX" required minLength={3} maxLength={3} />
            <TextField name="logo_url" label="Logo URL" type="url" placeholder="https://…" />
            <div className="space-y-2 md:col-span-2">
              <label htmlFor="address" className="text-sm font-medium">Address</label>
              <textarea id="address" name="address" rows={3} className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Physical or postal address" />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><UserRoundPlus className="size-5 text-primary" /> First farm administrator</CardTitle>
            <CardDescription>This person receives the one-time account setup invitation.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2">
            <TextField name="administrator_first_name" label="First name" required maxLength={100} />
            <TextField name="administrator_last_name" label="Last name" required maxLength={100} />
            <TextField name="administrator_username" label="Username" required minLength={3} maxLength={50} pattern="[A-Za-z0-9._-]+" placeholder="farmadmin" />
            <TextField name="administrator_email" label="Email" type="email" required placeholder="admin@example.com" />
            <TextField name="administrator_telephone" label="Telephone" placeholder="+256…" maxLength={30} />
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader>
            <CardTitle>Default operating settings</CardTitle>
            <CardDescription>The customer farm administrator can adjust these later.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <NumberField name="eggs_per_tray" label="Eggs per tray" value="30" min="1" max="100" step="1" />
            <NumberField name="low_production_threshold" label="Low production %" value="70" min="0" max="100" step="0.01" />
            <NumberField name="mortality_alert_threshold" label="Mortality alert %" value="1" min="0" max="100" step="0.01" />
            <NumberField name="vaccination_reminder_days" label="Vaccination reminder days" value="3" min="0" max="365" step="1" />
            <NumberField name="session_timeout_minutes" label="Session timeout minutes" value="60" min="1" max="1440" step="1" />
            <NumberField name="maximum_discount_percentage" label="Maximum discount %" value="0" min="0" max="100" step="0.01" />
            <label className="flex items-center gap-3 rounded-2xl border border-border/70 p-4 text-sm">
              <input type="checkbox" name="allow_customer_credit" defaultChecked className="size-4" /> Allow customer credit
            </label>
            <label className="flex items-center gap-3 rounded-2xl border border-border/70 p-4 text-sm">
              <input type="checkbox" name="allow_negative_stock" className="size-4" /> Allow negative stock
            </label>
          </CardContent>
        </Card>

        {error ? <div role="alert" className="rounded-2xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm text-destructive">{error}</div> : null}
        <div className="flex justify-end">
          <Button type="submit" className="h-12 rounded-xl px-6" disabled={pending}>
            {pending ? <LoaderCircle className="size-4 animate-spin" /> : <Save className="size-4" />}
            {pending ? "Registering farm…" : "Register farm and invite administrator"}
          </Button>
        </div>
      </form>
    </div>
  )
}
