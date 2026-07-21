import Link from "next/link"
import { ArrowLeft, Feather } from "lucide-react"

import { Button } from "@/components/ui/button"

export default function NotFound() {
  return (
    <main className="surface-grid grid min-h-screen place-items-center p-6">
      <div className="max-w-md text-center">
        <div className="mx-auto mb-6 grid size-16 place-items-center rounded-3xl bg-primary/12 text-primary">
          <Feather className="size-8" />
        </div>
        <p className="font-mono text-sm font-medium text-primary">404</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-tight">
          This farm view has flown away
        </h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">
          The page may have moved, or the module has not been enabled for
          your role yet.
        </p>
        <Button asChild className="mt-7 rounded-xl">
          <Link href="/dashboard">
            <ArrowLeft className="size-4" />
            Return to dashboard
          </Link>
        </Button>
      </div>
    </main>
  )
}
