import { useState, useEffect, useCallback } from 'react'
import type { FormEvent } from 'react'
import {
  listServiceAccounts,
  createServiceAccount,
  listProjects,
  getPolicy,
  setPolicy,
  serviceAccountId,
  projectId,
} from '../api/client.ts'
import type {
  ServiceAccount,
  Project,
  Policy,
  PolicyBinding,
} from '../api/client.ts'
import Modal from '../components/Modal.tsx'
import type { ToastMessage } from '../components/Toast.tsx'
import styles from './ServiceAccountsPage.module.css'

interface Props {
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
  onViewCredentials: (sa: ServiceAccount) => void
}

export default function ServiceAccountsPage({
  onToast,
  onViewCredentials,
}: Props) {
  const [accounts, setAccounts] = useState<ServiceAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [policyTarget, setPolicyTarget] = useState<ServiceAccount | null>(null)
  const [viewPolicyTarget, setViewPolicyTarget] =
    useState<ServiceAccount | null>(null)
  const [viewPolicyData, setViewPolicyData] = useState<Policy | null>(null)
  const [viewPolicyLoading, setViewPolicyLoading] = useState(false)

  const loadAccounts = useCallback(async () => {
    try {
      const data = await listServiceAccounts()
      setAccounts(data)
    } catch (err) {
      onToast({
        type: 'error',
        text:
          err instanceof Error
            ? err.message
            : 'Failed to load service accounts',
      })
    } finally {
      setLoading(false)
    }
  }, [onToast])

  useEffect(() => {
    loadAccounts()
  }, [loadAccounts])

  const handleCreated = useCallback(() => {
    setShowCreate(false)
    loadAccounts()
  }, [loadAccounts])

  const handleViewPolicy = useCallback(
    async (sa: ServiceAccount) => {
      setViewPolicyTarget(sa)
      setViewPolicyLoading(true)
      setViewPolicyData(null)
      try {
        const policy = await getPolicy(serviceAccountId(sa))
        setViewPolicyData(policy)
      } catch (err) {
        onToast({
          type: 'error',
          text:
            err instanceof Error ? err.message : 'Failed to load policy',
        })
        setViewPolicyTarget(null)
      } finally {
        setViewPolicyLoading(false)
      }
    },
    [onToast],
  )

  const handlePolicySaved = useCallback(() => {
    setPolicyTarget(null)
    loadAccounts()
  }, [loadAccounts])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.heading}>Service Accounts</h1>
        <button
          className={styles.createButton}
          onClick={() => setShowCreate(true)}
        >
          + Create Service Account
        </button>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Name / ID</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={3} className={styles.empty}>
                  Loading...
                </td>
              </tr>
            ) : accounts.length === 0 ? (
              <tr>
                <td colSpan={3} className={styles.empty}>
                  No service accounts found. Create one to get started.
                </td>
              </tr>
            ) : (
              accounts.map((sa) => (
                <tr key={sa.name}>
                  <td className={styles.nameCell}>
                    <span className={styles.saName}>
                      {sa.display_name || 'Unnamed'}
                    </span>
                    <span className={styles.saId}>{sa.name}</span>
                  </td>
                  <td>
                    {sa.create_time
                      ? new Date(sa.create_time).toLocaleDateString()
                      : '--'}
                  </td>
                  <td className={styles.actions}>
                    <button
                      className={styles.actionButton}
                      onClick={() => setPolicyTarget(sa)}
                    >
                      Set Policy
                    </button>
                    <button
                      className={styles.actionButton}
                      onClick={() => handleViewPolicy(sa)}
                    >
                      View Policy
                    </button>
                    <button
                      className={styles.actionButtonPrimary}
                      onClick={() => onViewCredentials(sa)}
                    >
                      Credentials
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {policyTarget && (
        <SetPolicyModal
          serviceAccount={policyTarget}
          onClose={() => setPolicyTarget(null)}
          onSaved={handlePolicySaved}
          onToast={onToast}
        />
      )}

      {viewPolicyTarget && (
        <Modal
          title={`Policy: ${viewPolicyTarget.display_name || viewPolicyTarget.name}`}
          onClose={() => setViewPolicyTarget(null)}
        >
          {viewPolicyLoading ? (
            <p className={styles.policyLoading}>Loading policy...</p>
          ) : viewPolicyData &&
            viewPolicyData.bindings &&
            viewPolicyData.bindings.length > 0 ? (
            <div className={styles.policyView}>
              {viewPolicyData.bindings.map((b, i) => (
                <div key={i} className={styles.bindingCard}>
                  <div className={styles.bindingRole}>
                    <span className={styles.bindingLabel}>Role:</span>
                    {b.role}
                  </div>
                  <div className={styles.bindingResources}>
                    <span className={styles.bindingLabel}>Resources:</span>
                    <ul className={styles.resourceList}>
                      {b.resources.map((r, j) => (
                        <li key={j} className={styles.resourceItem}>
                          {r}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className={styles.policyEmpty}>
              No policy bindings configured.
            </p>
          )}
        </Modal>
      )}

      {showCreate && (
        <CreateServiceAccountModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
          onToast={onToast}
        />
      )}
    </div>
  )
}

function CreateServiceAccountModal({
  onClose,
  onCreated,
  onToast,
}: {
  onClose: () => void
  onCreated: () => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}) {
  const [displayName, setDisplayName] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      const sa = await createServiceAccount(displayName)
      onToast({
        type: 'success',
        text: `Service account "${sa.display_name || sa.name}" created`,
      })
      onCreated()
    } catch (err) {
      onToast({
        type: 'error',
        text:
          err instanceof Error
            ? err.message
            : 'Failed to create service account',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="Create Service Account" onClose={onClose}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label}>Display Name</label>
          <input
            className={styles.select}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="My Service Account"
            required
            autoFocus
          />
        </div>
        <div className={styles.formActions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={saving}
          >
            {saving ? 'Creating...' : 'Create'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function SetPolicyModal({
  serviceAccount,
  onClose,
  onSaved,
  onToast,
}: {
  serviceAccount: ServiceAccount
  onClose: () => void
  onSaved: () => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}) {
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedRole, setSelectedRole] = useState('roles/project.owner')
  const [selectedProjects, setSelectedProjects] = useState<string[]>([])
  const [saving, setSaving] = useState(false)
  const [loadingProjects, setLoadingProjects] = useState(true)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await listProjects()
        if (!cancelled) setProjects(data)
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoadingProjects(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [])

  const toggleProject = (id: string) => {
    setSelectedProjects((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id],
    )
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (selectedProjects.length === 0) {
      onToast({ type: 'error', text: 'Select at least one project' })
      return
    }
    setSaving(true)
    const bindings: PolicyBinding[] = [
      {
        role: selectedRole,
        resources: selectedProjects.map((id) => `projects/${id}`),
      },
    ]
    try {
      await setPolicy(serviceAccountId(serviceAccount), bindings)
      onToast({ type: 'success', text: 'Policy updated successfully' })
      onSaved()
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to set policy',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal
      title={`Set Policy: ${serviceAccount.display_name || serviceAccount.name}`}
      onClose={onClose}
      width="560px"
    >
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label}>Role</label>
          <select
            className={styles.select}
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
          >
            <option value="roles/project.owner">Project Owner</option>
            <option value="roles/project.viewer">Project Viewer</option>
          </select>
        </div>

        <div className={styles.field}>
          <label className={styles.label}>Assign Projects</label>
          {loadingProjects ? (
            <p className={styles.policyLoading}>Loading projects...</p>
          ) : projects.length === 0 ? (
            <p className={styles.policyEmpty}>
              No projects available. Create a project first.
            </p>
          ) : (
            <div className={styles.checkboxList}>
              {projects.map((p) => (
                <label key={p.name} className={styles.checkboxItem}>
                  <input
                    type="checkbox"
                    checked={selectedProjects.includes(projectId(p))}
                    onChange={() => toggleProject(projectId(p))}
                  />
                  <span>{p.display_name}</span>
                  <span className={styles.checkboxId}>{p.name}</span>
                </label>
              ))}
            </div>
          )}
        </div>

        <div className={styles.formActions}>
          <button
            type="button"
            className={styles.cancelButton}
            onClick={onClose}
          >
            Cancel
          </button>
          <button
            type="submit"
            className={styles.submitButton}
            disabled={saving || selectedProjects.length === 0}
          >
            {saving ? 'Saving...' : 'Save Policy'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
