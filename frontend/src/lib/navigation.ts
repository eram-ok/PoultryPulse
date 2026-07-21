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
      },
      {
        label: "Reports",
        href: "/reports",
        icon: FileChartColumn,
        description: "Trends and management insights",
      },
      {
        label: "Alerts",
        href: "/alerts",
        icon: Bell,
        description: "Operational issues and reminders",
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
      },
      {
        label: "Houses",
        href: "/houses",
        icon: House,
        description: "Farm housing and occupancy",
      },
      {
        label: "Production",
        href: "/production",
        icon: Egg,
        description: "Daily egg production records",
      },
      {
        label: "Egg inventory",
        href: "/egg-inventory",
        icon: PackageOpen,
        description: "Balances, issues, and adjustments",
      },
      {
        label: "Feed",
        href: "/feed",
        icon: Utensils,
        description: "Feed stock, purchases, and usage",
      },
      {
        label: "Health",
        href: "/health",
        icon: Stethoscope,
        description: "Vaccinations, treatments, and incidents",
      },
      {
        label: "Bird losses",
        href: "/bird-losses",
        icon: HeartPulse,
        description: "Mortality and culling records",
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
      },
      {
        label: "Finance",
        href: "/finance",
        icon: WalletCards,
        description: "Cash flow, expenses, and profitability",
      },
      {
        label: "Suppliers",
        href: "/suppliers",
        icon: BriefcaseBusiness,
        description: "Supplier directory and statements",
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
      },
      {
        label: "Background jobs",
        href: "/jobs",
        icon: Activity,
        description: "Scheduled operations and history",
      },
      {
        label: "Audit trail",
        href: "/audit",
        icon: ScrollText,
        description: "Security and activity records",
      },
      {
        label: "Settings",
        href: "/settings",
        icon: Settings,
        description: "Farm and application preferences",
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
  },
  {
    label: "Record sale",
    href: "/sales/new",
    icon: ReceiptText,
    description: "Create a customer invoice",
  },
  {
    label: "Health incident",
    href: "/health/incidents/new",
    icon: ShieldCheck,
    description: "Report a flock health concern",
  },
  {
    label: "Stock adjustment",
    href: "/egg-inventory/adjustments/new",
    icon: Boxes,
    description: "Correct an inventory balance",
  },
]
