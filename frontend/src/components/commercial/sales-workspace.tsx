"use client"

import Link from "next/link"
import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Banknote,
  CircleDollarSign,
  CreditCard,
  FileText,
  Pencil,
  Plus,
  ReceiptText,
  RotateCcw,
  Search,
  ShoppingCart,
  UserRound,
  Users,
} from "lucide-react"
import { toast } from "sonner"

import {
  PaymentDialog,
  ReasonActionDialog,
  ReturnDialog,
} from "@/components/commercial/action-dialogs"
import {
  CommercialEmpty,
  CommercialLoading,
  CommercialMetric,
  CommercialPageHeader,
  CommercialPager,
  RefreshButton,
  StatusBadge,
} from "@/components/commercial/commercial-ui"
import { CustomerDialog } from "@/components/commercial/customer-dialog"
import { useAuth } from "@/components/auth/auth-provider"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
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
  Customer,
  CustomerStatement,
  Paginated,
  Sale,
  SalePayment,
  SaleReturn,
  SalesSummary,
} from "@/lib/commercial/types"

type WorkspaceTab = "sales" | "customers" | "payments" | "returns"

const limit = 12

export function SalesWorkspace() {
  const { session } = useAuth()
  const permissions = session.permissions
  const currency = session.farm.currency_code || "UGX"

  const [tab, setTab] = useState<WorkspaceTab>("sales")
  const [summary, setSummary] = useState<SalesSummary | null>(null)
  const [customers, setCustomers] = useState<Customer[]>([])
  const [sales, setSales] = useState<Sale[]>([])
  const [payments, setPayments] = useState<SalePayment[]>([])
  const [returns, setReturns] = useState<SaleReturn[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState("ALL")
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)

  const [customerDialogOpen, setCustomerDialogOpen] = useState(false)
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null)
  const [statementCustomer, setStatementCustomer] =
    useState<Customer | null>(null)
  const [statement, setStatement] = useState<CustomerStatement | null>(null)
  const [selectedSale, setSelectedSale] = useState<Sale | null>(null)
  const [paymentOpen, setPaymentOpen] = useState(false)
  const [paymentSale, setPaymentSale] = useState<Sale | null>(null)
  const [returnOpen, setReturnOpen] = useState(false)
  const [returnSale, setReturnSale] = useState<Sale | null>(null)
  const [action, setAction] = useState<{
    type: "cancel-sale" | "reverse-payment" | "reverse-return"
    id: string
  } | null>(null)

  const canManageCustomers = permissions.includes("customers.manage")
  const canCreateSales = permissions.includes("sales.create")
  const canConfirmSales = permissions.includes("sales.confirm")
  const canCancelSales = permissions.includes("sales.cancel")
  const canRecordPayments = permissions.includes("payments.record")
  const canReversePayments = permissions.includes("payments.reverse")
  const canHandleReturns = permissions.includes("sales.returns")

  const loadReferenceData = useCallback(async () => {
    const [customerResponse, saleResponse] = await Promise.all([
      browserApiRequest<Paginated<Customer>>(
        "/sales/customers?offset=0&limit=100",
      ),
      browserApiRequest<Paginated<Sale>>(
        "/sales/invoices?offset=0&limit=100",
      ),
    ])

    setCustomers(customerResponse.items)
    setSales(saleResponse.items)
  }, [])

  const loadWorkspace = useCallback(async () => {
    setLoading(true)

    try {
      const summaryPromise =
        browserApiRequest<SalesSummary>("/sales/summary")

      const params = new URLSearchParams({
        offset: String(offset),
        limit: String(limit),
      })

      if (status !== "ALL") {
        const statusParameter =
          tab === "customers"
            ? "customer_status"
            : tab === "payments"
              ? "payment_status"
              : tab === "returns"
                ? "return_status"
                : "sale_status"

        params.set(statusParameter, status)
      }
      if (search.trim() && (tab === "sales" || tab === "customers")) {
        params.set("search", search.trim())
      }

      let listPromise: Promise<
        Paginated<Customer | Sale | SalePayment | SaleReturn>
      >

      if (tab === "customers") {
        listPromise = browserApiRequest<Paginated<Customer>>(
          `/sales/customers?${params}`,
        )
      } else if (tab === "payments") {
        listPromise = browserApiRequest<Paginated<SalePayment>>(
          `/sales/payments?${params}`,
        )
      } else if (tab === "returns") {
        listPromise = browserApiRequest<Paginated<SaleReturn>>(
          `/sales/returns?${params}`,
        )
      } else {
        listPromise = browserApiRequest<Paginated<Sale>>(
          `/sales/invoices?${params}`,
        )
      }

      const [summaryResponse, listResponse] = await Promise.all([
        summaryPromise,
        listPromise,
      ])

      setSummary(summaryResponse)
      setTotal(listResponse.total)

      if (tab === "customers") {
        setCustomers(listResponse.items as Customer[])
      } else if (tab === "payments") {
        setPayments(listResponse.items as SalePayment[])
      } else if (tab === "returns") {
        setReturns(listResponse.items as SaleReturn[])
      } else {
        setSales(listResponse.items as Sale[])
      }
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Commercial records could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [offset, search, status, tab])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadWorkspace()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [loadWorkspace, refreshKey])

  function changeTab(value: string) {
    setTab(value as WorkspaceTab)
    setOffset(0)
    setStatus("ALL")
    setSearch("")
  }

  function refresh() {
    setRefreshKey((current) => current + 1)
    void loadReferenceData().catch(() => undefined)
  }

  async function openStatement(customer: Customer) {
    setStatementCustomer(customer)
    setStatement(null)

    try {
      const response = await browserApiRequest<CustomerStatement>(
        `/sales/customers/${customer.id}/statement`,
      )
      setStatement(response)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Statement could not be loaded.",
      )
    }
  }

  async function confirmSale(sale: Sale) {
    try {
      await browserApiRequest<Sale>(
        `/sales/invoices/${sale.id}/confirm`,
        {
          method: "POST",
          body: JSON.stringify({ notes: null }),
        },
      )
      toast.success("Invoice confirmed and egg stock deducted.")
      setSelectedSale(null)
      refresh()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Invoice could not be confirmed.",
      )
    }
  }

  async function executeReasonAction(reason: string) {
    if (!action) return

    try {
      if (action.type === "cancel-sale") {
        await browserApiRequest<Sale>(
          `/sales/invoices/${action.id}/cancel`,
          {
            method: "POST",
            body: JSON.stringify({ reason }),
          },
        )
        toast.success("Invoice cancelled.")
        setSelectedSale(null)
      } else if (action.type === "reverse-payment") {
        await browserApiRequest<SalePayment>(
          `/sales/payments/${action.id}/reverse`,
          {
            method: "POST",
            body: JSON.stringify({ reason }),
          },
        )
        toast.success("Payment reversed.")
      } else {
        await browserApiRequest<SaleReturn>(
          `/sales/returns/${action.id}/reverse`,
          {
            method: "POST",
            body: JSON.stringify({ reason }),
          },
        )
        toast.success("Sale return reversed.")
      }

      setAction(null)
      refresh()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "The action could not be completed.",
      )
      throw error
    }
  }

  const primaryActions = (
    <>
      <RefreshButton onClick={refresh} loading={loading} />
      {canManageCustomers ? (
        <Button
          variant="outline"
          className="rounded-xl"
          onClick={() => {
            setEditingCustomer(null)
            setCustomerDialogOpen(true)
          }}
        >
          <UserRound className="size-4" />
          Add customer
        </Button>
      ) : null}
      {canCreateSales ? (
        <Button asChild className="rounded-xl">
          <Link href="/sales/new">
            <Plus className="size-4" />
            New invoice
          </Link>
        </Button>
      ) : null}
    </>
  )

  const summaryCards = [
    {
      label: "Gross sales",
      value: formatMoney(summary?.gross_sales_value ?? 0, currency),
      detail: `${summary?.confirmed_sales ?? 0} confirmed invoices`,
      icon: ShoppingCart,
    },
    {
      label: "Outstanding",
      value: formatMoney(summary?.outstanding_receivables ?? 0, currency),
      detail: "Customer receivables",
      icon: CreditCard,
    },
    {
      label: "Payments",
      value: formatMoney(summary?.posted_payments ?? 0, currency),
      detail: "Posted customer receipts",
      icon: Banknote,
    },
    {
      label: "Active customers",
      value: String(summary?.active_customers ?? 0),
      detail: `${summary?.draft_sales ?? 0} draft invoices`,
      icon: Users,
    },
  ]

  const statusOptions =
    tab === "customers"
      ? ["ACTIVE", "INACTIVE", "BLOCKED"]
      : tab === "payments" || tab === "returns"
        ? ["POSTED", "REVERSED"]
        : [
            "DRAFT",
            "CONFIRMED",
            "PARTIALLY_PAID",
            "PAID",
            "PARTIALLY_RETURNED",
            "RETURNED",
            "CANCELLED",
          ]

  const listContent = useMemo(() => {
    if (loading) return <CommercialLoading />

    if (tab === "customers") {
      if (customers.length === 0) {
        return (
          <CommercialEmpty
            title="No customers found"
            description="Create the first customer account to begin issuing invoices."
          />
        )
      }

      return (
        <div className="divide-y">
          {customers.map((customer) => (
            <div
              key={customer.id}
              className="grid gap-4 p-4 transition-colors hover:bg-muted/30 lg:grid-cols-[1.4fr_1fr_1fr_auto] lg:items-center"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">{customer.name}</p>
                  <StatusBadge status={customer.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {customer.customer_code} ·{" "}
                  {customer.phone_number ?? "No telephone"}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">
                  Current balance
                </p>
                <p className="font-medium">
                  {formatMoney(customer.current_balance, currency)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">
                  Available credit
                </p>
                <p
                  className={
                    numeric(customer.available_credit) < 0
                      ? "font-medium text-destructive"
                      : "font-medium"
                  }
                >
                  {formatMoney(customer.available_credit, currency)}
                </p>
              </div>
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-xl"
                  onClick={() => void openStatement(customer)}
                >
                  <FileText className="size-4" />
                  Statement
                </Button>
                {canManageCustomers ? (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="rounded-xl"
                    onClick={() => {
                      setEditingCustomer(customer)
                      setCustomerDialogOpen(true)
                    }}
                  >
                    <Pencil className="size-4" />
                    Edit
                  </Button>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      )
    }

    if (tab === "payments") {
      if (payments.length === 0) {
        return (
          <CommercialEmpty
            title="No payments found"
            description="Payments recorded against confirmed invoices appear here."
          />
        )
      }

      return (
        <div className="divide-y">
          {payments.map((payment) => (
            <div
              key={payment.id}
              className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.2fr_1fr_1fr_auto] lg:items-center"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">{payment.payment_number}</p>
                  <StatusBadge status={payment.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {payment.customer_name} · {payment.invoice_number}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Amount</p>
                <p className="font-medium">
                  {formatMoney(payment.amount, currency)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Received</p>
                <p className="font-medium">
                  {formatDate(payment.payment_date)} ·{" "}
                  {titleCase(payment.method)}
                </p>
              </div>
              {canReversePayments && !payment.is_reversed ? (
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-xl text-destructive"
                  onClick={() =>
                    setAction({
                      type: "reverse-payment",
                      id: payment.id,
                    })
                  }
                >
                  <RotateCcw className="size-4" />
                  Reverse
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )
    }

    if (tab === "returns") {
      if (returns.length === 0) {
        return (
          <CommercialEmpty
            title="No sale returns found"
            description="Posted customer returns and their reversals appear here."
          />
        )
      }

      return (
        <div className="divide-y">
          {returns.map((saleReturn) => (
            <div
              key={saleReturn.id}
              className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.2fr_1fr_1fr_auto] lg:items-center"
            >
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="font-semibold">
                    {saleReturn.return_number}
                  </p>
                  <StatusBadge status={saleReturn.status} />
                </div>
                <p className="mt-1 text-xs text-muted-foreground">
                  {saleReturn.customer_name} · {saleReturn.invoice_number}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Refund value</p>
                <p className="font-medium">
                  {formatMoney(saleReturn.total_refund, currency)}
                </p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Return date</p>
                <p className="font-medium">
                  {formatDate(saleReturn.return_date)}
                </p>
              </div>
              {canHandleReturns && !saleReturn.is_reversed ? (
                <Button
                  variant="ghost"
                  size="sm"
                  className="rounded-xl text-destructive"
                  onClick={() =>
                    setAction({
                      type: "reverse-return",
                      id: saleReturn.id,
                    })
                  }
                >
                  <RotateCcw className="size-4" />
                  Reverse
                </Button>
              ) : null}
            </div>
          ))}
        </div>
      )
    }

    if (sales.length === 0) {
      return (
        <CommercialEmpty
          title="No invoices found"
          description="Create a draft customer invoice to begin the sales lifecycle."
          action={
            canCreateSales ? (
              <Button asChild className="rounded-xl">
                <Link href="/sales/new">Create invoice</Link>
              </Button>
            ) : undefined
          }
        />
      )
    }

    return (
      <div className="divide-y">
        {sales.map((sale) => (
          <button
            key={sale.id}
            type="button"
            className="grid w-full gap-4 p-4 text-left transition-colors hover:bg-muted/30 lg:grid-cols-[1.2fr_1fr_1fr_1fr] lg:items-center"
            onClick={() => setSelectedSale(sale)}
          >
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <p className="font-semibold">{sale.invoice_number}</p>
                <StatusBadge status={sale.status} />
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                {sale.customer_code} · {sale.customer_name}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Invoice date</p>
              <p className="font-medium">{formatDate(sale.sale_date)}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Total</p>
              <p className="font-medium">
                {formatMoney(sale.total_amount, currency)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Balance due</p>
              <p
                className={
                  numeric(sale.balance_due) > 0
                    ? "font-medium text-amber-700 dark:text-amber-300"
                    : "font-medium text-emerald-700 dark:text-emerald-300"
                }
              >
                {formatMoney(sale.balance_due, currency)}
              </p>
            </div>
          </button>
        ))}
      </div>
    )
  }, [
    canCreateSales,
    canHandleReturns,
    canManageCustomers,
    canReversePayments,
    currency,
    customers,
    loading,
    payments,
    returns,
    sales,
    tab,
  ])

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Commercial operations"
        title="Sales and customer accounts"
        description="Manage customer credit, draft and confirm egg invoices, record receipts, post returns, and review account statements."
        actions={primaryActions}
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summaryCards.map((card) => (
          <CommercialMetric key={card.label} {...card} />
        ))}
      </div>

      <Card className="overflow-hidden rounded-2xl">
        <CardContent className="p-0">
          <div className="border-b p-4">
            <Tabs
              value={tab}
              onValueChange={changeTab}
            >
              <TabsList className="h-auto flex-wrap rounded-xl">
                <TabsTrigger value="sales">Invoices</TabsTrigger>
                <TabsTrigger value="customers">Customers</TabsTrigger>
                <TabsTrigger value="payments">Payments</TabsTrigger>
                <TabsTrigger value="returns">Returns</TabsTrigger>
              </TabsList>
            </Tabs>

            <div className="mt-4 grid gap-3 sm:grid-cols-[1fr_220px]">
              {(tab === "sales" || tab === "customers") ? (
                <div className="relative">
                  <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder={
                      tab === "customers"
                        ? "Search code, name, telephone..."
                        : "Search invoice or customer..."
                    }
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

              <Select
                value={status}
                onValueChange={(value) => {
                  setStatus(value)
                  setOffset(0)
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All statuses" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ALL">All statuses</SelectItem>
                  {statusOptions.map((item) => (
                    <SelectItem key={item} value={item}>
                      {titleCase(item)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          {listContent}

          <CommercialPager
            offset={offset}
            limit={limit}
            total={total}
            onChange={setOffset}
          />
        </CardContent>
      </Card>

      {customerDialogOpen ? (
        <CustomerDialog
          open
          customer={editingCustomer}
          onOpenChange={setCustomerDialogOpen}
          onSaved={refresh}
        />
      ) : null}

      <Dialog
        open={Boolean(statementCustomer)}
        onOpenChange={(open) => {
          if (!open) {
            setStatementCustomer(null)
            setStatement(null)
          }
        }}
      >
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>
              {statementCustomer?.name ?? "Customer"} statement
            </DialogTitle>
            <DialogDescription>
              Complete account ledger and running customer balance.
            </DialogDescription>
          </DialogHeader>

          {!statement ? (
            <CommercialLoading label="Loading customer statement..." />
          ) : (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Opening balance
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(statement.opening_balance, currency)}
                  </p>
                </div>
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Closing balance
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(statement.closing_balance, currency)}
                  </p>
                </div>
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Available credit
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(
                      statement.customer.available_credit,
                      currency,
                    )}
                  </p>
                </div>
              </div>

              {statement.entries.length === 0 ? (
                <CommercialEmpty
                  title="No ledger activity"
                  description="This customer has no account movements in the selected period."
                />
              ) : (
                <div className="divide-y overflow-hidden rounded-2xl border">
                  {statement.entries.map((entry) => (
                    <div
                      key={entry.id}
                      className="grid gap-3 p-4 sm:grid-cols-[1fr_120px_120px_150px]"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline">
                            {titleCase(entry.entry_type)}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {formatDate(entry.entry_date)}
                          </span>
                        </div>
                        <p className="mt-2 text-sm">{entry.description}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">
                          Debit
                        </p>
                        <p className="text-sm font-medium">
                          {formatMoney(entry.debit_amount, currency)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">
                          Credit
                        </p>
                        <p className="text-sm font-medium">
                          {formatMoney(entry.credit_amount, currency)}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground">
                          Balance
                        </p>
                        <p className="text-sm font-semibold">
                          {formatMoney(entry.balance_after, currency)}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog
        open={Boolean(selectedSale)}
        onOpenChange={(open) => {
          if (!open) setSelectedSale(null)
        }}
      >
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle>{selectedSale?.invoice_number}</DialogTitle>
            <DialogDescription>
              Invoice lifecycle, customer balance, and line-item details.
            </DialogDescription>
          </DialogHeader>

          {selectedSale ? (
            <div className="space-y-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="font-semibold">{selectedSale.customer_name}</p>
                  <p className="text-xs text-muted-foreground">
                    {selectedSale.customer_code} ·{" "}
                    {formatDate(selectedSale.sale_date)}
                  </p>
                </div>
                <StatusBadge status={selectedSale.status} />
              </div>

              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">Total</p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(selectedSale.total_amount, currency)}
                  </p>
                </div>
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">Paid</p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(selectedSale.amount_paid, currency)}
                  </p>
                </div>
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Balance due
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(selectedSale.balance_due, currency)}
                  </p>
                </div>
              </div>

              <div className="divide-y overflow-hidden rounded-2xl border">
                {selectedSale.items.map((item) => (
                  <div
                    key={item.id}
                    className="grid gap-3 p-4 sm:grid-cols-[1fr_100px_130px_140px]"
                  >
                    <div>
                      <p className="font-medium">
                        {titleCase(item.egg_grade)}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {titleCase(item.unit)} · {item.eggs_per_unit} eggs
                        per unit
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Quantity
                      </p>
                      <p className="font-medium">{item.quantity}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Unit price
                      </p>
                      <p className="font-medium">
                        {formatMoney(item.unit_price, currency)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">
                        Line total
                      </p>
                      <p className="font-semibold">
                        {formatMoney(item.line_total, currency)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap justify-end gap-2">
                {selectedSale.status === "DRAFT" && canCreateSales ? (
                  <Button asChild variant="outline">
                    <Link href={`/sales/new?edit=${selectedSale.id}`}>
                      <Pencil className="size-4" />
                      Edit draft
                    </Link>
                  </Button>
                ) : null}
                {selectedSale.status === "DRAFT" && canConfirmSales ? (
                  <Button onClick={() => void confirmSale(selectedSale)}>
                    <ReceiptText className="size-4" />
                    Confirm invoice
                  </Button>
                ) : null}
                {selectedSale.status === "DRAFT" && canCancelSales ? (
                  <Button
                    variant="destructive"
                    onClick={() =>
                      setAction({
                        type: "cancel-sale",
                        id: selectedSale.id,
                      })
                    }
                  >
                    Cancel invoice
                  </Button>
                ) : null}
                {selectedSale.is_confirmed &&
                numeric(selectedSale.balance_due) > 0 &&
                canRecordPayments ? (
                  <Button
                    onClick={() => {
                      setPaymentSale(selectedSale)
                      setPaymentOpen(true)
                    }}
                  >
                    <CircleDollarSign className="size-4" />
                    Record payment
                  </Button>
                ) : null}
                {selectedSale.is_confirmed &&
                selectedSale.items.some(
                  (item) => item.remaining_returnable_quantity > 0,
                ) &&
                canHandleReturns ? (
                  <Button
                    variant="outline"
                    onClick={() => {
                      setReturnSale(selectedSale)
                      setReturnOpen(true)
                    }}
                  >
                    <RotateCcw className="size-4" />
                    Record return
                  </Button>
                ) : null}
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {paymentOpen ? (
        <PaymentDialog
          open
          sales={sales}
          initialSale={paymentSale}
          currency={currency}
          onOpenChange={(open) => {
            setPaymentOpen(open)
            if (!open) setPaymentSale(null)
          }}
          onSaved={refresh}
        />
      ) : null}

      {returnOpen ? (
        <ReturnDialog
          open
          sales={sales}
          initialSale={returnSale}
          onOpenChange={(open) => {
            setReturnOpen(open)
            if (!open) setReturnSale(null)
          }}
          onSaved={refresh}
        />
      ) : null}

      {action ? (
        <ReasonActionDialog
          open
          title={
            action.type === "cancel-sale"
              ? "Cancel invoice"
              : action.type === "reverse-payment"
                ? "Reverse payment"
                : "Reverse sale return"
          }
          description="This action is audited and changes customer balances. Enter a clear reason."
          confirmLabel={
            action.type === "cancel-sale"
              ? "Cancel invoice"
              : "Reverse record"
          }
          destructive
          onOpenChange={(open) => {
            if (!open) setAction(null)
          }}
          onConfirm={executeReasonAction}
        />
      ) : null}
    </div>
  )
}
