import { useEffect, useState } from 'react'
import { getReminders, deleteReminder, type RemindersData } from '../api'
import { DiscordLocation } from '../DiscordLocation'

export function Reminders() {
  const [data, setData] = useState<RemindersData | null>(null)

  const loadData = () => {
    getReminders().then(setData)
  }

  useEffect(() => {
    loadData()
  }, [])

  if (!data) return null

  const handleCancel = async (id: number) => {
    await deleteReminder(id)
    loadData()
  }

  return (
    <div className="section">
      <h2 className="section__title">Oczekujące przypomnienia</h2>
      <p className="section__desc">
        Przypomnienia ustawione komendą <code>przypomnij</code>, które jeszcze nie zostały zrealizowane.
        Użyj np. <code>przypomnij 5min Piekarnik</code> lub <code>przypomnij 2d12h Premiera filmu</code> na Discordzie.
      </p>

      {data.pending.length > 0 ? (
        <div className="card card--wide">
          <table className="data-table">
            <thead>
              <tr>
                <th>Treść</th>
                <th>Gdzie</th>
                <th>Kiedy</th>
                <th>Ustawiono</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.pending.map((r) => (
                <tr key={r.id}>
                  <td>{r.content}</td>
                  <td><DiscordLocation {...r} /></td>
                  <td className="mono">{new Date(r.execute_at).toLocaleString('pl-PL')}</td>
                  <td className="mono">{new Date(r.requested_at).toLocaleString('pl-PL')}</td>
                  <td>
                    <button
                      type="button"
                      className="btn btn--danger btn--small"
                      onClick={() => handleCancel(r.id)}
                    >
                      Anuluj
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card card--wide">
          <div className="empty">
            <span className="empty__icon">🍅</span>
            <div className="empty__text">
              Brak oczekujących przypomnień. Ustaw nowe komendą <code>przypomnij</code> na Discordzie.
            </div>
          </div>
        </div>
      )}

      {data.past.length > 0 && (
        <>
          <h2 className="section__title" style={{ marginTop: 36 }}>Ostatnio zrealizowane</h2>
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Treść</th>
                  <th>Gdzie</th>
                  <th>Zrealizowano</th>
                </tr>
              </thead>
              <tbody>
                {data.past.map((r, i) => (
                  <tr key={i}>
                    <td>{r.content}</td>
                    <td><DiscordLocation {...r} /></td>
                    <td className="mono">{new Date(r.execute_at).toLocaleString('pl-PL')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}
