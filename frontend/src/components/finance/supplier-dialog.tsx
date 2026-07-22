"use client"

import { useState } from "react"
import { toast } from "sonner"

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
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { browserApiRequest } from "@/lib/api/browser"
import type {
  Supplier,
  SupplierType,
} from "@/lib/finance/types"

interface SupplierForm {
  supplier_code: string
  name: string
  supplier_type: SupplierType
  telephone: string
  email: string
  address: string
  notes: string
}

function initialForm(supplier: Supplier | null): SupplierForm {
  return {
    supplier_code: supplier?.supplier_code ?? "",
    name: supplier?.name ?? "",
    supplier_type: supplier?.supplier_type ?? "GENERAL_SUPPLIER",
    telephone: supplier?.telephone ?? "",
    email: supplier?.email ?? "",
    address: supplier?.address ?? "",
    notes: supplier?.notes ?? "",
  }
}

export function SupplierDialog({
  supplier,
  onOpenChange,
  onSaved,
}: {
  supplier: Supplier | null
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const [form, setForm] = useState<SupplierForm>(() =>
    initialForm(supplier),
  )
  const [saving, setSaving] = useState(false)

  function optional(value: string): string | null {
    const trimmed = value.trim()
    return trimmed || null
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (form.supplier_code.trim().length < 2 || form.name.trim().length < 2) {
      toast.error("Supplier code and name must contain at least two characters.")
      return
    }

    const payload = {
      supplier_code: form.supplier_code.trim(),
      name: form.name.trim(),
      supplier_type: form.supplier_type,
      telephone: optional(form.telephone),
      email: optional(form.email),
      address: optional(form.address),
      notes: optional(form.notes),
    }

    setSaving(true)

    try {
      if (supplier) {
        await browserApiRequest<Supplier>(
          `/suppliers/${supplier.id}`,
          {
            method: "PATCH",
            body: JSON.stringify(payload),
          },
        )
        toast.success("Supplier updated.")
      } else {
        await browserApiRequest<Supplier>("/suppliers", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        toast.success("Supplier registered.")
      }

      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Supplier could not be saved.",
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
            {supplier ? "Edit supplier" : "Register supplier"}
          </DialogTitle>
          <DialogDescription>
            Maintain supplier identity, classification, and contact details.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="supplier-code">Supplier code</Label>
              <Input
                id="supplier-code"
                value={form.supplier_code}
                maxLength={30}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    supplier_code: event.target.value,
                  }))
                }
                placeholder="SUP-001"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="supplier-name">Supplier name</Label>
              <Input
                id="supplier-name"
                value={form.name}
                maxLength={150}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    name: event.target.value,
                  }))
                }
                placeholder="Mukono Farm Supplies"
                required
              />
            </div>

            <div className="space-y-2">
              <Label>Supplier type</Label>
              <Select
                value={form.supplier_type}
                onValueChange={(value) =>
                  setForm((current) => ({
                    ...current,
                    supplier_type: value as SupplierType,
                  }))
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="BIRD_SUPPLIER">Bird supplier</SelectItem>
                  <SelectItem value="FEED_SUPPLIER">Feed supplier</SelectItem>
                  <SelectItem value="MEDICINE_SUPPLIER">
                    Medicine supplier
                  </SelectItem>
                  <SelectItem value="EQUIPMENT_SUPPLIER">
                    Equipment supplier
                  </SelectItem>
                  <SelectItem value="GENERAL_SUPPLIER">
                    General supplier
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="supplier-phone">Telephone</Label>
              <Input
                id="supplier-phone"
                value={form.telephone}
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
              <Label htmlFor="supplier-email">Email</Label>
              <Input
                id="supplier-email"
                type="email"
                value={form.email}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    email: event.target.value,
                  }))
                }
                placeholder="supplier@example.com"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="supplier-address">Address</Label>
              <Input
                id="supplier-address"
                value={form.address}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    address: event.target.value,
                  }))
                }
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="supplier-notes">Notes</Label>
            <Textarea
              id="supplier-notes"
              rows={3}
              value={form.notes}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
            />
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
              {saving
                ? "Saving..."
                : supplier
                  ? "Save changes"
                  : "Register supplier"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
