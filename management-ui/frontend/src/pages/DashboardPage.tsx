import { useState, useEffect } from 'react'
import { listProjects, listServiceAccounts } from '../api/client.ts'
import type { Page } from '../components/Sidebar.tsx'
import styles from './DashboardPage.module.css'

interface Props {
  onNavigate: (page: Page) => void
}

export default function DashboardPage({ onNavigate }: Props) {
  const [projectCount, setProjectCount] = useState<number | null>(null)
  const [saCount, setSaCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [projects, accounts] = await Promise.all([
          listProjects(),
          listServiceAccounts(),
        ])
        if (!cancelled) {
          setProjectCount(projects.length)
          setSaCount(accounts.length)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load data')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Dashboard</h1>

      {error && <div className={styles.error}>{error}</div>}

      <div className={styles.cards}>
        <div className={styles.card}>
          <div className={styles.cardIcon}>{'\u25cb'}</div>
          <div className={styles.cardContent}>
            <div className={styles.cardValue}>
              {loading ? '--' : projectCount}
            </div>
            <div className={styles.cardLabel}>Projects</div>
          </div>
          <button
            className={styles.cardAction}
            onClick={() => onNavigate('projects')}
          >
            View All
          </button>
        </div>

        <div className={styles.card}>
          <div className={styles.cardIcon}>{'\u26bf'}</div>
          <div className={styles.cardContent}>
            <div className={styles.cardValue}>
              {loading ? '--' : saCount}
            </div>
            <div className={styles.cardLabel}>Service Accounts</div>
          </div>
          <button
            className={styles.cardAction}
            onClick={() => onNavigate('service-accounts')}
          >
            View All
          </button>
        </div>
      </div>

      <div className={styles.quickActions}>
        <h2 className={styles.sectionTitle}>Quick Actions</h2>
        <div className={styles.actionGrid}>
          <button
            className={styles.actionButton}
            onClick={() => onNavigate('projects')}
          >
            <span className={styles.actionIcon}>+</span>
            Create Project
          </button>
          <button
            className={styles.actionButton}
            onClick={() => onNavigate('service-accounts')}
          >
            <span className={styles.actionIcon}>+</span>
            Create Service Account
          </button>
        </div>
      </div>
    </div>
  )
}
