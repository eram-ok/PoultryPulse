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

interface InvitationAcceptPayload {
  token?: string
  new_password?: string
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
            "This account-activation request did not originate from PoultryPulse.",
        },
      },
      403,
    )
  }

  let payload: InvitationAcceptPayload

  try {
    payload =
      (await request.json()) as InvitationAcceptPayload
  } catch {
    return noStoreJson(
      {
        error: {
          code: "invalid_activation_payload",
          message:
            "The account-activation information could not be read.",
        },
      },
      400,
    )
  }

  const token = payload.token?.trim() ?? ""
  const newPassword = payload.new_password ?? ""

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

  if (newPassword.length < 12 || newPassword.length > 128) {
    return noStoreJson(
      {
        error: {
          code: "invalid_new_password",
          message:
            "Use a password containing between 12 and 128 characters.",
        },
      },
      400,
    )
  }

  try {
    const upstream = await backendFetch(
      "/onboarding/invitations/accept",
      {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token,
          new_password: newPassword,
        }),
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
              "PoultryPulse could not activate the account right now.",
          },
        },
        503,
      )
    }

    throw error
  }
}
