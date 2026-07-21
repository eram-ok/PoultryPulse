import { Activity, ArrowUpRight } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { flockHealth } from "@/lib/demo-data"
import { cn } from "@/lib/utils"

export function FlockHealthCard() {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Flock health</CardTitle>
            <CardDescription className="mt-1">
              Combined health and production signals.
            </CardDescription>
          </div>
          <div className="grid size-10 place-items-center rounded-2xl bg-info/10 text-info">
            <Activity className="size-5" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {flockHealth.map((flock) => (
          <div
            key={flock.flock}
            className="rounded-2xl border bg-muted/28 p-3.5"
          >
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold">
                  {flock.flock}
                </p>
                <p className="truncate text-xs text-muted-foreground">
                  {flock.house} · {flock.birds.toLocaleString()} birds
                </p>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "rounded-full",
                  flock.score >= 90
                    ? "border-primary/30 bg-primary/8 text-primary"
                    : flock.score >= 84
                      ? "border-info/30 bg-info/8 text-info"
                      : "border-warning/30 bg-warning/8 text-warning",
                )}
              >
                {flock.status}
              </Badge>
            </div>
            <div className="mt-3 flex items-center gap-3">
              <Progress value={flock.score} className="h-1.5 flex-1" />
              <span className="font-mono text-xs font-semibold">
                {flock.score}
              </span>
            </div>
          </div>
        ))}

        <Button variant="ghost" className="w-full rounded-xl">
          Review flock health
          <ArrowUpRight className="size-4" />
        </Button>
      </CardContent>
    </Card>
  )
}
