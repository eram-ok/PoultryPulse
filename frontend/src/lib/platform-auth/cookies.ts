import { cookies } from "next/headers"
import type { NextResponse } from "next/server"

import {
  getRefreshCookieMaxAge,
  shouldUseSecureCookies,
} from "@/lib/auth/config"
import {
  PLATFORM_ACCESS_TOKEN_COOKIE,
  PLATFORM_REFRESH_TOKEN_COOKIE,
} from "@/lib/platform-auth/constants"
import type {
  PlatformTokenResponse,
} from "@/lib/platform-auth/types"

function platformCookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: shouldUseSecureCookies(),
    sameSite: "lax" as const,
    path: "/",
    maxAge,
    priority: "high" as const,
  }
}

export function attachPlatformAuthCookies(
  response: NextResponse,
  tokens: PlatformTokenResponse,
): void {
  response.cookies.set(
    PLATFORM_ACCESS_TOKEN_COOKIE,
    tokens.access_token,
    platformCookieOptions(
      Math.max(60, tokens.expires_in),
    ),
  )
  response.cookies.set(
    PLATFORM_REFRESH_TOKEN_COOKIE,
    tokens.refresh_token,
    platformCookieOptions(getRefreshCookieMaxAge()),
  )
}

export function clearPlatformAuthCookies(
  response: NextResponse,
): void {
  response.cookies.set(
    PLATFORM_ACCESS_TOKEN_COOKIE,
    "",
    {
      ...platformCookieOptions(0),
      expires: new Date(0),
    },
  )
  response.cookies.set(
    PLATFORM_REFRESH_TOKEN_COOKIE,
    "",
    {
      ...platformCookieOptions(0),
      expires: new Date(0),
    },
  )
}

export async function readServerPlatformAuthCookies(): Promise<{
  accessToken: string | null
  refreshToken: string | null
}> {
  const cookieStore = await cookies()

  return {
    accessToken:
      cookieStore.get(
        PLATFORM_ACCESS_TOKEN_COOKIE,
      )?.value ?? null,
    refreshToken:
      cookieStore.get(
        PLATFORM_REFRESH_TOKEN_COOKIE,
      )?.value ?? null,
  }
}

export async function hasServerPlatformAuthCookie(): Promise<boolean> {
  const { accessToken, refreshToken } =
    await readServerPlatformAuthCookies()

  return Boolean(accessToken || refreshToken)
}
