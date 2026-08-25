'use client'

import { AlertTriangle, ArrowRight, Download, RefreshCw, Search } from 'lucide-react'
import { useMemo, useState } from 'react'

import type { EvidenceStatus, QuestionListItem, ReadinessSummary } from '@/lib/api'
import { attentionOrder, errorMessage, questionStats, statusLabel } from '@/lib/api'
import { downloadTextFile, rowsToCsv } from '@/lib/format'

import {
  EmptyState,
  ErrorNotice,
  EvidencePill,
  Loading,
  NotAvailable,
  PageTitle,
  ReviewPill,
  SearchField,
} from '../primitives'

const FILTERS: { value: 'ALL' | EvidenceStatus; label: string }[] = [
  { value: 'ALL', label: 'All' },
  { value: 'MISSING', label: 'Missing' },
  { value: 'PARTIAL', label: 'Partial' },
  { value: 'CONFLICTING', label: 'Conflicting' },
  { value: 'OUTDATED', label: 'Outdated' },
  { value: 'VERIFIED', label: 'Verified' },
  { value: 'NEEDS_MANUAL_REVIEW', label: 'Needs manual review' },
  { value: 'NOT_APPLICABLE', label: 'Not applicable' },
]

/**
 * `GET /api/v1/cases/{id}/questions`.
 *
 * Every status in this table is the server's. The Priority column shows what
 * the server sends, which is currently nothing: `priority_score` is always
 * null in this slice and the priority formula is a protected value, so the
 * column reads "Not scored" instead of a number computed here.
 */
