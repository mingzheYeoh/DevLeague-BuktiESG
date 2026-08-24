'use client'

import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CircleHelp,
  Plus,
  RotateCcw,
  ShieldCheck,
  Sparkles,
  X,
} from 'lucide-react'
import { useState } from 'react'

import type {
  AnswerRecord,
  QuestionListItem,
  ReviewAction,
  ReviewQuestionRequest,
} from '@/lib/api'
import {
  errorMessage,
  evidenceHeadline,
  evidenceTone,
  isActionableStatus,
  isEvidenceGap,
  locationLabelFor,
  pillarLabel,
  statusLabel,
} from '@/lib/api'
import { formatDateTimeLabel } from '@/lib/format'

import { DocumentPreview } from '../document-preview'
import {
  Drawer,
  ErrorNotice,
  EvidencePill,
  Key,
  NotAvailable,
  PageTitle,
  Pill,
  ReviewPill,
} from '../primitives'

/**
 * One question, its server-resolved evidence, and the human review verdict.
 *
 * Three rules shape this screen:
 *  - The evidence status and its reason are the server's. Nothing here
 *    recomputes or softens them.
 *  - The source location and excerpt come from `document_chunks` server-side.
 *    The AI pipeline only ever returns a chunk id, so a location shown here
 *    cannot be a fabricated one — and if the server sends none, none is shown.
 *  - Only a human action sets `HUMAN_CONFIRMED`. The mapping rationale is
 *    labelled as a recommendation and can never stand in for a verdict.
 *
 * Layout note: the left column used to stack seven blocks, two of which were
 * long explanations of API limitations, and the full `status_reason` sentence
 * appeared here *and* again in the right column. It now shows a one-line
 * conclusion, the specific findings as bullets, and everything else folded
 * away — with the API caveat moved next to the button it actually affects.
 */
