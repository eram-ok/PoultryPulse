import { NavigationPanel } from "@/components/layout/navigation-panel"

export function AppSidebar() {
  return (
    <aside className="fixed inset-y-0 left-0 z-40 hidden w-[284px] border-r border-sidebar-border bg-sidebar/96 backdrop-blur-xl lg:block">
      <NavigationPanel />
    </aside>
  )
}
