import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'

import { Layout } from './components/Layout'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './contexts/AuthContext'
import { Alerts } from './pages/Alerts'
import { AuthPage } from './pages/AuthPage'
import { Dashboard } from './pages/Dashboard'
import { IngestionConsole } from './pages/IngestionConsole'
import { LogExplorer } from './pages/LogExplorer'
import { Mappings } from './pages/Mappings'
import { Landing } from './pages/Landing'

function AnimatedRoutes() {
  const location = useLocation()
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<AuthPage mode="login" />} />
        <Route path="/signup" element={<AuthPage mode="signup" />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="explorer" element={<LogExplorer />} />
            <Route path="ingest" element={<IngestionConsole />} />
            <Route path="mappings" element={<Mappings />} />
            <Route path="alerts" element={<Alerts />} />
          </Route>
        </Route>
      </Routes>
    </AnimatePresence>
  )
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AnimatedRoutes />
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
