export type AuditAction =
  | "CREATE"
  | "VIEW"
  | "UPDATE"
  | "DELETE"
  | "ACTIVATE"
  | "DEACTIVATE"
  | "ASSIGN"
  | "REMOVE"
  | "SUBMIT"
  | "CONFIRM"
  | "REJECT"
  | "CANCEL"
  | "COMPLETE"
  | "RESOLVE"
  | "REOPEN"
  | "REVERSE"
  | "VOID"
  | "LOGIN"
  | "LOGIN_FAILED"
  | "LOGOUT"
  | "TOKEN_REFRESH"
  | "PASSWORD_CHANGE"
  | "EXPORT"
  | "PROCESS"
  | "SYNC"
  | "SYSTEM"

export type AuditOutcome = "SUCCESS" | "FAILURE" | "DENIED"
export type AuditSeverity = "INFO" | "WARNING" | "CRITICAL"

export interface AuditLog {
  id: string
  farm_id: string | null
  actor_user_id: string | null
  actor_username: string | null
  action: AuditAction
  outcome: AuditOutcome
  severity: AuditSeverity
  module: string
  resource_type: string | null
  resource_id: string | null
  description: string
  request_id: string | null
  request_method: string | null
  request_path: string | null
  ip_address: string | null
  user_agent: string | null
  before_values: Record<string, unknown> | null
  after_values: Record<string, unknown> | null
  changes: Record<string, unknown> | null
  metadata_json: Record<string, unknown> | null
  error_code: string | null
  error_message: string | null
  occurred_at: string
  created_at: string
}

export interface AuditLogList {
  items: AuditLog[]
  total: number
  offset: number
  limit: number
}

export interface AuditSummary {
  total: number
  successful: number
  failed: number
  critical: number
  unique_actors: number
}

export type BackgroundJobStatus = "RUNNING" | "SUCCESS" | "FAILURE"
export type BackgroundJobTrigger = "SCHEDULED" | "MANUAL"

export interface BackgroundJobDefinition {
  name: string
  enabled: boolean
  per_farm: boolean
  interval_seconds: number
}

export interface BackgroundJobDefinitionList {
  items: BackgroundJobDefinition[]
}

export interface BackgroundJobRun {
  id: string
  farm_id: string | null
  job_name: string
  status: BackgroundJobStatus
  trigger: BackgroundJobTrigger
  scheduled_for: string | null
  started_at: string
  completed_at: string | null
  duration_ms: number | null
  result_json: Record<string, unknown> | null
  error_type: string | null
  error_message: string | null
  worker_id: string
  created_at: string
}

export interface BackgroundJobRunList {
  items: BackgroundJobRun[]
  total: number
  offset: number
  limit: number
}
