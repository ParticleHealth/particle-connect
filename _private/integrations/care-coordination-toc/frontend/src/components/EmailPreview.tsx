interface Props {
  subject: string
  bodyHtml: string
  recipient?: string
}

export default function EmailPreview({ subject, bodyHtml, recipient }: Props) {
  return (
    <div style={{
      background: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius)',
      overflow: 'hidden',
    }}>
      <div style={{
        background: 'var(--color-bg)',
        padding: '12px 16px',
        borderBottom: '1px solid var(--color-border)',
        fontSize: '13px',
      }}>
        <div><strong>To:</strong> {recipient || 'patient@example.com'}</div>
        <div><strong>Subject:</strong> {subject}</div>
      </div>
      <div
        style={{ padding: '16px' }}
        dangerouslySetInnerHTML={{ __html: bodyHtml }}
      />
    </div>
  )
}
