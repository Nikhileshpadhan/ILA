import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Braces, Check, Database, RefreshCw } from 'lucide-react'
import { getMappings, type MappingRecord } from '../services/api'

const containerVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08, delayChildren: 0.2 } },
}
const cardVariants = {
  hidden: { opacity: 0, y: 24, scale: 0.96 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: 0.45, ease: 'easeOut' as const } },
}

export function Mappings() {
  const [mappings, setMappings] = useState<MappingRecord[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getMappings().then(setMappings).finally(() => setLoading(false))
  }, [])

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="flex items-end justify-between"
      >
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-400">Learning layer</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Mapping intelligence</h1>
          <p className="mt-2 text-sm text-zinc-500">The structures ULPF recognizes and the fields it learned.</p>
        </div>
        <span className="flex items-center gap-2 text-xs text-zinc-600">
          <RefreshCw size={14} /> {mappings.length} signatures
        </span>
      </motion.div>

      {loading ? (
        <div className="py-16 text-center text-sm text-zinc-600">Loading mapping memory...</div>
      ) : (
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"
        >
          {mappings.map((mapping) => (
            <motion.article
              key={mapping.signature_hash}
              variants={cardVariants}
              whileHover={{ y: -4, transition: { duration: 0.2 } }}
              className="rounded-xl border border-zinc-800/80 bg-zinc-900/45 p-5 transition-shadow hover:shadow-lg hover:shadow-emerald-500/5"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <motion.div
                    whileHover={{ rotate: 15, scale: 1.1 }}
                    transition={{ type: 'spring', stiffness: 400 }}
                    className="flex size-9 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400"
                  >
                    <Braces size={17} />
                  </motion.div>
                  <div>
                    <p className="text-sm font-semibold text-white">{mapping.format_type}</p>
                    <p className="mt-1 max-w-48 truncate font-mono text-[10px] text-zinc-600">{mapping.signature_hash}</p>
                  </div>
                </div>
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-300">
                  {Math.round(mapping.confidence * 100)}%
                </span>
              </div>

              <div className="mt-5 space-y-2 border-t border-zinc-800/70 pt-4">
                {Object.entries(mapping.field_mapping).map(([source, target]) => (
                  <div key={source} className="flex items-center justify-between gap-3 font-mono text-[11px]">
                    <span className="truncate text-zinc-500">{source}</span>
                    <span className="text-zinc-300">→ {target}</span>
                  </div>
                ))}
              </div>

              <div className="mt-5 flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-zinc-600">
                <Check size={13} className="text-emerald-400" /> Approved learning
              </div>
            </motion.article>
          ))}
        </motion.div>
      )}

      {!loading && mappings.length === 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="rounded-xl border border-dashed border-zinc-800 py-16 text-center text-sm text-zinc-600"
        >
          <Database className="mx-auto mb-3 text-zinc-700" size={22} />
          No learned mappings yet.
        </motion.div>
      )}
    </div>
  )
}
