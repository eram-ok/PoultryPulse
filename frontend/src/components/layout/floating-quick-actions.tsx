"use client"

import Link from "next/link"
import { Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { quickActions } from "@/lib/navigation"

export function FloatingQuickActions() {
  return (
    <div className="fixed bottom-5 right-5 z-40 lg:hidden">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button
            size="icon"
            className="size-14 rounded-2xl shadow-2xl shadow-primary/30"
            aria-label="Open quick actions"
          >
            <Plus className="size-6" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent
          align="end"
          side="top"
          className="mb-2 w-64 rounded-2xl p-2"
        >
          <DropdownMenuLabel>Quick record</DropdownMenuLabel>
          <DropdownMenuSeparator />
          {quickActions.map((action) => {
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
    </div>
  )
}
