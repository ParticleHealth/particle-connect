import { useState, useEffect, useCallback } from 'react'
import {
  listCredentials,
  createCredential,
  deleteCredential,
  serviceAccountId,
} from '../api/client.ts'
import type { Credential, NewCredential, ServiceAccount } from '../api/client.ts'
import Modal from '../components/Modal.tsx'
import CopyButton from '../components/CopyButton.tsx'
import type { ToastMessage } from '../components/Toast.tsx'
import styles from './CredentialsPage.module.css'

interface Props {
  serviceAccount: ServiceAccount
  onBack: () => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}

export default function CredentialsPage({
  serviceAccount,
  onBack,
  onToast,
}: Props) {
  const [credentials, setCredentials] = useState<Credential[]>([])
  const [loading, setLoading] = useState(true)
  const [showRotate, setShowRotate] = useState(false)
  const [newCred, setNewCred] = useState<NewCredential | null>(null)
  const [deleteTarget, setDeleteTarget] = useState<Credential | null>(null)
  const [deleting, setDeleting] = useState(false)

  const loadCredentials = useCallback(async () => {
    try {
      const data = await listCredentials(serviceAccountId(serviceAccount))
      setCredentials(data)
    } catch (err) {
      onToast({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to load credentials',
      })
    } finally {
      setLoading(false)
    }
  }, [serviceAccount.name, onToast])

  useEffect(() => {
    loadCredentials()
  }, [loadCredentials])

  const handleCreated = useCallback(
    (cred: NewCredential) => {
      setShowRotate(false)
      setNewCred(cred)
      // Add to local state since the list endpoint may not be available
      setCredentials((prev) => [
        ...prev,
        {
          id: cred.clientId,
          created_at: new Date().toISOString(),
          status: 'active',
        },
      ])
      loadCredentials()
    },
    [loadCredentials],
  )

  const handleDelete = useCallback(async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await deleteCredential(serviceAccountId(serviceAccount), deleteTarget.id)
      onToast({ type: 'success', text: 'Credential deleted' })
      setDeleteTarget(null)
      await loadCredentials()
    } catch (err) {
      onToast({
        type: 'error',
        text:
          err instanceof Error ? err.message : 'Failed to delete credential',
      })
    } finally {
      setDeleting(false)
    }
  }, [deleteTarget, serviceAccount.name, onToast, loadCredentials])

  return (
    <div className={styles.page}>
      <div className={styles.breadcrumb}>
        <button className={styles.breadcrumbLink} onClick={onBack}>
          Service Accounts
        </button>
        <span className={styles.breadcrumbSep}>/</span>
        <span>{serviceAccount.display_name || serviceAccount.name}</span>
        <span className={styles.breadcrumbSep}>/</span>
        <span className={styles.breadcrumbCurrent}>Credentials</span>
      </div>

      <div className={styles.header}>
        <h1 className={styles.heading}>Credentials</h1>
        <button
          className={styles.createButton}
          onClick={() => setShowRotate(true)}
        >
          + Create / Rotate Credentials
        </button>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Credential ID</th>
              <th>Created</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className={styles.empty}>
                  Loading...
                </td>
              </tr>
            ) : credentials.length === 0 ? (
              <tr>
                <td colSpan={4} className={styles.empty}>
                  No credentials found. Create one to get started.
                </td>
              </tr>
            ) : (
              credentials.map((c) => (
                <tr key={c.id}>
                  <td>
                    <span className={styles.credId}>{c.id}</span>
                  </td>
                  <td>
                    {c.created_at
                      ? new Date(c.created_at).toLocaleString()
                      : '--'}
                  </td>
                  <td>
                    <span
                      className={`${styles.badge} ${
                        c.status === 'active'
                          ? styles.badgeActive
                          : styles.badgeInactive
                      }`}
                    >
                      {c.status || 'active'}
                    </span>
                  </td>
                  <td>
                    <button
                      className={styles.deleteButton}
                      onClick={() => setDeleteTarget(c)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {showRotate && (
        <RotateModal
          saId={serviceAccountId(serviceAccount)}
          onClose={() => setShowRotate(false)}
          onCreated={handleCreated}
          onToast={onToast}
        />
      )}

      {newCred && (
        <SecretModal
          credential={newCred}
          onClose={() => setNewCred(null)}
        />
      )}

      {deleteTarget && (
        <Modal title="Delete Credential" onClose={() => setDeleteTarget(null)}>
          <div className={styles.confirmContent}>
            <p>
              Are you sure you want to delete credential{' '}
              <strong>{deleteTarget.id}</strong>?
            </p>
            <p className={styles.confirmWarning}>
              This action cannot be undone. Any systems using this credential
              will lose access.
            </p>
            <div className={styles.confirmActions}>
              <button
                className={styles.cancelButton}
                onClick={() => setDeleteTarget(null)}
              >
                Cancel
              </button>
              <button
                className={styles.dangerButton}
                onClick={handleDelete}
                disabled={deleting}
              >
                {deleting ? 'Deleting...' : 'Delete Credential'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}

function RotateModal({
  saId,
  onClose,
  onCreated,
  onToast,
}: {
  saId: string
  onClose: () => void
  onCreated: (cred: NewCredential) => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}) {
  const [ttlHours, setTtlHours] = useState(0)
  const [creating, setCreating] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      const cred = await createCredential(saId, ttlHours)
      onToast({ type: 'success', text: 'Credential created successfully' })
      onCreated(cred)
    } catch (err) {
      onToast({
        type: 'error',
        text:
          err instanceof Error
            ? err.message
            : 'Failed to create credential',
      })
    } finally {
      setCreating(false)
    }
  }

  return (
    <Modal title="Create / Rotate Credentials" onClose={onClose}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label}>
            Old Credential TTL: {ttlHours} hour{ttlHours !== 1 ? 's' : ''}
          </label>
          <input
            type="range"
            min={0}
            max={24}
            value={ttlHours}
            onChange={(e) => setTtlHours(Number(e.target.value))}
            className={styles.slider}
          />
          <div className={styles.sliderLabels}>
            <span>0h (immediate)</span>
            <span>24h</span>
          </div>
          <p className={styles.hint}>
            How long existing credentials remain valid after rotation. Set to 0
            for immediate revocation.
          </p>
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
            disabled={creating}
          >
            {creating ? 'Creating...' : 'Create Credential'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function SecretModal({
  credential,
  onClose,
}: {
  credential: NewCredential
  onClose: () => void
}) {
  const [confirmed, setConfirmed] = useState(false)

  return (
    <Modal title="New Credential Created" onClose={onClose} width="560px">
      <div className={styles.secretContent}>
        <div className={styles.secretWarning}>
          This secret will only be shown once. Copy it now and store it
          securely.
        </div>

        <div className={styles.secretField}>
          <label className={styles.secretLabel}>Client ID</label>
          <div className={styles.secretValueRow}>
            <code className={styles.secretValue}>{credential.clientId}</code>
            <CopyButton text={credential.clientId} />
          </div>
        </div>

        <div className={styles.secretField}>
          <label className={styles.secretLabel}>Client Secret</label>
          <div className={styles.secretValueRow}>
            <code className={styles.secretValue}>
              {credential.clientSecret}
            </code>
            <CopyButton text={credential.clientSecret} />
          </div>
        </div>

        <label className={styles.confirmCheckbox}>
          <input
            type="checkbox"
            checked={confirmed}
            onChange={(e) => setConfirmed(e.target.checked)}
          />
          I have saved these credentials securely
        </label>

        <button
          className={styles.submitButton}
          onClick={onClose}
          disabled={!confirmed}
          style={{ width: '100%' }}
        >
          I've Saved This
        </button>
      </div>
    </Modal>
  )
}
