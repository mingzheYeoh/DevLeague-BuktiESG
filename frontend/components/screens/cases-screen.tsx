'use client'

import {
  ArrowRight,
  FileSpreadsheet,
  MoreHorizontal,
  Plus,
  RefreshCw,
  Trash2,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import type { CaseStatus, CaseSummary } from '@/lib/api'
import { errorMessage } from '@/lib/api'
import { daysUntil, formatDateLabel, relativeTimeLabel } from '@/lib/format'

import { ConfirmDialog } from '../confirm-dialog'
import {
  CasePill,
  EmptyState,
  ErrorNotice,
  Loading,
  NotAvailable,
  PageTitle,
  SearchField,
  Summary,
} from '../primitives'


/**
 * `GET /api/v1/cases`.
 *
 * Columns are limited to what a Case row actually carries server-side
 * (`CaseSummary`): there is no owner and no per-case readiness on the list
 * endpoint, so neither is shown rather than being invented or fetched N+1.
 * Readiness for the open case lives on the Overview screen, which calls the
 * readiness endpoint directly.
 *
 * The list endpoint returns every case the organization owns, so nothing is
 * unreachable. Hiding them is this screen's decision, made with the toolbar
 * toggle below.
 */
export function CasesScreen({
  cases,
  loading,
  error,
  reload,
  onOpenCase,
  onNewCase,
  onDelete,
}: {
  cases: CaseSummary[]
  loading: boolean
  error: unknown
  reload: () => void
  onOpenCase: (caseId: string) => void
  onNewCase: () => void
  onDelete: (caseId: string) => Promise<void>
}) {
  const [query, setQuery] = useState('')
  const [openMenu, setOpenMenu] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<CaseSummary | null>(null)
  const [busy, setBusy] = useState(false)
  /** Row-level failures that have no dialog of their own. The delete dialog
   * shows its own error inline. */
  const [actionError, setActionError] = useState<string | null>(null)

  const visible = cases

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return visible
    return visible.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.customer_name ?? '').toLowerCase().includes(q),
    )
  }, [visible, query])

  const dueSoon = cases.filter((c) => {
    const days = daysUntil(c.deadline_at)
    return days !== null && days >= 0 && days <= 14
  }).length
  const drafts = cases.filter((c) => c.status === 'DRAFT').length
  const inReview = cases.filter((c) => c.status === 'IN_REVIEW').length
  const customerCount = new Set(
    cases.map((c) => c.customer_name).filter((name): name is string => Boolean(name)),
  ).size

  async function run(work: () => Promise<unknown>) {
    setBusy(true)
    setActionError(null)
    try {
      await work()
      return true
    } catch (err) {
      setActionError(errorMessage(err))
      return false
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <PageTitle
        eyebrow="Workspace"
        title="Response cases"
        desc="Every case stored by the API. Customer requests, evidence and deadlines."
        actions={
          <>
            <button className="secondary" type="button" onClick={reload}>
              <RefreshCw />
              Refresh
            </button>
            <button
              className="primary"
              type="button"
              data-testid="new-case-button"
              onClick={onNewCase}
            >
              <Plus />
              New case
            </button>
          </>
        }
      />

      {error ? <ErrorNotice message={errorMessage(error)} onRetry={reload} /> : null}
      {actionError ? <ErrorNotice message={actionError} /> : null}

      <div className="summary-grid">
        <Summary
          label="Cases"
          value={String(cases.length)}
          sub={customerCount ? `Across ${customerCount} named customers` : 'No customer names set'}
        />
        <Summary
          label="Due soon"
          value={String(dueSoon)}
          sub="Deadline within 14 days"
          tone="warn-text"
        />
        <Summary label="Draft" value={String(drafts)} sub="Not yet in review" />
        <Summary label="In review" value={String(inReview)} sub="Human review under way" />
      </div>

      <div className="toolbar">
        <SearchField
          placeholder="Search cases by title or customer"
          value={query}
          onChange={setQuery}
          grow
        />
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Case</th>
              <th>Customer</th>
              <th>Deadline</th>
              <th>Last updated</th>
              <th>Status</th>
              <th />
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => {
              return (
                <tr
                  key={c.id}
                  className="clickable"
                  data-testid={`case-row-${c.id}`}
                  onClick={() => onOpenCase(c.id)}
                >
                  <td>
                    <div className="cell-title">
                      <span className="file-icon">
                        <FileSpreadsheet />
                      </span>
                      <div>
                        <b>{c.title}</b>
                        <small>{c.id}</small>
                      </div>
                    </div>
                  </td>
                  <td>{c.customer_name ?? <NotAvailable title="No customer name recorded" />}</td>
                  <td>
                    <b>{formatDateLabel(c.deadline_at)}</b>
                    <small>
                      {c.deadline_at ? relativeDeadline(c.deadline_at) : 'No deadline set'}
                    </small>
                  </td>
                  <td>{relativeTimeLabel(c.updated_at)}</td>
                  <td>
                    <CasePill value={c.status} />
                  </td>
                  <td>
                    <ArrowRight />
                  </td>
                  <td>
                    <CaseRowMenu
                      row={c}
                      open={openMenu === c.id}
                      busy={busy}
                      onToggle={() => setOpenMenu((id) => (id === c.id ? null : c.id))}
                      onClose={() => setOpenMenu(null)}
                      onDelete={() => {
                        setOpenMenu(null)
                        setActionError(null)
                        setPendingDelete(c)
                      }}
                    />
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>

        {loading && cases.length === 0 ? <Loading label="Loading cases…" /> : null}

        {!loading && filtered.length === 0 ? (
          <EmptyState
            icon={<FileSpreadsheet />}
            title={emptyTitle(cases.length, query)}
          >
            {emptyBody(cases.length, query)}
          </EmptyState>
        ) : null}
      </div>

      {pendingDelete ? (
        <ConfirmDialog
          title={`Delete “${pendingDelete.title}”?`}
          confirmLabel="Delete case"
          busy={busy}
          error={actionError}
          onCancel={() => {
            setPendingDelete(null)
            setActionError(null)
          }}
          onConfirm={async () => {
            const ok = await run(() => onDelete(pendingDelete.id))
            if (ok) setPendingDelete(null)
          }}
        >
          <p>
            This permanently removes the case and everything filed under it — its questions and
            answers, every human review decision recorded against them, the uploaded documents and
            their stored files, and any actions raised.
          </p>
          <p className="confirm-emphasis">This cannot be undone.</p>
        </ConfirmDialog>
      ) : null}
    </div>
  )
}

/**
 * The per-row delete menu.
 *
 * Every handler stops propagation: the row itself is clickable and opens the
 * case, so without it, reaching for "Delete" would navigate away instead.
 */
function CaseRowMenu({
  row,
  open,
  busy,
  onToggle,
  onClose,
  onDelete,
}: {
  row: CaseSummary
  open: boolean
  busy: boolean
  onToggle: () => void
  onClose: () => void
  onDelete: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!open) return
    function onDocumentClick(event: MouseEvent) {
      if (!ref.current?.contains(event.target as Node)) onClose()
    }
    function onEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('mousedown', onDocumentClick)
    document.addEventListener('keydown', onEscape)
    return () => {
      document.removeEventListener('mousedown', onDocumentClick)
      document.removeEventListener('keydown', onEscape)
    }
  }, [open, onClose])

  return (
    <div className="row-menu" ref={ref} onClick={(e) => e.stopPropagation()}>
      <button
        className="icon-btn"
        type="button"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={`Actions for ${row.title}`}
        data-testid={`case-menu-${row.id}`}
        onClick={onToggle}
      >
        <MoreHorizontal />
      </button>

      {open ? (
        <ul className="status-dropdown-menu" role="menu">
          <li>
            <button
              type="button"
              role="menuitem"
              className="danger"
              disabled={busy}
              data-testid={`case-delete-${row.id}`}
              onClick={onDelete}
            >
              <Trash2 />
              Delete
            </button>
          </li>
        </ul>
      ) : null}
    </div>
  )
}

function statusLabel(status: string): string {
  return status.charAt(0) + status.slice(1).toLowerCase().replace(/_/g, ' ')
}

function emptyTitle(total: number, query: string): string {
  if (total === 0) return 'No cases yet'
  if (query.trim()) return 'No cases match that search'
  return 'No cases to show'
}

function emptyBody(
  total: number,
  query: string,
): string {
  if (total === 0) return 'Create a response case to start collecting evidence.'
  if (query.trim()) return 'Clear the search to see every case.'
  return 'Nothing to show with the current filters.'
}

function relativeDeadline(iso: string): string {
  const days = daysUntil(iso)
  if (days === null) return 'No deadline set'
  if (days < 0) return 'Overdue'
  if (days === 0) return 'Due today'
  return `${days} day${days === 1 ? '' : 's'} left`
}
