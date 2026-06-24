'use client'

import { useState } from 'react'
import useSWR from 'swr'
import {
  ExternalLink,
  Sparkles,
  Star,
  TrendingUp,
  X,
} from 'lucide-react'
import type { Repo } from '@/lib/api'
import { fetcher } from '@/lib/api'
import { compactNumber, languageColor } from '@/lib/format'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import {
  EmptyState,
  ErrorState,
  LoadingRows,
  Spinner,
} from '@/components/dashboard/states'

const LANGUAGES = [
  'All',
  'TypeScript',
  'Python',
  'JavaScript',
  'Rust',
  'Go',
  'Java',
]

export function ReposView({ query }: { query: string }) {
  const [language, setLanguage] = useState('All')
  const [selected, setSelected] = useState<Repo | null>(null)

  const trendingKey = `/trending?limit=40${
    language !== 'All' ? `&language=${encodeURIComponent(language)}` : ''
  }`
  const searchKey =
    query.length >= 2 ? `/search?q=${encodeURIComponent(query)}` : null

  const { data: trending, error, isLoading } = useSWR<Repo[]>(
    searchKey ? null : trendingKey,
    fetcher,
  )
  const { data: searchData, isLoading: searching } = useSWR<Repo[]>(
    searchKey,
    fetcher,
  )

  const repos = searchKey ? searchData : trending
  const loading = searchKey ? searching : isLoading

  return (
    <div className="relative flex gap-4">
      <div className="min-w-0 flex-1">
        {!searchKey && (
          <div className="mb-3 flex flex-wrap gap-1.5">
            {LANGUAGES.map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLanguage(lang)}
                className={cn(
                  'rounded-md border px-2.5 py-1 font-mono text-xs transition-colors',
                  language === lang
                    ? 'border-primary/40 bg-primary/10 text-primary'
                    : 'border-border text-muted-foreground hover:text-foreground',
                )}
              >
                {lang}
              </button>
            ))}
          </div>
        )}

        {searchKey && (
          <p className="mb-3 font-mono text-xs text-muted-foreground">
            search results for{' '}
            <span className="text-primary">&quot;{query}&quot;</span>
          </p>
        )}

        {error ? (
          <ErrorState message={error.message} />
        ) : loading ? (
          <LoadingRows rows={8} />
        ) : !repos || repos.length === 0 ? (
          <EmptyState message="No repositories found." />
        ) : (
          <div className="flex flex-col gap-2">
            {repos.map((repo, i) => (
              <RepoRow
                key={repo.id}
                rank={i + 1}
                repo={repo}
                active={selected?.id === repo.id}
                onSelect={() => setSelected(repo)}
              />
            ))}
          </div>
        )}
      </div>

      {selected && (
        <RecommendPanel repo={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  )
}

function RepoRow({
  repo,
  rank,
  active,
  onSelect,
}: {
  repo: Repo
  rank: number
  active: boolean
  onSelect: () => void
}) {
  return (
    <Card
      className={cn(
        'flex-row items-center gap-3 p-3 transition-colors hover:border-primary/30',
        active && 'border-primary/50 bg-primary/5',
      )}
    >
      <span className="w-6 shrink-0 text-center font-mono text-sm text-muted-foreground tabular-nums">
        {rank}
      </span>
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate font-mono text-sm font-medium">
            {repo.name}
          </span>
          {repo.language && (
            <span className="flex shrink-0 items-center gap-1 font-mono text-[11px] text-muted-foreground">
              <span
                className="size-2 rounded-full"
                style={{ backgroundColor: languageColor(repo.language) }}
              />
              {repo.language}
            </span>
          )}
        </div>
        {repo.description && (
          <p className="mt-0.5 line-clamp-1 text-xs text-muted-foreground">
            {repo.description}
          </p>
        )}
      </div>
      <div className="hidden shrink-0 items-center gap-3 sm:flex">
        {repo.stars != null && (
          <span className="flex items-center gap-1 font-mono text-xs text-muted-foreground">
            <Star className="size-3" aria-hidden />
            {compactNumber(repo.stars)}
          </span>
        )}
        <span className="flex items-center gap-1 rounded border border-primary/30 bg-primary/10 px-2 py-0.5 font-mono text-xs text-primary tabular-nums">
          <TrendingUp className="size-3" aria-hidden />
          {compactNumber(repo.trending_score)}
        </span>
      </div>
      <div className="flex shrink-0 items-center gap-1">
        <Button
          size="icon"
          variant="ghost"
          className="size-8"
          onClick={onSelect}
          aria-label={`Find repos similar to ${repo.name}`}
        >
          <Sparkles className="size-4" />
        </Button>
        {repo.url && (
          <Button
            size="icon"
            variant="ghost"
            className="size-8"
            asChild
          >
            <a
              href={repo.url}
              target="_blank"
              rel="noreferrer"
              aria-label={`Open ${repo.name} on GitHub`}
            >
              <ExternalLink className="size-4" />
            </a>
          </Button>
        )}
      </div>
    </Card>
  )
}

function RecommendPanel({
  repo,
  onClose,
}: {
  repo: Repo
  onClose: () => void
}) {
  const { data, error, isLoading } = useSWR<Repo[]>(
    `/recommend/${repo.id}?limit=6`,
    fetcher,
  )

  return (
    <Card className="sticky top-0 hidden h-fit w-80 shrink-0 gap-3 p-4 lg:flex">
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="flex items-center gap-1.5 font-mono text-[11px] uppercase tracking-wider text-primary">
            <Sparkles className="size-3.5" aria-hidden />
            Similar repos
          </p>
          <p className="mt-1 truncate font-mono text-sm font-medium">
            {repo.name}
          </p>
        </div>
        <Button
          size="icon"
          variant="ghost"
          className="size-7"
          onClick={onClose}
          aria-label="Close recommendations"
        >
          <X className="size-4" />
        </Button>
      </div>

      {error ? (
        <ErrorState message={error.message} />
      ) : isLoading ? (
        <div className="flex items-center gap-2 py-6 text-sm text-muted-foreground">
          <Spinner /> finding similar repos…
        </div>
      ) : !data || data.length === 0 ? (
        <EmptyState message="No similar repos found." />
      ) : (
        <div className="flex flex-col gap-2">
          {data.map((r) => (
            <a
              key={r.id}
              href={r.url ?? '#'}
              target={r.url ? '_blank' : undefined}
              rel="noreferrer"
              className="rounded-lg border border-border bg-background/40 p-2.5 transition-colors hover:border-primary/30"
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-mono text-sm">{r.name}</span>
                <span className="font-mono text-[11px] text-primary tabular-nums">
                  {compactNumber(r.trending_score)}
                </span>
              </div>
              {r.description && (
                <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">
                  {r.description}
                </p>
              )}
            </a>
          ))}
        </div>
      )}
    </Card>
  )
}
