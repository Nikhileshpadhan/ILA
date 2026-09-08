import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, ChevronRight, Filter, RefreshCw, Search } from 'lucide-react'
import { getEvents, type EventRecord } from '../services/api'

const value = (record: Record<string, unknown>, key: string) => String(record[key] ?? '—')
const date = (timestamp: string) => new Date(timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'medium' })

const rowVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: (i: number) => ({ opacity: 1, y: 0, transition: { delay: i * 0.03, duration: 0.35 } }),
}

export function LogExplorer() {
  const [events, setEvents] = useState<EventRecord[]>([])
  const [total, setTotal] = useState(0)
  const [query, setQuery] = useState('')
  const [expanded, setExpanded] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadEvents = () => {
    setLoading(true)
    getEvents({ limit: 100, user: query || undefined, ip: query || undefined })
      .then((result) => { setEvents(result.items); setTotal(result.total); setError('') })
      .catch(() => setError('Unable to load events from the API.'))
      .finally(() => setLoading(false))
  }

  useEffect(() => { loadEvents() }, [])

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex flex-col justify-between gap-4 md:flex-row md:items-end"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-400">Event intelligence</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Log explorer</h1>
          <p className="mt-2 text-sm text-zinc-500">{total} events in the current window</p>
        </div>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={loadEvents}
          className="inline-flex items-center justify-center gap-2 rounded-lg border border-zinc-700 px-4 py-2.5 text-sm text-zinc-300 transition hover:border-emerald-500/50 hover:text-white"
        >
          <RefreshCw size={15} className={loading ? 'animate-spin' : ''} /> Refresh
        </motion.button>
      </motion.div>

      {/* Filter bar */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="flex flex-col gap-3 rounded-xl border border-zinc-800 bg-zinc-900/45 p-4 md:flex-row"
      >
        <div className="relative flex-1">
          <Search size={16} className="absolute left-3 top-3 text-zinc-600" />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => event.key === 'Enter' && loadEvents()}
            placeholder="Filter by user or source IP"
            className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-10 py-2.5 text-sm text-zinc-200 outline-none placeholder:text-zinc-700 focus:border-emerald-500/60"
          />
        </div>
        <motion.button
          whileHover={{ scale: 1.03 }}
          whileTap={{ scale: 0.97 }}
          onClick={loadEvents}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-400"
        >
          <Filter size={15} /> Apply filter
        </motion.button>
      </motion.div>

      {error && <div className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-300">{error}</div>}

      {/* Table */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="overflow-hidden rounded-xl border border-zinc-800/80 bg-zinc-900/45"
      >
        <div className="hidden grid-cols-[1.4fr_1.25fr_0.7fr_1fr_1fr_0.8fr_0.7fr] gap-4 border-b border-zinc-800 bg-zinc-900/70 px-5 py-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-zinc-600 md:grid">
          <span>Timestamp</span><span>Event ID</span><span>Source</span><span>IP</span><span>Action</span><span>Status</span><span>Severity</span>
        </div>

        {loading ? (
          <div className="px-5 py-16 text-center text-sm text-zinc-600">Reading the event stream...</div>
        ) : events.length === 0 ? (
          <div className="px-5 py-16 text-center text-sm text-zinc-600">No events match this filter.</div>
        ) : (
          events.map((event, index) => {
            const open = expanded === event.event_id
            const status = value(event.event, 'status')
            const severity = value(event.event, 'severity')

            return (
              <motion.div
                key={event.event_id}
                layout
                variants={rowVariants}
                initial="hidden"
                animate="visible"
                custom={index}
                className="border-b border-zinc-800/70 last:border-0"
              >
                <button
                  onClick={() => setExpanded(open ? null : event.event_id)}
                  className="grid w-full gap-2 px-5 py-4 text-left transition hover:bg-zinc-800/30 md:grid-cols-[1.4fr_1.25fr_0.7fr_1fr_1fr_0.8fr_0.7fr] md:items-center md:gap-4"
                >
                  <span className="flex items-center gap-2 text-xs text-zinc-400">
                    <span className="text-zinc-600">{open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}</span>
                    {date(event.timestamp)}
                  </span>
                  <span className="truncate font-mono text-xs text-zinc-500">{event.event_id}</span>
                  <span className="text-xs text-zinc-300">{value(event.source, 'type') || value(event.processing, 'parser')}</span>
                  <span className="font-mono text-xs text-zinc-400">{value(event.actor, 'source_ip')}</span>
                  <span className="text-sm text-zinc-200">{value(event.event, 'action')}</span>
                  <span className={`w-fit rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wider ${status.toLowerCase().includes('fail') ? 'bg-rose-500/10 text-rose-300' : 'bg-emerald-500/10 text-emerald-300'}`}>{status}</span>
                  <span className={`text-xs uppercase ${severity === 'high' || severity === 'critical' ? 'text-rose-400' : severity === 'medium' ? 'text-amber-400' : 'text-zinc-500'}`}>{severity}</span>
                </button>

                <AnimatePresence>
                  {open && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: 'auto', opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.35, ease: 'easeInOut' }}
                      className="overflow-hidden"
                    >
                      <div className="grid gap-4 border-t border-zinc-800/70 bg-zinc-950/70 p-5 lg:grid-cols-2">
                        <div>
                          <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-600">Raw event</p>
                          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-black p-4 font-mono text-xs leading-6 text-zinc-400">{event.raw_event}</pre>
                        </div>
                        <div>
                          <p className="mb-2 text-[10px] uppercase tracking-[0.16em] text-zinc-600">Normalized event</p>
                          <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-black p-4 font-mono text-xs leading-6 text-emerald-300">{JSON.stringify(event, null, 2)}</pre>
                        </div>
                        <div className="lg:col-span-2">
                          <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs text-emerald-300">processing: {value(event.processing, 'method')}</span>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )
          })
        )}
      </motion.div>
    </div>
  )
}
