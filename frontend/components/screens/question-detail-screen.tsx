'use client'

import {
  AlertTriangle,
  ArrowLeft,
  Check,
  CircleHelp,
  Plus,
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
import { errorMessage, isEvidenceGap, pillarLabel, sourceLocationLabel, statusLabel } from '@/lib/api'
import { formatDateTimeLabel } from '@/lib/format'

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
 */
export function QuestionDetailScreen({
  question,
  reviewerName,
  onEditReviewer,
  busy,
  onReview,
  onCreateAction,
  onBack,
}: {
  question: QuestionListItem
  reviewerName: string
  onEditReviewer: () => void
  busy: boolean
  onReview: (questionId: string, body: ReviewQuestionRequest) => Promise<AnswerRecord>
  onCreateAction: (question: QuestionListItem) => void
  onBack: () => void
}) {
  const [tab, setTab] = useState<'evidence' | 'gap'>('evidence')
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
    if ((pendingAction === 'REJECT' || pendingAction === 'NOT_APPLICABLE') && !reason.trim()) {
      setReviewError(`A reason is required for ${statusLabel(pendingAction)}.`)
      return
    }

    setReviewError(null)
    try {
      const answer = await onReview(question.id, {
        action: pendingAction,
        reviewer_name: reviewerName.trim(),
        ...(pendingAction === 'EDIT' ? { edited_answer: editedAnswer.trim() } : {}),
        ...(pendingAction === 'REJECT' || pendingAction === 'NOT_APPLICABLE'
          ? { reason: reason.trim() }
          : {}),
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
          <div className="answer-head">
            <div>
              <Sparkles />
              <b>Answer</b>
              <Pill tone="unreviewed">Draft not exposed by the API</Pill>
            </div>
          </div>

          <div className="callout info">
            <CircleHelp />
            <div>
              <b>The stored draft answer cannot be shown here</b>
              <p>
                The questions endpoint does not return draft or confirmed answer text, and there is
                no question-detail endpoint. Accepting confirms whatever draft the server holds,
                sight unseen. Use <strong>Edit</strong> to write the answer you actually want
                recorded.
              </p>
            </div>
          </div>

          {result ? (
            <div className="answer-text answer-result">
              <b>{result.confirmed_answer ?? result.draft_answer ?? 'No answer text stored.'}</b>
              <div className="review-list">
                <Key label="Review status" value={<ReviewPill value={result.review_status} />} />
                <Key label="Evidence status" value={<EvidencePill value={result.evidence_status} />} />
                <Key label="Provenance" value={statusLabel(result.draft_provenance)} />
                <Key label="Reviewer" value={result.reviewer_name ?? <NotAvailable />} />
                <Key label="Reviewed at" value={formatDateTimeLabel(result.reviewed_at)} />
                {result.review_reason ? <Key label="Reason" value={result.review_reason} /> : null}
                {result.not_applicable_reason ? (
                  <Key label="Not applicable because" value={result.not_applicable_reason} />
                ) : null}
                {result.status_reason ? (
                  <Key label="Status reason" value={result.status_reason} />
                ) : null}
              </div>
            </div>
          ) : null}

          {question.status_reason ? (
            <div className={`callout ${isGap ? 'warning' : 'info'}`}>
              {isGap ? <AlertTriangle /> : <CircleHelp />}
              <div>
                <b>Why the evidence status is {statusLabel(question.evidence_status)}</b>
                <p>{question.status_reason}</p>
              </div>
            </div>
          ) : null}

          <div className="priority-box">
            <div>
              <span>Priority</span>
              <strong>
                {question.priority_score === null ? 'Not scored' : `${question.priority_score} / 100`}
              </strong>
            </div>
            <p className="field-hint">
              The server sends no priority score for this slice, and the priority formula is a
              protected value — so nothing is scored here rather than shown as a guess.
            </p>
          </div>

          <ReviewControls
            pendingAction={pendingAction}
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

          <div className="human-note">
            <ShieldCheck />
            Only a human confirmation marks an answer ready. Evidence status is computed separately
            by the rule engine and is not changed by confirming.
          </div>
        </main>

        <aside className="evidence-panel">
          <div className="tabs">
            <button
              type="button"
              className={tab === 'evidence' ? 'active' : ''}
              onClick={() => setTab('evidence')}
            >
              Evidence ({hasEvidence ? 1 : 0})
            </button>
            <button
              type="button"
              className={tab === 'gap' ? 'active' : ''}
              onClick={() => setTab('gap')}
            >
              Gap & action
            </button>
          </div>

          {tab === 'evidence' ? (
            hasEvidence ? (
              <div className="source-card selected">
                <div className="source-top">
                  <span>[1]</span>
                  <div>
                    <b>{sourceLocationLabel(question.evidence_location)}</b>
                    <small>Resolved by the server from stored document text</small>
                  </div>
                  <Pill tone="partial">Candidate</Pill>
                </div>
                {question.evidence_excerpt ? (
                  <blockquote>“{question.evidence_excerpt}”</blockquote>
                ) : (
                  <p className="field-hint">The server returned a location but no excerpt text.</p>
                )}
                {question.evidence_claim_supported ? (
                  <Key label="Claim supported" value={question.evidence_claim_supported} />
                ) : null}
                <button className="link" type="button" onClick={() => setSourceOpen(true)}>
                  Inspect source
                </button>
              </div>
            ) : (
              <div className="gap-card">
                <AlertTriangle />
                <h3>No evidence linked</h3>
                <p>
                  The server has not linked any document text to this question. Upload the
                  supporting document on the Evidence screen; matching runs on upload.
                </p>
              </div>
            )
          ) : isGap ? (
            <div className="gap-card">
              <AlertTriangle />
              <h3>{statusLabel(question.evidence_status)} evidence</h3>
              <p>
                {question.status_reason ??
                  'The rule engine found this question short of verified evidence.'}
              </p>
              <p className="field-hint">
                An Action needs an owner, a next step and a deadline — the API rejects it otherwise.
                Where evidence is Missing or Conflicting, the server also requires closure evidence
                before the Action can be completed.
              </p>
              <button className="primary full" type="button" onClick={() => onCreateAction(question)}>
                <Plus />
                Create submission action
              </button>
            </div>
          ) : (
            <div className="gap-card">
              <Check />
              <h3>No open gap</h3>
              <p>
                Evidence status is {statusLabel(question.evidence_status)} and review status is{' '}
                {statusLabel(question.review_status)}.
              </p>
            </div>
          )}

          {question.mapping_rationale ? (
            <div className="source-card">
              <div className="source-top">
                <span>
                  <Sparkles />
                </span>
                <div>
                  <b>Mapping rationale</b>
                  <small>AI recommendation · not a verdict</small>
                </div>
              </div>
              <p>{question.mapping_rationale}</p>
              <Key
                label="Mapped to"
                value={
                  question.sedg_disclosure_code ??
                  question.sedg_topic_code ?? <NotAvailable title="No SEDG code assigned" />
                }
              />
            </div>
          ) : null}
        </aside>
      </div>

      {sourceOpen && (
        <Drawer
          eyebrow="Evidence source"
          title={sourceLocationLabel(question.evidence_location)}
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
          <Key label="Source location" value={sourceLocationLabel(question.evidence_location)} />
          <Key
            label="Location type"
            value={question.evidence_location?.type ?? <NotAvailable />}
          />
          <Key
            label="Claim supported"
            value={question.evidence_claim_supported ?? <NotAvailable />}
          />
          <div className="callout info">
            <CircleHelp />
            <div>
              <b>Candidate link, resolved server-side</b>
              <p>
                This location was resolved from the stored document, not supplied by the model.
                Review it before confirming an answer. The original file cannot be opened — the API
                exposes no document download.
              </p>
            </div>
          </div>
        </Drawer>
      )}
    </div>
  )
}

function ReviewControls({
  pendingAction,
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
    <>
      {error ? <ErrorNotice message={error} /> : null}

      {!reviewerName.trim() ? (
        <div className="callout warning">
          <AlertTriangle />
          <div>
            <b>Set your reviewer label to record a verdict</b>
            <p>
              Every review call must carry a reviewer name. It is a label only — the API has no
              authentication and verifies nothing.
            </p>
          </div>
          <button className="link" type="button" onClick={onEditReviewer}>
            Set label
          </button>
        </div>
      ) : null}

      {pendingAction === null ? (
        <div className="answer-actions">
          <button className="danger" type="button" disabled={busy} onClick={() => start('REJECT')}>
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
          <button className="secondary" type="button" disabled={busy} onClick={() => start('EDIT')}>
            Edit answer
          </button>
          <button className="primary" type="button" disabled={busy} onClick={() => start('ACCEPT')}>
            <Check />
            Confirm draft
          </button>
        </div>
      ) : (
        <section className="form-card inline-form">
          <h2>{statusLabel(pendingAction)}</h2>

          {pendingAction === 'ACCEPT' ? (
            <p className="field-hint">
              This confirms the draft answer stored on the server as-is and sets review status to
              Human confirmed.
            </p>
          ) : null}

          {pendingAction === 'EDIT' ? (
            <label>
              Answer to record <span aria-hidden="true">*</span>
              <textarea
                value={editedAnswer}
                onChange={(e) => setEditedAnswer(e.target.value)}
                rows={5}
                placeholder="Write the answer that should be recorded as confirmed."
              />
            </label>
          ) : null}

          {pendingAction === 'REJECT' || pendingAction === 'NOT_APPLICABLE' ? (
            <label>
              Reason <span aria-hidden="true">*</span>
              <textarea
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                placeholder={
                  pendingAction === 'REJECT'
                    ? 'Why is this draft not acceptable?'
                    : 'Why does this question not apply to this organisation?'
                }
              />
            </label>
          ) : null}

          <Key label="Recorded against" value={reviewerName || '— not set —'} />

          <div className="form-actions">
            <button className="secondary" type="button" onClick={cancel} disabled={busy}>
              Cancel
            </button>
            <button className="primary" type="button" onClick={() => void submit()} disabled={busy}>
              <Check />
              {busy ? 'Submitting…' : `Submit ${statusLabel(pendingAction).toLowerCase()}`}
            </button>
          </div>
        </section>
      )}
    </>
  )
}
