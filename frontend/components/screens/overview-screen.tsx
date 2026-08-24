'use client'

import { AlertTriangle, ArrowRight, ClipboardCheck, FileText, RefreshCw } from 'lucide-react'
import type { CSSProperties } from 'react'
import { useMemo } from 'react'

import type {
  ActionRecord,
  CaseSummary,
  DocumentRecord,
  QuestionListItem,
  ReadinessSummary,
} from '@/lib/api'
import {
  PILLAR_ORDER,
  attentionOrder,
  documentsNeedingAttention,
  errorMessage,
  evidenceTone,
  openActions,
  pillarBreakdown,
  pillarLabel,
  questionStats,
  statusLabel,
} from '@/lib/api'
import { daysLeftLabel, daysUntil, initials, relativeTimeLabel } from '@/lib/format'

import type { Screen } from '../shell'
import {
  EmptyState,
  ErrorNotice,
  Key,
  Loading,
  Meter,
  PageTitle,
  Pill,
  Summary,
} from '../primitives'

/**
 * The case dashboard.
 *
 * The headline readiness number is the server's
 * (`GET /api/v1/cases/{id}/readiness`), because the readiness formula is a
 * protected value. Everything else on this screen is a tally of statuses the
 * server already assigned.
 */
export function OverviewScreen({
  caseSummary,
  readiness,
  questions,
  documents,
  actions,
  loading,
  error,
  refresh,
  go,
  onOpenQuestion,
}: {
  caseSummary: CaseSummary | null
  readiness: ReadinessSummary | null
  questions: QuestionListItem[]
  documents: DocumentRecord[]
  actions: ActionRecord[]
  loading: boolean
  error: unknown
  refresh: () => void
  go: (screen: Screen) => void
  onOpenQuestion: (questionId: string) => void
}) {
  const stats = questionStats(questions, readiness)
  const open = openActions(actions)
  const attention = documentsNeedingAttention(documents)
  const dueThisWeek = open.filter((a) => {
    const days = daysUntil(a.deadline_at)
    return days !== null && days >= 0 && days <= 7
  }).length

  const activity = useMemo(() => buildActivity(documents, actions), [documents, actions])
  const topQuestions = attentionOrder(questions).slice(0, 4)

  if (loading && !caseSummary) return <Loading label="Loading case…" />

  return (
    <div>
      <PageTitle
        eyebrow={caseSummary?.title ?? 'Response case'}
        title="Response readiness"
        desc="What is proven, what needs human review, and what has to happen next."
        actions={
          <>
            <button className="secondary" type="button" onClick={refresh}>
              <RefreshCw />
              Refresh
            </button>
            <button className="primary" type="button" onClick={() => go('questions')}>
              Open questionnaire
              <ArrowRight />
            </button>
          </>
        }
      />

      {error ? <ErrorNotice message={errorMessage(error)} onRetry={refresh} /> : null}

      <div className="readiness">
        <div className="score">
          <div
            className="ring"
            style={{ '--p': stats.readinessPercentage ?? 0 } as CSSProperties}
          >
            <div className="ring-inner">
              <strong>
                {stats.readinessPercentage === null ? '—' : `${stats.readinessPercentage}%`}
              </strong>
              <span>ready</span>
            </div>
          </div>
          <div>
            <Pill tone="warning">{daysLeftLabel(caseSummary?.deadline_at)}</Pill>
            <h2>
              {stats.confirmedRequired} of {stats.totalRequiredFromServer} required answers
              confirmed
            </h2>
            <p>
              {stats.totalRequiredFromServer === 0
                ? 'No required questions yet. Upload the customer questionnaire to identify them.'
                : `${
                    stats.totalRequiredFromServer - stats.confirmedRequired
                  } required answers still need evidence or human review before export.`}
            </p>
            <Meter value={stats.readinessPercentage} />
            <small className="field-hint">
              Computed by the server from confirmed required answers. An unconfirmed draft never
              counts.
            </small>
          </div>
        </div>
        {/* These two count different populations: readiness is required-only,
            because that is what gates export, while every question still needs
            a human before it can be sent. Without the denominators the pair
            reads as 0 + 20 = 20 against a stated total of 14, and the reader
            is left to work out that the six optional questions are the gap. */}
        <div className="readiness-stats">
          <Summary
            label="Confirmed"
            value={String(stats.confirmedRequired)}
            sub={`of ${stats.totalRequiredFromServer} required`}
          />
          <Summary
            label="Awaiting review"
            value={String(stats.unconfirmedDrafts)}
            sub={`of ${stats.total} questions`}
          />
          <Summary
            label="Open actions"
            value={String(open.length)}
            sub={`${dueThisWeek} due within 7 days`}
            tone={open.length > 0 ? 'warn-text' : undefined}
          />
        </div>
      </div>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Confirmed by pillar</h2>
              <p>Required questions only</p>
            </div>
          </div>
          {questions.length === 0 ? (
            <EmptyState icon={<FileText />} title="No questions yet" />
          ) : (
            PILLAR_ORDER.map((pillar) => {
              const b = pillarBreakdown(questions, pillar)
              if (b.total === 0) return null
              return (
                <div className="pillar" key={pillar}>
                  <div className="pillar-icon">{pillar === 'UNCATEGORIZED' ? '?' : pillar}</div>
                  <div>
                    <b>{pillarLabel(pillar)}</b>
                    <small>
                      {b.confirmedRequired} of {b.required} required confirmed
                    </small>
                  </div>
                  <Meter value={b.percentage} />
                  <strong>{b.percentage === null ? '—' : `${b.percentage}%`}</strong>
                </div>
              )
            })
          )}
        </section>

        <section className="panel priorities">
          <div className="section-head">
            <div>
              <h2>Needs attention first</h2>
              <p>Evidence gaps and unconfirmed answers · not a priority score</p>
            </div>
            <button className="link" type="button" onClick={() => go('questions')}>
              View all
            </button>
          </div>
          {topQuestions.length === 0 ? (
            <EmptyState icon={<FileText />} title="Nothing to review" />
          ) : (
            topQuestions.map((q) => (
              <button key={q.id} type="button" onClick={() => onOpenQuestion(q.id)}>
                <span className={`priority-dot ${evidenceTone(q.evidence_status)}`} aria-hidden="true" />
                <div>
                  <b>{q.question_text}</b>
                  <small>
                    {statusLabel(q.evidence_status)} · {statusLabel(q.review_status)}
                    {q.status_reason ? ` · ${q.status_reason}` : ''}
                  </small>
                </div>
                <ArrowRight />
              </button>
            ))
          )}
        </section>

        <section className="panel">
          <div className="section-head">
            <div>
              <h2>Evidence coverage</h2>
              <p>Across all {stats.total} questions</p>
            </div>
          </div>
          <div className="coverage">
            <div>
              <span className="supported">{stats.evidenceCounts.VERIFIED}</span>
              <small>Verified</small>
            </div>
            <div>
              <span className="partial">{stats.evidenceCounts.PARTIAL}</span>
              <small>Partial</small>
            </div>
            <div>
              <span className="missing">{stats.evidenceCounts.MISSING}</span>
              <small>Missing</small>
            </div>
            <div>
              <span className="conflict">{stats.evidenceCounts.CONFLICTING}</span>
              <small>Conflicting</small>
            </div>
          </div>
          {/* Every figure above and below counts QUESTIONS. The warning that
              follows counts DOCUMENTS. Both were once labelled "needs manual
              review", so a case with one unreadable file and no question
              blocked by it showed a 0 directly above a 1 and read as a
              contradiction — both numbers correct, the panel not. */}
          <div className="coverage-secondary">
            <Key label="Outdated" value={stats.evidenceCounts.OUTDATED} />
            <Key
              label="Questions blocked by an unreadable file"
              value={stats.evidenceCounts.NEEDS_MANUAL_REVIEW}
            />
            <Key label="Not applicable" value={stats.evidenceCounts.NOT_APPLICABLE} />
          </div>
          {attention.length > 0 && (
            <div className="callout warning">
              <AlertTriangle />
              <div>
                <b>
                  {attention.length} document{attention.length === 1 ? '' : 's'} could not be
                  processed
                </b>
                <p>
                  {attention[0].original_filename} could not be read, so nothing in it was
                  indexed.{' '}
                  {stats.evidenceCounts.NEEDS_MANUAL_REVIEW === 0
                    ? 'No question is blocked by it — every question found evidence elsewhere, which is not the same as the file being unnecessary.'
                    : `${stats.evidenceCounts.NEEDS_MANUAL_REVIEW} question${
                        stats.evidenceCounts.NEEDS_MANUAL_REVIEW === 1 ? '' : 's'
                      } above depend on it.`}
                </p>
              </div>
              <button className="link" type="button" onClick={() => go('intake')}>
                Inspect
              </button>
            </div>
          )}
        </section>

        <section className="panel activity">
          <div className="section-head">
            <div>
              <h2>Recent updates</h2>
              <p>From document and action timestamps</p>
            </div>
          </div>
          {activity.length === 0 ? (
            <EmptyState icon={<ClipboardCheck />} title="Nothing recorded yet" />
          ) : (
            activity.map((entry) => (
              <div key={entry.id}>
                <span>{entry.initials}</span>
                <p>
                  <b>{entry.text}</b>
                  <small>{entry.time}</small>
                </p>
              </div>
            ))
          )}
        </section>
      </div>

      {questions.length === 0 && documents.length === 0 ? (
        <div className="callout info">
          <ArrowRight />
          <div>
            <b>This case is empty</b>
            <p>Upload the customer questionnaire on the Evidence screen to identify questions.</p>
          </div>
          <button className="link" type="button" onClick={() => go('intake')}>
            Go to Evidence
          </button>
        </div>
      ) : null}
    </div>
  )
}

interface ActivityEntry {
  id: string
  initials: string
  text: string
  time: string
  at: number
}

/**
 * A feed built only from timestamps the server returns. The API has no audit
 * or activity endpoint, so this is not a full history — it is the most recent
 * document and action changes, labelled as such.
 */
function buildActivity(documents: DocumentRecord[], actions: ActionRecord[]): ActivityEntry[] {
  const entries: ActivityEntry[] = []

  for (const doc of documents) {
    entries.push({
      id: `doc-${doc.id}`,
      initials: 'DOC',
      text: `${doc.original_filename} uploaded · ${statusLabel(doc.processing_status)}`,
      time: relativeTimeLabel(doc.created_at),
      at: new Date(doc.created_at).getTime(),
    })
  }

  for (const action of actions) {
    entries.push({
      id: `action-${action.id}`,
      initials: initials(action.owner_name) || 'ACT',
      text: `${action.title} · ${statusLabel(action.status)}`,
      time: relativeTimeLabel(action.updated_at),
      at: new Date(action.updated_at).getTime(),
    })
  }

  return entries
    .filter((e) => Number.isFinite(e.at))
    .sort((a, b) => b.at - a.at)
    .slice(0, 6)
}
