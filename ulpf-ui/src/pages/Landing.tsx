import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { useGSAP } from '@gsap/react'
import {
  ArrowRight,
  Braces,
  ChevronRight,
  Cpu,
  Network,
  ShieldCheck,
  Sparkles,
} from 'lucide-react'

gsap.registerPlugin(ScrollTrigger)

/* ============================================================
   Data Pipeline Visualization (Canvas)
   ============================================================ */
function DataPipelineVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')!
    
    let width = 0
    let height = 0
    let animationFrameId: number

    const resize = () => {
      width = canvas.parentElement!.clientWidth
      height = canvas.parentElement!.clientHeight
      const dpr = window.devicePixelRatio || 1
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.scale(dpr, dpr)
      canvas.style.width = `${width}px`
      canvas.style.height = `${height}px`
    }
    
    window.addEventListener('resize', resize)
    resize()

    // Particles
    interface Particle {
      x: number
      y: number
      speed: number
      size: number
      type: 'circle' | 'square' | 'triangle'
      opacity: number
      state: 'entering' | 'processing' | 'exiting'
      angle: number
      distance: number
    }

    const particles: Particle[] = []
    const centerY = height / 2
    
    const createParticle = () => {
      const types: ('circle' | 'square' | 'triangle')[] = ['circle', 'square', 'triangle']
      const type = types[Math.floor(Math.random() * types.length)]
      return {
        x: -50,
        y: centerY + (Math.random() - 0.5) * height * 0.8,
        speed: 1 + Math.random() * 1.5,
        size: 2 + Math.random() * 3,
        type,
        opacity: 0.1 + Math.random() * 0.5,
        state: 'entering' as const,
        angle: 0,
        distance: 0
      }
    }

    for (let i = 0; i < 40; i++) {
      const p = createParticle()
      p.x = Math.random() * (width / 2) // distribute initially
      particles.push(p)
    }

    let ringAngle = 0

    const draw = () => {
      ctx.clearRect(0, 0, width, height)
      const centerX = width / 2
      const centerY = height / 2

      // Draw central ring (Universal Schema)
      ringAngle += 0.02
      ctx.save()
      ctx.translate(centerX, centerY)
      ctx.rotate(ringAngle)
      ctx.beginPath()
      ctx.arc(0, 0, 80, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)' // emerald-500 with opacity
      ctx.lineWidth = 1
      ctx.setLineDash([10, 15])
      ctx.stroke()
      
      ctx.beginPath()
      ctx.arc(0, 0, 60, 0, Math.PI * 2)
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.6)'
      ctx.lineWidth = 2
      ctx.setLineDash([5, 10])
      ctx.stroke()
      
      // Inner glowing core
      const coreGradient = ctx.createRadialGradient(0, 0, 0, 0, 0, 40)
      coreGradient.addColorStop(0, 'rgba(16, 185, 129, 0.2)')
      coreGradient.addColorStop(1, 'rgba(16, 185, 129, 0)')
      ctx.fillStyle = coreGradient
      ctx.beginPath()
      ctx.arc(0, 0, 40, 0, Math.PI * 2)
      ctx.fill()
      
      ctx.restore()

      // Update and draw particles
      particles.forEach(p => {
        if (p.state === 'entering') {
          // Move towards center
          const dx = centerX - p.x
          const dy = centerY - p.y
          const dist = Math.sqrt(dx * dx + dy * dy)
          
          if (dist < 85) {
            p.state = 'processing'
            p.angle = Math.atan2(dy, dx)
            p.distance = dist
          } else {
            p.x += (dx / dist) * p.speed
            p.y += (dy / dist) * p.speed
          }
          
          // Draw heterogeneous shapes
          ctx.fillStyle = `rgba(161, 161, 170, ${p.opacity})` // zinc-400
          ctx.beginPath()
          if (p.type === 'circle') {
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
          } else if (p.type === 'square') {
            ctx.rect(p.x - p.size, p.y - p.size, p.size * 2, p.size * 2)
          } else {
            ctx.moveTo(p.x, p.y - p.size)
            ctx.lineTo(p.x - p.size, p.y + p.size)
            ctx.lineTo(p.x + p.size, p.y + p.size)
            ctx.closePath()
          }
          ctx.fill()
          
        } else if (p.state === 'processing') {
          p.angle += 0.05
          p.distance -= 1
          p.x = centerX + Math.cos(p.angle) * p.distance
          p.y = centerY + Math.sin(p.angle) * p.distance
          
          if (p.distance < 20) {
            p.state = 'exiting'
            p.x = centerX + 40
            p.y = centerY + (Math.random() - 0.5) * 10
            p.type = 'circle' // normalize to uniform
            p.opacity = 0.8
            p.size = 2
          }
          
          ctx.fillStyle = `rgba(16, 185, 129, ${p.opacity})`
          ctx.beginPath()
          ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
          ctx.fill()
          
        } else if (p.state === 'exiting') {
          p.x += p.speed * 2
          ctx.fillStyle = `rgba(16, 185, 129, ${p.opacity})`
          ctx.beginPath()
          ctx.rect(p.x - p.size * 2, p.y - 1, p.size * 4, 2) // uniform stream shape
          ctx.fill()
          
          // Tail
          const tailGradient = ctx.createLinearGradient(p.x, p.y, p.x - 40, p.y)
          tailGradient.addColorStop(0, `rgba(16, 185, 129, ${p.opacity * 0.5})`)
          tailGradient.addColorStop(1, 'rgba(16, 185, 129, 0)')
          ctx.fillStyle = tailGradient
          ctx.fillRect(p.x - 40, p.y - 1, 40, 2)

          if (p.x > width + 50) {
            Object.assign(p, createParticle()) // Reset
          }
        }
      })
      
      // Keep adding particles occasionally
      if (Math.random() < 0.05 && particles.length < 80) {
        particles.push(createParticle())
      }

      animationFrameId = requestAnimationFrame(draw)
    }
    
    draw()

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return <canvas ref={canvasRef} className="absolute inset-0 pointer-events-none opacity-60" />
}

