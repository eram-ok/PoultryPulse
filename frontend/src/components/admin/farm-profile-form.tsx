"use client"

import { useState } from "react"
import { Building2, RefreshCw, Save } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { browserApiRequest } from "@/lib/api/browser"
import type { Farm } from "@/lib/auth/types"

interface FarmProfileForm {
  farm_code: string
  name: string
  owner_name: string
  telephone: string
  email: string
  district: string
  address: string
  logo_url: string
  timezone: string
  currency_code: string
}

function initialProfile(farm: Farm): FarmProfileForm {
  return {
    farm_code: farm.farm_code,
    name: farm.name,
    owner_name: farm.owner_name ?? "",
    telephone: farm.telephone ?? "",
    email: farm.email ?? "",
    district: farm.district ?? "",
    address: farm.address ?? "",
    logo_url: farm.logo_url ?? "",
    timezone: farm.timezone,
    currency_code: farm.currency_code,
  }
}

function optional(value: string): string | null {
  const trimmed = value.trim()
  return trimmed || null
}

export function FarmProfileForm({
  farm,
  canUpdate,
  onSaved,
}: {
  farm: Farm
  canUpdate: boolean
  onSaved: (farm: Farm) => void
}) {
  const [form, setForm] = useState<FarmProfileForm>(() =>
    initialProfile(farm),
  )
  const [saving, setSaving] = useState(false)

  function reset() {
    setForm(initialProfile(farm))
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (form.farm_code.trim().length < 2 || form.name.trim().length < 2) {
      toast.error("Farm code and farm name must contain at least two characters.")
      return
    }

    if (form.currency_code.trim().length !== 3) {
      toast.error("Currency code must contain exactly three letters.")
      return
    }

    setSaving(true)

    try {
      const updated = await browserApiRequest<Farm>(
        `/farms/${farm.id}`,
        {
          method: "PATCH",
          body: JSON.stringify({
            farm_code: form.farm_code.trim(),
            name: form.name.trim(),
            owner_name: optional(form.owner_name),
            telephone: optional(form.telephone),
            email: optional(form.email),
            district: optional(form.district),
            address: optional(form.address),
            logo_url: optional(form.logo_url),
            timezone: form.timezone.trim(),
            currency_code: form.currency_code.trim().toUpperCase(),
          }),
        },
      )

      toast.success(
        "Farm profile updated. Reloading the application will refresh the farm name everywhere.",
      )
      onSaved(updated)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The farm profile could not be updated.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="rounded-2xl">
      <CardHeader>
        <div className="flex items-center gap-3">
          <div className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
            <Building2 className="size-5" />
          </div>
          <div>
            <CardTitle className="text-base">Farm profile</CardTitle>
            <p className="mt-1 text-sm text-muted-foreground">
              Identity, ownership, contact, location, and regional settings.
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="settings-farm-code">Farm code</Label>
              <Input
                id="settings-farm-code"
                value={form.farm_code}
                minLength={2}
                maxLength={30}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    farm_code: event.target.value,
                  }))
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-farm-name">Farm name</Label>
              <Input
                id="settings-farm-name"
                value={form.name}
                minLength={2}
                maxLength={150}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    name: event.target.value,
                  }))
                }
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-owner-name">Owner name</Label>
              <Input
                id="settings-owner-name"
                value={form.owner_name}
                maxLength={150}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    owner_name: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-telephone">Telephone</Label>
              <Input
                id="settings-telephone"
                value={form.telephone}
                maxLength={30}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    telephone: event.target.value,
                  }))
                }
                placeholder="+256..."
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-email">Email</Label>
              <Input
                id="settings-email"
                type="email"
                value={form.email}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    email: event.target.value,
                  }))
                }
                placeholder="farm@example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-district">District</Label>
              <Input
                id="settings-district"
                value={form.district}
                maxLength={100}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    district: event.target.value,
                  }))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-timezone">Timezone</Label>
              <Input
                id="settings-timezone"
                value={form.timezone}
                maxLength={50}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    timezone: event.target.value,
                  }))
                }
                placeholder="Africa/Kampala"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings-currency">Currency code</Label>
              <Input
                id="settings-currency"
                value={form.currency_code}
                minLength={3}
                maxLength={3}
                disabled={!canUpdate}
                className="uppercase"
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    currency_code: event.target.value.toUpperCase(),
                  }))
                }
                placeholder="UGX"
                required
              />
            </div>

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="settings-logo-url">Logo URL</Label>
              <Input
                id="settings-logo-url"
                type="url"
                value={form.logo_url}
                disabled={!canUpdate}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    logo_url: event.target.value,
                  }))
                }
                placeholder="https://..."
              />
              <p className="text-xs text-muted-foreground">
                The backend currently stores a URL; direct image upload is not
                part of the available API contract.
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="settings-address">Address</Label>
            <Textarea
              id="settings-address"
              rows={3}
              value={form.address}
              disabled={!canUpdate}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  address: event.target.value,
                }))
              }
            />
          </div>

          <div className="rounded-xl border bg-muted/20 p-4">
            <p className="text-xs text-muted-foreground">Farm status</p>
            <p className="mt-1 font-semibold">
              {farm.is_active ? "Active" : "Inactive"}
            </p>
            <p className="mt-1 text-xs leading-5 text-muted-foreground">
              Status is shown read-only because deactivating the currently
              signed-in farm could make the application unusable and there is
              no dedicated farm-reactivation workflow.
            </p>
          </div>

          {canUpdate ? (
            <div className="flex flex-wrap justify-end gap-2">
              <Button type="button" variant="outline" onClick={reset}>
                <RefreshCw className="size-4" />
                Reset
              </Button>
              <Button type="submit" disabled={saving}>
                <Save className="size-4" />
                {saving ? "Saving..." : "Save farm profile"}
              </Button>
            </div>
          ) : (
            <p className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">
              Your role can view this profile but cannot update it.
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
