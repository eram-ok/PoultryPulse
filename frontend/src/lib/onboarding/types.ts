export type FarmInvitationStatus =
  | "PENDING"
  | "ACCEPTED"
  | "REVOKED"
  | "EXPIRED"

export interface FarmInvitationPublicResponse {
  farm_name: string
  farm_code: string
  administrator_name: string
  administrator_username: string
  status: FarmInvitationStatus
  expires_at: string
}

export interface FarmInvitationAcceptResponse {
  farm_code: string
  administrator_username: string
  accepted_at: string
  message: string
}

export interface OnboardingApiErrorBody {
  error?: {
    code?: string
    message?: string
  }
  detail?: string
}
