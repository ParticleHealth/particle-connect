import { useState, useEffect, useCallback } from 'react'
import type { FormEvent } from 'react'
import {
  listNotifications,
  createNotification,
  updateNotification,
  deleteNotification,
  createSignatureKey,
  deleteSignatureKey,
  notificationId,
} from '../api/client.ts'
import type { Notification, SignatureKey } from '../api/client.ts'
import Modal from '../components/Modal.tsx'
import CopyButton from '../components/CopyButton.tsx'
import type { ToastMessage } from '../components/Toast.tsx'
import styles from './NotificationsPage.module.css'

interface Props {
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}

const NOTIFICATION_TYPES = [
  { value: 'query', label: 'Query' },
  { value: 'patient', label: 'Patient' },
  { value: 'networkalert', label: 'Network Alert' },
  { value: 'hl7v2', label: 'HL7v2' },
]

export default function NotificationsPage({ onToast }: Props) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [toggling, setToggling] = useState<string | null>(null)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [sigkeyTarget, setSigkeyTarget] = useState<Notification | null>(null)

  const loadNotifications = useCallback(async () => {
    try {
      const data = await listNotifications()
      setNotifications(data)
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to load notifications',
      })
    } finally {
      setLoading(false)
    }
  }, [onToast])

  useEffect(() => {
    loadNotifications()
  }, [loadNotifications])

  const handleToggleActive = useCallback(
    async (n: Notification) => {
      const id = notificationId(n)
      setToggling(id)
      try {
        await updateNotification(id, { active: !n.active })
        onToast({
          type: 'success',
          text: `"${n.display_name}" ${n.active ? 'deactivated' : 'activated'}`,
        })
        await loadNotifications()
      } catch (err) {
        onToast({
          type: 'error',
          text: err instanceof Error ? err.message : 'Failed to update notification',
        })
      } finally {
        setToggling(null)
      }
    },
    [onToast, loadNotifications],
  )

  const handleDelete = useCallback(
    async (n: Notification) => {
      const id = notificationId(n)
      setDeleting(id)
      try {
        await deleteNotification(id)
        onToast({
          type: 'success',
          text: `"${n.display_name}" deleted`,
        })
        await loadNotifications()
      } catch (err) {
        onToast({
          type: 'error',
          text: err instanceof Error ? err.message : 'Failed to delete notification',
        })
      } finally {
        setDeleting(null)
      }
    },
    [onToast, loadNotifications],
  )

  const handleCreated = useCallback(() => {
    setShowCreate(false)
    loadNotifications()
  }, [loadNotifications])

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.heading}>Notifications</h1>
        <button
          className={styles.createButton}
          onClick={() => setShowCreate(true)}
        >
          + Create Notification
        </button>
      </div>

      <div className={styles.tableWrapper}>
        <table className={styles.table}>
          <thead>
            <tr>
              <th>Name</th>
              <th>Type</th>
              <th>Callback URL</th>
              <th>Active</th>
              <th>Created</th>
              <th>Updated</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={7} className={styles.empty}>
                  Loading...
                </td>
              </tr>
            ) : notifications.length === 0 ? (
              <tr>
                <td colSpan={7} className={styles.empty}>
                  No webhook notifications configured. Create one to get started.
                </td>
              </tr>
            ) : (
              notifications.map((n) => {
                const id = notificationId(n)
                return (
                  <tr key={n.name}>
                    <td className={styles.nameCell}>
                      <span className={styles.notifName}>
                        {n.display_name}
                      </span>
                      <span className={styles.notifId}>{n.name}</span>
                    </td>
                    <td>
                      <span className={styles.typeBadge}>
                        {n.notification_type}
                      </span>
                    </td>
                    <td className={styles.urlCell}>{n.callback_url}</td>
                    <td>
                      <span
                        className={`${styles.badge} ${
                          n.active ? styles.badgeActive : styles.badgeInactive
                        }`}
                      >
                        {n.active ? 'ACTIVE' : 'INACTIVE'}
                      </span>
                    </td>
                    <td className={styles.dateCell}>
                      {n.create_time
                        ? new Date(n.create_time).toLocaleDateString()
                        : '--'}
                    </td>
                    <td className={styles.dateCell}>
                      {n.update_time
                        ? new Date(n.update_time).toLocaleDateString()
                        : '--'}
                    </td>
                    <td className={styles.actions}>
                      <button
                        className={styles.sigkeyButton}
                        onClick={() => setSigkeyTarget(n)}
                      >
                        Sig Key
                      </button>
                      <button
                        className={`${styles.toggleButton} ${
                          n.active ? styles.deactivate : styles.activate
                        }`}
                        onClick={() => handleToggleActive(n)}
                        disabled={toggling === id}
                      >
                        {toggling === id
                          ? '...'
                          : n.active
                            ? 'Deactivate'
                            : 'Activate'}
                      </button>
                      <button
                        className={styles.deleteButton}
                        onClick={() => handleDelete(n)}
                        disabled={deleting === id}
                      >
                        {deleting === id ? '...' : 'Delete'}
                      </button>
                    </td>
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {showCreate && (
        <CreateNotificationModal
          onClose={() => setShowCreate(false)}
          onCreated={handleCreated}
          onToast={onToast}
        />
      )}

      {sigkeyTarget && (
        <SignatureKeyModal
          notification={sigkeyTarget}
          onClose={() => setSigkeyTarget(null)}
          onToast={onToast}
        />
      )}
    </div>
  )
}

function CreateNotificationModal({
  onClose,
  onCreated,
  onToast,
}: {
  onClose: () => void
  onCreated: () => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}) {
  const [displayName, setDisplayName] = useState('')
  const [notificationType, setNotificationType] = useState('query')
  const [callbackUrl, setCallbackUrl] = useState('')
  const [active, setActive] = useState(true)
  const [saving, setSaving] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setSaving(true)
    try {
      await createNotification({
        display_name: displayName,
        notification_type: notificationType,
        callback_url: callbackUrl,
        active,
      })
      onToast({
        type: 'success',
        text: `Notification "${displayName}" created`,
      })
      onCreated()
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create notification',
      })
    } finally {
      setSaving(false)
    }
  }

  return (
    <Modal title="Create Notification" onClose={onClose}>
      <form className={styles.form} onSubmit={handleSubmit}>
        <div className={styles.field}>
          <label className={styles.label}>Display Name</label>
          <input
            className={styles.input}
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="My Webhook"
            required
            autoFocus
          />
        </div>
        <div className={styles.fieldRow}>
          <div className={styles.field}>
            <label className={styles.label}>Notification Type</label>
            <select
              className={styles.input}
              value={notificationType}
              onChange={(e) => setNotificationType(e.target.value)}
            >
              {NOTIFICATION_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.field}>
            <label className={styles.label}>Active</label>
            <select
              className={styles.input}
              value={active ? 'true' : 'false'}
              onChange={(e) => setActive(e.target.value === 'true')}
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </select>
          </div>
        </div>
        <div className={styles.field}>
          <label className={styles.label}>Callback URL</label>
          <input
            className={styles.input}
            type="url"
            value={callbackUrl}
            onChange={(e) => setCallbackUrl(e.target.value)}
            placeholder="https://example.com/webhook"
            required
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
            {saving ? 'Creating...' : 'Create Notification'}
          </button>
        </div>
      </form>
    </Modal>
  )
}

