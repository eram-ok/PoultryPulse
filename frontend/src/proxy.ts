import {
  NextRequest,
  NextResponse,
} from "next/server"

import {
  ACCESS_TOKEN_COOKIE,
  REFRESH_TOKEN_COOKIE,
} from "@/lib/auth/constants"

export function proxy(
  request: NextRequest,
): NextResponse {
  const hasSession = Boolean(
    request.cookies.get(ACCESS_TOKEN_COOKIE)?.value ||
      request.cookies.get(REFRESH_TOKEN_COOKIE)?.value,
  )

  if (!hasSession) {
    const loginUrl = new URL("/login", request.url)
    loginUrl.searchParams.set(
      "next",
      `${request.nextUrl.pathname}${request.nextUrl.search}`,
    )
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    "/",
    "/dashboard/:path*",
    "/reports/:path*",
    "/alerts/:path*",
    "/flocks/:path*",
    "/houses/:path*",
    "/production/:path*",
    "/egg-inventory/:path*",
    "/feed/:path*",
    "/health/:path*",
    "/bird-losses/:path*",
    "/sales/:path*",
    "/finance/:path*",
    "/suppliers/:path*",
    "/users/:path*",
    "/jobs/:path*",
    "/audit/:path*",
    "/settings/:path*",
    "/change-password",
  ],
}
