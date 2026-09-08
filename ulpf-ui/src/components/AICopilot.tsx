import { useState } from 'react'
import type { FormEvent } from 'react'
import { Bot, ChevronRight, LoaderCircle, MessageCircle, Send, X } from 'lucide-react'
import { askChat, type ChatResult } from '../services/api'

type Message = { role: 'user' | 'assistant'; text: string; results?: ChatResult[] }

const readField = (event: Record<string, unknown>, section: string, field: string) => {
  const value = event[section]
  return value && typeof value === 'object' ? String((value as Record<string, unknown>)[field] ?? '—') : '—'
}

export function AICopilot() {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [busy, setBusy] = useState(false)
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', text: 'Ask me about your logs in plain English. Try “show failed logins from 192.0.2.10”.' },
  ])
  const [selected, setSelected] = useState<ChatResult | null>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const trimmed = query.trim()
    if (!trimmed || busy) return
    setMessages((current) => [...current, { role: 'user', text: trimmed }])
    setQuery('')
    setBusy(true)
    try {
      const response = await askChat(trimmed)
      setMessages((current) => [...current, { role: 'assistant', text: response.message, results: response.results }])
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'Unable to query the AI assistant.'
      setMessages((current) => [...current, { role: 'assistant', text: detail }])
    } finally {
      setBusy(false)
    }
  }

  return <>
    {open && <section className="fixed bottom-24 right-5 z-40 flex h-[min(680px,calc(100vh-7rem))] w-[min(440px,calc(100vw-2.5rem))] flex-col overflow-hidden rounded-2xl border border-zinc-700 bg-zinc-900 shadow-2xl shadow-black/60 md:right-8">
      <header className="flex items-center justify-between border-b border-zinc-800 bg-zinc-950 px-4 py-3"><div className="flex items-center gap-3"><span className="flex size-8 items-center justify-center rounded-lg bg-emerald-500/15 text-emerald-400"><Bot size={17} /></span><div><h2 className="text-sm font-semibold text-white">ULPF Copilot</h2><p className="text-[10px] uppercase tracking-[0.15em] text-zinc-600">Natural language search</p></div></div><button onClick={() => setOpen(false)} className="rounded-md p-1.5 text-zinc-600 hover:bg-zinc-800 hover:text-white" title="Close assistant"><X size={16} /></button></header>
      <div className="flex-1 space-y-4 overflow-y-auto p-4">{messages.map((message, index) => <div key={`${message.role}-${index}`} className={message.role === 'user' ? 'ml-8' : 'mr-3'}><div className={message.role === 'user' ? 'rounded-xl rounded-br-sm bg-emerald-500 px-3 py-2.5 text-sm text-zinc-950' : 'rounded-xl rounded-bl-sm border border-zinc-800 bg-zinc-950 px-3 py-2.5 text-sm leading-6 text-zinc-300'}>{message.text}</div>{message.results && message.results.length > 0 && <div className="mt-2 overflow-hidden rounded-lg border border-zinc-800 bg-zinc-950"><div className="max-h-64 overflow-auto"><table className="w-full text-left text-[11px]"><thead className="sticky top-0 bg-zinc-900 text-[9px] uppercase tracking-wider text-zinc-600"><tr><th className="px-2 py-2">Time</th><th className="px-2 py-2">IP</th><th className="px-2 py-2">User</th><th className="px-2 py-2">Action</th><th /></tr></thead><tbody className="divide-y divide-zinc-800/70">{message.results.map((result) => <tr key={result.event_id} className="text-zinc-400"><td className="whitespace-nowrap px-2 py-2">{new Date(result.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</td><td className="max-w-24 truncate px-2 py-2 font-mono">{readField(result.normalized_event, 'actor', 'source_ip')}</td><td className="max-w-20 truncate px-2 py-2">{readField(result.normalized_event, 'actor', 'user')}</td><td className="max-w-20 truncate px-2 py-2">{readField(result.normalized_event, 'event', 'action')}</td><td className="px-2 py-2"><button onClick={() => setSelected(result)} className="whitespace-nowrap text-[10px] text-emerald-400 hover:text-emerald-300">Inspect <ChevronRight size={11} className="inline" /></button></td></tr>)}</tbody></table></div></div>}</div>)}{busy && <div className="flex items-center gap-2 text-xs text-zinc-600"><LoaderCircle size={14} className="animate-spin text-emerald-400" /> Translating query and searching your events...</div>}</div>
      <form onSubmit={submit} className="border-t border-zinc-800 bg-zinc-950 p-3"><div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900 px-3 focus-within:border-emerald-500/50"><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ask about your logs..." className="min-w-0 flex-1 bg-transparent py-3 text-sm text-zinc-200 outline-none placeholder:text-zinc-600" /><button disabled={!query.trim() || busy} title="Send query" className="rounded-md p-2 text-emerald-400 transition hover:bg-emerald-500/10 disabled:opacity-30"><Send size={16} /></button></div></form>
    </section>}
    <button onClick={() => setOpen((value) => !value)} className="fixed bottom-5 right-5 z-40 flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-500 px-4 py-3 text-sm font-semibold text-zinc-950 shadow-lg shadow-emerald-950/40 transition hover:bg-emerald-400 md:right-8" title="Ask ULPF Copilot"><MessageCircle size={18} /> <span className="hidden sm:inline">Ask AI</span></button>
    {selected && <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/70 p-4 backdrop-blur-sm md:items-center"><section className="w-full max-w-2xl overflow-hidden rounded-xl border border-zinc-700 bg-zinc-900 shadow-2xl"><header className="flex items-center justify-between border-b border-zinc-800 px-5 py-4"><div><p className="text-[10px] uppercase tracking-[0.18em] text-emerald-400">Original evidence</p><h2 className="mt-1 font-mono text-sm text-white">{selected.event_id}</h2></div><button onClick={() => setSelected(null)} className="rounded-md p-2 text-zinc-600 hover:bg-zinc-800 hover:text-white" title="Close original log"><X size={17} /></button></header><pre className="max-h-[60vh] overflow-auto whitespace-pre-wrap p-5 font-mono text-xs leading-6 text-emerald-300">{selected.raw_event}</pre></section></div>}
  </>
}