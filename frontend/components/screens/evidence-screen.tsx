'use client'

import {
  AlertTriangle,
  ArrowRight,
  Check,
  CircleHelp,
  Eye,
  RefreshCw,
  Table2,
  UploadCloud,
} from 'lucide-react'
import { useMemo, useRef, useState } from 'react'

import type { DocumentRecord, DocumentType } from '@/lib/api'
import {
  DOCUMENT_TYPES,
  documentTypeLabel,
  documentsNeedingAttention,
  errorMessage,
  isRetryable,
} from '@/lib/api'
import { MAX_UPLOAD_BYTES } from '@/lib/constants'
import { formatBytes, getFileKind, relativeTimeLabel } from '@/lib/format'

import {
  DocumentPill,
  Drawer,
  EmptyState,
  ErrorNotice,
  FileKindIcon,
  Key,
  Loading,
  NotAvailable,
  PageTitle,
  SearchField,
} from '../primitives'
import { DocumentPreview } from '../document-preview'

// Evidence cannot be dated in the future. A mistyped year — 2062 for 2026 —
// would otherwise read as the freshest document in the case forever, which is
// the one direction of error the staleness rule cannot catch.
const TODAY = new Date().toISOString().slice(0, 10)

const ACCEPTED =
  '.pdf,.doc,.docx,.xls,.xlsx,.csv,.txt,.png,.jpg,.jpeg,.gif,.webp,application/pdf,text/csv,text/plain,image/*'

/**
 * `GET/POST /api/v1/cases/{id}/documents` and the retry endpoint.
 *
 * `document_type` is a real, required part of the upload: it decides whether
 * the server parses the file as a questionnaire or indexes it as evidence. The
 * prototype had no such control, so it is added here rather than defaulting
 * silently.
 */
