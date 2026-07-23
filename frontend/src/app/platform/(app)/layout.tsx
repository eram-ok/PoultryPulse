import {
  PlatformAuthProvider,
} from "@/components/platform/platform-auth-provider"
import {
  PlatformShell,
} from "@/components/platform/platform-shell"
import {
  requirePlatformServerSession,
} from "@/lib/platform-auth/session"

interface PlatformLayoutProps {
  children: React.ReactNode
}

export default async function PlatformLayout({
  children,
}: PlatformLayoutProps) {
  const session =
    await requirePlatformServerSession({
      returnTo: "/platform/dashboard",
    })

  return (
    <PlatformAuthProvider
      initialSession={session}
    >
      <PlatformShell>
        {children}
      </PlatformShell>
    </PlatformAuthProvider>
  )
}
