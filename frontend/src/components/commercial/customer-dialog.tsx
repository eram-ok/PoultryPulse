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
  Customer,
  CustomerCreatePayload,
  CustomerStatus,
} from "@/lib/commercial/types"

const emptyForm: CustomerCreatePayload = {
  customer_code: "",
  name: "",
  phone_number: null,
  email: null,
  address: null,
  tax_number: null,
  contact_person: null,
  credit_limit: "0",
  opening_balance: "0",
  notes: null,
}

function customerForm(customer: Customer | null): CustomerCreatePayload {
  if (!customer) return emptyForm

  return {
    customer_code: customer.customer_code,
    name: customer.name,
    phone_number: customer.phone_number,
    email: customer.email,
    address: customer.address,
    tax_number: customer.tax_number,
    contact_person: customer.contact_person,
    credit_limit: customer.credit_limit,
    opening_balance: customer.opening_balance,
    notes: customer.notes,
  }
}

export function CustomerDialog({
  open,
  customer,
  onOpenChange,
  onSaved,
}: {
  open: boolean
  customer: Customer | null
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const [form, setForm] = useState<CustomerCreatePayload>(() =>
    customerForm(customer),
  )
  const [status, setStatus] = useState<CustomerStatus>(
    customer?.status ?? "ACTIVE",
  )
  const [saving, setSaving] = useState(false)

  function textValue(value: string): string | null {
    const trimmed = value.trim()
    return trimmed ? trimmed : null
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!form.customer_code.trim() || !form.name.trim()) {
      toast.error("Customer code and name are required.")
      return
    }

    setSaving(true)

    try {
      const payload = {
        ...form,
        customer_code: form.customer_code.trim(),
        name: form.name.trim(),
        phone_number: textValue(form.phone_number ?? ""),
        email: textValue(form.email ?? ""),
        address: textValue(form.address ?? ""),
        tax_number: textValue(form.tax_number ?? ""),
        contact_person: textValue(form.contact_person ?? ""),
        notes: textValue(form.notes ?? ""),
      }

      if (customer) {
        const updatePayload = {
          customer_code: payload.customer_code,
          name: payload.name,
          phone_number: payload.phone_number,
          email: payload.email,
          address: payload.address,
          tax_number: payload.tax_number,
          contact_person: payload.contact_person,
          credit_limit: payload.credit_limit,
          notes: payload.notes,
          status,
        }

        await browserApiRequest<Customer>(
          `/sales/customers/${customer.id}`,
          {
            method: "PATCH",
            body: JSON.stringify(updatePayload),
          },
        )
        toast.success("Customer updated.")
      } else {
        await browserApiRequest<Customer>("/sales/customers", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        toast.success("Customer created.")
      }

      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Customer could not be saved.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {customer ? "Edit customer" : "Add customer"}
          </DialogTitle>
          <DialogDescription>
            Maintain customer identity, credit limits, and account status.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="customer-code">Customer code</Label>
              <Input
                id="customer-code"
                value={form.customer_code}
                maxLength={40}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    customer_code: event.target.value,
                  }))
                }
                placeholder="CUS-001"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer-name">Customer name</Label>
              <Input
                id="customer-name"
                value={form.name}
                maxLength={180}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    name: event.target.value,
                  }))
                }
                placeholder="Mukono Retail Shop"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer-phone">Telephone</Label>
              <Input
                id="customer-phone"
                value={form.phone_number ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    phone_number: event.target.value,
                  }))
                }
                placeholder="+256..."
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="customer-email">Email</Label>
              <Input
                id="customer-email"
                type="email"
                value={form.email ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    email: event.target.value,
                  }))
                }
                placeholder="customer@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="contact-person">Contact person</Label>
              <Input
                id="contact-person"
                value={form.contact_person ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    contact_person: event.target.value,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="tax-number">Tax number</Label>
              <Input
                id="tax-number"
                value={form.tax_number ?? ""}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    tax_number: event.target.value,
                  }))
                }
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="credit-limit">Credit limit</Label>
              <Input
                id="credit-limit"
                type="number"
                min="0"
                step="0.01"
                value={form.credit_limit}
                onChange={(event) =>
                  setForm((current) => ({
                    ...current,
                    credit_limit: event.target.value,
                  }))
                }
              />
            </div>
            {!customer ? (
              <div className="space-y-2">
                <Label htmlFor="opening-balance">Opening balance</Label>
                <Input
                  id="opening-balance"
                  type="number"
                  min="0"
                  step="0.01"
                  value={form.opening_balance}
                  onChange={(event) =>
                    setForm((current) => ({
                      ...current,
                      opening_balance: event.target.value,
                    }))
                  }
                />
              </div>
            ) : (
              <div className="space-y-2">
                <Label>Account status</Label>
                <Select
                  value={status}
                  onValueChange={(value) =>
                    setStatus(value as CustomerStatus)
                  }
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ACTIVE">Active</SelectItem>
                    <SelectItem value="INACTIVE">Inactive</SelectItem>
                    <SelectItem value="BLOCKED">Blocked</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="customer-address">Address</Label>
            <Textarea
              id="customer-address"
              value={form.address ?? ""}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  address: event.target.value,
                }))
              }
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="customer-notes">Notes</Label>
            <Textarea
              id="customer-notes"
              value={form.notes ?? ""}
              onChange={(event) =>
                setForm((current) => ({
                  ...current,
                  notes: event.target.value,
                }))
              }
              rows={3}
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
                : customer
                  ? "Save changes"
                  : "Create customer"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
