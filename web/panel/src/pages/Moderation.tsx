import { useEffect, useState } from 'react'
import { getModeration, type ModerationData } from '../api'

export function Moderation() {
  const [data, setData] = useState<ModerationData | null>(null)

  useEffect(() => {
    getModeration().then(setData)
  }, [])

  if (!data) return null

  return (
    <>
      {data.type_counts.length > 0 && (
        <div className="cards">
          {data.type_counts.map((tc, i) => (
            <div className="card" key={i}>
              <span className="card__icon">{tc.icon}</span>
              <div className="card__label">{tc.label}</div>
              <div className="card__value">{tc.count}</div>
            </div>
          ))}
        </div>
      )}

      <div className="section">
        <p className="section__desc">
          Kartoteka rejestruje zdarzenia moderacyjne na serwerach: ostrzeżenia (<code>ostrzeż</code>),
          wyrzucenia (<code>wyrzuć</code>), bany (<code>zbanuj</code>), przebaczenia (<code>przebacz</code>),
          a także dołączenia i opuszczenia. Swoją kartotekę na serwerze możesz sprawdzić komendą <code>kartoteka</code>.
        </p>
        <h2 className="section__title">Zdarzenia</h2>

        {data.events.length > 0 ? (
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Typ</th>
                  <th>Szczegóły</th>
                  <th>Data</th>
                </tr>
              </thead>
              <tbody>
                {data.events.map((e, i) => (
                  <tr key={i}>
                    <td>{e.type_icon} {e.type_label}</td>
                    <td>{e.details || '—'}</td>
                    <td className="mono">{new Date(e.occurred_at).toLocaleString('pl-PL')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card card--wide">
            <div className="empty">
              <span className="empty__icon">📂</span>
              <div className="empty__text">Brak zdarzeń w kartotece.</div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
