"use client"

import {
  useEffect,
  useMemo,
  useState,
} from "react"
import Link from "next/link"
import {
  Bell,
  ChevronDown,
  KeyRound,
  LogOut,
  Search,
  Settings,
  UserRound,
} from "lucide-react"

import { useAuth } from "@/components/auth/auth-provider"
import { CommandMenu } from "@/components/layout/command-menu"
import { MobileNavigation } from "@/components/layout/mobile-navigation"
import { ThemeToggle } from "@/components/layout/theme-toggle"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Separator } from "@/components/ui/separator"
import { browserApiRequest } from "@/lib/api/browser"
import type { AlertCountsResponse } from "@/lib/api/types"

export function Topbar() {
  const [commandOpen, setCommandOpen] = useState(false)
  const [alertCount, setAlertCount] = useState(0)
  const { session, logout } = useAuth()
  const canViewAlerts =
    session.permissions.includes("alerts.view")
  const primaryRole =
    session.roles[0] ?? "Farm user"
  const initials = useMemo(
    () =>
      `${session.user.first_name.charAt(
        0,
      )}${session.user.last_name.charAt(0)}`.toUpperCase(),
    [session.user.first_name, session.user.last_name],
  )

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.key.toLowerCase() === "k"
      ) {
        event.preventDefault()
        setCommandOpen((current) => !current)
      }
    }

    window.addEventListener("keydown", handleKeyDown)
    return () =>
      window.removeEventListener("keydown", handleKeyDown)
  }, [])

  useEffect(() => {
    if (!canViewAlerts) {
      return
    }

    const controller = new AbortController()

    browserApiRequest<AlertCountsResponse>(
      "/alerts/counts",
      {
        signal: controller.signal,
      },
    )
      .then((counts) => {
        setAlertCount(counts.unread)
      })
      .catch(() => {
        setAlertCount(0)
      })

    return () => controller.abort()
  }, [canViewAlerts])

  return (
    <>
      <header className="sticky top-0 z-30 border-b border-border/70 bg-background/88 backdrop-blur-xl supports-[backdrop-filter]:bg-background/72">
        <div className="flex h-16 items-center gap-3 px-4 sm:px-6 lg:px-8">
          <MobileNavigation />

          <Button
            variant="outline"
            className="hidden h-10 max-w-md flex-1 justify-start rounded-xl border-border/80 bg-card/70 text-muted-foreground shadow-sm sm:flex"
            onClick={() => setCommandOpen(true)}
          >
            <Search className="size-4" />
            <span className="truncate">
              Search PoultryPulse...
            </span>
            <kbd className="ml-auto rounded-md border bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              Ctrl K
            </kbd>
          </Button>

          <div className="ml-auto flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="rounded-xl sm:hidden"
              onClick={() => setCommandOpen(true)}
              aria-label="Search PoultryPulse"
            >
              <Search className="size-[18px]" />
            </Button>

            <ThemeToggle />

            {canViewAlerts ? (
              <Button
                asChild
                variant="ghost"
                size="icon"
                className="relative rounded-xl"
              >
                <Link
                  href="/alerts"
                  aria-label={`View alerts${
                    alertCount
                      ? `, ${alertCount} unread`
                      : ""
                  }`}
                >
                  <Bell className="size-[18px]" />
                  {alertCount > 0 ? (
                    <span className="absolute right-1.5 top-1.5 grid min-h-4 min-w-4 place-items-center rounded-full bg-destructive px-1 text-[9px] font-semibold text-white ring-2 ring-background">
                      {alertCount > 99 ? "99+" : alertCount}
                    </span>
                  ) : null}
                </Link>
              </Button>
            ) : null}

            <Separator
              orientation="vertical"
              className="mx-2 h-7"
            />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="h-11 gap-2 rounded-xl px-2"
                >
                  <Avatar className="size-8">
                    <AvatarFallback className="bg-primary/15 text-xs font-semibold text-primary">
                      {initials}
                    </AvatarFallback>
                  </Avatar>
                  <div className="hidden min-w-0 text-left md:block">
                    <p className="max-w-36 truncate text-xs font-semibold">
                      {session.user.full_name}
                    </p>
                    <div className="flex items-center gap-1">
                      <Badge
                        variant="secondary"
                        className="h-4 max-w-32 truncate rounded-full px-1.5 text-[9px]"
                      >
                        {primaryRole}
                      </Badge>
                    </div>
                  </div>
                  <ChevronDown className="hidden size-3.5 text-muted-foreground md:block" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                align="end"
                className="w-64"
              >
                <DropdownMenuLabel>
                  <p className="truncate text-sm">
                    {session.user.full_name}
                  </p>
                  <p className="truncate text-xs font-normal text-muted-foreground">
                    {session.user.email ??
                      `@${session.user.username}`}
                  </p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem asChild>
                  <Link href="/profile">
                    <UserRound className="size-4" />
                    Profile
                  </Link>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <Link href="/change-password">
                    <KeyRound className="size-4" />
                    Change password
                  </Link>
                </DropdownMenuItem>
                {session.permissions.includes(
                  "farms.view",
                ) ? (
                  <DropdownMenuItem asChild>
                    <Link href="/settings">
                      <Settings className="size-4" />
                      Farm settings
                    </Link>
                  </DropdownMenuItem>
                ) : null}
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  variant="destructive"
                  onSelect={() => {
                    void logout()
                  }}
                >
                  <LogOut className="size-4" />
                  Sign out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </header>

      <CommandMenu
        open={commandOpen}
        onOpenChange={setCommandOpen}
      />
    </>
  )
}
