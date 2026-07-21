import {
  NextRequest,
  NextResponse,
} from "next/server"

import { clearAuthCookies } from "@/lib/auth/cookies"
import { REFRESH_TOKEN_COOKIE } from "@/lib/auth/constants"
import {
  isSameOriginBrowserRequest,
} from "@/lib/auth/security"
import {
  BackendUnavailableError,
  backendFetch,
} from "@/lib/auth/upstream"

export async function POST(
  request: NextRequest,
): Promise<NextResponse> {
  if (!isSameOriginBrowserRequest(request)) {
    return NextResponse.json(
      {
        error: {
          code: "invalid_request_origin",
          message:
            "This sign-out request did not originate from PoultryPulse.",
        },
      },
      { status: 403 },
    )
  }

  const refreshToken =
    request.cookies.get(REFRESH_TOKEN_COOKIE)?.value

  if (refreshToken) {
    try {
      await backendFetch("/auth/logout", {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          refresh_token: refreshToken,
        }),
      })
    } catch (error) {
      if (!(error instanceof BackendUnavailableError)) {
        throw error
      }
    }
  }

  const response = new NextResponse(null, {
    status: 204,
    headers: {
      "Cache-Control": "no-store",
    },
  })
  clearAuthCookies(response)
  return response
}
