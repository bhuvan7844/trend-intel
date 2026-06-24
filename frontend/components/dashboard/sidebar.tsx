'use client'

import {
  Activity,
  Boxes,
  Flame,
  Hash,
  type LucideIcon,
  Newspaper,
  Sparkles,
  Terminal,
} from 'lucide-react'
import { cn } from '@/lib/utils'

export type ViewId = 'overview' | 'repos' | 'hn' | 'devto' | 'assistant'

const NAV: {
  section: string
  items: { id: ViewId; label: string; icon: LucideIcon; hint?: string }[]
}[] = [
  {
    section: 'Intelligence',
    items: [
      { id: 'overview', label: 'Overview', icon: Activity },
      { id: 'assistant', label: 'AI Assistant', icon: Sparkles, hint: 'AI' },
    ],
  },
  {
    section: 'Signals',
    items: [
      { id: 'repos', label: 'Trending Repos', icon: Flame },
      { id: 'hn', label: 'Hacker News', icon: Newspaper },
      { id: 'devto', label: 'DEV.to', icon: Hash },
    ],
  },
]

export function Sidebar({
  active,
  onChange,
  online,
}: {
  active: ViewId
  onChange: (id: ViewId) => void
  online: boolean | null
}) {
  return (
    <aside className="flex h-full w-full flex-col gap-6 bg-sidebar px-3 py-5">
      <div className="flex items-center gap-2.5 px-2">
        <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
          <Terminal className="size-4" aria-hidden />
        </div>
        <div className="leading-tight">
          <p className="font-mono text-sm font-semibold tracking-tight">
            TrendIntel
          </p>
          <p className="font-mono text-[10px] text-muted-foreground">
            dev signal radar
          </p>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-5">
        {NAV.map((group) => (
          <div key={group.section} className="flex flex-col gap-1">
            <p className="px-2 pb-1 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
              {group.section}
            </p>
            {group.items.map((item) => {
              const Icon = item.icon
              const isActive = active === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onChange(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  className={cn(
                    'group flex items-center gap-2.5 rounded-md px-2 py-2 text-sm transition-colors',
                    isActive
                      ? 'bg-sidebar-accent text-foreground'
                      : 'text-muted-foreground hover:bg-sidebar-accent/60 hover:text-foreground',
                  )}
                >
                  <Icon
                    className={cn(
                      'size-4 shrink-0',
                      isActive
                        ? 'text-primary'
                        : 'text-muted-foreground group-hover:text-foreground',
                    )}
                    aria-hidden
                  />
                  <span className="flex-1 text-left">{item.label}</span>
                  {item.hint && (
                    <span className="rounded border border-primary/30 bg-primary/10 px-1 font-mono text-[9px] uppercase text-primary">
                      {item.hint}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        ))}
      </nav>

      <div className="flex items-center gap-2 rounded-md border border-border bg-card/50 px-2.5 py-2">
        <span
          className={cn(
            'relative flex size-2 items-center justify-center',
            online === false && 'opacity-100',
          )}
        >
          <span
            className={cn(
              'absolute inline-flex size-2 rounded-full',
              online === null && 'bg-muted-foreground',
              online === true && 'animate-ping bg-primary/60',
              online === false && 'bg-destructive',
            )}
          />
          <span
            className={cn(
              'relative inline-flex size-2 rounded-full',
              online === null && 'bg-muted-foreground',
              online === true && 'bg-primary',
              online === false && 'bg-destructive',
            )}
          />
        </span>
        <span className="flex items-center gap-1.5 font-mono text-[11px] text-muted-foreground">
          <Boxes className="size-3" aria-hidden />
          {online === null
            ? 'connecting…'
            : online
              ? 'api online'
              : 'api offline'}
        </span>
      </div>
    </aside>
  )
}
