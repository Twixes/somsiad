import { useEffect, useState, useCallback } from 'react'
import { getCommands, getCommandsChart, type CommandsData, type CommandsChartData } from '../api'
import { DiscordLocation } from '../DiscordLocation'

const RANGE_OPTIONS = [
  { label: '4 tygodnie', weeks: 4 },
  { label: '12 tygodni', weeks: 12 },
  { label: 'Rok', weeks: 52 },
]

function formatWeekLabel(isoDate: string): string {
  const d = new Date(isoDate + 'T00:00:00')
  return d.toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' })
}

export function Commands() {
  const [data, setData] = useState<CommandsData | null>(null)
  const [chart, setChart] = useState<CommandsChartData | null>(null)
  const [weeks, setWeeks] = useState(12)

  useEffect(() => {
    getCommands().then(setData)
  }, [])

  const loadChart = useCallback((w: number) => {
    setWeeks(w)
    getCommandsChart(w).then(setChart)
  }, [])

  useEffect(() => {
    loadChart(12)
  }, [loadChart])

  if (!data) return null

  const hasAi = (data.total_ai_messages ?? 0) > 0

  const chartWeeks = chart
    ? chart.commands_by_week.map((w) => ({
        week: w.week,
        commands: w.commands ?? 0,
        ai: w.ai_messages ?? 0,
        total: (w.commands ?? 0) + (w.ai_messages ?? 0),
      }))
    : []
  const maxCount = Math.max(...chartWeeks.map((w) => w.total), 1)

  // For wide ranges, only show every Nth label
  const labelEvery = chartWeeks.length > 12 ? Math.ceil(chartWeeks.length / 10) : 1

  return (
    <>
      <div className="section">
        <p className="section__desc">
          Tu widzisz statystyki swoich komend Somsiada. Każda komenda wywołana na Discordzie (np. <code>pomocy</code>,{' '}
          <code>stat serwer</code>, <code>oof</code>) jest tutaj zliczana.
        </p>
      </div>

      <div className="cards">
        <div className="card">
          <span className="card__icon">📊</span>
          <div className="card__label">Wywołania komend</div>
          <div className="card__value">{data.total_count}</div>
        </div>
        <div className="card">
          <span className="card__icon">🔢</span>
          <div className="card__label">Unikalne komendy</div>
          <div className="card__value">{data.unique_count}</div>
        </div>
        <div className="card">
          <span className="card__icon">🏆</span>
          <div className="card__label">Najczęściej używana</div>
          <div className="card__value">{data.most_used || '—'}</div>
        </div>
        {hasAi && (
          <div className="card">
            <span className="card__icon">🤖</span>
            <div className="card__label">Wiadomości AI</div>
            <div className="card__value">{data.total_ai_messages}</div>
          </div>
        )}
      </div>

      {chart && (
        <div className="section">
          <div className="chart-header">
            <h2 className="section__title" style={{ marginBottom: 0 }}>Aktywność</h2>
            <div className="range-picker">
              {RANGE_OPTIONS.map((opt) => (
                <button
                  key={opt.weeks}
                  className={`range-picker__btn${weeks === opt.weeks ? ' range-picker__btn--active' : ''}`}
                  onClick={() => loadChart(opt.weeks)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
          <div className="card card--wide">
            <div className={`chart${chartWeeks.length > 20 ? ' chart--dense' : ''}`}>
              {chartWeeks.map((w, i) => (
                <div className="chart__col" key={w.week} title={`${w.week}: ${w.total}`}>
                  <span className="chart__count">{chartWeeks.length <= 20 ? (w.total || '') : ''}</span>
                  <div style={{ flexGrow: maxCount - w.total, minHeight: 0 }} />
                  <div className="chart__bar-stack" style={{ flexGrow: Math.max(w.total, maxCount * 0.02), minHeight: 0 }}>
                    {w.ai > 0 && <div className="chart__bar chart__bar--ai" style={{ flex: w.ai }} />}
                    <div className="chart__bar chart__bar--commands" style={{ flex: w.commands || 1 }} />
                  </div>
                  {i % labelEvery === 0 ? (
                    <span className="chart__label">{formatWeekLabel(w.week)}</span>
                  ) : (
                    <span className="chart__label" />
                  )}
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
        </div>
      )}

<div className="section" style={{ marginTop: 36 }}>
        <h2 className="section__title">Najczęściej używane komendy</h2>

        {data.top_commands.length > 0 ? (
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Komenda</th>
                  <th>Gdzie</th>
                  <th>Liczba wywołań</th>
                </tr>
              </thead>
              <tbody>
                {data.top_commands.map((c, i) => (
                  <tr key={i}>
                    <td><code>{c.full_command}</code></td>
                    <td><DiscordLocation {...c} /></td>
                    <td className="mono">{c.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card card--wide">
            <div className="empty">
              <span className="empty__icon">📈</span>
              <div className="empty__text">Brak danych o komendach.</div>
            </div>
          </div>
        )}
      </div>

      {data.recent.length > 0 && (
        <div className="section" style={{ marginTop: 36 }}>
          <h2 className="section__title">Ostatnie wywołania</h2>
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Komenda</th>
                  <th>Gdzie</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {data.recent.map((r, i) => (
                  <tr key={i}>
                    <td><code>{r.full_command}</code></td>
                    <td><DiscordLocation {...r} /></td>
                    <td className="mono">{new Date(r.created_at).toLocaleString('pl-PL')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {hasAi && data.recent_ai.length > 0 && (
        <div className="section" style={{ marginTop: 36 }}>
          <h2 className="section__title">Ostatnie wiadomości AI</h2>
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Gdzie</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {data.recent_ai.map((r, i) => (
                  <tr key={i}>
                    <td><DiscordLocation {...r} /></td>
                    <td className="mono">{new Date(r.created_at).toLocaleString('pl-PL')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </>
  )
}
