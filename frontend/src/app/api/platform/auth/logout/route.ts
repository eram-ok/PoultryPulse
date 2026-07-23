import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  isSameOriginBrowserRequest,
} from "@/lib/auth/security"
import {
  backendFetch,
} from "@/lib/auth/upstream"
import {
  clearPlatformAuthCookies,
} from "@/lib/platform-auth/cookies"
import {
  PLATFORM_REFRESH_TOKEN_COOKIE,
} from "@/lib/platform-auth/constants"

export async function POST(
  request: NextRequest,
): Promise<NextResponse> {
  if (!isSameOriginBrowserRequest(request)) {
    return NextResponse.json(
      {
        error: {
          code: "invalid_request_origin",
          message:
            "This platform logout request did not originate from PoultryPulse.",
        },
      },
      { status: 403 },
    )
  }

  const refreshToken =
    request.cookies.get(
      PLATFORM_REFRESH_TOKEN_COOKIE,
    )?.value

  if (refreshToken) {
    try {
      await backendFetch(
        "/platform/auth/logout",
        {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type":
              "application/json",
          },
          body: JSON.stringify({
            refresh_token: refreshToken,
          }),
        },
      )
    } catch {
      // Local cookie removal remains authoritative.
    }
  }

  const response = new NextResponse(null, {
    status: 204,
  })
  clearPlatformAuthCookies(response)
  return response
}
