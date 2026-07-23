import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  BackendUnavailableError,
} from "@/lib/auth/upstream"
import {
  attachPlatformAuthCookies,
  clearPlatformAuthCookies,
} from "@/lib/platform-auth/cookies"
import {
  PLATFORM_ACCESS_TOKEN_COOKIE,
  PLATFORM_REFRESH_TOKEN_COOKIE,
} from "@/lib/platform-auth/constants"
import {
  loadPlatformSessionWithAccessToken,
} from "@/lib/platform-auth/session"
import type {
  PlatformTokenResponse,
} from "@/lib/platform-auth/types"
import {
  refreshPlatformTokenPair,
} from "@/lib/platform-auth/upstream"

function unauthorized(): NextResponse {
  const response = NextResponse.json(
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
  clearPlatformAuthCookies(response)
  return response
}

export async function GET(
  request: NextRequest,
): Promise<NextResponse> {
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
      return unauthorized()
    }

    let lookup =
      await loadPlatformSessionWithAccessToken(
        accessToken,
      )

    if (
      lookup.status === 401 &&
      refreshToken
    ) {
      rotated = await refreshPlatformTokenPair(
        refreshToken,
        request.headers.get("user-agent"),
      )

      if (rotated) {
        lookup =
          await loadPlatformSessionWithAccessToken(
            rotated.access_token,
          )
      }
    }

    if (
      !lookup.session ||
      !lookup.session.user.is_super_admin
    ) {
      return unauthorized()
    }

    const response = NextResponse.json(
      lookup.session,
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    )

    if (rotated) {
      attachPlatformAuthCookies(
        response,
        rotated,
      )
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
