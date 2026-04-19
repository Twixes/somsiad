import { useEffect, useState } from 'react'
import { getCommands, type CommandsData } from '../api'

export function Commands() {
  const [data, setData] = useState<CommandsData | null>(null)

  useEffect(() => {
    getCommands().then(setData)
  }, [])

  if (!data) return null

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
          <div className="card__label">Wszystkie wywołania</div>
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
      </div>

      <div className="section">
        <h2 className="section__title">Najczęściej używane komendy</h2>

        {data.top_commands.length > 0 ? (
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Komenda</th>
                  <th>Liczba wywołań</th>
                </tr>
              </thead>
              <tbody>
                {data.top_commands.map((c, i) => (
                  <tr key={i}>
                    <td><code>{c.full_command}</code></td>
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
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {data.recent.map((r, i) => (
                  <tr key={i}>
                    <td><code>{r.full_command}</code></td>
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
