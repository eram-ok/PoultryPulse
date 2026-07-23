import { redirect } from "next/navigation"

import {
  BackendUnavailableError,
  backendFetch,
  readJsonSafely,
} from "@/lib/auth/upstream"
import {
  readServerPlatformAuthCookies,
} from "@/lib/platform-auth/cookies"
import type {
  PlatformSessionPayload,
  PlatformUser,
} from "@/lib/platform-auth/types"

interface PlatformSessionLookup {
  session: PlatformSessionPayload | null
  status: number
}

export async function loadPlatformSessionWithAccessToken(
  accessToken: string,
): Promise<PlatformSessionLookup> {
  const response = await backendFetch(
    "/platform/auth/me",
    {
      headers: {
        Accept: "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
    },
  )

  if (!response.ok) {
    return {
      session: null,
      status: response.status,
    }
  }

  const user =
    await readJsonSafely<PlatformUser>(response)

  if (!user) {
    return {
      session: null,
      status: 502,
    }
  }

  return {
    status: 200,
    session: { user },
  }
}

interface RequirePlatformSessionOptions {
  allowPasswordChange?: boolean
  returnTo?: string
}

export async function requirePlatformServerSession(
  options: RequirePlatformSessionOptions = {},
): Promise<PlatformSessionPayload> {
  const {
    allowPasswordChange = false,
    returnTo = "/platform/dashboard",
  } = options

  const { accessToken, refreshToken } =
    await readServerPlatformAuthCookies()

  if (!accessToken) {
    if (refreshToken) {
      redirect(
        `/api/platform/auth/refresh?returnTo=${encodeURIComponent(
          returnTo,
        )}`,
      )
    }

    redirect(
      `/platform/login?next=${encodeURIComponent(
        returnTo,
      )}`,
    )
  }

  let lookup: PlatformSessionLookup

  try {
    lookup =
      await loadPlatformSessionWithAccessToken(
        accessToken,
      )
  } catch (error) {
    if (error instanceof BackendUnavailableError) {
      throw error
    }

    throw new BackendUnavailableError()
  }

  if (lookup.status === 401 && refreshToken) {
    redirect(
      `/api/platform/auth/refresh?returnTo=${encodeURIComponent(
        returnTo,
      )}`,
    )
  }

  if (!lookup.session) {
    redirect(
      `/platform/login?reason=session-expired&next=${encodeURIComponent(
        returnTo,
      )}`,
    )
  }

  if (!lookup.session.user.is_super_admin) {
    redirect(
      "/platform/login?reason=super-admin-required",
    )
  }

  if (
    lookup.session.user.must_change_password &&
    !allowPasswordChange
  ) {
    redirect("/platform/change-password")
  }

  return lookup.session
}
