import { AuthProvider } from "@/components/auth/auth-provider"
import { AppShell } from "@/components/layout/app-shell"
import { requireServerSession } from "@/lib/auth/session"

interface ApplicationLayoutProps {
  children: React.ReactNode
}

export default async function ApplicationLayout({
  children,
}: ApplicationLayoutProps) {
  const session = await requireServerSession({
    returnTo: "/dashboard",
  })

  return (
    <AuthProvider initialSession={session}>
      <AppShell>{children}</AppShell>
    </AuthProvider>
  )
}
