"use client"

import {
  useState,
  useTransition,
} from "react"
import {
  Eye,
  EyeOff,
  LoaderCircle,
  LockKeyhole,
  UserRound,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { ApiErrorBody } from "@/lib/auth/types"

interface LoginFormProps {
  nextPath: string
}

interface LoginSuccess {
  redirect_to: string
}

export function LoginForm({
  nextPath,
}: LoginFormProps) {
  const [showPassword, setShowPassword] =
    useState(false)
  const [error, setError] = useState<string | null>(
    null,
  )
  const [pending, startTransition] = useTransition()

  function submit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError(null)

    const form = new FormData(event.currentTarget)
    const username = String(
      form.get("username") ?? "",
    ).trim()
    const password = String(
      form.get("password") ?? "",
    )

    startTransition(async () => {
      try {
        const response = await fetch(
          "/api/auth/login",
          {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              username,
              password,
              next: nextPath,
            }),
          },
        )

        const payload = (await response.json()) as
          | LoginSuccess
          | ApiErrorBody

        if (!response.ok) {
          setError(
            "error" in payload
              ? payload.error?.message ??
                  "PoultryPulse could not sign you in."
              : "PoultryPulse could not sign you in.",
          )
          return
        }

        const destination =
          "redirect_to" in payload
            ? payload.redirect_to
            : "/dashboard"

        window.location.replace(
          destination === "/dashboard"
            ? nextPath
            : destination,
        )
      } catch {
        setError(
          "PoultryPulse could not reach the authentication service.",
        )
      }
    })
  }

  return (
    <form
      className="space-y-5"
      onSubmit={submit}
    >
      <div className="space-y-2">
        <label
          htmlFor="username"
          className="text-sm font-medium"
        >
          Username
        </label>
        <div className="relative">
          <UserRound className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="username"
            name="username"
            autoComplete="username"
            autoCapitalize="none"
            spellCheck={false}
            required
            minLength={2}
            maxLength={50}
            className="h-12 rounded-xl pl-10"
            placeholder="Enter your username"
          />
        </div>
      </div>

      <div className="space-y-2">
        <label
          htmlFor="password"
          className="text-sm font-medium"
        >
          Password
        </label>
        <div className="relative">
          <LockKeyhole className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            id="password"
            name="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            required
            maxLength={128}
            className="h-12 rounded-xl px-10"
            placeholder="Enter your password"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute right-1 top-1/2 size-10 -translate-y-1/2 rounded-lg"
            aria-label={
              showPassword
                ? "Hide password"
                : "Show password"
            }
            onClick={() =>
              setShowPassword((current) => !current)
            }
          >
            {showPassword ? (
              <EyeOff className="size-4" />
            ) : (
              <Eye className="size-4" />
            )}
          </Button>
        </div>
      </div>

      {error ? (
        <div
          role="alert"
          className="rounded-xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </div>
      ) : null}

      <Button
        type="submit"
        className="h-12 w-full rounded-xl shadow-lg shadow-primary/20"
        disabled={pending}
      >
        {pending ? (
          <LoaderCircle className="size-4 animate-spin" />
        ) : (
          <LockKeyhole className="size-4" />
        )}
        {pending ? "Signing in..." : "Sign in securely"}
      </Button>
    </form>
  )
}
