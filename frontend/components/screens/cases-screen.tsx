'use client'

import { ArrowRight, FileSpreadsheet, Plus, RefreshCw } from 'lucide-react'
import { useMemo, useState } from 'react'

import type { CaseSummary } from '@/lib/api'
import { errorMessage } from '@/lib/api'
import { daysUntil, formatDateLabel, relativeTimeLabel } from '@/lib/format'

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
 */
export function CasesScreen({
  cases,
  loading,
  error,
  reload,
  onOpenCase,
  onNewCase,
}: {
  cases: CaseSummary[]
  loading: boolean
  error: unknown
  reload: () => void
  onOpenCase: (caseId: string) => void
  onNewCase: () => void
}) {
  const [query, setQuery] = useState('')

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return cases
    return cases.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        (c.customer_name ?? '').toLowerCase().includes(q),
    )
  }, [cases, query])

  const dueSoon = cases.filter((c) => {
    const days = daysUntil(c.deadline_at)
    return days !== null && days >= 0 && days <= 14
  }).length
  const drafts = cases.filter((c) => c.status === 'DRAFT').length
  const inReview = cases.filter((c) => c.status === 'IN_REVIEW').length
  const customerCount = new Set(
    cases.map((c) => c.customer_name).filter((name): name is string => Boolean(name)),
  ).size

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
            </tr>
          </thead>
          <tbody>
            {filtered.map((c) => (
              <tr key={c.id} className="clickable" onClick={() => onOpenCase(c.id)}>
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
                  <small>{c.deadline_at ? relativeDeadline(c.deadline_at) : 'No deadline set'}</small>
                </td>
                <td>{relativeTimeLabel(c.updated_at)}</td>
                <td>
                  <CasePill value={c.status} />
                </td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {loading && cases.length === 0 ? <Loading label="Loading cases…" /> : null}

        {!loading && filtered.length === 0 ? (
          <EmptyState
            icon={<FileSpreadsheet />}
            title={cases.length === 0 ? 'No cases yet' : 'No cases match that search'}
          >
            {cases.length === 0
              ? 'Create a response case to start collecting evidence.'
              : 'Clear the search to see every case.'}
          </EmptyState>
        ) : null}
      </div>
    </div>
  )
}

function relativeDeadline(iso: string): string {
  const days = daysUntil(iso)
  if (days === null) return 'No deadline set'
  if (days < 0) return 'Overdue'
  if (days === 0) return 'Due today'
  return `${days} day${days === 1 ? '' : 's'} left`
}
