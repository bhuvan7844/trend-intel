'use client'

import { useRef, useState } from 'react'
import { ArrowUp, Sparkles, Terminal, User } from 'lucide-react'
import { postJson } from '@/lib/api'
import type { ChatResponse } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/dashboard/states'
import { cn } from '@/lib/utils'

interface Message {
  role: 'user' | 'assistant'
  content: string
  error?: boolean
}

const SUGGESTIONS = [
  'What are the hottest repos right now?',
  'Summarize the top developer trends this week.',
  'Which programming languages are gaining momentum?',
  'What topics are emerging across HN and DEV.to?',
]

export function ChatView() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  async function send(query: string) {
    const text = query.trim()
    if (!text || loading) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])
    setLoading(true)
    requestAnimationFrame(() =>
      scrollRef.current?.scrollTo({ top: 9e9, behavior: 'smooth' }),
    )
    try {
      const res = await postJson<ChatResponse>('/api/chat', { query: text })
      setMessages((m) => [...m, { role: 'assistant', content: res.analysis }])
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: 'assistant',
          content:
            e instanceof Error ? e.message : 'Something went wrong with the AI.',
          error: true,
        },
      ])
    } finally {
      setLoading(false)
      requestAnimationFrame(() =>
        scrollRef.current?.scrollTo({ top: 9e9, behavior: 'smooth' }),
      )
    }
  }

  const empty = messages.length === 0

  return (
    <div className="flex h-[calc(100vh-8.5rem)] flex-col overflow-hidden rounded-lg border border-border bg-card">
      <div
        ref={scrollRef}
        className="scrollbar-thin flex-1 overflow-y-auto px-4 py-5"
      >
        {empty ? (
          <div className="mx-auto flex h-full max-w-xl flex-col items-center justify-center text-center">
            <div className="flex size-12 items-center justify-center rounded-lg border border-primary/30 bg-primary/10">
              <Sparkles className="size-6 text-primary" aria-hidden />
            </div>
            <h2 className="mt-4 text-lg font-medium">Trend Intelligence AI</h2>
            <p className="mt-1 max-w-sm text-sm text-muted-foreground text-pretty">
              Ask anything about trending repos, Hacker News, DEV.to articles,
              and emerging developer topics. Grounded on live data.
            </p>
            <div className="mt-6 grid w-full gap-2 sm:grid-cols-2">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => send(s)}
                  className="rounded-lg border border-border bg-background/50 p-3 text-left text-sm text-muted-foreground transition-colors hover:border-primary/30 hover:text-foreground"
                >
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="mx-auto flex max-w-3xl flex-col gap-5">
            {messages.map((m, i) => (
              <MessageBubble key={i} message={m} />
            ))}
            {loading && (
              <div className="flex items-center gap-2 pl-11 text-sm text-muted-foreground">
                <Spinner /> analyzing trend data…
              </div>
            )}
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault()
          send(input)
        }}
        className="border-t border-border p-3"
      >
        <div className="mx-auto flex max-w-3xl items-end gap-2">
          <div className="flex flex-1 items-center gap-2 rounded-lg border border-border bg-background px-3 py-2 focus-within:border-primary/50">
            <Terminal
              className="size-4 shrink-0 text-muted-foreground"
              aria-hidden
            />
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about developer trends…"
              aria-label="Message the AI assistant"
              className="flex-1 bg-transparent font-mono text-sm outline-none placeholder:text-muted-foreground"
            />
          </div>
          <Button
            type="submit"
            size="icon"
            disabled={loading || !input.trim()}
            aria-label="Send message"
          >
            <ArrowUp className="size-4" />
          </Button>
        </div>
      </form>
    </div>
  )
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user'
  return (
    <div className={cn('flex gap-3', isUser && 'flex-row-reverse')}>
      <div
        className={cn(
          'flex size-8 shrink-0 items-center justify-center rounded-md border',
          isUser
            ? 'border-border bg-muted'
            : 'border-primary/30 bg-primary/10',
        )}
      >
        {isUser ? (
          <User className="size-4 text-muted-foreground" aria-hidden />
        ) : (
          <Sparkles className="size-4 text-primary" aria-hidden />
        )}
      </div>
      <div
        className={cn(
          'max-w-[85%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed',
          isUser
            ? 'bg-secondary text-secondary-foreground'
            : message.error
              ? 'border border-destructive/30 bg-destructive/5 text-foreground'
              : 'border border-border bg-background/50 text-foreground',
        )}
      >
        <p className="whitespace-pre-wrap text-pretty">{message.content}</p>
      </div>
    </div>
  )
}
