import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AlertTriangle, ArrowUpRight, Clock3, Network, RefreshCw } from 'lucide-react'
import { getIncidents, type Incident } from '../services/api'

const formatDate = (value: string) => new Date(value).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })

const alertVariants = {
  hidden: { opacity: 0, x: 80, scale: 0.96 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    scale: 1,
    transition: { delay: i * 0.12, duration: 0.5, ease: 'easeOut' as const },
  }),
  exit: { opacity: 0, x: -40, transition: { duration: 0.3 } },
}

export function Alerts() {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getIncidents().then(setIncidents).finally(() => setLoading(false))
  }, [])

  return (
    <div className="mx-auto max-w-[1100px] space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-end justify-between"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-rose-400">Security posture</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Cross-source alerts</h1>
          <p className="mt-2 text-sm text-zinc-500">Signals that travelled farther than they should have.</p>
        </div>
        <span className="flex items-center gap-2 text-xs text-zinc-600">
          <RefreshCw size={14} /> {incidents.length} active
        </span>
      </motion.div>

      {loading ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="py-16 text-center text-sm text-zinc-600"
        >
          Correlating source activity...
        </motion.div>
      ) : incidents.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-xl border border-dashed border-zinc-800 py-20 text-center text-sm text-zinc-600"
        >
          <Network className="mx-auto mb-3 text-zinc-700" size={24} />
          No multi-source incidents detected.
        </motion.div>
      ) : (
        <AnimatePresence>
          <div className="space-y-4">
            {incidents.map((incident, i) => (
              <motion.article
                key={incident.incident_id}
                variants={alertVariants}
                initial="hidden"
                animate="visible"
                exit="exit"
                custom={i}
                whileHover={{
                  boxShadow: '0 0 30px 4px rgba(244,63,94,0.12)',
                  transition: { duration: 0.3 },
                }}
                className="rounded-xl border border-rose-500/40 bg-rose-500/[0.045] p-5 md:p-6"
              >
                <div className="flex flex-col justify-between gap-5 md:flex-row">
                  <div className="flex gap-4">
                    <motion.div
                      animate={{
                        boxShadow: [
                          '0 0 0px 0px rgba(244,63,94,0)',
                          '0 0 16px 4px rgba(244,63,94,0.3)',
                          '0 0 0px 0px rgba(244,63,94,0)',
                        ],
                      }}
                      transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
                      className="flex size-10 shrink-0 items-center justify-center rounded-lg border border-rose-500/30 bg-rose-500/10 text-rose-400"
                    >
                      <AlertTriangle size={19} />
                    </motion.div>
                    <div>
                      <div className="flex flex-wrap items-center gap-3">
                        <h2 className="font-semibold text-white">Suspicious multi-vector reconnaissance</h2>
                        <span className="rounded-full bg-rose-500/15 px-2 py-1 text-[10px] font-semibold uppercase tracking-wider text-rose-300">
                          {incident.severity}
                        </span>
                      </div>
                      <p className="mt-2 text-sm leading-6 text-zinc-400">{incident.narrative}</p>
                    </div>
                  </div>
                  <ArrowUpRight className="hidden text-rose-400 md:block" size={18} />
                </div>

                <div className="mt-6 grid gap-4 border-t border-rose-500/15 pt-5 sm:grid-cols-3">
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-zinc-600">Suspect IP</p>
                    <p className="mt-2 font-mono text-sm text-white">{incident.suspect_ip}</p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-zinc-600">Sources involved</p>
                    <p className="mt-2 flex flex-wrap gap-1.5">
                      {incident.sources_involved.map((source) => (
                        <span key={source} className="rounded bg-zinc-900 px-2 py-1 text-xs text-zinc-300">{source}</span>
                      ))}
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase tracking-[0.16em] text-zinc-600">Observed activity</p>
                    <p className="mt-2 flex items-center gap-2 text-sm text-zinc-300">
                      <Clock3 size={14} className="text-rose-400" />{incident.events_count} events
                    </p>
                  </div>
                </div>
                <div className="mt-4 text-xs text-zinc-600">
                  {formatDate(incident.first_seen)} — {formatDate(incident.last_seen)}
                </div>
              </motion.article>
            ))}
          </div>
        </AnimatePresence>
      )}
    </div>
  )
}
