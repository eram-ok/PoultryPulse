import type {
  NextRequest,
} from "next/server"

import {
  forwardPlatformAuthenticatedRequest,
} from "@/lib/platform-auth/authenticated-request"

interface PlatformBackendRouteContext {
  params: Promise<{
    path: string[]
  }>
}

async function handle(
  request: NextRequest,
  context: PlatformBackendRouteContext,
) {
  const { path } = await context.params
  const encodedPath = path
    .map((segment) =>
      encodeURIComponent(segment),
    )
    .join("/")
  const upstreamPath =
    `/${encodedPath}${request.nextUrl.search}`

  return forwardPlatformAuthenticatedRequest(
    request,
    upstreamPath,
  )
}

export const GET = handle
export const POST = handle
export const PUT = handle
export const PATCH = handle
export const DELETE = handle
