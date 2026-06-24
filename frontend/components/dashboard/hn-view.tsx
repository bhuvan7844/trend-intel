'use client'

import useSWR from 'swr'
import { ArrowUp, ExternalLink, MessageCircle } from 'lucide-react'
import type { HNStory } from '@/lib/api'
import { fetcher } from '@/lib/api'
import { compactNumber, hostname } from '@/lib/format'
import { Card } from '@/components/ui/card'
import { EmptyState, ErrorState, LoadingRows } from '@/components/dashboard/states'

export function HNView() {
  const { data, error, isLoading } = useSWR<HNStory[]>(
    '/trends/hn?limit=30',
    fetcher,
  )

  if (error) return <ErrorState message={error.message} />
  if (isLoading) return <LoadingRows rows={8} />
  if (!data || data.length === 0)
    return <EmptyState message="No Hacker News stories yet." />

  return (
    <div className="flex flex-col gap-2">
      {data.map((story, i) => {
        const host = hostname(story.url)
        return (
          <Card
            key={story.id}
            className="flex-row items-center gap-3 p-3 transition-colors hover:border-primary/30"
          >
            <span className="w-6 shrink-0 text-center font-mono text-sm text-muted-foreground tabular-nums">
              {i + 1}
            </span>
            <div className="flex w-12 shrink-0 flex-col items-center justify-center rounded-md border border-[var(--chart-3)]/30 bg-[var(--chart-3)]/10 py-1.5">
              <ArrowUp
                className="size-3 text-[var(--chart-3)]"
                aria-hidden
              />
              <span className="font-mono text-sm font-semibold tabular-nums text-[var(--chart-3)]">
                {compactNumber(story.points)}
              </span>
            </div>
            <div className="min-w-0 flex-1">
              <a
                href={story.url ?? '#'}
                target={story.url ? '_blank' : undefined}
                rel="noreferrer"
                className="line-clamp-2 text-sm font-medium hover:text-primary"
              >
                {story.title}
              </a>
              <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-0.5 font-mono text-[11px] text-muted-foreground">
                {host && (
                  <span className="flex items-center gap-1">
                    <ExternalLink className="size-3" aria-hidden />
                    {host}
                  </span>
                )}
                {story.author && <span>by {story.author}</span>}
                {story.num_comments != null && (
                  <span className="flex items-center gap-1">
                    <MessageCircle className="size-3" aria-hidden />
                    {compactNumber(story.num_comments)}
                  </span>
                )}
              </div>
            </div>
          </Card>
        )
      })}
    </div>
  )
}
