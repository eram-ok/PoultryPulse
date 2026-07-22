"use client"

import Link from "next/link"
import { useState } from "react"
import {
  AtSign,
  BadgeCheck,
  Building2,
  CalendarClock,
  KeyRound,
  Mail,
  MapPin,
  Pencil,
  Phone,
  Save,
  ShieldCheck,
  UserCog,
  UserRound,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import {
  CommercialPageHeader,
  StatusBadge,
} from "@/components/commercial/commercial-ui"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { browserApiRequest } from "@/lib/api/browser"
import type { AuthenticatedUser } from "@/lib/auth/types"

function formatDateTime(value: string | null): string {
  if (!value) return "Not recorded"

  return new Intl.DateTimeFormat("en-UG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value))
}

function initials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
}

function optional(value: string): string | null {
  const trimmed = value.trim()
  return trimmed || null
}

function EditProfileDialog({
  user,
  onOpenChange,
}: {
  user: AuthenticatedUser
  onOpenChange: (open: boolean) => void
}) {
  const [firstName, setFirstName] = useState(user.first_name)
  const [lastName, setLastName] = useState(user.last_name)
  const [email, setEmail] = useState(user.email ?? "")
  const [telephone, setTelephone] = useState(user.telephone ?? "")
  const [saving, setSaving] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (firstName.trim().length < 1 || lastName.trim().length < 1) {
      toast.error("First name and last name are required.")
      return
    }

    setSaving(true)

    try {
      const payload: {
        first_name?: string
        last_name?: string
        email?: string | null
        telephone?: string | null
      } = {}

      const normalizedFirstName = firstName.trim()
      const normalizedLastName = lastName.trim()
      const normalizedEmail = optional(email)
      const normalizedTelephone = optional(telephone)

      if (normalizedFirstName !== user.first_name) {
        payload.first_name = normalizedFirstName
      }

      if (normalizedLastName !== user.last_name) {
        payload.last_name = normalizedLastName
      }

      if (normalizedEmail !== user.email) {
        payload.email = normalizedEmail
      }

      if (normalizedTelephone !== user.telephone) {
        payload.telephone = normalizedTelephone
      }

      if (Object.keys(payload).length === 0) {
        toast.info("No profile changes were detected.")
        setSaving(false)
        return
      }

      await browserApiRequest<AuthenticatedUser>(
        `/users/${user.id}`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
      )

      toast.success("Your profile was updated.")
      onOpenChange(false)

      window.setTimeout(() => {
        window.location.reload()
      }, 250)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Your profile could not be updated.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Edit personal profile</DialogTitle>
          <DialogDescription>
            Update your name and contact details. Your username and access roles
            are managed separately.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="profile-first-name">First name</Label>
              <Input
                id="profile-first-name"
                value={firstName}
                maxLength={100}
                onChange={(event) => setFirstName(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-last-name">Last name</Label>
              <Input
                id="profile-last-name"
                value={lastName}
                maxLength={100}
                onChange={(event) => setLastName(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-email">Email</Label>
              <Input
                id="profile-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="profile-telephone">Telephone</Label>
              <Input
                id="profile-telephone"
                value={telephone}
                maxLength={30}
                onChange={(event) => setTelephone(event.target.value)}
                placeholder="+256..."
              />
            </div>
          </div>

          <div className="rounded-xl border bg-muted/25 p-4">
            <p className="text-xs text-muted-foreground">Username</p>
            <p className="mt-1 font-semibold">@{user.username}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              The current backend does not support changing usernames.
            </p>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              <Save className="size-4" />
              {saving ? "Saving..." : "Save profile"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function ProfileWorkspace() {
  const { session } = useAuth()
  const user = session.user
  const farm = session.farm
  const permissions = session.permissions
  const [editing, setEditing] = useState(false)

  const canEdit = permissions.includes("users.update")
  const canViewUsers = permissions.includes("users.view")
  const canViewFarm = permissions.includes("farms.view")

  const permissionModules = Array.from(
    new Set(
      user.roles.flatMap((role) =>
        role.permissions.map((permission) => permission.module),
      ),
    ),
  ).sort()

  const detailItems = [
    {
      label: "Username",
      value: `@${user.username}`,
      icon: AtSign,
    },
    {
      label: "Email",
      value: user.email ?? "Not recorded",
      icon: Mail,
    },
    {
      label: "Telephone",
      value: user.telephone ?? "Not recorded",
      icon: Phone,
    },
    {
      label: "Last login",
      value: formatDateTime(user.last_login_at),
      icon: CalendarClock,
    },
  ]

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="My account"
        title="Personal profile"
        description="Review your PoultryPulse identity, contact details, farm context, security status, roles, and effective access."
        actions={
          <>
            <Button asChild variant="outline" className="rounded-xl">
              <Link href="/change-password">
                <KeyRound className="size-4" />
                Change password
              </Link>
            </Button>
            {canEdit ? (
              <Button
                className="rounded-xl"
                onClick={() => setEditing(true)}
              >
                <Pencil className="size-4" />
                Edit profile
              </Button>
            ) : null}
          </>
        }
      />

      <Card className="overflow-hidden rounded-2xl">
        <div className="h-28 bg-gradient-to-r from-primary/25 via-primary/10 to-transparent" />

        <CardContent className="relative p-5 sm:p-6">
          <div className="-mt-16 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
              <div className="grid size-24 place-items-center rounded-3xl border-4 border-background bg-primary text-3xl font-semibold text-primary-foreground shadow-lg">
                {initials(user.first_name, user.last_name)}
              </div>

              <div className="pb-1">
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-2xl font-semibold tracking-tight">
                    {user.full_name}
                  </h2>
                  {user.is_verified ? (
                    <BadgeCheck className="size-5 text-primary" />
                  ) : null}
                  <StatusBadge
                    status={user.is_active ? "ACTIVE" : "INACTIVE"}
                  />
                </div>
                <p className="mt-1 text-sm text-muted-foreground">
                  {farm.name} · {session.roles.join(", ") || "No active role"}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 pb-1">
              {user.is_verified ? (
                <Badge variant="secondary">
                  <ShieldCheck className="mr-1 size-3.5" />
                  Verified
                </Badge>
              ) : (
                <Badge variant="outline">Not verified</Badge>
              )}
              {user.must_change_password ? (
                <Badge variant="destructive">Password change required</Badge>
              ) : (
                <Badge variant="outline">Password current</Badge>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Identity and contact</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            {detailItems.map((item) => {
              const Icon = item.icon

              return (
                <div key={item.label} className="rounded-2xl border p-4">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Icon className="size-4" />
                    <p className="text-xs">{item.label}</p>
                  </div>
                  <p className="mt-2 break-words font-semibold">
                    {item.value}
                  </p>
                </div>
              )
            })}

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <CalendarClock className="size-4" />
                <p className="text-xs">Account created</p>
              </div>
              <p className="mt-2 font-semibold">
                {formatDateTime(user.created_at)}
              </p>
            </div>

            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-2 text-muted-foreground">
                <UserRound className="size-4" />
                <p className="text-xs">Account ID</p>
              </div>
              <p className="mt-2 break-all font-mono text-xs font-medium">
                {user.id}
              </p>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Farm context</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-2xl border p-4">
              <div className="flex items-center gap-3">
                <div className="grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Building2 className="size-5" />
                </div>
                <div>
                  <p className="font-semibold">{farm.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {farm.farm_code}
                  </p>
                </div>
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-xl border p-3">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <MapPin className="size-4" />
                  <p className="text-xs">District</p>
                </div>
                <p className="mt-1 font-medium">
                  {farm.district ?? "Not recorded"}
                </p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Timezone</p>
                <p className="mt-1 font-medium">{farm.timezone}</p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Currency</p>
                <p className="mt-1 font-medium">{farm.currency_code}</p>
              </div>
              <div className="rounded-xl border p-3">
                <p className="text-xs text-muted-foreground">Farm status</p>
                <p className="mt-1 font-medium">
                  {farm.is_active ? "Active" : "Inactive"}
                </p>
              </div>
            </div>

            {canViewFarm ? (
              <Button asChild variant="outline" className="w-full rounded-xl">
                <Link href="/settings">
                  <Building2 className="size-4" />
                  Open farm settings
                </Link>
              </Button>
            ) : null}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Assigned roles</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {user.roles.length === 0 ? (
              <p className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                No role is assigned to this account.
              </p>
            ) : (
              user.roles.map((role) => (
                <div key={role.id} className="rounded-2xl border p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">{role.name}</p>
                        {role.is_system_role ? (
                          <ShieldCheck className="size-4 text-primary" />
                        ) : null}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        {role.description ?? "No role description"}
                      </p>
                    </div>
                    <StatusBadge
                      status={role.is_active ? "ACTIVE" : "INACTIVE"}
                    />
                  </div>
                  <p className="mt-3 text-xs text-muted-foreground">
                    {role.permissions.length} permissions
                  </p>
                </div>
              ))
            )}

            {canViewUsers ? (
              <Button asChild variant="outline" className="w-full rounded-xl">
                <Link href="/users">
                  <UserCog className="size-4" />
                  Open user administration
                </Link>
              </Button>
            ) : null}
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle className="text-base">Effective access</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {permissionModules.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No effective permission modules are available.
                </p>
              ) : (
                permissionModules.map((module) => (
                  <Badge key={module} variant="outline">
                    {module}
                  </Badge>
                ))
              )}
            </div>

            <details className="mt-4 rounded-2xl border p-4">
              <summary className="cursor-pointer font-medium">
                View all {permissions.length} permission codes
              </summary>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                {permissions.map((permission) => (
                  <code
                    key={permission}
                    className="rounded-lg bg-muted px-3 py-2 text-xs"
                  >
                    {permission}
                  </code>
                ))}
              </div>
            </details>
          </CardContent>
        </Card>
      </div>

      <Card className="rounded-2xl border-dashed">
        <CardContent className="p-4 text-sm leading-6 text-muted-foreground">
          Your personal profile is separate from the farm profile. Use
          <strong className="font-medium text-foreground">
            {" "}Change password{" "}
          </strong>
          for account credentials and
          <strong className="font-medium text-foreground">
            {" "}Farm settings{" "}
          </strong>
          for business identity and operational rules.
        </CardContent>
      </Card>

      {editing ? (
        <EditProfileDialog
          user={user}
          onOpenChange={setEditing}
        />
      ) : null}
    </div>
  )
}
