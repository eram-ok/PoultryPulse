import type { PlatformApiErrorBody } from "@/lib/platform-auth/types"

export async function platformFarmRequest<T>(
  path: string,
): Promise<T> {
  if (!path.startsWith("/platform/")) {
    throw new Error(
      "Platform farm requests must target a platform API path.",
    )
  }

  const response = await fetch(
    `/api/platform/backend${path}`,
    {
      credentials: "same-origin",
      cache: "no-store",
      headers: {
        Accept: "application/json",
      },
    },
  )

  let payload: unknown = null
  try {
    payload = await response.json()
  } catch {
    payload = null
  }

  if (!response.ok) {
    const error = payload as PlatformApiErrorBody | null
    throw new Error(
      error?.error?.message ??
        error?.detail ??
        "The platform request could not be completed.",
    )
  }

  return payload as T
}

export function formatPlatformDate(
  value: string | null,
): string {
  if (!value) {
    return "Never"
  }

  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "Unavailable"
  }

  return new Intl.DateTimeFormat("en-UG", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}
