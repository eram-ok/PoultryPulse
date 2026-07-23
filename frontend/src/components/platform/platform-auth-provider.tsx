"use client"

import {
  createContext,
  useContext,
  useMemo,
} from "react"

import type {
  PlatformSessionPayload,
} from "@/lib/platform-auth/types"

interface PlatformAuthContextValue {
  session: PlatformSessionPayload
  logout: () => Promise<void>
}

const PlatformAuthContext =
  createContext<PlatformAuthContextValue | null>(
    null,
  )

interface PlatformAuthProviderProps {
  initialSession: PlatformSessionPayload
  children: React.ReactNode
}

export function PlatformAuthProvider({
  initialSession,
  children,
}: PlatformAuthProviderProps) {
  const value =
    useMemo<PlatformAuthContextValue>(
      () => ({
        session: initialSession,
        logout: async () => {
          try {
            await fetch(
              "/api/platform/auth/logout",
              {
                method: "POST",
                credentials: "same-origin",
              },
            )
          } finally {
            window.location.replace(
              "/platform/login",
            )
          }
        },
      }),
      [initialSession],
    )

  return (
    <PlatformAuthContext.Provider value={value}>
      {children}
    </PlatformAuthContext.Provider>
  )
}

export function usePlatformAuth(): PlatformAuthContextValue {
  const context = useContext(
    PlatformAuthContext,
  )

  if (!context) {
    throw new Error(
      "usePlatformAuth must be used within PlatformAuthProvider.",
    )
  }

  return context
}
