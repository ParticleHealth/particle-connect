import { useState } from 'react'
import Sidebar from './components/Sidebar.tsx'
import DashboardPage from './pages/DashboardPage.tsx'
import WorkflowDetailPage from './pages/WorkflowDetailPage.tsx'

type View =
  | { page: 'dashboard' }
  | { page: 'workflow'; workflowId: string }

export default function App() {
  const [view, setView] = useState<View>({ page: 'dashboard' })

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      <Sidebar
        activePage={view.page === 'workflow' ? 'dashboard' : view.page}
        onNavigate={() => setView({ page: 'dashboard' })}
      />
      <main style={{ flex: 1, overflow: 'auto' }}>
        {view.page === 'dashboard' && (
          <DashboardPage onSelectWorkflow={(id) => setView({ page: 'workflow', workflowId: id })} />
        )}
        {view.page === 'workflow' && (
          <WorkflowDetailPage
            workflowId={view.workflowId}
            onBack={() => setView({ page: 'dashboard' })}
          />
        )}
      </main>
    </div>
  )
}
