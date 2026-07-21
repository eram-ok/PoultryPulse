import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function toNumber(
  value: number | string | null | undefined,
): number {
  const parsed = Number(value ?? 0)
  return Number.isFinite(parsed) ? parsed : 0
}

export function formatNumber(
  value: number,
  maximumFractionDigits = 0,
): string {
  return new Intl.NumberFormat("en-UG", {
    maximumFractionDigits,
  }).format(value)
}

export function formatCurrency(
  value: number,
  currency = "UGX",
): string {
  return new Intl.NumberFormat("en-UG", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPercent(
  value: number,
  maximumFractionDigits = 1,
): string {
  return new Intl.NumberFormat("en-UG", {
    style: "percent",
    maximumFractionDigits,
  }).format(value / 100)
}
