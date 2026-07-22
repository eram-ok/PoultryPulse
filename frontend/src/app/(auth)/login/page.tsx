import { redirect } from "next/navigation"
import {
  Activity,
  BarChart3,
  LockKeyhole,
  ShieldCheck,
  Sparkles,
} from "lucide-react"

import { LoginForm } from "@/components/auth/login-form"
import { PoultryPulseLogo } from "@/components/brand/poultry-pulse-logo"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { hasServerAuthCookie } from "@/lib/auth/cookies"
import { safeReturnTo } from "@/lib/auth/security"

export const metadata = {
  title: "Sign in",
}

interface LoginPageProps {
  searchParams: Promise<{
    next?: string
    reason?: string
    passwordChanged?: string
    accountActivated?: string
  }>
}

export default async function LoginPage({
  searchParams,
}: LoginPageProps) {
  if (await hasServerAuthCookie()) {
    redirect("/dashboard")
  }

  const parameters = await searchParams
  const nextPath = safeReturnTo(parameters.next ?? null)
  const sessionMessage =
    parameters.reason === "session-expired"
      ? "Your session expired. Sign in again to continue."
      : parameters.reason === "api-unavailable"
        ? "The API was temporarily unavailable. Try signing in again."
        : null
  const successMessage =
    parameters.accountActivated === "1"
      ? "Administrator account activated. Sign in with your farm code, username, and new password."
      : parameters.passwordChanged === "1"
        ? "Password updated. Sign in with your new password."
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
              Farm intelligence workspace
            </Badge>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight xl:text-5xl">
              Every important farm signal, secured in one place.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-muted-foreground">
              Monitor production, flock health, stock,
              sales, finance, alerts, and operational
              accountability from a single modern workspace.
            </p>

            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              {[
                {
                  icon: Activity,
                  title: "Live pulse",
                  detail: "Real farm metrics",
                },
                {
                  icon: BarChart3,
                  title: "Clear trends",
                  detail: "Actionable insight",
                },
                {
                  icon: ShieldCheck,
                  title: "Protected",
                  detail: "Role-based access",
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
            PoultryPulse · Know your flock. Grow your farm.
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
                  <LockKeyhole className="size-5" />
                </div>
                <div>
                  <CardTitle className="text-2xl">
                    Welcome back
                  </CardTitle>
                  <CardDescription className="mt-2 leading-6">
                    Sign in with your PoultryPulse account to
                    access your farm workspace.
                  </CardDescription>
                </div>
              </CardHeader>
              <CardContent className="px-6 pb-6 sm:px-8 sm:pb-8">
                {successMessage ? (
                  <div className="mb-5 rounded-xl border border-primary/25 bg-primary/8 px-4 py-3 text-sm leading-6 text-primary">
                    {successMessage}
                  </div>
                ) : null}

                {sessionMessage ? (
                  <div className="mb-5 rounded-xl border border-warning/25 bg-warning/8 px-4 py-3 text-sm text-warning">
                    {sessionMessage}
                  </div>
                ) : null}

                <LoginForm nextPath={nextPath} />

                <p className="mt-6 text-center text-xs leading-5 text-muted-foreground">
                  Access is limited to authorized farm users.
                  Contact your administrator if you cannot sign
                  in.
                </p>
              </CardContent>
            </Card>
          </div>
        </section>
      </div>
    </main>
  )
}
