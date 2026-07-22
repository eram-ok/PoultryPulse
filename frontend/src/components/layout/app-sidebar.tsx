import { NavigationPanel } from "@/components/layout/navigation-panel"
import { cn } from "@/lib/utils"

export function AppSidebar({
  compact,
  onToggle,
}: {
  compact: boolean
  onToggle: () => void
}) {
  return (
    <aside
      className={cn(
        "floating-panel fixed bottom-4 left-4 top-4 z-40 hidden overflow-hidden rounded-[30px] transition-[width] duration-300 ease-out lg:block",
        compact ? "w-[88px]" : "w-[288px]",
      )}
    >
      <NavigationPanel
        compact={compact}
        onToggleCompact={onToggle}
      />
    </aside>
  )
}
