import type { PaginatedResponse } from "@/lib/api/operations"

export type ProductionStatus = "DRAFT" | "SUBMITTED" | "CONFIRMED" | "REJECTED" | "VOIDED"
export interface ProductionRecord {
  id: string; farm_id: string; flock_id: string; flock_code: string; flock_name: string
  house_id: string; house_code: string; production_date: string; birds_present: number
  morning_eggs: number; afternoon_eggs: number; evening_eggs: number; total_collected: number
  large_eggs: number; medium_eggs: number; small_eggs: number; damaged_eggs: number
  rejected_eggs: number; total_graded: number; saleable_eggs: number; ungraded_eggs: number
  laying_percentage: string; status: ProductionStatus; notes: string | null
  rejection_reason: string | null; revision_number: number; created_at: string; updated_at: string
}
export type ProductionListResponse = PaginatedResponse<ProductionRecord>
export interface ProductionSummary {
  date_from: string; date_to: string; status: ProductionStatus | null; record_count: number
  bird_days: number; morning_eggs: number; afternoon_eggs: number; evening_eggs: number
  total_collected: number; large_eggs: number; medium_eggs: number; small_eggs: number
  damaged_eggs: number; rejected_eggs: number; saleable_eggs: number
  weighted_laying_percentage: string
}

export type EggGrade = "LARGE" | "MEDIUM" | "SMALL" | "DAMAGED" | "REJECTED"
export type EggTransactionType = "PRODUCTION_IN" | "SALE_OUT" | "SALE_RETURN_IN" | "INTERNAL_USE_OUT" | "DONATION_OUT" | "DAMAGE_OUT" | "ADJUSTMENT_IN" | "ADJUSTMENT_OUT" | "REVERSAL"
export interface EggBalance { egg_grade: EggGrade; balance_eggs: number; trays: number; loose_eggs: number; eggs_per_tray: number; is_saleable: boolean }
export interface EggSummary { eggs_per_tray: number; balances: EggBalance[]; total_saleable_eggs: number; total_saleable_trays: number; total_saleable_loose_eggs: number; total_non_saleable_eggs: number; total_all_eggs: number }
export interface EggTransaction { id: string; inventory_date: string; egg_grade: EggGrade; transaction_type: EggTransactionType; quantity: number; signed_quantity: number; direction: string; source_type: string; source_id: string | null; reference: string | null; description: string | null; reversed_transaction_id: string | null; is_reversal: boolean; created_at: string }
export type EggTransactionListResponse = PaginatedResponse<EggTransaction>

export type FeedCategory = "CHICK_STARTER" | "GROWERS_MASH" | "LAYERS_MASH" | "BROILER_STARTER" | "BROILER_FINISHER" | "CONCENTRATE" | "SUPPLEMENT" | "OTHER"
export interface FeedItem { id: string; feed_code: string; name: string; category: FeedCategory; brand: string | null; manufacturer: string | null; description: string | null; reorder_level_kg: string; is_active: boolean; created_at: string; updated_at: string }
export type FeedItemListResponse = PaginatedResponse<FeedItem>
export interface FeedBalance { feed_item_id: string; feed_code: string; feed_name: string; category: FeedCategory; balance_kg: string; reorder_level_kg: string; is_low_stock: boolean; is_out_of_stock: boolean; is_active: boolean }
export interface FeedSummary { balances: FeedBalance[]; total_feed_kg: string; active_feed_items: number; low_stock_items: number; out_of_stock_items: number }
export interface FeedPurchase { id: string; feed_item_id: string; feed_code: string; feed_name: string; supplier_id: string | null; supplier_code: string | null; supplier_name: string | null; purchase_date: string; invoice_number: string | null; quantity_kg: string; unit_cost: string; total_cost: string; status: "RECEIVED" | "VOIDED"; notes: string | null; created_at: string }
export type FeedPurchaseListResponse = PaginatedResponse<FeedPurchase>
export interface FeedUsage { id: string; flock_id: string; flock_code: string; flock_name: string; feed_item_id: string; feed_code: string; feed_name: string; usage_date: string; feeding_period: "MORNING" | "AFTERNOON" | "EVENING" | "OTHER"; quantity_kg: string; birds_present: number; grams_per_bird: string; notes: string | null; created_at: string }
export type FeedUsageListResponse = PaginatedResponse<FeedUsage>
export interface FeedTransaction { id: string; feed_item_id: string; feed_code: string; feed_name: string; inventory_date: string; transaction_type: string; quantity_kg: string; signed_quantity_kg: string; direction: string; source_type: string; reference: string | null; description: string | null; is_reversal: boolean; created_at: string }
export type FeedTransactionListResponse = PaginatedResponse<FeedTransaction>
