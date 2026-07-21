import type { LucideIcon } from "lucide-react"
import {
  Activity,
  Bell,
  Bird,
  Boxes,
  BriefcaseBusiness,
  ClipboardList,
  Egg,
  FileChartColumn,
  HeartPulse,
  House,
  LayoutDashboard,
  PackageOpen,
  ReceiptText,
  ScrollText,
  Settings,
  ShieldCheck,
  ShoppingCart,
  Stethoscope,
  Users,
  Utensils,
  WalletCards,
} from "lucide-react"

export interface NavigationItem {
  label: string
  href: string
  icon: LucideIcon
  description: string
  permission?: string
}

export interface NavigationGroup {
  label: string
  items: NavigationItem[]
}

export const navigationGroups: NavigationGroup[] = [
  {
    label: "Overview",
    items: [
      {
        label: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
        description: "Farm performance at a glance",
        permission: "dashboard.view",
      },
      {
        label: "Reports",
        href: "/reports",
        icon: FileChartColumn,
        description: "Trends and management insights",
        permission: "reports.view",
      },
      {
        label: "Alerts",
        href: "/alerts",
        icon: Bell,
        description: "Operational issues and reminders",
        permission: "alerts.view",
      },
    ],
  },
  {
    label: "Farm operations",
    items: [
      {
        label: "Flocks",
        href: "/flocks",
        icon: Bird,
        description: "Bird populations and placements",
        permission: "flocks.view",
      },
      {
        label: "Houses",
        href: "/houses",
        icon: House,
        description: "Farm housing and occupancy",
        permission: "houses.view",
      },
      {
        label: "Production",
        href: "/production",
        icon: Egg,
        description: "Daily egg production records",
        permission: "production.view",
      },
      {
        label: "Egg inventory",
        href: "/egg-inventory",
        icon: PackageOpen,
        description: "Balances, issues, and adjustments",
        permission: "eggs.view",
      },
      {
        label: "Feed",
        href: "/feed",
        icon: Utensils,
        description: "Feed stock, purchases, and usage",
        permission: "feed.view",
      },
      {
        label: "Health",
        href: "/health",
        icon: Stethoscope,
        description: "Vaccinations, treatments, and incidents",
        permission: "health.view",
      },
      {
        label: "Bird losses",
        href: "/bird-losses",
        icon: HeartPulse,
        description: "Mortality and culling records",
        permission: "bird_losses.view",
      },
    ],
  },
  {
    label: "Commercial",
    items: [
      {
        label: "Sales",
        href: "/sales",
        icon: ShoppingCart,
        description: "Customers, invoices, and payments",
        permission: "sales.view",
      },
      {
        label: "Finance",
        href: "/finance",
        icon: WalletCards,
        description: "Cash flow, expenses, and profitability",
        permission: "finance.view",
      },
      {
        label: "Suppliers",
        href: "/suppliers",
        icon: BriefcaseBusiness,
        description: "Supplier directory and statements",
        permission: "suppliers.view",
      },
    ],
  },
  {
    label: "Administration",
    items: [
      {
        label: "Users",
        href: "/users",
        icon: Users,
        description: "Accounts, roles, and access",
        permission: "users.view",
      },
      {
        label: "Background jobs",
        href: "/jobs",
        icon: Activity,
        description: "Scheduled operations and history",
        permission: "audit.view",
      },
      {
        label: "Audit trail",
        href: "/audit",
        icon: ScrollText,
        description: "Security and activity records",
        permission: "audit.view",
      },
      {
        label: "Settings",
        href: "/settings",
        icon: Settings,
        description: "Farm and application preferences",
        permission: "farms.view",
      },
    ],
  },
]

export const quickActions: NavigationItem[] = [
  {
    label: "Record production",
    href: "/production/new",
    icon: ClipboardList,
    description: "Enter today's egg production",
    permission: "production.create",
  },
  {
    label: "Record sale",
    href: "/sales/new",
    icon: ReceiptText,
    description: "Create a customer invoice",
    permission: "sales.create",
  },
  {
    label: "Health incident",
    href: "/health/incidents/new",
    icon: ShieldCheck,
    description: "Report a flock health concern",
    permission: "health.create",
  },
  {
    label: "Stock adjustment",
    href: "/egg-inventory/adjustments/new",
    icon: Boxes,
    description: "Correct an inventory balance",
    permission: "eggs.adjust",
  },
]

export function canUseNavigationItem(
  permissions: readonly string[],
  item: NavigationItem,
): boolean {
  return (
    !item.permission ||
    permissions.includes(item.permission)
  )
}

export function allowedNavigationGroups(
  permissions: readonly string[],
): NavigationGroup[] {
  return navigationGroups
    .map((group) => ({
      ...group,
      items: group.items.filter((item) =>
        canUseNavigationItem(permissions, item),
      ),
    }))
    .filter((group) => group.items.length > 0)
}

export function allowedQuickActions(
  permissions: readonly string[],
): NavigationItem[] {
  return quickActions.filter((item) =>
    canUseNavigationItem(permissions, item),
  )
}
