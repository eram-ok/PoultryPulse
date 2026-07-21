"use client"

import { LoaderCircle, Scale } from "lucide-react"
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
  Flock,
  PopulationTransaction,
  PopulationTransactionType,
} from "@/lib/api/operations"
import { todayIso } from "@/lib/operational/format"
import { useState } from "react"

interface PopulationAdjustmentDialogProps {
  flock: Flock | null
  open: boolean
  onOpenChange: (open: boolean) => void
  onSaved: (transaction: PopulationTransaction) => void
}

export function PopulationAdjustmentDialog({
  flock,
  open,
  onOpenChange,
  onSaved,
}: PopulationAdjustmentDialogProps) {
  const [saving, setSaving] = useState(false)

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (!flock) {
      return
    }

    const form = new FormData(event.currentTarget)
    const quantity = Number(form.get("quantity"))

    if (!Number.isInteger(quantity) || quantity <= 0) {
      toast.error(
        "Population quantity must be a whole number greater than zero.",
      )
      return
    }

    setSaving(true)

    try {
      const transaction =
        await browserApiRequest<PopulationTransaction>(
          `/flocks/${flock.id}/population-transactions`,
          {
            method: "POST",
            body: JSON.stringify({
              transaction_date:
                String(form.get("transaction_date") ?? "") ||
                todayIso(),
              transaction_type: String(
                form.get("transaction_type"),
              ) as PopulationTransactionType,
              quantity,
              description:
                String(form.get("description") ?? "").trim() ||
                null,
            }),
          },
        )

      toast.success("Population movement recorded.")
      onSaved(transaction)
      onOpenChange(false)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The population movement could not be recorded.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl">
        <DialogHeader>
          <div className="mb-1 grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
            <Scale className="size-5" />
          </div>
          <DialogTitle>Adjust flock population</DialogTitle>
          <DialogDescription>
            Record a controlled population movement for{" "}
            {flock?.flock_code ?? "this flock"}. Mortality and
            culling should be recorded in Bird Losses.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <FormField
            label="Movement type"
            htmlFor="transaction_type"
            required
          >
            <NativeSelect
              id="transaction_type"
              name="transaction_type"
              defaultValue="ADJUSTMENT_IN"
            >
              <option value="TRANSFER_IN">Transfer in</option>
              <option value="TRANSFER_OUT">Transfer out</option>
              <option value="BIRD_SALE">Bird sale</option>
              <option value="ADJUSTMENT_IN">Adjustment in</option>
              <option value="ADJUSTMENT_OUT">
                Adjustment out
              </option>
            </NativeSelect>
          </FormField>

          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Transaction date"
              htmlFor="transaction_date"
              required
            >
              <Input
                id="transaction_date"
                name="transaction_date"
                type="date"
                defaultValue={todayIso()}
                required
              />
            </FormField>

            <FormField
              label="Quantity"
              htmlFor="quantity"
              required
            >
              <Input
                id="quantity"
                name="quantity"
                type="number"
                min={1}
                step={1}
                required
              />
            </FormField>
          </div>

          <FormField
            label="Description"
            htmlFor="description"
          >
            <Textarea
              id="description"
              name="description"
              placeholder="Reason, destination, source, or supporting reference…"
            />
          </FormField>

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
                <Scale className="size-4" />
              )}
              Record movement
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
