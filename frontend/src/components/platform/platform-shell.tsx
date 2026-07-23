"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  Building2,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  UserRound,
} from "lucide-react"

import {
  usePlatformAuth,
} from "@/components/platform/platform-auth-provider"
import {
  PoultryPulseLogo,
} from "@/components/brand/poultry-pulse-logo"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface PlatformShellProps {
  children: React.ReactNode
}

const navigation = [
  {
    href: "/platform/dashboard",
    label: "Overview",
    icon: LayoutDashboard,
  },
] as const

export function PlatformShell({
  children,
}: PlatformShellProps) {
  const pathname = usePathname()
  const { session, logout } = usePlatformAuth()

  return (
    <div className="app-canvas relative min-h-screen overflow-x-clip">
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 -z-10 overflow-hidden"
      >
        <div className="absolute -right-24 -top-24 size-80 rounded-full bg-info/8 blur-3xl" />
        <div className="absolute -bottom-28 left-[18%] size-96 rounded-full bg-primary/8 blur-3xl" />
      </div>

      <aside className="floating-panel fixed bottom-4 left-4 top-4 z-40 hidden w-[288px] overflow-hidden rounded-[30px] lg:flex lg:flex-col">
        <div className="flex h-20 items-center border-b border-sidebar-border/70 px-5">
          <Link
            href="/platform/dashboard"
            aria-label="Platform dashboard"
          >
            <PoultryPulseLogo />
          </Link>
        </div>

        <div className="border-b border-sidebar-border/70 p-4">
          <div className="rounded-2xl border border-primary/20 bg-primary/8 p-3.5">
            <div className="flex items-center gap-3">
              <div className="grid size-10 place-items-center rounded-xl bg-primary/15 text-primary">
                <ShieldCheck className="size-5" />
              </div>
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">
                  Platform control
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  Super administrator
                </p>
              </div>
            </div>
          </div>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navigation.map((item) => {
            const Icon = item.icon
            const active =
              pathname === item.href ||
              pathname.startsWith(
                `${item.href}/`,
              )

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                  active
                    ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-lg shadow-primary/20"
                    : "text-sidebar-foreground/72 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                )}
              >
                <Icon className="size-[18px]" />
                {item.label}
              </Link>
            )
          })}
        </nav>

        <div className="border-t border-sidebar-border/70 p-4">
          <div className="mb-3 flex items-center gap-3 rounded-2xl bg-sidebar-accent/55 p-3">
            <div className="grid size-9 place-items-center rounded-xl bg-background/70">
              <UserRound className="size-4" />
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold">
                {session.user.full_name}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                @{session.user.username}
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            className="w-full justify-start rounded-xl text-muted-foreground"
            onClick={() => void logout()}
          >
            <LogOut className="size-4" />
            Sign out
          </Button>
        </div>
      </aside>

      <div className="min-h-screen lg:pl-[320px]">
        <header className="sticky top-0 z-30 border-b border-border/65 bg-background/82 backdrop-blur-xl">
          <div className="mx-auto flex h-18 w-full max-w-[1720px] items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-3">
              <div className="lg:hidden">
                <PoultryPulseLogo compact />
              </div>
              <div>
                <p className="text-sm font-semibold">
                  Platform administration
                </p>
                <p className="hidden text-xs text-muted-foreground sm:block">
                  Multi-tenant governance and customer-farm control
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Badge
                variant="outline"
                className="hidden rounded-full border-primary/25 bg-primary/8 text-primary sm:flex"
              >
                <Building2 className="mr-1 size-3" />
                Isolated platform session
              </Badge>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="rounded-xl lg:hidden"
                aria-label="Sign out"
                onClick={() => void logout()}
              >
                <LogOut className="size-4" />
              </Button>
            </div>
          </div>
        </header>

        <main className="mx-auto w-full max-w-[1720px] px-3 pb-9 pt-4 sm:px-5 lg:px-6 lg:pb-10 lg:pt-5 xl:px-8">
          {children}
        </main>
      </div>
    </div>
  )
}
