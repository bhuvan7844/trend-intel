export function compactNumber(n: number | null | undefined): string {
  if (n == null) return '0'
  return new Intl.NumberFormat('en', {
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(n)
}

export function fullNumber(n: number | null | undefined): string {
  if (n == null) return '0'
  return new Intl.NumberFormat('en').format(n)
}

export function relativeTime(iso?: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  const diff = Date.now() - date.getTime()
  const mins = Math.round(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.round(hours / 24)
  if (days < 30) return `${days}d ago`
  return date.toLocaleDateString()
}

// Stable color per language using a small curated palette.
const LANG_COLORS: Record<string, string> = {
  typescript: 'oklch(0.7 0.15 235)',
  javascript: 'oklch(0.82 0.16 95)',
  python: 'oklch(0.72 0.13 230)',
  rust: 'oklch(0.7 0.14 45)',
  go: 'oklch(0.78 0.12 200)',
  java: 'oklch(0.68 0.16 40)',
  'c++': 'oklch(0.68 0.16 320)',
  c: 'oklch(0.65 0.04 264)',
  ruby: 'oklch(0.62 0.2 25)',
  php: 'oklch(0.6 0.12 280)',
  swift: 'oklch(0.72 0.18 40)',
  kotlin: 'oklch(0.7 0.16 300)',
  shell: 'oklch(0.78 0.16 145)',
  html: 'oklch(0.68 0.18 35)',
  css: 'oklch(0.66 0.16 295)',
  dart: 'oklch(0.7 0.12 210)',
  elixir: 'oklch(0.66 0.14 300)',
}

export function languageColor(lang?: string | null): string {
  if (!lang) return 'oklch(0.6 0.01 264)'
  return LANG_COLORS[lang.toLowerCase()] ?? 'oklch(0.74 0.13 152)'
}

export function parseTags(tags: any): string[] {
  if (!tags) return [];
  
  // If the backend already parsed it into an array, clean up the items and return it
  if (Array.isArray(tags)) {
    return tags.map((t: any) => (typeof t === 'string' ? t.trim() : String(t).trim())).filter(Boolean).slice(0, 4);
  }
  
  // Fallback if it comes as a raw string format
  if (typeof tags === 'string') {
    return tags
      .split(/[\s,]+/)
      .map((t) => t.trim())
      .filter(Boolean)
      .slice(0, 4);
  }

  return [];
}

export function hostname(url?: string | null): string {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return ''
  }
}
