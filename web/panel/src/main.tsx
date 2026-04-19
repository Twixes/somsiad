import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import posthog from 'posthog-js'
import { PostHogProvider } from 'posthog-js/react'
import { App } from './App'
import './panel.css'

const posthogKey = import.meta.env.POSTHOG_API_KEY as string | undefined
const posthogHost = import.meta.env.POSTHOG_HOST as string | undefined

if (posthogKey) {
  posthog.init(posthogKey, {
    api_host: posthogHost || 'https://us.i.posthog.com',
    capture_pageview: false, // We capture manually on route changes
  })
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <PostHogProvider client={posthog}>
      <BrowserRouter basename="/panel">
        <App />
      </BrowserRouter>
    </PostHogProvider>
  </StrictMode>
)
