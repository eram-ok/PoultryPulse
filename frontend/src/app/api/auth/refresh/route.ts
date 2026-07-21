import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  attachAuthCookies,
  clearAuthCookies,
} from "@/lib/auth/cookies"
import { REFRESH_TOKEN_COOKIE } from "@/lib/auth/constants"
import { safeReturnTo } from "@/lib/auth/security"
import {
  BackendUnavailableError,
  refreshTokenPair,
} from "@/lib/auth/upstream"

function loginRedirect(
  request: NextRequest,
  reason: string,
): NextResponse {
  const response = NextResponse.redirect(
    new URL(`/login?reason=${reason}`, request.url),
  )
  clearAuthCookies(response)
  return response
}

export async function GET(
  request: NextRequest,
): Promise<NextResponse> {
  const returnTo = safeReturnTo(
    request.nextUrl.searchParams.get("returnTo"),
  )
  const refreshToken =
    request.cookies.get(REFRESH_TOKEN_COOKIE)?.value

  if (!refreshToken) {
    return loginRedirect(request, "session-expired")
  }

  try {
    const tokens = await refreshTokenPair(
      refreshToken,
      request.headers.get("user-agent"),
    )

    if (!tokens) {
      return loginRedirect(request, "session-expired")
    }

    const destination =
      tokens.user.must_change_password
        ? "/change-password"
        : returnTo
    const response = NextResponse.redirect(
      new URL(destination, request.url),
    )

    attachAuthCookies(response, tokens)
    return response
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return loginRedirect(request, "api-unavailable")
    }

    throw error
  }
}
