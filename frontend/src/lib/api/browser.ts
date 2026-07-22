import type { ApiErrorBody } from "@/lib/auth/types"

export class BrowserApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message)
    this.name = "BrowserApiError"
  }
}

export async function browserApiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api/backend${path}`, {
    ...options,
    cache: "no-store",
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(options.body
        ? { "Content-Type": "application/json" }
        : {}),
      ...options.headers,
    },
  })

  if (response.status === 401) {
    window.location.assign(
      `/login?reason=session-expired&next=${encodeURIComponent(
        window.location.pathname,
      )}`,
    )

    throw new BrowserApiError(
      "Your session has expired.",
      401,
      "frontend_session_expired",
    )
  }

  if (!response.ok) {
    type FastApiValidationItem = {
      loc?: Array<string | number>
      msg?: string
      type?: string
    }

    type ErrorPayload = ApiErrorBody & {
      detail?: FastApiValidationItem[] | string
    }

    let payload: ErrorPayload | null = null

    try {
      payload = (await response.json()) as ErrorPayload
    } catch {
      payload = null
    }

    const validationMessage = Array.isArray(payload?.detail)
      ? payload.detail
          .map((item) => {
            const field = item.loc
              ?.filter((part) => part !== "body")
              .join(".")

            if (field && item.msg) {
              return `${field}: ${item.msg}`
            }

            return item.msg
          })
          .filter(Boolean)
          .join(" ")
      : typeof payload?.detail === "string"
        ? payload.detail
        : undefined

    throw new BrowserApiError(
      payload?.error?.message ??
        validationMessage ??
        "PoultryPulse could not complete this request.",
      response.status,
      payload?.error?.code,
    )
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