export function QuestionDetailScreen({
  caseId,
  question,
  reviewerName,
  onEditReviewer,
  busy,
  onReview,
  onCreateAction,
  onBack,
}: {
  caseId: string
  question: QuestionListItem
  reviewerName: string
  onEditReviewer: () => void
  busy: boolean
  onReview: (questionId: string, body: ReviewQuestionRequest) => Promise<AnswerRecord>
  onCreateAction: (question: QuestionListItem) => void
  onBack: () => void
}) {
  const [pendingAction, setPendingAction] = useState<ReviewAction | null>(null)
  const [editedAnswer, setEditedAnswer] = useState('')
  const [reason, setReason] = useState('')
  const [reviewError, setReviewError] = useState<string | null>(null)
  const [result, setResult] = useState<AnswerRecord | null>(null)
  const [sourceOpen, setSourceOpen] = useState(false)

  const hasEvidence = Boolean(question.evidence_excerpt || question.evidence_location)
  const isGap = isEvidenceGap(question.evidence_status)

  function start(action: ReviewAction) {
    setReviewError(null)
    setResult(null)
    setEditedAnswer('')
    setReason('')
    setPendingAction(action)
  }

  async function submit() {
    if (!pendingAction) return
    if (!reviewerName.trim()) {
      setReviewError('Set your reviewer label first — the API rejects a blank reviewer_name.')
      return
    }
    if (pendingAction === 'EDIT' && !editedAnswer.trim()) {
      setReviewError('An edited answer is required for EDIT.')
      return
    }
    if (REASON_REQUIRED.includes(pendingAction) && !reason.trim()) {
      setReviewError(`A reason is required for ${statusLabel(pendingAction)}.`)
      return
    }

    setReviewError(null)
    try {
      const answer = await onReview(question.id, {
        action: pendingAction,
        reviewer_name: reviewerName.trim(),
        ...(pendingAction === 'EDIT' ? { edited_answer: editedAnswer.trim() } : {}),
        ...(REASON_REQUIRED.includes(pendingAction) ? { reason: reason.trim() } : {}),
      })
      setResult(answer)
      setPendingAction(null)
    } catch (err) {
      setReviewError(errorMessage(err))
    }
  }

  return (
    <div className="detail-page">
      <button className="back" type="button" onClick={onBack}>
        <ArrowLeft />
        Back to questionnaire
      </button>

      <PageTitle
        eyebrow={`${question.external_question_id ?? question.id.slice(0, 8)} · ${pillarLabel(
          question.pillar,
        )}${question.sedg_topic_code ? ` · ${question.sedg_topic_code}` : ''}`}
        title={question.question_text}
        desc={`${question.is_required ? 'Required' : 'Optional'} customer question`}
        actions={
          <>
            <EvidencePill value={question.evidence_status} />
            <ReviewPill value={question.review_status} />
          </>
        }
      />

      <div className="detail-grid">
        <main className="answer-panel">
          <StatusSummary question={question} />

          {result ? <ReviewResult result={result} /> : null}

          <ReviewControls
            pendingAction={pendingAction}
            notApplicable={question.evidence_status === 'NOT_APPLICABLE'}
            confirmed={question.review_status === 'HUMAN_CONFIRMED'}
            reviewerName={reviewerName}
            onEditReviewer={onEditReviewer}
            editedAnswer={editedAnswer}
            setEditedAnswer={setEditedAnswer}
            reason={reason}
            setReason={setReason}
            error={reviewError}
            busy={busy}
            start={start}
            cancel={() => setPendingAction(null)}
            submit={submit}
          />
        </main>

        <aside className="evidence-panel">
          <EvidenceSection
            question={question}
            hasEvidence={hasEvidence}
            onOpenDocument={() => setSourceOpen(true)}
          />

          {isGap ? (
            <section className="side-card action-card">
              <h3>
                <AlertTriangle />
                Turn this into an action
              </h3>
              <p>Give the gap an owner, a next step and a deadline so it can be chased.</p>
              <button
                className="primary full"
                type="button"
                onClick={() => onCreateAction(question)}
              >
                <Plus />
                Create submission action
              </button>
            </section>
          ) : null}

          {question.mapping_rationale ? (
            <section className="side-card">
              <h3>
                <Sparkles />
                Suggested category
                <Pill tone="unreviewed">AI · not a verdict</Pill>
              </h3>
              <p>
                {question.sedg_disclosure_code ?? question.sedg_topic_code ?? 'Not categorised'}
                {' — '}
                {pillarLabel(question.pillar)}
              </p>
              <details className="status-detail">
                <summary>How this was matched</summary>
                <p>{question.mapping_rationale}</p>
              </details>
            </section>
          ) : null}
        </aside>
      </div>

      {sourceOpen && question.evidence_document_id && question.evidence_document_name ? (
        <DocumentPreview
          caseId={caseId}
          documentId={question.evidence_document_id}
          documentName={question.evidence_document_name}
          highlightLocation={question.evidence_location}
          onClose={() => setSourceOpen(false)}
        />
      ) : null}

      {/* Fallback for an evidence link whose document row could not be loaded.
          Gated on the *name*, not the id: `evidence_document_id` comes from
          `evidence_links.document_id`, a NOT NULL column, so it is always set
          when a link exists and `!evidence_document_id` was unreachable. The
          case this was written for is `evidence_document_name === null`
          (schemas.py: `getattr(document, 'original_filename', None)`), and
          that fell through both branches — a click on "Open document" that
          rendered nothing at all. */}
      {sourceOpen && !question.evidence_document_name && (
        <Drawer
          eyebrow="Evidence source"
          title="Source document not identified"
          close={() => setSourceOpen(false)}
        >
          {question.evidence_excerpt ? (
            <div className="pdf-preview">
              <div className="pdf-sheet">
                <small>Extracted text stored by the server</small>
                <div className="highlight">
                  <span>Excerpt</span>
                  <strong>{question.evidence_excerpt}</strong>
                </div>
              </div>
            </div>
          ) : null}
          <Key
            label="Where in it"
            value={locationLabelFor(question.evidence_location, null)}
          />
          <Key
            label="Matched on"
            value={question.evidence_claim_supported ?? <NotAvailable />}
          />
          <div className="callout warning">
            <AlertTriangle />
            <div>
              <b>The document behind this citation is missing</b>
              <p>
                The excerpt above was read from a stored document, but the record naming that
                document is no longer present, so it cannot be opened. Treat this citation as
                unverifiable until the document is re-uploaded.
              </p>
            </div>
          </div>
        </Drawer>
      )}
    </div>
  )
}

