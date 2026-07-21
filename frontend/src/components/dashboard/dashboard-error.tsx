import {
  CircleAlert,
  RotateCcw,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"

interface DashboardErrorProps {
  message: string
  onRetry: () => void
}

export function DashboardError({
  message,
  onRetry,
}: DashboardErrorProps) {
  return (
    <div className="grid min-h-[65vh] place-items-center">
      <Card className="w-full max-w-lg rounded-3xl">
        <CardContent className="p-8 text-center">
          <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-destructive/10 text-destructive">
            <CircleAlert className="size-6" />
          </div>
          <h1 className="mt-5 text-xl font-semibold">
            Live dashboard unavailable
          </h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            {message}
          </p>
          <Button
            className="mt-6 rounded-xl"
            onClick={onRetry}
          >
            <RotateCcw className="size-4" />
            Try again
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
