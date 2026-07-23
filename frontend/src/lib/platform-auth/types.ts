export interface PlatformUser {
  id: string
  username: string
  email: string
  first_name: string
  last_name: string
  full_name: string
  is_active: boolean
  is_super_admin: boolean
  must_change_password: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface PlatformTokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: PlatformUser
}

export interface PlatformSessionPayload {
  user: PlatformUser
}

export interface PlatformApiErrorBody {
  error?: {
    code?: string
    message?: string
  }
  detail?: string
}

export type FarmLifecycleStatus =
  | "ACTIVE"
  | "SUSPENDED"
  | "DEACTIVATED"

export interface PlatformFarmListResponse {
  items: unknown[]
  total: number
  offset: number
  limit: number
  recent_login_window_days: number
}
