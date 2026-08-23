'use client'

import { AlertTriangle, Check, Download, FileCheck2, ShieldCheck, Zap } from 'lucide-react'
import { useState } from 'react'

import type {
  ActionRecord,
  CaseSummary,
  DocumentRecord,
  QuestionListItem,
  ReadinessSummary,
} from '@/lib/api'
import { questionStats, sourceLocationLabel, statusLabel } from '@/lib/api'
import { downloadTextFile, formatDateLabel, rowsToCsv } from '@/lib/format'

import { Drawer, Key, Mark, PageTitle, Pill } from '../primitives'

/**
 * Draft output package.
 *
 * There is no export endpoint: these files are generated in the browser from
 * the case data already loaded from the API. Nothing is rendered that the
 * server did not send — in particular the evidence index carries the server's
 * own statuses, reasons and resolved locations, and unresolved items stay
 * visible in the output rather than being smoothed over.
 */
export function ExportScreen({
  caseSummary,
  readiness,
  questions,
  documents,
  actions,
}: {
  caseSummary: CaseSummary | null
  readiness: ReadinessSummary | null
  questions: QuestionListItem[]
  documents: DocumentRecord[]
  actions: ActionRecord[]
}) {
  const [generated, setGenerated] = useState(false)
  const [showBlockers, setShowBlockers] = useState(false)
  const stats = questionStats(questions, readiness)
  const outstanding = Math.max(stats.totalRequiredFromServer - stats.confirmedRequired, 0)
  const openActionCount = actions.filter((a) => a.status !== 'COMPLETED').length
  const caseName = caseSummary?.title ?? 'Response case'

  function questionsCsv(): string {
    return rowsToCsv([
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
        'evidence_location',
        'evidence_excerpt',
        'claim_supported',
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
        q.evidence_location ? sourceLocationLabel(q.evidence_location) : '',
        q.evidence_excerpt,
        q.evidence_claim_supported,
      ]),
    ])
  }

  function actionsCsv(): string {
    return rowsToCsv([
      [
        'action_id',
        'type',
        'title',
        'question_id',
        'owner_name',
        'owner_role',
        'next_step',
        'deadline_at',
        'status',
        'requires_closure_evidence',
        'closure_evidence_link_id',
        'completion_note',
        'completed_at',
      ],
      ...actions.map((a) => [
        a.id,
        a.type,
        a.title,
        a.question_id,
        a.owner_name,
        a.owner_role,
        a.next_step,
        a.deadline_at,
        a.status,
        a.requires_closure_evidence ? 'true' : 'false',
        a.closure_evidence_link_id,
        a.completion_note,
        a.completed_at,
      ]),
    ])
  }

  function documentsCsv(): string {
    return rowsToCsv([
      [
        'document_id',
        'original_filename',
        'document_type',
        'processing_status',
        'size_bytes',
        'sha256',
        'error',
        'created_at',
      ],
      ...documents.map((d) => [
        d.id,
        d.original_filename,
        d.document_type,
        d.processing_status,
        d.size_bytes,
        d.sha256,
        d.error,
        d.created_at,
      ]),
    ])
  }

  function summaryText(): string {
    const lines: string[] = [
      'ESG QUESTIONNAIRE RESPONSE — DRAFT, NOT SUBMISSION-READY',
      caseName,
      caseSummary?.customer_name ? `Customer: ${caseSummary.customer_name}` : '',
      caseSummary?.deadline_at ? `Deadline: ${formatDateLabel(caseSummary.deadline_at)}` : '',
      `Readiness: ${
        stats.readinessPercentage === null ? 'not available' : `${stats.readinessPercentage}%`
      } (${stats.confirmedRequired} of ${stats.totalRequiredFromServer} required answers confirmed)`,
      '',
      `Unresolved: ${outstanding} required answers unconfirmed, ${stats.evidenceGaps} evidence gaps, ${stats.sourceConflicts} source conflicts, ${openActionCount} open actions.`,
      '',
      '--- QUESTIONS ---',
      '',
    ]

    for (const q of questions) {
      lines.push(
        `${q.external_question_id ?? q.id} · ${q.is_required ? 'REQUIRED' : 'OPTIONAL'} · ${q.pillar}`,
        q.question_text,
        `Evidence: ${statusLabel(q.evidence_status)} | Review: ${statusLabel(q.review_status)}`,
      )
      if (q.status_reason) lines.push(`Reason: ${q.status_reason}`)
      if (q.evidence_excerpt) {
        lines.push(
          `Evidence excerpt: "${q.evidence_excerpt}" (${sourceLocationLabel(q.evidence_location)})`,
        )
      }
      lines.push('')
    }

    lines.push(
      '--- DISCLOSURE ---',
      'This draft was generated from unconfirmed and partially evidenced data.',
      'Every unresolved item above is disclosed deliberately and must not be removed.',
      'It is not an audit, not a certification, and not submission-ready.',
    )

    return lines.filter((line) => line !== undefined).join('\n')
  }

  function downloadPackage() {
    downloadTextFile('customer-response-summary.txt', summaryText())
    downloadTextFile('evidence-index.csv', questionsCsv(), 'text/csv;charset=utf-8')
    downloadTextFile('action-register.csv', actionsCsv(), 'text/csv;charset=utf-8')
    downloadTextFile('document-register.csv', documentsCsv(), 'text/csv;charset=utf-8')
  }

  const previewQuestion =
    questions.find((q) => q.evidence_status !== 'VERIFIED') ?? questions[0] ?? null

  return (
    <div>
      <PageTitle
        eyebrow="Customer outputs"
        title="Review & export"
        desc="Outputs that keep gaps, assumptions and source traceability intact."
        actions={
          generated ? (
            <button className="primary" type="button" onClick={downloadPackage}>
              <Download />
              Download package
            </button>
          ) : undefined
        }
      />

      <div className="export-banner">
        <div>
          <AlertTriangle />
          <div>
            <b>
              {outstanding} required answer{outstanding === 1 ? '' : 's'} not confirmed
            </b>
            <p>
              A marked-up draft can still be generated. It discloses every unresolved item and
              cannot be treated as submission-ready.
            </p>
          </div>
        </div>
        <button className="secondary" type="button" onClick={() => setShowBlockers(true)}>
          Review blockers
        </button>
      </div>

      <div className="blocker-grid">
        <div>
          <strong>{stats.evidenceCounts.MISSING}</strong>
          <span>Missing evidence</span>
          <small>Across all questions</small>
        </div>
        <div>
          <strong>{stats.sourceConflicts}</strong>
          <span>Source conflicts</span>
          <small>Human decision needed</small>
        </div>
        <div>
          <strong>{stats.unconfirmedDrafts}</strong>
          <span>Unconfirmed answers</span>
          <small>Human review needed</small>
        </div>
        <div>
          <strong>{openActionCount}</strong>
          <span>Open actions</span>
          <small>Before the customer deadline</small>
        </div>
      </div>

      <div className="export-grid">
        <section className="panel">
          <h2>Output package</h2>
          <p>Generated in your browser from the loaded case data. There is no export endpoint.</p>
          {(
            [
              ['Customer response summary', 'TXT', 'Answers, statuses and disclosed gaps'],
              ['Evidence index', 'CSV', 'Question-to-source traceability'],
              ['Action register', 'CSV', 'Owners, deadlines and closure evidence'],
              ['Document register', 'CSV', 'Files, checksums and processing state'],
            ] as const
          ).map(([name, kind, desc]) => (
            <label className="output" key={name}>
              <input type="checkbox" defaultChecked disabled />
              <span className="file-icon">
                <FileCheck2 />
              </span>
              <div>
                <b>{name}</b>
                <small>{desc}</small>
              </div>
              <Pill>{kind}</Pill>
            </label>
          ))}
          <button
            className="primary full"
            type="button"
            disabled={questions.length === 0 && documents.length === 0}
            onClick={() => setGenerated(true)}
          >
            <Zap />
            {generated ? 'Regenerate marked-up draft' : 'Generate marked-up draft'}
          </button>
          <div className="human-note">
            <ShieldCheck />
            Generating does not submit anything to the customer.
          </div>
        </section>

        <section className="preview">
          <div className="preview-bar">
            <span>customer-response-summary.txt</span>
            <Pill tone="warning">{generated ? 'Ready · Not submitted' : 'Preview'}</Pill>
          </div>
          <div className="paper">
            <div className="watermark">Draft · Unconfirmed</div>
            <Mark />
            <h2>ESG Questionnaire Response</h2>
            <p>{caseName}</p>
            {caseSummary?.customer_name ? <p>{caseSummary.customer_name}</p> : null}
            <div className="paper-rule" />
            {previewQuestion ? (
              <>
                <h3>
                  {previewQuestion.pillar}
                  {previewQuestion.sedg_topic_code ? ` · ${previewQuestion.sedg_topic_code}` : ''}
                </h3>
                <b>{previewQuestion.question_text}</b>
                <p>
                  Evidence: {statusLabel(previewQuestion.evidence_status)} · Review:{' '}
                  {statusLabel(previewQuestion.review_status)}
                </p>
                {previewQuestion.status_reason && (
                  <div className="paper-warning">
                    <AlertTriangle />
                    {previewQuestion.status_reason}
                  </div>
                )}
                {previewQuestion.evidence_excerpt && (
                  <small>
                    “{previewQuestion.evidence_excerpt}” —{' '}
                    {sourceLocationLabel(previewQuestion.evidence_location)}
                  </small>
                )}
              </>
            ) : (
              <p>No questions have been identified for this case yet.</p>
            )}
          </div>
        </section>
      </div>

      {generated && (
        <div className="history">
          <Check />
          <div>
            <b>Draft package ready</b>
            <span>4 files · generated in this browser</span>
          </div>
          <button className="secondary" type="button" onClick={downloadPackage}>
            <Download />
            Download
          </button>
        </div>
      )}

      {showBlockers && (
        <Drawer eyebrow="Export" title="Review blockers" close={() => setShowBlockers(false)}>
          <div className="gap-card">
            <AlertTriangle />
            <h3>
              {outstanding} required answer{outstanding === 1 ? '' : 's'} not confirmed
            </h3>
            <p>Resolve these before treating the package as submission-ready.</p>
          </div>
          <Key label="Missing evidence" value={`${stats.evidenceCounts.MISSING} questions`} />
          <Key label="Partial evidence" value={`${stats.evidenceCounts.PARTIAL} questions`} />
          <Key label="Outdated evidence" value={`${stats.evidenceCounts.OUTDATED} questions`} />
          <Key label="Source conflicts" value={`${stats.sourceConflicts} need a human decision`} />
          <Key label="Unconfirmed answers" value={`${stats.unconfirmedDrafts} need review`} />
          <Key label="Open actions" value={`${openActionCount} before the deadline`} />
          <Key
            label="Documents needing attention"
            value={`${
              documents.filter(
                (d) =>
                  d.processing_status === 'FAILED' ||
                  d.processing_status === 'NEEDS_MANUAL_REVIEW',
              ).length
            } files`}
          />
        </Drawer>
      )}
    </div>
  )
}
