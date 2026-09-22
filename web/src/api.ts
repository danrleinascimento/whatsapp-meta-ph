import type { MessagesResponse, PanelSession } from './types'

function ticketFromUrl(): string | null {
  const q = new URLSearchParams(window.location.search)
  const t = q.get('ticket')
  return t && t.trim() ? t.trim() : null
}

export function getTicket(): string | null {
  return ticketFromUrl()
}

export async function fetchSession(ticket: string): Promise<PanelSession> {
  const r = await fetch(`/v1/panel/session?ticket=${encodeURIComponent(ticket)}`)
  if (!r.ok) {
    const err = new Error(`session_${r.status}`) as Error & { status: number }
    err.status = r.status
    throw err
  }
  return r.json()
}

export async function fetchMessages(ticket: string, limit = 100): Promise<MessagesResponse> {
  const r = await fetch(
    `/v1/panel/messages?ticket=${encodeURIComponent(ticket)}&limit=${limit}`,
  )
  if (!r.ok) {
    const err = new Error(`messages_${r.status}`) as Error & { status: number }
    err.status = r.status
    throw err
  }
  return r.json()
}
