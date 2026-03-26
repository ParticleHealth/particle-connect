export type Page = 'dashboard' | 'workflow'

interface Props {
  activePage: Page
  onNavigate: (page: Page) => void
}

export default function Sidebar({ activePage, onNavigate }: Props) {
  return (
    <aside style={{
      width: '220px',
      background: 'var(--color-surface)',
      borderRight: '1px solid var(--color-border)',
      padding: '20px 0',
      display: 'flex',
      flexDirection: 'column',
      minHeight: '100vh',
    }}>
      <div style={{ padding: '0 16px 20px', borderBottom: '1px solid var(--color-border)' }}>
        <h2 style={{ fontSize: '16px', color: 'var(--color-primary)' }}>ToC Workflow</h2>
        <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>Transitions of Care</p>
      </div>
      <nav style={{ padding: '12px 8px', flex: 1 }}>
        <NavItem
          label="Dashboard"
          active={activePage === 'dashboard'}
          onClick={() => onNavigate('dashboard')}
        />
      </nav>
      <div style={{ padding: '12px 16px', fontSize: '11px', color: 'var(--color-text-secondary)' }}>
        Particle Connect Demo
      </div>
    </aside>
  )
}

function NavItem({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        display: 'block',
        width: '100%',
        textAlign: 'left',
        padding: '8px 12px',
        borderRadius: 'var(--radius)',
        background: active ? 'var(--color-primary-light)' : 'transparent',
        color: active ? 'var(--color-primary)' : 'var(--color-text)',
        fontWeight: active ? 600 : 400,
        border: 'none',
        fontSize: '14px',
      }}
    >
      {label}
    </button>
  )
}
