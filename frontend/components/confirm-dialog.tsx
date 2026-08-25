'use client'

import { AlertTriangle, X } from 'lucide-react'
import { useCallback, useEffect, useRef } from 'react'
import type { ReactNode } from 'react'

/**
 * A modal for an action that cannot be undone.
 *
 * Follows the same conventions as `DocumentPreview`: overlay click closes,
 * Escape closes, Tab is kept inside the dialog. Escape and the overlay click
 * both stop propagation because the callers sit on top of clickable table rows
 * — without that, dismissing the dialog would also trigger whatever is
 * underneath it.
 *
 * Confirm is what gets focus on open, not Cancel. The dialog is only ever shown
 * after the user asked for the destructive thing, and the copy states the
 * consequence in full; making them tab to the button they came for is friction
 * that teaches people to click through warnings.
 */
export function ConfirmDialog({
  title,
  confirmLabel,
  onConfirm,
  onCancel,
  busy = false,
  error = null,
  children,
}: {
  title: string
  confirmLabel: string
  onConfirm: () => void
  onCancel: () => void
  /** Disables both buttons while the request is in flight, so a double-click
   * cannot fire a second DELETE against an id the first one already removed. */
  busy?: boolean
  /** Shown in place of closing the dialog when the request is refused, so the
   * server's reason (e.g. CASE_NOT_DELETABLE) is read where the action was
   * taken rather than as a toast somewhere else. */
  error?: string | null
  children: ReactNode
}) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const confirmRef = useRef<HTMLButtonElement>(null)

  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.stopPropagation()
        if (!busy) onCancel()
        return
      }
      if (event.key !== 'Tab') return
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button:not(:disabled), [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
      )
      if (!focusable || focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    [busy, onCancel],
  )

  useEffect(() => {
    confirmRef.current?.focus()
  }, [])

  return (
    <div
      className="preview-overlay"
      onClick={(e) => {
        e.stopPropagation()
        if (!busy) onCancel()
      }}
    >
      <div
        className="confirm-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="confirm-dialog-title"
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={onKeyDown}
      >
        <header className="confirm-head">
          <span className="confirm-icon" aria-hidden="true">
            <AlertTriangle />
          </span>
          <h2 id="confirm-dialog-title">{title}</h2>
          <button
            className="icon-btn"
            type="button"
            onClick={onCancel}
            disabled={busy}
            aria-label="Cancel"
          >
            <X />
          </button>
        </header>

        <div className="confirm-body">{children}</div>

        {error ? (
          <div className="callout warning" role="alert">
            {error}
          </div>
        ) : null}

        <footer className="confirm-actions">
          <button className="secondary" type="button" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button
            className="danger"
            type="button"
            ref={confirmRef}
            onClick={onConfirm}
            disabled={busy}
            data-testid="confirm-destructive"
          >
            {busy ? 'Working…' : confirmLabel}
          </button>
        </footer>
      </div>
    </div>
  )
}
