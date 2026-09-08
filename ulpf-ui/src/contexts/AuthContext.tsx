import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { getCurrentUser, login, signup, type User } from '../services/api'

type AuthContextValue = {
  user: User | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<void>
  signUp: (email: string, password: string, displayName: string) => Promise<void>
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    if (!localStorage.getItem('ila_access_token')) { setLoading(false); return }
    getCurrentUser().then(setUser).catch(() => localStorage.removeItem('ila_access_token')).finally(() => setLoading(false))
  }, [])
  const signIn = async (email: string, password: string) => { const result = await login(email, password); localStorage.setItem('ila_access_token', result.access_token); setUser(result.user) }
  const signUp = async (email: string, password: string, displayName: string) => { const result = await signup(email, password, displayName); localStorage.setItem('ila_access_token', result.access_token); setUser(result.user) }
  const signOut = () => { localStorage.removeItem('ila_access_token'); setUser(null) }
  return <AuthContext.Provider value={{ user, loading, signIn, signUp, signOut }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}