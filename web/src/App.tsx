import { RefreshCw, Search, ShieldAlert } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { fetchMessages, fetchSession, getTicket } from './api'
import type { PanelMessage, PanelSession } from './types'

/** Valores internos da API (não exibidos crus ao usuário). */
const STATUS_OPTS = ['TODOS', 'ACCEPTED', 'SENT', 'DELIVERED', 'READ', 'FAILED'] as const

function statusLabel(status?: string): string {
  switch ((status || '').toUpperCase()) {
    case 'ACCEPTED':
      return 'Aceito pela Meta'
    case 'SENT':
      return 'Enviado'
    case 'DELIVERED':
      return 'Entregue'
    case 'READ':
      return 'Lido'
    case 'FAILED':
      return 'Com falha'
    case 'CONNECTED':
      return 'Conectado'
    case 'DISCONNECTED':
      return 'Desconectado'
    case 'TODOS':
      return 'Todas as situações'
    default:
      return status || '—'
  }
}

function tipoEnvioLabel(tipo?: string): string {
  switch ((tipo || '').toLowerCase()) {
    case 'document':
      return 'Documento (PDF)'
    case 'template':
      return 'Modelo de mensagem'
    case 'text':
      return 'Texto'
    default:
      return tipo || '—'
  }
}

function statusTone(status?: string): string {
  switch ((status || '').toUpperCase()) {
    case 'DELIVERED':
    case 'READ':
    case 'SENT':
    case 'ACCEPTED':
      return 'bg-[#d8f5e8] text-[#0d524c] ring-1 ring-[#1b9e6e]/40'
    case 'FAILED':
      return 'bg-[#fde8e6] text-[#b42318] ring-1 ring-[#b42318]/25'
    default:
      return 'bg-white/70 text-[var(--color-muted)] ring-1 ring-[var(--color-line)]'
  }
}

