export interface Permission {
  id: string
  code: string
  module: string
  name: string
  description: string | null
}

export interface Role {
  id: string
  farm_id: string
  name: string
  description: string | null
  is_system_role: boolean
  is_active: boolean
  permissions: Permission[]
}

export interface AuthenticatedUser {
  id: string
  farm_id: string
  username: string
  email: string | null
  telephone: string | null
  first_name: string
  last_name: string
  full_name: string
  is_active: boolean
  is_verified: boolean
  must_change_password: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
  roles: Role[]
}

export interface FarmSettings {
  id: string
  farm_id: string
  eggs_per_tray: number
  low_production_threshold: string
  mortality_alert_threshold: string
  vaccination_reminder_days: number
  session_timeout_minutes: number
  allow_negative_stock: boolean
  allow_customer_credit: boolean
  maximum_discount_percentage: string
  created_at: string
  updated_at: string
}

export interface Farm {
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
  created_at: string
  updated_at: string
  settings: FarmSettings | null
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: AuthenticatedUser
}

export interface SessionPayload {
  user: AuthenticatedUser
  farm: Farm
  permissions: string[]
  roles: string[]
}

export interface ApiErrorBody {
  error?: {
    code?: string
    message?: string
    path?: string
  }
  detail?: unknown
}
