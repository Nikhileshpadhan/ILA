import { useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BellRing,
  Braces,
  ChevronLeft,
  ChevronRight,
  Database,
  FileSearch,
  Gauge,
  Layers3,
  LogOut,
  Menu,
  Radio,
  X,
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'
import { AICopilot } from './AICopilot'

const navigation = [
  { label: 'Dashboard', to: '/dashboard', icon: Gauge, end: true },
  { label: 'Log Explorer', to: '/explorer', icon: FileSearch },
  { label: 'Ingestion Console', to: '/ingest', icon: Radio },
  { label: 'Mapping Intelligence', to: '/mappings', icon: Braces },
  { label: 'Security Alerts', to: '/alerts', icon: BellRing },
]

/* ---------- Animated SVG Logo ---------- */
function UlpfLogo({ size = 32 }: { size?: number }) {
  return (
    <motion.svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      whileHover={{ rotate: 360 }}
      transition={{ duration: 0.8, ease: 'easeInOut' }}
    >
      {/* Outer ring */}
      <motion.circle
        cx="20" cy="20" r="18"
        stroke="#10b981"
        strokeWidth="1.5"
        strokeDasharray="113"
        initial={{ strokeDashoffset: 113 }}
        animate={{ strokeDashoffset: 0, opacity: [0.4, 1] }}
        transition={{ duration: 1.2, ease: 'easeOut' }}
      />
      {/* Inner hexagon shield */}
      <motion.path
        d="M20 6 L32 13 L32 27 L20 34 L8 27 L8 13 Z"
        stroke="#34d399"
        strokeWidth="1.2"
        fill="rgba(16,185,129,0.08)"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.3, duration: 0.6, ease: 'backOut' }}
      />
      {/* Center node */}
      <motion.circle
        cx="20" cy="20" r="4"
        fill="#10b981"
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.6, duration: 0.4, type: 'spring', stiffness: 300 }}
      />
      {/* Pulse ring */}
      <motion.circle
        cx="20" cy="20" r="4"
        stroke="#10b981"
        strokeWidth="1"
        fill="none"
        animate={{ r: [4, 12], opacity: [0.6, 0] }}
        transition={{ duration: 2, repeat: Infinity, ease: 'easeOut', delay: 1 }}
      />
    </motion.svg>
  )
}

/* ---------- Magnetic nav link ---------- */
function MagneticNavLink({ to, label, icon: Icon, end }: { to: string; label: string; icon: React.ComponentType<{ size?: number; className?: string }>; end?: boolean }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `group flex items-center justify-between rounded-md px-3 py-2.5 text-sm transition ${
          isActive
            ? 'bg-zinc-900 text-white ring-1 ring-zinc-800'
            : 'text-zinc-500 hover:bg-zinc-900/70 hover:text-zinc-200'
        }`
      }
    >
      {({ isActive }) => (
        <motion.div
          className="flex w-full items-center justify-between"
          whileHover={{ x: 4 }}
          transition={{ type: 'spring', stiffness: 400, damping: 20 }}
        >
          <span className="flex items-center gap-3">
            <Icon size={17} className={isActive ? 'text-emerald-400' : 'text-zinc-600'} />
            {label}
          </span>
          <ChevronRight size={14} className={isActive ? 'text-zinc-500' : 'invisible'} />
        </motion.div>
      )}
    </NavLink>
  )
}

/* ---------- Sidebar variants ---------- */
const sidebarVariants = {
  expanded: { width: 288, transition: { duration: 0.3, ease: 'easeInOut' as const } },
  collapsed: { width: 72, transition: { duration: 0.3, ease: 'easeInOut' as const } },
}

