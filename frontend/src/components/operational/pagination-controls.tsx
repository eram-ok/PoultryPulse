import { ChevronLeft, ChevronRight } from "lucide-react"

import { Button } from "@/components/ui/button"

interface PaginationControlsProps {
  offset: number
  limit: number
  total: number
  onOffsetChange: (offset: number) => void
}

export function PaginationControls({
  offset,
  limit,
  total,
  onOffsetChange,
}: PaginationControlsProps) {
  const page = Math.floor(offset / limit) + 1
  const pages = Math.max(1, Math.ceil(total / limit))
  const from = total === 0 ? 0 : offset + 1
  const to = Math.min(offset + limit, total)

  return (
    <div className="flex flex-col gap-3 border-t border-border/70 px-4 py-3 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
      <p>
        Showing {from}–{to} of {total}
      </p>
      <div className="flex items-center gap-2">
        <span>
          Page {page} of {pages}
        </span>
        <Button
          variant="outline"
          size="icon-sm"
          className="rounded-lg"
          disabled={offset === 0}
          onClick={() =>
            onOffsetChange(Math.max(0, offset - limit))
          }
          aria-label="Previous page"
        >
          <ChevronLeft className="size-4" />
        </Button>
        <Button
          variant="outline"
          size="icon-sm"
          className="rounded-lg"
          disabled={offset + limit >= total}
          onClick={() =>
            onOffsetChange(offset + limit)
          }
          aria-label="Next page"
        >
          <ChevronRight className="size-4" />
        </Button>
      </div>
    </div>
  )
}
