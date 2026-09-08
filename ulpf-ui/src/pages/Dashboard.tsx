import { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ShieldAlert, Sparkles, AlertTriangle, Users } from 'lucide-react'
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  getAnalyticsSummary,
  getEvents,
  getAlerts,
  getTimeSeries,
  getTopEntities,
  type EventRecord,
  type SecurityAlert,
  type SummaryStats,
  type TimeSeriesPoint,
  type TopEntities,
} from '../services/api'

const panel = 'rounded-xl border border-zinc-800 bg-zinc-900/45'
const tooltipStyle = {
  backgroundColor: '#18181b',
  borderColor: '#27272a',
  color: '#e4e4e7',
  borderRadius: '8px',
}
const actionColors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#06b6d4', '#e11d48']
const formatNumber = (value: number) => new Intl.NumberFormat('en-US').format(value)

function statusOf(event: EventRecord) {
  return String(event.status ?? '').toLowerCase()
}

/* ---------- Stagger variants ---------- */
const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.1, delayChildren: 0.15 } },
}
const cardVariants = {
  hidden: { opacity: 0, y: 24, scale: 0.96 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.5, ease: 'easeOut' as const } },
}
const sectionVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.5, ease: 'easeOut' as const } },
}

function ChartPanel({ title, eyebrow, children, className = '', delay = 0 }: { title: string; eyebrow: string; children: React.ReactNode; className?: string; delay?: number }) {
  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut', delay }}
      className={`${panel} min-w-0 overflow-hidden ${className}`}
    >
      <div className="flex items-end justify-between border-b border-zinc-800/80 px-5 py-4">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">{eyebrow}</p>
          <h2 className="mt-1.5 text-sm font-semibold text-white">{title}</h2>
        </div>
        <motion.span
          animate={{ scale: [1, 1.6, 1], opacity: [0.7, 1, 0.7] }}
          transition={{ duration: 2, repeat: Infinity, ease: 'easeInOut' }}
          className="size-1.5 rounded-full bg-emerald-400 shadow-[0_0_10px_rgba(52,211,153,0.7)]"
        />
      </div>
      <div className="p-3">{children}</div>
    </motion.section>
  )
}

