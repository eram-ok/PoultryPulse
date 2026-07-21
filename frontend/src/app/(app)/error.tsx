"use client"

import { AlertTriangle, RotateCcw } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

interface ApplicationErrorProps {
  error: Error & { digest?: string }
  reset: () => void
}

export default function ApplicationError({
  error,
  reset,
}: ApplicationErrorProps) {
  return (
    <div className="grid min-h-[65vh] place-items-center">
      <Card className="w-full max-w-lg rounded-2xl border-destructive/20 shadow-xl shadow-destructive/5">
        <CardHeader>
          <div className="mb-3 grid size-12 place-items-center rounded-2xl bg-destructive/10 text-destructive">
            <AlertTriangle className="size-6" />
          </div>
          <CardTitle>Something interrupted this view</CardTitle>
          <CardDescription>
            PoultryPulse could not complete this screen. Your saved farm
            records were not changed.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {error.digest ? (
            <p className="font-mono text-xs text-muted-foreground">
              Reference: {error.digest}
            </p>
          ) : null}
          <Button onClick={reset} className="rounded-xl">
            <RotateCcw className="size-4" />
            Try again
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
