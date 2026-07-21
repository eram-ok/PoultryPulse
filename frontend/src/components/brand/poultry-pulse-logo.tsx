import { cn } from "@/lib/utils"

interface PoultryPulseLogoProps {
  compact?: boolean
  className?: string
}

export function PoultryPulseLogo({
  compact = false,
  className,
}: PoultryPulseLogoProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-3",
        className,
      )}
    >
      <div className="relative grid size-10 shrink-0 place-items-center overflow-hidden rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
        <svg
          aria-hidden="true"
          viewBox="0 0 40 40"
          className="size-8"
          fill="none"
        >
          <path
            d="M20 5.4c-6.7 0-11.7 5.4-11.7 12.2 0 8.1 6.5 14.7 11.7 17 5.2-2.3 11.7-8.9 11.7-17C31.7 10.8 26.7 5.4 20 5.4Z"
            fill="currentColor"
            opacity=".2"
          />
          <path
            d="M20.1 9.5c-4.8 0-8.2 3.8-8.2 8.7 0 5.6 4.3 10.1 8.2 12.2 3.8-2.1 8.1-6.6 8.1-12.2 0-4.9-3.4-8.7-8.1-8.7Z"
            stroke="currentColor"
            strokeWidth="2.2"
          />
          <path
            d="M16.1 23.7c3.8-.8 6.8-3.1 8.7-6.8.1 4.4-1.7 7.7-5.5 9.7"
            stroke="currentColor"
            strokeLinecap="round"
            strokeWidth="2.2"
          />
          <circle cx="25.9" cy="13.4" r="1.2" fill="currentColor" />
        </svg>
      </div>

      {!compact ? (
        <div className="min-w-0">
          <p className="truncate text-[15px] font-semibold tracking-tight">
            PoultryPulse
          </p>
          <p className="truncate text-[10px] font-medium uppercase tracking-[0.22em] text-muted-foreground">
            Farm intelligence
          </p>
        </div>
      ) : null}
    </div>
  )
}
