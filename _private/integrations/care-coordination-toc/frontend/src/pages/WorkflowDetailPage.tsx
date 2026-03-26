import { useState, useEffect, useCallback } from 'react'
import { getWorkflow, decideGate, retryWorkflow, cancelWorkflow } from '../api/client.ts'
import type { WorkflowDetail } from '../api/client.ts'
import WorkflowTimeline from '../components/WorkflowTimeline.tsx'
import StatusBadge from '../components/StatusBadge.tsx'
import GateControl from '../components/GateControl.tsx'
import PatientSummaryCard from '../components/PatientSummaryCard.tsx'
import EmailPreview from '../components/EmailPreview.tsx'

interface Props {
  workflowId: string
  onBack: () => void
}

export default function WorkflowDetailPage({ workflowId, onBack }: Props) {
  const [wf, setWf] = useState<WorkflowDetail | null>(null)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const data = await getWorkflow(workflowId)
      setWf(data)
    } catch (e) {
      setError(String(e))
    }
  }, [workflowId])

  useEffect(() => {
    refresh()
    const interval = setInterval(refresh, 3000)
    return () => clearInterval(interval)
  }, [refresh])

  if (error) return <div style={{ padding: '24px', color: 'var(--color-danger)' }}>Error: {error}</div>
  if (!wf) return <div style={{ padding: '24px', color: 'var(--color-text-secondary)' }}>Loading...</div>

  const handleGateDecide = async (gateNumber: number, decision: string, notes: string) => {
    await decideGate(workflowId, gateNumber, decision, notes)
    await refresh()
  }

  const handleRetry = async () => {
    await retryWorkflow(workflowId)
    await refresh()
  }

  const handleCancel = async () => {
    await cancelWorkflow(workflowId)
    await refresh()
  }

  const ctx = wf.patient_context
  const call = wf.call_result
  const email = wf.email_record

  return (
    <div style={{ padding: '24px', maxWidth: '1000px' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        <button className="btn-ghost" onClick={onBack}>&larr; Back</button>
        <h1 style={{ fontSize: '20px', flex: 1 }}>{wf.patient_name}</h1>
        <StatusBadge status={wf.status} />
        {wf.status === 'failed' && <button className="btn-warning" onClick={handleRetry}>Retry</button>}
        {!['completed', 'cancelled', 'failed'].includes(wf.status) && (
          <button className="btn-ghost" onClick={handleCancel}>Cancel</button>
        )}
      </div>

      {/* Timeline */}
      <div style={{
        background: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius)',
        padding: '0 20px',
        marginBottom: '20px',
      }}>
        <WorkflowTimeline status={wf.status} />
      </div>

      {/* Error message */}
      {wf.error_message && (
        <div style={{
          background: 'var(--color-danger-light)',
          border: '1px solid var(--color-danger)',
          borderRadius: 'var(--radius)',
          padding: '12px 16px',
          marginBottom: '16px',
          fontSize: '13px',
        }}>
          <strong>Error:</strong> {wf.error_message}
        </div>
      )}

      {/* Gate 1 control */}
      <GateControl gateNumber={1} status={wf.status} onDecide={(d, n) => handleGateDecide(1, d, n)} />

      {/* Patient Context Panel */}
      {ctx && (
        <div style={{ marginTop: '20px' }}>
          <PatientSummaryCard context={ctx.context} careGaps={ctx.care_gaps} />
        </div>
      )}

      {/* Gate 2 control */}
      <GateControl gateNumber={2} status={wf.status} onDecide={(d, n) => handleGateDecide(2, d, n)} />

      {/* Call Result Panel */}
      {call && (
        <div style={{
          background: 'var(--color-surface)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius)',
          padding: '20px',
          marginTop: '20px',
        }}>
          <h3 style={{ marginBottom: '12px' }}>Call Result</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div>
              <span style={dimStyle}>Call ID:</span> {call.call_id || 'N/A'}
            </div>
            <div>
              <span style={dimStyle}>Duration:</span> {call.duration_ms ? `${(call.duration_ms / 1000).toFixed(1)}s` : 'N/A'}
            </div>
            <div>
              <span style={dimStyle}>Disposition:</span>{' '}
              <strong>{call.disposition_action?.replace(/_/g, ' ') || 'None'}</strong>
            </div>
            <div>
              <span style={dimStyle}>Status:</span> {call.status}
            </div>
          </div>
          {call.disposition_params && (
            <div style={{
              background: 'var(--color-success-light)',
              padding: '12px',
              borderRadius: 'var(--radius)',
              fontSize: '13px',
              marginBottom: '12px',
            }}>
              <strong>Disposition Details:</strong>
              <pre style={{ margin: '4px 0 0', whiteSpace: 'pre-wrap' }}>
                {JSON.stringify(call.disposition_params, null, 2)}
              </pre>
            </div>
          )}
          {call.transcript && (
            <div>
              <h4 style={{ marginBottom: '8px' }}>Transcript</h4>
              <div style={{
                background: 'var(--color-bg)',
                padding: '12px',
                borderRadius: 'var(--radius)',
                fontSize: '13px',
                maxHeight: '300px',
                overflow: 'auto',
                whiteSpace: 'pre-wrap',
              }}>
                {call.transcript}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Gate 3 control */}
      <GateControl gateNumber={3} status={wf.status} onDecide={(d, n) => handleGateDecide(3, d, n)} />

      {/* Email Panel */}
      {email && email.body_html && (
        <div style={{ marginTop: '20px' }}>
          <h3 style={{ marginBottom: '12px' }}>Follow-up Email</h3>
          <EmailPreview
            subject={email.subject || ''}
            bodyHtml={email.body_html}
            recipient={email.recipient_email || undefined}
          />
        </div>
      )}

      {/* Event Log */}
      {wf.events && wf.events.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h3 style={{ marginBottom: '12px' }}>Event Log</h3>
          <div style={{
            background: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius)',
            overflow: 'hidden',
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--color-bg)', fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  <th style={th}>Time</th>
                  <th style={th}>Event</th>
                  <th style={th}>Details</th>
                </tr>
              </thead>
              <tbody>
                {wf.events.map(ev => (
                  <tr key={ev.id} style={{ borderTop: '1px solid var(--color-border)' }}>
                    <td style={tdSmall}>{new Date(ev.created_at).toLocaleTimeString()}</td>
                    <td style={tdSmall}>{ev.event_type}</td>
                    <td style={tdSmall}>{ev.event_data ? JSON.stringify(ev.event_data) : ''}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Gate decisions summary */}
      {wf.gate_decisions && wf.gate_decisions.length > 0 && (
        <div style={{ marginTop: '24px' }}>
          <h3 style={{ marginBottom: '12px' }}>Gate Decisions</h3>
          {wf.gate_decisions.map(g => (
            <div key={g.gate_number} style={{
              padding: '8px 12px',
              marginBottom: '4px',
              borderRadius: 'var(--radius)',
              background: g.decision === 'approved' ? 'var(--color-success-light)' :
                          g.decision === 'rejected' ? 'var(--color-warning-light)' :
                          'var(--color-danger-light)',
              fontSize: '13px',
            }}>
              <strong>Gate {g.gate_number}:</strong> {g.decision}
              {g.coordinator_notes && <span> — {g.coordinator_notes}</span>}
              {g.decided_at && <span style={dimStyle}> ({new Date(g.decided_at).toLocaleString()})</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

const dimStyle = { color: 'var(--color-text-secondary)', fontSize: '13px' }
const th = { padding: '8px 12px', textAlign: 'left' as const, fontWeight: 600 }
const tdSmall = { padding: '6px 12px', fontSize: '12px' }
