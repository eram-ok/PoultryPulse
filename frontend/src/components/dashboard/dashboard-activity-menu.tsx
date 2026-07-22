"use client"

import Link from "next/link"
import { Plus, Sparkles } from "lucide-react"

import { useAuth } from "@/components/auth/auth-provider"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { allowedQuickActions } from "@/lib/navigation"

export function DashboardActivityMenu() {
  const { session } = useAuth()
  const actions = allowedQuickActions(session.permissions)

  if (actions.length === 0) {
    return null
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button className="rounded-xl shadow-lg shadow-primary/20">
          <Plus className="size-4" />
          Record activity
          <Sparkles className="size-3.5 opacity-75" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent
        align="end"
        className="w-72 rounded-2xl p-2"
      >
        <DropdownMenuLabel>Choose an activity</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {actions.map((action) => {
          const Icon = action.icon

          return (
            <DropdownMenuItem
              key={action.href}
              asChild
              className="rounded-xl p-3"
            >
              <Link href={action.href}>
                <div className="grid size-9 place-items-center rounded-xl bg-primary/10 text-primary">
                  <Icon className="size-4" />
                </div>
                <div>
                  <p className="font-medium">{action.label}</p>
                  <p className="text-xs text-muted-foreground">
                    {action.description}
                  </p>
                </div>
              </Link>
            </DropdownMenuItem>
          )
        })}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
