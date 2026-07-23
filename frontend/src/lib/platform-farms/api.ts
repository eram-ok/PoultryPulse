import type { PlatformApiErrorBody } from "@/lib/platform-auth/types"

export class PlatformFarmApiError extends Error {
  readonly status: number
  readonly code: string | null

  constructor(message: string, status: number, code: string | null = null) {
    super(message)
    this.name = "PlatformFarmApiError"
    this.status = status
    this.code = code
  }
}

async function readJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") ?? ""
  if (response.status === 204 || !contentType.includes("application/json")) {
    return null
  }
  try {
    return await response.json()
  } catch {
    return null
  }
}

export async function platformFarmRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  if (!path.startsWith("/platform/")) {
    throw new Error("Platform farm requests must target a platform API path.")
  }

  const response = await fetch(`/api/platform/backend${path}`, {
    credentials: "same-origin",
    cache: "no-store",
    ...init,
    headers: {
      Accept: "application/json",
      ...(init.headers ?? {}),
    },
  })
  const payload = await readJson(response)

  if (!response.ok) {
    const error = payload as PlatformApiErrorBody | null
    throw new PlatformFarmApiError(
      error?.error?.message ??
        error?.detail ??
        "The platform request could not be completed.",
      response.status,
      error?.error?.code ?? null,
    )
  }

  return payload as T
}

export function jsonRequestInit(
  method: "POST" | "PATCH",
  payload: unknown,
  extraHeaders?: HeadersInit,
): RequestInit {
  return {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(extraHeaders ?? {}),
    },
    body: JSON.stringify(payload),
  }
}

export function requiredText(value: FormDataEntryValue | null): string {
  return String(value ?? "").trim()
}

export function optionalText(value: FormDataEntryValue | null): string | null {
  const normalized = requiredText(value)
  return normalized || null
}

export function numberValue(
  value: FormDataEntryValue | null,
  fallback: number,
): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

export function formatPlatformDate(value: string | null): string {
  if (!value) return "Never"
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return "Unavailable"
  return new Intl.DateTimeFormat("en-UG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}
