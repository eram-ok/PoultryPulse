"use client"

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { MoreHorizontal, TrendingUp } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { productionTrend } from "@/lib/demo-data"

export function ProductionTrendChart() {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader className="flex flex-row items-start justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <CardTitle>Egg production trend</CardTitle>
            <Badge
              variant="secondary"
              className="rounded-full bg-primary/10 text-primary"
            >
              <TrendingUp className="mr-1 size-3" />
              Healthy
            </Badge>
          </div>
          <CardDescription>
            Daily collection compared with the farm target.
          </CardDescription>
        </div>
        <Button variant="ghost" size="icon" className="rounded-xl">
          <MoreHorizontal className="size-4" />
          <span className="sr-only">Production chart options</span>
        </Button>
      </CardHeader>
      <CardContent>
        <div className="mb-5 grid grid-cols-2 gap-3 sm:flex sm:gap-8">
          <div>
            <p className="text-xs text-muted-foreground">Seven-day total</p>
            <p className="mt-1 font-mono text-xl font-semibold">55,260</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Average / day</p>
            <p className="mt-1 font-mono text-xl font-semibold">7,894</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Target attainment</p>
            <p className="mt-1 font-mono text-xl font-semibold text-primary">
              103.9%
            </p>
          </div>
        </div>

        <div className="h-[286px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={productionTrend}
              margin={{ top: 12, right: 8, bottom: 0, left: -16 }}
            >
              <CartesianGrid
                stroke="var(--border)"
                strokeDasharray="4 5"
                vertical={false}
                opacity={0.55}
              />
              <XAxis
                dataKey="day"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 12 }}
                dy={10}
              />
              <YAxis
                axisLine={false}
                tickLine={false}
                tick={{ fill: "var(--muted-foreground)", fontSize: 11 }}
                tickFormatter={(value: number) =>
                  `${Math.round(value / 1000)}k`
                }
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "14px",
                  border: "1px solid var(--border)",
                  background: "var(--popover)",
                  color: "var(--popover-foreground)",
                  boxShadow: "0 18px 45px rgba(0,0,0,.18)",
                }}
                formatter={(value, name) => [
                  Number(value).toLocaleString(),
                  name === "eggs" ? "Eggs collected" : "Target",
                ]}
              />
              <Line
                type="monotone"
                dataKey="target"
                stroke="var(--chart-2)"
                strokeDasharray="5 6"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="eggs"
                stroke="var(--chart-1)"
                strokeWidth={3}
                dot={{
                  r: 3.5,
                  fill: "var(--card)",
                  stroke: "var(--chart-1)",
                  strokeWidth: 2,
                }}
                activeDot={{
                  r: 6,
                  fill: "var(--chart-1)",
                  stroke: "var(--card)",
                  strokeWidth: 3,
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
