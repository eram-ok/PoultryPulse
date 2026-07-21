import { AlertsWorkspace } from "@/components/alerts/alerts-workspace"
import { PermissionDenied } from "@/components/operational/permission-denied"
import {
  requireServerSession,
  sessionHasPermission,
} from "@/lib/auth/session"

export default async function AlertsPage() {
  const session = await requireServerSession({
    returnTo: "/alerts",
  })

  if (!sessionHasPermission(session, "alerts.view")) {
    return <PermissionDenied moduleName="operational alerts" />
  }

  return <AlertsWorkspace />
}