export function Dashboard() {
  const [summary, setSummary] = useState<SummaryStats | null>(null)
  const [series, setSeries] = useState<TimeSeriesPoint[]>([])
  const [entities, setEntities] = useState<TopEntities | null>(null)
  const [alerts, setAlerts] = useState<SecurityAlert[]>([])
  const [events, setEvents] = useState<EventRecord[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getAnalyticsSummary(), getTimeSeries(), getTopEntities(), getAlerts(), getEvents({ limit: 500 })])
      .then(([nextSummary, nextSeries, nextEntities, nextAlerts, nextEvents]) => {
        setSummary(nextSummary)
        setSeries(nextSeries)
        setEntities(nextEntities)
        setAlerts(nextAlerts)
        setEvents(nextEvents.items)
      })
      .catch(() => setError('Could not reach the local analytics API. Start the backend on port 8000.'))
  }, [])

  const actionData = useMemo(() => entities?.top_actions.map(a => ({ name: a.entity, value: a.count })) ?? [], [entities])
  
  const chartData = useMemo(() => {
    const interval = 15 * 60 * 1000
    const statuses = new Map<number, { successful: number; failed: number }>()
    events.forEach((event) => {
      const timestamp = new Date(event.timestamp || event.ingested_at || Date.now()).getTime()
      const bucket = Math.floor(timestamp / interval) * interval
      const current = statuses.get(bucket) ?? { successful: 0, failed: 0 }
      if (['success', 'succeeded', 'ok', 'passed'].includes(statusOf(event))) current.successful += 1
      else current.failed += 1
      statuses.set(bucket, current)
    })
    return series.map((point) => {
      const bucket = Math.floor(new Date(point.timestamp).getTime() / interval) * interval
      const current = statuses.get(bucket) ?? { successful: 0, failed: 0 }
      if (current.successful + current.failed === 0) current.successful = point.count
      return { label: new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), ...current }
    })
  }, [events, series])

  const cards = [
    { label: 'Total events', value: summary ? formatNumber(summary.total_events) : '--', icon: Activity, accent: 'text-emerald-400', bg: 'bg-emerald-500/10', detail: 'last 24 hours' },
    { label: 'Ingestion rate', value: summary ? `${summary.throughput.logs_per_second} /s` : '--', icon: Activity, accent: 'text-sky-400', bg: 'bg-sky-500/10', detail: 'logs per second' },
    { label: 'Global Error Rate', value: summary ? `${summary.error_rate_percent}%` : '--', icon: AlertTriangle, accent: 'text-amber-400', bg: 'bg-amber-500/10', detail: 'failed / total' },
    { label: 'Security incidents', value: alerts.length, icon: ShieldAlert, accent: 'text-rose-400', bg: 'bg-rose-500/10', detail: 'active alerts' },
  ]

  return (
    <div className="mx-auto max-w-[1600px] space-y-5">
      {/* Header */}
      <motion.section
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col justify-between gap-4 border-b border-zinc-800/80 pb-5 md:flex-row md:items-end"
      >
        <div>
          <div className="mb-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.2em] text-emerald-400">
            <Sparkles size={13} /> Security operations center
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-white md:text-3xl">Ido Log Analyzer (ILA)</h1>
          <p className="mt-1.5 text-xs text-zinc-500">A live read on telemetry health, threat pressure, and mapping behavior.</p>
        </div>
        <div className="flex items-center gap-2 text-[11px] text-zinc-500">
          <motion.span
            animate={{ scale: [1, 1.5, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="size-1.5 rounded-full bg-emerald-400"
          />
          24h window · auto refreshed on load
        </div>
      </motion.section>

      {error && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>}

      {/* KPI Cards — staggered entrance */}
      <motion.section
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4"
      >
        {cards.map(({ label, value, icon: Icon, accent, bg, detail }) => (
          <motion.div
            key={label}
            variants={cardVariants}
            whileHover={{ y: -4, transition: { duration: 0.2 } }}
            className={`${panel} p-4 transition-shadow hover:shadow-lg hover:shadow-zinc-900/50`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-500">{label}</span>
              <div className={`flex size-8 items-center justify-center rounded-lg ${bg}`}>
                <Icon size={16} className={accent} />
              </div>
            </div>
            <div className="mt-4 text-2xl font-semibold tracking-tight text-white">{value}</div>
            <div className="mt-1.5 text-[11px] text-zinc-600">{detail}</div>
          </motion.div>
        ))}
      </motion.section>

      {/* Charts Row 2 */}
      <motion.section variants={sectionVariants} initial="hidden" animate="visible" className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <ChartPanel title="Event Throughput & Status" eyebrow="Timeline / 15-minute buckets" delay={0.2}>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData} margin={{ top: 12, right: 8, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
              <XAxis dataKey="label" axisLine={false} tickLine={false} tick={{ fill: '#71717a', fontSize: 10 }} minTickGap={28} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#71717a', fontSize: 10 }} allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ color: '#a1a1aa', fontSize: 11, paddingTop: 8 }} />
              <Area type="monotone" dataKey="successful" name="Successful" stroke="#10b981" fill="#10b981" fillOpacity={0.2} stackId="status" animationDuration={1400} animationEasing="ease-out" />
              <Area type="monotone" dataKey="failed" name="Failed/Warnings" stroke="#f43f5e" fill="#f43f5e" fillOpacity={0.2} stackId="status" animationDuration={1400} animationEasing="ease-out" animationBegin={200} />
            </AreaChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Most Common Event Types" eyebrow="Actions mix" delay={0.35}>
          <div className="relative">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={actionData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={96} paddingAngle={3} stroke="#18181b" strokeWidth={3} animationDuration={1200} animationEasing="ease-out">
                  {actionData.map((entry, index) => <Cell key={entry.name} fill={actionColors[index % actionColors.length]} />)}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
                <Legend iconType="circle" wrapperStyle={{ color: '#a1a1aa', fontSize: 11 }} />
              </PieChart>
            </ResponsiveContainer>
            {actionData.length > 0 && (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-semibold text-white">{actionData.reduce((a, b) => a + b.value, 0)}</div>
                  <div className="text-[10px] uppercase tracking-wider text-zinc-600">actions</div>
                </div>
              </div>
            )}
          </div>
        </ChartPanel>
      </motion.section>

      {/* Charts Row 3 */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="grid gap-4 xl:grid-cols-3"
      >
        <ChartPanel title="Top Source IPs" eyebrow="Actor Analysis" delay={0.5}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={entities?.top_source_ips ?? []} layout="vertical" margin={{ top: 8, right: 14, left: 10, bottom: 8 }}>
              <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#71717a', fontSize: 10 }} allowDecimals={false} />
              <YAxis type="category" dataKey="entity" width={96} axisLine={false} tickLine={false} tick={{ fill: '#a1a1aa', fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" name="Events" fill="#e11d48" radius={[0, 3, 3, 0]} barSize={16} animationDuration={1000} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Top Users" eyebrow="Identity pressure" delay={0.6}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={entities?.top_users ?? []} layout="vertical" margin={{ top: 8, right: 14, left: 10, bottom: 8 }}>
              <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#71717a', fontSize: 10 }} allowDecimals={false} />
              <YAxis type="category" dataKey="entity" width={96} axisLine={false} tickLine={false} tick={{ fill: '#a1a1aa', fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" name="Events" fill="#d97706" radius={[0, 3, 3, 0]} barSize={16} animationDuration={1000} animationBegin={200} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
        <ChartPanel title="Most Active Systems" eyebrow="Infrastructure" delay={0.7}>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={entities?.most_active_systems ?? []} layout="vertical" margin={{ top: 8, right: 14, left: 10, bottom: 8 }}>
              <XAxis type="number" axisLine={false} tickLine={false} tick={{ fill: '#71717a', fontSize: 10 }} allowDecimals={false} />
              <YAxis type="category" dataKey="entity" width={96} axisLine={false} tickLine={false} tick={{ fill: '#a1a1aa', fontSize: 10 }} />
              <Tooltip contentStyle={tooltipStyle} />
              <Bar dataKey="count" name="Events" fill="#3b82f6" radius={[0, 3, 3, 0]} barSize={16} animationDuration={1000} animationBegin={300} />
            </BarChart>
          </ResponsiveContainer>
        </ChartPanel>
      </motion.section>

      {/* Charts Row 4: Threat Intelligence */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.8 }}
      >
        <ChartPanel title="Active Security Alerts" eyebrow="Threat Intelligence" delay={0.8}>
          {alerts.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-sm text-zinc-500">No active threats detected.</div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div key={alert.alert_id} className="flex flex-col gap-2 rounded-lg border border-zinc-800/60 bg-zinc-900/30 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-xs font-semibold text-rose-400 border border-rose-500/20">{alert.rule_name}</span>
                      <span className="text-sm font-semibold text-white">{alert.details}</span>
                    </div>
                    <div className="mt-1 flex items-center gap-4 text-xs text-zinc-500">
                      {alert.entity_ip && <span>IP: {alert.entity_ip}</span>}
                      {alert.entity_user && <span>User: {alert.entity_user}</span>}
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                  <div className="flex flex-col sm:items-end">
                    <span className="text-xs uppercase tracking-wider text-zinc-600">Events</span>
                    <span className="text-lg font-semibold text-white">{alert.matched_events_count}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ChartPanel>
      </motion.section>

      <div className="flex items-center gap-2 border-t border-zinc-800/80 pt-4 text-[11px] text-zinc-600">
        <Users size={13} /> Data is scoped to your authenticated observatory.
      </div>
    </div>
  )
}
