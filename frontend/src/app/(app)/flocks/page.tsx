import { FlocksWorkspace } from "@/components/flocks/flocks-workspace"
import { PermissionDenied } from "@/components/operational/permission-denied"
import {
  requireServerSession,
  sessionHasPermission,
} from "@/lib/auth/session"

export default async function FlocksPage() {
  const session = await requireServerSession({
    returnTo: "/flocks",
  })

  if (!sessionHasPermission(session, "flocks.view")) {
    return <PermissionDenied moduleName="flock operations" />
  }

  return <FlocksWorkspace />
}
