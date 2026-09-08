import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, LockKeyhole, ShieldCheck } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export function AuthPage({ mode }: { mode: 'login' | 'signup' }) {
  const isSignup = mode === 'signup'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const { signIn, signUp } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const submit = async (event: FormEvent) => {
    event.preventDefault(); setError(''); setSubmitting(true)
    try { if (isSignup) await signUp(email, password, name); else await signIn(email, password); navigate((location.state as { from?: string } | null)?.from || '/dashboard', { replace: true }) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to authenticate') }
    finally { setSubmitting(false) }
  }

  return <main className="flex min-h-screen bg-zinc-950 text-zinc-300"><div className="hidden flex-1 overflow-hidden border-r border-zinc-800/80 bg-[radial-gradient(circle_at_30%_30%,rgba(16,185,129,0.13),transparent_35%),#09090b] p-12 lg:flex lg:flex-col lg:justify-between"><Link to="/" className="flex items-center gap-3"><span className="flex size-9 items-center justify-center rounded-lg bg-emerald-500 text-zinc-950"><ShieldCheck size={19} /></span><span className="text-sm font-semibold tracking-[0.2em] text-white">ILA</span></Link><div><p className="mb-5 text-xs uppercase tracking-[0.22em] text-emerald-400">Private observatory</p><h1 className="max-w-xl text-6xl font-semibold leading-tight tracking-[-0.04em] text-white">Your logs.<br />Your signals.<br /><span className="text-emerald-400">Your control.</span></h1><p className="mt-7 max-w-lg text-sm leading-7 text-zinc-500">A local-first intelligence layer for the telemetry your team already owns.</p></div><p className="text-xs text-zinc-700">ILA Engine · Phase 4</p></div><div className="flex w-full items-center justify-center px-6 py-12 lg:max-w-xl lg:px-16"><div className="w-full max-w-sm"><Link to="/" className="mb-12 inline-flex items-center gap-2 text-xs text-zinc-600 transition hover:text-white"><ArrowLeft size={14} /> Back to home</Link><div className="mb-8"><div className="mb-5 flex size-10 items-center justify-center rounded-xl border border-emerald-500/30 bg-emerald-500/10 text-emerald-400"><LockKeyhole size={19} /></div><h2 className="text-3xl font-semibold text-white">{isSignup ? 'Create your account' : 'Welcome back'}</h2><p className="mt-2 text-sm text-zinc-500">{isSignup ? 'Start your private log observatory.' : 'Sign in to continue to your observatory.'}</p></div><form onSubmit={submit} className="space-y-4">{isSignup && <label className="block text-xs text-zinc-500">Display name<input required value={name} onChange={(event) => setName(event.target.value)} className="mt-2 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm text-white outline-none focus:border-emerald-500/60" placeholder="" /></label>}<label className="block text-xs text-zinc-500">Email<input required type="email" value={email} onChange={(event) => setEmail(event.target.value)} className="mt-2 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm text-white outline-none focus:border-emerald-500/60" /></label><label className="block text-xs text-zinc-500">Password<input required minLength={8} type="password" value={password} onChange={(event) => setPassword(event.target.value)} className="mt-2 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm text-white outline-none focus:border-emerald-500/60" /></label>{error && <p className="rounded-lg border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs text-rose-300">{error}</p>}<button disabled={submitting} className="group flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-500 px-4 py-3 text-sm font-semibold text-zinc-950 transition hover:bg-emerald-400 disabled:opacity-50">{submitting ? 'Opening...' : isSignup ? 'Create account' : 'Sign in'}<ArrowRight size={15} className="transition group-hover:translate-x-1" /></button></form><p className="mt-7 text-center text-xs text-zinc-600">{isSignup ? 'Already have an account?' : 'Need an account?'} <Link to={isSignup ? '/login' : '/signup'} className="text-emerald-400 hover:text-emerald-300">{isSignup ? 'Sign in' : 'Sign up'}</Link></p>{!isSignup && <p className="mt-7 text-center text-[11px] text-zinc-700">Demo: demo@ila.local / demo12345</p>}</div></div></main>
}
