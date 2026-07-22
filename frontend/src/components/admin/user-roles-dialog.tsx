"use client"

import { useMemo, useState } from "react"
import { ShieldCheck } from "lucide-react"
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
import { browserApiRequest } from "@/lib/api/browser"
import type {
  AdminRole,
  AdminUser,
} from "@/lib/admin/types"

export function UserRolesDialog({
  user,
  roles,
  onOpenChange,
  onSaved,
}: {
  user: AdminUser
  roles: AdminRole[]
  onOpenChange: (open: boolean) => void
  onSaved: (user: AdminUser) => void
}) {
  const availableRoles = useMemo(
    () => roles.filter((role) => role.is_active),
    [roles],
  )
  const originalIds = useMemo(
    () => user.roles.map((role) => role.id),
    [user.roles],
  )
  const [selectedIds, setSelectedIds] = useState<string[]>(originalIds)
  const [saving, setSaving] = useState(false)

  function toggle(roleId: string) {
    setSelectedIds((current) =>
      current.includes(roleId)
        ? current.filter((id) => id !== roleId)
        : [...current, roleId],
    )
  }

  async function save() {
    if (selectedIds.length === 0) {
      toast.error("A farm user must retain at least one role.")
      return
    }

    const toAssign = selectedIds.filter((id) => !originalIds.includes(id))
    const toRemove = originalIds.filter((id) => !selectedIds.includes(id))

    if (toAssign.length === 0 && toRemove.length === 0) {
      onOpenChange(false)
      return
    }

    setSaving(true)

    try {
      let updated = user

      for (const roleId of toAssign) {
        updated = await browserApiRequest<AdminUser>(
          `/users/${user.id}/roles/${roleId}`,
          { method: "POST" },
        )
      }

      for (const roleId of toRemove) {
        updated = await browserApiRequest<AdminUser>(
          `/users/${user.id}/roles/${roleId}`,
          { method: "DELETE" },
        )
      }

      toast.success("User roles updated.")
      onOpenChange(false)
      onSaved(updated)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Role assignments could not be updated.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Manage roles for {user.full_name}</DialogTitle>
          <DialogDescription>
            Assign active roles or remove roles that are no longer required.
            Every change is independently audited.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-3 sm:grid-cols-2">
          {availableRoles.map((role) => (
            <label
              key={role.id}
              className="flex cursor-pointer items-start gap-3 rounded-xl border p-4"
            >
              <Checkbox
                checked={selectedIds.includes(role.id)}
                onCheckedChange={() => toggle(role.id)}
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

        <DialogFooter>
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
          >
            Cancel
          </Button>
          <Button onClick={save} disabled={saving}>
            {saving ? "Updating..." : "Save role assignments"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
