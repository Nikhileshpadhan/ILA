import { useEffect, useRef, useState } from 'react'
import type { ChangeEvent } from 'react'
import { motion } from 'framer-motion'
import { animate as animeAnimate, type JSAnimation } from 'animejs'
import { CheckCircle2, FileUp, Play, RotateCcw, UploadCloud } from 'lucide-react'
import { ingestLog, uploadLogs, type EventRecord } from '../services/api'

const sample = '{"username":"alice","source_ip":"192.0.2.10","action":"login","status":"success"}'

export function IngestionConsole() {
  const [log, setLog] = useState(sample)
  const [output, setOutput] = useState('Waiting for input...')
  const [loading, setLoading] = useState(false)
  const [uploadResult, setUploadResult] = useState('')
  const fileRef = useRef<HTMLInputElement>(null)
  const outputRef = useRef<HTMLPreElement>(null)
  const typingRef = useRef<JSAnimation | null>(null)

  /* ---------- Typing reveal effect ---------- */
  const revealOutput = (text: string) => {
    if (!outputRef.current) {
      setOutput(text)
      return
    }
    // Cancel previous typing animation
    if (typingRef.current) typingRef.current.pause()

    const el = outputRef.current
    el.textContent = ''
    const obj = { progress: 0 }

    typingRef.current = animeAnimate(obj, {
      progress: text.length,
      duration: Math.min(text.length * 12, 2500),
      ease: 'linear',
      onUpdate: () => {
        el.textContent = text.slice(0, obj.progress)
      },
      onComplete: () => {
        el.textContent = text
        setOutput(text)
      },
    })
  }

  // Cleanup anime on unmount
  useEffect(() => {
    return () => {
      if (typingRef.current) typingRef.current.pause()
    }
  }, [])

  const process = async () => {
    if (!log.trim()) return
    setLoading(true)
    revealOutput('> initializing ILA pipeline\n> detecting source signature...')
    try {
      const event: EventRecord = await ingestLog(log)
      revealOutput(JSON.stringify(event, null, 2))
    } catch (error) {
      revealOutput(`> processing failed\n${error instanceof Error ? error.message : 'Unable to reach API'}`)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return
    setLoading(true)
    setUploadResult(`Uploading ${file.name}...`)
    try {
      const result = await uploadLogs(file)
      setUploadResult(`${result.processed} processed · ${result.failed} failed`)
      revealOutput(JSON.stringify(result, null, 2))
    } catch {
      setUploadResult('Upload failed. Check the API and supported file type.')
    } finally {
      setLoading(false)
      event.target.value = ''
    }
  }

  return (
    <div className="mx-auto max-w-[1500px] space-y-6">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <p className="text-xs uppercase tracking-[0.2em] text-emerald-400">Live intake</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-white">Ingestion console</h1>
        <p className="mt-2 text-sm text-zinc-500">Send raw telemetry directly into the normalization engine.</p>
      </motion.div>

      <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        {/* Input panel */}
        <motion.section
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="rounded-xl border border-zinc-800/80 bg-zinc-900/45 p-5 md:p-6"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-white">Raw log input</h2>
              <p className="mt-1 text-xs text-zinc-600">JSON, CEF, syslog, or key-value text</p>
            </div>
            <motion.button
              whileHover={{ rotate: -180 }}
              transition={{ duration: 0.3 }}
              onClick={() => setLog('')}
              title="Clear input"
              className="rounded-md p-2 text-zinc-600 transition hover:bg-zinc-800 hover:text-zinc-200"
            >
              <RotateCcw size={15} />
            </motion.button>
          </div>
          <textarea
            value={log}
            onChange={(event) => setLog(event.target.value)}
            spellCheck={false}
            className="mt-5 h-80 w-full resize-none rounded-lg border border-zinc-800 bg-black p-4 font-mono text-xs leading-6 text-zinc-300 outline-none placeholder:text-zinc-700 focus:border-emerald-500/60"
            placeholder="Paste one raw log event..."
          />
          <div className="mt-4 flex flex-wrap gap-3">
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={process}
              disabled={loading || !log.trim()}
              className="inline-flex items-center gap-2 rounded-lg bg-emerald-500 px-4 py-2.5 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-400 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Play size={15} /> {loading ? 'Processing...' : 'Process log'}
            </motion.button>
            <input ref={fileRef} type="file" accept=".log,.txt,.json,.csv" onChange={handleUpload} className="hidden" />
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => fileRef.current?.click()}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg border border-zinc-700 px-4 py-2.5 text-sm text-zinc-300 transition hover:border-emerald-500/50 hover:text-white disabled:opacity-40"
            >
              <UploadCloud size={15} /> Upload file
            </motion.button>
          </div>
          {uploadResult && (
            <motion.p
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-4 flex items-center gap-2 text-xs text-emerald-400"
            >
              <CheckCircle2 size={14} />{uploadResult}
            </motion.p>
          )}
        </motion.section>

        {/* Terminal output panel */}
        <motion.section
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="overflow-hidden rounded-xl border border-zinc-800/80 bg-black"
        >
          <div className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-5 py-4">
            <div className="flex items-center gap-2">
              <motion.span
                animate={{ scale: [1, 1.3, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="size-2 rounded-full bg-emerald-400"
              />
              <span className="size-2 rounded-full bg-amber-400" />
              <span className="size-2 rounded-full bg-rose-400" />
              <span className="ml-2 font-mono text-xs text-zinc-500">ila / normalized-event</span>
            </div>
            <FileUp size={15} className="text-zinc-700" />
          </div>
          <pre
            ref={outputRef}
            className="h-[436px] overflow-auto whitespace-pre-wrap p-5 font-mono text-xs leading-6 text-emerald-300/90"
          >
            {output}
          </pre>
        </motion.section>
      </div>
    </div>
  )
}
