import { NextResponse } from "next/server"

import {
  getBackendBaseUrl,
  getBackendRequestTimeoutMs,
} from "@/lib/auth/config"
import type {
  ApiErrorBody,
  TokenResponse,
} from "@/lib/auth/types"

export class BackendUnavailableError extends Error {
  constructor(message = "PoultryPulse API is unavailable.") {
    super(message)
    this.name = "BackendUnavailableError"
  }
}

export function backendUrl(path: string): URL {
  const baseUrl = getBackendBaseUrl()
  const normalizedPath = path.replace(/^\/+/, "")

  return new URL(`${baseUrl}/${normalizedPath}`)
}

export async function backendFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  try {
    return await fetch(backendUrl(path), {
      ...init,
      cache: "no-store",
      signal:
        init.signal ??
        AbortSignal.timeout(getBackendRequestTimeoutMs()),
    })
  } catch (error) {
    throw new BackendUnavailableError(
      error instanceof Error
        ? `PoultryPulse API request failed: ${error.message}`
        : undefined,
    )
  }
}

export async function readJsonSafely<T>(
  response: Response,
): Promise<T | null> {
  try {
    return (await response.json()) as T
  } catch {
    return null
  }
}

export async function refreshTokenPair(
  refreshToken: string,
  userAgent?: string | null,
): Promise<TokenResponse | null> {
  const response = await backendFetch("/auth/refresh", {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
      ...(userAgent ? { "User-Agent": userAgent } : {}),
    },
    body: JSON.stringify({
      refresh_token: refreshToken,
    }),
  })

  if (!response.ok) {
    return null
  }

  return readJsonSafely<TokenResponse>(response)
}

export async function apiErrorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  const payload = await readJsonSafely<ApiErrorBody>(response)

  if (payload?.error?.message) {
    return payload.error.message
  }

  if (typeof payload?.detail === "string") {
    return payload.detail
  }

  return fallback
}

const FORWARDED_RESPONSE_HEADERS = [
  "content-type",
  "content-disposition",
  "etag",
  "last-modified",
  "cache-control",
] as const

export async function toNextResponse(
  upstream: Response,
): Promise<NextResponse> {
  const headers = new Headers()

  for (const name of FORWARDED_RESPONSE_HEADERS) {
    const value = upstream.headers.get(name)

    if (value) {
      headers.set(name, value)
    }
  }

  headers.set("Cache-Control", "no-store")

  if (
    upstream.status === 204 ||
    upstream.status === 304
  ) {
    return new NextResponse(null, {
      status: upstream.status,
      headers,
    })
  }

  return new NextResponse(await upstream.arrayBuffer(), {
    status: upstream.status,
    headers,
  })
}
