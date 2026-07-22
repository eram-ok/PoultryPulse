"use client"

import Link from "next/link"
import {
  useEffect,
  useMemo,
  useRef,
  useState,
  useTransition,
} from "react"
import {
  AlertTriangle,
  Check,
  CheckCircle2,
  Clock3,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import type {
  FarmInvitationAcceptResponse,
  FarmInvitationPublicResponse,
  OnboardingApiErrorBody,
} from "@/lib/onboarding/types"

type ScreenState =
  | "loading"
  | "ready"
  | "error"
  | "accepted"

const PASSWORD_RULES = [
  {
    label: "At least 12 characters",
    test: (value: string) => value.length >= 12,
  },
  {
    label: "One uppercase letter",
    test: (value: string) => /[A-Z]/.test(value),
  },
  {
    label: "One lowercase letter",
    test: (value: string) => /[a-z]/.test(value),
  },
  {
    label: "One number",
    test: (value: string) => /\d/.test(value),
  },
  {
    label: "One special character",
    test: (value: string) =>
      /[^A-Za-z0-9]/.test(value),
  },
] as const

function invitationTokenFromLocation(): string | null {
  const currentUrl = new URL(window.location.href)
  const queryToken =
    currentUrl.searchParams.get("token")?.trim() ?? ""

  const fragmentParameters = new URLSearchParams(
    currentUrl.hash.replace(/^#/, ""),
  )
  const fragmentToken =
    fragmentParameters.get("token")?.trim() ?? ""

  const token = queryToken || fragmentToken

  window.history.replaceState(
    {},
    document.title,
    currentUrl.pathname,
  )

  return token || null
}

async function errorMessage(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const payload =
      (await response.json()) as OnboardingApiErrorBody

    return (
      payload.error?.message ??
      payload.detail ??
      fallback
    )
  } catch {
    return fallback
  }
}

function formatExpiry(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return "the stated expiry time"
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date)
}

