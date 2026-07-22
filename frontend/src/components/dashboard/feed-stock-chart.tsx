import {
  AlertTriangle,
  PackageCheck,
  Scale,
} from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { formatNumber } from "@/lib/utils"

interface FeedStockChartProps {
  totalFeedKg: number
  lowStockItems: number
}

export function FeedStockChart({
  totalFeedKg,
  lowStockItems,
}: FeedStockChartProps) {
  return (
    <Card className="rounded-[24px] border-border/70 bg-gradient-to-br from-info/8 via-card/90 to-card/88 backdrop-blur-xl">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Feed stock</CardTitle>
          <Badge
            variant={lowStockItems > 0 ? "outline" : "secondary"}
            className={
              lowStockItems > 0
                ? "rounded-full border-warning/30 bg-warning/8 text-warning"
                : "rounded-full bg-primary/8 text-primary"
            }
          >
            {lowStockItems > 0 ? (
              <AlertTriangle className="mr-1 size-3" />
            ) : (
              <PackageCheck className="mr-1 size-3" />
            )}
            {lowStockItems > 0
              ? `${lowStockItems} low stock`
              : "Stock healthy"}
          </Badge>
        </div>
        <CardDescription>
          Live feed inventory summary across all items.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-5">
        <div className="rounded-2xl border bg-muted/25 p-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs text-muted-foreground">
                Total feed available
              </p>
              <p className="mt-2 font-mono text-3xl font-semibold">
                {formatNumber(totalFeedKg, 1)}
                <span className="ml-2 text-sm font-normal text-muted-foreground">
                  kg
                </span>
              </p>
            </div>
            <div className="grid size-12 place-items-center rounded-2xl bg-primary/10 text-primary">
              <Scale className="size-5" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-2xl border bg-card/55 p-4">
            <p className="text-xs text-muted-foreground">
              Reorder flags
            </p>
            <p className="mt-2 font-mono text-2xl font-semibold">
              {lowStockItems}
            </p>
          </div>
          <div className="rounded-2xl border bg-card/55 p-4">
            <p className="text-xs text-muted-foreground">
              Inventory status
            </p>
            <p
              className={
                lowStockItems > 0
                  ? "mt-2 text-sm font-semibold text-warning"
                  : "mt-2 text-sm font-semibold text-primary"
              }
            >
              {lowStockItems > 0
                ? "Review required"
                : "Within limits"}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
