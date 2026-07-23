import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  isSameOriginBrowserRequest,
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

interface ChangePasswordPayload {
  current_password?: string
  new_password?: string
}

async function changePassword(
  accessToken: string,
  payload: ChangePasswordPayload,
): Promise<Response> {
  return backendFetch(
    "/platform/auth/change-password",
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization:
          `Bearer ${accessToken}`,
      },
      body: JSON.stringify(payload),
    },
  )
}

export async function POST(
  request: NextRequest,
): Promise<NextResponse> {
  if (!isSameOriginBrowserRequest(request)) {
    return NextResponse.json(
      {
        error: {
          code: "invalid_request_origin",
          message:
            "This platform password request did not originate from PoultryPulse.",
        },
      },
      { status: 403 },
    )
  }

  let payload: ChangePasswordPayload

  try {
    payload =
      (await request.json()) as
        ChangePasswordPayload
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "invalid_password_payload",
          message:
            "Enter your current password and a new password.",
        },
      },
      { status: 400 },
    )
  }

  if (
    !payload.current_password ||
    !payload.new_password
  ) {
    return NextResponse.json(
      {
        error: {
          code: "missing_password_fields",
          message:
            "Enter your current password and a new password.",
        },
      },
      { status: 400 },
    )
  }

  let accessToken =
    request.cookies.get(
      PLATFORM_ACCESS_TOKEN_COOKIE,
    )?.value ?? null
  const refreshToken =
    request.cookies.get(
      PLATFORM_REFRESH_TOKEN_COOKIE,
    )?.value ?? null
  let rotated:
    | PlatformTokenResponse
    | null = null

  try {
    if (!accessToken && refreshToken) {
      rotated = await refreshPlatformTokenPair(
        refreshToken,
        request.headers.get("user-agent"),
      )
      accessToken =
        rotated?.access_token ?? null
    }

    if (!accessToken) {
      const response = NextResponse.json(
        {
          error: {
            code:
              "platform_frontend_session_expired",
            message:
              "Your PoultryPulse platform session has expired.",
          },
        },
        { status: 401 },
      )
      clearPlatformAuthCookies(response)
      return response
    }

    let upstream = await changePassword(
      accessToken,
      payload,
    )

    if (
      upstream.status === 401 &&
      refreshToken
    ) {
      rotated = await refreshPlatformTokenPair(
        refreshToken,
        request.headers.get("user-agent"),
      )

      if (rotated) {
        upstream = await changePassword(
          rotated.access_token,
          payload,
        )
      }
    }

    const response =
      await toNextResponse(upstream)

    if (rotated && !upstream.ok) {
      attachPlatformAuthCookies(
        response,
        rotated,
      )
    }

    if (
      upstream.ok ||
      upstream.status === 401
    ) {
      clearPlatformAuthCookies(response)
    }

    return response
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return NextResponse.json(
        {
          error: {
            code: "backend_unavailable",
            message:
              "The PoultryPulse API is temporarily unavailable.",
          },
        },
        { status: 503 },
      )
    }

    throw error
  }
}
