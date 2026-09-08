import axios from 'axios'

export const api = axios.create({
  baseURL: 'http://127.0.0.1:8000',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ila_access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export type EventRecord = {
  event_id: string
  timestamp: string | null
  ingested_at: string
  source_name: string | null
  source_type: string | null
  source_ip: string | null
  user: string | null
  action: string | null
  status: string | null
  severity: string | null
  processing_method: string
  raw_event: string
}

export type SummaryStats = {
  hours: number
  total_events: number
  error_rate_percent: number
  throughput: {
    logs_per_second: number
    logs_per_minute: number
    logs_per_hour: number
  }
  by_source_type: Record<string, number>
  by_severity: Record<string, number>
  success_failure: { success: number; failure: number }
}

export type TimeSeriesPoint = { timestamp: string; count: number }
export type EntityCount = { entity: string; count: number }
export type TopEntities = {
  hours: number
  limit: number
  top_source_ips: EntityCount[]
  top_users: EntityCount[]
  most_active_systems: EntityCount[]
  top_actions: EntityCount[]
}

export type SecurityAlert = {
  alert_id: string
  rule_name: string
  severity: string
  entity_ip: string | null
  entity_user: string | null
  matched_events_count: number
  details: string
  timestamp: string
}

export type PaginatedEvents = {
  total: number
  page: number
  limit: number
  items: EventRecord[]
}

export type MappingRecord = {
  id: number
  signature_hash: string
  format_type: string
  field_mapping: Record<string, string>
  confidence: number
  is_approved: boolean
  created_at: string
  updated_at: string
}

export type Incident = {
  incident_id: string
  suspect_ip: string
  sources_involved: string[]
  events_count: number
  first_seen: string
  last_seen: string
  narrative: string
  severity: string
}

export type ChatResult = EventRecord

export type ChatResponse = {
  message: string
  filters: Record<string, string | null>
  results: ChatResult[]
}

export type User = { id: number; email: string; display_name: string }
export type AuthResult = { access_token: string; token_type: string; user: User }

export type EventQuery = {
  page?: number
  limit?: number
  source_type?: string
  severity?: string
  user?: string
  ip?: string
  start_time?: string
  end_time?: string
}

export async function getAnalyticsSummary(hours = 24) {
  const { data } = await api.get<SummaryStats>('/api/v1/analytics/summary', { params: { hours } })
  return data
}

export async function getTimeSeries(intervalMinutes = 15, hours = 24) {
  const { data } = await api.get<TimeSeriesPoint[]>('/api/v1/analytics/time-series', {
    params: { interval_minutes: intervalMinutes, hours },
  })
  return data
}

export async function getTopEntities(limit = 5, hours = 24) {
  const { data } = await api.get<TopEntities>('/api/v1/analytics/top-entities', {
    params: { limit, hours },
  })
  return data
}

export async function getEvents(params: EventQuery = {}) {
  const { data } = await api.get<PaginatedEvents>('/api/v1/events/', { params })
  return data
}

export async function getMappings() {
  const { data } = await api.get<MappingRecord[]>('/api/v1/mappings/')
  return data
}

export async function getIncidents() {
  const { data } = await api.get<Incident[]>('/api/v1/analytics/incidents')
  return data
}

export async function getAlerts() {
  const { data } = await api.get<SecurityAlert[]>('/api/v1/analytics/alerts')
  return data
}

export async function ingestLog(logString: string) {
  const { data } = await api.post<EventRecord>('/api/v1/ingest/single', { log: logString })
  return data
}

export async function uploadLogs(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<{ processed: number; failed: number; sample_event_ids: string[] }>(
    '/api/v1/ingest/upload',
    formData,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  )
  return data
}

export async function login(email: string, password: string) {
  const { data } = await api.post<AuthResult>('/api/v1/auth/login', { email, password })
  return data
}

export async function signup(email: string, password: string, displayName: string) {
  const { data } = await api.post<AuthResult>('/api/v1/auth/signup', { email, password, display_name: displayName })
  return data
}

export async function getCurrentUser() {
  const { data } = await api.get<User>('/api/v1/auth/me')
  return data
}

export async function askChat(query: string) {
  const { data } = await api.post<ChatResponse>('/api/v1/chat/ask', { query })
  return data
}
