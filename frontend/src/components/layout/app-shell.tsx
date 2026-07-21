import { AppSidebar } from "@/components/layout/app-sidebar"
import { FloatingQuickActions } from "@/components/layout/floating-quick-actions"
import { Topbar } from "@/components/layout/topbar"

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({
  children,
}: AppShellProps) {
  return (
    <div className="min-h-screen">
      <AppSidebar />
      <div className="lg:pl-[284px]">
        <Topbar />
        <main className="mx-auto w-full max-w-[1680px] px-4 py-5 sm:px-6 lg:px-8 lg:py-7">
          {children}
        </main>
      </div>
      <FloatingQuickActions />
    </div>
  )
}
