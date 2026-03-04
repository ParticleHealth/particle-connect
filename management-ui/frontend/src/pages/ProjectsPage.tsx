import { useState, useEffect, useCallback } from 'react'
import type { FormEvent } from 'react'
import {
  listProjects,
  createProject,
  updateProjectState,
  projectId,
} from '../api/client.ts'
import type { Project } from '../api/client.ts'
import Modal from '../components/Modal.tsx'
import type { ToastMessage } from '../components/Toast.tsx'
import styles from './ProjectsPage.module.css'

interface Props {
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}

export default function ProjectsPage({ onToast }: Props) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [toggling, setToggling] = useState<string | null>(null)

  const loadProjects = useCallback(async () => {
    try {
      const data = await listProjects()
      setProjects(data)
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to load projects',
      })
    } finally {
      setLoading(false)
    }
  }, [onToast])

  useEffect(() => {
    loadProjects()
  }, [loadProjects])

  const handleToggle = useCallback(
    async (project: Project) => {
      const newState =
        project.state === 'STATE_ACTIVE' ? 'STATE_INACTIVE' : 'STATE_ACTIVE'
      const id = projectId(project)
      setToggling(id)
      try {
        await updateProjectState(id, newState)
        onToast({
          type: 'success',
          text: `Project "${project.display_name}" set to ${newState}`,
        })
        await loadProjects()
      } catch (err) {
        onToast({
          type: 'error',
          text: err instanceof Error ? err.message : 'Failed to update project',
        })
      } finally {
        setToggling(null)
      }
    },
    [onToast, loadProjects],
  )

  const handleCreated = useCallback(() => {
    setShowCreate(false)
    loadProjects()
  }, [loadProjects])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.heading}>Projects</h1>
        <button
          className={styles.createButton}
          onClick={() => setShowCreate(true)}
        >
          + Create Project
        </button>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Name</th>
              <th>NPI</th>
              <th>NPI Type</th>
              <th>OID</th>
              <th>State</th>
              <th>CommonWell Type</th>
              <th>Epic Approval</th>
              <th>Location</th>
              <th>Created</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={11} className={styles.empty}>
                  Loading...
                </td>
              </tr>
            ) : projects.length === 0 ? (
              <tr>
                <td colSpan={11} className={styles.empty}>
                  No projects found. Create one to get started.
                </td>
              </tr>
            ) : (
              projects.map((p) => (
                <tr key={p.name}>
                  <td className={styles.nameCell}>
                    <span className={styles.projectName}>
                      {p.display_name}
                    </span>
                    <span className={styles.projectId}>{p.name}</span>
                  </td>
                  <td>{p.npi}</td>
                  <td>{p.npi_type || '--'}</td>
                  <td className={styles.oidCell}>{p.oid || '--'}</td>
                  <td>
                    <span
                      className={`${styles.badge} ${
                        p.state === 'STATE_ACTIVE'
                          ? styles.badgeActive
                          : styles.badgeInactive
                      }`}
                    >
                      {p.state.replace('STATE_', '')}
                    </span>
                  </td>
                  <td>
                    <span className={styles.enumValue}>
                      {p.commonwell_type
                        ? p.commonwell_type
                            .replace('COMMONWELL_TYPE_', '')
                            .replace(/_/g, ' ')
                            .toLowerCase()
                            .replace(/\b\w/g, (c) => c.toUpperCase())
                        : '--'}
                    </span>
                  </td>
                  <td>
                    <span
                      className={`${styles.badge} ${
                        p.epic_approval_status === 'APPROVED'
                          ? styles.badgeActive
                          : styles.badgeInactive
                      }`}
                    >
                      {p.epic_approval_status
                        ? p.epic_approval_status.replace(/_/g, ' ')
                        : '--'}
                    </span>
                  </td>
                  <td>
                    {p.address
                      ? `${p.address.city}, ${p.address.state}`
                      : '--'}
                  </td>
                  <td className={styles.dateCell}>
                    {p.create_time
                      ? new Date(p.create_time).toLocaleDateString()
                      : '--'}
                  </td>
                  <td className={styles.dateCell}>
                    {p.update_time
                      ? new Date(p.update_time).toLocaleDateString()
                      : '--'}
                  </td>
                  <td>
                    <button
                      className={`${styles.toggleButton} ${
                        p.state === 'STATE_ACTIVE'
                          ? styles.deactivate
                          : styles.activate
                      }`}
                      onClick={() => handleToggle(p)}
                      disabled={toggling === projectId(p)}
                    >
                      {toggling === projectId(p)
                        ? '...'
                        : p.state === 'STATE_ACTIVE'
                          ? 'Deactivate'
                          : 'Activate'}
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <CreateProjectModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
          onToast={onToast}
        />
      )}
    </div>
  )
}

