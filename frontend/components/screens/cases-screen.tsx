'use client'

import {
  Archive,
  ArchiveRestore,
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
 * Mirror of `CASE_DELETABLE_FROM` in `backend/app/enums.py`.
 *
 * Deliberately an allow-list, the same shape as the server's, rather than a
 * list of statuses that block deletion. The two will drift — they are edited in
 * different repositories' worth of code — and this shape drifts safely: a
 * status added server-side and not added here renders as blocked, which is
 * what the endpoint does anyway. A block-list would render Delete as available
 * and let the user find out on the 409.
 */
const DELETABLE_FROM: readonly CaseStatus[] = ['DRAFT', 'ARCHIVED']

/**
 * Which retirement controls a case row offers.
 *
 * The server is the authority here, not this function: `DELETE /cases/{id}` is
 * gated on `CASE_DELETABLE_FROM` and refuses with 409 `CASE_NOT_DELETABLE`
 * regardless of what the browser rendered. This mirror exists only so the UI
 * can explain the rule up front instead of letting the user discover it by
 * being refused.
 */
function retirementControls(c: CaseSummary): {
  canArchive: boolean
  canRestore: boolean
  /** `null` means deletable. A string is the reason it is not, shown to the
   * user on the disabled menu item. */
  deleteBlockedReason: string | null
} {
  return {
    // Allowed from every status except ARCHIVED, matching the endpoint —
    // including PROCESSING, so a case whose parse died halfway can still be
    // filed away. Offering it on an already-archived case would only produce
    // 409 CASE_ALREADY_ARCHIVED.
    canArchive: c.status !== 'ARCHIVED',
    canRestore: c.status === 'ARCHIVED',
    // The server's refusal is required to name the way through rather than
    // just say no (test_case_retirement.py asserts "archive" appears in it).
    // This carries the same obligation before the click instead of after it.
    deleteBlockedReason: DELETABLE_FROM.includes(c.status)
      ? null
      : 'This case holds evidence and review decisions. Archive it first — archived cases can be deleted.',
  }
}

/**
 * `GET /api/v1/cases`.
 *
 * Columns are limited to what a Case row actually carries server-side
 * (`CaseSummary`): there is no owner and no per-case readiness on the list
 * endpoint, so neither is shown rather than being invented or fetched N+1.
 * Readiness for the open case lives on the Overview screen, which calls the
 * readiness endpoint directly.
 *
 * The list endpoint returns archived cases too — deliberately, so nothing is
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
  onArchive,
  onUnarchive,
  onDelete,
}: {
  cases: CaseSummary[]
  loading: boolean
  error: unknown
  reload: () => void
  onOpenCase: (caseId: string) => void
  onNewCase: () => void
  onArchive: (caseId: string) => Promise<CaseSummary>
  onUnarchive: (caseId: string) => Promise<CaseSummary>
  onDelete: (caseId: string) => Promise<void>
}) {
  const [query, setQuery] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [openMenu, setOpenMenu] = useState<string | null>(null)
  const [pendingDelete, setPendingDelete] = useState<CaseSummary | null>(null)
  const [busy, setBusy] = useState(false)
  /** Failures from archive/unarchive, which have no dialog of their own. The
   * delete dialog shows its own error inline. */
  const [actionError, setActionError] = useState<string | null>(null)

  const archived = useMemo(() => cases.filter((c) => c.status === 'ARCHIVED'), [cases])
  const active = useMemo(() => cases.filter((c) => c.status !== 'ARCHIVED'), [cases])

  const visible = showArchived ? cases : active

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return visible
    return visible.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.customer_name ?? '').toLowerCase().includes(q),
    )
  }, [visible, query])

  // The summary tiles count live work only. Counting archived cases as "Cases"
  // or "Draft" would report a backlog the user has already dealt with.
  const dueSoon = active.filter((c) => {
    const days = daysUntil(c.deadline_at)
    return days !== null && days >= 0 && days <= 14
  }).length
  const drafts = active.filter((c) => c.status === 'DRAFT').length
  const inReview = active.filter((c) => c.status === 'IN_REVIEW').length
  const customerCount = new Set(
    active.map((c) => c.customer_name).filter((name): name is string => Boolean(name)),
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
        {/* All four tiles count `active`, and the label says so. "Cases 1"
            beside a "Show archived 1" toggle invites the reader to add them
            together; the tile counts what the table below is showing. */}
        <Summary
          label="Active cases"
          value={String(active.length)}
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
        <label className="toggle-field">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(e) => setShowArchived(e.target.checked)}
            data-testid="show-archived-toggle"
          />
          Show archived
          <span className="toggle-count">{archived.length}</span>
        </label>
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
              const isArchived = c.status === 'ARCHIVED'
              return (
                <tr
                  key={c.id}
                  className={isArchived ? 'clickable is-archived' : 'clickable'}
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
                  <td>
                    {isArchived && c.archived_at ? (
                      <>
                        <b>{relativeTimeLabel(c.archived_at)}</b>
                        <small>Archived</small>
                      </>
                    ) : (
                      relativeTimeLabel(c.updated_at)
                    )}
                  </td>
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
                      onArchive={async () => {
                        setOpenMenu(null)
                        await run(() => onArchive(c.id))
                      }}
                      onUnarchive={async () => {
                        setOpenMenu(null)
                        await run(() => onUnarchive(c.id))
                      }}
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
            title={emptyTitle(cases.length, visible.length, query)}
          >
            {emptyBody(cases.length, visible.length, query, archived.length)}
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
 * The per-row archive / restore / delete menu.
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
  onArchive,
  onUnarchive,
  onDelete,
}: {
  row: CaseSummary
  open: boolean
  busy: boolean
  onToggle: () => void
  onClose: () => void
  onArchive: () => void
  onUnarchive: () => void
  onDelete: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const hintId = `delete-hint-${row.id}`
  const { canArchive, canRestore, deleteBlockedReason } = retirementControls(row)

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
          {canArchive ? (
            <li>
              <button type="button" role="menuitem" disabled={busy} onClick={onArchive}>
                <Archive />
                Archive
              </button>
            </li>
          ) : null}

          {canRestore ? (
            <li>
              <button type="button" role="menuitem" disabled={busy} onClick={onUnarchive}>
                <ArchiveRestore />
                {/* Naming the target is the whole reason the server keeps
                    `status_before_archive`; an unlabelled "Restore" would throw
                    that away at the last step. */}
                Restore to {statusLabel(row.status_before_archive ?? 'DRAFT')}
              </button>
            </li>
          ) : null}

          <li>
            {/* No `title` here. A button's accessible name falls back to its
                `title`, so a tooltip carrying the whole refusal sentence
                replaces the word "Delete" in the accessibility tree — the user
                who most needs the control named is told only why it is off.
                The reason is visible text below, referenced as a description,
                which also makes it reachable by keyboard and touch. */}
            <button
              type="button"
              role="menuitem"
              className="danger"
              disabled={busy || deleteBlockedReason !== null}
              aria-describedby={deleteBlockedReason ? hintId : undefined}
              data-testid={`case-delete-${row.id}`}
              onClick={onDelete}
            >
              <Trash2 />
              Delete
            </button>
          </li>

          {deleteBlockedReason ? (
            <li className="menu-hint" id={hintId} role="presentation">
              {deleteBlockedReason}
            </li>
          ) : null}
        </ul>
      ) : null}
    </div>
  )
}

function statusLabel(status: string): string {
  return status.charAt(0) + status.slice(1).toLowerCase().replace(/_/g, ' ')
}

function emptyTitle(total: number, visibleCount: number, query: string): string {
  if (total === 0) return 'No cases yet'
  if (visibleCount === 0) return 'Nothing active'
  if (query.trim()) return 'No cases match that search'
  return 'No cases to show'
}

function emptyBody(
  total: number,
  visibleCount: number,
  query: string,
  archivedCount: number,
): string {
  if (total === 0) return 'Create a response case to start collecting evidence.'
  if (visibleCount === 0 && archivedCount > 0) {
    return `Every case is archived. Turn on “Show archived” to see ${
      archivedCount === 1 ? 'it' : 'them'
    }.`
  }
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
