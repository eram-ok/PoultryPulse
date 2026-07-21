"use client"

import { useState } from "react"
import { Menu } from "lucide-react"

import { NavigationPanel } from "@/components/layout/navigation-panel"
import { Button } from "@/components/ui/button"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet"

export function MobileNavigation() {
  const [open, setOpen] = useState(false)

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="rounded-xl lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </Button>
      </SheetTrigger>
      <SheetContent
        side="left"
        className="w-[292px] border-sidebar-border bg-sidebar p-0"
      >
        <SheetTitle className="sr-only">
          PoultryPulse navigation
        </SheetTitle>
        <SheetDescription className="sr-only">
          Navigate to PoultryPulse farm modules.
        </SheetDescription>
        <NavigationPanel onNavigate={() => setOpen(false)} />
      </SheetContent>
    </Sheet>
  )
}
