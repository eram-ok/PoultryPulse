"use client"

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { PackageCheck } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { feedStock } from "@/lib/demo-data"

export function FeedStockChart() {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between gap-3">
          <CardTitle>Feed stock</CardTitle>
          <Badge variant="outline" className="rounded-full">
            <PackageCheck className="mr-1 size-3" />
            4 items
          </Badge>
        </div>
        <CardDescription>
          Current kilograms against reorder thresholds.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="h-[245px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={feedStock}
              layout="vertical"
              margin={{ top: 0, right: 8, bottom: 0, left: 12 }}
            >
              <CartesianGrid
                horizontal={false}
                stroke="var(--border)"
                opacity={0.45}
              />
              <XAxis
                type="number"
                hide
              />
              <YAxis
                dataKey="feed"
                type="category"
                axisLine={false}
                tickLine={false}
                width={92}
                tick={{
                  fill: "var(--muted-foreground)",
                  fontSize: 11,
                }}
              />
              <Tooltip
                cursor={{ fill: "var(--muted)", opacity: 0.4 }}
                contentStyle={{
                  borderRadius: "14px",
                  border: "1px solid var(--border)",
                  background: "var(--popover)",
                  color: "var(--popover-foreground)",
                }}
                formatter={(value) => [
                  `${Number(value).toLocaleString()} kg`,
                  "Available",
                ]}
              />
              <Bar
                dataKey="quantity"
                fill="var(--chart-1)"
                radius={[0, 8, 8, 0]}
                barSize={18}
              />
              <Bar
                dataKey="reorder"
                fill="var(--chart-2)"
                radius={[0, 8, 8, 0]}
                barSize={7}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="mt-3 flex items-center gap-5 text-[11px] text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-chart-1" />
            Current stock
          </span>
          <span className="flex items-center gap-1.5">
            <span className="size-2 rounded-full bg-chart-2" />
            Reorder level
          </span>
        </div>
      </CardContent>
    </Card>
  )
}
