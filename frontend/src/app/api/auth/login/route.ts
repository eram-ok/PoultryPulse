import {
  NextRequest,
  NextResponse,
} from "next/server"

import { attachAuthCookies } from "@/lib/auth/cookies"
import {
  isSameOriginBrowserRequest,
} from "@/lib/auth/security"
import type {
  ApiErrorBody,
  TokenResponse,
} from "@/lib/auth/types"
import {
  BackendUnavailableError,
  backendFetch,
  readJsonSafely,
} from "@/lib/auth/upstream"

interface LoginPayload {
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
            "This sign-in request did not originate from PoultryPulse.",
        },
      },
      { status: 403 },
    )
  }

  let payload: LoginPayload

  try {
    payload = (await request.json()) as LoginPayload
  } catch {
    return NextResponse.json(
      {
        error: {
          code: "invalid_login_payload",
          message:
            "Enter your username and password.",
        },
      },
      { status: 400 },
    )
  }

  const username = payload.username?.trim() ?? ""
  const password = payload.password ?? ""

  if (!username || !password) {
    return NextResponse.json(
      {
        error: {
          code: "missing_credentials",
          message:
            "Enter both your username and password.",
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
    const upstream = await backendFetch("/auth/login", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type":
          "application/x-www-form-urlencoded",
        "User-Agent":
          request.headers.get("user-agent") ??
          "PoultryPulse-Frontend",
      },
      body,
    })

    if (!upstream.ok) {
      const error =
        await readJsonSafely<ApiErrorBody>(upstream)

      return NextResponse.json(
        error ?? {
          error: {
            code: "login_failed",
            message:
              "PoultryPulse could not sign you in.",
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
      await readJsonSafely<TokenResponse>(upstream)

    if (!tokens) {
      return NextResponse.json(
        {
          error: {
            code: "invalid_login_response",
            message:
              "The authentication service returned an invalid response.",
          },
        },
        { status: 502 },
      )
    }

    const response = NextResponse.json(
      {
        user: tokens.user,
        redirect_to:
          tokens.user.must_change_password
            ? "/change-password"
            : "/dashboard",
      },
      {
        headers: {
          "Cache-Control": "no-store",
        },
      },
    )

    attachAuthCookies(response, tokens)
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
