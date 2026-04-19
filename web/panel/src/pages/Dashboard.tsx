import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getDashboard, type DashboardData } from '../api'

function formatWeekLabel(isoDate: string): string {
  const d = new Date(isoDate + 'T00:00:00')
  return d.toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' })
}

export function Dashboard() {
  const [data, setData] = useState<DashboardData | null>(null)

  useEffect(() => {
    getDashboard().then(setData)
  }, [])

  if (!data) return null

  const hasAi = (data.total_ai_messages ?? 0) > 0
  const weeks = data.commands_by_week.map((w) => ({
    week: w.week,
    commands: w.commands ?? 0,
    ai: w.ai_messages ?? 0,
    total: (w.commands ?? 0) + (w.ai_messages ?? 0),
  }))
  const maxCount = Math.max(...weeks.map((w) => w.total), 1)

  return (
    <>
      <div className="cards">
        <div className="card card--wide">
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 16 }}>
            <span className="card__icon" style={{ marginBottom: 0 }}>📈</span>
            <div>
              <div className="card__label">Wywołane komendy</div>
              <div className="card__value">{data.total_commands}</div>
            </div>
            {hasAi && (
              <div style={{ marginLeft: 16 }}>
                <div className="card__label">Wiadomości AI</div>
                <div className="card__value">{data.total_ai_messages}</div>
              </div>
            )}
            <Link to="/komendy" className="card__link" style={{ marginTop: 0, marginLeft: 'auto' }}>
              Szczegóły
            </Link>
          </div>
          <div className="chart">
            {weeks.map((w) => (
              <div className="chart__col" key={w.week}>
                <span className="chart__count">{w.total || ''}</span>
                <div style={{ flexGrow: maxCount - w.total, minHeight: 0 }} />
                <div className="chart__bar-stack" style={{ flexGrow: Math.max(w.total, maxCount * 0.02), minHeight: 0 }}>
                  {w.ai > 0 && <div className="chart__bar chart__bar--ai" style={{ flex: w.ai }} />}
                  <div className="chart__bar chart__bar--commands" style={{ flex: w.commands || 1 }} />
                </div>
                <span className="chart__label">{formatWeekLabel(w.week)}</span>
              </div>
            ))}
          </div>
          {hasAi && (
            <div className="chart__legend">
              <span className="chart__legend-item"><span className="chart__legend-swatch chart__legend-swatch--commands" /> Komendy</span>
              <span className="chart__legend-item"><span className="chart__legend-swatch chart__legend-swatch--ai" /> AI</span>
            </div>
          )}
        </div>

        <div className="card">
          <span className="card__icon">🎂</span>
          <div className="card__label">Data urodzin</div>
          <div className="card__value">{data.birthday_display || 'Nie ustawiono'}</div>
          <Link to="/urodziny" className="card__link">Zarządzaj</Link>
        </div>

        <div className="card">
          <span className="card__icon">🍅</span>
          <div className="card__label">Oczekujące przypomnienia</div>
          <div className="card__value">{data.pending_reminders}</div>
          <Link to="/przypomnienia" className="card__link">Zobacz wszystkie</Link>
        </div>

        <div className="card">
          <span className="card__icon">📂</span>
          <div className="card__label">Zdarzenia w kartotece</div>
          <div className="card__value">{data.moderation_events}</div>
          <Link to="/kartoteka" className="card__link">Zobacz kartotekę</Link>
        </div>

        <div className="card">
          <span className="card__icon">🗳</span>
          <div className="card__label">Aktywne głosowania</div>
          <div className="card__value">{data.active_polls}</div>
          <Link to="/glosowania" className="card__link">Zobacz głosowania</Link>
        </div>

        <div className="card">
          <span className="card__icon">🔥</span>
          <div className="card__label">Oczekujące spalenia</div>
          <div className="card__value">{data.pending_burns}</div>
          <Link to="/spalenia" className="card__link">Zobacz spalenia</Link>
        </div>

        <div className="card">
          <span className="card__icon">💨</span>
          <div className="card__label">Łącznie oofnięć</div>
          <div className="card__value">{data.total_oofs}</div>
          <Link to="/oof" className="card__link">Zobacz statystyki</Link>
        </div>
      </div>
    </>
  )
}
