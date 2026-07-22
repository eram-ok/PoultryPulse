"use client"

import { useMemo, useState } from "react"
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
import { formatMoney, todayIso } from "@/lib/commercial/format"
import type {
  PaymentMethod,
  PaymentPayload,
  ReturnPayload,
  Sale,
  SalePayment,
  SaleReturn,
} from "@/lib/commercial/types"

export function ReasonActionDialog({
  open,
  title,
  description,
  confirmLabel,
  destructive,
  onOpenChange,
  onConfirm,
}: {
  open: boolean
  title: string
  description: string
  confirmLabel: string
  destructive?: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: (reason: string) => Promise<void>
}) {
  const [reason, setReason] = useState("")
  const [saving, setSaving] = useState(false)

  async function submit() {
    if (reason.trim().length < 5) {
      toast.error("Enter a reason of at least five characters.")
      return
    }

    setSaving(true)
    try {
      await onConfirm(reason.trim())
      onOpenChange(false)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <Label htmlFor="action-reason">Reason</Label>
          <Textarea
            id="action-reason"
            value={reason}
            onChange={(event) => setReason(event.target.value)}
            rows={4}
            placeholder="Explain why this action is required..."
          />
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Keep record
          </Button>
          <Button
            variant={destructive ? "destructive" : "default"}
            onClick={submit}
            disabled={saving}
          >
            {saving ? "Working..." : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function PaymentDialog({
  open,
  sales,
  initialSale,
  currency,
  onOpenChange,
  onSaved,
}: {
  open: boolean
  sales: Sale[]
  initialSale: Sale | null
  currency: string
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const eligibleSales = useMemo(
    () =>
      sales.filter(
        (sale) =>
          sale.is_confirmed &&
          !sale.is_cancelled &&
          Number(sale.balance_due) > 0,
      ),
    [sales],
  )
  const defaultSale =
    initialSale && eligibleSales.some((sale) => sale.id === initialSale.id)
      ? initialSale
      : eligibleSales[0] ?? null

  const [saleId, setSaleId] = useState(defaultSale?.id ?? "")
  const [paymentDate, setPaymentDate] = useState(todayIso())
  const [amount, setAmount] = useState(defaultSale?.balance_due ?? "")
  const [method, setMethod] = useState<PaymentMethod>("CASH")
  const [reference, setReference] = useState("")
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)

  const selectedSale = eligibleSales.find((sale) => sale.id === saleId)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!saleId || Number(amount) <= 0) {
      toast.error("Select an invoice and enter a valid amount.")
      return
    }

    const payload: PaymentPayload = {
      sale_id: saleId,
      payment_date: paymentDate,
      amount,
      method,
      reference_number: reference.trim() || null,
      notes: notes.trim() || null,
    }

    setSaving(true)
    try {
      await browserApiRequest<SalePayment>("/sales/payments", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      toast.success("Payment recorded.")
      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Payment could not be recorded.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Record customer payment</DialogTitle>
          <DialogDescription>
            Post money received against a confirmed invoice.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Invoice</Label>
            <Select value={saleId} onValueChange={setSaleId}>
              <SelectTrigger>
                <SelectValue placeholder="Select invoice" />
              </SelectTrigger>
              <SelectContent>
                {eligibleSales.map((sale) => (
                  <SelectItem key={sale.id} value={sale.id}>
                    {sale.invoice_number} · {sale.customer_name} ·{" "}
                    {formatMoney(sale.balance_due, currency)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {eligibleSales.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                No confirmed invoice currently has an outstanding balance.
              </p>
            ) : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="payment-date">Payment date</Label>
              <Input
                id="payment-date"
                type="date"
                value={paymentDate}
                onChange={(event) => setPaymentDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="payment-amount">Amount</Label>
              <Input
                id="payment-amount"
                type="number"
                min="0.01"
                step="0.01"
                max={selectedSale?.balance_due}
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Method</Label>
              <Select
                value={method}
                onValueChange={(value) =>
                  setMethod(value as PaymentMethod)
                }
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="CASH">Cash</SelectItem>
                  <SelectItem value="MOBILE_MONEY">Mobile money</SelectItem>
                  <SelectItem value="BANK_TRANSFER">Bank transfer</SelectItem>
                  <SelectItem value="CHEQUE">Cheque</SelectItem>
                  <SelectItem value="OTHER">Other</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="payment-reference">Reference</Label>
              <Input
                id="payment-reference"
                value={reference}
                onChange={(event) => setReference(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="payment-notes">Notes</Label>
            <Textarea
              id="payment-notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
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
            <Button
              type="submit"
              disabled={saving || eligibleSales.length === 0}
            >
              {saving ? "Posting..." : "Record payment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function ReturnDialog({
  open,
  sales,
  initialSale,
  onOpenChange,
  onSaved,
}: {
  open: boolean
  sales: Sale[]
  initialSale: Sale | null
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const eligibleSales = useMemo(
    () =>
      sales.filter(
        (sale) =>
          sale.is_confirmed &&
          !sale.is_cancelled &&
          sale.items.some(
            (item) => item.remaining_returnable_quantity > 0,
          ),
      ),
    [sales],
  )
  const defaultSale =
    initialSale && eligibleSales.some((sale) => sale.id === initialSale.id)
      ? initialSale
      : eligibleSales[0] ?? null

  const [saleId, setSaleId] = useState(defaultSale?.id ?? "")
  const [returnDate, setReturnDate] = useState(todayIso())
  const [reason, setReason] = useState("")
  const [notes, setNotes] = useState("")
  const [quantities, setQuantities] = useState<Record<string, number>>({})
  const [saving, setSaving] = useState(false)

  const selectedSale = eligibleSales.find((sale) => sale.id === saleId)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const items =
      selectedSale?.items
        .map((item) => ({
          sale_item_id: item.id,
          quantity: quantities[item.id] ?? 0,
          reason: null,
        }))
        .filter((item) => item.quantity > 0) ?? []

    if (!saleId || reason.trim().length < 5 || items.length === 0) {
      toast.error(
        "Select an invoice, enter a reason, and choose returned quantities.",
      )
      return
    }

    const payload: ReturnPayload = {
      sale_id: saleId,
      return_date: returnDate,
      reason: reason.trim(),
      notes: notes.trim() || null,
      items,
    }

    setSaving(true)
    try {
      await browserApiRequest<SaleReturn>("/sales/returns", {
        method: "POST",
        body: JSON.stringify(payload),
      })
      toast.success("Sale return posted and inventory restored.")
      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Return could not be posted.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Record sale return</DialogTitle>
          <DialogDescription>
            Return eligible invoice items to egg inventory and update the
            customer ledger.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-5">
          <div className="space-y-2">
            <Label>Confirmed invoice</Label>
            <Select
              value={saleId}
              onValueChange={(value) => {
                setSaleId(value)
                setQuantities({})
              }}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select invoice" />
              </SelectTrigger>
              <SelectContent>
                {eligibleSales.map((sale) => (
                  <SelectItem key={sale.id} value={sale.id}>
                    {sale.invoice_number} · {sale.customer_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {selectedSale ? (
            <div className="space-y-3 rounded-2xl border p-4">
              <p className="text-sm font-semibold">Return quantities</p>
              {selectedSale.items.map((item) => (
                <div
                  key={item.id}
                  className="grid gap-3 rounded-xl bg-muted/40 p-3 sm:grid-cols-[1fr_140px]"
                >
                  <div>
                    <p className="text-sm font-medium">
                      {item.egg_grade} · {item.unit}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Up to {item.remaining_returnable_quantity} units
                    </p>
                  </div>
                  <Input
                    type="number"
                    min="0"
                    max={item.remaining_returnable_quantity}
                    value={quantities[item.id] ?? 0}
                    onChange={(event) =>
                      setQuantities((current) => ({
                        ...current,
                        [item.id]: Math.max(
                          0,
                          Math.min(
                            item.remaining_returnable_quantity,
                            Number(event.target.value) || 0,
                          ),
                        ),
                      }))
                    }
                  />
                </div>
              ))}
            </div>
          ) : null}

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="return-date">Return date</Label>
              <Input
                id="return-date"
                type="date"
                value={returnDate}
                onChange={(event) => setReturnDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="return-reason">Reason</Label>
              <Input
                id="return-reason"
                value={reason}
                onChange={(event) => setReason(event.target.value)}
                placeholder="Customer returned damaged trays"
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="return-notes">Notes</Label>
            <Textarea
              id="return-notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
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
            <Button
              type="submit"
              disabled={saving || eligibleSales.length === 0}
            >
              {saving ? "Posting..." : "Post return"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
