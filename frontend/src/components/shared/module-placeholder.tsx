import Link from "next/link"
import {
  ArrowLeft,
  Blocks,
  Construction,
  Sparkles,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface ModulePlaceholderProps {
  title: string
}

export function ModulePlaceholder({
  title,
}: ModulePlaceholderProps) {
  return (
    <div className="grid min-h-[68vh] place-items-center">
      <Card className="surface-grid w-full max-w-2xl overflow-hidden rounded-3xl border-primary/15 bg-card/85 shadow-2xl shadow-primary/5">
        <CardHeader className="relative pb-2 pt-10 text-center">
          <div className="mx-auto mb-5 grid size-16 place-items-center rounded-3xl bg-primary/12 text-primary shadow-lg shadow-primary/10">
            <Construction className="size-8" />
          </div>
          <div className="mb-3 flex justify-center">
            <Badge
              variant="outline"
              className="rounded-full border-primary/25 bg-primary/8 text-primary"
            >
              <Sparkles className="mr-1 size-3" />
              Foundation ready
            </Badge>
          </div>
          <CardTitle className="text-2xl">
            {title}
          </CardTitle>
          <CardDescription className="mx-auto mt-2 max-w-lg leading-6">
            The responsive application shell and design system are ready.
            This module will receive its live API workflows in the next
            frontend stages.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center gap-5 pb-10 pt-5">
          <div className="flex items-center gap-2 rounded-2xl border bg-muted/30 px-4 py-3 text-sm text-muted-foreground">
            <Blocks className="size-4 text-primary" />
            Reusable tables, forms, charts, dialogs, and status states are
            prepared.
          </div>
          <Button asChild className="rounded-xl">
            <Link href="/dashboard">
              <ArrowLeft className="size-4" />
              Return to dashboard
            </Link>
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
