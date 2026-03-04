import { useState } from 'react'
import { switchEnvironment } from '../api/client.ts'
import type { Environment } from '../api/client.ts'
import styles from './Sidebar.module.css'

export type Page = 'dashboard' | 'projects' | 'service-accounts' | 'notifications'

interface Props {
  activePage: Page
  environment: Environment
  onNavigate: (page: Page) => void
  onEnvironmentChange: (env: Environment) => void
}

const NAV_ITEMS: { page: Page; label: string; icon: string }[] = [
  { page: 'dashboard', label: 'Dashboard', icon: '\u25a6' },
  { page: 'projects', label: 'Projects', icon: '\u25cb' },
  { page: 'service-accounts', label: 'Service Accounts', icon: '\u26bf' },
  { page: 'notifications', label: 'Notifications', icon: '\u2709' },
]

export default function Sidebar({ activePage, environment, onNavigate, onEnvironmentChange }: Props) {
  const [switching, setSwitching] = useState(false)

  async function handleSwitch(env: Environment) {
    if (env === environment || switching) return
    setSwitching(true)
    try {
      const result = await switchEnvironment(env)
      onEnvironmentChange(result.environment)
    } catch {
      // stay on current environment
    } finally {
      setSwitching(false)
    }
  }

  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <span className={styles.logo}>P</span>
        <span className={styles.brandText}>Particle Console</span>
      </div>

      <div className={styles.envToggle}>
        <button
          className={`${styles.envButton} ${environment === 'sandbox' ? styles.envActive : ''}`}
          onClick={() => handleSwitch('sandbox')}
          disabled={switching}
        >
          Sandbox
        </button>
        <button
          className={`${styles.envButton} ${environment === 'production' ? styles.envActive : ''}`}
          onClick={() => handleSwitch('production')}
          disabled={switching}
        >
          Production
        </button>
      </div>

      <nav className={styles.nav}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.page}
            className={`${styles.navItem} ${
              activePage === item.page ? styles.active : ''
            }`}
            onClick={() => onNavigate(item.page)}
          >
            <span className={styles.navIcon}>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
