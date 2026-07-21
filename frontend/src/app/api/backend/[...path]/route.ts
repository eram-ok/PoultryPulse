import type { NextRequest } from "next/server"

import {
  forwardAuthenticatedRequest,
} from "@/lib/auth/authenticated-request"

interface BackendRouteContext {
  params: Promise<{
    path: string[]
  }>
}

async function handle(
  request: NextRequest,
  context: BackendRouteContext,
) {
  const { path } = await context.params
  const encodedPath = path
    .map((segment) => encodeURIComponent(segment))
    .join("/")
  const upstreamPath = `/${encodedPath}${request.nextUrl.search}`

  return forwardAuthenticatedRequest(
    request,
    upstreamPath,
  )
}

export const GET = handle
export const POST = handle
export const PUT = handle
export const PATCH = handle
export const DELETE = handle
