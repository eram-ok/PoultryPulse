import {
  backendFetch,
  readJsonSafely,
} from "@/lib/auth/upstream"
import type {
  PlatformTokenResponse,
} from "@/lib/platform-auth/types"

export async function refreshPlatformTokenPair(
  refreshToken: string,
  userAgent?: string | null,
): Promise<PlatformTokenResponse | null> {
  const response = await backendFetch(
    "/platform/auth/refresh",
    {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        ...(userAgent
          ? { "User-Agent": userAgent }
          : {}),
      },
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    },
  )

  if (!response.ok) {
    return null
  }

  return readJsonSafely<PlatformTokenResponse>(
    response,
  )
}
