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
  readJsonSafely,
} from "@/lib/auth/upstream"
import {
  attachPlatformAuthCookies,
} from "@/lib/platform-auth/cookies"
import {
  safePlatformReturnTo,
} from "@/lib/platform-auth/security"
import type {
  PlatformApiErrorBody,
  PlatformTokenResponse,
} from "@/lib/platform-auth/types"

interface PlatformLoginPayload {
  username?: string
  password?: string
  next?: string
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
            "This platform sign-in request did not originate from PoultryPulse.",
        },
      },
      { status: 403 },
    )
  }

  let payload: PlatformLoginPayload

  try {
    payload =
      (await request.json()) as
        PlatformLoginPayload
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "invalid_platform_login_payload",
          message:
            "Enter your platform username and password.",
        },
      },
      { status: 400 },
    )
  }

  const username =
    payload.username?.trim() ?? ""
  const password = payload.password ?? ""

  if (!username || !password) {
    return NextResponse.json(
      {
        error: {
          code: "missing_platform_credentials",
          message:
            "Enter both your platform username and password.",
        },
      },
      { status: 400 },
    )
  }

  const body = new URLSearchParams({
    username,
    password,
  })

  try {
    const upstream = await backendFetch(
      "/platform/auth/login",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type":
            "application/x-www-form-urlencoded",
          "User-Agent":
            request.headers.get("user-agent") ??
            "PoultryPulse-Platform-Frontend",
        },
        body,
      },
    )

    if (!upstream.ok) {
      const error =
        await readJsonSafely<PlatformApiErrorBody>(
          upstream,
        )

      return NextResponse.json(
        error ?? {
          error: {
            code: "platform_login_failed",
            message:
              "PoultryPulse could not sign you in to platform administration.",
          },
        },
        {
          status: upstream.status,
          headers: {
            "Cache-Control": "no-store",
          },
        },
      )
    }

    const tokens =
      await readJsonSafely<PlatformTokenResponse>(
        upstream,
      )

    if (!tokens) {
      return NextResponse.json(
        {
          error: {
            code: "invalid_platform_login_response",
            message:
              "The platform authentication service returned an invalid response.",
          },
        },
        { status: 502 },
      )
    }

    if (!tokens.user.is_super_admin) {
      return NextResponse.json(
        {
          error: {
            code: "platform_super_admin_required",
            message:
              "Platform super-administrator access is required.",
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

    const response = NextResponse.json(
      {
        user: tokens.user,
        redirect_to:
          tokens.user.must_change_password
            ? "/platform/change-password"
            : safePlatformReturnTo(
                payload.next,
              ),
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    )

    attachPlatformAuthCookies(
      response,
      tokens,
    )
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
