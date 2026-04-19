import { useEffect, useState } from 'react'
import { getPolls, type PollsData } from '../api'
import { DiscordLocation } from '../DiscordLocation'

export function Polls() {
  const [data, setData] = useState<PollsData | null>(null)

  useEffect(() => {
    getPolls().then(setData)
  }, [])

  if (!data) return null

  return (
    <>
      <div className="section">
        <p className="section__desc">
          Głosowania tworzy się na Discordzie komendą <code>głosowanie</code>. Domyślnie jest to głosowanie za/przeciw.
          Możesz też podać opcje literowe (np. <code>głosowanie 1h A. Tak B. Nie C. Może</code>) lub skalę liczbową.
          Opcjonalnie podaj czas zakończenia jako pierwszy argument.
        </p>
        <h2 className="section__title">Aktywne głosowania</h2>

        {data.active.length > 0 ? (
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sprawa</th>
                  <th>Gdzie</th>
                  <th>Typ</th>
                  <th>Rozpoczęto</th>
                  <th>Zakończenie</th>
                </tr>
              </thead>
              <tbody>
                {data.active.map((p, i) => (
                  <tr key={i}>
                    <td>{p.matter}</td>
                    <td><DiscordLocation {...p} /></td>
                    <td>{p.type}</td>
                    <td className="mono">{new Date(p.commenced_at).toLocaleString('pl-PL')}</td>
                    <td className="mono">{new Date(p.conclude_at).toLocaleString('pl-PL')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="card card--wide">
            <div className="empty">
              <span className="empty__icon">🗳</span>
              <div className="empty__text">Brak aktywnych głosowań.</div>
            </div>
          </div>
        )}
      </div>

      {data.past.length > 0 && (
        <div className="section" style={{ marginTop: 36 }}>
          <h2 className="section__title">Zakończone głosowania</h2>
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sprawa</th>
                  <th>Gdzie</th>
                  <th>Typ</th>
                  <th>Rozpoczęto</th>
                  <th>Zakończono</th>
                </tr>
              </thead>
              <tbody>
                {data.past.map((p, i) => (
                  <tr key={i}>
                    <td>{p.matter}</td>
                    <td><DiscordLocation {...p} /></td>
                    <td>{p.type}</td>
                    <td className="mono">{new Date(p.commenced_at).toLocaleString('pl-PL')}</td>
                    <td className="mono">{new Date(p.conclude_at).toLocaleString('pl-PL')}</td>
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
