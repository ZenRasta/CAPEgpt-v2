import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.jsx'
import { AvatarProvider } from './context/AvatarProvider.jsx'

function Root() {
  return (
    <AvatarProvider>
      <div className="grid h-screen p-4 gap-4 grid-cols-1 md:grid-cols-[280px,1fr] lg:grid-cols-[280px,1fr,320px]">
        <aside className="hidden md:block" />
        <main className="min-w-0">
          <App />
        </main>
        <aside className="hidden lg:block" />
      </div>
    </AvatarProvider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
