"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Banknote,

  Plus,
  ReceiptText,
  RefreshCw,
  Search,
  TrendingDown,
  Wallet,
} from "lucide-react"
import { toast } from "sonner"

import { useAuth } from "@/components/auth/auth-provider"
import {
  CommercialEmpty,
  CommercialLoading,
  CommercialMetric,
  CommercialPageHeader,
  CommercialPager,
  RefreshButton,
  StatusBadge,
} from "@/components/commercial/commercial-ui"
import {
  BillDialog,
  CashAdjustmentDialog,
  CategoryDialog,
  ExpenseDialog,
  ReasonDialog,
  SupplierPaymentDialog,
} from "@/components/finance/finance-dialogs"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { browserApiRequest } from "@/lib/api/browser"
import {
  formatDate,
  formatMoney,
  numeric,
  titleCase,
} from "@/lib/commercial/format"
import type {
  CashLedgerList,
  Expense,
  ExpenseCategory,
  FinanceSummary,
  Paginated,
  SalesReceiptSync,
  Supplier,
  SupplierBill,
  SupplierPayment,
} from "@/lib/finance/types"

type FinanceTab =
  | "expenses"
  | "bills"
  | "payments"
  | "ledger"
  | "categories"

const limit = 12

export function FinanceWorkspace() {
  const { session } = useAuth()
  const permissions = session.permissions
  const currency = session.farm.currency_code || "UGX"

  const [tab, setTab] = useState<FinanceTab>("expenses")
  const [summary, setSummary] = useState<FinanceSummary | null>(null)
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [categories, setCategories] = useState<ExpenseCategory[]>([])
  const [billsReference, setBillsReference] = useState<SupplierBill[]>([])

  const [expenses, setExpenses] = useState<Expense[]>([])
  const [bills, setBills] = useState<SupplierBill[]>([])
  const [payments, setPayments] = useState<SupplierPayment[]>([])
  const [ledger, setLedger] = useState<CashLedgerList | null>(null)

  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("ALL")
  const [dateFrom, setDateFrom] = useState("")
  const [dateTo, setDateTo] = useState("")
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const [dialog, setDialog] = useState<
    | "category-new"
    | "expense"
    | "bill"
    | "payment"
    | "adjustment"
    | null
  >(null)
  const [editingCategory, setEditingCategory] =
    useState<ExpenseCategory | null>(null)
  const [reasonAction, setReasonAction] = useState<{
    type: "expense" | "bill" | "payment"
    id: string
  } | null>(null)

  const canManageCategories = permissions.includes(
    "expense_categories.manage",
  )
  const canRecordExpenses = permissions.includes("expenses.record")
  const canVoidExpenses = permissions.includes("expenses.void")
  const canManageBills = permissions.includes("supplier_bills.manage")
  const canRecordPayments = permissions.includes(
    "supplier_payments.record",
  )
  const canReversePayments = permissions.includes(
    "supplier_payments.reverse",
  )
  const canAdjustCash = permissions.includes("cash_ledger.adjust")

  const loadReferenceData = useCallback(async () => {
    const [supplierResponse, categoryResponse, billResponse] =
      await Promise.all([
        browserApiRequest<Paginated<Supplier>>(
          "/suppliers?offset=0&limit=100&is_active=true",
        ),
        browserApiRequest<Paginated<ExpenseCategory>>(
          "/finance/expense-categories?offset=0&limit=100",
        ),
        browserApiRequest<Paginated<SupplierBill>>(
          "/finance/supplier-bills?offset=0&limit=100",
        ),
      ])

    setSuppliers(supplierResponse.items)
    setCategories(categoryResponse.items)
    setBillsReference(billResponse.items)
  }, [])

  const load = useCallback(async () => {
    setLoading(true)

    try {
      const params = new URLSearchParams({
        offset: String(offset),
        limit: String(limit),
      })

      if (dateFrom && tab !== "categories") {
        params.set("date_from", dateFrom)
      }
      if (dateTo && tab !== "categories") {
        params.set("date_to", dateTo)
      }
      if (
        search.trim() &&
        (tab === "expenses" || tab === "bills" || tab === "categories")
      ) {
        params.set("search", search.trim())
      }

      if (status !== "ALL") {
        if (tab === "expenses") params.set("expense_status", status)
        if (tab === "bills") params.set("bill_status", status)
        if (tab === "payments") params.set("payment_status", status)
        if (tab === "categories") {
          params.set("active_only", String(status === "ACTIVE"))
        }
        if (tab === "ledger") params.set("direction", status)
      }

      const summaryPromise =
        browserApiRequest<FinanceSummary>("/finance/summary")

      let listPromise: Promise<
        | Paginated<Expense>
        | Paginated<SupplierBill>
        | Paginated<SupplierPayment>
        | Paginated<ExpenseCategory>
        | CashLedgerList
      >

      if (tab === "bills") {
        listPromise = browserApiRequest<Paginated<SupplierBill>>(
          `/finance/supplier-bills?${params}`,
        )
      } else if (tab === "payments") {
        listPromise = browserApiRequest<Paginated<SupplierPayment>>(
          `/finance/supplier-payments?${params}`,
        )
      } else if (tab === "ledger") {
        listPromise = browserApiRequest<CashLedgerList>(
          `/finance/cash-ledger?${params}`,
        )
      } else if (tab === "categories") {
        listPromise = browserApiRequest<Paginated<ExpenseCategory>>(
          `/finance/expense-categories?${params}`,
        )
      } else {
        listPromise = browserApiRequest<Paginated<Expense>>(
          `/finance/expenses?${params}`,
        )
      }

      const [summaryResponse, listResponse] = await Promise.all([
        summaryPromise,
        listPromise,
      ])

      setSummary(summaryResponse)
      setTotal(listResponse.total)

      if (tab === "bills") {
        setBills((listResponse as Paginated<SupplierBill>).items)
      } else if (tab === "payments") {
        setPayments(
          (listResponse as Paginated<SupplierPayment>).items,
        )
      } else if (tab === "ledger") {
        setLedger(listResponse as CashLedgerList)
      } else if (tab === "categories") {
        setCategories(
          (listResponse as Paginated<ExpenseCategory>).items,
        )
      } else {
        setExpenses((listResponse as Paginated<Expense>).items)
      }
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Finance records could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [dateFrom, dateTo, offset, search, status, tab])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void Promise.all([load(), loadReferenceData()])
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, loadReferenceData, refreshKey])

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  function changeTab(value: string) {
    setTab(value as FinanceTab)
    setOffset(0)
    setSearch("")
    setStatus("ALL")
  }

  async function syncReceipts() {
    try {
      const response =
        await browserApiRequest<SalesReceiptSync>(
          "/finance/sync/sales-receipts",
          {
            method: "POST",
          },
        )

      toast.success(
        `Sales receipts synchronized: ${response.receipts_created} created, ${response.reversals_created} reversals.`,
      )
      refresh()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Sales receipts could not be synchronized.",
      )
    }
  }

  async function executeReasonAction(reason: string) {
    if (!reasonAction) return

    const endpoint =
      reasonAction.type === "expense"
        ? `/finance/expenses/${reasonAction.id}/void`
        : reasonAction.type === "bill"
          ? `/finance/supplier-bills/${reasonAction.id}/void`
          : `/finance/supplier-payments/${reasonAction.id}/reverse`

    try {
      await browserApiRequest(endpoint, {
        method: "POST",
        body: JSON.stringify({ reason }),
      })

      toast.success(
        reasonAction.type === "payment"
          ? "Supplier payment reversed."
          : `${titleCase(reasonAction.type)} voided.`,
      )
      setReasonAction(null)
      refresh()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Finance action could not be completed.",
      )
      throw error
    }
  }

  const tabStatuses = useMemo(() => {
    if (tab === "expenses") return ["POSTED", "VOIDED"]
    if (tab === "bills") {
      return ["UNPAID", "PARTIALLY_PAID", "PAID", "VOIDED"]
    }
    if (tab === "payments") return ["POSTED", "REVERSED"]
    if (tab === "categories") return ["ACTIVE", "INACTIVE"]
    if (tab === "ledger") return ["INFLOW", "OUTFLOW"]
    return []
  }, [tab])

  function primaryAction() {
    if (tab === "expenses" && canRecordExpenses) {
      return (
        <Button className="rounded-xl" onClick={() => setDialog("expense")}>
          <Plus className="size-4" />
          Record expense
        </Button>
      )
    }

    if (tab === "bills" && canManageBills) {
      return (
        <Button className="rounded-xl" onClick={() => setDialog("bill")}>
          <Plus className="size-4" />
          Record bill
        </Button>
      )
    }

    if (tab === "payments" && canRecordPayments) {
      return (
        <Button className="rounded-xl" onClick={() => setDialog("payment")}>
          <Plus className="size-4" />
          Record payment
        </Button>
      )
    }

    if (tab === "ledger" && canAdjustCash) {
      return (
        <Button
          className="rounded-xl"
          onClick={() => setDialog("adjustment")}
        >
          <Plus className="size-4" />
          Cash adjustment
        </Button>
      )
    }

    if (tab === "categories" && canManageCategories) {
      return (
        <Button
          className="rounded-xl"
          onClick={() => {
            setEditingCategory(null)
            setDialog("category-new")
          }}
        >
          <Plus className="size-4" />
          Add category
        </Button>
      )
    }

    return null
  }

  function listContent() {
    if (loading) return <CommercialLoading label="Loading finance data..." />

    if (tab === "expenses") {
      if (expenses.length === 0) {
        return (
          <CommercialEmpty
            title="No expenses found"
            description="Record an operating expense or change the filters."
          />
        )
      }

      return (
        <div className="divide-y">
          {expenses.map((expense) => (
            <div
              key={expense.id}
              className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.3fr_1fr_1fr_auto] lg:items-center"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">{expense.expense_number}</p>
                  <StatusBadge status={expense.status} />
                </div>
                <p className="mt-1 text-sm">{expense.description}</p>
                <p className="text-xs text-muted-foreground">
                  {expense.category_code} Â· {expense.category_name}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Date</p>
                <p className="font-medium">
                  {formatDate(expense.expense_date)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Amount</p>
                <p className="font-semibold">
                  {formatMoney(expense.amount, currency)}
                </p>
              </div>
              {canVoidExpenses && !expense.is_voided ? (
                <Button
                  size="sm"
                  variant="ghost"
                  className="rounded-xl text-destructive"
                  onClick={() =>
                    setReasonAction({
                      type: "expense",
                      id: expense.id,
                    })
                  }
                >
                  Void
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )
    }

    if (tab === "bills") {
      if (bills.length === 0) {
        return (
          <CommercialEmpty
            title="No supplier bills found"
            description="Record a supplier payable or change the filters."
          />
        )
      }

      return (
        <div className="divide-y">
          {bills.map((bill) => (
            <div
              key={bill.id}
              className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.3fr_1fr_1fr_auto] lg:items-center"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">{bill.bill_number}</p>
                  <StatusBadge status={bill.status} />
                </div>
                <p className="mt-1 text-sm">{bill.supplier_name}</p>
                <p className="text-xs text-muted-foreground">
                  {bill.description}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">
                  Bill / due date
                </p>
                <p className="font-medium">
                  {formatDate(bill.bill_date)} /{" "}
                  {formatDate(bill.due_date)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">
                  Total / balance
                </p>
                <p className="font-semibold">
                  {formatMoney(bill.total_amount, currency)}
                </p>
                <p className="text-xs text-muted-foreground">
                  {formatMoney(bill.balance_due, currency)} due
                </p>
              </div>
              {canManageBills && !bill.is_voided && numeric(bill.amount_paid) === 0 ? (
                <Button
                  size="sm"
                  variant="ghost"
                  className="rounded-xl text-destructive"
                  onClick={() =>
                    setReasonAction({
                      type: "bill",
                      id: bill.id,
                    })
                  }
                >
                  Void
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )
    }

    if (tab === "payments") {
      if (payments.length === 0) {
        return (
          <CommercialEmpty
            title="No supplier payments found"
            description="Payments made against supplier bills appear here."
          />
        )
      }

      return (
        <div className="divide-y">
          {payments.map((payment) => (
            <div
              key={payment.id}
              className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.3fr_1fr_1fr_auto] lg:items-center"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">{payment.payment_number}</p>
                  <StatusBadge status={payment.status} />
                </div>
                <p className="mt-1 text-sm">{payment.supplier_name}</p>
                <p className="text-xs text-muted-foreground">
                  {payment.bill_number}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Payment date</p>
                <p className="font-medium">
                  {formatDate(payment.payment_date)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Amount</p>
                <p className="font-semibold">
                  {formatMoney(payment.amount, currency)}
                </p>
              </div>
              {canReversePayments && !payment.is_reversed ? (
                <Button
                  size="sm"
                  variant="ghost"
                  className="rounded-xl text-destructive"
                  onClick={() =>
                    setReasonAction({
                      type: "payment",
                      id: payment.id,
                    })
                  }
                >
                  Reverse
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )
    }

    if (tab === "ledger") {
      if (!ledger || ledger.items.length === 0) {
        return (
          <CommercialEmpty
            title="No cash-ledger entries found"
            description="Posted sales receipts, expenses, supplier payments, and adjustments appear here."
          />
        )
      }

      return (
        <div className="divide-y">
          {ledger.items.map((entry) => (
            <div
              key={entry.id}
              className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.4fr_1fr_1fr_1fr] lg:items-center"
            >
              <div>
                <p className="font-semibold">{entry.description}</p>
                <p className="text-xs text-muted-foreground">
                  {titleCase(entry.entry_type)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Date</p>
                <p className="font-medium">
                  {formatDate(entry.entry_date)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Movement</p>
                <p
                  className={
                    entry.direction === "INFLOW"
                      ? "font-semibold text-emerald-700 dark:text-emerald-300"
                      : "font-semibold text-destructive"
                  }
                >
                  {entry.direction === "INFLOW" ? "+" : "-"}
                  {formatMoney(entry.amount, currency)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">
                  Balance after
                </p>
                <p className="font-semibold">
                  {formatMoney(entry.balance_after, currency)}
                </p>
              </div>
            </div>
          ))}
        </div>
      )
    }

    if (categories.length === 0) {
      return (
        <CommercialEmpty
          title="No expense categories found"
          description="Create categories before recording operating expenses."
        />
      )
    }

    return (
      <div className="divide-y">
        {categories.map((category) => (
          <div
            key={category.id}
            className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.4fr_1fr_1fr_auto] lg:items-center"
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold">{category.name}</p>
                <StatusBadge
                  status={category.is_active ? "ACTIVE" : "INACTIVE"}
                />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {category.category_code}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Kind</p>
              <p className="font-medium">{titleCase(category.kind)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Description</p>
              <p className="text-sm">
                {category.description ?? "Not recorded"}
              </p>
            </div>
            {canManageCategories ? (
              <Button
                size="sm"
                variant="ghost"
                className="rounded-xl"
                onClick={() => {
                  setEditingCategory(category)
                  setDialog("category-new")
                }}
              >
                Edit
              </Button>
            ) : null}
          </div>
        ))}
      </div>
    )
  }

  const ledgerBalance = ledger?.current_balance ?? summary?.current_cash_balance ?? "0"

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Financial operations"
        title="Expenses, payables, and cash ledger"
        description="Post operating expenses, manage supplier bills and payments, synchronize customer receipts, and maintain an auditable cash balance."
        actions={
          <>
            <RefreshButton onClick={refresh} loading={loading} />
            <Button
              variant="outline"
              className="rounded-xl"
              onClick={() => void syncReceipts()}
            >
              <RefreshCw className="size-4" />
              Sync sales receipts
            </Button>
            {primaryAction()}
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CommercialMetric
          label="Cash balance"
          value={formatMoney(ledgerBalance, currency)}
          detail={`As of ${summary?.as_of_date ?? "today"}`}
          icon={Wallet}
        />
        <CommercialMetric
          label="Supplier payables"
          value={formatMoney(
            summary?.outstanding_supplier_payables ?? 0,
            currency,
          )}
          detail="Outstanding supplier bills"
          icon={ReceiptText}
        />
        <CommercialMetric
          label="Posted expenses"
          value={formatMoney(summary?.posted_expenses ?? 0, currency)}
          detail="Operating expenses to date"
          icon={TrendingDown}
        />
        <CommercialMetric
          label="Sales receipts"
          value={formatMoney(summary?.sales_receipts ?? 0, currency)}
          detail="Synchronized customer payments"
          icon={Banknote}
        />
      </div>

      <Card className="overflow-hidden rounded-2xl">
        <CardContent className="p-0">
          <div className="border-b p-4">
            <Tabs value={tab} onValueChange={changeTab}>
              <TabsList className="h-auto flex-wrap rounded-xl">
                <TabsTrigger value="expenses">Expenses</TabsTrigger>
                <TabsTrigger value="bills">Supplier bills</TabsTrigger>
                <TabsTrigger value="payments">Payments</TabsTrigger>
                <TabsTrigger value="ledger">Cash ledger</TabsTrigger>
                <TabsTrigger value="categories">Categories</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="mt-4 grid gap-3 lg:grid-cols-[1fr_160px_160px_210px]">
              {tab === "expenses" ||
              tab === "bills" ||
              tab === "categories" ? (
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder="Search records..."
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value)
                      setOffset(0)
                    }}
                  />
                </div>
              ) : (
                <div />
              )}

              {tab !== "categories" ? (
                <>
                  <Input
                    type="date"
                    value={dateFrom}
                    onChange={(event) => {
                      setDateFrom(event.target.value)
                      setOffset(0)
                    }}
                    aria-label="Date from"
                  />
                  <Input
                    type="date"
                    value={dateTo}
                    onChange={(event) => {
                      setDateTo(event.target.value)
                      setOffset(0)
                    }}
                    aria-label="Date to"
                  />
                </>
              ) : (
                <>
                  <div />
                  <div />
                </>
              )}

              <Select
                value={status}
                onValueChange={(value) => {
                  setStatus(value)
                  setOffset(0)
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All statuses</SelectItem>
                  {tabStatuses.map((value) => (
                    <SelectItem key={value} value={value}>
                      {titleCase(value)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {listContent()}

          <CommercialPager
            offset={offset}
            limit={limit}
            total={total}
            onChange={setOffset}
          />
        </CardContent>
      </Card>

      {dialog === "category-new" ? (
        <CategoryDialog
          category={editingCategory}
          onOpenChange={(open) => {
            if (!open) {
              setDialog(null)
              setEditingCategory(null)
            }
          }}
          onSaved={refresh}
        />
      ) : null}

      {dialog === "expense" ? (
        <ExpenseDialog
          categories={categories}
          suppliers={suppliers}
          onOpenChange={(open) => {
            if (!open) setDialog(null)
          }}
          onSaved={refresh}
        />
      ) : null}

      {dialog === "bill" ? (
        <BillDialog
          suppliers={suppliers}
          onOpenChange={(open) => {
            if (!open) setDialog(null)
          }}
          onSaved={refresh}
        />
      ) : null}

      {dialog === "payment" ? (
        <SupplierPaymentDialog
          bills={billsReference}
          onOpenChange={(open) => {
            if (!open) setDialog(null)
          }}
          onSaved={refresh}
        />
      ) : null}

      {dialog === "adjustment" ? (
        <CashAdjustmentDialog
          onOpenChange={(open) => {
            if (!open) setDialog(null)
          }}
          onSaved={refresh}
        />
      ) : null}

      {reasonAction ? (
        <ReasonDialog
          title={
            reasonAction.type === "payment"
              ? "Reverse supplier payment"
              : `Void ${reasonAction.type}`
          }
          description="This audited action changes the cash ledger and related document balance. Enter a clear reason."
          confirmLabel={
            reasonAction.type === "payment"
              ? "Reverse payment"
              : "Void record"
          }
          onOpenChange={(open) => {
            if (!open) setReasonAction(null)
          }}
          onConfirm={executeReasonAction}
        />
      ) : null}
    </div>
  )
}

