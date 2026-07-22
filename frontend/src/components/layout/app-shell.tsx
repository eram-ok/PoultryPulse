"use client"

import { useState } from "react"

import { AppSidebar } from "@/components/layout/app-sidebar"
import { FloatingQuickActions } from "@/components/layout/floating-quick-actions"
import { Topbar } from "@/components/layout/topbar"
import { cn } from "@/lib/utils"

interface AppShellProps {
  children: React.ReactNode
}

export function AppShell({
  children,
}: AppShellProps) {
  const [sidebarCompact, setSidebarCompact] = useState(false)

  return (
    <div className="app-canvas relative min-h-screen overflow-x-clip">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      >
        <div className="absolute -right-24 -top-24 size-80 rounded-full bg-info/8 blur-3xl" />
        <div className="absolute -bottom-28 left-[18%] size-96 rounded-full bg-primary/8 blur-3xl" />
        <div className="absolute left-[48%] top-[42%] size-72 rounded-full bg-accent/6 blur-3xl" />
      </div>

      <AppSidebar
        compact={sidebarCompact}
        onToggle={() => setSidebarCompact((current) => !current)}
      />

      <div
        className={cn(
          "min-h-screen transition-[padding] duration-300 ease-out",
          sidebarCompact
            ? "lg:pl-[120px]"
            : "lg:pl-[320px]",
        )}
      >
        <Topbar />
        <main className="mx-auto w-full max-w-[1720px] px-3 pb-9 pt-4 sm:px-5 lg:px-6 lg:pb-10 lg:pt-5 xl:px-8">
          {children}
        </main>
      </div>

      <FloatingQuickActions />
    </div>
  )
}
