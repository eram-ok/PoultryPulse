"use client"

import Link from "next/link"
import {
  Activity,
  ArrowLeft,
  Ban,
  Building2,
  CheckCircle2,
  CirclePause,
  KeyRound,
  LoaderCircle,
  Mail,
  Pencil,
  RefreshCw,
  Save,
  ShieldCheck,
  UsersRound,
  X,
} from "lucide-react"
import { useCallback, useEffect, useState } from "react"

import { OneTimeSetupUrl } from "@/components/platform/one-time-setup-url"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  formatPlatformDate,
  jsonRequestInit,
  optionalText,
  platformFarmRequest,
  requiredText,
} from "@/lib/platform-farms/api"
import type {
  PlatformFarmDetail,
  PlatformFarmInvitationIssue,
  PlatformFarmOnboardingStatus,
} from "@/lib/platform-farms/types"
import type { FarmLifecycleStatus } from "@/lib/platform-auth/types"

interface PlatformFarmDetailOverviewProps {
  farmId: string
}

type LifecycleAction = "activate" | "suspend" | "deactivate"

function statusClass(status: FarmLifecycleStatus): string {
  if (status === "ACTIVE") return "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300"
  if (status === "SUSPENDED") return "border-amber-500/25 bg-amber-500/10 text-amber-700 dark:text-amber-300"
  return "border-destructive/25 bg-destructive/8 text-destructive"
}

function ProfileField(props: {
  name: string
  label: string
  value: string
  type?: string
  required?: boolean
  minLength?: number
  maxLength?: number
}) {
  return (
    <div className="space-y-2">
      <label htmlFor={`edit-${props.name}`} className="text-sm font-medium">{props.label}</label>
      <Input
        id={`edit-${props.name}`}
        name={props.name}
        type={props.type ?? "text"}
        required={props.required}
        defaultValue={props.value}
        minLength={props.minLength}
        maxLength={props.maxLength}
        className="h-11 rounded-xl"
      />
    </div>
  )
}

