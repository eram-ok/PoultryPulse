"use client"

import { useCallback, useEffect, useMemo, useState } from "react"
import {
  Building2,
  FileText,
  Pencil,
  Plus,
  Power,
  PowerOff,
  Search,
  Truck,
  WalletCards,
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
import { SupplierDialog } from "@/components/finance/supplier-dialog"
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
import { browserApiRequest } from "@/lib/api/browser"
import {
  formatDate,
  formatMoney,
  titleCase,
} from "@/lib/commercial/format"
import type {
  Paginated,
  Supplier,
  SupplierStatement,
} from "@/lib/finance/types"

const limit = 12

export function SuppliersWorkspace() {
  const { session } = useAuth()
  const permissions = session.permissions
  const currency = session.farm.currency_code || "UGX"

  const [items, setItems] = useState<Supplier[]>([])
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [search, setSearch] = useState("")
  const [supplierType, setSupplierType] = useState("ALL")
  const [activeFilter, setActiveFilter] = useState("ALL")
  const [loading, setLoading] = useState(true)
  const [refreshKey, setRefreshKey] = useState(0)
  const [dialogSupplier, setDialogSupplier] =
    useState<Supplier | null | undefined>(undefined)
  const [statementSupplier, setStatementSupplier] =
    useState<Supplier | null>(null)
  const [statement, setStatement] =
    useState<SupplierStatement | null>(null)

  const canCreate = permissions.includes("suppliers.create")
  const canUpdate = permissions.includes("suppliers.update")
  const canViewStatements = permissions.includes("finance.reports")

  const load = useCallback(async () => {
    setLoading(true)

    const params = new URLSearchParams({
      offset: String(offset),
      limit: String(limit),
    })

    if (search.trim()) params.set("search", search.trim())
    if (supplierType !== "ALL") {
      params.set("supplier_type", supplierType)
    }
    if (activeFilter !== "ALL") {
      params.set("is_active", String(activeFilter === "ACTIVE"))
    }

    try {
      const response = await browserApiRequest<Paginated<Supplier>>(
        `/suppliers?${params}`,
      )
      setItems(response.items)
      setTotal(response.total)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Suppliers could not be loaded.",
      )
    } finally {
      setLoading(false)
    }
  }, [activeFilter, offset, search, supplierType])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void load()
    }, 0)

    return () => window.clearTimeout(timer)
  }, [load, refreshKey])

  const metrics = useMemo(() => {
    const active = items.filter((item) => item.is_active).length
    const feed = items.filter(
      (item) => item.supplier_type === "FEED_SUPPLIER",
    ).length
    const medicine = items.filter(
      (item) => item.supplier_type === "MEDICINE_SUPPLIER",
    ).length

    return { active, feed, medicine }
  }, [items])

  function refresh() {
    setRefreshKey((current) => current + 1)
  }

  async function toggleSupplier(supplier: Supplier) {
    try {
      await browserApiRequest<Supplier>(
        `/suppliers/${supplier.id}/${
          supplier.is_active ? "deactivate" : "activate"
        }`,
        {
          method: "POST",
        },
      )
      toast.success(
        supplier.is_active
          ? "Supplier deactivated."
          : "Supplier activated.",
      )
      refresh()
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Supplier status could not be changed.",
      )
    }
  }

  async function openStatement(supplier: Supplier) {
    setStatementSupplier(supplier)
    setStatement(null)

    try {
      const response =
        await browserApiRequest<SupplierStatement>(
          `/finance/suppliers/${supplier.id}/statement`,
        )
      setStatement(response)
    } catch (error) {
      toast.error(
        error instanceof Error
          ? error.message
          : "Supplier statement could not be loaded.",
      )
    }
  }

  return (
    <div className="space-y-6">
      <CommercialPageHeader
        eyebrow="Commercial operations"
        title="Supplier directory"
        description="Register farm suppliers, maintain contact details and activity status, and review supplier account statements."
        actions={
          <>
            <RefreshButton onClick={refresh} loading={loading} />
            {canCreate ? (
              <Button
                className="rounded-xl"
                onClick={() => setDialogSupplier(null)}
              >
                <Plus className="size-4" />
                Add supplier
              </Button>
            ) : null}
          </>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <CommercialMetric
          label="Visible suppliers"
          value={String(total)}
          detail="Matching current filters"
          icon={Building2}
        />
        <CommercialMetric
          label="Active on page"
          value={String(metrics.active)}
          detail="Available for new transactions"
          icon={Power}
        />
        <CommercialMetric
          label="Feed suppliers"
          value={String(metrics.feed)}
          detail="Visible page records"
          icon={Truck}
        />
        <CommercialMetric
          label="Medicine suppliers"
          value={String(metrics.medicine)}
          detail="Visible page records"
          icon={WalletCards}
        />
      </div>

      <Card className="overflow-hidden rounded-2xl">
        <CardContent className="p-0">
          <div className="grid gap-3 border-b p-4 lg:grid-cols-[1fr_230px_190px]">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-3 size-4 text-muted-foreground" />
              <Input
                className="pl-9"
                placeholder="Search code, name, telephone, or email..."
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value)
                  setOffset(0)
                }}
              />
            </div>

            <Select
              value={supplierType}
              onValueChange={(value) => {
                setSupplierType(value)
                setOffset(0)
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All supplier types</SelectItem>
                {[
                  "BIRD_SUPPLIER",
                  "FEED_SUPPLIER",
                  "MEDICINE_SUPPLIER",
                  "EQUIPMENT_SUPPLIER",
                  "GENERAL_SUPPLIER",
                ].map((value) => (
                  <SelectItem key={value} value={value}>
                    {titleCase(value)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select
              value={activeFilter}
              onValueChange={(value) => {
                setActiveFilter(value)
                setOffset(0)
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="ALL">All activity states</SelectItem>
                <SelectItem value="ACTIVE">Active only</SelectItem>
                <SelectItem value="INACTIVE">Inactive only</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {loading ? (
            <CommercialLoading label="Loading suppliers..." />
          ) : items.length === 0 ? (
            <CommercialEmpty
              title="No suppliers found"
              description="Register a supplier or change the current filters."
            />
          ) : (
            <div className="divide-y">
              {items.map((supplier) => (
                <div
                  key={supplier.id}
                  className="grid gap-4 p-4 hover:bg-muted/30 lg:grid-cols-[1.3fr_1fr_1fr_auto] lg:items-center"
                >
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <p className="font-semibold">{supplier.name}</p>
                      <StatusBadge
                        status={supplier.is_active ? "ACTIVE" : "INACTIVE"}
                      />
                    </div>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {supplier.supplier_code} Â·{" "}
                      {titleCase(supplier.supplier_type)}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">Contact</p>
                    <p className="text-sm font-medium">
                      {supplier.telephone ?? "No telephone"}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {supplier.email ?? "No email"}
                    </p>
                  </div>

                  <div>
                    <p className="text-xs text-muted-foreground">Address</p>
                    <p className="text-sm font-medium">
                      {supplier.address ?? "Not recorded"}
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {canViewStatements ? (
                      <Button
                        size="sm"
                        variant="outline"
                        className="rounded-xl"
                        onClick={() => void openStatement(supplier)}
                      >
                        <FileText className="size-4" />
                        Statement
                      </Button>
                    ) : null}
                    {canUpdate ? (
                      <>
                        <Button
                          size="sm"
                          variant="ghost"
                          className="rounded-xl"
                          onClick={() => setDialogSupplier(supplier)}
                        >
                          <Pencil className="size-4" />
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          className={
                            supplier.is_active
                              ? "rounded-xl text-destructive"
                              : "rounded-xl text-emerald-700 dark:text-emerald-300"
                          }
                          onClick={() => void toggleSupplier(supplier)}
                        >
                          {supplier.is_active ? (
                            <PowerOff className="size-4" />
                          ) : (
                            <Power className="size-4" />
                          )}
                          {supplier.is_active ? "Deactivate" : "Activate"}
                        </Button>
                      </>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}

          <CommercialPager
            offset={offset}
            limit={limit}
            total={total}
            onChange={setOffset}
          />
        </CardContent>
      </Card>

      {dialogSupplier !== undefined ? (
        <SupplierDialog
          supplier={dialogSupplier}
          onOpenChange={(open) => {
            if (!open) setDialogSupplier(undefined)
          }}
          onSaved={refresh}
        />
      ) : null}

      <Dialog
        open={Boolean(statementSupplier)}
        onOpenChange={(open) => {
          if (!open) {
            setStatementSupplier(null)
            setStatement(null)
          }
        }}
      >
        <DialogContent className="max-h-[92vh] overflow-y-auto sm:max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              {statementSupplier?.name ?? "Supplier"} statement
            </DialogTitle>
            <DialogDescription>
              Bills, payments, and outstanding supplier balance.
            </DialogDescription>
          </DialogHeader>

          {!statement ? (
            <CommercialLoading label="Loading supplier statement..." />
          ) : (
            <div className="space-y-5">
              <div className="grid gap-3 sm:grid-cols-3">
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Total billed
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(statement.total_billed, currency)}
                  </p>
                </div>
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Total paid
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(statement.total_paid, currency)}
                  </p>
                </div>
                <div className="rounded-2xl border p-4">
                  <p className="text-xs text-muted-foreground">
                    Outstanding
                  </p>
                  <p className="mt-1 font-semibold">
                    {formatMoney(statement.outstanding_balance, currency)}
                  </p>
                </div>
              </div>

              <div>
                <h3 className="mb-3 font-semibold">Bills</h3>
                {statement.bills.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No supplier bills recorded.
                  </p>
                ) : (
                  <div className="divide-y overflow-hidden rounded-2xl border">
                    {statement.bills.map((bill) => (
                      <div
                        key={bill.id}
                        className="grid gap-3 p-4 sm:grid-cols-[1fr_140px_140px]"
                      >
                        <div>
                          <p className="font-medium">{bill.bill_number}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatDate(bill.bill_date)} Â· {bill.description}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Total
                          </p>
                          <p className="font-medium">
                            {formatMoney(bill.total_amount, currency)}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">
                            Balance
                          </p>
                          <p className="font-medium">
                            {formatMoney(bill.balance_due, currency)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}

