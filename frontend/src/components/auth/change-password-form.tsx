"use client"

import {
  useState,
  useTransition,
} from "react"
import {
  Eye,
  EyeOff,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import type { ApiErrorBody } from "@/lib/auth/types"

export function ChangePasswordForm() {
  const [showPasswords, setShowPasswords] =
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
    const currentPassword = String(
      form.get("currentPassword") ?? "",
    )
    const newPassword = String(
      form.get("newPassword") ?? "",
    )
    const confirmPassword = String(
      form.get("confirmPassword") ?? "",
    )

    if (newPassword.length < 12) {
      setError(
        "Your new password must contain at least 12 characters.",
      )
      return
    }

    if (newPassword !== confirmPassword) {
      setError(
        "The new password and confirmation do not match.",
      )
      return
    }

    if (currentPassword === newPassword) {
      setError(
        "Choose a new password that is different from your current password.",
      )
      return
    }

    startTransition(async () => {
      try {
        const response = await fetch(
          "/api/auth/change-password",
          {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              current_password: currentPassword,
              new_password: newPassword,
            }),
          },
        )

        if (!response.ok) {
          const payload =
            (await response.json()) as ApiErrorBody
          setError(
            payload.error?.message ??
              "PoultryPulse could not change your password.",
          )
          return
        }

        window.location.replace(
          "/login?passwordChanged=1",
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
      className="space-y-4"
      onSubmit={submit}
    >
      {[
        {
          id: "currentPassword",
          label: "Current password",
          autoComplete: "current-password",
        },
        {
          id: "newPassword",
          label: "New password",
          autoComplete: "new-password",
        },
        {
          id: "confirmPassword",
          label: "Confirm new password",
          autoComplete: "new-password",
        },
      ].map((field) => (
        <div
          key={field.id}
          className="space-y-2"
        >
          <label
            htmlFor={field.id}
            className="text-sm font-medium"
          >
            {field.label}
          </label>
          <div className="relative">
            <Input
              id={field.id}
              name={field.id}
              type={
                showPasswords ? "text" : "password"
              }
              autoComplete={field.autoComplete}
              required
              maxLength={128}
              className="h-12 rounded-xl pr-11"
            />
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 size-10 -translate-y-1/2 rounded-lg"
              aria-label={
                showPasswords
                  ? "Hide passwords"
                  : "Show passwords"
              }
              onClick={() =>
                setShowPasswords(
                  (current) => !current,
                )
              }
            >
              {showPasswords ? (
                <EyeOff className="size-4" />
              ) : (
                <Eye className="size-4" />
              )}
            </Button>
          </div>
        </div>
      ))}

      <p className="text-xs leading-5 text-muted-foreground">
        Use at least 12 characters and combine uppercase,
        lowercase, numbers, and symbols.
      </p>

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
        className="h-12 w-full rounded-xl"
        disabled={pending}
      >
        {pending ? (
          <LoaderCircle className="size-4 animate-spin" />
        ) : (
          <ShieldCheck className="size-4" />
        )}
        {pending
          ? "Updating password..."
          : "Update password"}
      </Button>
    </form>
  )
}
