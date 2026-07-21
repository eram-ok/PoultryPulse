import { ModulePlaceholder } from "@/components/shared/module-placeholder"

interface ModulePageProps {
  params: Promise<{
    module: string[]
  }>
}

export default async function ModulePage({
  params,
}: ModulePageProps) {
  const { module } = await params
  const title = module
    .map((segment) =>
      segment
        .split("-")
        .map(
          (word) =>
            word.charAt(0).toUpperCase() + word.slice(1),
        )
        .join(" "),
    )
    .join(" / ")

  return <ModulePlaceholder title={title} />
}
