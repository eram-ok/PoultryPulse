import Link from "next/link"
import { ShieldAlert } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

interface PermissionDeniedProps {
  moduleName: string
}

export function PermissionDenied({
  moduleName,
}: PermissionDeniedProps) {
  return (
    <div className="mx-auto flex min-h-[65vh] max-w-3xl items-center px-4 py-10">
      <Card className="w-full rounded-3xl border-border/80 bg-card/75">
        <CardContent className="flex flex-col items-center p-10 text-center">
          <div className="grid size-16 place-items-center rounded-2xl bg-destructive/10 text-destructive">
            <ShieldAlert className="size-7" />
          </div>
          <h1 className="mt-5 text-2xl font-semibold">
            Access to {moduleName} is restricted
          </h1>
          <p className="mt-2 max-w-md text-sm leading-6 text-muted-foreground">
            Your current role does not include the permission
            needed to open this operational module.
          </p>
          <Button asChild className="mt-6 rounded-xl">
            <Link href="/dashboard">Return to dashboard</Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
