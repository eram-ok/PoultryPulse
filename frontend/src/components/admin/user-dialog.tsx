"use client"

import { useMemo, useState } from "react"
import { Eye, EyeOff, ShieldCheck } from "lucide-react"
import { toast } from "sonner"

import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
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
import type {
  AdminRole,
  AdminUser,
  AdminUserCreate,
  AdminUserUpdate,
} from "@/lib/admin/types"

function optional(value: string): string | null {
  const trimmed = value.trim()
  return trimmed || null
}

function passwordProblem(password: string): string | null {
  if (password.length < 12) {
    return "Password must contain at least 12 characters."
  }
  if (!/[A-Z]/.test(password)) {
    return "Password must contain an uppercase letter."
  }
  if (!/[a-z]/.test(password)) {
    return "Password must contain a lowercase letter."
  }
  if (!/\d/.test(password)) {
    return "Password must contain a number."
  }
  if (!/[^A-Za-z0-9]/.test(password)) {
    return "Password must contain a special character."
  }
  return null
}

export function UserDialog({
  user,
  roles,
  onOpenChange,
  onSaved,
}: {
  user: AdminUser | null
  roles: AdminRole[]
  onOpenChange: (open: boolean) => void
  onSaved: (user: AdminUser) => void
}) {
  const activeRoles = useMemo(
    () => roles.filter((role) => role.is_active),
    [roles],
  )
  const [username, setUsername] = useState(user?.username ?? "")
  const [firstName, setFirstName] = useState(user?.first_name ?? "")
  const [lastName, setLastName] = useState(user?.last_name ?? "")
  const [email, setEmail] = useState(user?.email ?? "")
  const [telephone, setTelephone] = useState(user?.telephone ?? "")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>(
    user?.roles.map((role) => role.id) ?? [],
  )
  const [verified, setVerified] = useState(user?.is_verified ?? false)
  const [mustChangePassword, setMustChangePassword] = useState(
    user?.must_change_password ?? true,
  )
  const [saving, setSaving] = useState(false)

  function toggleRole(roleId: string) {
    setSelectedRoleIds((current) =>
      current.includes(roleId)
        ? current.filter((id) => id !== roleId)
        : [...current, roleId],
    )
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (firstName.trim().length < 1 || lastName.trim().length < 1) {
      toast.error("First and last names are required.")
      return
    }

    if (!user) {
      if (username.trim().length < 3) {
        toast.error("Username must contain at least three characters.")
        return
      }

      const problem = passwordProblem(password)
      if (problem) {
        toast.error(problem)
        return
      }

      if (selectedRoleIds.length === 0) {
        toast.error("Assign at least one active role.")
        return
      }
    }

    setSaving(true)

    try {
      let saved: AdminUser

      if (user) {
        const payload: AdminUserUpdate = {
          email: optional(email),
          telephone: optional(telephone),
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          is_verified: verified,
          must_change_password: mustChangePassword,
        }

        saved = await browserApiRequest<AdminUser>(
          `/users/${user.id}`,
          {
            method: "PATCH",
            body: JSON.stringify(payload),
          },
        )
        toast.success("User profile updated.")
      } else {
        const payload: AdminUserCreate = {
          username: username.trim(),
          email: optional(email),
          telephone: optional(telephone),
          password,
          first_name: firstName.trim(),
          last_name: lastName.trim(),
          role_ids: selectedRoleIds,
          must_change_password: mustChangePassword,
        }

        saved = await browserApiRequest<AdminUser>("/users", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        toast.success("Farm user created.")
      }

      onOpenChange(false)
      onSaved(saved)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The user could not be saved.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {user ? "Edit farm user" : "Create farm user"}
          </DialogTitle>
          <DialogDescription>
            {user
              ? "Update contact, verification, and password-change requirements."
              : "Create a secure account and assign at least one farm role."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            {!user ? (
              <div className="space-y-2 sm:col-span-2">
                <Label htmlFor="admin-username">Username</Label>
                <Input
                  id="admin-username"
                  value={username}
                  minLength={3}
                  maxLength={50}
                  autoComplete="off"
                  onChange={(event) => setUsername(event.target.value)}
                  placeholder="farm.manager"
                  required
                />
              </div>
            ) : (
              <div className="rounded-xl border bg-muted/30 p-4 sm:col-span-2">
                <p className="text-xs text-muted-foreground">Username</p>
                <p className="mt-1 font-semibold">{user.username}</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Usernames cannot be changed by the current backend contract.
                </p>
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="admin-first-name">First name</Label>
              <Input
                id="admin-first-name"
                value={firstName}
                maxLength={100}
                onChange={(event) => setFirstName(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-last-name">Last name</Label>
              <Input
                id="admin-last-name"
                value={lastName}
                maxLength={100}
                onChange={(event) => setLastName(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-email">Email</Label>
              <Input
                id="admin-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="name@example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-telephone">Telephone</Label>
              <Input
                id="admin-telephone"
                value={telephone}
                maxLength={30}
                onChange={(event) => setTelephone(event.target.value)}
                placeholder="+256..."
              />
            </div>
          </div>

          {!user ? (
            <>
              <div className="space-y-2">
                <Label htmlFor="admin-password">Temporary password</Label>
                <div className="relative">
                  <Input
                    id="admin-password"
                    type={showPassword ? "text" : "password"}
                    value={password}
                    minLength={12}
                    maxLength={128}
                    autoComplete="new-password"
                    className="pr-11"
                    onChange={(event) => setPassword(event.target.value)}
                    required
                  />
                  <Button
                    type="button"
                    size="icon"
                    variant="ghost"
                    className="absolute right-1 top-1 size-8"
                    onClick={() => setShowPassword((current) => !current)}
                    aria-label={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? (
                      <EyeOff className="size-4" />
                    ) : (
                      <Eye className="size-4" />
                    )}
                  </Button>
                </div>
                <p className="text-xs leading-5 text-muted-foreground">
                  Use at least 12 characters with uppercase, lowercase,
                  number, and special-character content.
                </p>
              </div>

              <div className="space-y-3">
                <div>
                  <Label>Initial roles</Label>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Roles are defined by the backend and may be assigned here.
                  </p>
                </div>

                {activeRoles.length === 0 ? (
                  <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
                    No active roles are available. A user cannot be created.
                  </div>
                ) : (
                  <div className="grid gap-3 sm:grid-cols-2">
                    {activeRoles.map((role) => (
                      <label
                        key={role.id}
                        className="flex cursor-pointer items-start gap-3 rounded-xl border p-3"
                      >
                        <Checkbox
                          checked={selectedRoleIds.includes(role.id)}
                          onCheckedChange={() => toggleRole(role.id)}
                        />
                        <span>
                          <span className="flex items-center gap-2 font-medium">
                            {role.name}
                            {role.is_system_role ? (
                              <ShieldCheck className="size-3.5 text-primary" />
                            ) : null}
                          </span>
                          <span className="mt-1 block text-xs leading-5 text-muted-foreground">
                            {role.description ?? `${role.permissions.length} permissions`}
                          </span>
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="rounded-xl border bg-muted/20 p-4">
              <p className="text-sm font-medium">Role management</p>
              <p className="mt-1 text-xs leading-5 text-muted-foreground">
                Use the separate Manage roles action so profile changes and
                access changes remain independently audited.
              </p>
            </div>
          )}

          <div className="space-y-3">
            {user ? (
              <label className="flex cursor-pointer items-start gap-3 rounded-xl border p-3">
                <Checkbox
                  checked={verified}
                  onCheckedChange={(checked) => setVerified(checked === true)}
                />
                <span>
                  <span className="font-medium">Verified account</span>
                  <span className="mt-1 block text-xs text-muted-foreground">
                    Mark the account as administratively verified.
                  </span>
                </span>
              </label>
            ) : null}

            <label className="flex cursor-pointer items-start gap-3 rounded-xl border p-3">
              <Checkbox
                checked={mustChangePassword}
                onCheckedChange={(checked) =>
                  setMustChangePassword(checked === true)
                }
              />
              <span>
                <span className="font-medium">
                  Require password change at next sign-in
                </span>
                <span className="mt-1 block text-xs text-muted-foreground">
                  Recommended for every newly issued temporary password.
                </span>
              </span>
            </label>
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={
                saving ||
                (!user && activeRoles.length === 0)
              }
            >
              {saving
                ? "Saving..."
                : user
                  ? "Save profile"
                  : "Create user"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
