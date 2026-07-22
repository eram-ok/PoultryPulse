"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  KeyRound,
  Pencil,
  Plus,
  Power,
  PowerOff,
  RefreshCw,
  Search,
  ShieldCheck,
  UserCheck,
  UserCog,
  Users,
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
import { UserDialog } from "@/components/admin/user-dialog"
import { UserRolesDialog } from "@/components/admin/user-roles-dialog"
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
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { browserApiRequest } from "@/lib/api/browser"
import { formatDate } from "@/lib/commercial/format"
import type {
  AdminRole,
  AdminUser,
  AdminUserList,
} from "@/lib/admin/types"

type AdminTab = "users" | "roles"
const limit = 20

export function UsersWorkspace() {
  const { session } = useAuth()
  const permissions = session.permissions
  const currentUserId = session.user.id

  const [tab, setTab] = useState<AdminTab>("users")
  const [users, setUsers] = useState<AdminUser[]>([])
  const [roles, setRoles] = useState<AdminRole[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("ALL")
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const [editingUser, setEditingUser] =
    useState<AdminUser | null | undefined>(undefined)
  const [roleUser, setRoleUser] = useState<AdminUser | null>(null)
  const [detailUser, setDetailUser] = useState<AdminUser | null>(null)

  const canCreate = permissions.includes("users.create")
  const canUpdate = permissions.includes("users.update")
  const canDeactivate = permissions.includes("users.deactivate")
  const canViewRoles = permissions.includes("roles.view")
  const canAssignRoles = permissions.includes("roles.assign")

  const load = useCallback(async () => {
    setLoading(true)

    try {
      const userPromise = browserApiRequest<AdminUserList>(
        `/users?offset=${offset}&limit=${limit}`,
      )
      const rolePromise = canViewRoles
        ? browserApiRequest<AdminRole[]>("/roles")
        : Promise.resolve([] as AdminRole[])

      const [userResponse, roleResponse] = await Promise.all([
        userPromise,
        rolePromise,
      ])

      setUsers(userResponse.items)
      setTotal(userResponse.total)
      setRoles(roleResponse)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "User administration data could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [canViewRoles, offset])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  const visibleUsers = useMemo(() => {
    const needle = search.trim().toLowerCase()

    return users.filter((user) => {
      if (status === "ACTIVE" && !user.is_active) return false
      if (status === "INACTIVE" && user.is_active) return false
      if (!needle) return true

      return [
        user.username,
        user.full_name,
        user.email ?? "",
        user.telephone ?? "",
        ...user.roles.map((role) => role.name),
      ].some((value) => value.toLowerCase().includes(needle))
    })
  }, [search, status, users])

  const metrics = useMemo(
    () => ({
      active: users.filter((user) => user.is_active).length,
      verified: users.filter((user) => user.is_verified).length,
      passwordChange: users.filter(
        (user) => user.must_change_password,
      ).length,
    }),
    [users],
  )

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  function replaceUser(updated: AdminUser) {
    setUsers((current) =>
      current.map((user) => (user.id === updated.id ? updated : user)),
    )
    refresh()
  }

  async function toggleStatus(user: AdminUser) {
    if (user.id === currentUserId && user.is_active) {
      toast.error("You cannot deactivate your own signed-in account.")
      return
    }

    const endpoint = `/users/${user.id}/${
      user.is_active ? "deactivate" : "activate"
    }`

    try {
      const updated = await browserApiRequest<AdminUser>(endpoint, {
        method: "POST",
      })
      toast.success(
        user.is_active ? "User deactivated." : "User activated.",
      )
      replaceUser(updated)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "User status could not be changed.",
      )
    }
  }

  function changeTab(value: string) {
    setTab(value as AdminTab)
    setSearch("")
    setStatus("ALL")
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Administration"
        title="Users, roles, and access"
        description="Create farm accounts, maintain user profiles, control activation, assign existing roles, and inspect role permissions."
        actions={
          <>
            <RefreshButton onClick={refresh} loading={loading} />
            {canCreate && canViewRoles ? (
              <Button
                className="rounded-xl"
                onClick={() => setEditingUser(null)}
              >
                <Plus className="size-4" />
                Create user
              </Button>
            ) : null}
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CommercialMetric
          label="Farm users"
          value={String(total)}
          detail="Accounts registered for this farm"
          icon={Users}
        />
        <CommercialMetric
          label="Active on page"
          value={String(metrics.active)}
          detail="May sign in when otherwise eligible"
          icon={UserCheck}
        />
        <CommercialMetric
          label="Verified on page"
          value={String(metrics.verified)}
          detail="Administratively verified accounts"
          icon={ShieldCheck}
        />
        <CommercialMetric
          label="Password change required"
          value={String(metrics.passwordChange)}
          detail="Users prompted at next sign-in"
          icon={KeyRound}
        />
      </div>

      <Card className="overflow-hidden rounded-2xl">
        <CardContent className="p-0">
          <div className="border-b p-4">
            <Tabs value={tab} onValueChange={changeTab}>
              <TabsList className="h-auto rounded-xl">
                <TabsTrigger value="users">Users</TabsTrigger>
                {canViewRoles ? (
                  <TabsTrigger value="roles">Role definitions</TabsTrigger>
                ) : null}
              </TabsList>
            </Tabs>

            {tab === "users" ? (
              <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_210px]">
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder="Filter users loaded on this page..."
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </div>

                <Select value={status} onValueChange={setStatus}>
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ALL">All activity states</SelectItem>
                    <SelectItem value="ACTIVE">Active only</SelectItem>
                    <SelectItem value="INACTIVE">Inactive only</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            ) : null}
          </div>

          {loading ? (
            <CommercialLoading label="Loading administration data..." />
          ) : tab === "users" ? (
            visibleUsers.length === 0 ? (
              <CommercialEmpty
                title="No users found"
                description="Change the page filter or create the first additional farm account."
              />
            ) : (
              <div className="divide-y">
                {visibleUsers.map((user) => (
                  <div
                    key={user.id}
                    className="grid gap-4 p-4 hover:bg-muted/30 xl:grid-cols-[1.25fr_1fr_1fr_auto] xl:items-center"
                  >
                    <button
                      type="button"
                      className="text-left"
                      onClick={() => setDetailUser(user)}
                    >
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="font-semibold">{user.full_name}</p>
                        <StatusBadge
                          status={user.is_active ? "ACTIVE" : "INACTIVE"}
                        />
                        {user.id === currentUserId ? (
                          <Badge variant="outline">You</Badge>
                        ) : null}
                      </div>
                      <p className="mt-1 text-sm text-muted-foreground">
                        @{user.username}
                      </p>
                    </button>

                    <div>
                      <p className="text-xs text-muted-foreground">Contact</p>
                      <p className="text-sm font-medium">
                        {user.email ?? "No email"}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {user.telephone ?? "No telephone"}
                      </p>
                    </div>

                    <div>
                      <p className="text-xs text-muted-foreground">Roles</p>
                      <div className="mt-1 flex flex-wrap gap-1">
                        {user.roles.length === 0 ? (
                          <span className="text-sm text-destructive">
                            No roles assigned
                          </span>
                        ) : (
                          user.roles.map((role) => (
                            <Badge key={role.id} variant="secondary">
                              {role.name}
                            </Badge>
                          ))
                        )}
                      </div>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      {canUpdate ? (
                        <Button
                          size="sm"
                          variant="ghost"
                          className="rounded-xl"
                          onClick={() => setEditingUser(user)}
                        >
                          <Pencil className="size-4" />
                          Edit
                        </Button>
                      ) : null}

                      {canAssignRoles && canViewRoles ? (
                        <Button
                          size="sm"
                          variant="outline"
                          className="rounded-xl"
                          onClick={() => setRoleUser(user)}
                        >
                          <UserCog className="size-4" />
                          Roles
                        </Button>
                      ) : null}

                      {user.is_active
                        ? canDeactivate && user.id !== currentUserId
                          ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="rounded-xl text-destructive"
                                onClick={() => void toggleStatus(user)}
                              >
                                <PowerOff className="size-4" />
                                Deactivate
                              </Button>
                            )
                          : null
                        : canUpdate
                          ? (
                              <Button
                                size="sm"
                                variant="ghost"
                                className="rounded-xl text-emerald-700 dark:text-emerald-300"
                                onClick={() => void toggleStatus(user)}
                              >
                                <Power className="size-4" />
                                Activate
                              </Button>
                            )
                          : null}
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : roles.length === 0 ? (
            <CommercialEmpty
              title="No roles available"
              description="No role definitions were returned for this farm."
            />
          ) : (
            <div className="grid gap-4 p-4 lg:grid-cols-2">
              {roles.map((role) => {
                const modules = Array.from(
                  new Set(role.permissions.map((permission) => permission.module)),
                ).sort()

                return (
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

                    <div className="mt-4 flex flex-wrap gap-2">
                      {modules.map((module) => (
                        <Badge key={module} variant="outline">
                          {module}
                        </Badge>
                      ))}
                    </div>

                    <details className="mt-4 rounded-xl border bg-muted/20 p-3">
                      <summary className="cursor-pointer text-sm font-medium">
                        {role.permissions.length} permissions
                      </summary>
                      <div className="mt-3 space-y-2">
                        {role.permissions.map((permission) => (
                          <div
                            key={permission.id}
                            className="rounded-lg bg-background p-2"
                          >
                            <p className="font-mono text-xs font-medium">
                              {permission.code}
                            </p>
                            <p className="mt-1 text-xs text-muted-foreground">
                              {permission.description ?? permission.name}
                            </p>
                          </div>
                        ))}
                      </div>
                    </details>
                  </div>
                )
              })}
            </div>
          )}

          {tab === "users" ? (
            <CommercialPager
              offset={offset}
              limit={limit}
              total={total}
              onChange={setOffset}
            />
          ) : null}
        </CardContent>
      </Card>

      {editingUser !== undefined ? (
        <UserDialog
          user={editingUser}
          roles={roles}
          onOpenChange={(open) => {
            if (!open) setEditingUser(undefined)
          }}
          onSaved={(saved) => {
            if (editingUser === null) {
              refresh()
            } else {
              replaceUser(saved)
            }
          }}
        />
      ) : null}

      {roleUser ? (
        <UserRolesDialog
          user={roleUser}
          roles={roles}
          onOpenChange={(open) => {
            if (!open) setRoleUser(null)
          }}
          onSaved={replaceUser}
        />
      ) : null}

      <Dialog
        open={Boolean(detailUser)}
        onOpenChange={(open) => {
          if (!open) setDetailUser(null)
        }}
      >
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{detailUser?.full_name}</DialogTitle>
            <DialogDescription>
              Farm account, verification, access, and sign-in information.
            </DialogDescription>
          </DialogHeader>

          {detailUser ? (
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                ["Username", detailUser.username],
                ["Email", detailUser.email ?? "Not recorded"],
                ["Telephone", detailUser.telephone ?? "Not recorded"],
                ["Created", formatDate(detailUser.created_at)],
                ["Last login", formatDate(detailUser.last_login_at)],
                [
                  "Verification",
                  detailUser.is_verified ? "Verified" : "Not verified",
                ],
                [
                  "Password requirement",
                  detailUser.must_change_password
                    ? "Change required"
                    : "No forced change",
                ],
                [
                  "Activity",
                  detailUser.is_active ? "Active" : "Inactive",
                ],
              ].map(([label, value]) => (
                <div key={label} className="rounded-xl border p-3">
                  <p className="text-xs text-muted-foreground">{label}</p>
                  <p className="mt-1 font-medium">{value}</p>
                </div>
              ))}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      <Card className="rounded-2xl border-dashed">
        <CardContent className="flex items-start gap-3 p-4 text-sm text-muted-foreground">
          <RefreshCw className="mt-0.5 size-5 shrink-0 text-primary" />
          <p>
            The current backend exposes role listing and assignment, but
            not role creation or role editing. Role definitions are therefore
            displayed as read-only instead of presenting unsupported controls.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
