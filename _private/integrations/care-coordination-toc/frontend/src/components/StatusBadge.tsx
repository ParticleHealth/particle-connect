import { CSSProperties } from 'react'

const STATUS_STYLES: Record<string, { bg: string; color: string; label: string }> = {
  pending:         { bg: 'var(--color-info-light)',    color: 'var(--color-info)',    label: 'Pending' },
  data_gathering:  { bg: 'var(--color-info-light)',    color: 'var(--color-info)',    label: 'Gathering Data' },
  gate_1_pending:  { bg: 'var(--color-warning-light)', color: 'var(--color-warning)', label: 'Gate 1: Review' },
  calling:         { bg: 'var(--color-info-light)',    color: 'var(--color-info)',    label: 'Calling Patient' },
  gate_2_pending:  { bg: 'var(--color-warning-light)', color: 'var(--color-warning)', label: 'Gate 2: Review' },
  emailing:        { bg: 'var(--color-info-light)',    color: 'var(--color-info)',    label: 'Sending Email' },
  gate_3_pending:  { bg: 'var(--color-warning-light)', color: 'var(--color-warning)', label: 'Gate 3: Review' },
  completed:       { bg: 'var(--color-success-light)', color: 'var(--color-success)', label: 'Completed' },
  failed:          { bg: 'var(--color-danger-light)',  color: 'var(--color-danger)',  label: 'Failed' },
  cancelled:       { bg: 'var(--color-border)',        color: 'var(--color-text-secondary)', label: 'Cancelled' },
}

export default function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLES[status] || STATUS_STYLES.pending
  const style: CSSProperties = {
    display: 'inline-block',
    padding: '2px 10px',
    borderRadius: '12px',
    fontSize: '12px',
    fontWeight: 600,
    background: s.bg,
    color: s.color,
  }
  return <span style={style}>{s.label}</span>
}
