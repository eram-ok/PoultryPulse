export interface AdminPermission {
  id: string
  code: string
  module: string
  name: string
  description: string | null
}

export interface AdminRole {
  id: string
  farm_id: string
  name: string
  description: string | null
  is_system_role: boolean
  is_active: boolean
  permissions: AdminPermission[]
}

export interface AdminUser {
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
  roles: AdminRole[]
}

export interface AdminUserList {
  items: AdminUser[]
  total: number
  offset: number
  limit: number
}

export interface AdminUserCreate {
  username: string
  email: string | null
  telephone: string | null
  password: string
  first_name: string
  last_name: string
  role_ids: string[]
  must_change_password: boolean
}

export interface AdminUserUpdate {
  email: string | null
  telephone: string | null
  first_name: string
  last_name: string
  is_verified: boolean
  must_change_password: boolean
}