export function PlatformFarmDetailOverview({ farmId }: PlatformFarmDetailOverviewProps) {
  const [farm, setFarm] = useState<PlatformFarmDetail | null>(null)
  const [onboarding, setOnboarding] = useState<PlatformFarmOnboardingStatus | null>(null)
  const [setupUrl, setSetupUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [pendingAction, setPendingAction] = useState<string | null>(null)
  const [selectedLifecycleAction, setSelectedLifecycleAction] = useState<LifecycleAction | null>(null)
  const [refreshKey, setRefreshKey] = useState(0)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const encodedFarmId = encodeURIComponent(farmId)
      const [farmResponse, onboardingResponse] = await Promise.all([
        platformFarmRequest<PlatformFarmDetail>(`/platform/farms/${encodedFarmId}`),
        platformFarmRequest<PlatformFarmOnboardingStatus>(`/platform/farms/${encodedFarmId}/onboarding`),
      ])
      setFarm(farmResponse)
      setOnboarding(onboardingResponse)
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "The farm workspace could not be loaded.")
    } finally {
      setLoading(false)
    }
  }, [farmId])

  useEffect(() => {
    const timer = window.setTimeout(() => void load(), 0)
    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  async function updateFarm(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!farm) return
    setPendingAction("update")
    setError(null)
    const form = new FormData(event.currentTarget)

    try {
      const response = await platformFarmRequest<PlatformFarmDetail>(
        `/platform/farms/${encodeURIComponent(farm.id)}`,
        jsonRequestInit("PATCH", {
          farm_code: requiredText(form.get("farm_code")),
          name: requiredText(form.get("name")),
          owner_name: optionalText(form.get("owner_name")),
          telephone: optionalText(form.get("telephone")),
          email: optionalText(form.get("email")),
          district: optionalText(form.get("district")),
          address: optionalText(form.get("address")),
          logo_url: optionalText(form.get("logo_url")),
          timezone: requiredText(form.get("timezone")),
          currency_code: requiredText(form.get("currency_code")).toUpperCase(),
        }),
      )
      setFarm(response)
      setEditing(false)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The farm profile could not be updated.")
    } finally {
      setPendingAction(null)
    }
  }

  async function applyLifecycle(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!farm || !selectedLifecycleAction) return
    const form = new FormData(event.currentTarget)
    const reason = requiredText(form.get("reason"))
    const action = selectedLifecycleAction

    if (action !== "activate" && reason.length < 5) {
      setError("Suspension and deactivation require a reason of at least five characters.")
      return
    }

    setPendingAction(action)
    setError(null)
    setSetupUrl(null)
    try {
      const response = await platformFarmRequest<PlatformFarmDetail>(
        `/platform/farms/${encodeURIComponent(farm.id)}/${action}`,
        jsonRequestInit("POST", { reason: reason || null }),
      )
      setFarm(response)
      setSelectedLifecycleAction(null)
      setRefreshKey((value) => value + 1)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The lifecycle action could not be completed.")
    } finally {
      setPendingAction(null)
    }
  }

  async function resendInvitation() {
    if (!farm) return
    setPendingAction("resend")
    setSetupUrl(null)
    setError(null)
    try {
      const response = await platformFarmRequest<PlatformFarmInvitationIssue>(
        `/platform/farms/${encodeURIComponent(farm.id)}/onboarding/resend`,
        { method: "POST" },
      )
      setSetupUrl(response.setup_url)
      setOnboarding((current) => current ? { ...current, invitation: response.invitation } : current)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The invitation could not be reissued.")
    } finally {
      setPendingAction(null)
    }
  }

  async function revokeInvitation(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!farm) return
    const reason = requiredText(new FormData(event.currentTarget).get("revocation_reason"))
    if (reason.length < 5) {
      setError("Enter a revocation reason of at least five characters.")
      return
    }

    setPendingAction("revoke")
    setSetupUrl(null)
    setError(null)
    try {
      const response = await platformFarmRequest<PlatformFarmOnboardingStatus>(
        `/platform/farms/${encodeURIComponent(farm.id)}/onboarding/revoke`,
        jsonRequestInit("POST", { reason }),
      )
      setOnboarding(response)
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The invitation could not be revoked.")
    } finally {
      setPendingAction(null)
    }
  }

  if (loading && !farm) {
    return <div className="grid min-h-[60vh] place-items-center"><LoaderCircle className="size-8 animate-spin text-primary" /></div>
  }

  if (!farm) {
    return (
      <div className="mx-auto max-w-xl rounded-3xl border border-destructive/25 bg-destructive/8 p-6">
        <h1 className="text-xl font-semibold">Farm unavailable</h1>
        <p className="mt-2 text-sm text-destructive">{error ?? "The requested farm could not be loaded."}</p>
        <Button asChild variant="outline" className="mt-5 rounded-xl"><Link href="/platform/farms"><ArrowLeft className="size-4" /> Farm registry</Link></Button>
      </div>
    )
  }

  const invitation = onboarding?.invitation
  const onboardingCompleted = Boolean(onboarding?.completed || onboarding?.legacy_completed)
  const invitationCanBeManaged = !onboardingCompleted
  const farmIsActive = farm.lifecycle_status === "ACTIVE"
  const lifecycleOptions: Array<{
    action: LifecycleAction
    label: string
    icon: typeof Activity
    description: string
  }> = [
    { action: "activate", label: "Activate farm", icon: Activity, description: "Restore tenant access and normal operations." },
    { action: "suspend", label: "Suspend farm", icon: CirclePause, description: "Temporarily block tenant sessions and writes." },
    { action: "deactivate", label: "Deactivate farm", icon: Ban, description: "Close tenant access until explicitly reactivated." },
  ]

  return (
    <div className="space-y-6">
      <section className="flex flex-col justify-between gap-4 rounded-[28px] border border-border/70 bg-card/74 p-5 shadow-sm backdrop-blur sm:p-7 lg:flex-row lg:items-end">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="rounded-full border-primary/25 bg-primary/8 text-primary"><Building2 className="mr-1 size-3" />{farm.farm_code}</Badge>
            <Badge variant="outline" className={`rounded-full ${statusClass(farm.lifecycle_status)}`}>{farm.lifecycle_status}</Badge>
          </div>
          <h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">{farm.name}</h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground sm:text-base">
            Manage customer profile, administrator onboarding, invitation delivery, and tenant lifecycle.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline" className="rounded-xl"><Link href="/platform/farms"><ArrowLeft className="size-4" /> Registry</Link></Button>
          <Button type="button" variant="outline" className="rounded-xl" disabled={loading} onClick={() => setRefreshKey((value) => value + 1)}>
            {loading ? <LoaderCircle className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Refresh
          </Button>
        </div>
      </section>

      {error ? <div role="alert" className="rounded-2xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm text-destructive">{error}</div> : null}

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {[
          { label: "Total users", value: farm.total_users, icon: UsersRound },
          { label: "Active users", value: farm.active_users, icon: CheckCircle2 },
          { label: "Recent logins", value: farm.recent_login_users, icon: Activity },
          { label: "Active sessions", value: farm.active_refresh_sessions, icon: ShieldCheck },
        ].map((item) => {
          const Icon = item.icon
          return (
            <Card key={item.label} className="rounded-3xl border-border/70 bg-card/82">
              <CardContent className="flex items-center justify-between p-5">
                <div><p className="text-sm text-muted-foreground">{item.label}</p><p className="mt-2 text-3xl font-semibold">{item.value}</p></div>
                <div className="grid size-11 place-items-center rounded-2xl bg-primary/10 text-primary"><Icon className="size-5" /></div>
              </CardContent>
            </Card>
          )
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(380px,0.8fr)]">
        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader className="gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div><CardTitle>Farm profile</CardTitle><CardDescription className="mt-2">Updated {formatPlatformDate(farm.updated_at)}</CardDescription></div>
            <Button type="button" variant="outline" size="sm" className="rounded-xl" onClick={() => setEditing((value) => !value)}>
              {editing ? <X className="size-4" /> : <Pencil className="size-4" />}{editing ? "Cancel" : "Edit profile"}
            </Button>
          </CardHeader>
          <CardContent>
            {editing ? (
              <form key={farm.updated_at} className="grid gap-4 md:grid-cols-2" onSubmit={updateFarm}>
                <ProfileField name="farm_code" label="Farm code" value={farm.farm_code} required maxLength={30} />
                <ProfileField name="name" label="Farm name" value={farm.name} required maxLength={150} />
                <ProfileField name="owner_name" label="Owner name" value={farm.owner_name ?? ""} maxLength={150} />
                <ProfileField name="telephone" label="Telephone" value={farm.telephone ?? ""} maxLength={30} />
                <ProfileField name="email" label="Email" value={farm.email ?? ""} type="email" />
                <ProfileField name="district" label="District" value={farm.district ?? ""} maxLength={100} />
                <ProfileField name="timezone" label="Timezone" value={farm.timezone} required maxLength={50} />
                <ProfileField name="currency_code" label="Currency" value={farm.currency_code} required minLength={3} maxLength={3} />
                <ProfileField name="logo_url" label="Logo URL" value={farm.logo_url ?? ""} type="url" />
                <div className="space-y-2 md:col-span-2">
                  <label htmlFor="edit-address" className="text-sm font-medium">Address</label>
                  <textarea id="edit-address" name="address" rows={3} defaultValue={farm.address ?? ""} className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" />
                </div>
                <div className="md:col-span-2">
                  <Button type="submit" className="rounded-xl" disabled={pendingAction === "update"}>
                    {pendingAction === "update" ? <LoaderCircle className="size-4 animate-spin" /> : <Save className="size-4" />} Save farm profile
                  </Button>
                </div>
              </form>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2">
                {[
                  ["Owner", farm.owner_name],
                  ["Telephone", farm.telephone],
                  ["Email", farm.email],
                  ["District", farm.district],
                  ["Address", farm.address],
                  ["Timezone", farm.timezone],
                  ["Currency", farm.currency_code],
                  ["Last farm login", formatPlatformDate(farm.last_login_at)],
                ].map(([label, value]) => (
                  <div key={label} className="rounded-2xl bg-muted/30 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 break-words font-medium">{value || "Not recorded"}</p></div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-3xl border-border/70 bg-card/82">
          <CardHeader><CardTitle>Tenant lifecycle</CardTitle><CardDescription>Last changed {formatPlatformDate(farm.lifecycle_changed_at)}</CardDescription></CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border border-border/70 p-4">
              <p className="text-xs text-muted-foreground">Current state</p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <Badge variant="outline" className={`rounded-full ${statusClass(farm.lifecycle_status)}`}>{farm.lifecycle_status}</Badge>
                <span className="text-sm text-muted-foreground">{farm.is_active ? "Tenant access enabled" : "Tenant access restricted"}</span>
              </div>
              {farm.lifecycle_reason ? <p className="mt-3 text-sm leading-6 text-muted-foreground">{farm.lifecycle_reason}</p> : null}
            </div>

            <div className="grid gap-2">
              {lifecycleOptions.map((option) => {
                const Icon = option.icon
                const disabled =
                  (option.action === "activate" && farm.lifecycle_status === "ACTIVE") ||
                  (option.action === "suspend" && farm.lifecycle_status === "SUSPENDED") ||
                  (option.action === "deactivate" && farm.lifecycle_status === "DEACTIVATED")
                return (
                  <button key={option.action} type="button" disabled={disabled} className="flex items-start gap-3 rounded-2xl border border-border/70 p-3 text-left transition hover:bg-muted/35 disabled:cursor-not-allowed disabled:opacity-45" onClick={() => setSelectedLifecycleAction(option.action)}>
                    <div className="grid size-9 shrink-0 place-items-center rounded-xl bg-muted/50"><Icon className="size-4" /></div>
                    <div><p className="text-sm font-semibold">{option.label}</p><p className="mt-1 text-xs leading-5 text-muted-foreground">{option.description}</p></div>
                  </button>
                )
              })}
            </div>

            {selectedLifecycleAction ? (
              <form className="space-y-3 rounded-2xl border border-primary/20 bg-primary/5 p-4" onSubmit={applyLifecycle}>
                <label htmlFor="lifecycle-reason" className="text-sm font-medium">
                  {selectedLifecycleAction === "activate" ? "Activation note (optional)" : "Required reason"}
                </label>
                <textarea id="lifecycle-reason" name="reason" rows={3} required={selectedLifecycleAction !== "activate"} minLength={selectedLifecycleAction === "activate" ? undefined : 5} maxLength={1000} className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" />
                <div className="flex gap-2">
                  <Button type="submit" className="rounded-xl" disabled={pendingAction === selectedLifecycleAction}>
                    {pendingAction === selectedLifecycleAction ? <LoaderCircle className="size-4 animate-spin" /> : <ShieldCheck className="size-4" />} Confirm {selectedLifecycleAction}
                  </Button>
                  <Button type="button" variant="ghost" className="rounded-xl" onClick={() => setSelectedLifecycleAction(null)}>Cancel</Button>
                </div>
              </form>
            ) : null}
          </CardContent>
        </Card>
      </section>

      <Card className="rounded-3xl border-border/70 bg-card/82">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><KeyRound className="size-5 text-primary" /> Administrator onboarding</CardTitle>
          <CardDescription>Invitation state and first-administrator activation controls.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {[
              ["Administrator", onboarding?.administrator_username ? `@${onboarding.administrator_username}` : "Unavailable"],
              ["Email", onboarding?.administrator_email ?? "Unavailable"],
              ["Activation", onboardingCompleted ? "Completed" : "Pending"],
              ["Invitation", invitation?.status ?? (onboarding?.legacy_completed ? "Legacy completed" : "Unavailable")],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl bg-muted/30 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 break-words font-medium">{value}</p></div>
            ))}
          </div>

          {invitation ? (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {[
                ["Delivery", invitation.delivery_status],
                ["Attempts", String(invitation.delivery_attempt_count)],
                ["Expires", formatPlatformDate(invitation.expires_at)],
                ["Sent", formatPlatformDate(invitation.sent_at)],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-border/70 p-4"><p className="text-xs text-muted-foreground">{label}</p><p className="mt-1 font-semibold">{value}</p></div>
              ))}
            </div>
          ) : null}

          {invitation?.last_delivery_error ? <div className="rounded-2xl border border-destructive/25 bg-destructive/8 p-4 text-sm text-destructive">{invitation.last_delivery_error}</div> : null}
          {setupUrl ? <OneTimeSetupUrl url={setupUrl} title="Reissued one-time setup link" /> : null}

          {invitationCanBeManaged ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-2xl border border-border/70 p-4">
                <div className="flex items-start gap-3">
                  <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary"><Mail className="size-5" /></div>
                  <div><p className="font-semibold">Reissue invitation</p><p className="mt-1 text-sm leading-6 text-muted-foreground">Revokes the previous secret and returns a new one-time setup URL.</p></div>
                </div>
                {!farmIsActive ? <p className="mt-3 text-xs leading-5 text-amber-700 dark:text-amber-300">Activate the farm before reissuing an invitation.</p> : null}
                <Button type="button" variant="outline" className="mt-4 rounded-xl" disabled={pendingAction === "resend" || !farmIsActive} onClick={() => void resendInvitation()}>
                  {pendingAction === "resend" ? <LoaderCircle className="size-4 animate-spin" /> : <RefreshCw className="size-4" />} Reissue invitation
                </Button>
              </div>

              <form className="rounded-2xl border border-destructive/20 p-4" onSubmit={revokeInvitation}>
                <p className="font-semibold">Revoke pending invitation</p>
                <p className="mt-1 text-sm leading-6 text-muted-foreground">The administrator will no longer be able to use the current setup link.</p>
                <textarea name="revocation_reason" rows={3} required minLength={5} maxLength={1000} className="mt-3 w-full rounded-xl border border-input bg-background px-3 py-2 text-sm outline-none focus-visible:ring-2 focus-visible:ring-ring" placeholder="Reason for revocation" />
                <Button type="submit" variant="outline" className="mt-3 rounded-xl border-destructive/30 text-destructive hover:bg-destructive/8" disabled={pendingAction === "revoke" || invitation?.status !== "PENDING"}>
                  {pendingAction === "revoke" ? <LoaderCircle className="size-4 animate-spin" /> : <Ban className="size-4" />} Revoke invitation
                </Button>
              </form>
            </div>
          ) : (
            <div className="rounded-2xl border border-emerald-500/25 bg-emerald-500/8 p-4 text-sm text-emerald-800 dark:text-emerald-200">
              The first administrator has completed account activation. Invitation secrets are no longer manageable.
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
