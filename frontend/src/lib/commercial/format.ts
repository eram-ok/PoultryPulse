export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}

export function formatMoney(
  value: string | number,
  currency = "UGX",
): string {
  const amount =
    typeof value === "number"
      ? value
      : Number.parseFloat(value || "0")

  return new Intl.NumberFormat("en-UG", {
    style: "currency",
    currency,
    maximumFractionDigits: currency === "UGX" ? 0 : 2,
  }).format(Number.isFinite(amount) ? amount : 0)
}

export function formatDate(value: string | null): string {
  if (!value) return "—"

  return new Intl.DateTimeFormat("en-UG", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  }).format(new Date(`${value.slice(0, 10)}T00:00:00`))
}

export function titleCase(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map((word) => `${word.charAt(0).toUpperCase()}${word.slice(1)}`)
    .join(" ")
}

export function numeric(value: string | number): number {
  const parsed =
    typeof value === "number" ? value : Number.parseFloat(value || "0")
  return Number.isFinite(parsed) ? parsed : 0
}
