import { CSSProperties } from 'react'

const STEPS = [
  { key: 'data', label: 'Data', statuses: ['data_gathering'] },
  { key: 'gate_1', label: 'Gate 1', statuses: ['gate_1_pending'] },
  { key: 'call', label: 'Call', statuses: ['calling'] },
  { key: 'gate_2', label: 'Gate 2', statuses: ['gate_2_pending'] },
  { key: 'email', label: 'Email', statuses: ['emailing'] },
  { key: 'gate_3', label: 'Gate 3', statuses: ['gate_3_pending'] },
  { key: 'done', label: 'Done', statuses: ['completed'] },
]

const STATUS_ORDER = [
  'pending', 'data_gathering', 'gate_1_pending', 'calling',
  'gate_2_pending', 'emailing', 'gate_3_pending', 'completed',
]

function getStepState(stepStatuses: string[], workflowStatus: string): 'done' | 'active' | 'pending' | 'failed' {
  if (workflowStatus === 'failed' || workflowStatus === 'cancelled') {
    const currentIdx = STATUS_ORDER.indexOf(workflowStatus)
    const stepIdx = STATUS_ORDER.indexOf(stepStatuses[0])
    if (stepIdx < currentIdx) return 'done'
    if (stepStatuses.includes(workflowStatus)) return 'failed'
    return 'pending'
  }
  if (stepStatuses.includes(workflowStatus)) return 'active'
  const currentIdx = STATUS_ORDER.indexOf(workflowStatus)
  const stepIdx = STATUS_ORDER.indexOf(stepStatuses[0])
  if (currentIdx > stepIdx) return 'done'
  return 'pending'
}

const container: CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '4px',
  padding: '20px 0',
}

const nodeBase: CSSProperties = {
  width: '36px',
  height: '36px',
  borderRadius: '50%',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  fontSize: '11px',
  fontWeight: 600,
  flexShrink: 0,
}

const lineBase: CSSProperties = {
  flex: 1,
  height: '2px',
  minWidth: '16px',
}

const colors = {
  done:    { bg: 'var(--color-success)', color: 'white', line: 'var(--color-success)' },
  active:  { bg: 'var(--color-primary)', color: 'white', line: 'var(--color-border)' },
  pending: { bg: 'var(--color-border)',  color: 'var(--color-text-secondary)', line: 'var(--color-border)' },
  failed:  { bg: 'var(--color-danger)',  color: 'white', line: 'var(--color-border)' },
}

export default function WorkflowTimeline({ status }: { status: string }) {
  return (
    <div style={container}>
      {STEPS.map((step, i) => {
        const state = getStepState(step.statuses, status)
        const c = colors[state]
        const isGate = step.key.startsWith('gate')
        return (
          <div key={step.key} style={{ display: 'flex', alignItems: 'center', flex: i < STEPS.length - 1 ? 1 : 0 }}>
            <div style={{ textAlign: 'center' }}>
              <div style={{
                ...nodeBase,
                background: c.bg,
                color: c.color,
                borderRadius: isGate ? '6px' : '50%',
                width: isGate ? '40px' : '36px',
              }}>
                {state === 'done' ? '\u2713' : (i + 1)}
              </div>
              <div style={{ fontSize: '10px', color: 'var(--color-text-secondary)', marginTop: '4px', whiteSpace: 'nowrap' }}>
                {step.label}
              </div>
            </div>
            {i < STEPS.length - 1 && (
              <div style={{ ...lineBase, background: state === 'done' ? c.line : 'var(--color-border)' }} />
            )}
          </div>
        )
      })}
    </div>
  )
}
