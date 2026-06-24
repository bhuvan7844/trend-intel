'use client'

import useSWR from 'swr'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  XAxis,
  YAxis,
} from 'recharts'
import {
  Boxes,
  GitFork,
  Hash,
  MessageSquareText,
  Newspaper,
  TrendingUp,
} from 'lucide-react'
import type { Analytics } from '@/lib/api'
import { fetcher } from '@/lib/api'
import { compactNumber, fullNumber, languageColor } from '@/lib/format'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from '@/components/ui/chart'
import { Card } from '@/components/ui/card'
import { ErrorState, LoadingRows } from '@/components/dashboard/states'

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
}: {
  label: string
  value: string
  sub: string
  icon: typeof Boxes
}) {
  return (
    <Card className="gap-0 p-4">
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <Icon className="size-4 text-muted-foreground" aria-hidden />
      </div>
      <span className="mt-3 font-mono text-3xl font-semibold tabular-nums">
        {value}
      </span>
      <span className="mt-1 text-xs text-muted-foreground">{sub}</span>
    </Card>
  )
}

export function Overview() {
  const { data, error, isLoading } = useSWR<Analytics>('/analytics', fetcher)

  if (error) return <ErrorState message={error.message} />
  if (isLoading || !data) return <LoadingRows rows={5} />

  const { summary, top_languages, repos_added_last_7_days, source_breakdown } =
    data

  const langData = top_languages.map((l) => ({
    name: l.language,
    value: l.repo_count,
    fill: languageColor(l.language),
  }))

  const maxTopic = Math.max(1, ...data.top_topics.map((t) => t.weekly_count))

  return (
    <div className="flex flex-col gap-4">
      {/* Stat row */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatCard
          label="Tracked Repos"
          value={fullNumber(summary.total_repos)}
          sub="repositories monitored"
          icon={GitFork}
        />
        <StatCard
          label="Mentions"
          value={fullNumber(summary.total_mentions)}
          sub={`${summary.hn_mentions} HN · ${summary.devto_mentions} DEV.to`}
          icon={MessageSquareText}
        />
        <StatCard
          label="Topics"
          value={fullNumber(summary.total_topics)}
          sub="emerging keywords"
          icon={Hash}
        />
        <StatCard
          label="Sources"
          value="2"
          sub="Hacker News · DEV.to"
          icon={Boxes}
        />
      </div>

      <div className="grid gap-3 lg:grid-cols-3">
        {/* Repos added over time */}
        <Card className="gap-0 p-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="flex items-center gap-2 text-sm font-medium">
                <TrendingUp className="size-4 text-primary" aria-hidden />
                Repos Discovered
              </h3>
              <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
                last 7 days
              </p>
            </div>
          </div>
          {repos_added_last_7_days.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No repos discovered in this window yet.
            </p>
          ) : (
            <ChartContainer
              config={{ count: { label: 'Repos', color: 'var(--chart-1)' } }}
              className="mt-4 h-[220px] w-full"
            >
              <AreaChart
                data={repos_added_last_7_days}
                margin={{ left: -16, right: 8, top: 8 }}
              >
                <defs>
                  <linearGradient id="fillRepos" x1="0" y1="0" x2="0" y2="1">
                    <stop
                      offset="5%"
                      stopColor="var(--color-count)"
                      stopOpacity={0.4}
                    />
                    <stop
                      offset="95%"
                      stopColor="var(--color-count)"
                      stopOpacity={0}
                    />
                  </linearGradient>
                </defs>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                <XAxis
                  dataKey="date"
                  tickLine={false}
                  axisLine={false}
                  tickMargin={8}
                  tickFormatter={(v: string) => v.slice(5)}
                  className="font-mono text-[10px]"
                />
                <YAxis
                  tickLine={false}
                  axisLine={false}
                  allowDecimals={false}
                  width={32}
                  className="font-mono text-[10px]"
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Area
                  dataKey="count"
                  type="monotone"
                  stroke="var(--color-count)"
                  strokeWidth={2}
                  fill="url(#fillRepos)"
                />
              </AreaChart>
            </ChartContainer>
          )}
        </Card>

        {/* Source breakdown */}
        <Card className="gap-3 p-4">
          <h3 className="text-sm font-medium">Source Breakdown</h3>
          <SourceRow
            icon={Newspaper}
            name="Hacker News"
            fetched={source_breakdown.hn.stories_fetched}
            mentions={source_breakdown.hn.mentions_created}
            avg={source_breakdown.hn.avg_score}
            color="var(--chart-3)"
          />
          <SourceRow
            icon={Hash}
            name="DEV.to"
            fetched={source_breakdown.devto.articles_fetched}
            mentions={source_breakdown.devto.mentions_created}
            avg={source_breakdown.devto.avg_score}
            color="var(--chart-2)"
          />
        </Card>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        {/* Language distribution */}
        <Card className="gap-0 p-4">
          <h3 className="text-sm font-medium">Language Distribution</h3>
          <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
            repos per language
          </p>
          {langData.length === 0 ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              No language data yet.
            </p>
          ) : (
            <ChartContainer
              config={{ value: { label: 'Repos' } }}
              className="mt-4 h-[260px] w-full"
            >
              <BarChart
                data={langData}
                layout="vertical"
                margin={{ left: 8, right: 16 }}
              >
                <CartesianGrid horizontal={false} stroke="var(--border)" />
                <XAxis
                  type="number"
                  hide
                  allowDecimals={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  tickLine={false}
                  axisLine={false}
                  width={84}
                  className="font-mono text-[11px]"
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="value" radius={4} barSize={16}>
                  {langData.map((entry) => (
                    <Cell key={entry.name} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ChartContainer>
          )}
        </Card>

        {/* Top topics */}
        <Card className="gap-0 p-4">
          <h3 className="text-sm font-medium">Top Topics</h3>
          <p className="mt-0.5 font-mono text-[11px] text-muted-foreground">
            by weekly mentions
          </p>
          <div className="mt-4 flex flex-col gap-2.5">
            {data.top_topics.length === 0 && (
              <p className="py-8 text-center text-sm text-muted-foreground">
                No topics tracked yet.
              </p>
            )}
            {data.top_topics.slice(0, 8).map((t) => (
              <div key={t.name} className="flex flex-col gap-1">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-mono text-foreground">{t.name}</span>
                  <span className="font-mono text-xs text-muted-foreground tabular-nums">
                    {t.weekly_count}
                    <span className="text-muted-foreground/50">
                      {' '}
                      / {t.total_count}
                    </span>
                  </span>
                </div>
                <div className="h-1.5 overflow-hidden rounded-full bg-muted">
                  <div
                    className="h-full rounded-full bg-primary"
                    style={{
                      width: `${(t.weekly_count / maxTopic) * 100}%`,
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Most mentioned repos */}
      <Card className="gap-0 p-4">
        <h3 className="text-sm font-medium">Most Mentioned Repos</h3>
        <div className="mt-3 flex flex-col divide-y divide-border">
          {data.most_mentioned_repos.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              No mentions recorded yet.
            </p>
          )}
          {data.most_mentioned_repos.map((r, i) => (
            <div
              key={r.repo}
              className="flex items-center gap-3 py-2.5 first:pt-0"
            >
              <span className="w-5 font-mono text-xs text-muted-foreground tabular-nums">
                {String(i + 1).padStart(2, '0')}
              </span>
              <span className="flex-1 truncate font-mono text-sm">
                {r.repo}
              </span>
              <span className="font-mono text-xs text-muted-foreground">
                score {compactNumber(r.score)}
              </span>
              <span className="rounded border border-primary/30 bg-primary/10 px-2 py-0.5 font-mono text-xs text-primary tabular-nums">
                {r.mentions} mentions
              </span>
            </div>
          ))}
        </div>
      </Card>
    </div>
  )
}

function SourceRow({
  icon: Icon,
  name,
  fetched,
  mentions,
  avg,
  color,
}: {
  icon: typeof Boxes
  name: string
  fetched: number
  mentions: number
  avg: number
  color: string
}) {
  return (
    <div className="rounded-lg border border-border bg-background/40 p-3">
      <div className="flex items-center gap-2">
        <Icon className="size-4" style={{ color }} aria-hidden />
        <span className="text-sm font-medium">{name}</span>
      </div>
      <div className="mt-3 grid grid-cols-3 gap-2 text-center">
        <Metric label="fetched" value={compactNumber(fetched)} />
        <Metric label="mentions" value={compactNumber(mentions)} />
        <Metric label="avg score" value={String(avg)} />
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="font-mono text-lg font-semibold tabular-nums">{value}</p>
      <p className="font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
    </div>
  )
}