/* ============================================================
   Bento Box Feature Card
   ============================================================ */
interface FeatureProps {
  icon: React.ElementType
  title: string
  description: string
  stat: string
  statLabel: string
  colSpan?: number
}

function BentoCard({ icon: Icon, title, description, stat, statLabel, colSpan = 1 }: FeatureProps) {
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 })
  const cardRef = useRef<HTMLDivElement>(null)

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!cardRef.current) return
    const rect = cardRef.current.getBoundingClientRect()
    setMousePosition({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    })
  }

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      className={`feature-card group relative overflow-hidden rounded-3xl border border-white/10 bg-white/5 p-8 backdrop-blur-md transition-all hover:border-white/20 md:col-span-${colSpan}`}
      style={{ gridColumn: colSpan > 1 ? `span ${colSpan}` : 'span 1' }}
    >
      <div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
        style={{
          background: `radial-gradient(600px circle at ${mousePosition.x}px ${mousePosition.y}px, rgba(255,255,255,0.06), transparent 40%)`,
        }}
      />
      <div className="relative z-10 flex h-full flex-col">
        <div className="mb-6 flex size-12 items-center justify-center rounded-xl bg-emerald-500/20 text-emerald-400">
          <Icon size={24} />
        </div>
        <div className="mb-6">
          <span className="text-4xl font-bold tracking-tight text-white">{stat}</span>
          <span className="ml-2 text-xs uppercase tracking-wider text-zinc-500">{statLabel}</span>
        </div>
        <h3 className="mb-3 text-xl font-semibold text-white">{title}</h3>
        <p className="mt-auto text-sm leading-relaxed text-zinc-400">{description}</p>
      </div>
    </div>
  )
}

/* ============================================================
   Landing Page component
   ============================================================ */
