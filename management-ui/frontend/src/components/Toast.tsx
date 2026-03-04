import { useEffect } from 'react'
import styles from './Toast.module.css'

export interface ToastMessage {
  id: number
  type: 'success' | 'error'
  text: string
}

interface Props {
  toasts: ToastMessage[]
  onDismiss: (id: number) => void
}

export default function Toast({ toasts, onDismiss }: Props) {
  return (
    <div className={styles.container}>
      {toasts.map((t) => (
        <ToastItem key={t.id} toast={t} onDismiss={onDismiss} />
      ))}
    </div>
  )
}

function ToastItem({
  toast,
  onDismiss,
}: {
  toast: ToastMessage
  onDismiss: (id: number) => void
}) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(toast.id), 4000)
    return () => clearTimeout(timer)
  }, [toast.id, onDismiss])

  return (
    <div className={`${styles.toast} ${styles[toast.type]}`}>
      <span className={styles.icon}>
        {toast.type === 'success' ? '\u2713' : '\u2717'}
      </span>
      <span className={styles.text}>{toast.text}</span>
      <button
        className={styles.close}
        onClick={() => onDismiss(toast.id)}
        aria-label="Dismiss"
      >
        \u00d7
      </button>
    </div>
  )
}
