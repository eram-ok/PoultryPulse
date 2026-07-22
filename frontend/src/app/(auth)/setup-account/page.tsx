import { Suspense } from "react"
import {
  KeyRound,
  ShieldCheck,
  Sparkles,
  UserCheck,
} from "lucide-react"

import {
  SetupAccountWorkspace,
} from "@/components/auth/setup-account-workspace"
import {
  PoultryPulseLogo,
} from "@/components/brand/poultry-pulse-logo"
import { Badge } from "@/components/ui/badge"

export const metadata = {
  title: "Set up administrator account",
  robots: {
    index: false,
    follow: false,
  },
}

export default function SetupAccountPage() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
      <div
        aria-hidden="true"
        className="surface-grid absolute inset-0 opacity-25"
      />

      <div className="relative grid min-h-screen lg:grid-cols-[minmax(0,1.05fr)_minmax(440px,0.95fr)]">
        <section className="hidden border-r border-border/70 bg-sidebar/72 p-10 lg:flex lg:flex-col lg:justify-between xl:p-14">
          <PoultryPulseLogo />

          <div className="max-w-xl">
            <Badge
              variant="outline"
              className="rounded-full border-primary/25 bg-primary/8 text-primary"
            >
              <Sparkles className="mr-1 size-3" />
              Protected farm onboarding
            </Badge>
            <h1 className="mt-6 text-4xl font-semibold tracking-tight xl:text-5xl">
              Start your farm workspace with a secure
              administrator identity.
            </h1>
            <p className="mt-5 max-w-lg text-base leading-7 text-muted-foreground">
              Your invitation is verified before access is
              activated. Create a strong password, then
              continue to your isolated PoultryPulse farm.
            </p>

            <div className="mt-9 grid gap-3 sm:grid-cols-3">
              {[
                {
                  icon: KeyRound,
                  title: "One-time",
                  detail: "Expiring setup link",
                },
                {
                  icon: UserCheck,
                  title: "Verified",
                  detail: "Named administrator",
                },
                {
                  icon: ShieldCheck,
                  title: "Protected",
                  detail: "Isolated farm access",
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
          <div className="w-full max-w-lg">
            <div className="mb-8 lg:hidden">
              <PoultryPulseLogo />
            </div>

            <Suspense
              fallback={
                <div className="min-h-80 rounded-3xl border border-border/75 bg-card/88" />
              }
            >
              <SetupAccountWorkspace />
            </Suspense>
          </div>
        </section>
      </div>
    </main>
  )
}