export function Landing() {
  const featuresRef = useRef<HTMLElement>(null)

  useGSAP(() => {
    if (!featuresRef.current) return

    const cards = featuresRef.current.querySelectorAll('.feature-card')
    cards.forEach((card, i) => {
      gsap.fromTo(
        card,
        { opacity: 0, y: 40 },
        {
          opacity: 1,
          y: 0,
          duration: 0.8,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: card,
            start: 'top 85%',
          },
          delay: i * 0.1,
        }
      )
    })
  }, { scope: featuresRef })

  return (
    <motion.main
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.4 }}
      className="min-h-screen overflow-hidden bg-zinc-950 text-zinc-300 font-sans"
    >
      {/* ---------- Navbar ---------- */}
      <nav className="sticky top-0 z-50 border-b border-white/5 bg-zinc-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">
          <div className="flex items-center gap-3">
            <motion.div
              className="flex size-9 items-center justify-center rounded-lg bg-emerald-500 text-white"
              whileHover={{ scale: 1.05 }}
              transition={{ type: 'spring', stiffness: 400 }}
            >
              <ShieldCheck size={20} />
            </motion.div>
            <span className="text-sm font-semibold tracking-widest text-white">ULPF</span>
          </div>
          <div className="flex items-center gap-6 text-sm">
            <Link to="/login" className="text-zinc-400 transition hover:text-white font-medium">
              Sign in
            </Link>
            <Link
              to="/dashboard"
              className="rounded-lg bg-emerald-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/25"
            >
              Launch Console
            </Link>
          </div>
        </div>
      </nav>

      {/* ---------- Hero Section ---------- */}
      <section className="relative min-h-[90vh] flex flex-col justify-center overflow-hidden">
        <DataPipelineVisualization />

        {/* Ambient background glow */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 -tranzinc-x-1/2 -tranzinc-y-1/2 size-[40rem] rounded-full bg-emerald-500/10 blur-[120px]" />

        <div className="relative mx-auto flex w-full max-w-7xl flex-col items-center px-6 text-center z-10 pt-10 pb-20">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="mb-8 flex items-center gap-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-emerald-400 backdrop-blur-sm"
          >
            <Sparkles size={14} /> Enterprise Edition
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
            className="max-w-5xl text-5xl font-bold tracking-tight text-white md:text-7xl lg:text-8xl leading-tight"
          >
            Enterprise-Grade Log Normalization.{' '}
            <span className="text-emerald-400">Zero Data Loss.</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
            className="mt-8 max-w-2xl text-lg leading-relaxed text-zinc-400"
          >
            A vendor-agnostic translation layer that automatically onboards new log sources and makes heterogeneous events analytics-ready.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.3 }}
            className="mt-12 flex flex-col sm:flex-row items-center gap-4"
          >
            <Link
              to="/dashboard"
              className="group inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-lg bg-emerald-600 px-8 py-4 text-sm font-semibold text-white transition-all hover:bg-emerald-500 hover:-tranzinc-y-0.5 shadow-[0_0_20px_rgba(79,70,229,0.3)] hover:shadow-[0_0_30px_rgba(79,70,229,0.5)]"
            >
              Launch Console
              <ArrowRight size={16} className="transition group-hover:tranzinc-x-1" />
            </Link>
            <Link
              to="/architecture"
              className="inline-flex w-full sm:w-auto items-center justify-center gap-2 rounded-lg border border-zinc-700 bg-transparent px-8 py-4 text-sm font-semibold text-zinc-300 transition-colors hover:bg-zinc-800 hover:text-white"
            >
              View Architecture
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ---------- Features Section (Bento Grid) ---------- */}
      <section ref={featuresRef} className="relative bg-zinc-950 py-24 md:py-32">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 md:mb-24">
            <h2 className="text-3xl font-bold tracking-tight text-white md:text-5xl max-w-3xl">
              Engineered for scale, precision, and zero ambiguity.
            </h2>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            <BentoCard
              icon={Braces}
              title="Deterministic Parsing"
              description="One-pass structural recognition turns chaotic raw telemetry into a normalized Universal Event schema. Millisecond latency for known formats."
              stat="< 2ms"
              statLabel="latency"
            />
            <BentoCard
              icon={Cpu}
              title="ML Semantic Mapping"
              description="When structures are unknown, the ML layer learns field-to-field relationships from observed data. Automatic onboarding for unknown formats."
              stat="99.9%"
              statLabel="accuracy"
            />
            <BentoCard
              icon={Network}
              title="Cross-Source Correlation"
              description="Automatically link lateral movement, brute-force campaigns, and reconnaissance across firewall, VPN, IAM, and endpoint sources. Unified security analysis."
              stat="∞"
              statLabel="sources"
            />
          </div>
        </div>
      </section>

      {/* ---------- Footer ---------- */}
      <footer className="border-t border-white/5 bg-zinc-950">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-10 text-sm text-zinc-500">
          <div className="flex items-center gap-3">
            <ShieldCheck size={18} className="text-emerald-500" />
            <span className="font-medium text-zinc-300">ULPF Enterprise</span>
          </div>
          <span className="flex items-center gap-1">
            Built for scale <ChevronRight size={14} />
          </span>
        </div>
      </footer>
    </motion.main>
  )
}
