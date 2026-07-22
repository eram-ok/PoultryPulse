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
  toNextResponse,
} from "@/lib/auth/upstream"

interface InvitationTokenPayload {
  token?: string
}

export const dynamic = "force-dynamic"

function noStoreJson(
  body: object,
  status: number,
): NextResponse {
  const response = NextResponse.json(body, { status })
  response.headers.set("Cache-Control", "no-store, max-age=0")
  response.headers.set("Pragma", "no-cache")
  return response
}

export async function POST(
  request: NextRequest,
): Promise<NextResponse> {
  if (!isSameOriginBrowserRequest(request)) {
    return noStoreJson(
      {
        error: {
          code: "invalid_request_origin",
          message:
            "This invitation request did not originate from PoultryPulse.",
        },
      },
      403,
    )
  }

  let payload: InvitationTokenPayload

  try {
    payload =
      (await request.json()) as InvitationTokenPayload
  } catch {
    return noStoreJson(
      {
        error: {
          code: "invalid_invitation_payload",
          message:
            "The invitation information could not be read.",
        },
      },
      400,
    )
  }

  const token = payload.token?.trim() ?? ""

  if (token.length < 32 || token.length > 512) {
    return noStoreJson(
      {
        error: {
          code: "invalid_invitation_token",
          message:
            "This farm invitation link is invalid.",
        },
      },
      400,
    )
  }

  try {
    const upstream = await backendFetch(
      "/onboarding/invitations/validate",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ token }),
      },
    )

    return toNextResponse(upstream)
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      return noStoreJson(
        {
          error: {
            code: "backend_unavailable",
            message:
              "PoultryPulse could not validate the invitation right now.",
          },
        },
        503,
      )
    }

    throw error
  }
}
