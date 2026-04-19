export function Login() {
  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-logo"><a href="/">Somsiad</a></div>
        <div className="login-subtitle">Panel sterowania</div>
        <a href="/panel/auth" className="login-button">
          <svg viewBox="0 0 71 55" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M60.1 4.9A58.5 58.5 0 0045.6.5a.2.2 0 00-.2.1 41 41 0 00-1.8 3.6 54 54 0 00-16.2 0A41.8 41.8 0 0025.5.6a.2.2 0 00-.2-.1 58.4 58.4 0 00-14.4 4.4.2.2 0 00-.1.1C1.6 18-.9 30.6.3 43a.3.3 0 00.1.2 58.7 58.7 0 0017.7 9 .2.2 0 00.3-.1c1.4-1.9 2.6-3.9 3.6-6 .1-.1 0-.3-.1-.3a38.6 38.6 0 01-5.6-2.7c-.1-.1-.1-.3 0-.3l1.1-.9a.2.2 0 01.2 0 42 42 0 0035.7 0 .2.2 0 01.2 0l1.1.9c.1.1.1.3 0 .3a36.3 36.3 0 01-5.6 2.7c-.1.1-.2.2-.1.3 1.1 2.1 2.3 4.1 3.7 6a.2.2 0 00.2.1 58.5 58.5 0 0017.7-9 .3.3 0 00.1-.2c1.4-14.7-2.4-27.4-10.1-38.7a.2.2 0 00-.1-.1zM23.7 35.3c-3.4 0-6.1-3.1-6.1-6.9s2.7-6.9 6.1-6.9c3.4 0 6.2 3.1 6.1 6.9 0 3.8-2.7 6.9-6.1 6.9zm22.6 0c-3.4 0-6.1-3.1-6.1-6.9s2.7-6.9 6.1-6.9c3.4 0 6.2 3.1 6.1 6.9 0 3.8-2.7 6.9-6.1 6.9z"
              fill="currentColor"
            />
          </svg>
          Zaloguj się przez Discorda
        </a>
      </div>
      <div className="login-features">
        <div className="login-feature">
          <span className="login-feature__icon">📈</span>
          <div className="login-feature__title">Twoja aktywność w liczbach</div>
          <div className="login-feature__desc">Wykresy, trendy i rankingi – zobacz jak korzystasz z Somsiada w czasie</div>
        </div>
        <div className="login-feature">
          <span className="login-feature__icon">🍅</span>
          <div className="login-feature__title">Wszystko pod kontrolą</div>
          <div className="login-feature__desc">Przypomnienia, głosowania, spalenia – zarządzaj z jednego miejsca</div>
        </div>
        <div className="login-feature">
          <span className="login-feature__icon">⚙️</span>
          <div className="login-feature__title">Twoje ustawienia</div>
          <div className="login-feature__desc">Urodziny, widoczność na serwerach i inne preferencje – dostosuj Somsiada do siebie</div>
        </div>
        <div className="login-feature">
          <span className="login-feature__icon">🔍</span>
          <div className="login-feature__title">Pełna historia</div>
          <div className="login-feature__desc">Komendy, rozmowy z AI, zdarzenia moderacyjne – nic nie ginie</div>
        </div>
      </div>
    </div>
  )
}
