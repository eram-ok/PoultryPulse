export interface PaginatedResponse<T> {
  items: T[]
  total: number
  offset: number
  limit: number
}

export type PoultryHouseStatus =
  | "ACTIVE"
  | "INACTIVE"
  | "UNDER_MAINTENANCE"
  | "CLOSED"

export interface PoultryHouse {
  id: string
  farm_id: string
  house_code: string
  name: string
  capacity: number
  location: string | null
  description: string | null
  status: PoultryHouseStatus
  created_at: string
  updated_at: string
}

export type PoultryHouseListResponse =
  PaginatedResponse<PoultryHouse>

export interface PoultryHouseCreate {
  house_code: string
  name: string
  capacity: number
  location: string | null
  description: string | null
  status: PoultryHouseStatus
}

export type PoultryHouseUpdate =
  Partial<PoultryHouseCreate>

export type FlockStatus =
  | "PLANNED"
  | "ACTIVE"
  | "SUSPENDED"
  | "DEPLETED"
  | "SOLD"
  | "ARCHIVED"

export type FlockProductionStage =
  | "BROODING"
  | "GROWING"
  | "POINT_OF_LAY"
  | "LAYING"
  | "MOLTING"
  | "DEPLETED"
  | "SOLD"

export interface Flock {
  id: string
  farm_id: string
  house_id: string
  house_code: string
  house_name: string
  house_capacity: number
  supplier_id: string | null
  supplier_code: string | null
  supplier_name: string | null
  flock_code: string
  name: string
  breed: string
  arrival_date: string
  hatch_date: string | null
  age_at_arrival_days: number | null
  initial_population: number
  current_population: number
  purchase_cost: string
  production_stage: FlockProductionStage
  status: FlockStatus
  notes: string | null
  created_at: string
  updated_at: string
}

export type FlockListResponse =
  PaginatedResponse<Flock>

export interface FlockCreate {
  house_id: string
  supplier_id: string | null
  flock_code: string
  name: string
  breed: string
  arrival_date: string
  hatch_date: string | null
  age_at_arrival_days: number | null
  initial_population: number
  purchase_cost: string
  production_stage: FlockProductionStage
  notes: string | null
}

export interface FlockUpdate {
  house_id?: string
  supplier_id?: string | null
  flock_code?: string
  name?: string
  breed?: string
  purchase_cost?: string
  production_stage?: FlockProductionStage
  status?: FlockStatus
  notes?: string | null
}

export type PopulationTransactionType =
  | "INITIAL_PLACEMENT"
  | "TRANSFER_IN"
  | "TRANSFER_OUT"
  | "MORTALITY"
  | "CULLING"
  | "BIRD_SALE"
  | "ADJUSTMENT_IN"
  | "ADJUSTMENT_OUT"
  | "REVERSAL"

export interface PopulationTransaction {
  id: string
  farm_id: string
  flock_id: string
  transaction_date: string
  transaction_type: PopulationTransactionType
  quantity: number
  signed_quantity: number
  source_type: string
  source_id: string | null
  description: string | null
  created_by: string
  reversed_transaction_id: string | null
  created_at: string
}

export type PopulationTransactionListResponse =
  PaginatedResponse<PopulationTransaction>

export interface PopulationSummary {
  flock_id: string
  flock_code: string
  house_id: string
  house_code: string
  initial_population: number
  current_population: number
  house_capacity: number
  house_occupancy: number
  available_house_capacity: number
}

export type AlertStatus =
  | "OPEN"
  | "ACKNOWLEDGED"
  | "RESOLVED"

export type AlertSeverity =
  | "INFO"
  | "WARNING"
  | "CRITICAL"

export type AlertType =
  | "LOW_FEED_STOCK"
  | "OVERDUE_VACCINATION"
  | "HEALTH_INCIDENT"
  | "HIGH_MORTALITY"
  | "OVERDUE_SUPPLIER_BILL"
  | "CUSTOMER_CREDIT_LIMIT"
  | "NEGATIVE_CASH_BALANCE"

export interface PersistentAlert {
  id: string
  farm_id: string
  fingerprint: string
  alert_type: AlertType
  severity: AlertSeverity
  status: AlertStatus
  title: string
  message: string
  source_module: string
  source_id: string | null
  action_path: string | null
  assigned_to: string | null
  first_detected_at: string
  last_detected_at: string
  occurrence_count: number
  acknowledged_by: string | null
  acknowledged_at: string | null
  resolved_by: string | null
  resolved_at: string | null
  resolution_notes: string | null
  is_read: boolean
  is_dismissed: boolean
  created_at: string
  updated_at: string
}

export type PersistentAlertListResponse =
  PaginatedResponse<PersistentAlert>

export interface AlertCounts {
  total_active: number
  unread: number
  open: number
  acknowledged: number
  critical: number
  assigned_to_me: number
}

export interface AlertEvent {
  id: string
  alert_id: string
  actor_user_id: string | null
  event_type: string
  from_status: AlertStatus | null
  to_status: AlertStatus | null
  notes: string | null
  created_at: string
}

export interface AlertEventListResponse {
  items: AlertEvent[]
  total: number
}

export interface AlertRefreshResponse {
  run_id: string
  detected_count: number
  created_count: number
  updated_count: number
  resolved_count: number
  deliveries_queued: number
  deliveries_sent: number
  deliveries_failed: number
}
