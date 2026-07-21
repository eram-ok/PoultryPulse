import { redirect } from "next/navigation"

import {
  readServerAuthCookies,
} from "@/lib/auth/cookies"
import type {
  AuthenticatedUser,
  Farm,
  SessionPayload,
} from "@/lib/auth/types"
import {
  BackendUnavailableError,
  backendFetch,
  readJsonSafely,
} from "@/lib/auth/upstream"

export interface SessionLookup {
  session: SessionPayload | null
  status: number
}

export function collectPermissionCodes(
  user: AuthenticatedUser,
): string[] {
  return Array.from(
    new Set(
      user.roles
        .filter((role) => role.is_active)
        .flatMap((role) =>
          role.permissions.map(
            (permission) => permission.code,
          ),
        ),
    ),
  ).sort()
}

function fallbackFarm(user: AuthenticatedUser): Farm {
  return {
    id: user.farm_id,
    farm_code: "FARM",
    name: "PoultryPulse Farm",
    owner_name: null,
    telephone: null,
    email: null,
    district: null,
    address: null,
    logo_url: null,
    timezone: "Africa/Kampala",
    currency_code: "UGX",
    is_active: true,
    created_at: "",
    updated_at: "",
    settings: null,
  }
}

export async function loadSessionWithAccessToken(
  accessToken: string,
): Promise<SessionLookup> {
  const userResponse = await backendFetch("/auth/me", {
    headers: {
      Accept: "application/json",
      Authorization: `Bearer ${accessToken}`,
    },
  })

  if (!userResponse.ok) {
    return {
      session: null,
      status: userResponse.status,
    }
  }

  const user =
    await readJsonSafely<AuthenticatedUser>(userResponse)

  if (!user) {
    return {
      session: null,
      status: 502,
    }
  }

  const permissions = collectPermissionCodes(user)
  let farm = fallbackFarm(user)

  if (permissions.includes("farms.view")) {
    const farmResponse = await backendFetch(
      `/farms/${encodeURIComponent(user.farm_id)}`,
      {
        headers: {
          Accept: "application/json",
          Authorization: `Bearer ${accessToken}`,
        },
      },
    )

    if (farmResponse.ok) {
      farm =
        (await readJsonSafely<Farm>(farmResponse)) ??
        farm
    }
  }

  return {
    status: 200,
    session: {
      user,
      farm,
      permissions,
      roles: user.roles
        .filter((role) => role.is_active)
        .map((role) => role.name),
    },
  }
}

interface RequireSessionOptions {
  allowPasswordChange?: boolean
  returnTo?: string
}

export async function requireServerSession(
  options: RequireSessionOptions = {},
): Promise<SessionPayload> {
  const {
    allowPasswordChange = false,
    returnTo = "/dashboard",
  } = options
  const { accessToken, refreshToken } =
    await readServerAuthCookies()

  if (!accessToken) {
    if (refreshToken) {
      redirect(
        `/api/auth/refresh?returnTo=${encodeURIComponent(
          returnTo,
        )}`,
      )
    }

    redirect(
      `/login?next=${encodeURIComponent(returnTo)}`,
    )
  }

  let lookup: SessionLookup

  try {
    lookup = await loadSessionWithAccessToken(
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
      `/api/auth/refresh?returnTo=${encodeURIComponent(
        returnTo,
      )}`,
    )
  }

  if (!lookup.session) {
    redirect(
      `/login?reason=session-expired&next=${encodeURIComponent(
        returnTo,
      )}`,
    )
  }

  if (
    lookup.session.user.must_change_password &&
    !allowPasswordChange
  ) {
    redirect("/change-password")
  }

  return lookup.session
}

export function sessionHasPermission(
  session: SessionPayload,
  permission: string,
): boolean {
  return session.permissions.includes(permission)
}