/**
 * The one block that answers "what state is this in, and why".
 *
 * Headline comes from the status enum, bullets come from the server's findings
 * (`status_points`). The full audit sentence and the priority note are folded
 * away — present for anyone who wants them, not in the way of anyone who does
 * not.
 */
function StatusSummary({ question }: { question: QuestionListItem }) {
  const actionable = isActionableStatus(question.evidence_status)
  const points = question.status_points ?? []

  return (
    <section className={`status-summary ${evidenceTone(question.evidence_status)}`}>
      <div className="status-summary-head">
        {actionable ? <AlertTriangle /> : <Check />}
        <div>
          <b>{evidenceHeadline(question.evidence_status)}</b>
          <small>
            Evidence {statusLabel(question.evidence_status).toLowerCase()} · Review{' '}
            {statusLabel(question.review_status).toLowerCase()}
          </small>
        </div>
      </div>

      {points.length > 0 ? (
        // `role="list"` is redundant markup everywhere except Safari, which
        // drops list semantics from a `ul` whose `list-style` is `none`.
        <ul className="status-points" role="list">
          {points.map((point) => (
            <li key={point}>{point}</li>
          ))}
        </ul>
      ) : null}

      {question.status_reason || question.priority_score === null ? (
        <details className="status-detail">
          <summary>Technical detail</summary>
          {question.status_reason ? (
            <p className="status-reason-full">{question.status_reason}</p>
          ) : null}
          <Key
            label="Priority"
            value={
              question.priority_score === null
                ? 'Not scored'
                : `${question.priority_score} / 100`
            }
          />
          {question.priority_score === null ? (
            <p className="field-hint">
              The server sends no priority score in this build, and the priority formula is a
              protected value — so nothing is scored rather than guessed.
            </p>
          ) : null}
        </details>
      ) : null}
    </section>
  )
}

/** What the server recorded, shown straight after a review. */
function ReviewResult({ result }: { result: AnswerRecord }) {
  return (
    <section className="status-summary supported">
      <div className="status-summary-head">
        <Check />
        <div>
          <b>Recorded</b>
          <small>
            {result.reviewer_name ?? 'Unknown reviewer'} ·{' '}
            {formatDateTimeLabel(result.reviewed_at)}
          </small>
        </div>
      </div>

      <p className="answer-recorded">
        {result.confirmed_answer ?? result.draft_answer ?? 'No answer text was stored.'}
      </p>

      <details className="status-detail">
        <summary>What changed</summary>
        <div className="review-list">
          <Key label="Review status" value={<ReviewPill value={result.review_status} />} />
          <Key label="Evidence status" value={<EvidencePill value={result.evidence_status} />} />
          <Key label="Answer provenance" value={statusLabel(result.draft_provenance)} />
          {result.review_reason ? <Key label="Reason" value={result.review_reason} /> : null}
          {result.not_applicable_reason ? (
            <Key label="Not applicable because" value={result.not_applicable_reason} />
          ) : null}
          {result.status_reason ? <Key label="Status reason" value={result.status_reason} /> : null}
        </div>
      </details>
    </section>
  )
}

/** Evidence the server resolved from stored document text. */
function EvidenceSection({
  question,
  hasEvidence,
  onOpenDocument,
}: {
  question: QuestionListItem
  hasEvidence: boolean
  onOpenDocument: () => void
}) {
  if (!hasEvidence) {
    return (
      <section className="side-card">
        <h3>
          <AlertTriangle />
          No evidence linked
        </h3>
        <p>
          Upload the supporting document on the Evidence screen. Matching runs as soon as a file is
          stored.
        </p>
      </section>
    )
  }

  const others = Math.max(question.evidence_candidate_count - 1, 0)

  return (
    <section className="side-card">
      <h3>
        Evidence
        <Pill tone="partial">Candidate</Pill>
      </h3>

      {/* Filename first. The location on its own ("Paragraph 8") says nothing
          about which file it is in, which was the entire problem. */}
      <p className="evidence-where">
        {question.evidence_document_name ?? 'Source document not identified'}
      </p>
      <p className="evidence-locus">
        {locationLabelFor(question.evidence_location, question.evidence_document_name)}
        {question.evidence_candidate_count > 1
          ? ` · showing 1 of ${question.evidence_candidate_count} possible matches`
          : ''}
      </p>

      {question.evidence_excerpt ? (
        <blockquote>“{question.evidence_excerpt}”</blockquote>
      ) : (
        <p className="field-hint">The server returned a location but no excerpt text.</p>
      )}

      <button className="link" type="button" onClick={onOpenDocument}>
        Open document
      </button>

      {others > 0 ? (
        <p className="field-hint">
          The matcher found {question.evidence_candidate_count} passages that share words with this
          question, across your uploaded documents. Only the one above is shown, and it is the most
          recently matched rather than the closest — so check that this document really does answer
          the question.
        </p>
      ) : null}

      {question.evidence_claim_supported ? (
        <details className="status-detail">
          <summary>Why it was matched</summary>
          <p>{question.evidence_claim_supported}</p>
        </details>
      ) : null}
    </section>
  )
}

