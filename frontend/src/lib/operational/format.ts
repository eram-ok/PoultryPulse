export function formatEnum(value: string): string {
  return value
    .toLowerCase()
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() + word.slice(1),
    )
    .join(" ")
}

export function formatDate(
  value: string | null | undefined,
): string {
  if (!value) {
    return "Not recorded"
  }

  const parsed = new Date(`${value}T00:00:00`)

  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat("en-UG", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(parsed)
}

export function formatDateTime(
  value: string | null | undefined,
): string {
  if (!value) {
    return "Not recorded"
  }

  const parsed = new Date(value)

  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat("en-UG", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsed)
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-UG").format(value)
}

export function formatMoney(
  value: string | number,
  currency = "UGX",
): string {
  const numeric = Number(value)

  if (!Number.isFinite(numeric)) {
    return `${currency} ${value}`
  }

  return new Intl.NumberFormat("en-UG", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(numeric)
}

export function todayIso(): string {
  return new Date().toISOString().slice(0, 10)
}
