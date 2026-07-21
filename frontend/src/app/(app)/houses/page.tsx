import { HousesWorkspace } from "@/components/houses/houses-workspace"
import { PermissionDenied } from "@/components/operational/permission-denied"
import {
  requireServerSession,
  sessionHasPermission,
} from "@/lib/auth/session"

export default async function HousesPage() {
  const session = await requireServerSession({
    returnTo: "/houses",
  })

  if (!sessionHasPermission(session, "houses.view")) {
    return <PermissionDenied moduleName="poultry houses" />
  }

  return <HousesWorkspace />
}
