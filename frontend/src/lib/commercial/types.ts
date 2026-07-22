export type CustomerStatus = "ACTIVE" | "INACTIVE" | "BLOCKED"
export type SaleStatus =
  | "DRAFT"
  | "CONFIRMED"
  | "PARTIALLY_PAID"
  | "PAID"
  | "PARTIALLY_RETURNED"
  | "RETURNED"
  | "CANCELLED"
export type SalePaymentTerms = "CASH" | "CREDIT"
export type EggGrade =
  | "LARGE"
  | "MEDIUM"
  | "SMALL"
  | "DAMAGED"
  | "REJECTED"
export type EggSaleUnit = "PIECE" | "TRAY" | "CRATE"
export type PaymentMethod =
  | "CASH"
  | "MOBILE_MONEY"
  | "BANK_TRANSFER"
  | "CHEQUE"
  | "OTHER"
export type PaymentStatus = "POSTED" | "REVERSED"
export type SaleReturnStatus = "POSTED" | "REVERSED"

export interface Paginated<T> {
  items: T[]
  total: number
  offset: number
  limit: number
}

export interface Customer {
  id: string
  farm_id: string
  customer_code: string
  name: string
  phone_number: string | null
  email: string | null
  address: string | null
  tax_number: string | null
  contact_person: string | null
  credit_limit: string
  opening_balance: string
  current_balance: string
  available_credit: string
  status: CustomerStatus
  is_active: boolean
  notes: string | null
  created_at: string
  updated_at: string
}

export interface CustomerCreatePayload {
  customer_code: string
  name: string
  phone_number: string | null
  email: string | null
  address: string | null
  tax_number: string | null
  contact_person: string | null
  credit_limit: string
  opening_balance: string
  notes: string | null
}

export interface CustomerUpdatePayload
  extends Partial<Omit<CustomerCreatePayload, "opening_balance">> {
  status?: CustomerStatus
}

export interface CustomerLedgerEntry {
  id: string
  entry_date: string
  entry_type: string
  description: string
  debit_amount: string
  credit_amount: string
  balance_after: string
  created_at: string
}

export interface CustomerStatement {
  customer: Customer
  date_from: string | null
  date_to: string | null
  opening_balance: string
  closing_balance: string
  entries: CustomerLedgerEntry[]
}

export interface SaleItem {
  id: string
  egg_grade: EggGrade
  unit: EggSaleUnit
  eggs_per_unit: number
  quantity: number
  quantity_returned: number
  remaining_returnable_quantity: number
  unit_price: string
  line_total: string
  total_eggs: number
  notes: string | null
  created_at: string
}

export interface Sale {
  id: string
  farm_id: string
  customer_id: string
  customer_code: string
  customer_name: string
  invoice_number: string
  sale_date: string
  due_date: string | null
  payment_terms: SalePaymentTerms
  status: SaleStatus
  subtotal: string
  discount_amount: string
  tax_amount: string
  total_amount: string
  amount_paid: string
  balance_due: string
  is_paid: boolean
  is_cancelled: boolean
  is_confirmed: boolean
  notes: string | null
  items: SaleItem[]
  cancellation_reason: string | null
  created_at: string
  updated_at: string
}

export interface SaleItemPayload {
  egg_grade: EggGrade
  unit: EggSaleUnit
  eggs_per_unit: number | null
  quantity: number
  unit_price: string
  notes: string | null
}

export interface SaleCreatePayload {
  customer_id: string
  sale_date: string
  due_date: string | null
  payment_terms: SalePaymentTerms
  discount_amount: string
  tax_amount: string
  notes: string | null
  items: SaleItemPayload[]
}

export interface SalesSummary {
  as_of_date: string
  active_customers: number
  draft_sales: number
  confirmed_sales: number
  paid_sales: number
  outstanding_receivables: string
  gross_sales_value: string
  posted_payments: string
  posted_returns: string
  inventory_by_grade: Record<string, number>
}

export interface SalePayment {
  id: string
  customer_id: string
  customer_code: string
  customer_name: string
  sale_id: string
  invoice_number: string
  payment_number: string
  payment_date: string
  amount: string
  method: PaymentMethod
  reference_number: string | null
  status: PaymentStatus
  notes: string | null
  reversal_reason: string | null
  is_reversed: boolean
  created_at: string
}

export interface SaleReturnItem {
  id: string
  sale_item_id: string
  egg_grade: EggGrade
  unit: EggSaleUnit
  quantity: number
  unit_price: string
  line_total: string
  total_eggs: number
  reason: string | null
}

export interface SaleReturn {
  id: string
  sale_id: string
  invoice_number: string
  customer_id: string
  customer_code: string
  customer_name: string
  return_number: string
  return_date: string
  total_refund: string
  status: SaleReturnStatus
  reason: string
  notes: string | null
  reversal_reason: string | null
  is_reversed: boolean
  items: SaleReturnItem[]
  created_at: string
}

export interface PaymentPayload {
  sale_id: string
  payment_date: string
  amount: string
  method: PaymentMethod
  reference_number: string | null
  notes: string | null
}

export interface ReturnPayload {
  sale_id: string
  return_date: string
  reason: string
  notes: string | null
  items: Array<{
    sale_item_id: string
    quantity: number
    reason: string | null
  }>
}
