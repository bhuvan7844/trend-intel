'use client'

import { useState } from 'react'
import useSWR from 'swr'
import { ExternalLink, Heart } from 'lucide-react'
import type { DevArticle } from '@/lib/api'
import { fetcher } from '@/lib/api'
import { compactNumber, parseTags } from '@/lib/format'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { EmptyState, ErrorState, LoadingRows } from '@/components/dashboard/states'

const TAGS = ['All', 'javascript', 'webdev', 'react', 'python', 'ai', 'rust']

export function DevtoView() {
  const [tag, setTag] = useState('All')
  const key = `/trends/devto?limit=30${
    tag !== 'All' ? `&tag=${encodeURIComponent(tag)}` : ''
  }`
  const { data, error, isLoading } = useSWR<DevArticle[]>(key, fetcher)

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap gap-1.5">
        {TAGS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTag(t)}
            className={cn(
              'rounded-md border px-2.5 py-1 font-mono text-xs transition-colors',
              tag === t
                ? 'border-[var(--chart-2)]/40 bg-[var(--chart-2)]/10 text-[var(--chart-2)]'
                : 'border-border text-muted-foreground hover:text-foreground',
            )}
          >
            {t === 'All' ? 'All' : `#${t}`}
          </button>
        ))}
      </div>

      {error ? (
        <ErrorState message={error.message} />
      ) : isLoading ? (
        <LoadingRows rows={8} />
      ) : !data || data.length === 0 ? (
        <EmptyState message="No DEV.to articles found." />
      ) : (
        <div className="grid gap-2 md:grid-cols-2">
          {data.map((article) => (
            <Card
              key={article.id}
              className="gap-2 p-3 transition-colors hover:border-[var(--chart-2)]/40"
            >
              <a
                href={article.url ?? '#'}
                target={article.url ? '_blank' : undefined}
                rel="noreferrer"
                className="line-clamp-2 text-sm font-medium hover:text-[var(--chart-2)]"
              >
                {article.title}
              </a>
              <div className="flex flex-wrap gap-1">
                {parseTags(article.tags).map((t) => (
                  <span
                    key={t}
                    className="rounded bg-muted px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
                  >
                    #{t}
                  </span>
                ))}
              </div>
              <div className="mt-auto flex items-center justify-between font-mono text-[11px] text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Heart
                    className="size-3 text-[var(--chart-4)]"
                    aria-hidden
                  />
                  {compactNumber(article.reactions)} reactions
                </span>
                {article.author && <span>{article.author}</span>}
                {article.url && (
                  <ExternalLink className="size-3" aria-hidden />
                )}
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
