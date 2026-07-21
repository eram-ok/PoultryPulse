"use client"

import {
  createContext,
  useContext,
  useMemo,
  useState,
} from "react"

import type { SessionPayload } from "@/lib/auth/types"

interface AuthContextValue {
  session: SessionPayload
  setSession: (
    session: SessionPayload,
  ) => void
  logout: () => Promise<void>
  hasPermission: (permission: string) => boolean
}

const AuthContext =
  createContext<AuthContextValue | null>(null)

interface AuthProviderProps {
  initialSession: SessionPayload
  children: React.ReactNode
}

export function AuthProvider({
  initialSession,
  children,
}: AuthProviderProps) {
  const [session, setSession] =
    useState(initialSession)

  const value = useMemo<AuthContextValue>(
    () => ({
      session,
      setSession,
      hasPermission: (permission: string) =>
        session.permissions.includes(permission),
      logout: async () => {
        try {
          await fetch("/api/auth/logout", {
            method: "POST",
            credentials: "same-origin",
          })
        } finally {
          window.location.replace("/login")
        }
      },
    }),
    [session],
  )

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error(
      "useAuth must be used within AuthProvider.",
    )
  }

  return context
}
