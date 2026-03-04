import { useState, useCallback, useEffect } from 'react'
import { getStatus, connect } from './api/client.ts'
import type { ServiceAccount, Environment } from './api/client.ts'
import Sidebar from './components/Sidebar.tsx'
import type { Page } from './components/Sidebar.tsx'
import Toast from './components/Toast.tsx'
import type { ToastMessage } from './components/Toast.tsx'
import DashboardPage from './pages/DashboardPage.tsx'
import ProjectsPage from './pages/ProjectsPage.tsx'
import ServiceAccountsPage from './pages/ServiceAccountsPage.tsx'
import CredentialsPage from './pages/CredentialsPage.tsx'
import NotificationsPage from './pages/NotificationsPage.tsx'
import styles from './App.module.css'

type View =
  | { page: 'dashboard' }
  | { page: 'projects' }
  | { page: 'service-accounts' }
  | { page: 'notifications' }
  | { page: 'credentials'; serviceAccount: ServiceAccount }

let toastId = 0

function App() {
  const [view, setView] = useState<View>({ page: 'dashboard' })
  const [environment, setEnvironment] = useState<Environment>('sandbox')
  const [connected, setConnected] = useState(false)
  const [toasts, setToasts] = useState<ToastMessage[]>([])

  const addToast = useCallback((toast: Omit<ToastMessage, 'id'>) => {
    const id = ++toastId
    setToasts((prev) => [...prev, { ...toast, id }])
  }, [])

  const dismissToast = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  const handleNavigate = useCallback((page: Page) => {
    setView({ page })
  }, [])

  const handleViewCredentials = useCallback((sa: ServiceAccount) => {
    setView({ page: 'credentials', serviceAccount: sa })
  }, [])

  const handleEnvironmentChange = useCallback((env: Environment) => {
    setEnvironment(env)
    // Reset to dashboard when environment changes
    setView({ page: 'dashboard' })
  }, [])

  // Check connection status on mount; auto-connect if needed
  useEffect(() => {
    let cancelled = false
    async function init() {
      try {
        const status = await getStatus()
        if (cancelled) return
        setEnvironment(status.environment)
        if (status.authenticated) {
          setConnected(true)
          return
        }
        // Not connected — try to connect
        const result = await connect()
        if (cancelled) return
        setEnvironment(result.environment)
        setConnected(true)
      } catch {
        if (cancelled) return
        addToast({
          type: 'error',
          text: 'Failed to connect — check PARTICLE_CLIENT_ID and PARTICLE_CLIENT_SECRET in .env',
        })
      }
    }
    init()
    return () => { cancelled = true }
  }, [addToast])

  const activePage: Page =
    view.page === 'credentials' ? 'service-accounts' : (view.page as Page)

  if (!connected) {
    return (
      <div className={styles.layout} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--color-text-secondary)' }}>Connecting to Particle...</p>
        <Toast toasts={toasts} onDismiss={dismissToast} />
      </div>
    )
  }

  return (
    <div className={styles.layout}>
      <Sidebar
        activePage={activePage}
        environment={environment}
        onNavigate={handleNavigate}
        onEnvironmentChange={handleEnvironmentChange}
      />
      <main className={styles.main}>
        {view.page === 'dashboard' && (
          <DashboardPage onNavigate={handleNavigate} />
        )}
        {view.page === 'projects' && <ProjectsPage onToast={addToast} />}
        {view.page === 'service-accounts' && (
          <ServiceAccountsPage
            onToast={addToast}
            onViewCredentials={handleViewCredentials}
          />
        )}
        {view.page === 'notifications' && (
          <NotificationsPage onToast={addToast} />
        )}
        {view.page === 'credentials' && (
          <CredentialsPage
            serviceAccount={view.serviceAccount}
            onBack={() => setView({ page: 'service-accounts' })}
            onToast={addToast}
          />
        )}
      </main>
      <Toast toasts={toasts} onDismiss={dismissToast} />
    </div>
  )
}

export default App