function fmtWhen(v?: string): string {
  if (!v) return '—'
  const d = new Date(v)
  if (Number.isNaN(d.getTime())) return v
  return d.toLocaleString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function detailOf(m: PanelMessage): string {
  if (m.error_message) {
    return `${m.error_code ? `${m.error_code}: ` : ''}${m.error_message}`
  }
  if (m.template_name) return `Modelo: ${m.template_name}`
  if (m.caption) return m.caption
  if (m.local_file_path) {
    const parts = m.local_file_path.replace(/\\/g, '/').split('/')
    return parts[parts.length - 1] || m.local_file_path
  }
  return '—'
}

function Blocked({ expired }: { expired: boolean }) {
  return (
    <div className="flex min-h-screen items-center justify-center px-6">
      <div className="anim-rise w-full max-w-md border border-[var(--color-line)] bg-[var(--color-paper)]/90 p-8 shadow-[0_24px_60px_rgba(6,58,54,0.12)] backdrop-blur">
        <p className="font-display text-xs font-semibold tracking-[0.22em] text-[var(--color-leaf)]">
          PH SOFTWARES
        </p>
        <h1 className="mt-3 font-display text-2xl font-semibold tracking-tight text-[var(--color-ink)]">
          Acompanhar envios WhatsApp
        </h1>
        <div className="mt-5 flex gap-3 text-[var(--color-muted)]">
          <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0 text-[var(--color-warn)]" />
          <div>
            <p className="text-[15px] leading-relaxed text-[var(--color-ink-soft)]">
              {expired
                ? 'Este acesso expirou ou não é mais válido.'
                : 'Abra esta tela pelo GEPH (menu Ferramentas).'}
            </p>
            <p className="mt-2 text-sm leading-relaxed">
              Por segurança, o acompanhamento de envios só abre a partir do sistema GEPH, com o
              usuário já identificado.
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function App() {
  const ticket = useMemo(() => getTicket(), [])
  const [session, setSession] = useState<PanelSession | null>(null)
  const [messages, setMessages] = useState<PanelMessage[]>([])
  const [bootError, setBootError] = useState<'missing' | 'expired' | null>(
    ticket ? null : 'missing',
  )
  const [loading, setLoading] = useState(Boolean(ticket))
  const [filterStatus, setFilterStatus] = useState<(typeof STATUS_OPTS)[number]>('TODOS')
  const [query, setQuery] = useState('')
  const [updatedAt, setUpdatedAt] = useState<Date | null>(null)

  const reload = useCallback(async () => {
    if (!ticket) return
    setLoading(true)
    try {
      const [s, m] = await Promise.all([fetchSession(ticket), fetchMessages(ticket, 150)])
      setSession(s)
      setMessages(m.messages || [])
      setBootError(null)
      setUpdatedAt(new Date())
    } catch (e) {
      const status = (e as { status?: number }).status
      if (status === 403) setBootError('expired')
      else setBootError('expired')
      setSession(null)
      setMessages([])
    } finally {
      setLoading(false)
    }
  }, [ticket])

  useEffect(() => {
    if (!ticket) return
    void reload()
    const id = window.setInterval(() => void reload(), 15000)
    return () => window.clearInterval(id)
  }, [ticket, reload])

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return messages.filter((m) => {
      if (filterStatus !== 'TODOS' && (m.status || '').toUpperCase() !== filterStatus) {
        return false
      }
      if (!q) return true
      const blob = [
        m.to_wa_id,
        tipoEnvioLabel(m.msg_type),
        m.msg_type,
        statusLabel(m.status),
        m.status,
        m.usuario_geph,
        m.template_name,
        m.caption,
        m.local_file_path,
        m.error_message,
        String(m.id),
      ]
        .filter(Boolean)
        .join(' ')
        .toLowerCase()
      return blob.includes(q)
    })
  }, [messages, filterStatus, query])

  const counts = useMemo(() => {
    const c: Record<string, number> = { TOTAL: messages.length }
    for (const m of messages) {
      const s = (m.status || '—').toUpperCase()
      c[s] = (c[s] || 0) + 1
    }
    return c
  }, [messages])

  if (bootError === 'missing') return <Blocked expired={false} />
  if (bootError === 'expired' && !session) return <Blocked expired />

  const situacaoConta = session?.connected
    ? 'Conta conectada'
    : statusLabel(session?.status) === '—'
      ? 'Conta não conectada'
      : statusLabel(session?.status)

  return (
    <div className="mx-auto min-h-screen max-w-6xl px-4 pb-10 pt-6 sm:px-6 lg:px-8">
      <header className="anim-rise flex flex-col gap-5 border-b border-[var(--color-ink)]/10 pb-6 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-display text-[11px] font-semibold tracking-[0.28em] text-[var(--color-leaf)]">
            PH SOFTWARES
          </p>
          <h1 className="mt-1 font-display text-3xl font-semibold tracking-tight text-[var(--color-ink)] sm:text-4xl">
            Acompanhar envios WhatsApp
          </h1>
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-[var(--color-muted)]">
            Veja os boletos e mensagens enviados pelo WhatsApp deste escritório. A lista atualiza
            sozinha a cada 15 segundos.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <div
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ${
              session?.connected
                ? 'bg-[#d8f5e8] text-[#0d524c]'
                : 'bg-white/80 text-[var(--color-muted)]'
            }`}
          >
            <span
              className={`h-2 w-2 rounded-full ${
                session?.connected ? 'bg-[var(--color-leaf)] pulse-dot' : 'bg-[var(--color-line)]'
              }`}
            />
            {situacaoConta}
            {session?.display_phone ? ` · ${session.display_phone}` : ''}
          </div>
          <div className="text-xs text-[var(--color-muted)]">
            Usuário no GEPH:{' '}
            <span className="font-medium text-[var(--color-ink)]">
              {session?.usuario_geph || '—'}
            </span>
          </div>
          <button
            type="button"
            onClick={() => void reload()}
            disabled={loading}
            className="inline-flex items-center gap-2 bg-[var(--color-ink)] px-3.5 py-2 text-sm font-medium text-[var(--color-paper)] transition hover:bg-[var(--color-ink-soft)] disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            Atualizar lista
          </button>
        </div>
      </header>

      <section className="anim-rise-delay mt-6 grid gap-3 sm:grid-cols-4">
        {[
          ['Total', counts.TOTAL || 0],
          ['Entregues', (counts.DELIVERED || 0) + (counts.READ || 0)],
          ['Enviados', (counts.SENT || 0) + (counts.ACCEPTED || 0)],
          ['Com falha', counts.FAILED || 0],
        ].map(([label, value]) => (
          <div
            key={String(label)}
            className="border border-[var(--color-line)] bg-[var(--color-paper)]/75 px-4 py-3 backdrop-blur"
          >
            <p className="text-[11px] font-semibold tracking-wider text-[var(--color-muted)] uppercase">
              {label}
            </p>
            <p className="mt-1 font-display text-2xl font-semibold text-[var(--color-ink)]">
              {value}
            </p>
          </div>
        ))}
      </section>

      <section className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-center">
        <label className="relative min-w-0 flex-1">
          <Search className="pointer-events-none absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-[var(--color-muted)]" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar telefone, situação, PDF ou usuário…"
            className="w-full border border-[var(--color-line)] bg-white/80 py-2.5 pr-3 pl-10 text-sm outline-none focus:border-[var(--color-leaf)]"
          />
        </label>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value as (typeof STATUS_OPTS)[number])}
          className="border border-[var(--color-line)] bg-white/80 px-3 py-2.5 text-sm outline-none focus:border-[var(--color-leaf)]"
          aria-label="Filtrar por situação do envio"
        >
          {STATUS_OPTS.map((s) => (
            <option key={s} value={s}>
              {statusLabel(s)}
            </option>
          ))}
        </select>
        <p className="text-xs text-[var(--color-muted)] sm:ml-auto">
          {filtered.length} de {messages.length} envios
          {updatedAt ? ` · atualizado às ${updatedAt.toLocaleTimeString('pt-BR')}` : ''}
        </p>
      </section>

      <section className="mt-4 overflow-hidden border border-[var(--color-line)] bg-[var(--color-paper)]/80 backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-[var(--color-line)] bg-[var(--color-ink)] text-[var(--color-paper)]">
                <th className="px-3 py-3 font-medium">Quando</th>
                <th className="px-3 py-3 font-medium">Tipo</th>
                <th className="px-3 py-3 font-medium">Telefone</th>
                <th className="px-3 py-3 font-medium">Situação</th>
                <th className="px-3 py-3 font-medium">Usuário</th>
                <th className="px-3 py-3 font-medium">Detalhe</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-3 py-16 text-center text-[var(--color-muted)]">
                    {loading ? 'Carregando…' : 'Nenhum envio encontrado.'}
                  </td>
                </tr>
              ) : (
                filtered.map((m) => (
                  <tr
                    key={m.id}
                    className="border-b border-[var(--color-line)]/80 transition hover:bg-white/50"
                  >
                    <td className="px-3 py-3 whitespace-nowrap text-[var(--color-ink-soft)]">
                      {fmtWhen(m.created_at)}
                    </td>
                    <td className="px-3 py-3 font-medium">{tipoEnvioLabel(m.msg_type)}</td>
                    <td className="px-3 py-3 font-mono text-[13px]">{m.to_wa_id || '—'}</td>
                    <td className="px-3 py-3">
                      <span
                        className={`inline-block px-2 py-0.5 text-[11px] font-semibold tracking-wide ${statusTone(m.status)}`}
                      >
                        {statusLabel(m.status)}
                      </span>
                    </td>
                    <td className="px-3 py-3">{m.usuario_geph || '—'}</td>
                    <td
                      className="max-w-[280px] truncate px-3 py-3 text-[var(--color-muted)]"
                      title={detailOf(m)}
                    >
                      {detailOf(m)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
