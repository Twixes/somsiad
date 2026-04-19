import { useEffect, useState } from 'react'
import { getBirthday, updateBirthday, deleteBirthday, hideBirthday, type BirthdayData } from '../api'

export function Birthday() {
  const [data, setData] = useState<BirthdayData | null>(null)
  const [day, setDay] = useState(1)
  const [month, setMonth] = useState(1)
  const [year, setYear] = useState('')
  const [flash, setFlash] = useState<{ type: string; message: string } | null>(null)

  const loadData = () => {
    getBirthday().then((d) => {
      setData(d)
      if (d.birthday) {
        setDay(d.birthday.day)
        setMonth(d.birthday.month)
        setYear(d.birthday.year != null ? String(d.birthday.year) : '')
      }
    })
  }

  useEffect(() => {
    loadData()
  }, [])

  if (!data) return null

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault()
    const result = await updateBirthday(day, month, year)
    if (result.error) {
      setFlash({ type: 'error', message: result.error })
    } else {
      setFlash({ type: 'success', message: result.message || 'Zapisano.' })
      loadData()
    }
  }

  const handleDelete = async () => {
    const result = await deleteBirthday()
    if (result.error) {
      setFlash({ type: 'error', message: result.error })
    } else {
      setFlash({ type: 'success', message: result.message || 'Usunieto.' })
      setYear('')
      loadData()
    }
  }

  const handleHide = async (serverId: number) => {
    const result = await hideBirthday(serverId)
    if (result.error) {
      setFlash({ type: 'error', message: result.error })
    } else {
      setFlash({ type: 'success', message: result.message || 'Utajniono.' })
      loadData()
    }
  }

  return (
    <div className="section">
      <h2 className="section__title">Twoja data urodzin</h2>
      <p className="section__desc">
        Ustaw swoją datę urodzin, aby inni mogli ci składać życzenia na serwerach Discorda.
        Na Discordzie możesz to też zrobić komendą <code>urodziny ustaw 15.03.1999</code>.
        Upublicznianie daty na poszczególnych serwerach odbywa się komendą{' '}
        <code>urodziny upublicznij</code>, a sprawdzenie czyichś urodzin komendą <code>urodziny @użytkownik</code>.
      </p>

      {flash && <div className={`flash flash--${flash.type}`}>{flash.message}</div>}

      <div className="card card--wide">
        <form onSubmit={handleSave}>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label" htmlFor="day">Dzień</label>
              <select className="form-select" id="day" value={day} onChange={(e) => setDay(Number(e.target.value))}>
                {Array.from({ length: 31 }, (_, i) => i + 1).map((d) => (
                  <option key={d} value={d}>{d}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="month">Miesiąc</label>
              <select className="form-select" id="month" value={month} onChange={(e) => setMonth(Number(e.target.value))}>
                {data.months.map(([m, name]) => (
                  <option key={m} value={m}>{name}</option>
                ))}
              </select>
            </div>
            <div className="form-group">
              <label className="form-label" htmlFor="year">
                Rok{' '}
                <span style={{ color: 'var(--text-muted)', textTransform: 'none', letterSpacing: 0 }}>
                  (opcjonalnie)
                </span>
              </label>
              <input
                className="form-input"
                type="number"
                id="year"
                min={1901}
                max={data.current_year}
                placeholder="—"
                value={year}
                onChange={(e) => setYear(e.target.value)}
              />
            </div>
            <button type="submit" className="btn btn--primary">Zapisz</button>
          </div>
        </form>
      </div>

      {data.birthday && (
        <div style={{ marginTop: 12 }}>
          <button type="button" className="btn btn--danger" onClick={handleDelete}>
            Usuń datę urodzin
          </button>
        </div>
      )}

      {data.public_server_count != null && (
        <div className="card card--wide" style={{ marginTop: 24 }}>
          <span className="card__icon">📖</span>
          <div className="card__label">Widoczność</div>
          <div className="card__value" style={{ fontSize: '1rem' }}>
            {data.public_server_count === 0
              ? 'Twoja data urodzin nie jest publiczna na żadnym serwerze.'
              : data.public_server_count === 1
                ? 'Twoja data urodzin jest publiczna na 1 serwerze.'
                : `Twoja data urodzin jest publiczna na ${data.public_server_count} serwerach.`}
          </div>
          <div className="card__sub">
            Zarządzaj widocznością na poszczególnych serwerach za pomocą komend{' '}
            <code>urodziny upublicznij</code> i <code>urodziny utajnij</code>.
          </div>
        </div>
      )}

      {data.public_servers.length > 0 && (
        <>
          <h2 className="section__title" style={{ marginTop: 36 }}>Publiczność na serwerach</h2>
          <div className="card card--wide">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Serwer</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {data.public_servers.map((s) => (
                  <tr key={s.server_id}>
                    <td>{s.server_name}</td>
                    <td>
                      <button
                        type="button"
                        className="btn btn--danger btn--small"
                        onClick={() => handleHide(s.server_id)}
                      >
                        Utajnij
                      </button>
                    </td>
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
