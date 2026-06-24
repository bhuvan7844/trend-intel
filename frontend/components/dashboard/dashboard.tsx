'use client'

import { useEffect, useState } from 'react'
import useSWR from 'swr'
import { Menu, Search, X } from 'lucide-react'
import { fetcher } from '@/lib/api'
import { Sidebar, type ViewId } from '@/components/dashboard/sidebar'
import { Overview } from '@/components/dashboard/overview'
import { ReposView } from '@/components/dashboard/repos-view'
import { HNView } from '@/components/dashboard/hn-view'
import { DevtoView } from '@/components/dashboard/devto-view'
import { ChatView } from '@/components/dashboard/chat-view'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

const META: Record<ViewId, { title: string; desc: string }> = {
  overview: {
    title: 'Overview',
    desc: 'Live intelligence across the developer ecosystem',
  },
  repos: {
    title: 'Trending Repos',
    desc: 'Repositories ranked by trending score',
  },
  hn: { title: 'Hacker News', desc: 'Top stories driving developer attention' },
  devto: { title: 'DEV.to', desc: 'Most-reacted articles from the community' },
  assistant: {
    title: 'AI Assistant',
    desc: 'Ask questions grounded on live trend data',
  },
}

export function Dashboard() {
  const [view, setView] = useState<ViewId>('overview')
  const [search, setSearch] = useState('')
  const [debounced, setDebounced] = useState('')
  const [navOpen, setNavOpen] = useState(false)

  // Lightweight health check, revalidated periodically.
  const { error, data } = useSWR('/trending?limit=1', fetcher, {
    refreshInterval: 30000,
    shouldRetryOnError: true,
  })
  const online = data ? true : error ? false : null

  useEffect(() => {
    const t = setTimeout(() => setDebounced(search), 300)
    return () => clearTimeout(t)
  }, [search])

  const meta = META[view]

  function changeView(id: ViewId) {
    setView(id)
    setNavOpen(false)
    if (id !== 'repos') setSearch('')
  }

  return (
    <div className="grid-bg flex h-svh w-full overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden w-60 shrink-0 border-r border-border md:block">
        <Sidebar active={view} onChange={changeView} online={online} />
      </div>

      {/* Mobile sidebar */}
      {navOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          <button
            type="button"
            aria-label="Close navigation"
            className="absolute inset-0 bg-background/80 backdrop-blur-sm"
            onClick={() => setNavOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-64 border-r border-border">
            <Sidebar active={view} onChange={changeView} online={online} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        {/* Topbar */}
        <header className="flex items-center gap-3 border-b border-border bg-background/80 px-4 py-3 backdrop-blur-sm">
          <Button
            size="icon"
            variant="ghost"
            className="size-8 md:hidden"
            onClick={() => setNavOpen(true)}
            aria-label="Open navigation"
          >
            <Menu className="size-4" />
          </Button>

          <div className="min-w-0 flex-1">
            <h1 className="truncate text-base font-semibold tracking-tight">
              {meta.title}
            </h1>
            <p className="hidden truncate text-xs text-muted-foreground sm:block">
              {meta.desc}
            </p>
          </div>

          {view === 'repos' && (
            <div
              className={cn(
                'flex items-center gap-2 rounded-md border border-border bg-card px-2.5 py-1.5 transition-colors focus-within:border-primary/50',
                'w-40 sm:w-64',
              )}
            >
              <Search
                className="size-4 shrink-0 text-muted-foreground"
                aria-hidden
              />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search repos…"
                aria-label="Search repositories"
                className="min-w-0 flex-1 bg-transparent font-mono text-sm outline-none placeholder:text-muted-foreground"
              />
              {search && (
                <button
                  type="button"
                  onClick={() => setSearch('')}
                  aria-label="Clear search"
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="size-3.5" />
                </button>
              )}
            </div>
          )}
        </header>

        {/* Content */}
        <main className="scrollbar-thin flex-1 overflow-y-auto p-4">
          <div className="mx-auto max-w-6xl">
            {view === 'overview' && <Overview />}
            {view === 'repos' && <ReposView query={debounced} />}
            {view === 'hn' && <HNView />}
            {view === 'devto' && <DevtoView />}
            {view === 'assistant' && <ChatView />}
          </div>
        </main>
      </div>
    </div>
  )
}
