import { cookies } from "next/headers"
import type { NextResponse } from "next/server"

import {
  getRefreshCookieMaxAge,
  shouldUseSecureCookies,
} from "@/lib/auth/config"
import {
  ACCESS_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
} from "@/lib/auth/constants"
import type { TokenResponse } from "@/lib/auth/types"

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    secure: shouldUseSecureCookies(),
    sameSite: "lax" as const,
    path: "/",
    maxAge,
    priority: "high" as const,
  }
}

export function attachAuthCookies(
  response: NextResponse,
  tokens: TokenResponse,
): void {
  response.cookies.set(
    ACCESS_TOKEN_COOKIE,
    tokens.access_token,
    cookieOptions(Math.max(60, tokens.expires_in)),
  )
  response.cookies.set(
    REFRESH_TOKEN_COOKIE,
    tokens.refresh_token,
    cookieOptions(getRefreshCookieMaxAge()),
  )
}

export function clearAuthCookies(
  response: NextResponse,
): void {
  response.cookies.set(ACCESS_TOKEN_COOKIE, "", {
    ...cookieOptions(0),
    expires: new Date(0),
  })
  response.cookies.set(REFRESH_TOKEN_COOKIE, "", {
    ...cookieOptions(0),
    expires: new Date(0),
  })
}

export async function readServerAuthCookies(): Promise<{
  accessToken: string | null
  refreshToken: string | null
}> {
  const cookieStore = await cookies()

  return {
    accessToken:
      cookieStore.get(ACCESS_TOKEN_COOKIE)?.value ?? null,
    refreshToken:
      cookieStore.get(REFRESH_TOKEN_COOKIE)?.value ?? null,
  }
}

export async function hasServerAuthCookie(): Promise<boolean> {
  const { accessToken, refreshToken } =
    await readServerAuthCookies()

  return Boolean(accessToken || refreshToken)
}
