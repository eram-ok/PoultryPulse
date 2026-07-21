import { ArrowUpRight, Boxes } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { inventoryBalances } from "@/lib/demo-data"

export function InventoryOverview() {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Egg inventory</CardTitle>
            <CardDescription className="mt-1">
              Available stock by grade.
            </CardDescription>
          </div>
          <div className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary">
            <Boxes className="size-5" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {inventoryBalances.map((item) => {
          const percentage = Math.round(
            (item.quantity / item.capacity) * 100,
          )

          return (
            <div key={item.grade}>
              <div className="mb-2 flex items-end justify-between gap-3">
                <div>
                  <p className="text-sm font-medium">{item.grade}</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {item.quantity.toLocaleString()} eggs
                  </p>
                </div>
                <span className="font-mono text-xs font-semibold">
                  {percentage}%
                </span>
              </div>
              <Progress value={percentage} className="h-2" />
            </div>
          )
        })}

        <Button variant="ghost" className="w-full rounded-xl">
          Open inventory
          <ArrowUpRight className="size-4" />
        </Button>
      </CardContent>
    </Card>
  )
}
