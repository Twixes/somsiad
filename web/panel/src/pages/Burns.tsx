import { useEffect, useState } from 'react'
import { getBurns, type BurnsData } from '../api'

export function Burns() {
  const [data, setData] = useState<BurnsData | null>(null)

  useEffect(() => {
    getBurns().then(setData)
  }, [])

  if (!data) return null

  return (
    <>
      <div className="section">
        <p className="section__desc">
          Spalenie to zaplanowane usunięcie wiadomości. Użyj komendy <code>spal</code> z podaniem czasu,
          np. <code>spal 5min</code> lub <code>spal 2d12h</code>, a Somsiad usunie twoją wiadomość we wskazanym momencie.
          Anulować spalenie można komendą <code>nie</code>.
        </p>
        <h2 className="section__title">Oczekujące spalenia</h2>

        {data.pending.length > 0 ? (
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Zlecono</th>
                  <th>Zaplanowano na</th>
                </tr>
              </thead>
              <tbody>
                {data.pending.map((b, i) => (
                  <tr key={i}>
                    <td className="mono">{new Date(b.requested_at).toLocaleString('pl-PL')}</td>
                    <td className="mono">{new Date(b.execute_at).toLocaleString('pl-PL')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card card--wide">
            <div className="empty">
              <span className="empty__icon">🔥</span>
              <div className="empty__text">Brak oczekujących spaleń.</div>
            </div>
          </div>
        )}
      </div>

      {data.past.length > 0 && (
        <div className="section" style={{ marginTop: 36 }}>
          <h2 className="section__title">Wykonane spalenia</h2>
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Zlecono</th>
                  <th>Wykonano</th>
                </tr>
              </thead>
              <tbody>
                {data.past.map((b, i) => (
                  <tr key={i}>
                    <td className="mono">{new Date(b.requested_at).toLocaleString('pl-PL')}</td>
                    <td className="mono">{new Date(b.execute_at).toLocaleString('pl-PL')}</td>
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
