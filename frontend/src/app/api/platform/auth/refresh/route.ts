import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  clearPlatformAuthCookies,
  attachPlatformAuthCookies,
} from "@/lib/platform-auth/cookies"
import {
  PLATFORM_REFRESH_TOKEN_COOKIE,
} from "@/lib/platform-auth/constants"
import {
  safePlatformReturnTo,
} from "@/lib/platform-auth/security"
import {
  refreshPlatformTokenPair,
} from "@/lib/platform-auth/upstream"
import {
  BackendUnavailableError,
} from "@/lib/auth/upstream"

function loginRedirect(
  request: NextRequest,
  reason: string,
): NextResponse {
  const response = NextResponse.redirect(
    new URL(
      `/platform/login?reason=${reason}`,
      request.url,
    ),
  )
  clearPlatformAuthCookies(response)
  return response
}

export async function GET(
  request: NextRequest,
): Promise<NextResponse> {
  const returnTo = safePlatformReturnTo(
    request.nextUrl.searchParams.get(
      "returnTo",
    ),
  )
  const refreshToken =
    request.cookies.get(
      PLATFORM_REFRESH_TOKEN_COOKIE,
    )?.value

  if (!refreshToken) {
    return loginRedirect(
      request,
      "session-expired",
    )
  }

  try {
    const tokens =
      await refreshPlatformTokenPair(
        refreshToken,
        request.headers.get("user-agent"),
      )

    if (!tokens) {
      return loginRedirect(
        request,
        "session-expired",
      )
    }

    if (!tokens.user.is_super_admin) {
      return loginRedirect(
        request,
        "super-admin-required",
      )
    }

    const destination =
      tokens.user.must_change_password
        ? "/platform/change-password"
        : returnTo
    const response = NextResponse.redirect(
      new URL(destination, request.url),
    )

    attachPlatformAuthCookies(
      response,
      tokens,
    )
    return response
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return loginRedirect(
        request,
        "api-unavailable",
      )
    }

    throw error
  }
}