export function EvidenceScreen({
  caseId,
  documents,
  loading,
  error,
  busy,
  refresh,
  onUpload,
  onRetry,
  lastUpload,
  onDismissMapping,
}: {
  caseId: string
  documents: DocumentRecord[]
  loading: boolean
  error: unknown
  busy: boolean
  refresh: () => void
  onUpload: (file: File, documentType: DocumentType, sourceDate?: string) => Promise<void>
  onRetry: (documentId: string) => Promise<void>
  /** The most recent upload response, kept for its transient
   * `detected_columns` read-back. */
  lastUpload: DocumentRecord | null
  onDismissMapping: () => void
}) {
  const [documentType, setDocumentType] = useState<DocumentType>('OTHER')
  // Applies to the next batch, like `documentType` above — the date is a
  // property of the documents you are about to drop, not of the screen.
  const [sourceDate, setSourceDate] = useState('')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [previewId, setPreviewId] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [query, setQuery] = useState('')
  const [uploadError, setUploadError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement | null>(null)

  const selected = documents.find((d) => d.id === selectedId) ?? null
  const previewDoc = documents.find((d) => d.id === previewId) ?? null
  const attention = documentsNeedingAttention(documents)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return documents
    return documents.filter(
      (d) =>
        d.original_filename.toLowerCase().includes(q) ||
        documentTypeLabel(d.document_type).toLowerCase().includes(q),
    )
  }, [documents, query])

  async function upload(list: FileList | File[]) {
    const files = Array.from(list)
    if (files.length === 0) return
    setUploadError(null)
    for (const file of files) {
      if (file.size > MAX_UPLOAD_BYTES) {
        setUploadError(
          `${file.name} is ${formatBytes(file.size)}; the API limit is ${formatBytes(
            MAX_UPLOAD_BYTES,
          )}.`,
        )
        continue
      }
      try {
        await onUpload(file, documentType, sourceDate || undefined)
      } catch (err) {
        setUploadError(`${file.name}: ${errorMessage(err)}`)
      }
    }
  }

  return (
    <div>
      <PageTitle
        eyebrow="Evidence intake"
        title="Documents & evidence"
        desc="Files the server has stored, parsed and indexed for this case."
        actions={
          <>
            <button className="secondary" type="button" onClick={refresh}>
              <RefreshCw />
              Refresh
            </button>
            <button
              className="primary"
              type="button"
              disabled={busy}
              onClick={() => inputRef.current?.click()}
            >
              <UploadCloud />
              {busy ? 'Uploading…' : 'Upload evidence'}
            </button>
          </>
        }
      />

      {error ? <ErrorNotice message={errorMessage(error)} onRetry={refresh} /> : null}
      {uploadError ? <ErrorNotice message={uploadError} /> : null}

      <ColumnMappingReadback record={lastUpload} onDismiss={onDismissMapping} />

      <div className="toolbar">
        <label className="control select-control">
          Upload as
          <select
            value={documentType}
            onChange={(e) => setDocumentType(e.target.value as DocumentType)}
          >
            {DOCUMENT_TYPES.map((t) => (
              <option key={t} value={t}>
                {documentTypeLabel(t)}
              </option>
            ))}
          </select>
        </label>
        <label className="control date-control">
          Evidence dated
          <input
            type="date"
            value={sourceDate}
            max={TODAY}
            onChange={(e) => setSourceDate(e.target.value)}
            aria-describedby="source-date-hint"
          />
        </label>
        <SearchField placeholder="Search documents" value={query} onChange={setQuery} grow />
      </div>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ACCEPTED}
        style={{ display: 'none' }}
        onChange={(e) => {
          if (e.target.files) void upload(e.target.files)
          e.target.value = ''
        }}
      />
      <div
        className={`dropzone compact clickable${dragActive ? ' active' : ''}`}
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
          if (e.dataTransfer.files?.length) void upload(e.dataTransfer.files)
        }}
      >
        <UploadCloud />
        <div>
          <b>Drop supporting documents here</b>
          <span>
            Uploading as <strong>{documentTypeLabel(documentType)}</strong> ·{' '}
            <span id="source-date-hint">
              {sourceDate
                ? `dated ${sourceDate}`
                : 'undated — staleness cannot be assessed'}
            </span>{' '}
            · identical files are de-duplicated by checksum
          </span>
        </div>
      </div>

      <div className="section-head">
        <div>
          <h2>Evidence library</h2>
          <p>
            {documents.length} file{documents.length === 1 ? '' : 's'} ·{' '}
            {attention.length} need{attention.length === 1 ? 's' : ''} attention
          </p>
        </div>
      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th>Document</th>
              <th>Type</th>
              <th>Processing</th>
              <th>Size</th>
              <th>Uploaded</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {filtered.map((doc) => (
              <tr key={doc.id} className="clickable" onClick={() => setSelectedId(doc.id)}>
                <td>
                  <div className="cell-title">
                    <span className="file-icon">
                      <FileKindIcon kind={getFileKind(doc.original_filename, doc.mime_type)} />
                    </span>
                    <div>
                      <b>{doc.original_filename}</b>
                      <small>{doc.error ? doc.error : doc.mime_type}</small>
                    </div>
                  </div>
                </td>
                <td>{documentTypeLabel(doc.document_type)}</td>
                <td>
                  <DocumentPill value={doc.processing_status} />
                </td>
                <td>{formatBytes(doc.size_bytes)}</td>
                <td>{relativeTimeLabel(doc.created_at)}</td>
                <td>
                  <ArrowRight />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {loading && documents.length === 0 ? <Loading label="Loading documents…" /> : null}

        {!loading && filtered.length === 0 ? (
          <EmptyState
            icon={<UploadCloud />}
            title={documents.length === 0 ? 'No documents uploaded yet' : 'No documents match'}
          >
            {documents.length === 0
              ? 'Drop files above to store and index them against this case.'
              : 'Clear the search to see every document.'}
          </EmptyState>
        ) : null}
      </div>

      {selected && (
        <DocumentDrawer
          doc={selected}
          busy={busy}
          onRetry={onRetry}
          onPreview={() => setPreviewId(selected.id)}
          close={() => setSelectedId(null)}
        />
      )}

      {previewDoc ? (
        <DocumentPreview
          caseId={caseId}
          documentId={previewDoc.id}
          documentName={previewDoc.original_filename}
          onClose={() => setPreviewId(null)}
        />
      ) : null}
    </div>
  )
}

/**
 * Read-back of the columns the questionnaire parser actually used.
 *
 * `detected_columns` is transient server-side — it exists only on the response
 * to the upload that parsed the file, and is null on any later
 * `GET /documents`. So this is a confirmation that the parse read what you
 * expected, not an editable mapping: there is no endpoint to change it. If it
 * read the wrong columns, fix the spreadsheet and upload again.
 */
function ColumnMappingReadback({
  record,
  onDismiss,
}: {
  record: DocumentRecord | null
  onDismiss: () => void
}) {
  const columns = record?.detected_columns
  if (!record || !columns || Object.keys(columns).length === 0) return null

  return (
    <section className="panel mapping-readback">
      <div className="section-head">
        <div>
          <h2>
            <Table2 /> Columns detected in {record.original_filename}
          </h2>
          <p>
            What the parser read. Not editable — there is no mapping endpoint. If a column was read
            wrongly, correct the file and upload it again.
          </p>
        </div>
        <button className="link" type="button" onClick={onDismiss}>
          <Check />
          Looks right
        </button>
      </div>
      <div className="review-list">
        {Object.entries(columns).map(([header, column]) => (
          <Key key={header} label={header} value={`Column ${column}`} />
        ))}
      </div>
    </section>
  )
}

function DocumentDrawer({
  doc,
  busy,
  onRetry,
  onPreview,
  close,
}: {
  doc: DocumentRecord
  busy: boolean
  onRetry: (documentId: string) => Promise<void>
  onPreview: () => void
  close: () => void
}) {
  const [retryError, setRetryError] = useState<string | null>(null)
  const kind = getFileKind(doc.original_filename, doc.mime_type)
  const parsed = doc.processing_status === 'PARSED' || doc.processing_status === 'INDEXED'

  return (
    <Drawer eyebrow="Stored document" title={doc.original_filename} close={close}>
      <div className="doc-preview">
        <FileKindIcon kind={kind} />
        <b>{parsed ? 'Open this document' : 'Nothing was extracted'}</b>
        <span>
          {parsed
            ? 'See the text the server extracted, with the original file alongside it.'
            : 'Parsing produced no text, so there is nothing to match evidence against. The original file can still be downloaded.'}
        </span>
        <button className="primary" type="button" onClick={onPreview}>
          <Eye />
          Open preview
        </button>
      </div>

      <Key label="Type" value={documentTypeLabel(doc.document_type)} />
      <Key label="Processing" value={<DocumentPill value={doc.processing_status} />} />
      <Key label="Size" value={formatBytes(doc.size_bytes)} />
      <Key label="MIME type" value={doc.mime_type} />
      <Key label="Uploaded" value={relativeTimeLabel(doc.created_at)} />
      <Key
        label="Reporting period"
        value={
          doc.period_start || doc.period_end
            ? `${doc.period_start ?? '—'} to ${doc.period_end ?? '—'}`
            : <NotAvailable title="The server has not derived a period for this document" />
        }
      />
      <Key label="Checksum (SHA-256)" value={<code className="hash">{doc.sha256}</code>} />
      <Key
        label="Latest job"
        value={doc.latest_job_id ?? <NotAvailable title="No processing job recorded" />}
      />

      {doc.error ? (
        <div className="callout warning">
          <AlertTriangle />
          <div>
            <b>Processing failed</b>
            <p>{doc.error}</p>
          </div>
        </div>
      ) : null}

      {retryError ? <ErrorNotice message={retryError} /> : null}

      {isRetryable(doc.processing_status) ? (
        <button
          className="primary full"
          type="button"
          disabled={busy}
          onClick={async () => {
            setRetryError(null)
            try {
              await onRetry(doc.id)
              close()
            } catch (err) {
              setRetryError(errorMessage(err))
            }
          }}
        >
          <RefreshCw />
          {busy ? 'Retrying…' : 'Retry processing'}
        </button>
      ) : (
        <div className="callout info">
          <CircleHelp />
          <div>
            <b>Retry not available</b>
            <p>
              Only a document in <code>FAILED</code> or <code>NEEDS_MANUAL_REVIEW</code> can be
              retried. This one is <code>{doc.processing_status}</code>.
            </p>
          </div>
        </div>
      )}
    </Drawer>
  )
}
