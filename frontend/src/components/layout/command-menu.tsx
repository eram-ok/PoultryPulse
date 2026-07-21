"use client"

import { useRouter } from "next/navigation"
import { Search } from "lucide-react"

import { useAuth } from "@/components/auth/auth-provider"
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
  CommandShortcut,
} from "@/components/ui/command"
import {
  allowedNavigationGroups,
  allowedQuickActions,
} from "@/lib/navigation"

interface CommandMenuProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandMenu({
  open,
  onOpenChange,
}: CommandMenuProps) {
  const router = useRouter()
  const { session } = useAuth()
  const groups = allowedNavigationGroups(
    session.permissions,
  )
  const actions = allowedQuickActions(
    session.permissions,
  )

  function navigate(href: string) {
    onOpenChange(false)
    router.push(href)
  }

  return (
    <CommandDialog
      open={open}
      onOpenChange={onOpenChange}
    >
      <CommandInput placeholder="Search available modules and actions..." />
      <CommandList>
        <CommandEmpty>
          No permitted PoultryPulse module found.
        </CommandEmpty>

        {actions.length > 0 ? (
          <CommandGroup heading="Quick actions">
            {actions.map((item, index) => {
              const Icon = item.icon
              return (
                <CommandItem
                  key={item.href}
                  value={`${item.label} ${item.description}`}
                  onSelect={() => navigate(item.href)}
                >
                  <Icon className="size-4" />
                  <span>{item.label}</span>
                  <CommandShortcut>
                    ⌘{index + 1}
                  </CommandShortcut>
                </CommandItem>
              )
            })}
          </CommandGroup>
        ) : null}

        {actions.length > 0 ? (
          <CommandSeparator />
        ) : null}

        {groups.map((group) => (
          <CommandGroup
            heading={group.label}
            key={group.label}
          >
            {group.items.map((item) => {
              const Icon = item.icon
              return (
                <CommandItem
                  key={item.href}
                  value={`${item.label} ${item.description}`}
                  onSelect={() => navigate(item.href)}
                >
                  <Icon className="size-4" />
                  <div>
                    <p>{item.label}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.description}
                    </p>
                  </div>
                </CommandItem>
              )
            })}
          </CommandGroup>
        ))}
      </CommandList>
      <div className="flex items-center gap-2 border-t px-3 py-2 text-[11px] text-muted-foreground">
        <Search className="size-3.5" />
        Search the modules available to your account
      </div>
    </CommandDialog>
  )
}
