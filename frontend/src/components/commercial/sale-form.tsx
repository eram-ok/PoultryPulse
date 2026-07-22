"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useMemo, useState } from "react"
import {
  ArrowLeft,
  Calculator,
  Plus,
  Save,
  Trash2,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import { CommercialPageHeader } from "@/components/commercial/commercial-ui"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { browserApiRequest } from "@/lib/api/browser"
import {
  formatMoney,
  numeric,
  todayIso,
} from "@/lib/commercial/format"
import type {
  Customer,
  EggGrade,
  EggSaleUnit,
  Paginated,
  Sale,
  SaleCreatePayload,
  SaleItemPayload,
  SalePaymentTerms,
} from "@/lib/commercial/types"

const newItem = (): SaleItemPayload => ({
  egg_grade: "LARGE",
  unit: "TRAY",
  eggs_per_unit: null,
  quantity: 1,
  unit_price: "0",
  notes: null,
})

export function SaleForm({
  saleId,
}: {
  saleId?: string
}) {
  const router = useRouter()
  const { session } = useAuth()
  const currency = session.farm.currency_code || "UGX"
  const [customers, setCustomers] = useState<Customer[]>([])
  const [customerId, setCustomerId] = useState("")
  const [saleDate, setSaleDate] = useState(todayIso())
  const [dueDate, setDueDate] = useState("")
  const [terms, setTerms] = useState<SalePaymentTerms>("CASH")
  const [discount, setDiscount] = useState("0")
  const [tax, setTax] = useState("0")
  const [notes, setNotes] = useState("")
  const [items, setItems] = useState<SaleItemPayload[]>([newItem()])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  const subtotal = useMemo(
    () =>
      items.reduce(
        (total, item) =>
          total + item.quantity * numeric(item.unit_price),
        0,
      ),
    [items],
  )
  const total = Math.max(
    0,
    subtotal - numeric(discount) + numeric(tax),
  )

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      try {
        const customerList = await browserApiRequest<Paginated<Customer>>(
          "/sales/customers?offset=0&limit=100&status=ACTIVE",
        )

        if (cancelled) return
        setCustomers(customerList.items)

        if (saleId) {
          const sale = await browserApiRequest<Sale>(
            `/sales/invoices/${saleId}`,
          )

          if (cancelled) return

          if (sale.status !== "DRAFT") {
            toast.error("Only draft invoices can be edited.")
            router.replace("/sales")
            return
          }

          setCustomerId(sale.customer_id)
          setSaleDate(sale.sale_date)
          setDueDate(sale.due_date ?? "")
          setTerms(sale.payment_terms)
          setDiscount(sale.discount_amount)
          setTax(sale.tax_amount)
          setNotes(sale.notes ?? "")
          setItems(
            sale.items.map((item) => ({
              egg_grade: item.egg_grade,
              unit: item.unit,
              eggs_per_unit: item.eggs_per_unit,
              quantity: item.quantity,
              unit_price: item.unit_price,
              notes: item.notes,
            })),
          )
        } else if (customerList.items[0]) {
          setCustomerId(customerList.items[0].id)
        }
      } catch (error) {
        toast.error(
          error instanceof Error
            ? error.message
            : "Sale form could not be loaded.",
        )
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    void load()
    return () => {
      cancelled = true
    }
  }, [saleId, router])

  function updateItem(
    index: number,
    patch: Partial<SaleItemPayload>,
  ) {
    setItems((current) =>
      current.map((item, itemIndex) =>
        itemIndex === index ? { ...item, ...patch } : item,
      ),
    )
  }

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!customerId || items.length === 0) {
      toast.error("Select a customer and add at least one item.")
      return
    }

    if (
      items.some(
        (item) =>
          item.quantity <= 0 || numeric(item.unit_price) < 0,
      )
    ) {
      toast.error("Every invoice line needs a valid quantity and price.")
      return
    }

    const payload: SaleCreatePayload = {
      customer_id: customerId,
      sale_date: saleDate,
      due_date: dueDate || null,
      payment_terms: terms,
      discount_amount: discount || "0",
      tax_amount: tax || "0",
      notes: notes.trim() || null,
      items: items.map((item) => ({
        ...item,
        eggs_per_unit:
          item.unit === "PIECE"
            ? 1
            : item.eggs_per_unit || null,
        notes: item.notes?.trim() || null,
      })),
    }

    setSaving(true)
    try {
      if (saleId) {
        await browserApiRequest<Sale>(
          `/sales/invoices/${saleId}`,
          {
            method: "PATCH",
            body: JSON.stringify({
              due_date: payload.due_date,
              payment_terms: payload.payment_terms,
              discount_amount: payload.discount_amount,
              tax_amount: payload.tax_amount,
              notes: payload.notes,
              items: payload.items,
            }),
          },
        )
        toast.success("Draft invoice updated.")
      } else {
        await browserApiRequest<Sale>("/sales/invoices", {
          method: "POST",
          body: JSON.stringify(payload),
        })
        toast.success("Draft invoice created.")
      }

      router.push("/sales")
      router.refresh()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Invoice could not be saved.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Commercial operations"
        title={saleId ? "Edit draft invoice" : "Create customer invoice"}
        description="Prepare egg-sale lines, payment terms, discounts, taxes, and due dates. Stock is deducted only after confirmation."
        actions={
          <Button asChild variant="outline" className="rounded-xl">
            <Link href="/sales">
              <ArrowLeft className="size-4" />
              Back to sales
            </Link>
          </Button>
        }
      />

      {loading ? (
        <Card className="rounded-2xl">
          <CardContent className="p-8 text-sm text-muted-foreground">
            Loading invoice form...
          </CardContent>
        </Card>
      ) : (
        <form onSubmit={submit} className="grid gap-6 xl:grid-cols-[1fr_360px]">
          <div className="space-y-6">
            <Card className="rounded-2xl">
              <CardHeader>
                <CardTitle className="text-base">Invoice details</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label>Customer</Label>
                  <Select
                    value={customerId}
                    onValueChange={setCustomerId}
                    disabled={Boolean(saleId)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {customers.map((customer) => (
                        <SelectItem key={customer.id} value={customer.id}>
                          {customer.customer_code} · {customer.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {customers.length === 0 ? (
                    <p className="text-xs text-destructive">
                      Add an active customer from the Sales workspace first.
                    </p>
                  ) : null}
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sale-date">Sale date</Label>
                  <Input
                    id="sale-date"
                    type="date"
                    value={saleDate}
                    onChange={(event) => setSaleDate(event.target.value)}
                    disabled={Boolean(saleId)}
                  />
                </div>

                <div className="space-y-2">
                  <Label>Payment terms</Label>
                  <Select
                    value={terms}
                    onValueChange={(value) =>
                      setTerms(value as SalePaymentTerms)
                    }
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CASH">Cash</SelectItem>
                      <SelectItem value="CREDIT">Credit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="due-date">Due date</Label>
                  <Input
                    id="due-date"
                    type="date"
                    value={dueDate}
                    onChange={(event) => setDueDate(event.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="sale-notes">Notes</Label>
                  <Input
                    id="sale-notes"
                    value={notes}
                    onChange={(event) => setNotes(event.target.value)}
                    placeholder="Optional invoice notes"
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="rounded-2xl">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">Invoice items</CardTitle>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="rounded-xl"
                  onClick={() =>
                    setItems((current) => [...current, newItem()])
                  }
                  disabled={items.length >= 10}
                >
                  <Plus className="size-4" />
                  Add line
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                {items.map((item, index) => (
                  <div
                    key={index}
                    className="grid gap-4 rounded-2xl border bg-muted/20 p-4 lg:grid-cols-[1fr_1fr_120px_150px_auto]"
                  >
                    <div className="space-y-2">
                      <Label>Egg grade</Label>
                      <Select
                        value={item.egg_grade}
                        onValueChange={(value) =>
                          updateItem(index, {
                            egg_grade: value as EggGrade,
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {["LARGE", "MEDIUM", "SMALL", "DAMAGED", "REJECTED"].map(
                            (grade) => (
                              <SelectItem key={grade} value={grade}>
                                {grade}
                              </SelectItem>
                            ),
                          )}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Unit</Label>
                      <Select
                        value={item.unit}
                        onValueChange={(value) =>
                          updateItem(index, {
                            unit: value as EggSaleUnit,
                            eggs_per_unit:
                              value === "PIECE" ? 1 : item.eggs_per_unit,
                          })
                        }
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="PIECE">Piece</SelectItem>
                          <SelectItem value="TRAY">Tray</SelectItem>
                          <SelectItem value="CRATE">Crate</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <Label>Quantity</Label>
                      <Input
                        type="number"
                        min="1"
                        value={item.quantity}
                        onChange={(event) =>
                          updateItem(index, {
                            quantity: Number(event.target.value) || 1,
                          })
                        }
                      />
                    </div>

                    <div className="space-y-2">
                      <Label>Unit price</Label>
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        value={item.unit_price}
                        onChange={(event) =>
                          updateItem(index, {
                            unit_price: event.target.value,
                          })
                        }
                      />
                    </div>

                    <div className="flex items-end">
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        className="rounded-xl text-destructive"
                        disabled={items.length === 1}
                        onClick={() =>
                          setItems((current) =>
                            current.filter(
                              (_, itemIndex) => itemIndex !== index,
                            ),
                          )
                        }
                        aria-label="Remove invoice line"
                      >
                        <Trash2 className="size-4" />
                      </Button>
                    </div>

                    {item.unit !== "PIECE" ? (
                      <div className="space-y-2 lg:col-span-2">
                        <Label>Eggs per {item.unit.toLowerCase()}</Label>
                        <Input
                          type="number"
                          min="1"
                          max="10000"
                          value={item.eggs_per_unit ?? ""}
                          onChange={(event) =>
                            updateItem(index, {
                              eggs_per_unit:
                                Number(event.target.value) || null,
                            })
                          }
                          placeholder={
                            item.unit === "TRAY"
                              ? "Uses farm tray setting when empty"
                              : "Enter eggs per crate"
                          }
                        />
                      </div>
                    ) : null}

                    <div className="rounded-xl bg-background px-3 py-2 text-sm lg:col-span-3">
                      Line total:{" "}
                      <strong>
                        {formatMoney(
                          item.quantity * numeric(item.unit_price),
                          currency,
                        )}
                      </strong>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6 xl:sticky xl:top-24 xl:self-start">
            <Card className="rounded-2xl">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Calculator className="size-4" />
                  Invoice totals
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subtotal</span>
                  <strong>{formatMoney(subtotal, currency)}</strong>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="discount">Discount amount</Label>
                  <Input
                    id="discount"
                    type="number"
                    min="0"
                    step="0.01"
                    value={discount}
                    onChange={(event) => setDiscount(event.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="tax">Tax amount</Label>
                  <Input
                    id="tax"
                    type="number"
                    min="0"
                    step="0.01"
                    value={tax}
                    onChange={(event) => setTax(event.target.value)}
                  />
                </div>
                <div className="border-t pt-4">
                  <div className="flex items-end justify-between">
                    <span className="text-sm text-muted-foreground">
                      Invoice total
                    </span>
                    <strong className="text-2xl">
                      {formatMoney(total, currency)}
                    </strong>
                  </div>
                </div>
                <Button
                  type="submit"
                  className="w-full rounded-xl"
                  disabled={saving || customers.length === 0}
                >
                  <Save className="size-4" />
                  {saving
                    ? "Saving..."
                    : saleId
                      ? "Update draft"
                      : "Save draft invoice"}
                </Button>
              </CardContent>
            </Card>
          </div>
        </form>
      )}
    </div>
  )
}
