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
          className="rounded-xl border border-border/55 bg-card/60 shadow-sm lg:hidden"
          aria-label="Open navigation"
        >
          <Menu className="size-5" />
        </Button>
      </SheetTrigger>

      <SheetContent
        side="left"
        className="w-[316px] border-none bg-transparent p-3 shadow-none"
      >
        <SheetTitle className="sr-only">
          PoultryPulse navigation
        </SheetTitle>
        <SheetDescription className="sr-only">
          Navigate to PoultryPulse farm modules.
        </SheetDescription>

        <div className="floating-panel h-full overflow-hidden rounded-[28px]">
          <NavigationPanel onNavigate={() => setOpen(false)} />
        </div>
      </SheetContent>
    </Sheet>
  )
}
