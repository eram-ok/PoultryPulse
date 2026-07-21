const DEFAULT_BACKEND_BASE_URL =
  "http://127.0.0.1:8000/api/v1"

function normalizeBaseUrl(value: string): string {
  return value.replace(/\/+$/, "")
}

export function getBackendBaseUrl(): string {
  return normalizeBaseUrl(
    process.env.POULTRYPULSE_API_BASE_URL ??
      process.env.NEXT_PUBLIC_API_BASE_URL ??
      DEFAULT_BACKEND_BASE_URL,
  )
}

export function getBackendRequestTimeoutMs(): number {
  const configured = Number(
    process.env.AUTH_BACKEND_TIMEOUT_MS ?? "10000",
  )

  if (!Number.isFinite(configured) || configured < 1000) {
    return 10000
  }

  return Math.floor(configured)
}

export function getRefreshCookieMaxAge(): number {
  const configured = Number(
    process.env.AUTH_REFRESH_COOKIE_MAX_AGE_SECONDS ??
      "2592000",
  )

  if (!Number.isFinite(configured) || configured < 3600) {
    return 2592000
  }

  return Math.floor(configured)
}

export function shouldUseSecureCookies(): boolean {
  const configured = process.env.AUTH_COOKIE_SECURE

  if (configured !== undefined) {
    return configured.trim().toLowerCase() === "true"
  }

  return process.env.NODE_ENV === "production"
}
