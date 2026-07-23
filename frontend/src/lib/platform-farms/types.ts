import type { FarmLifecycleStatus } from "@/lib/platform-auth/types"

export type FarmInvitationStatus = "PENDING" | "ACCEPTED" | "REVOKED" | "EXPIRED"
export type FarmInvitationDeliveryStatus =
  | "NOT_CONFIGURED"
  | "PENDING"
  | "SENT"
  | "FAILED"

export interface PlatformFarmSummary {
  id: string
  farm_code: string
  name: string
  owner_name: string | null
  telephone: string | null
  email: string | null
  district: string | null
  address: string | null
  logo_url: string | null
  timezone: string
  currency_code: string
  is_active: boolean
  lifecycle_status: FarmLifecycleStatus
  lifecycle_reason: string | null
  lifecycle_changed_at: string
  lifecycle_changed_by_platform_user_id: string | null
  suspended_at: string | null
  deactivated_at: string | null
  created_at: string
  updated_at: string
  total_users: number
  active_users: number
  recent_login_users: number
  active_refresh_sessions: number
  last_login_at: string | null
}

export interface PlatformFarmSettings {
  id: string
  farm_id: string
  eggs_per_tray: number
  low_production_threshold: string | number
  mortality_alert_threshold: string | number
  vaccination_reminder_days: number
  session_timeout_minutes: number
  allow_negative_stock: boolean
  allow_customer_credit: boolean
  maximum_discount_percentage: string | number
  created_at: string
  updated_at: string
}

export interface PlatformFarmDetail extends PlatformFarmSummary {
  settings: PlatformFarmSettings | null
}

export interface PlatformFarmListResponse {
  items: PlatformFarmSummary[]
  total: number
  offset: number
  limit: number
  recent_login_window_days: number
}

export interface PlatformFarmInvitation {
  id: string
  farm_id: string
  administrator_user_id: string
  issued_by_platform_user_id: string | null
  status: FarmInvitationStatus
  expires_at: string
  accepted_at: string | null
  revoked_at: string | null
  delivery_status: FarmInvitationDeliveryStatus
  delivery_attempt_count: number
  last_delivery_attempt_at: string | null
  last_delivery_error: string | null
  sent_at: string | null
  idempotency_key: string | null
  created_at: string
  updated_at: string
}

export interface PlatformFarmOnboardingStatus {
  farm_id: string
  administrator_user_id: string | null
  administrator_username: string | null
  administrator_email: string | null
  administrator_is_active: boolean | null
  administrator_is_verified: boolean | null
  completed: boolean
  legacy_completed: boolean
  invitation: PlatformFarmInvitation | null
}

export interface PlatformFarmAdministrator {
  id: string
  farm_id: string
  username: string
  email: string | null
  telephone: string | null
  first_name: string
  last_name: string
  is_active: boolean
  is_verified: boolean
  must_change_password: boolean
}

export interface PlatformFarmInvitationIssue {
  invitation: PlatformFarmInvitation
  setup_url: string | null
  setup_url_returned_once: boolean
}

export interface PlatformFarmCreateResponse {
  farm: PlatformFarmDetail
  administrator: PlatformFarmAdministrator
  invitation: PlatformFarmInvitation
  setup_url: string | null
  setup_url_returned_once: boolean
  idempotent_replay: boolean
}

export interface PlatformFarmCreatePayload {
  farm_code: string
  name: string
  owner_name: string | null
  telephone: string | null
  email: string | null
  district: string | null
  address: string | null
  logo_url: string | null
  timezone: string
  currency_code: string
  settings: {
    eggs_per_tray: number
    low_production_threshold: number
    mortality_alert_threshold: number
    vaccination_reminder_days: number
    session_timeout_minutes: number
    allow_negative_stock: boolean
    allow_customer_credit: boolean
    maximum_discount_percentage: number
  }
  first_administrator: {
    username: string
    email: string
    telephone: string | null
    first_name: string
    last_name: string
  }
}
