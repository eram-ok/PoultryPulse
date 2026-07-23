const DEFAULT_PLATFORM_RETURN_TO =
  "/platform/dashboard"

export function safePlatformReturnTo(
  value: string | null | undefined,
): string {
  if (!value) {
    return DEFAULT_PLATFORM_RETURN_TO
  }

  const normalized = value.trim()

  if (
    !normalized.startsWith("/platform") ||
    normalized.startsWith("//") ||
    normalized.startsWith("/platform/login")
  ) {
    return DEFAULT_PLATFORM_RETURN_TO
  }

  return normalized
}