function ReviewControls({
  pendingAction,
  notApplicable,
  confirmed,
  reviewerName,
  onEditReviewer,
  editedAnswer,
  setEditedAnswer,
  reason,
  setReason,
  error,
  busy,
  start,
  cancel,
  submit,
}: {
  pendingAction: ReviewAction | null
  /** The server refuses ACCEPT and EDIT while this is true. */
  notApplicable: boolean
  confirmed: boolean
  reviewerName: string
  onEditReviewer: () => void
  editedAnswer: string
  setEditedAnswer: (v: string) => void
  reason: string
  setReason: (v: string) => void
  error: string | null
  busy: boolean
  start: (action: ReviewAction) => void
  cancel: () => void
  submit: () => void | Promise<void>
}) {
  return (
    <section className="review-block">
      <h3>Your decision</h3>

      {error ? <ErrorNotice message={error} /> : null}

      {!reviewerName.trim() ? (
        // `callout-inline` keeps this visible but lighter than the decision it
        // sits above — the plain `warning` callout out-weighed the buttons.
        <div className="callout warning callout-inline">
          <AlertTriangle />
          <div>
            <b>Set your reviewer label first</b>
            <p>
              Every review is recorded against a name. It is a label only — the API has no
              authentication and verifies nothing.
            </p>
          </div>
          <button className="secondary" type="button" onClick={onEditReviewer}>
            Set label
          </button>
        </div>
      ) : null}

      {pendingAction === null ? (
        notApplicable ? (
          // A not-applicable question cannot also be answered — the server
          // refuses ACCEPT and EDIT on it. Offering those buttons would only
          // produce a 422, so the single real choice is shown instead.
          <>
            <div className="answer-actions">
              <button
                className="primary"
                type="button"
                disabled={busy}
                onClick={() => start('REOPEN')}
              >
                <RotateCcw />
                Reopen this question
              </button>
            </div>
            <p className="field-hint">
              You marked this question as not applicable, so there is nothing to answer. Reopening
              withdraws that decision and lets the rule engine assess your evidence again.
            </p>
          </>
        ) : (
          <>
            {/* Two groups rather than one flex row: what you are expected to do
                first, then the less frequent decisions and the withdrawal.
                Same five buttons, same handlers, same labels — only their
                grouping and order in the bar changed. */}
            <div className="decision-actions">
              <div className="decision-primary">
                <button
                  className="primary"
                  type="button"
                  disabled={busy}
                  onClick={() => start('EDIT')}
                >
                  <Check />
                  Write the answer
                </button>
                <button
                  className="secondary"
                  type="button"
                  disabled={busy}
                  onClick={() => start('ACCEPT')}
                >
                  Confirm draft
                </button>
              </div>
              <div className="decision-secondary">
                <button
                  className="danger"
                  type="button"
                  disabled={busy}
                  onClick={() => start('REJECT')}
                >
                  <X />
                  Reject
                </button>
                <button
                  className="secondary"
                  type="button"
                  disabled={busy}
                  onClick={() => start('NOT_APPLICABLE')}
                >
                  Not applicable
                </button>
                {confirmed ? (
                  <button
                    className="secondary"
                    type="button"
                    disabled={busy}
                    onClick={() => start('REOPEN')}
                  >
                    <RotateCcw />
                    Undo
                  </button>
                ) : null}
              </div>
            </div>

            {/* The caveat sits with the button it affects, rather than as a
                banner at the top of the page. Verified against the running API:
                nothing ever writes `draft_answer`, so ACCEPT copies null into
                confirmed_answer and still counts toward readiness. */}
            <p className="field-hint">
              Pick one. <strong>Write the answer</strong> records text you type.{' '}
              <strong>Confirm draft</strong> accepts the draft the server already holds — which is
              empty in this build, so it marks the question confirmed with no answer text.
            </p>
          </>
        )
      ) : (
        <div className="review-form">
          <h4>{ACTION_TITLES[pendingAction]}</h4>

          {pendingAction === 'ACCEPT' ? (
            <div className="callout warning">
              <AlertTriangle />
              <div>
                <b>This confirms an empty answer</b>
                <p>
                  The server holds no draft text for this question, so confirming records no answer
                  while still counting toward readiness. Use <strong>Write the answer</strong>
                  {' '}instead unless you specifically want that.
                </p>
              </div>
            </div>
          ) : null}

          {pendingAction === 'EDIT' ? (
            <label>
              {/* Text and marker in one span: the shared label rule is a flex
                  column, so a bare sibling span would drop to its own line. */}
              <span className="label-row">
                Answer to record <span aria-hidden="true">*</span>
              </span>
              <textarea
                value={editedAnswer}
                onChange={(e) => setEditedAnswer(e.target.value)}
                rows={5}
                placeholder="Write the answer that should be recorded as confirmed."
                autoFocus
              />
            </label>
          ) : null}

          {pendingAction === 'NOT_APPLICABLE' ? (
            <div className="callout warning">
              <AlertTriangle />
              <div>
                <b>Only for questions that genuinely do not apply</b>
                <p>
                  A required question marked not applicable counts as confirmed, so readiness goes
                  up. Use it when the question cannot apply to this company — no vehicle fleet, no
                  such facility — not when you are unsure. If you are unsure, write what you do know
                  instead.
                </p>
              </div>
            </div>
          ) : null}

          {pendingAction === 'REOPEN' ? (
            <div className="callout info">
              <CircleHelp />
              <div>
                <b>This withdraws your decision</b>
                <p>
                  The review goes back to unreviewed and any confirmed answer text is cleared. The
                  rule engine then reassesses the evidence, so this question stops counting toward
                  readiness until you decide again.
                </p>
              </div>
            </div>
          ) : null}

          {pendingAction === 'REJECT' ||
          pendingAction === 'NOT_APPLICABLE' ||
          pendingAction === 'REOPEN' ? (
            <label>
              <span className="label-row">
                Reason <span aria-hidden="true">*</span>
              </span>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                placeholder={REASON_PLACEHOLDERS[pendingAction]}
                autoFocus
              />
            </label>
          ) : null}

          <div className="form-actions">
            <button className="secondary" type="button" onClick={cancel} disabled={busy}>
              Cancel
            </button>
            <button className="primary" type="button" onClick={() => void submit()} disabled={busy}>
              <Check />
              {busy ? 'Saving…' : `Record as ${reviewerName || 'reviewer'}`}
            </button>
          </div>
        </div>
      )}

      <p className="human-note">
        <ShieldCheck />
        Only a human confirmation marks an answer ready. Evidence status is computed separately by
        the rule engine and does not change when you confirm.
      </p>
    </section>
  )
}

const ACTION_TITLES: Record<ReviewAction, string> = {
  ACCEPT: 'Confirm the stored draft',
  EDIT: 'Write the answer',
  REJECT: 'Reject the draft',
  NOT_APPLICABLE: 'Mark as not applicable',
  REOPEN: 'Reopen this question',
}

/** Actions the server rejects without a non-blank reason. */
const REASON_REQUIRED: ReviewAction[] = ['REJECT', 'NOT_APPLICABLE', 'REOPEN']

const REASON_PLACEHOLDERS: Record<ReviewAction, string> = {
  ACCEPT: '',
  EDIT: '',
  REJECT: 'Why is this draft not acceptable?',
  NOT_APPLICABLE: 'Why can this question not apply to this company?',
  REOPEN: 'Why are you withdrawing the earlier decision?',
}
