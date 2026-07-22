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
import { todayIso } from "@/lib/commercial/format"
import type {
  CashFlowDirection,
  CashLedgerEntry,
  Expense,
  ExpenseCategory,
  ExpenseCategoryKind,
  FinancePaymentMethod,
  Supplier,
  SupplierBill,
  SupplierPayment,
} from "@/lib/finance/types"

export function ReasonDialog({
  title,
  description,
  confirmLabel,
  onOpenChange,
  onConfirm,
}: {
  title: string
  description: string
  confirmLabel: string
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
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <Label htmlFor="finance-reason">Reason</Label>
          <Textarea
            id="finance-reason"
            rows={4}
            value={reason}
            onChange={(event) => setReason(event.target.value)}
          />
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Keep record
          </Button>
          <Button
            variant="destructive"
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

export function CategoryDialog({
  category,
  onOpenChange,
  onSaved,
}: {
  category: ExpenseCategory | null
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const [code, setCode] = useState(category?.category_code ?? "")
  const [name, setName] = useState(category?.name ?? "")
  const [kind, setKind] = useState<ExpenseCategoryKind>(
    category?.kind ?? "OTHER",
  )
  const [description, setDescription] = useState(
    category?.description ?? "",
  )
  const [active, setActive] = useState(category?.is_active ?? true)
  const [saving, setSaving] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (code.trim().length < 2 || name.trim().length < 2) {
      toast.error("Category code and name are required.")
      return
    }

    const payload = {
      category_code: code.trim(),
      name: name.trim(),
      kind,
      description: description.trim() || null,
      ...(category ? { is_active: active } : {}),
    }

    setSaving(true)

    try {
      if (category) {
        await browserApiRequest<ExpenseCategory>(
          `/finance/expense-categories/${category.id}`,
          {
            method: "PATCH",
            body: JSON.stringify(payload),
          },
        )
        toast.success("Expense category updated.")
      } else {
        await browserApiRequest<ExpenseCategory>(
          "/finance/expense-categories",
          {
            method: "POST",
            body: JSON.stringify(payload),
          },
        )
        toast.success("Expense category created.")
      }

      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Expense category could not be saved.",
      )
    } finally {
      setSaving(false)
    }
  }

  const kinds: ExpenseCategoryKind[] = [
    "FEED",
    "VETERINARY",
    "LABOUR",
    "UTILITIES",
    "TRANSPORT",
    "EQUIPMENT",
    "MAINTENANCE",
    "HOUSING",
    "ADMINISTRATION",
    "BIOSECURITY",
    "OTHER",
  ]

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            {category ? "Edit expense category" : "Add expense category"}
          </DialogTitle>
          <DialogDescription>
            Classify operating expenses for finance reporting.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="category-code">Category code</Label>
              <Input
                id="category-code"
                value={code}
                onChange={(event) => setCode(event.target.value)}
                maxLength={40}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="category-name">Category name</Label>
              <Input
                id="category-name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                maxLength={150}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label>Category kind</Label>
            <Select
              value={kind}
              onValueChange={(value) =>
                setKind(value as ExpenseCategoryKind)
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {kinds.map((value) => (
                  <SelectItem key={value} value={value}>
                    {value.replaceAll("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {category ? (
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={active ? "ACTIVE" : "INACTIVE"}
                onValueChange={(value) => setActive(value === "ACTIVE")}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ACTIVE">Active</SelectItem>
                  <SelectItem value="INACTIVE">Inactive</SelectItem>
                </SelectContent>
              </Select>
            </div>
          ) : null}

          <div className="space-y-2">
            <Label htmlFor="category-description">Description</Label>
            <Textarea
              id="category-description"
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
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
              {saving ? "Saving..." : "Save category"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function ExpenseDialog({
  categories,
  suppliers,
  onOpenChange,
  onSaved,
}: {
  categories: ExpenseCategory[]
  suppliers: Supplier[]
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const activeCategories = categories.filter((item) => item.is_active)
  const activeSuppliers = suppliers.filter((item) => item.is_active)

  const [categoryId, setCategoryId] = useState(
    activeCategories[0]?.id ?? "",
  )
  const [supplierId, setSupplierId] = useState("NONE")
  const [expenseDate, setExpenseDate] = useState(todayIso())
  const [description, setDescription] = useState("")
  const [amount, setAmount] = useState("")
  const [method, setMethod] =
    useState<FinancePaymentMethod>("CASH")
  const [reference, setReference] = useState("")
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!categoryId || description.trim().length < 3 || Number(amount) <= 0) {
      toast.error("Select a category and enter a valid expense.")
      return
    }

    setSaving(true)

    try {
      await browserApiRequest<Expense>("/finance/expenses", {
        method: "POST",
        body: JSON.stringify({
          category_id: categoryId,
          supplier_id: supplierId === "NONE" ? null : supplierId,
          expense_date: expenseDate,
          description: description.trim(),
          amount,
          payment_method: method,
          reference_number: reference.trim() || null,
          notes: notes.trim() || null,
        }),
      })

      toast.success("Expense posted to the cash ledger.")
      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Expense could not be recorded.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Record operating expense</DialogTitle>
          <DialogDescription>
            A posted expense immediately creates a cash-ledger outflow.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Expense category</Label>
            <Select value={categoryId} onValueChange={setCategoryId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {activeCategories.map((category) => (
                  <SelectItem key={category.id} value={category.id}>
                    {category.category_code} · {category.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {activeCategories.length === 0 ? (
              <p className="text-xs text-destructive">
                Create an active expense category first.
              </p>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label>Supplier (optional)</Label>
            <Select value={supplierId} onValueChange={setSupplierId}>
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="NONE">No supplier</SelectItem>
                {activeSuppliers.map((supplier) => (
                  <SelectItem key={supplier.id} value={supplier.id}>
                    {supplier.supplier_code} · {supplier.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="expense-date">Expense date</Label>
              <Input
                id="expense-date"
                type="date"
                value={expenseDate}
                onChange={(event) => setExpenseDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expense-amount">Amount</Label>
              <Input
                id="expense-amount"
                type="number"
                min="0.01"
                step="0.01"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="expense-description">Description</Label>
            <Input
              id="expense-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={255}
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Payment method</Label>
              <PaymentMethodSelect
                value={method}
                onChange={setMethod}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="expense-reference">Reference</Label>
              <Input
                id="expense-reference"
                value={reference}
                onChange={(event) => setReference(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="expense-notes">Notes</Label>
            <Textarea
              id="expense-notes"
              rows={3}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
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
              disabled={saving || activeCategories.length === 0}
            >
              {saving ? "Posting..." : "Post expense"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function BillDialog({
  suppliers,
  onOpenChange,
  onSaved,
}: {
  suppliers: Supplier[]
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const activeSuppliers = suppliers.filter((item) => item.is_active)

  const [supplierId, setSupplierId] = useState(
    activeSuppliers[0]?.id ?? "",
  )
  const [invoiceNumber, setInvoiceNumber] = useState("")
  const [billDate, setBillDate] = useState(todayIso())
  const [dueDate, setDueDate] = useState("")
  const [description, setDescription] = useState("")
  const [subtotal, setSubtotal] = useState("")
  const [tax, setTax] = useState("0")
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!supplierId || description.trim().length < 3 || Number(subtotal) < 0) {
      toast.error("Select a supplier and enter valid bill details.")
      return
    }

    setSaving(true)

    try {
      await browserApiRequest<SupplierBill>(
        "/finance/supplier-bills",
        {
          method: "POST",
          body: JSON.stringify({
            supplier_id: supplierId,
            feed_purchase_id: null,
            supplier_invoice_number: invoiceNumber.trim() || null,
            bill_date: billDate,
            due_date: dueDate || null,
            description: description.trim(),
            subtotal,
            tax_amount: tax || "0",
            notes: notes.trim() || null,
          }),
        },
      )

      toast.success("Supplier bill recorded.")
      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Supplier bill could not be recorded.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Record supplier bill</DialogTitle>
          <DialogDescription>
            Create a payable supplier document with an optional due date.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Supplier</Label>
            <Select value={supplierId} onValueChange={setSupplierId}>
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select supplier" />
              </SelectTrigger>
              <SelectContent>
                {activeSuppliers.map((supplier) => (
                  <SelectItem key={supplier.id} value={supplier.id}>
                    {supplier.supplier_code} · {supplier.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="bill-date">Bill date</Label>
              <Input
                id="bill-date"
                type="date"
                value={billDate}
                onChange={(event) => setBillDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bill-due-date">Due date</Label>
              <Input
                id="bill-due-date"
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="supplier-invoice">Supplier invoice number</Label>
            <Input
              id="supplier-invoice"
              value={invoiceNumber}
              onChange={(event) => setInvoiceNumber(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="bill-description">Description</Label>
            <Input
              id="bill-description"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={255}
              required
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="bill-subtotal">Subtotal</Label>
              <Input
                id="bill-subtotal"
                type="number"
                min="0"
                step="0.01"
                value={subtotal}
                onChange={(event) => setSubtotal(event.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="bill-tax">Tax amount</Label>
              <Input
                id="bill-tax"
                type="number"
                min="0"
                step="0.01"
                value={tax}
                onChange={(event) => setTax(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="bill-notes">Notes</Label>
            <Textarea
              id="bill-notes"
              rows={3}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
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
              disabled={saving || activeSuppliers.length === 0}
            >
              {saving ? "Saving..." : "Record bill"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function SupplierPaymentDialog({
  bills,
  onOpenChange,
  onSaved,
}: {
  bills: SupplierBill[]
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const payableBills = bills.filter(
    (bill) =>
      !bill.is_voided &&
      !bill.is_paid &&
      Number(bill.balance_due) > 0,
  )

  const [billId, setBillId] = useState(payableBills[0]?.id ?? "")
  const selectedBill = payableBills.find((bill) => bill.id === billId)
  const [paymentDate, setPaymentDate] = useState(todayIso())
  const [amount, setAmount] = useState(
    selectedBill?.balance_due ?? "",
  )
  const [method, setMethod] =
    useState<FinancePaymentMethod>("CASH")
  const [reference, setReference] = useState("")
  const [notes, setNotes] = useState("")
  const [saving, setSaving] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!billId || Number(amount) <= 0) {
      toast.error("Select a payable bill and enter a valid amount.")
      return
    }

    setSaving(true)

    try {
      await browserApiRequest<SupplierPayment>(
        "/finance/supplier-payments",
        {
          method: "POST",
          body: JSON.stringify({
            supplier_bill_id: billId,
            payment_date: paymentDate,
            amount,
            method,
            reference_number: reference.trim() || null,
            notes: notes.trim() || null,
          }),
        },
      )

      toast.success("Supplier payment posted.")
      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Supplier payment could not be recorded.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Record supplier payment</DialogTitle>
          <DialogDescription>
            Post a cash outflow against an unpaid supplier bill.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-2">
            <Label>Supplier bill</Label>
            <Select
              value={billId}
              onValueChange={(value) => {
                setBillId(value)
                const bill = payableBills.find((item) => item.id === value)
                setAmount(bill?.balance_due ?? "")
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select payable bill" />
              </SelectTrigger>
              <SelectContent>
                {payableBills.map((bill) => (
                  <SelectItem key={bill.id} value={bill.id}>
                    {bill.bill_number} · {bill.supplier_name} ·{" "}
                    {bill.balance_due}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="supplier-payment-date">Payment date</Label>
              <Input
                id="supplier-payment-date"
                type="date"
                value={paymentDate}
                onChange={(event) => setPaymentDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="supplier-payment-amount">Amount</Label>
              <Input
                id="supplier-payment-amount"
                type="number"
                min="0.01"
                step="0.01"
                max={selectedBill?.balance_due}
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label>Payment method</Label>
              <PaymentMethodSelect
                value={method}
                onChange={setMethod}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="supplier-payment-reference">Reference</Label>
              <Input
                id="supplier-payment-reference"
                value={reference}
                onChange={(event) => setReference(event.target.value)}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="supplier-payment-notes">Notes</Label>
            <Textarea
              id="supplier-payment-notes"
              rows={3}
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
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
              disabled={saving || payableBills.length === 0}
            >
              {saving ? "Posting..." : "Record payment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export function CashAdjustmentDialog({
  onOpenChange,
  onSaved,
}: {
  onOpenChange: (open: boolean) => void
  onSaved: () => void
}) {
  const [entryDate, setEntryDate] = useState(todayIso())
  const [direction, setDirection] =
    useState<CashFlowDirection>("INFLOW")
  const [amount, setAmount] = useState("")
  const [description, setDescription] = useState("")
  const [saving, setSaving] = useState(false)

  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (Number(amount) <= 0 || description.trim().length < 5) {
      toast.error("Enter a valid amount and a clear description.")
      return
    }

    setSaving(true)

    try {
      await browserApiRequest<CashLedgerEntry>(
        "/finance/cash-ledger/adjustments",
        {
          method: "POST",
          body: JSON.stringify({
            entry_date: entryDate,
            direction,
            amount,
            description: description.trim(),
          }),
        },
      )

      toast.success("Cash adjustment posted.")
      onOpenChange(false)
      onSaved()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Cash adjustment could not be recorded.",
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cash-ledger adjustment</DialogTitle>
          <DialogDescription>
            Use controlled adjustments only for verified cash corrections.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={submit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="adjustment-date">Entry date</Label>
              <Input
                id="adjustment-date"
                type="date"
                value={entryDate}
                onChange={(event) => setEntryDate(event.target.value)}
              />
            </div>
            <div className="space-y-2">
              <Label>Direction</Label>
              <Select
                value={direction}
                onValueChange={(value) =>
                  setDirection(value as CashFlowDirection)
                }
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="INFLOW">Inflow</SelectItem>
                  <SelectItem value="OUTFLOW">Outflow</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="adjustment-amount">Amount</Label>
            <Input
              id="adjustment-amount"
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(event) => setAmount(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="adjustment-description">Description</Label>
            <Textarea
              id="adjustment-description"
              rows={3}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
              maxLength={255}
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
              {saving ? "Posting..." : "Post adjustment"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function PaymentMethodSelect({
  value,
  onChange,
}: {
  value: FinancePaymentMethod
  onChange: (value: FinancePaymentMethod) => void
}) {
  return (
    <Select
      value={value}
      onValueChange={(nextValue) =>
        onChange(nextValue as FinancePaymentMethod)
      }
    >
      <SelectTrigger className="w-full">
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
  )
}
