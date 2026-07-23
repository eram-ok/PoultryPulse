"use client"

import { Check, Copy, ExternalLink, KeyRound, TriangleAlert } from "lucide-react"
import { useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

interface OneTimeSetupUrlProps {
  url: string
  title?: string
}

export function OneTimeSetupUrl({
  url,
  title = "One-time administrator setup link",
}: OneTimeSetupUrlProps) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "failed">("idle")

  async function copyUrl() {
    setCopyState("idle")
    try {
      await navigator.clipboard.writeText(url)
      setCopyState("copied")
    } catch {
      setCopyState("failed")
    }
  }

  return (
    <section className="rounded-2xl border border-amber-500/25 bg-amber-500/8 p-4">
      <div className="flex items-start gap-3">
        <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-amber-500/15 text-amber-700 dark:text-amber-300">
          <KeyRound className="size-5" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-semibold">{title}</h3>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            This secret URL is returned only once. Share it only with the intended farm administrator.
          </p>
        </div>
      </div>

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <Input
          readOnly
          value={url}
          aria-label={title}
          className="h-11 min-w-0 rounded-xl font-mono text-xs"
          onFocus={(event) => event.currentTarget.select()}
        />
        <Button type="button" variant="outline" className="h-11 rounded-xl" onClick={() => void copyUrl()}>
          {copyState === "copied" ? <Check className="size-4" /> : <Copy className="size-4" />}
          {copyState === "copied" ? "Copied" : "Copy"}
        </Button>
        <Button asChild type="button" variant="outline" className="h-11 rounded-xl">
          <a href={url} target="_blank" rel="noreferrer">
            <ExternalLink className="size-4" />
            Open
          </a>
        </Button>
      </div>

      {copyState === "failed" ? (
        <p className="mt-3 text-xs text-destructive">
          Automatic copying was blocked. Select the URL manually and copy it.
        </p>
      ) : null}

      <div className="mt-3 flex items-start gap-2 text-xs leading-5 text-amber-800 dark:text-amber-200">
        <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
        Do not place this link in tickets, logs, screenshots, or shared documents.
      </div>
    </section>
  )
}
