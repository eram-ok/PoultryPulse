"use client"

import { useState } from "react"
import { Bird, LoaderCircle } from "lucide-react"
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
  FlockCreate,
  FlockProductionStage,
  FlockStatus,
  FlockUpdate,
  PoultryHouse,
} from "@/lib/api/operations"
import { todayIso } from "@/lib/operational/format"

interface FlockFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  flock?: Flock | null
  houses: PoultryHouse[]
  onSaved: (flock: Flock) => void
}

export function FlockFormDialog({
  open,
  onOpenChange,
  flock,
  houses,
  onSaved,
}: FlockFormDialogProps) {
  const editing = Boolean(flock)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    const form = new FormData(event.currentTarget)

    const common = {
      house_id: String(form.get("house_id") ?? ""),
      flock_code: String(form.get("flock_code") ?? "").trim(),
      name: String(form.get("name") ?? "").trim(),
      breed: String(form.get("breed") ?? "").trim(),
      purchase_cost: String(
        form.get("purchase_cost") ?? "0",
      ),
      production_stage: String(
        form.get("production_stage") ?? "GROWING",
      ) as FlockProductionStage,
      notes:
        String(form.get("notes") ?? "").trim() || null,
    }

    if (
      !common.house_id ||
      common.flock_code.length < 2 ||
      common.name.length < 2 ||
      common.breed.length < 2
    ) {
      toast.error(
        "Select a house and complete the required flock fields.",
      )
      return
    }

    setSaving(true)

    try {
      let saved: Flock

      if (editing && flock) {
        const payload: FlockUpdate = {
          ...common,
          status: String(
            form.get("status") ?? flock.status,
          ) as FlockStatus,
          supplier_id: flock.supplier_id,
        }

        saved = await browserApiRequest<Flock>(
          `/flocks/${flock.id}`,
          {
            method: "PATCH",
            body: JSON.stringify(payload),
          },
        )
      } else {
        const population = Number(
          form.get("initial_population"),
        )

        if (!Number.isInteger(population) || population <= 0) {
          toast.error(
            "Initial population must be a whole number greater than zero.",
          )
          setSaving(false)
          return
        }

        const payload: FlockCreate = {
          ...common,
          supplier_id: null,
          arrival_date:
            String(form.get("arrival_date") ?? "") ||
            todayIso(),
          hatch_date:
            String(form.get("hatch_date") ?? "") || null,
          age_at_arrival_days:
            String(form.get("age_at_arrival_days") ?? "")
              .trim()
              ? Number(form.get("age_at_arrival_days"))
              : null,
          initial_population: population,
        }

        saved = await browserApiRequest<Flock>(
          "/flocks",
          {
            method: "POST",
            body: JSON.stringify(payload),
          },
        )
      }

      toast.success(
        editing
          ? "Flock updated successfully."
          : "Flock registered successfully.",
      )
      onSaved(saved)
      onOpenChange(false)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The flock could not be saved.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto rounded-3xl sm:max-w-2xl">
        <DialogHeader>
          <div className="mb-1 grid size-10 place-items-center rounded-xl bg-primary/10 text-primary">
            <Bird className="size-5" />
          </div>
          <DialogTitle>
            {editing ? "Edit flock" : "Register a flock"}
          </DialogTitle>
          <DialogDescription>
            {editing
              ? "Update the placement, stage, status, and commercial details."
              : "Create the flock and its opening population transaction."}
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="House"
              htmlFor="house_id"
              required
              className="sm:col-span-2"
            >
              <NativeSelect
                id="house_id"
                name="house_id"
                defaultValue={flock?.house_id ?? ""}
                required
              >
                <option value="" disabled>
                  Select poultry house
                </option>
                {houses.map((house) => (
                  <option value={house.id} key={house.id}>
                    {house.house_code} — {house.name} (
                    {house.capacity.toLocaleString()} birds)
                  </option>
                ))}
              </NativeSelect>
            </FormField>

            <FormField
              label="Flock code"
              htmlFor="flock_code"
              required
            >
              <Input
                id="flock_code"
                name="flock_code"
                defaultValue={flock?.flock_code ?? ""}
                minLength={2}
                maxLength={30}
                placeholder="FLK-2026-01"
                required
              />
            </FormField>

            <FormField label="Flock name" htmlFor="name" required>
              <Input
                id="name"
                name="name"
                defaultValue={flock?.name ?? ""}
                minLength={2}
                maxLength={120}
                placeholder="Main layer flock"
                required
              />
            </FormField>

            <FormField label="Breed" htmlFor="breed" required>
              <Input
                id="breed"
                name="breed"
                defaultValue={flock?.breed ?? ""}
                minLength={2}
                maxLength={120}
                placeholder="ISA Brown"
                required
              />
            </FormField>

            <FormField
              label="Production stage"
              htmlFor="production_stage"
              required
            >
              <NativeSelect
                id="production_stage"
                name="production_stage"
                defaultValue={
                  flock?.production_stage ?? "GROWING"
                }
              >
                <option value="BROODING">Brooding</option>
                <option value="GROWING">Growing</option>
                <option value="POINT_OF_LAY">
                  Point of lay
                </option>
                <option value="LAYING">Laying</option>
                <option value="MOLTING">Molting</option>
                <option value="DEPLETED">Depleted</option>
                <option value="SOLD">Sold</option>
              </NativeSelect>
            </FormField>

            {!editing ? (
              <>
                <FormField
                  label="Arrival date"
                  htmlFor="arrival_date"
                  required
                >
                  <Input
                    id="arrival_date"
                    name="arrival_date"
                    type="date"
                    defaultValue={todayIso()}
                    required
                  />
                </FormField>

                <FormField
                  label="Initial population"
                  htmlFor="initial_population"
                  required
                >
                  <Input
                    id="initial_population"
                    name="initial_population"
                    type="number"
                    min={1}
                    step={1}
                    placeholder="1000"
                    required
                  />
                </FormField>

                <FormField
                  label="Hatch date"
                  htmlFor="hatch_date"
                >
                  <Input
                    id="hatch_date"
                    name="hatch_date"
                    type="date"
                  />
                </FormField>

                <FormField
                  label="Age at arrival (days)"
                  htmlFor="age_at_arrival_days"
                >
                  <Input
                    id="age_at_arrival_days"
                    name="age_at_arrival_days"
                    type="number"
                    min={0}
                    max={5000}
                    step={1}
                    placeholder="0"
                  />
                </FormField>
              </>
            ) : (
              <FormField
                label="Operational status"
                htmlFor="status"
              >
                <NativeSelect
                  id="status"
                  name="status"
                  defaultValue={flock?.status}
                >
                  <option value="PLANNED">Planned</option>
                  <option value="ACTIVE">Active</option>
                  <option value="SUSPENDED">Suspended</option>
                  <option value="DEPLETED">Depleted</option>
                  <option value="SOLD">Sold</option>
                  <option value="ARCHIVED">Archived</option>
                </NativeSelect>
              </FormField>
            )}

            <FormField
              label="Purchase cost"
              htmlFor="purchase_cost"
              hint="Total acquisition cost in the farm currency."
            >
              <Input
                id="purchase_cost"
                name="purchase_cost"
                type="number"
                min={0}
                step="0.01"
                defaultValue={flock?.purchase_cost ?? "0"}
              />
            </FormField>

            <FormField
              label="Notes"
              htmlFor="notes"
              className="sm:col-span-2"
            >
              <Textarea
                id="notes"
                name="notes"
                defaultValue={flock?.notes ?? ""}
                placeholder="Placement notes, supplier context, or management remarks…"
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
                <Bird className="size-4" />
              )}
              {editing ? "Save changes" : "Register flock"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
