import {
  ArrowUpRight,
  Boxes,
} from "lucide-react"
import Link from "next/link"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import { formatNumber } from "@/lib/utils"

interface InventoryOverviewProps {
  totalEggs: number
  saleableEggs: number
  damagedToday: number
  canViewInventory: boolean
}

export function InventoryOverview({
  totalEggs,
  saleableEggs,
  damagedToday,
  canViewInventory,
}: InventoryOverviewProps) {
  const saleablePercentage =
    totalEggs > 0
      ? Math.round((saleableEggs / totalEggs) * 100)
      : 0
  const otherEggs = Math.max(
    0,
    totalEggs - saleableEggs,
  )
  const otherPercentage =
    totalEggs > 0
      ? Math.round((otherEggs / totalEggs) * 100)
      : 0

  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Egg inventory</CardTitle>
            <CardDescription className="mt-1">
              Live stock quality and availability.
            </CardDescription>
          </div>
          <div className="grid size-10 place-items-center rounded-2xl bg-primary/10 text-primary">
            <Boxes className="size-5" />
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {[
          {
            label: "Saleable eggs",
            quantity: saleableEggs,
            percentage: saleablePercentage,
          },
          {
            label: "Other stock",
            quantity: otherEggs,
            percentage: otherPercentage,
          },
        ].map((item) => (
          <div key={item.label}>
            <div className="mb-2 flex items-end justify-between gap-3">
              <div>
                <p className="text-sm font-medium">
                  {item.label}
                </p>
                <p className="font-mono text-xs text-muted-foreground">
                  {formatNumber(item.quantity)} eggs
                </p>
              </div>
              <span className="font-mono text-xs font-semibold">
                {item.percentage}%
              </span>
            </div>
            <Progress
              value={item.percentage}
              className="h-2"
            />
          </div>
        ))}

        <div className="rounded-xl border bg-muted/25 px-4 py-3 text-xs text-muted-foreground">
          Damaged or rejected today:{" "}
          <span className="font-mono font-semibold text-foreground">
            {formatNumber(damagedToday)}
          </span>
        </div>

        {canViewInventory ? (
          <Button
            asChild
            variant="ghost"
            className="w-full rounded-xl"
          >
            <Link href="/egg-inventory">
              Open inventory
              <ArrowUpRight className="size-4" />
            </Link>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  )
}
