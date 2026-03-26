import { useState } from 'react'

interface Props {
  gateNumber: number
  status: string
  onDecide: (decision: string, notes: string) => Promise<void>
}

export default function GateControl({ gateNumber, status, onDecide }: Props) {
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)

  if (status !== `gate_${gateNumber}_pending`) {
    return null
  }

  const handle = async (decision: string) => {
    setLoading(true)
    try {
      await onDecide(decision, notes)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{
      background: 'var(--color-warning-light)',
      border: '1px solid var(--color-warning)',
      borderRadius: 'var(--radius)',
      padding: '16px',
      marginTop: '16px',
    }}>
      <h4 style={{ marginBottom: '8px' }}>Gate {gateNumber} — Coordinator Review</h4>
      <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '12px' }}>
        {gateNumber === 1 && 'Review patient data and care gaps before placing the call.'}
        {gateNumber === 2 && 'Review call transcript and disposition before sending email.'}
        {gateNumber === 3 && 'Review email and close the case or escalate.'}
      </p>
      <textarea
        value={notes}
        onChange={e => setNotes(e.target.value)}
        placeholder="Coordinator notes (optional)"
        style={{
          width: '100%',
          minHeight: '60px',
          padding: '8px',
          borderRadius: 'var(--radius)',
          border: '1px solid var(--color-border)',
          fontFamily: 'inherit',
          fontSize: '13px',
          marginBottom: '12px',
          resize: 'vertical',
        }}
      />
      <div style={{ display: 'flex', gap: '8px' }}>
        <button className="btn-success" disabled={loading} onClick={() => handle('approved')}>
          Approve
        </button>
        <button className="btn-warning" disabled={loading} onClick={() => handle('rejected')}>
          Reject
        </button>
        <button className="btn-danger" disabled={loading} onClick={() => handle('escalated')}>
          Escalate
        </button>
      </div>
    </div>
  )
}