export function SetupAccountWorkspace() {
  const initialized = useRef(false)
  const [screen, setScreen] =
    useState<ScreenState>("loading")
  const [token, setToken] = useState<string | null>(
    null,
  )
  const [invitation, setInvitation] =
    useState<FarmInvitationPublicResponse | null>(
      null,
    )
  const [accepted, setAccepted] =
    useState<FarmInvitationAcceptResponse | null>(
      null,
    )
  const [error, setError] = useState<string | null>(
    null,
  )
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] =
    useState("")
  const [showPasswords, setShowPasswords] =
    useState(false)
  const [pending, startTransition] = useTransition()

  useEffect(() => {
    if (initialized.current) {
      return
    }

    initialized.current = true
    const controller = new AbortController()

    async function validate() {
      await Promise.resolve()

      const invitationToken =
        invitationTokenFromLocation()

      if (!invitationToken) {
        setError(
          "This setup link is incomplete. Request a new invitation from the PoultryPulse platform administrator.",
        )
        setScreen("error")
        return
      }

      setToken(invitationToken)

      try {
        const response = await fetch(
          "/api/onboarding/invitations/validate",
          {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              token: invitationToken,
            }),
            signal: controller.signal,
          },
        )

        if (!response.ok) {
          setToken(null)
          setError(
            await errorMessage(
              response,
              "This farm invitation is invalid or no longer available.",
            ),
          )
          setScreen("error")
          return
        }

        const payload =
          (await response.json()) as FarmInvitationPublicResponse
        setInvitation(payload)
        setScreen("ready")
      } catch (validationError) {
        if (
          validationError instanceof DOMException &&
          validationError.name === "AbortError"
        ) {
          return
        }

        setToken(null)
        setError(
          "PoultryPulse could not validate this invitation. Check your connection and try opening the invitation again.",
        )
        setScreen("error")
      }
    }

    void validate()

    return () => {
      controller.abort()
    }
  }, [])

  const passwordChecks = useMemo(
    () =>
      PASSWORD_RULES.map((rule) => ({
        label: rule.label,
        passed: rule.test(newPassword),
      })),
    [newPassword],
  )

  const passwordIsStrong = passwordChecks.every(
    (check) => check.passed,
  )
  const passwordsMatch =
    newPassword.length > 0 &&
    newPassword === confirmPassword

  function submit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError(null)

    if (!token || !invitation) {
      setError(
        "The invitation is no longer available. Request a new setup link.",
      )
      return
    }

    if (!passwordIsStrong) {
      setError(
        "Choose a password that satisfies every security requirement.",
      )
      return
    }

    if (!passwordsMatch) {
      setError(
        "The password and confirmation do not match.",
      )
      return
    }

    startTransition(async () => {
      try {
        const response = await fetch(
          "/api/onboarding/invitations/accept",
          {
            method: "POST",
            credentials: "same-origin",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              token,
              new_password: newPassword,
            }),
          },
        )

        if (!response.ok) {
          const message = await errorMessage(
            response,
            "PoultryPulse could not activate this account.",
          )
          setError(message)

          if (
            response.status === 404 ||
            response.status === 409 ||
            response.status === 422
          ) {
            setToken(null)
          }
          return
        }

        const result =
          (await response.json()) as FarmInvitationAcceptResponse

        setAccepted(result)
        setToken(null)
        setNewPassword("")
        setConfirmPassword("")
        setScreen("accepted")
      } catch {
        setError(
          "PoultryPulse could not reach the account-activation service.",
        )
      }
    })
  }

  if (screen === "loading") {
    return (
      <Card className="rounded-3xl border-border/75 bg-card/88 shadow-2xl shadow-black/10 backdrop-blur-xl">
        <CardContent className="flex min-h-80 flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="grid size-14 place-items-center rounded-2xl bg-primary/12 text-primary">
            <LoaderCircle className="size-6 animate-spin" />
          </div>
          <div>
            <p className="font-semibold">
              Checking your invitation
            </p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              PoultryPulse is securely validating this
              one-time account setup link.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (screen === "error") {
    return (
      <Card className="rounded-3xl border-border/75 bg-card/88 shadow-2xl shadow-black/10 backdrop-blur-xl">
        <CardHeader className="space-y-4 p-6 sm:p-8">
          <div className="grid size-12 place-items-center rounded-2xl bg-destructive/10 text-destructive">
            <AlertTriangle className="size-5" />
          </div>
          <div>
            <CardTitle className="text-2xl">
              Setup link unavailable
            </CardTitle>
            <CardDescription className="mt-2 leading-6">
              This account cannot be activated with the
              supplied invitation.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-5 px-6 pb-6 sm:px-8 sm:pb-8">
          <div
            role="alert"
            className="rounded-xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm leading-6 text-destructive"
          >
            {error}
          </div>
          <Button
            asChild
            variant="outline"
            className="h-12 w-full rounded-xl"
          >
            <Link href="/login">Return to sign in</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (screen === "accepted" && accepted) {
    return (
      <Card className="rounded-3xl border-border/75 bg-card/88 shadow-2xl shadow-black/10 backdrop-blur-xl">
        <CardHeader className="space-y-4 p-6 sm:p-8">
          <div className="grid size-12 place-items-center rounded-2xl bg-primary/12 text-primary">
            <CheckCircle2 className="size-6" />
          </div>
          <div>
            <CardTitle className="text-2xl">
              Account activated
            </CardTitle>
            <CardDescription className="mt-2 leading-6">
              Your PoultryPulse farm administrator
              account is ready.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="space-y-5 px-6 pb-6 sm:px-8 sm:pb-8">
          <div className="rounded-2xl border border-border/70 bg-muted/35 p-4">
            <p className="text-xs font-medium uppercase tracking-[0.18em] text-muted-foreground">
              Sign-in identity
            </p>
            <p className="mt-2 font-semibold">
              {accepted.farm_code}:
              {accepted.administrator_username}
            </p>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              Use this farm code and username with the
              password you just created.
            </p>
          </div>
          <Button
            asChild
            className="h-12 w-full rounded-xl"
          >
            <Link href="/login?accountActivated=1">
              Continue to sign in
            </Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!invitation) {
    return null
  }

  return (
    <Card className="rounded-3xl border-border/75 bg-card/88 shadow-2xl shadow-black/10 backdrop-blur-xl">
      <CardHeader className="space-y-4 p-6 sm:p-8">
        <div className="flex items-center justify-between gap-4">
          <div className="grid size-12 place-items-center rounded-2xl bg-primary/12 text-primary">
            <KeyRound className="size-5" />
          </div>
          <Badge
            variant="outline"
            className="rounded-full border-primary/25 bg-primary/8 text-primary"
          >
            Secure invitation
          </Badge>
        </div>
        <div>
          <CardTitle className="text-2xl">
            Create your administrator account
          </CardTitle>
          <CardDescription className="mt-2 leading-6">
            Confirm your invitation and choose the
            password you will use for PoultryPulse.
          </CardDescription>
        </div>
      </CardHeader>

      <CardContent className="space-y-6 px-6 pb-6 sm:px-8 sm:pb-8">
        <div className="grid gap-3 rounded-2xl border border-border/70 bg-muted/30 p-4 sm:grid-cols-2">
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
              Farm
            </p>
            <p className="mt-1 font-semibold">
              {invitation.farm_name}
            </p>
            <p className="text-sm text-muted-foreground">
              {invitation.farm_code}
            </p>
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
              Administrator
            </p>
            <p className="mt-1 font-semibold">
              {invitation.administrator_name}
            </p>
            <p className="text-sm text-muted-foreground">
              {invitation.administrator_username}
            </p>
          </div>
          <div className="flex items-start gap-2 border-t border-border/60 pt-3 text-sm text-muted-foreground sm:col-span-2">
            <Clock3 className="mt-0.5 size-4 shrink-0" />
            <span>
              This one-time invitation expires{" "}
              {formatExpiry(invitation.expires_at)}.
            </span>
          </div>
        </div>

        <form className="space-y-4" onSubmit={submit}>
          {[
            {
              id: "newPassword",
              label: "New password",
              value: newPassword,
              change: setNewPassword,
            },
            {
              id: "confirmPassword",
              label: "Confirm password",
              value: confirmPassword,
              change: setConfirmPassword,
            },
          ].map((field) => (
            <div key={field.id} className="space-y-2">
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
                  value={field.value}
                  onChange={(event) =>
                    field.change(event.target.value)
                  }
                  autoComplete="new-password"
                  required
                  minLength={12}
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

          <div className="grid gap-2 rounded-2xl border border-border/70 bg-muted/25 p-4 sm:grid-cols-2">
            {passwordChecks.map((check) => (
              <div
                key={check.label}
                className="flex items-center gap-2 text-xs"
              >
                <span
                  className={
                    check.passed
                      ? "grid size-5 place-items-center rounded-full bg-primary/12 text-primary"
                      : "grid size-5 place-items-center rounded-full bg-muted text-muted-foreground"
                  }
                >
                  {check.passed ? (
                    <Check className="size-3" />
                  ) : (
                    <span className="size-1.5 rounded-full bg-current" />
                  )}
                </span>
                <span
                  className={
                    check.passed
                      ? "text-foreground"
                      : "text-muted-foreground"
                  }
                >
                  {check.label}
                </span>
              </div>
            ))}
            <div className="flex items-center gap-2 text-xs">
              <span
                className={
                  passwordsMatch
                    ? "grid size-5 place-items-center rounded-full bg-primary/12 text-primary"
                    : "grid size-5 place-items-center rounded-full bg-muted text-muted-foreground"
                }
              >
                {passwordsMatch ? (
                  <Check className="size-3" />
                ) : (
                  <span className="size-1.5 rounded-full bg-current" />
                )}
              </span>
              <span
                className={
                  passwordsMatch
                    ? "text-foreground"
                    : "text-muted-foreground"
                }
              >
                Passwords match
              </span>
            </div>
          </div>

          {error ? (
            <div
              role="alert"
              className="rounded-xl border border-destructive/25 bg-destructive/8 px-4 py-3 text-sm leading-6 text-destructive"
            >
              {error}
            </div>
          ) : null}

          <Button
            type="submit"
            className="h-12 w-full rounded-xl"
            disabled={
              pending ||
              !passwordIsStrong ||
              !passwordsMatch
            }
          >
            {pending ? (
              <LoaderCircle className="size-4 animate-spin" />
            ) : (
              <ShieldCheck className="size-4" />
            )}
            {pending
              ? "Activating account..."
              : "Activate administrator account"}
          </Button>
        </form>

        <p className="text-center text-xs leading-5 text-muted-foreground">
          The invitation token is used only in memory
          during activation and is removed from the
          browser address bar.
        </p>
      </CardContent>
    </Card>
  )
}
