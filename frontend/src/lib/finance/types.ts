export type SupplierType =
  | "BIRD_SUPPLIER"
  | "FEED_SUPPLIER"
  | "MEDICINE_SUPPLIER"
  | "EQUIPMENT_SUPPLIER"
  | "GENERAL_SUPPLIER"

export type ExpenseCategoryKind =
  | "FEED"
  | "VETERINARY"
  | "LABOUR"
  | "UTILITIES"
  | "TRANSPORT"
  | "EQUIPMENT"
  | "MAINTENANCE"
  | "HOUSING"
  | "ADMINISTRATION"
  | "BIOSECURITY"
  | "OTHER"

export type FinanceDocumentStatus = "DRAFT" | "POSTED" | "VOIDED"
export type SupplierBillStatus =
  | "UNPAID"
  | "PARTIALLY_PAID"
  | "PAID"
  | "VOIDED"
export type FinancePaymentMethod =
  | "CASH"
  | "MOBILE_MONEY"
  | "BANK_TRANSFER"
  | "CHEQUE"
  | "OTHER"
export type FinancePaymentStatus = "POSTED" | "REVERSED"
export type CashFlowDirection = "INFLOW" | "OUTFLOW"
export type CashLedgerEntryType =
  | "OPENING_BALANCE"
  | "SALES_RECEIPT"
  | "EXPENSE_PAYMENT"
  | "SUPPLIER_BILL_PAYMENT"
  | "OTHER_INCOME"
  | "ADJUSTMENT"
  | "REVERSAL"

export interface Paginated<T> {
  items: T[]
  total: number
  offset: number
  limit: number
}

export interface Supplier {
  id: string
  farm_id: string
  supplier_code: string
  name: string
  supplier_type: SupplierType
  telephone: string | null
  email: string | null
  address: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface ExpenseCategory {
  id: string
  farm_id: string
  category_code: string
  name: string
  kind: ExpenseCategoryKind
  description: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Expense {
  id: string
  farm_id: string
  category_id: string
  category_code: string
  category_name: string
  supplier_id: string | null
  supplier_name: string | null
  expense_number: string
  expense_date: string
  description: string
  amount: string
  payment_method: FinancePaymentMethod
  reference_number: string | null
  status: FinanceDocumentStatus
  notes: string | null
  void_reason: string | null
  is_posted: boolean
  is_voided: boolean
  created_at: string
  updated_at: string
}

export interface SupplierBill {
  id: string
  farm_id: string
  supplier_id: string
  supplier_code: string
  supplier_name: string
  feed_purchase_id: string | null
  bill_number: string
  supplier_invoice_number: string | null
  bill_date: string
  due_date: string | null
  description: string
  subtotal: string
  tax_amount: string
  total_amount: string
  amount_paid: string
  balance_due: string
  status: SupplierBillStatus
  notes: string | null
  void_reason: string | null
  is_paid: boolean
  is_voided: boolean
  created_at: string
  updated_at: string
}

export interface SupplierPayment {
  id: string
  farm_id: string
  supplier_id: string
  supplier_code: string
  supplier_name: string
  supplier_bill_id: string
  bill_number: string
  payment_number: string
  payment_date: string
  amount: string
  method: FinancePaymentMethod
  reference_number: string | null
  status: FinancePaymentStatus
  notes: string | null
  reversal_reason: string | null
  is_reversed: boolean
  created_at: string
}

export interface CashLedgerEntry {
  id: string
  farm_id: string
  entry_date: string
  entry_type: CashLedgerEntryType
  direction: CashFlowDirection
  amount: string
  signed_amount: string
  balance_after: string
  description: string
  expense_id: string | null
  supplier_bill_payment_id: string | null
  sale_payment_id: string | null
  source_type: string | null
  source_id: string | null
  created_at: string
}

export interface CashLedgerList extends Paginated<CashLedgerEntry> {
  current_balance: string
}

export interface FinanceSummary {
  as_of_date: string
  current_cash_balance: string
  outstanding_supplier_payables: string
  posted_expenses: string
  sales_receipts: string
  net_cash_flow: string
}

export interface SupplierStatement {
  supplier_id: string
  supplier_code: string
  supplier_name: string
  date_from: string | null
  date_to: string | null
  total_billed: string
  total_paid: string
  outstanding_balance: string
  bills: SupplierBill[]
  payments: SupplierPayment[]
}

export interface SalesReceiptSync {
  receipts_created: number
  reversals_created: number
  current_balance: string
}