function CreateProjectModal({
  onClose,
  onCreated,
  onToast,
}: {
  onClose: () => void
  onCreated: () => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}) {
  const [displayName, setDisplayName] = useState('')
  const [npi, setNpi] = useState('')
  const [projectState, setProjectState] = useState('STATE_ACTIVE')
  const [commonwellType, setCommonwellType] = useState('COMMONWELL_TYPE_POSTACUTECARE')
  const [line1, setLine1] = useState('')
  const [city, setCity] = useState('')
  const [state, setState] = useState('')
  const [postalCode, setPostalCode] = useState('')
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createProject({
        display_name: displayName,
        npi,
        state: projectState,
        commonwell_type: commonwellType,
        address: { line1, city, state, postal_code: postalCode },
      })
      onToast({ type: 'success', text: `Project "${displayName}" created` })
      onCreated()
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create project',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="Create Project" onClose={onClose}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label}>Project Name</label>
          <input
            className={styles.input}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="My Project"
            required
            autoFocus
          />
        </div>
        <div className={styles.field}>
          <label className={styles.label}>NPI</label>
          <input
            className={styles.input}
            value={npi}
            onChange={(e) => setNpi(e.target.value)}
            placeholder="1234567890"
            required
          />
        </div>
        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label className={styles.label}>Project State</label>
            <select
              className={styles.input}
              value={projectState}
              onChange={(e) => setProjectState(e.target.value)}
            >
              <option value="STATE_ACTIVE">Active</option>
              <option value="STATE_INACTIVE">Inactive</option>
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label}>CommonWell Type</label>
            <select
              className={styles.input}
              value={commonwellType}
              onChange={(e) => setCommonwellType(e.target.value)}
            >
              <option value="COMMONWELL_TYPE_POSTACUTECARE">Post Acute Care</option>
              <option value="COMMONWELL_TYPE_ACUTECARE">Acute Care</option>
            </select>
          </div>
        </div>
        <div className={styles.field}>
          <label className={styles.label}>Address</label>
          <input
            className={styles.input}
            value={line1}
            onChange={(e) => setLine1(e.target.value)}
            placeholder="123 Main St"
            required
          />
        </div>
        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label className={styles.label}>City</label>
            <input
              className={styles.input}
              value={city}
              onChange={(e) => setCity(e.target.value)}
              placeholder="Springfield"
              required
            />
          </div>
          <div className={styles.fieldSmall}>
            <label className={styles.label}>State</label>
            <input
              className={styles.input}
              value={state}
              onChange={(e) => setState(e.target.value)}
              placeholder="IL"
              maxLength={2}
              required
            />
          </div>
          <div className={styles.fieldSmall}>
            <label className={styles.label}>ZIP</label>
            <input
              className={styles.input}
              value={postalCode}
              onChange={(e) => setPostalCode(e.target.value)}
              placeholder="62704"
              required
            />
          </div>
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
            {saving ? 'Creating...' : 'Create Project'}
          </button>
        </div>
      </form>
    </Modal>
  )
}