export function Layout() {
  const { user, signOut } = useAuth()
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-300">
      {/* ---------- Desktop Sidebar ---------- */}
      <motion.aside
        variants={sidebarVariants}
        animate={collapsed ? 'collapsed' : 'expanded'}
        className="fixed inset-y-0 left-0 z-20 hidden flex-col border-r border-zinc-800/80 bg-zinc-950/95 backdrop-blur-md lg:flex"
        style={{ overflow: 'hidden' }}
      >
        {/* Logo area */}
        <div className="flex items-center gap-3 border-b border-zinc-800/80 px-5 py-6">
          <UlpfLogo size={collapsed ? 28 : 32} />
          <AnimatePresence>
            {!collapsed && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden whitespace-nowrap"
              >
                <p className="text-sm font-semibold tracking-[0.18em] text-white">ULPF</p>
                <p className="mt-0.5 text-[10px] uppercase tracking-[0.2em] text-zinc-500">Core observatory</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Section label */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="mt-8 flex items-center gap-2 px-5 text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-600"
            >
              <Layers3 size={13} /> Operations
            </motion.div>
          )}
        </AnimatePresence>

        {/* Navigation */}
        <nav className="mt-3 flex-1 space-y-1 px-3">
          {collapsed
            ? navigation.map(({ to, icon: Icon, end, label }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  title={label}
                  className={({ isActive }) =>
                    `flex items-center justify-center rounded-md p-2.5 transition ${
                      isActive ? 'bg-zinc-900 text-emerald-400 ring-1 ring-zinc-800' : 'text-zinc-600 hover:bg-zinc-900/70 hover:text-zinc-200'
                    }`
                  }
                >
                  <Icon size={18} />
                </NavLink>
              ))
            : navigation.map(({ label, to, icon, end }) => (
                <MagneticNavLink key={to} to={to} label={label} icon={icon} end={end} />
              ))}
        </nav>

        {/* Status panel */}
        <AnimatePresence>
          {!collapsed && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 10 }}
              className="mx-5 mb-5 rounded-lg border border-zinc-800 bg-zinc-900/50 p-4"
            >
              <div className="flex items-center gap-2 text-xs font-medium text-zinc-300">
                <Database size={14} className="text-emerald-400" /> Engine connected
              </div>
              <p className="mt-2 text-xs leading-5 text-zinc-600">SQLite telemetry store · local node</p>
              <div className="mt-3 flex items-center gap-2 text-[10px] uppercase tracking-[0.16em] text-emerald-500">
                <span className="size-1.5 rounded-full bg-emerald-400" /> Online
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Collapse toggle */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex items-center justify-center border-t border-zinc-800/80 py-3 text-zinc-600 transition hover:text-zinc-200"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </motion.aside>

      {/* ---------- Mobile Sidebar Overlay ---------- */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
            />
            <motion.aside
              initial={{ x: -288 }}
              animate={{ x: 0 }}
              exit={{ x: -288 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
              className="fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-zinc-800/80 bg-zinc-950/98 px-5 py-6 lg:hidden"
            >
              <div className="flex items-center justify-between border-b border-zinc-800/80 pb-6">
                <div className="flex items-center gap-3">
                  <UlpfLogo />
                  <div>
                    <p className="text-sm font-semibold tracking-[0.18em] text-white">ULPF</p>
                    <p className="mt-0.5 text-[10px] uppercase tracking-[0.2em] text-zinc-500">Core observatory</p>
                  </div>
                </div>
                <button onClick={() => setMobileOpen(false)} className="rounded-md p-1.5 text-zinc-600 hover:text-white">
                  <X size={18} />
                </button>
              </div>
              <nav className="mt-6 flex-1 space-y-1">
                {navigation.map(({ label, to, icon, end }) => (
                  <MagneticNavLink key={to} to={to} label={label} icon={icon} end={end} />
                ))}
              </nav>
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* ---------- Main content area ---------- */}
      <main
        className="min-h-screen transition-all duration-300"
        style={{ paddingLeft: collapsed ? 72 : 288 }}
      >
        {/* Sticky glassmorphism top bar */}
        <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-zinc-800/80 bg-zinc-950/80 px-5 backdrop-blur-md md:px-8">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileOpen(true)}
              className="rounded-md p-1.5 text-zinc-600 hover:text-white lg:hidden"
            >
              <Menu size={20} />
            </button>
            <span className="hidden text-xs text-zinc-600 md:block">Universal Log Pre-processing Framework</span>
          </div>
          <div className="flex items-center gap-3 text-xs text-zinc-500">
            <span className="size-1.5 rounded-full bg-emerald-400" />
            {user?.display_name || 'API connected'}
            <button
              onClick={signOut}
              title="Sign out"
              className="ml-2 rounded-md p-1.5 text-zinc-600 transition hover:bg-zinc-800 hover:text-rose-300"
            >
              <LogOut size={14} />
            </button>
          </div>
        </header>

        {/* Page content with Framer Motion transition */}
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -12 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          className="p-5 md:p-8"
        >
          <Outlet />
        </motion.div>
      </main>

      {/* Copilot */}
      <AICopilot />
    </div>
  )
}
