import {
  ArrowUpRight,
  History,
} from "lucide-react"
import Link from "next/link"

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

export interface OperationalSummaryItem {
  event: string
  module: string
  value: string
  detail: string
  status: "Healthy" | "Attention" | "Recorded"
}

interface RecentActivityProps {
  items: OperationalSummaryItem[]
  canViewAudit: boolean
}

export function RecentActivity({
  items,
  canViewAudit,
}: RecentActivityProps) {
  return (
    <Card className="rounded-2xl border-border/70 bg-card/82 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <CardTitle>
              Today&apos;s operational summary
            </CardTitle>
            <History className="size-4 text-muted-foreground" />
          </div>
          <CardDescription className="mt-1">
            Current live values across core farm modules.
          </CardDescription>
        </div>
        {canViewAudit ? (
          <Button
            asChild
            variant="outline"
            className="hidden rounded-xl sm:flex"
          >
            <Link href="/audit">
              View audit trail
              <ArrowUpRight className="size-4" />
            </Link>
          </Button>
        ) : null}
      </CardHeader>
      <CardContent>
        <div className="overflow-hidden rounded-2xl border">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/35 hover:bg-muted/35">
                <TableHead>Indicator</TableHead>
                <TableHead className="hidden md:table-cell">
                  Module
                </TableHead>
                <TableHead>Value</TableHead>
                <TableHead className="hidden lg:table-cell">
                  Detail
                </TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((item) => (
                <TableRow key={`${item.module}-${item.event}`}>
                  <TableCell className="font-medium">
                    {item.event}
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground md:table-cell">
                    {item.module}
                  </TableCell>
                  <TableCell className="font-mono text-xs">
                    {item.value}
                  </TableCell>
                  <TableCell className="hidden text-muted-foreground lg:table-cell">
                    {item.detail}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="secondary"
                      className={
                        item.status === "Attention"
                          ? "rounded-full bg-warning/8 text-warning"
                          : "rounded-full bg-primary/8 text-primary"
                      }
                    >
                      {item.status}
                    </Badge>
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
