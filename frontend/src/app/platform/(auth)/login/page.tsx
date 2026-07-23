import { redirect } from "next/navigation"
import {
  Building2,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
} from "lucide-react"

import {
  PoultryPulseLogo,
} from "@/components/brand/poultry-pulse-logo"
import {
  PlatformLoginForm,
} from "@/components/platform/platform-login-form"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  hasServerPlatformAuthCookie,
} from "@/lib/platform-auth/cookies"
import {
  safePlatformReturnTo,
} from "@/lib/platform-auth/security"

export const metadata = {
  title: "Platform administration sign in",
  robots: {
    index: false,
    follow: false,
  },
}

interface PlatformLoginPageProps {
  searchParams: Promise<{
    next?: string
    reason?: string
    passwordChanged?: string
  }>
}

export default async function PlatformLoginPage({
  searchParams,
}: PlatformLoginPageProps) {
  const parameters = await searchParams

  if (
    !parameters.reason &&
    await hasServerPlatformAuthCookie()
  ) {
    redirect("/platform/dashboard")
  }

  const nextPath = safePlatformReturnTo(
    parameters.next,
  )
  const message =
    parameters.passwordChanged === "1"
      ? "Platform password updated. Sign in with your new password."
      : parameters.reason ===
          "session-expired"
        ? "Your platform session expired. Sign in again."
        : parameters.reason ===
            "api-unavailable"
          ? "The API was temporarily unavailable. Try again."
          : parameters.reason ===
              "super-admin-required"
            ? "A platform super-administrator account is required."
            : null

  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
      <div
        aria-hidden="true"
        className="surface-grid absolute inset-0 opacity-25"
      />

      <div className="relative grid min-h-screen lg:grid-cols-[minmax(0,1.05fr)_minmax(420px,0.95fr)]">
        <section className="hidden border-r border-border/70 bg-sidebar/72 p-10 lg:flex lg:flex-col lg:justify-between xl:p-14">
          <PoultryPulseLogo />

          <div className="max-w-xl">
            <Badge
              variant="outline"
              className="rounded-full border-primary/25 bg-primary/8 text-primary"
            >
              <Sparkles className="mr-1 size-3" />
              Platform control plane
            </Badge>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight xl:text-5xl">
              Govern every customer farm without entering
              a tenant session.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-muted-foreground">
              Platform identities are separate from farm
              users and provide audited control over farm
              onboarding, lifecycle, and service status.
            </p>

            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              {[
                {
                  icon: ShieldCheck,
                  title: "Separated",
                  detail: "Independent identity",
                },
                {
                  icon: Building2,
                  title: "Multi-tenant",
                  detail: "Farm isolation",
                },
                {
                  icon: LockKeyhole,
                  title: "Protected",
                  detail: "HttpOnly sessions",
                },
              ].map((item) => {
                const Icon = item.icon

                return (
                  <div
                    key={item.title}
                    className="rounded-2xl border border-border/70 bg-card/55 p-4 backdrop-blur"
                  >
                    <Icon className="size-5 text-primary" />
                    <p className="mt-4 text-sm font-semibold">
                      {item.title}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {item.detail}
                    </p>
                  </div>
                )
              })}
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            PoultryPulse platform administration
          </p>
        </section>

        <section className="flex items-center justify-center p-5 sm:p-8 lg:p-12">
          <div className="w-full max-w-md">
            <div className="mb-8 lg:hidden">
              <PoultryPulseLogo />
            </div>

            <Card className="rounded-3xl border-border/75 bg-card/88 shadow-2xl shadow-black/10 backdrop-blur-xl">
              <CardHeader className="space-y-3 p-6 sm:p-8">
                <div className="grid size-12 place-items-center rounded-2xl bg-primary/12 text-primary">
                  <ShieldCheck className="size-5" />
                </div>
                <div>
                  <CardTitle className="text-2xl">
                    Platform sign in
                  </CardTitle>
                  <CardDescription className="mt-2 leading-6">
                    Use your PoultryPulse platform
                    administrator identity.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="px-6 pb-6 sm:px-8 sm:pb-8">
                {message ? (
                  <div className="mb-5 rounded-xl border border-primary/25 bg-primary/8 px-4 py-3 text-sm leading-6 text-primary">
                    {message}
                  </div>
                ) : null}

                <PlatformLoginForm
                  nextPath={nextPath}
                />

                <p className="mt-6 text-center text-xs leading-5 text-muted-foreground">
                  Farm administrators must use the normal
                  farm sign-in page.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  )
}
