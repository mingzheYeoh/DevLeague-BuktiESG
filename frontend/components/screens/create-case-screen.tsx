'use client'

import { ArrowLeft, ArrowRight, Check, CircleHelp, UploadCloud, X } from 'lucide-react'
import { useRef, useState } from 'react'

import type { CreateCaseRequest } from '@/lib/api'
import { errorMessage } from '@/lib/api'
import { MAX_UPLOAD_BYTES } from '@/lib/constants'
import { dateInputToIso, formatBytes, formatDateLabel, getFileKind } from '@/lib/format'

import { ErrorNotice, FileKindIcon, Key, PageTitle } from '../primitives'

const STEPS = ['Case details', 'Reporting scope', 'Questionnaire', 'Review'] as const

/**
 * `POST /api/v1/cases`, optionally followed by a QUESTIONNAIRE upload.
 *
 * Only fields the server accepts are collected — `CaseCreate` is title,
 * customer_name, deadline_at and the two flat reporting-period dates. The
 * prototype's "Entity"/"Site" inputs are gone: there is no Organization
 * endpoint, so those values had nowhere to go.
 */
export function CreateCaseScreen({
  onCancel,
  onCreate,
  busy,
}: {
  onCancel: () => void
  onCreate: (body: CreateCaseRequest, questionnaire: File | null) => Promise<void>
  busy: boolean
}) {
  const [step, setStep] = useState(1)
  const [title, setTitle] = useState('')
  const [customer, setCustomer] = useState('')
  const [deadline, setDeadline] = useState('')
  const [periodStart, setPeriodStart] = useState('')
  const [periodEnd, setPeriodEnd] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const titleValid = title.trim().length > 0

  function pickFile(list: FileList | File[]) {
    const next = Array.from(list)[0]
    if (!next) return
    if (next.size > MAX_UPLOAD_BYTES) {
      setFileError(
        `${next.name} is ${formatBytes(next.size)}. The API rejects anything over ${formatBytes(
          MAX_UPLOAD_BYTES,
        )}.`,
      )
      return
    }
    setFileError(null)
    setFile(next)
  }

  async function submit() {
    setError(null)
    try {
      await onCreate(
        {
          title: title.trim(),
          customer_name: customer.trim() || null,
          deadline_at: dateInputToIso(deadline),
          reporting_period_start: periodStart || null,
          reporting_period_end: periodEnd || null,
        },
        file,
      )
    } catch (err) {
      setError(err)
    }
  }

  return (
    <div className="narrow">
      <button className="back" type="button" onClick={onCancel}>
        <ArrowLeft />
        Back to cases
      </button>
      <PageTitle
        eyebrow={`New case · Step ${step} of ${STEPS.length}`}
        title="Create a response case"
        desc="Set up the customer request and, if you have it, the questionnaire file."
      />
      <div className="steps">
        {STEPS.map((label, i) => (
          <div className={i + 1 <= step ? 'done' : ''} key={label}>
            <span>{i + 1 < step ? <Check /> : i + 1}</span>
            {label}
          </div>
        ))}
      </div>

      <section className="form-card">
        {error ? <ErrorNotice message={errorMessage(error)} /> : null}

        {step === 1 && (
          <>
            <h2>Case details</h2>
            <label>
              Case title <span aria-hidden="true">*</span>
              <input
                data-testid="case-title-input"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Major customer ESG questionnaire 2026"
                required
                aria-invalid={!titleValid && title.length > 0}
              />
            </label>
            {!titleValid && title.length > 0 && (
              <p className="field-hint">A title is required by the API.</p>
            )}
            <div className="form-grid">
              <label>
                Customer
                <input
                  data-testid="customer-name-input"
                  value={customer}
                  onChange={(e) => setCustomer(e.target.value)}
                  placeholder="Requesting customer"
                />
              </label>
              <label>
                Deadline
                <input
                  type="date"
                  value={deadline}
                  onChange={(e) => setDeadline(e.target.value)}
                />
              </label>
            </div>
            <div className="callout info">
              <CircleHelp />
              <div>
                <b>No owner field</b>
                <p>
                  A Case has no owner server-side. Owners are recorded per Action, where the API
                  requires one.
                </p>
              </div>
            </div>
          </>
        )}

        {step === 2 && (
          <>
            <h2>Reporting scope</h2>
            <div className="form-grid">
              <label>
                Period start
                <input
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                />
              </label>
              <label>
                Period end
                <input
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                />
              </label>
            </div>
            <p className="field-hint">
              Optional. The reporting period is stored on the Case and bounds what evidence counts
              as current.
            </p>
          </>
        )}

        {step === 3 && (
          <>
            <h2>Questionnaire</h2>
            {fileError ? <ErrorNotice message={fileError} /> : null}
            {!file && (
              <div
                className={`dropzone clickable${dragActive ? ' active' : ''}`}
                role="button"
                tabIndex={0}
                onClick={() => inputRef.current?.click()}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    inputRef.current?.click()
                  }
                }}
                onDragOver={(e) => {
                  e.preventDefault()
                  setDragActive(true)
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={(e) => {
                  e.preventDefault()
                  setDragActive(false)
                  if (e.dataTransfer.files?.length) pickFile(e.dataTransfer.files)
                }}
              >
                <UploadCloud />
                <b>Drop the customer questionnaire here</b>
                <span>
                  XLSX parses into questions · PDF, DOCX and CSV are stored and indexed · Max{' '}
                  {formatBytes(MAX_UPLOAD_BYTES)}
                </span>
              </div>
            )}
            <input
              ref={inputRef}
              type="file"
              accept=".pdf,.doc,.docx,.xls,.xlsx,.csv,.txt"
              style={{ display: 'none' }}
              onChange={(e) => {
                if (e.target.files?.length) pickFile(e.target.files)
                e.target.value = ''
              }}
            />
            {file && (
              <div className="uploaded">
                <FileKindIcon kind={getFileKind(file.name, file.type)} />
                <div>
                  <b>{file.name}</b>
                  <small>{formatBytes(file.size)}</small>
                </div>
                <button
                  className="icon-btn"
                  type="button"
                  aria-label="Remove file"
                  onClick={() => setFile(null)}
                >
                  <X />
                </button>
              </div>
            )}
            <p className="field-hint">
              Optional here — you can upload it later from the Evidence screen. Questions are
              extracted only from a spreadsheet with the expected header row; anything else is
              stored and flagged for manual review rather than silently producing zero questions.
            </p>
          </>
        )}

        {step === 4 && (
          <>
            <h2>Review case setup</h2>
            <div className="review-list">
              <Key label="Case title" value={title.trim() || '— required —'} />
              <Key label="Customer" value={customer.trim() || 'Not set'} />
              <Key label="Deadline" value={deadline ? formatDateLabel(deadline) : 'Not set'} />
              <Key
                label="Reporting period"
                value={
                  periodStart || periodEnd
                    ? `${periodStart ? formatDateLabel(periodStart) : '—'} to ${
                        periodEnd ? formatDateLabel(periodEnd) : '—'
                      }`
                    : 'Not set'
                }
              />
              <Key label="Questionnaire" value={file ? file.name : 'None — upload later'} />
            </div>
            <div className="callout info">
              <CircleHelp />
              <div>
                <b>Nothing is sent to your customer</b>
                <p>
                  This creates an internal response workspace. Uploading the questionnaire runs
                  parsing on the server straight away, so the result is visible immediately.
                </p>
              </div>
            </div>
          </>
        )}

        <div className="form-actions">
          <button
            className="secondary"
            type="button"
            disabled={step === 1 || busy}
            onClick={() => setStep(step - 1)}
          >
            Back
          </button>
          {step < STEPS.length ? (
            <button
              className="primary"
              type="button"
              data-testid="create-case-continue"
              disabled={step === 1 && !titleValid}
              onClick={() => setStep(step + 1)}
            >
              Continue
              <ArrowRight />
            </button>
          ) : (
            <button
              className="primary"
              type="button"
              data-testid="create-case-submit"
              disabled={!titleValid || busy}
              onClick={() => void submit()}
            >
              <Check />
              {busy ? 'Creating…' : 'Create case'}
            </button>
          )}
        </div>
      </section>
    </div>
  )
}