export function QuestionsScreen({
  questions,
  readiness,
  loading,
  error,
  refresh,
  onOpenQuestion,
  attentionFirst,
}: {
  questions: QuestionListItem[]
  readiness: ReadinessSummary | null
  loading: boolean
  error: unknown
  refresh: () => void
  onOpenQuestion: (questionId: string) => void
  /** Start on the review queue ordering rather than questionnaire order. */
  attentionFirst?: boolean
}) {
  const [filter, setFilter] = useState<'ALL' | EvidenceStatus>('ALL')
  const [query, setQuery] = useState('')
  const [byAttention, setByAttention] = useState(Boolean(attentionFirst))

  const stats = questionStats(questions, readiness)

  const list = useMemo(() => {
    let next = questions
    if (filter !== 'ALL') next = next.filter((q) => q.evidence_status === filter)
    const q = query.trim().toLowerCase()
    if (q) {
      next = next.filter(
        (item) =>
          item.question_text.toLowerCase().includes(q) ||
          (item.external_question_id ?? '').toLowerCase().includes(q) ||
          (item.sedg_topic_code ?? '').toLowerCase().includes(q),
      )
    }
    return byAttention ? attentionOrder(next) : next
  }, [questions, filter, query, byAttention])

  function exportCsv() {
    const rows: (string | number | null)[][] = [
      [
        'question_id',
        'external_question_id',
        'question_text',
        'pillar',
        'sedg_topic_code',
        'sedg_disclosure_code',
        'is_required',
        'evidence_status',
        'review_status',
        'status_reason',
        'priority_score',
      ],
      ...questions.map((q) => [
        q.id,
        q.external_question_id,
        q.question_text,
        q.pillar,
        q.sedg_topic_code,
        q.sedg_disclosure_code,
        q.is_required ? 'true' : 'false',
        q.evidence_status,
        q.review_status,
        q.status_reason,
        q.priority_score,
      ]),
    ]
    downloadTextFile('questions.csv', rowsToCsv(rows), 'text/csv;charset=utf-8')
  }

  return (
    <div>
      <PageTitle
        eyebrow="Question workbench"
        title="Customer questionnaire"
        desc={`${stats.total} question${stats.total === 1 ? '' : 's'} · ${
          stats.requiredCount
        } required · Evidence status and human review stay separate.`}
        actions={
          <>
            <button className="secondary" type="button" onClick={refresh}>
              <RefreshCw />
              Refresh
            </button>
            <button
              className="secondary"
              type="button"
              onClick={exportCsv}
              disabled={questions.length === 0}
            >
              <Download />
              Export list
            </button>
          </>
        }
      />

      {error ? <ErrorNotice message={errorMessage(error)} onRetry={refresh} /> : null}

      <div className="summary-strip">
        <b>
          {stats.confirmedRequired} / {stats.totalRequiredFromServer}{' '}
          <span>required confirmed</span>
        </b>
        {/* Only the first figure counts required answers - that is what gates
            export. The other three count every question. All four sit in one
            strip, so each states its own total; without that they read against
            the only denominator on the line, which is the wrong one for three
            of them. */}
        <b>
          {stats.unconfirmedDrafts} <span>of {stats.total} awaiting human review</span>
        </b>
        <b>
          {stats.evidenceGaps} <span>of {stats.total} with an evidence gap</span>
        </b>
        <b>
          {stats.sourceConflicts} <span>of {stats.total} reporting a source conflict</span>
        </b>
      </div>

      <div className="toolbar">
        <SearchField placeholder="Search questions" value={query} onChange={setQuery} grow />
        {FILTERS.map(({ value, label }) => (
          <button
            key={value}
            type="button"
            className={`filter${filter === value ? ' active' : ''}`}
            onClick={() => setFilter(value)}
          >
            {label}
          </button>
        ))}
        <button
          type="button"
          className={`control${byAttention ? ' active' : ''}`}
          onClick={() => setByAttention((v) => !v)}
          title="Sort gaps and unconfirmed answers first. Not a priority score."
        >
          {byAttention ? 'Needs attention first' : 'Questionnaire order'}
        </button>
      </div>

      {/* `questions-table` scopes this screen's column widths and the Reason
          clamp. The other three tables in the app share `.table-card` and must
          not inherit any of it. */}
      <div className="table-card questions-table">
        <table>
          <thead>
            <tr>
              <th className="col-question">Question</th>
              <th className="col-topic">Topic</th>
              <th className="col-evidence">Evidence</th>
              <th className="col-review">Review</th>
              <th className="col-reason">Reason</th>
              <th className="col-priority">Priority</th>
              <th className="col-action">
                <span className="sr-only">Open question</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {list.map((q) => (
              <tr key={q.id} className="clickable" onClick={() => onOpenQuestion(q.id)}>
                <td>
                  <div className="question-cell">
                    <span>{q.external_question_id ?? q.id.slice(0, 8)}</span>
                    <b>{q.question_text}</b>
                    <small>{q.is_required ? 'Required' : 'Optional'}</small>
                  </div>
                </td>
                <td>
                  {q.sedg_topic_code ?? statusLabel(q.pillar)}
                  {q.sedg_disclosure_code ? <small>{q.sedg_disclosure_code}</small> : null}
                </td>
                <td>
                  <EvidencePill value={q.evidence_status} />
                </td>
                <td>
                  <ReviewPill value={q.review_status} />
                </td>
                <td className="reason-cell">
                  {q.status_reason ? (
                    // The full reason stays in the DOM; `.reason-summary`
                    // clamps it to two lines visually. Truncation is never
                    // applied to the data, so the export and the detail screen
                    // still carry the complete text.
                    <div className="reason-content">
                      <AlertTriangle aria-hidden="true" />
                      <span className="reason-summary">{q.status_reason}</span>
                    </div>
                  ) : (
                    <NotAvailable title="The server has not recorded a reason for this status" />
                  )}
                </td>
                <td>
                  {q.priority_score === null ? (
                    <small className="muted">Not scored</small>
                  ) : (
                    <strong className="priority-score">{q.priority_score}</strong>
                  )}
                </td>
                <td className="col-action">
                  {/* The row is clickable, but a click handler on <tr> is not
                      reachable by keyboard. This button is the focusable route
                      to the same destination. */}
                  <button
                    type="button"
                    className="row-open-btn"
                    aria-label={`View question ${
                      q.external_question_id ?? q.id.slice(0, 8)
                    }: ${q.question_text}`}
                    title="View question"
                    onClick={(e) => {
                      e.stopPropagation()
                      onOpenQuestion(q.id)
                    }}
                  >
                    <ArrowRight aria-hidden="true" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {loading && questions.length === 0 ? <Loading label="Loading questions…" /> : null}

        {!loading && list.length === 0 ? (
          <EmptyState
            icon={<Search />}
            title={
              questions.length === 0
                ? 'No questions identified yet'
                : 'No questions match these filters'
            }
          >
            {questions.length === 0
              ? 'Upload the customer questionnaire as a spreadsheet on the Evidence screen. Questions appear here once the server has parsed it.'
              : 'Clear the filters to see every question.'}
          </EmptyState>
        ) : null}
      </div>
    </div>
  )
}