function generateKey(length: number): string {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
  const arr = new Uint8Array(length)
  crypto.getRandomValues(arr)
  return Array.from(arr, (b) => chars[b % chars.length]).join('')
}

function SignatureKeyModal({
  notification,
  onClose,
  onToast,
}: {
  notification: Notification
  onClose: () => void
  onToast: (toast: Omit<ToastMessage, 'id'>) => void
}) {
  const [keyValue, setKeyValue] = useState(() => generateKey(48))
  const [saving, setSaving] = useState(false)
  const [createdKey, setCreatedKey] = useState<SignatureKey | null>(null)
  const [deleting, setDeleting] = useState(false)

  const nId = notificationId(notification)

  const handleGenerate = () => {
    setKeyValue(generateKey(48))
  }

  const handleCreate = async (e: FormEvent) => {
    e.preventDefault()
    if (keyValue.length < 24 || keyValue.length > 80) {
      onToast({ type: 'error', text: 'Signature key must be between 24 and 80 characters' })
      return
    }
    setSaving(true)
    try {
      const key = await createSignatureKey(nId, keyValue)
      setCreatedKey(key)
      onToast({ type: 'success', text: 'Signature key created' })
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to create signature key',
      })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!createdKey) return
    const keyId = createdKey.name.split('/').pop() || ''
    setDeleting(true)
    try {
      await deleteSignatureKey(nId, keyId)
      onToast({ type: 'success', text: 'Signature key deleted' })
      setCreatedKey(null)
      setKeyValue(generateKey(48))
    } catch (err) {
      onToast({
        type: 'error',
        text: err instanceof Error ? err.message : 'Failed to delete signature key',
      })
    } finally {
      setDeleting(false)
    }
  }

  return (
    <Modal
      title={`Signature Key: ${notification.display_name}`}
      onClose={onClose}
      width="560px"
    >
      {createdKey ? (
        <div className={styles.sigkeyResult}>
          <div className={styles.sigkeyWarning}>
            Save this key now. You'll need it to verify webhook signatures.
          </div>
          <div className={styles.sigkeyField}>
            <label className={styles.sigkeyLabel}>Signature Key</label>
            <div className={styles.sigkeyValueRow}>
              <code className={styles.sigkeyValue}>{createdKey.signature_key}</code>
              <CopyButton text={createdKey.signature_key} />
            </div>
          </div>
          <div className={styles.sigkeyField}>
            <label className={styles.sigkeyLabel}>Key ID</label>
            <div className={styles.sigkeyValueRow}>
              <code className={styles.sigkeyValue}>{createdKey.name}</code>
              <CopyButton text={createdKey.name} />
            </div>
          </div>
          <div className={styles.formActions}>
            <button
              className={styles.deleteButton}
              onClick={handleDelete}
              disabled={deleting}
            >
              {deleting ? 'Deleting...' : 'Delete Key'}
            </button>
            <button className={styles.submitButton} onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      ) : (
        <form className={styles.form} onSubmit={handleCreate}>
          <div className={styles.field}>
            <label className={styles.label}>
              Signature Key ({keyValue.length} chars, must be 24–80)
            </label>
            <div className={styles.sigkeyInputRow}>
              <input
                className={styles.input}
                value={keyValue}
                onChange={(e) => setKeyValue(e.target.value)}
                minLength={24}
                maxLength={80}
                required
                style={{ fontFamily: 'var(--font-mono)', fontSize: '0.85rem' }}
              />
              <button
                type="button"
                className={styles.generateButton}
                onClick={handleGenerate}
              >
                Generate
              </button>
            </div>
            <p className={styles.sigkeyHint}>
              A random key has been generated. Click Generate for a new one, or enter your own.
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
              disabled={saving}
            >
              {saving ? 'Creating...' : 'Create Signature Key'}
            </button>
          </div>
        </form>
      )}
    </Modal>
  )
}
