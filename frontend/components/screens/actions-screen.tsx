'use client'

import { AlertTriangle, ArrowRight, ClipboardCheck, Plus, RefreshCw } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'

import type {
  ActionRecord,
  ActionStatus,
  ActionType,
  CreateActionRequest,
  QuestionListItem,
} from '@/lib/api'
import { ACTION_STATUSES, errorMessage, statusLabel } from '@/lib/api'
import { dateInputToIso, formatDateLabel, isoToDateInput, relativeTimeLabel } from '@/lib/format'

import {
  ActionPill,
  Drawer,
  EmptyState,
  ErrorNotice,
  Key,
  Loading,
  NotAvailable,
  PageTitle,
  Pill,
  SearchField,
} from '../primitives'

export interface ActionPrefill {
  questionId: string | null
  title: string
}

/**
 * `GET/POST /api/v1/cases/{id}/actions` and the status endpoint.
 *
 * The server's Gate P5 rules are mirrored in the form rather than discovered
 * through a 422: an Action needs an owner, a next step and a deadline;
 * completing one needs a completion note; and completing one flagged
 * `requires_closure_evidence` needs a valid evidence-link id.
 */
export function ActionsScreen({
  actions,
  questions,
  loading,
  error,
  busy,
  refresh,
  onCreate,
  onUpdateStatus,
  prefill,
  onConsumePrefill,
}: {
  actions: ActionRecord[]
  questions: QuestionListItem[]
  loading: boolean
  error: unknown
  busy: boolean
  refresh: () => void
  onCreate: (body: CreateActionRequest) => Promise<ActionRecord>
  onUpdateStatus: (
    actionId: string,
    body: { status: ActionStatus; completion_note?: string | null; closure_evidence_link_id?: string | null },
  ) => Promise<ActionRecord>
  prefill: ActionPrefill | null
  onConsumePrefill: () => void
}) {
  const [tab, setTab] = useState<ActionType>('SUBMISSION')
  const [query, setQuery] = useState('')
  const [creating, setCreating] = useState(false)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    if (prefill) setCreating(true)
  }, [prefill])

  const questionLabel = useMemo(() => {
    const map = new Map<string, string>()
    for (const q of questions) {
      map.set(q.id, q.external_question_id ?? q.question_text.slice(0, 40))
    }
    return map
  }, [questions])

  const submissionCount = actions.filter((a) => a.type === 'SUBMISSION').length
  const improvementCount = actions.filter((a) => a.type === 'IMPROVEMENT').length

  const list = useMemo(() => {
    const q = query.trim().toLowerCase()
    return actions
      .filter((a) => a.type === tab)
      .filter(
        (a) =>
          !q ||
          a.title.toLowerCase().includes(q) ||
          (a.owner_name ?? '').toLowerCase().includes(q) ||
          (a.next_step ?? '').toLowerCase().includes(q),
      )
  }, [actions, tab, query])

  const selected = actions.find((a) => a.id === selectedId) ?? null

  return (
    <div>
      <PageTitle
        eyebrow="Follow-up work"
        title="Actions"
        desc="Turn evidence gaps into owned next steps with closure evidence."
        actions={
          <>
            <button className="secondary" type="button" onClick={refresh}>
              <RefreshCw />
              Refresh
            </button>
            <button className="primary" type="button" onClick={() => setCreating(true)}>
              <Plus />
              New action
            </button>
          </>
        }
      />

      {error ? <ErrorNotice message={errorMessage(error)} onRetry={refresh} /> : null}

      <div className="tabs page-tabs">
        <button
          className={tab === 'SUBMISSION' ? 'active' : ''}
          type="button"
          onClick={() => setTab('SUBMISSION')}
        >
          Submission actions
          <b>{submissionCount}</b>
        </button>
        <button
          className={tab === 'IMPROVEMENT' ? 'active' : ''}
          type="button"
          onClick={() => setTab('IMPROVEMENT')}
        >
          Improvement actions
          <b>{improvementCount}</b>
        </button>
      </div>

      <div className="toolbar">
        <SearchField placeholder="Search actions" value={query} onChange={setQuery} grow />
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Action</th>
              <th>Linked question</th>
              <th>Owner</th>
              <th>Deadline</th>
              <th>Status</th>
              <th>Closure evidence</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {list.map((a) => (
              <tr key={a.id} className="clickable" onClick={() => setSelectedId(a.id)}>
                <td>
                  <b>{a.title}</b>
                  <small>{a.next_step ?? ''}</small>
                </td>
                <td>
                  {a.question_id ? (
                    <Pill>{questionLabel.get(a.question_id) ?? a.question_id.slice(0, 8)}</Pill>
                  ) : (
                    <NotAvailable title="Not linked to a question" />
                  )}
                </td>
                <td>
                  {a.owner_name ?? <NotAvailable />}
                  {a.owner_role ? <small>{a.owner_role}</small> : null}
                </td>
                <td>{formatDateLabel(a.deadline_at)}</td>
                <td>
                  <ActionPill value={a.status} />
                </td>
                <td>
                  <ClosureEvidenceCell action={a} />
                </td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {loading && actions.length === 0 ? <Loading label="Loading actions…" /> : null}

        {!loading && list.length === 0 ? (
          <EmptyState
            icon={<ClipboardCheck />}
            title={`No ${tab === 'SUBMISSION' ? 'submission' : 'improvement'} actions`}
          >
            Create one from a question gap, or with the New action button.
          </EmptyState>
        ) : null}
      </div>

      {creating && (
        <CreateActionDrawer
          questions={questions}
          prefill={prefill}
          busy={busy}
          defaultType={tab}
          close={() => {
            setCreating(false)
            onConsumePrefill()
          }}
          onCreate={onCreate}
        />
      )}

      {selected && (
        <ActionDrawer
          action={selected}
          questionLabel={
            selected.question_id ? questionLabel.get(selected.question_id) ?? null : null
          }
          busy={busy}
          onUpdateStatus={onUpdateStatus}
          close={() => setSelectedId(null)}
        />
      )}
    </div>
  )
}

function ClosureEvidenceCell({ action }: { action: ActionRecord }) {
  if (action.closure_evidence_link_id) {
    return <Pill tone="supported">Attached</Pill>
  }
  if (action.requires_closure_evidence) {
    return <Pill tone="warning">Required</Pill>
  }
  return <span className="muted">Not required</span>
}

function CreateActionDrawer({
  questions,
  prefill,
  busy,
  defaultType,
  close,
  onCreate,
}: {
  questions: QuestionListItem[]
  prefill: ActionPrefill | null
  busy: boolean
  defaultType: ActionType
  close: () => void
  onCreate: (body: CreateActionRequest) => Promise<ActionRecord>
}) {
  const [title, setTitle] = useState(prefill?.title ?? '')
  const [type, setType] = useState<ActionType>(defaultType)
  const [questionId, setQuestionId] = useState(prefill?.questionId ?? '')
  const [ownerName, setOwnerName] = useState('')
  const [ownerRole, setOwnerRole] = useState('')
  const [nextStep, setNextStep] = useState('')
  const [deadline, setDeadline] = useState('')
  const [requireClosure, setRequireClosure] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canSubmit =
    title.trim() && ownerName.trim() && nextStep.trim() && deadline && !busy

  async function submit() {
    setError(null)
    const deadlineIso = dateInputToIso(deadline)
    if (!deadlineIso) {
      setError('A valid deadline is required.')
      return
    }
    try {
      await onCreate({
        question_id: questionId || null,
        type,
        title: title.trim(),
        owner_name: ownerName.trim(),
        owner_role: ownerRole.trim() || null,
        next_step: nextStep.trim(),
        deadline_at: deadlineIso,
        // Omitted unless ticked, so the server keeps deriving it from the
        // linked question's evidence status. Sending `false` would override
        // that derivation and silently weaken the rule.
        ...(requireClosure ? { requires_closure_evidence: true } : {}),
      })
      close()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <Drawer eyebrow="New action" title="Create action" close={close}>
      {error ? <ErrorNotice message={error} /> : null}

      <label>
        Action title <span aria-hidden="true">*</span>
        <input value={title} onChange={(e) => setTitle(e.target.value)} />
      </label>
      <label>
        Type
        <select value={type} onChange={(e) => setType(e.target.value as ActionType)}>
          <option value="SUBMISSION">Submission</option>
          <option value="IMPROVEMENT">Improvement</option>
        </select>
      </label>
      <label>
        Linked question
        <select value={questionId} onChange={(e) => setQuestionId(e.target.value)}>
          <option value="">Not linked</option>
          {questions.map((q) => (
            <option key={q.id} value={q.id}>
              {(q.external_question_id ?? q.id.slice(0, 8)) + ' · ' + q.question_text.slice(0, 60)}
            </option>
          ))}
        </select>
      </label>
      <label>
        Owner <span aria-hidden="true">*</span>
        <input
          value={ownerName}
          onChange={(e) => setOwnerName(e.target.value)}
          placeholder="Who is accountable"
        />
      </label>
      <label>
        Owner role
        <input value={ownerRole} onChange={(e) => setOwnerRole(e.target.value)} />
      </label>
      <label>
        Next step <span aria-hidden="true">*</span>
        <textarea value={nextStep} onChange={(e) => setNextStep(e.target.value)} rows={3} />
      </label>
      <label>
        Deadline <span aria-hidden="true">*</span>
        <input type="date" value={deadline} onChange={(e) => setDeadline(e.target.value)} />
      </label>

      <label className="checkbox-row">
        <input
          type="checkbox"
          checked={requireClosure}
          onChange={(e) => setRequireClosure(e.target.checked)}
        />
        <span>
          Require closure evidence before this can be completed
          <small>
            Leave unticked to let the server decide, which it does from the linked
            question&apos;s evidence status — Missing or Conflicting means closure evidence is
            required. Tick it to demand closure evidence regardless.
          </small>
        </span>
      </label>

      <p className="field-hint">
        Owner, next step and deadline are all required by the API.
      </p>

      <button className="primary full" type="button" disabled={!canSubmit} onClick={() => void submit()}>
        <Plus />
        {busy ? 'Creating…' : 'Create action'}
      </button>
    </Drawer>
  )
}

function ActionDrawer({
  action,
  questionLabel,
  busy,
  onUpdateStatus,
  close,
}: {
  action: ActionRecord
  questionLabel: string | null
  busy: boolean
  onUpdateStatus: (
    actionId: string,
    body: { status: ActionStatus; completion_note?: string | null; closure_evidence_link_id?: string | null },
  ) => Promise<ActionRecord>
  close: () => void
}) {
  const [status, setStatus] = useState<ActionStatus>(action.status)
  const [completionNote, setCompletionNote] = useState(action.completion_note ?? '')
  const [linkId, setLinkId] = useState(action.closure_evidence_link_id ?? '')
  const [error, setError] = useState<string | null>(null)

  const completing = status === 'COMPLETED'
  const needsLink = completing && action.requires_closure_evidence && !action.closure_evidence_link_id

  async function submit() {
    setError(null)
    if (completing && !completionNote.trim()) {
      setError('A completion note is required to mark an Action completed.')
      return
    }
    if (needsLink && !linkId.trim()) {
      setError('This Action requires a closure evidence link id before it can be completed.')
      return
    }
    try {
      await onUpdateStatus(action.id, {
        status,
        completion_note: completionNote.trim() || null,
        closure_evidence_link_id: linkId.trim() || null,
      })
      close()
    } catch (err) {
      setError(errorMessage(err))
    }
  }

  return (
    <Drawer eyebrow="Action" title={action.title} close={close}>
      {error ? <ErrorNotice message={error} /> : null}

      <div className="review-list">
        <Key label="Type" value={statusLabel(action.type)} />
        <Key label="Current status" value={<ActionPill value={action.status} />} />
        <Key label="Owner" value={action.owner_name ?? <NotAvailable />} />
        <Key label="Owner role" value={action.owner_role ?? <NotAvailable />} />
        <Key label="Next step" value={action.next_step ?? <NotAvailable />} />
        <Key label="Deadline" value={formatDateLabel(action.deadline_at)} />
        <Key label="Linked question" value={questionLabel ?? <NotAvailable />} />
        <Key
          label="Closure evidence"
          value={
            action.requires_closure_evidence
              ? action.closure_evidence_link_id ?? 'Required, not attached'
              : 'Not required'
          }
        />
        <Key label="Created" value={relativeTimeLabel(action.created_at)} />
        <Key label="Last updated" value={relativeTimeLabel(action.updated_at)} />
        {action.completed_at ? (
          <Key label="Completed" value={relativeTimeLabel(action.completed_at)} />
        ) : null}
      </div>

      <label>
        Status
        <select value={status} onChange={(e) => setStatus(e.target.value as ActionStatus)}>
          {ACTION_STATUSES.map((s) => (
            <option key={s} value={s}>
              {statusLabel(s)}
            </option>
          ))}
        </select>
      </label>

      {completing ? (
        <label>
          Completion note <span aria-hidden="true">*</span>
          <textarea
            value={completionNote}
            onChange={(e) => setCompletionNote(e.target.value)}
            rows={3}
            placeholder="What was done, and what proves it."
          />
        </label>
      ) : null}

      {needsLink ? (
        <>
          <label>
            Closure evidence link id <span aria-hidden="true">*</span>
            <input
              value={linkId}
              onChange={(e) => setLinkId(e.target.value)}
              placeholder="evidence_links row id"
            />
          </label>
          <div className="callout warning">
            <AlertTriangle />
            <div>
              <b>No picker available</b>
              <p>
                The API exposes no endpoint that lists evidence links for a question, so the id has
                to be pasted in. The server still validates it: it must belong to this
                Action&apos;s question and must not be invalidated.
              </p>
            </div>
          </div>
        </>
      ) : null}

      <button className="primary full" type="button" disabled={busy} onClick={() => void submit()}>
        {busy ? 'Saving…' : 'Update status'}
      </button>
    </Drawer>
  )
}
