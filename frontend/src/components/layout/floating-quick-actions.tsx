"use client"

import { useState } from "react"
import { Plus, X } from "lucide-react"
import Link from "next/link"

import { useAuth } from "@/components/auth/auth-provider"
import { Button } from "@/components/ui/button"
import { allowedQuickActions } from "@/lib/navigation"

export function FloatingQuickActions() {
  const [open, setOpen] = useState(false)
  const { session } = useAuth()
  const actions = allowedQuickActions(
    session.permissions,
  )

  if (actions.length === 0) {
    return null
  }

  return (
    <div className="fixed bottom-5 right-5 z-40 flex flex-col items-end gap-2 lg:hidden">
      {open ? (
        <div className="flex flex-col items-end gap-2">
          {actions.map((action) => {
            const Icon = action.icon

            return (
              <Button
                key={action.href}
                asChild
                variant="outline"
                className="h-11 rounded-full bg-card/92 pr-4 shadow-lg backdrop-blur"
              >
                <Link
                  href={action.href}
                  onClick={() => setOpen(false)}
                >
                  <Icon className="size-4 text-primary" />
                  {action.label}
                </Link>
              </Button>
            )
          })}
        </div>
      ) : null}

      <Button
        size="icon"
        className="size-14 rounded-full shadow-xl shadow-primary/25"
        aria-label={
          open
            ? "Close quick actions"
            : "Open quick actions"
        }
        aria-expanded={open}
        onClick={() =>
          setOpen((current) => !current)
        }
      >
        {open ? (
          <X className="size-5" />
        ) : (
          <Plus className="size-5" />
        )}
      </Button>
    </div>
  )
}
