"use client"

import { useCallback, useEffect, useState } from "react"
import {
  Building2,
  CalendarClock,
  Coins,
  MapPin,
  Settings,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import { FarmProfileForm } from "@/components/admin/farm-profile-form"
import { FarmSettingsForm } from "@/components/admin/farm-settings-form"
import {
  CommercialLoading,
  CommercialMetric,
  CommercialPageHeader,
  RefreshButton,
  StatusBadge,
} from "@/components/commercial/commercial-ui"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { browserApiRequest } from "@/lib/api/browser"
import type {
  Farm,
  FarmSettings,
} from "@/lib/auth/types"
import { formatDate } from "@/lib/commercial/format"

export function SettingsWorkspace() {
  const { session } = useAuth()
  const farmId = session.farm.id
  const permissions = session.permissions

  const [farm, setFarm] = useState<Farm | null>(null)
  const [settings, setSettings] = useState<FarmSettings | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const canUpdateProfile = permissions.includes("farms.update")
  const canUpdateSettings = permissions.includes("farms.settings.update")

  const load = useCallback(async () => {
    setLoading(true)

    try {
      const [farmResponse, settingsResponse] = await Promise.all([
        browserApiRequest<Farm>(`/farms/${farmId}`),
        browserApiRequest<FarmSettings>(
          `/farms/${farmId}/settings`,
        ),
      ])

      setFarm(farmResponse)
      setSettings(settingsResponse)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Farm settings could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [farmId])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  if (loading || !farm || !settings) {
    return <CommercialLoading label="Loading farm settings..." />
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Administration"
        title="Farm and application settings"
        description="Maintain the current farm profile and the operational rules used throughout production, inventory, health, sales, alerts, and authentication."
        actions={
          <RefreshButton
            onClick={() => setRefreshKey((current) => current + 1)}
            loading={loading}
          />
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CommercialMetric
          label="Farm code"
          value={farm.farm_code}
          detail={farm.name}
          icon={Building2}
        />
        <CommercialMetric
          label="Location"
          value={farm.district ?? "Not set"}
          detail={farm.timezone}
          icon={MapPin}
        />
        <CommercialMetric
          label="Currency"
          value={farm.currency_code}
          detail="Commercial display currency"
          icon={Coins}
        />
        <CommercialMetric
          label="Last settings update"
          value={formatDate(settings.updated_at)}
          detail={`${settings.session_timeout_minutes} minute session setting`}
          icon={CalendarClock}
        />
      </div>

      <Card className="rounded-2xl">
        <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div className="flex items-center gap-3">
            <div className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
              <Settings className="size-5" />
            </div>
            <div>
              <p className="font-semibold">{farm.name}</p>
              <p className="text-sm text-muted-foreground">
                Current signed-in farm context
              </p>
            </div>
          </div>
          <StatusBadge status={farm.is_active ? "ACTIVE" : "INACTIVE"} />
        </CardContent>
      </Card>

      <Tabs defaultValue="profile">
        <TabsList className="h-auto rounded-xl">
          <TabsTrigger value="profile">Farm profile</TabsTrigger>
          <TabsTrigger value="operations">Operational settings</TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-5">
          <FarmProfileForm
            key={`${farm.id}-${farm.updated_at}`}
            farm={farm}
            canUpdate={canUpdateProfile}
            onSaved={setFarm}
          />
        </TabsContent>

        <TabsContent value="operations" className="mt-5">
          <FarmSettingsForm
            key={`${settings.id}-${settings.updated_at}`}
            farmId={farm.id}
            settings={settings}
            canUpdate={canUpdateSettings}
            onSaved={setSettings}
          />
        </TabsContent>
      </Tabs>

      <Card className="rounded-2xl border-dashed">
        <CardContent className="p-4 text-sm leading-6 text-muted-foreground">
          PoultryPulse currently operates in the authenticated user&apos;s
          single-farm context. Although the API contains a farm-registration
          endpoint, it has no farm-switching workflow, so this page deliberately
          manages only the active signed-in farm rather than creating an
          inaccessible second farm.
        </CardContent>
      </Card>
    </div>
  )
}
