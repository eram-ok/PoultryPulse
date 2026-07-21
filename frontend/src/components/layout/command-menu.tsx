"use client"

import { useRouter } from "next/navigation"
import { Search } from "lucide-react"

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
import { navigationGroups, quickActions } from "@/lib/navigation"

interface CommandMenuProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CommandMenu({
  open,
  onOpenChange,
}: CommandMenuProps) {
  const router = useRouter()

  function navigate(href: string) {
    onOpenChange(false)
    router.push(href)
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange}>
      <CommandInput placeholder="Search modules and quick actions..." />
      <CommandList>
        <CommandEmpty>No PoultryPulse module found.</CommandEmpty>

        <CommandGroup heading="Quick actions">
          {quickActions.map((item, index) => {
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

        <CommandSeparator />

        {navigationGroups.map((group) => (
          <CommandGroup heading={group.label} key={group.label}>
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
        Search across the PoultryPulse workspace
      </div>
    </CommandDialog>
  )
}
