"use client"

import { useState } from "react"
import { Home, LoaderCircle } from "lucide-react"
import { toast } from "sonner"

import {
  FormField,
  NativeSelect,
  Textarea,
} from "@/components/operational/form-controls"
import { Button } from "@/components/ui/button"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Input } from "@/components/ui/input"
import { browserApiRequest } from "@/lib/api/browser"
import type {
  PoultryHouse,
  PoultryHouseCreate,
  PoultryHouseStatus,
  PoultryHouseUpdate,
} from "@/lib/api/operations"

interface HouseFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  house?: PoultryHouse | null
  onSaved: (house: PoultryHouse) => void
}

export function HouseFormDialog({
  open,
  onOpenChange,
  house,
  onSaved,
}: HouseFormDialogProps) {
  const editing = Boolean(house)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)
    const capacity = Number(form.get("capacity"))

    if (!Number.isInteger(capacity) || capacity <= 0) {
      toast.error(
        "House capacity must be a whole number greater than zero.",
      )
      return
    }

    const payload: PoultryHouseCreate = {
      house_code: String(
        form.get("house_code") ?? "",
      ).trim(),
      name: String(form.get("name") ?? "").trim(),
      capacity,
      location:
        String(form.get("location") ?? "").trim() || null,
      description:
        String(form.get("description") ?? "").trim() ||
        null,
      status: String(
        form.get("status") ?? "ACTIVE",
      ) as PoultryHouseStatus,
    }

    if (
      payload.house_code.length < 2 ||
      payload.name.length < 2
    ) {
      toast.error(
        "House code and name must contain at least two characters.",
      )
      return
    }

    setSaving(true)

    try {
      const saved = editing && house
        ? await browserApiRequest<PoultryHouse>(
            `/houses/${house.id}`,
            {
              method: "PATCH",
              body: JSON.stringify(
                payload satisfies PoultryHouseUpdate,
              ),
            },
          )
        : await browserApiRequest<PoultryHouse>(
            "/houses",
            {
              method: "POST",
              body: JSON.stringify(payload),
            },
          )

      toast.success(
        editing
          ? "Poultry house updated."
          : "Poultry house registered.",
      )
      onSaved(saved)
      onOpenChange(false)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The poultry house could not be saved.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-3xl sm:max-w-xl">
        <DialogHeader>
          <div className="mb-1 grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
            <Home className="size-5" />
          </div>
          <DialogTitle>
            {editing
              ? "Edit poultry house"
              : "Register a poultry house"}
          </DialogTitle>
          <DialogDescription>
            Keep house identity, capacity, location, and
            operational status accurate.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="House code"
              htmlFor="house_code"
              required
            >
              <Input
                id="house_code"
                name="house_code"
                defaultValue={house?.house_code ?? ""}
                minLength={2}
                maxLength={30}
                placeholder="H-01"
                required
              />
            </FormField>

            <FormField label="House name" htmlFor="name" required>
              <Input
                id="name"
                name="name"
                defaultValue={house?.name ?? ""}
                minLength={2}
                maxLength={100}
                placeholder="Main Layer House"
                required
              />
            </FormField>

            <FormField
              label="Bird capacity"
              htmlFor="capacity"
              required
            >
              <Input
                id="capacity"
                name="capacity"
                type="number"
                min={1}
                step={1}
                defaultValue={house?.capacity ?? ""}
                placeholder="5000"
                required
              />
            </FormField>

            <FormField
              label="Operational status"
              htmlFor="status"
            >
              <NativeSelect
                id="status"
                name="status"
                defaultValue={house?.status ?? "ACTIVE"}
              >
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="UNDER_MAINTENANCE">
                  Under maintenance
                </option>
                <option value="CLOSED">Closed</option>
              </NativeSelect>
            </FormField>

            <FormField
              label="Location"
              htmlFor="location"
              className="sm:col-span-2"
            >
              <Input
                id="location"
                name="location"
                defaultValue={house?.location ?? ""}
                maxLength={255}
                placeholder="Eastern block, next to feed store"
              />
            </FormField>

            <FormField
              label="Description"
              htmlFor="description"
              className="sm:col-span-2"
            >
              <Textarea
                id="description"
                name="description"
                defaultValue={house?.description ?? ""}
                placeholder="Ventilation, equipment, floor system, or other management notes…"
              />
            </FormField>
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
              {saving ? (
                <LoaderCircle className="size-4 animate-spin" />
              ) : (
                <Home className="size-4" />
              )}
              {editing ? "Save changes" : "Register house"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
