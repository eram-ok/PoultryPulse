import { SaleForm } from "@/components/commercial/sale-form"

interface NewSalePageProps {
  searchParams: Promise<{
    edit?: string
  }>
}

export default async function NewSalePage({
  searchParams,
}: NewSalePageProps) {
  const { edit } = await searchParams

  return <SaleForm saleId={edit} />
}
