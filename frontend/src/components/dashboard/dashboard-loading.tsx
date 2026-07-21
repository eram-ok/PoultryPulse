import { Skeleton } from "@/components/ui/skeleton"

export function DashboardLoading() {
  return (
    <div className="space-y-6 pb-24 lg:pb-8">
      <div className="space-y-3">
        <Skeleton className="h-6 w-48 rounded-full" />
        <Skeleton className="h-10 w-96 max-w-full" />
        <Skeleton className="h-5 w-[34rem] max-w-full" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton
            key={index}
            className="h-52 rounded-2xl"
          />
        ))}
      </div>
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.65fr)_minmax(320px,0.85fr)]">
        <Skeleton className="h-[430px] rounded-2xl" />
        <Skeleton className="h-[430px] rounded-2xl" />
      </div>
      <div className="grid gap-6 lg:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }, (_, index) => (
          <Skeleton
            key={index}
            className="h-[350px] rounded-2xl"
          />
        ))}
      </div>
    </div>
  )
}
