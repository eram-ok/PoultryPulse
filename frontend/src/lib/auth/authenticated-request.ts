import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  attachAuthCookies,
  clearAuthCookies,
} from "@/lib/auth/cookies"
import {
  ACCESS_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
} from "@/lib/auth/constants"
import {
  isSameOriginBrowserRequest,
  requestChangesState,
} from "@/lib/auth/security"
import {
  BackendUnavailableError,
  backendFetch,
  refreshTokenPair,
  toNextResponse,
} from "@/lib/auth/upstream"
import type { TokenResponse } from "@/lib/auth/types"

function unauthorizedResponse(): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "frontend_session_expired",
        message:
          "Your PoultryPulse session has expired. Sign in again.",
      },
    },
    {
      status: 401,
      headers: {
        "Cache-Control": "no-store",
      },
    },
  )
}

function forbiddenOriginResponse(): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "invalid_request_origin",
        message:
          "This request did not originate from PoultryPulse.",
      },
    },
    {
      status: 403,
      headers: {
        "Cache-Control": "no-store",
      },
    },
  )
}

function unavailableResponse(): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "backend_unavailable",
        message:
          "The PoultryPulse API is temporarily unavailable.",
      },
    },
    {
      status: 503,
      headers: {
        "Cache-Control": "no-store",
      },
    },
  )
}

function upstreamHeaders(
  request: NextRequest,
  accessToken: string,
): Headers {
  const headers = new Headers({
    Accept:
      request.headers.get("accept") ??
      "application/json",
    Authorization: `Bearer ${accessToken}`,
  })

  for (const name of [
    "content-type",
    "if-match",
    "if-none-match",
    "x-request-id",
  ]) {
    const value = request.headers.get(name)

    if (value) {
      headers.set(name, value)
    }
  }

  return headers
}

async function execute(
  request: NextRequest,
  path: string,
  accessToken: string,
  body: ArrayBuffer | undefined,
): Promise<Response> {
  return backendFetch(path, {
    method: request.method,
    headers: upstreamHeaders(request, accessToken),
    body,
    redirect: "manual",
  })
}

async function refreshedTokens(
  request: NextRequest,
): Promise<TokenResponse | null> {
  const refreshToken =
    request.cookies.get(REFRESH_TOKEN_COOKIE)?.value

  if (!refreshToken) {
    return null
  }

  return refreshTokenPair(
    refreshToken,
    request.headers.get("user-agent"),
  )
}

export async function forwardAuthenticatedRequest(
  request: NextRequest,
  path: string,
): Promise<NextResponse> {
  if (
    requestChangesState(request) &&
    !isSameOriginBrowserRequest(request)
  ) {
    return forbiddenOriginResponse()
  }

  const body = request.body
    ? await request.arrayBuffer()
    : undefined
  let accessToken =
    request.cookies.get(ACCESS_TOKEN_COOKIE)?.value ??
    null
  let rotatedTokens: TokenResponse | null = null

  try {
    if (!accessToken) {
      rotatedTokens = await refreshedTokens(request)
      accessToken = rotatedTokens?.access_token ?? null
    }

    if (!accessToken) {
      const response = unauthorizedResponse()
      clearAuthCookies(response)
      return response
    }

    let upstream = await execute(
      request,
      path,
      accessToken,
      body,
    )

    if (upstream.status === 401) {
      rotatedTokens = await refreshedTokens(request)

      if (!rotatedTokens) {
        const response = unauthorizedResponse()
        clearAuthCookies(response)
        return response
      }

      upstream = await execute(
        request,
        path,
        rotatedTokens.access_token,
        body,
      )
    }

    const response = await toNextResponse(upstream)

    if (rotatedTokens) {
      attachAuthCookies(response, rotatedTokens)
    }

    if (upstream.status === 401) {
      clearAuthCookies(response)
    }

    return response
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return unavailableResponse()
    }

    throw error
  }
}
