interface Props {
  context: Record<string, unknown>
  careGaps: Array<{ type: string; severity: string; detail: string }>
}

export default function PatientSummaryCard({ context, careGaps }: Props) {
  const meds = (context.active_medications as string[]) || []
  const problems = (context.problems as Array<{ name: string }>) || []

  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius)',
      padding: '20px',
    }}>
      <h3 style={{ marginBottom: '16px' }}>Patient Summary</h3>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        <Section title="Demographics">
          <Row label="Name" value={`${context.patient_first_name} ${context.patient_last_name}`} />
          <Row label="DOB" value={context.patient_dob as string} />
          <Row label="Phone" value={context.phone_number as string} />
          <Row label="Language" value={context.language as string} />
        </Section>

        <Section title="Discharge">
          <Row label="Facility" value={context.facility_name as string} />
          <Row label="Date" value={context.discharge_date as string} />
          <Row label="Diagnosis" value={context.discharge_diagnosis as string} />
          <Row label="Disposition" value={context.discharge_disposition as string} />
          <Row label="Physician" value={context.attending_physician as string} />
        </Section>

        <Section title={`Medications (${meds.length})`}>
          {meds.length === 0 && <p style={dimStyle}>None documented</p>}
          <ul style={{ paddingLeft: '16px', fontSize: '13px' }}>
            {meds.slice(0, 8).map(m => <li key={m}>{m}</li>)}
            {meds.length > 8 && <li style={dimStyle}>...and {meds.length - 8} more</li>}
          </ul>
        </Section>

        <Section title={`Problems (${problems.length})`}>
          {problems.length === 0 && <p style={dimStyle}>None documented</p>}
          <ul style={{ paddingLeft: '16px', fontSize: '13px' }}>
            {problems.slice(0, 6).map(p => <li key={p.name}>{p.name}</li>)}
            {problems.length > 6 && <li style={dimStyle}>...and {problems.length - 6} more</li>}
          </ul>
        </Section>
      </div>

      {careGaps.length > 0 && (
        <div style={{ marginTop: '16px' }}>
          <h4 style={{ marginBottom: '8px', color: 'var(--color-danger)' }}>
            Care Gaps ({careGaps.length})
          </h4>
          {careGaps.map((g, i) => (
            <div key={i} style={{
              padding: '8px 12px',
              marginBottom: '4px',
              borderRadius: 'var(--radius)',
              background: g.severity === 'high' ? 'var(--color-danger-light)' : 'var(--color-warning-light)',
              fontSize: '13px',
            }}>
              <strong>{g.type.replace(/_/g, ' ')}</strong>: {g.detail}
            </div>
          ))}
        </div>
      )}

      {typeof context.ai_discharge_summary === 'string' && context.ai_discharge_summary && (
        <div style={{ marginTop: '16px' }}>
          <h4 style={{ marginBottom: '8px' }}>AI Discharge Summary</h4>
          <div style={{
            background: 'var(--color-bg)',
            padding: '12px',
            borderRadius: 'var(--radius)',
            fontSize: '13px',
            maxHeight: '200px',
            overflow: 'auto',
            whiteSpace: 'pre-wrap',
          }}>
            {(context.ai_discharge_summary as string).slice(0, 1500)}
            {(context.ai_discharge_summary as string).length > 1500 && '...'}
          </div>
        </div>
      )}
    </div>
  )
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h4 style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginBottom: '6px' }}>{title}</h4>
      {children}
    </div>
  )
}

function Row({ label, value }: { label: string; value: string | undefined | null }) {
  return (
    <div style={{ fontSize: '13px', marginBottom: '2px' }}>
      <span style={dimStyle}>{label}:</span> {value || 'Unknown'}
    </div>
  )
}

const dimStyle = { color: 'var(--color-text-secondary)' }
