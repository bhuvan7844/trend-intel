export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '') ||
  'http://localhost:8000'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

export async function fetcher<T>(path: string): Promise<T> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      headers: { Accept: 'application/json' },
    })
  } catch {
    throw new ApiError(
      0,
      `Unable to reach the API at ${API_BASE}. Make sure the backend is running.`,
    )
  }
  if (!res.ok) {
    let detail = res.statusText
    try {
      const body = await res.json()
      detail = body?.detail ?? detail
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const data = await res.json()
      detail = data?.detail ?? detail
    } catch {
      /* ignore */
    }
    throw new ApiError(res.status, detail)
  }
  return res.json() as Promise<T>
}

// ── Domain types (mirrors the FastAPI models) ──────────────────────────────
export interface Repo {
  id: number
  name: string
  description: string | null
  language: string | null
  trending_score: number
  stars?: number | null
  url?: string | null
  first_seen_at?: string
}

export interface HNStory {
  id: number
  title: string
  url?: string | null
  points: number
  author?: string | null
  num_comments?: number | null
}

export interface DevArticle {
  id: number
  title: string
  url?: string | null
  reactions: number
  tags?: string | null
  author?: string | null
}

export interface Analytics {
  summary: {
    total_repos: number
    total_mentions: number
    hn_mentions: number
    devto_mentions: number
    total_topics: number
  }
  top_languages: { language: string; repo_count: number }[]
  repos_added_last_7_days: { date: string; count: number }[]
  most_mentioned_repos: { repo: string; mentions: number; score: number }[]
  top_topics: { name: string; weekly_count: number; total_count: number }[]
  source_breakdown: {
    hn: { stories_fetched: number; mentions_created: number; avg_score: number }
    devto: {
      articles_fetched: number
      mentions_created: number
      avg_score: number
    }
  }
}

export interface ChatResponse {
  query: string
  analysis: string
}
