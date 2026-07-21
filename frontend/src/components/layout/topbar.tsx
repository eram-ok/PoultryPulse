"use client"

import { useEffect, useState } from "react"
import {
  Bell,
  ChevronDown,
  LogOut,
  Search,
  Settings,
  UserRound,
} from "lucide-react"

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

export function Topbar() {
  const [commandOpen, setCommandOpen] = useState(false)

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
            <span className="truncate">Search PoultryPulse...</span>
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

            <Button
              variant="ghost"
              size="icon"
              className="relative rounded-xl"
              aria-label="View alerts"
            >
              <Bell className="size-[18px]" />
              <span className="absolute right-2 top-2 size-2 rounded-full bg-destructive ring-2 ring-background" />
            </Button>

            <Separator orientation="vertical" className="mx-2 h-7" />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  className="h-11 gap-2 rounded-xl px-2"
                >
                  <Avatar className="size-8">
                    <AvatarFallback className="bg-primary/15 text-xs font-semibold text-primary">
                      PA
                    </AvatarFallback>
                  </Avatar>
                  <div className="hidden min-w-0 text-left md:block">
                    <p className="max-w-36 truncate text-xs font-semibold">
                      PoultryPulse Admin
                    </p>
                    <div className="flex items-center gap-1">
                      <Badge
                        variant="secondary"
                        className="h-4 rounded-full px-1.5 text-[9px]"
                      >
                        Administrator
                      </Badge>
                    </div>
                  </div>
                  <ChevronDown className="hidden size-3.5 text-muted-foreground md:block" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <p className="text-sm">PoultryPulse Admin</p>
                  <p className="text-xs font-normal text-muted-foreground">
                    admin@poultrypulse.local
                  </p>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem>
                  <UserRound className="size-4" />
                  Profile
                </DropdownMenuItem>
                <DropdownMenuItem>
                  <Settings className="size-4" />
                  Preferences
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem variant="destructive">
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
