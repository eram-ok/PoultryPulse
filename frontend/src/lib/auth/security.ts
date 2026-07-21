import type { NextRequest } from "next/server"

const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"])

export function requestChangesState(
  request: Request,
): boolean {
  return !SAFE_METHODS.has(request.method.toUpperCase())
}

export function isSameOriginBrowserRequest(
  request: NextRequest,
): boolean {
  const fetchSite = request.headers.get("sec-fetch-site")

  if (
    fetchSite &&
    !["same-origin", "same-site", "none"].includes(
      fetchSite.toLowerCase(),
    )
  ) {
    return false
  }

  const origin = request.headers.get("origin")

  if (!origin) {
    return true
  }

  return origin === request.nextUrl.origin
}

export function safeReturnTo(
  candidate: string | null,
  fallback = "/dashboard",
): string {
  if (
    !candidate ||
    !candidate.startsWith("/") ||
    candidate.startsWith("//") ||
    candidate.includes("\\")
  ) {
    return fallback
  }

  return candidate
}
