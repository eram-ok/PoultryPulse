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
  loadSessionWithAccessToken,
} from "@/lib/auth/session"
import {
  BackendUnavailableError,
  refreshTokenPair,
} from "@/lib/auth/upstream"

export async function GET(
  request: NextRequest,
): Promise<NextResponse> {
  let accessToken =
    request.cookies.get(ACCESS_TOKEN_COOKIE)?.value ??
    null
  const refreshToken =
    request.cookies.get(REFRESH_TOKEN_COOKIE)?.value ??
    null
  let rotated = null

  try {
    if (!accessToken && refreshToken) {
      rotated = await refreshTokenPair(
        refreshToken,
        request.headers.get("user-agent"),
      )
      accessToken = rotated?.access_token ?? null
    }

    if (!accessToken) {
      const response = NextResponse.json(
        {
          error: {
            code: "frontend_session_expired",
            message:
              "Your PoultryPulse session has expired.",
          },
        },
        { status: 401 },
      )
      clearAuthCookies(response)
      return response
    }

    let lookup =
      await loadSessionWithAccessToken(accessToken)

    if (
      lookup.status === 401 &&
      refreshToken &&
      !rotated
    ) {
      rotated = await refreshTokenPair(
        refreshToken,
        request.headers.get("user-agent"),
      )

      if (rotated) {
        lookup = await loadSessionWithAccessToken(
          rotated.access_token,
        )
      }
    }

    if (!lookup.session) {
      const response = NextResponse.json(
        {
          error: {
            code: "frontend_session_expired",
            message:
              "Your PoultryPulse session has expired.",
          },
        },
        { status: lookup.status || 401 },
      )

      if (lookup.status === 401) {
        clearAuthCookies(response)
      }

      return response
    }

    const response = NextResponse.json(lookup.session, {
      headers: {
        "Cache-Control": "no-store",
      },
    })

    if (rotated) {
      attachAuthCookies(response, rotated)
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
