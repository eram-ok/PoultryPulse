import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  isSameOriginBrowserRequest,
  requestChangesState,
} from "@/lib/auth/security"
import {
  BackendUnavailableError,
  backendFetch,
  toNextResponse,
} from "@/lib/auth/upstream"
import {
  attachPlatformAuthCookies,
  clearPlatformAuthCookies,
} from "@/lib/platform-auth/cookies"
import {
  PLATFORM_ACCESS_TOKEN_COOKIE,
  PLATFORM_REFRESH_TOKEN_COOKIE,
} from "@/lib/platform-auth/constants"
import type {
  PlatformTokenResponse,
} from "@/lib/platform-auth/types"
import {
  refreshPlatformTokenPair,
} from "@/lib/platform-auth/upstream"

function unauthorizedResponse(): NextResponse {
  return NextResponse.json(
    {
      error: {
        code: "platform_frontend_session_expired",
        message:
          "Your PoultryPulse platform session has expired.",
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
          "This platform request did not originate from PoultryPulse.",
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
    "idempotency-key",
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
    headers: upstreamHeaders(
      request,
      accessToken,
    ),
    body,
    redirect: "manual",
  })
}

async function refreshedTokens(
  request: NextRequest,
): Promise<PlatformTokenResponse | null> {
  const refreshToken =
    request.cookies.get(
      PLATFORM_REFRESH_TOKEN_COOKIE,
    )?.value

  if (!refreshToken) {
    return null
  }

  return refreshPlatformTokenPair(
    refreshToken,
    request.headers.get("user-agent"),
  )
}

export async function forwardPlatformAuthenticatedRequest(
  request: NextRequest,
  path: string,
): Promise<NextResponse> {
  if (!path.startsWith("/platform/")) {
    return NextResponse.json(
      {
        error: {
          code: "invalid_platform_api_path",
          message:
            "Only platform administration APIs are available through this route.",
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
    request.cookies.get(
      PLATFORM_ACCESS_TOKEN_COOKIE,
    )?.value ?? null
  let rotatedTokens:
    | PlatformTokenResponse
    | null = null

  try {
    if (!accessToken) {
      rotatedTokens = await refreshedTokens(request)
      accessToken =
        rotatedTokens?.access_token ?? null
    }

    if (!accessToken) {
      const response = unauthorizedResponse()
      clearPlatformAuthCookies(response)
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
        clearPlatformAuthCookies(response)
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
      attachPlatformAuthCookies(
        response,
        rotatedTokens,
      )
    }

    if (upstream.status === 401) {
      clearPlatformAuthCookies(response)
    }

    return response
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return unavailableResponse()
    }

    throw error
  }
}
