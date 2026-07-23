import {
  KeyRound,
  ShieldCheck,
} from "lucide-react"

import {
  PoultryPulseLogo,
} from "@/components/brand/poultry-pulse-logo"
import {
  PlatformChangePasswordForm,
} from "@/components/platform/platform-change-password-form"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  requirePlatformServerSession,
} from "@/lib/platform-auth/session"

export const metadata = {
  title: "Change platform password",
  robots: {
    index: false,
    follow: false,
  },
}

export default async function PlatformChangePasswordPage() {
  const session =
    await requirePlatformServerSession({
      allowPasswordChange: true,
      returnTo: "/platform/change-password",
    })

  return (
    <main className="relative min-h-screen overflow-hidden bg-background">
      <div
        aria-hidden="true"
        className="surface-grid absolute inset-0 opacity-25"
      />

      <div className="relative mx-auto flex min-h-screen w-full max-w-xl flex-col justify-center px-5 py-10 sm:px-8">
        <div className="mb-8">
          <PoultryPulseLogo />
        </div>

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
                <ShieldCheck className="mr-1 size-3" />
                Platform identity
              </Badge>
            </div>

            <div>
              <CardTitle className="text-2xl">
                Change platform password
              </CardTitle>
              <CardDescription className="mt-2 leading-6">
                Create a secure password before accessing
                the PoultryPulse platform administration
                workspace.
              </CardDescription>
            </div>
          </CardHeader>

          <CardContent className="space-y-5 px-6 pb-6 sm:px-8 sm:pb-8">
            <div className="rounded-2xl border border-border/70 bg-muted/30 p-4">
              <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">
                Signed-in platform administrator
              </p>
              <p className="mt-2 font-semibold">
                {session.user.full_name}
              </p>
              <p className="text-sm text-muted-foreground">
                @{session.user.username}
              </p>
            </div>

            <PlatformChangePasswordForm />

            <p className="text-center text-xs leading-5 text-muted-foreground">
              Changing the password revokes all existing
              platform sessions. You will sign in again
              afterward.
            </p>
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
