import {
  KeyRound,
  ShieldCheck,
} from "lucide-react"

import {
  ChangePasswordForm,
} from "@/components/auth/change-password-form"
import { PoultryPulseLogo } from "@/components/brand/poultry-pulse-logo"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { requireServerSession } from "@/lib/auth/session"

export const metadata = {
  title: "Change password",
}

export default async function ChangePasswordPage() {
  const session = await requireServerSession({
    allowPasswordChange: true,
    returnTo: "/change-password",
  })

  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden p-5 sm:p-8">
      <div
        aria-hidden="true"
        className="surface-grid absolute inset-0 opacity-25"
      />
      <div className="relative w-full max-w-lg">
        <div className="mb-7">
          <PoultryPulseLogo />
        </div>

        <Card className="rounded-3xl border-border/75 bg-card/90 shadow-2xl shadow-black/10 backdrop-blur-xl">
          <CardHeader className="space-y-4 p-6 sm:p-8">
            <div className="flex items-center justify-between gap-4">
              <div className="grid size-12 place-items-center rounded-2xl bg-primary/12 text-primary">
                <KeyRound className="size-5" />
              </div>
              {session.user.must_change_password ? (
                <span className="rounded-full border border-warning/25 bg-warning/8 px-3 py-1 text-xs font-medium text-warning">
                  Required
                </span>
              ) : (
                <ShieldCheck className="size-5 text-primary" />
              )}
            </div>
            <div>
              <CardTitle className="text-2xl">
                Secure your account
              </CardTitle>
              <CardDescription className="mt-2 leading-6">
                {session.user.must_change_password
                  ? "Your administrator requires you to replace the temporary password before continuing."
                  : "Change the password for your PoultryPulse account."}
              </CardDescription>
            </div>
          </CardHeader>
          <CardContent className="px-6 pb-6 sm:px-8 sm:pb-8">
            <ChangePasswordForm />
          </CardContent>
        </Card>
      </div>
    </main>
  )
}
