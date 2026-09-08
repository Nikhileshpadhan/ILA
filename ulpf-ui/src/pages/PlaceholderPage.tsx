import { ArrowUpRight, Construction } from 'lucide-react'

type PlaceholderPageProps = {
  eyebrow: string
  title: string
  description: string
}

export function PlaceholderPage({ eyebrow, title, description }: PlaceholderPageProps) {
  return (
    <section className="mx-auto flex min-h-[calc(100vh-10rem)] max-w-5xl items-center">
      <div className="max-w-2xl">
        <div className="mb-5 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-400">
          <Construction size={14} /> {eyebrow}
        </div>
        <h1 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">{title}</h1>
        <p className="mt-5 max-w-xl text-base leading-7 text-zinc-500">{description}</p>
        <div className="mt-8 inline-flex items-center gap-2 border-b border-emerald-500/40 pb-2 text-sm text-emerald-400">
          Module ready for the next build phase <ArrowUpRight size={15} />
        </div>
      </div>
    </section>
  )
}
