import { ArrowUpRight, History } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { recentActivity } from "@/lib/demo-data"

export function RecentActivity() {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle>Recent farm activity</CardTitle>
            <History className="size-4 text-muted-foreground" />
          </div>
          <CardDescription className="mt-1">
            Latest confirmed work across operational modules.
          </CardDescription>
        </div>
        <Button variant="outline" className="hidden rounded-xl sm:flex">
          View audit trail
          <ArrowUpRight className="size-4" />
        </Button>
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-2xl border">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/35 hover:bg-muted/35">
                <TableHead>Activity</TableHead>
                <TableHead className="hidden md:table-cell">
                  Module
                </TableHead>
                <TableHead className="hidden lg:table-cell">
                  Actor
                </TableHead>
                <TableHead className="hidden sm:table-cell">
                  Reference
                </TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {recentActivity.map((item) => (
                <TableRow key={item.reference}>
                  <TableCell className="font-medium">
                    {item.event}
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">
                    {item.module}
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground lg:table-cell">
                    {item.actor}
                  </TableCell>
                  <TableCell className="hidden font-mono text-xs text-muted-foreground sm:table-cell">
                    {item.reference}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className="rounded-full bg-primary/8 text-primary"
                    >
                      {item.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-mono text-xs text-muted-foreground">
                    {item.time}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
