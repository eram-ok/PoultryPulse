import {
  PlatformFarmDetailOverview,
} from "@/components/platform/platform-farm-detail-overview"

interface PlatformFarmDetailPageProps {
  params: Promise<{
    farmId: string
  }>
}

export const metadata = {
  title: "Customer farm",
}

export default async function PlatformFarmDetailPage({
  params,
}: PlatformFarmDetailPageProps) {
  const { farmId } = await params

  return (
    <PlatformFarmDetailOverview
      farmId={farmId}
    />
  )
}
