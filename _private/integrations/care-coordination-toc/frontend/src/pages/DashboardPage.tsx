import { useState, useEffect, useCallback } from 'react'
import { listWorkflows, listPatients, createWorkflow, startWorkflow } from '../api/client.ts'
import type { Workflow, Patient } from '../api/client.ts'
import StatusBadge from '../components/StatusBadge.tsx'

interface Props {
  onSelectWorkflow: (id: string) => void
}

export default function DashboardPage({ onSelectWorkflow }: Props) {
  const [workflows, setWorkflows] = useState<Workflow[]>([])
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)

  const refresh = useCallback(async () => {
    try {
      const [wf, pt] = await Promise.all([listWorkflows(), listPatients()])
      setWorkflows(wf)
      setPatients(pt)
    } catch (e) {
      console.error('Failed to load data:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 5000)
    return () => clearInterval(interval)
  }, [refresh])

  const handleCreate = async () => {
    const p = patients[0]
    if (!p) return
    setCreating(true)
    try {
      const wf = await createWorkflow({
        patient_id: p.patient_id,
        given_name: 'Elvira',
        family_name: 'Valadez-Nucleus',
        date_of_birth: '1970-12-26',
        gender: 'FEMALE',
        postal_code: '02215',
        address_city: 'Boston',
        address_state: 'MA',
        telephone: '234-567-8910',
      })
      await startWorkflow(wf.id)
      await refresh()
    } catch (e) {
      console.error('Failed to create workflow:', e)
    } finally {
      setCreating(false)
    }
  }

  // Summary counts
  const totalActive = workflows.filter(w => !['completed', 'cancelled', 'failed'].includes(w.status)).length
  const pendingGates = workflows.filter(w => w.status.includes('gate')).length
  const completed = workflows.filter(w => w.status === 'completed').length
  const failed = workflows.filter(w => w.status === 'failed').length

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px' }}>Transitions of Care Dashboard</h1>
        <button className="btn-primary" onClick={handleCreate} disabled={creating}>
          {creating ? 'Creating...' : 'Start New Workflow'}
        </button>
      </div>

      {/* Summary cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <SummaryCard label="Active Workflows" value={totalActive} color="var(--color-primary)" />
        <SummaryCard label="Pending Gates" value={pendingGates} color="var(--color-warning)" />
        <SummaryCard label="Completed" value={completed} color="var(--color-success)" />
        <SummaryCard label="Failed" value={failed} color="var(--color-danger)" />
      </div>

      {/* Workflow table */}
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)',
        overflow: 'hidden',
      }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: 'var(--color-bg)', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
              <th style={th}>Patient</th>
              <th style={th}>Status</th>
              <th style={th}>Step</th>
              <th style={th}>Created</th>
              <th style={th}>Updated</th>
              <th style={th}>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6} style={{ ...td, textAlign: 'center', color: 'var(--color-text-secondary)' }}>Loading...</td></tr>
            ) : workflows.length === 0 ? (
              <tr><td colSpan={6} style={{ ...td, textAlign: 'center', color: 'var(--color-text-secondary)' }}>No workflows yet. Click "Start New Workflow" to begin.</td></tr>
            ) : (
              workflows.map(w => (
                <tr key={w.id} style={{ borderTop: '1px solid var(--color-border)' }}>
                  <td style={td}>{w.patient_name}</td>
                  <td style={td}><StatusBadge status={w.status} /></td>
                  <td style={td}>{w.current_step}</td>
                  <td style={td}>{new Date(w.created_at).toLocaleString()}</td>
                  <td style={td}>{new Date(w.updated_at).toLocaleString()}</td>
                  <td style={td}>
                    <button className="btn-ghost" onClick={() => onSelectWorkflow(w.id)}>
                      View
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius)',
      padding: '16px',
    }}>
      <div style={{ fontSize: '28px', fontWeight: 700, color }}>{value}</div>
      <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>{label}</div>
    </div>
  )
}

const th = { padding: '10px 12px', textAlign: 'left' as const, fontWeight: 600 }
const td = { padding: '10px 12px', fontSize: '14px' }
