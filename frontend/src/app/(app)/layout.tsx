import { AppShell } from "@/components/layout/app-shell"

interface ApplicationLayoutProps {
  children: React.ReactNode
}

export default function ApplicationLayout({
  children,
}: ApplicationLayoutProps) {
  return <AppShell>{children}</AppShell>
}
