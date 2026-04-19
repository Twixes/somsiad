export interface User {
  id: number
  username: string
  display_name: string
  avatar_url: string
}

export interface DashboardData {
  birthday_display: string | null
  pending_reminders: number
  total_commands: number
  total_ai_messages: number
  total_oofs: number
  active_polls: number
  pending_burns: number
  moderation_events: number
  commands_by_week: { week: string; commands: number; ai_messages: number }[]
}

export interface BirthdayData {
  birthday: { day: number; month: number; year: number | null } | null
  months: [number, string][]
  current_year: number
  public_server_count: number | null
  public_servers: { server_id: number; server_name: string }[]
}

export interface RemindersData {
  pending: { id: number; content: string; execute_at: string; requested_at: string }[]
  past: { content: string; execute_at: string }[]
}

export interface CommandsData {
  total_count: number
  unique_count: number
  most_used: string | null
  top_commands: { full_command: string; count: number }[]
  recent: { full_command: string; created_at: string }[]
}

export interface ModerationData {
  events: { type: string; type_label: string; type_icon: string; details: string | null; occurred_at: string }[]
  type_counts: { type: string; label: string; icon: string; count: number }[]
}

export interface PollsData {
  active: { matter: string; type: string; commenced_at: string; conclude_at: string }[]
  past: { matter: string; type: string; commenced_at: string; conclude_at: string }[]
}

export interface BurnsData {
  pending: { requested_at: string; execute_at: string }[]
  past: { requested_at: string; execute_at: string }[]
}

export interface OofData {
  total_oofs: number
  server_count: number
  per_server: { server_name: string; oofs: number }[]
}

let csrfToken: string | null = null

async function apiFetch(path: string, options?: RequestInit): Promise<Response> {
  const headers: Record<string, string> = {}
  if (csrfToken && options?.method && options.method !== 'GET') {
    headers['X-CSRF-Token'] = csrfToken
  }
  if (options?.body) {
    headers['Content-Type'] = 'application/json'
  }
  return fetch(`/panel/api${path}`, {
    ...options,
    headers: { ...headers, ...(options?.headers as Record<string, string>) },
  })
}

export async function getMe(): Promise<User | null> {
  const res = await apiFetch('/me')
  if (res.status === 401) return null
  const data = await res.json()
  csrfToken = data.csrf_token
  return data.user
}

export async function getDashboard(): Promise<DashboardData> {
  const res = await apiFetch('/dashboard')
  return res.json()
}

export async function getBirthday(): Promise<BirthdayData> {
  const res = await apiFetch('/birthday')
  const raw = (await res.json()) as Partial<BirthdayData>
  return {
    birthday: raw.birthday ?? null,
    months: raw.months ?? [],
    current_year: raw.current_year ?? new Date().getFullYear(),
    public_server_count: raw.public_server_count ?? null,
    public_servers: Array.isArray(raw.public_servers) ? raw.public_servers : [],
  }
}

export async function updateBirthday(
  day: number,
  month: number,
  year: string
): Promise<{ ok?: boolean; error?: string; message?: string }> {
  const res = await apiFetch('/birthday', {
    method: 'POST',
    body: JSON.stringify({ day, month, year }),
  })
  return res.json()
}

export async function deleteBirthday(): Promise<{ ok?: boolean; error?: string; message?: string }> {
  const res = await apiFetch('/birthday', { method: 'DELETE' })
  return res.json()
}

export async function hideBirthday(
  serverId: number
): Promise<{ ok?: boolean; error?: string; message?: string }> {
  const res = await apiFetch('/birthday/hide', {
    method: 'POST',
    body: JSON.stringify({ server_id: serverId }),
  })
  return res.json()
}

export async function getReminders(): Promise<RemindersData> {
  const res = await apiFetch('/reminders')
  return res.json()
}

export async function deleteReminder(
  id: number
): Promise<{ ok?: boolean; error?: string; message?: string }> {
  const res = await apiFetch(`/reminders/${id}`, { method: 'DELETE' })
  return res.json()
}

export async function getCommands(): Promise<CommandsData> {
  const res = await apiFetch('/commands')
  return res.json()
}

export async function getModeration(): Promise<ModerationData> {
  const res = await apiFetch('/moderation')
  return res.json()
}

export async function getPolls(): Promise<PollsData> {
  const res = await apiFetch('/polls')
  return res.json()
}

export async function getBurns(): Promise<BurnsData> {
  const res = await apiFetch('/burns')
  return res.json()
}

export async function getOof(): Promise<OofData> {
  const res = await apiFetch('/oof')
  return res.json()
}

export async function logout(): Promise<void> {
  await apiFetch('/logout', { method: 'POST' })
}
