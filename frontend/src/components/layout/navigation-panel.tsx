"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  ChevronsUpDown,
  CloudSun,
  LifeBuoy,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react"

import { useAuth } from "@/components/auth/auth-provider"
import { PoultryPulseLogo } from "@/components/brand/poultry-pulse-logo"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { allowedNavigationGroups } from "@/lib/navigation"
import { cn } from "@/lib/utils"

interface NavigationPanelProps {
  onNavigate?: () => void
  compact?: boolean
  onToggleCompact?: () => void
}

export function NavigationPanel({
  onNavigate,
  compact = false,
  onToggleCompact,
}: NavigationPanelProps) {
  const pathname = usePathname()
  const { session } = useAuth()
  const groups = allowedNavigationGroups(session.permissions)
  const farmDetail = [
    session.farm.district,
    session.farm.farm_code,
  ]
    .filter(Boolean)
    .join(" · ")

  return (
    <div className="flex h-full flex-col bg-sidebar/72">
      <div
        className={cn(
          "flex border-b border-sidebar-border/70",
          compact
            ? "h-28 flex-col items-center justify-center gap-2 px-2"
            : "h-20 items-center justify-between px-5",
        )}
      >
        <Tooltip>
          <TooltipTrigger asChild>
            <Link
              href="/dashboard"
              onClick={onNavigate}
              aria-label="Return to PoultryPulse dashboard"
              className="rounded-2xl outline-none ring-offset-2 transition hover:scale-[1.02] focus-visible:ring-2 focus-visible:ring-sidebar-ring"
            >
              <PoultryPulseLogo compact={compact} />
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right">
            Return to dashboard
          </TooltipContent>
        </Tooltip>

        {onToggleCompact ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className={cn(
                  "shrink-0 rounded-xl text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  compact ? "size-8" : "size-9",
                )}
                onClick={onToggleCompact}
                aria-label={
                  compact
                    ? "Expand navigation"
                    : "Minimize navigation"
                }
              >
                {compact ? (
                  <PanelLeftOpen className="size-4" />
                ) : (
                  <PanelLeftClose className="size-4" />
                )}
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              {compact ? "Expand navigation" : "Minimize navigation"}
            </TooltipContent>
          </Tooltip>
        ) : null}
      </div>

      <div className={cn("pb-4 pt-4", compact ? "px-3" : "px-4")}>
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              type="button"
              className={cn(
                "group flex w-full items-center rounded-2xl border border-sidebar-border/80 bg-sidebar-accent/58 text-left shadow-sm transition hover:-translate-y-0.5 hover:bg-sidebar-accent hover:shadow-md",
                compact
                  ? "justify-center p-2.5"
                  : "gap-3 p-3",
              )}
              aria-label={`Current farm: ${session.farm.name}`}
            >
              <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/15 text-primary">
                <CloudSun className="size-5" />
              </div>

              {!compact ? (
                <>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold">
                      {session.farm.name}
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {farmDetail || session.farm.timezone}
                    </p>
                  </div>
                  <ChevronsUpDown className="size-4 text-muted-foreground transition group-hover:text-foreground" />
                </>
              ) : null}
            </button>
          </TooltipTrigger>
          {compact ? (
            <TooltipContent side="right">
              <p className="font-medium">{session.farm.name}</p>
              <p className="text-xs opacity-75">
                {farmDetail || session.farm.timezone}
              </p>
            </TooltipContent>
          ) : null}
        </Tooltip>
      </div>

      <ScrollArea
        className={cn(
          "scrollbar-subtle min-h-0 flex-1",
          compact ? "px-3" : "px-3",
        )}
      >
        <nav className="space-y-5 pb-6">
          {groups.map((group) => (
            <div key={group.label}>
              {!compact ? (
                <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.22em] text-muted-foreground/75">
                  {group.label}
                </p>
              ) : (
                <div className="mx-auto mb-2 h-px w-8 bg-sidebar-border/75" />
              )}

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
                          aria-label={compact ? item.label : undefined}
                          className={cn(
                            "group relative flex items-center rounded-xl text-sm font-medium transition duration-200",
                            compact
                              ? "h-11 justify-center px-2"
                              : "gap-3 px-3 py-2.5",
                            active
                              ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-lg shadow-primary/20"
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

                          {!compact ? (
                            <>
                              <span className="truncate">
                                {item.label}
                              </span>
                              {active ? (
                                <span className="ml-auto size-1.5 rounded-full bg-sidebar-primary-foreground/80" />
                              ) : null}
                            </>
                          ) : null}
                        </Link>
                      </TooltipTrigger>
                      <TooltipContent side="right">
                        <p className="font-medium">{item.label}</p>
                        <p className="max-w-52 text-xs opacity-75">
                          {item.description}
                        </p>
                      </TooltipContent>
                    </Tooltip>
                  )
                })}
              </div>
            </div>
          ))}
        </nav>
      </ScrollArea>

      <div
        className={cn(
          "border-t border-sidebar-border/70",
          compact ? "p-3" : "p-4",
        )}
      >
        {compact ? (
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="mx-auto flex rounded-xl text-muted-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                aria-label="Support information"
              >
                <LifeBuoy className="size-4" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="right">
              Contact your farm administrator for support.
            </TooltipContent>
          </Tooltip>
        ) : (
          <div className="rounded-2xl border border-primary/15 bg-gradient-to-br from-primary/10 via-primary/5 to-info/8 p-3.5">
            <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
              <LifeBuoy className="size-4 text-primary" />
              Need help?
            </div>
            <p className="text-xs leading-5 text-muted-foreground">
              Contact your farm administrator for account or workflow support.
            </p>
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 h-8 w-full justify-start rounded-lg px-2 text-xs"
            >
              View support centre
            </Button>
          </div>
        )}
      </div>
    </div>
  )
}
