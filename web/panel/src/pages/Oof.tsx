import { useEffect, useState } from 'react'
import { getOof, type OofData } from '../api'

export function Oof() {
  const [data, setData] = useState<OofData | null>(null)

  useEffect(() => {
    getOof().then(setData)
  }, [])

  if (!data) return null

  return (
    <>
      <div className="section">
        <p className="section__desc">
          Napisz <code>oof</code> na Discordzie, a Somsiad zliczy twoje oofnięcie. Sprawdź ile razy oofnąłeś
          komendą <code>oof ile</code>, a ranking serwera komendą <code>oof ranking</code>.
        </p>
      </div>

      <div className="cards">
        <div className="card">
          <span className="card__icon">💨</span>
          <div className="card__label">Łącznie oofnięć</div>
          <div className="card__value">{data.total_oofs}</div>
        </div>
        <div className="card">
          <span className="card__icon">🖥</span>
          <div className="card__label">Serwerów</div>
          <div className="card__value">{data.server_count}</div>
        </div>
      </div>

      <div className="section">
        <h2 className="section__title">Oofnięcia na serwerach</h2>

        {data.per_server.length > 0 ? (
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Serwer</th>
                  <th>Oofnięć</th>
                </tr>
              </thead>
              <tbody>
                {data.per_server.map((s, i) => (
                  <tr key={i}>
                    <td>{s.server_name}</td>
                    <td className="mono">{s.oofs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card card--wide">
            <div className="empty">
              <span className="empty__icon">💨</span>
              <div className="empty__text">Nie oofnąłeś jeszcze ani razu. Napisz <code>oof</code> na Discordzie!</div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}
