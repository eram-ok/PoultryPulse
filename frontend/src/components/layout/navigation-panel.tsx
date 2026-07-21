"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { ChevronsUpDown, CloudSun, LifeBuoy } from "lucide-react"

import { PoultryPulseLogo } from "@/components/brand/poultry-pulse-logo"
import { Button } from "@/components/ui/button"
import {
  ScrollArea,
} from "@/components/ui/scroll-area"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { navigationGroups } from "@/lib/navigation"
import { cn } from "@/lib/utils"

interface NavigationPanelProps {
  onNavigate?: () => void
}

export function NavigationPanel({
  onNavigate,
}: NavigationPanelProps) {
  const pathname = usePathname()

  return (
    <div className="flex h-full flex-col">
      <div className="flex h-20 items-center px-5">
        <PoultryPulseLogo />
      </div>

      <div className="px-4 pb-4">
        <button
          type="button"
          className="group flex w-full items-center gap-3 rounded-2xl border border-sidebar-border bg-sidebar-accent/55 p-3 text-left transition hover:bg-sidebar-accent"
        >
          <div className="grid size-10 place-items-center rounded-xl bg-primary/15 text-primary">
            <CloudSun className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-semibold">
              PoultryPulse Farm
            </p>
            <p className="truncate text-xs text-muted-foreground">
              Mukono · PP-FARM-001
            </p>
          </div>
          <ChevronsUpDown className="size-4 text-muted-foreground transition group-hover:text-foreground" />
        </button>
      </div>

      <ScrollArea className="min-h-0 flex-1 px-3">
        <nav className="space-y-5 pb-6">
          {navigationGroups.map((group) => (
            <div key={group.label}>
              <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground/75">
                {group.label}
              </p>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const active =
                    pathname === item.href ||
                    pathname.startsWith(`${item.href}/`)
                  const Icon = item.icon

                  return (
                    <Tooltip key={item.href}>
                      <TooltipTrigger asChild>
                        <Link
                          href={item.href}
                          onClick={onNavigate}
                          className={cn(
                            "group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition",
                            active
                              ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-lg shadow-primary/15"
                              : "text-sidebar-foreground/72 hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                          )}
                        >
                          <Icon
                            className={cn(
                              "size-[18px] shrink-0",
                              active
                                ? "text-sidebar-primary-foreground"
                                : "text-muted-foreground transition group-hover:text-foreground",
                            )}
                          />
                          <span className="truncate">
                            {item.label}
                          </span>
                          {active ? (
                            <span className="ml-auto size-1.5 rounded-full bg-sidebar-primary-foreground/80" />
                          ) : null}
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent side="right">
                        {item.description}
                      </TooltipContent>
                    </Tooltip>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      <div className="border-t border-sidebar-border p-4">
        <div className="rounded-2xl border border-primary/15 bg-primary/8 p-3.5">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
            <LifeBuoy className="size-4 text-primary" />
            Need help?
          </div>
          <p className="text-xs leading-5 text-muted-foreground">
            Open the workshop guide or contact your farm administrator.
          </p>
          <Button
            variant="ghost"
            size="sm"
            className="mt-2 h-8 w-full justify-start rounded-lg px-2 text-xs"
          >
            View support centre
          </Button>
        </div>
      </div>
    </div>
  )
}
