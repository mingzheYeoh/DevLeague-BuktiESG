'use client'

import { AlertTriangle, Download, FileText, Loader2, X } from 'lucide-react'
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { DocumentChunkRecord, SourceLocation } from '@/lib/api'
import { api, errorMessage } from '@/lib/api'

/**
 * How the original file can be shown, if at all.
 *
 * Mirrors the server's inline allow-list in
 * `backend/app/routers/documents.py::_INLINE_CONTENT_TYPES` one-for-one. If that
 * list changes, this has to change with it: anything outside it comes back as an
 * `application/octet-stream` attachment, which an `<iframe>` would download
 * rather than display.
 */
type PreviewMode = 'pdf' | 'image' | 'text' | 'unsupported'

function previewMode(filename: string): PreviewMode {
  const name = filename.toLowerCase()
  if (name.endsWith('.pdf')) return 'pdf'
  if (/\.(png|jpe?g|gif|webp)$/.test(name)) return 'image'
  if (/\.(txt|csv)$/.test(name)) return 'text'
  return 'unsupported'
}

function fileTypeLabel(filename: string): string {
  const name = filename.toLowerCase()
  if (name.endsWith('.pdf')) return 'PDF'
  if (/\.(png|jpe?g|gif|webp)$/.test(name)) return 'Image'
  if (name.endsWith('.csv')) return 'CSV'
  if (name.endsWith('.txt')) return 'Plain text'
  if (/\.docx?$/.test(name)) return 'Word'
  if (/\.xlsx?$/.test(name)) return 'Excel'
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.slice(dot + 1).toUpperCase() : 'File'
}

/**
 * Full-screen preview of a stored document.
 *
 * Two views, because no single one works for every format:
 *
 *  - **Extracted text** (default) — the fragments the server parsed, with the
 *    cited one highlighted and scrolled to. Works for every supported format,
 *    and it is the text the evidence matcher actually read, so it is the right
 *    thing to check a citation against. A rendered original can differ from what
 *    extraction produced, and the citation rests on the extraction.
 *  - **Original file** — the bytes as uploaded. PDFs and images render inline;
 *    DOCX and XLSX cannot be rendered by a browser without pulling in a
 *    converter library, so those offer a download instead of pretending.
 *
 * The server decides inline vs attachment from an extension allow-list, so an
 * uploaded `.html` comes back as an opaque download rather than executing on the
 * API origin.
 */
export function DocumentPreview({
  caseId,
  documentId,
  documentName,
  highlightLocation,
  onClose,
}: {
  caseId: string
  documentId: string
  documentName: string
  /** The cited location, used to highlight and scroll to one fragment. */
  highlightLocation?: SourceLocation | null
  onClose: () => void
}) {
  const [view, setView] = useState<'text' | 'original'>('text')
  const [chunks, setChunks] = useState<DocumentChunkRecord[] | null>(null)
  const [error, setError] = useState<unknown>(null)

  const dialogRef = useRef<HTMLDivElement | null>(null)
  const highlightRef = useRef<HTMLLIElement | null>(null)
  const closeRef = useRef<HTMLButtonElement | null>(null)

  const mode = previewMode(documentName)
  const typeLabel = fileTypeLabel(documentName)
  const contentUrl = api.documentContentUrl(caseId, documentId)
  const downloadUrl = api.documentContentUrl(caseId, documentId, { download: true })

  useEffect(() => {
    let cancelled = false
    api
      .getDocumentChunks(caseId, documentId)
      .then((result) => {
        if (!cancelled) setChunks(result)
      })
      .catch((err) => {
        if (!cancelled) setError(err)
      })
    return () => {
      cancelled = true
    }
  }, [caseId, documentId])

  // Esc closes; Tab is kept inside the dialog.
  const onKeyDown = useCallback(
    (event: React.KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.stopPropagation()
        onClose()
        return
      }
      if (event.key !== 'Tab') return
      const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
        'button, [href], input, select, textarea, iframe, [tabindex]:not([tabindex="-1"])',
      )
      if (!focusable || focusable.length === 0) return
      const first = focusable[0]
      const last = focusable[focusable.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    },
    [onClose],
  )

  useEffect(() => {
    closeRef.current?.focus()
  }, [])

  const highlightIndex = useMemo(
    () => (chunks ? chunks.findIndex((c) => matchesLocation(c, highlightLocation)) : -1),
    [chunks, highlightLocation],
  )

  useEffect(() => {
    if (view !== 'text' || highlightIndex < 0) return
    highlightRef.current?.scrollIntoView({ block: 'center', behavior: 'smooth' })
  }, [view, highlightIndex, chunks])

  return (
    <div className="preview-overlay" onClick={onClose}>
      <div
        className="preview-dialog"
        role="dialog"
        aria-modal="true"
        aria-label={`Preview of ${documentName}`}
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        onKeyDown={onKeyDown}
      >
        <header className="preview-head">
          <div className="preview-title">
            <FileText aria-hidden="true" />
            <div>
              <b>{documentName}</b>
              <small>
                {typeLabel}
                {chunks
                  ? ` · ${chunks.length} extracted fragment${chunks.length === 1 ? '' : 's'}`
                  : ''}
              </small>
            </div>
          </div>

          <div className="preview-tabs" role="tablist" aria-label="Preview mode">
            <button
              type="button"
              role="tab"
              aria-selected={view === 'text'}
              className={view === 'text' ? 'active' : ''}
              onClick={() => setView('text')}
            >
              Extracted text
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={view === 'original'}
              className={view === 'original' ? 'active' : ''}
              onClick={() => setView('original')}
            >
              Original file
            </button>
          </div>

          <button
            className="icon-btn"
            type="button"
            onClick={onClose}
            aria-label="Close preview"
            ref={closeRef}
          >
            <X />
          </button>
        </header>

        <div className="preview-body">
          {view === 'text' ? (
            <ExtractedTextView
              chunks={chunks}
              error={error}
              highlightIndex={highlightIndex}
              highlightRef={highlightRef}
              hasLocation={Boolean(highlightLocation)}
            />
          ) : (
            <OriginalFileView
              mode={mode}
              typeLabel={typeLabel}
              url={contentUrl}
              documentName={documentName}
            />
          )}
        </div>

        <footer className="preview-foot">
          <span className="field-hint">
            {view === 'text'
              ? 'This is the text the evidence matcher read. A citation is checked against this, not against the rendered original.'
              : 'Served straight from storage. Formats a browser cannot render safely are offered as a download instead.'}
          </span>
          {/* No `download` attribute: it is ignored cross-origin, and this
              link points at the API on another origin. The server sends
              `Content-Disposition: attachment` for `?download=1`, which is
              what actually makes the browser save rather than navigate. */}
          <a className="secondary" href={downloadUrl}>
            <Download />
            Download original
          </a>
        </footer>
      </div>
    </div>
  )
}

function ExtractedTextView({
  chunks,
  error,
  highlightIndex,
  highlightRef,
  hasLocation,
}: {
  chunks: DocumentChunkRecord[] | null
  error: unknown
  highlightIndex: number
  highlightRef: React.RefObject<HTMLLIElement | null>
  hasLocation: boolean
}) {
  if (error) {
    return (
      <div className="callout warning" role="alert">
        <AlertTriangle />
        <div>
          <b>Could not load the parsed text</b>
          <p>{errorMessage(error)}</p>
        </div>
      </div>
    )
  }

  if (chunks === null) {
    return (
      <div className="preview-empty" role="status">
        <Loader2 className="spin" />
        <b>Loading the parsed text…</b>
      </div>
    )
  }

  if (chunks.length === 0) {
    return (
      <div className="preview-empty">
        <AlertTriangle />
        <b>Nothing was extracted from this file</b>
        <span>
          Parsing produced no text, so no evidence can be matched against it. The Evidence screen
          shows the reason and offers a retry.
        </span>
      </div>
    )
  }

  return (
    <>
      {hasLocation && highlightIndex < 0 ? (
        <p className="field-hint preview-note">
          The cited fragment could not be located in the current parse — the document may have been
          re-processed since the citation was made.
        </p>
      ) : null}
      <ol className="chunk-list">
        {chunks.map((chunk, index) => {
          const cited = index === highlightIndex
          return (
            <li
              key={chunk.id}
              className={cited ? 'chunk cited' : 'chunk'}
              ref={cited ? highlightRef : undefined}
              aria-current={cited ? 'true' : undefined}
            >
              <span className="chunk-locus">{chunkLocus(chunk)}</span>
              <p className="chunk-text">{chunk.text}</p>
              {cited ? <span className="chunk-badge">Cited here</span> : null}
            </li>
          )
        })}
      </ol>
    </>
  )
}

function OriginalFileView({
  mode,
  typeLabel,
  url,
  documentName,
}: {
  mode: PreviewMode
  typeLabel: string
  url: string
  documentName: string
}) {
  if (mode === 'unsupported') {
    return (
      <div className="preview-empty">
        <FileText />
        <b>A browser cannot display {typeLabel} files</b>
        <span>
          Rendering {typeLabel} in the page would need a converter library, which this build does
          not carry. Use <strong>Extracted text</strong> to check the citation — that view works for
          every format — or download the file to open it in its own application.
        </span>
        <a className="primary" href={url} download={documentName}>
          <Download />
          Download {documentName}
        </a>
      </div>
    )
  }

  if (mode === 'image') {
    return (
      <div className="preview-original">
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src={url} alt={`Original of ${documentName}`} />
      </div>
    )
  }

  return (
    <div className="preview-original">
      <iframe src={url} title={`Original of ${documentName}`} />
    </div>
  )
}

/** A short label for where a fragment sits, phrased for the format it came from. */
function chunkLocus(chunk: DocumentChunkRecord): string {
  if (chunk.page_number !== null) return `Page ${chunk.page_number}`
  if (chunk.sheet_name) {
    return chunk.cell_range ? `${chunk.sheet_name} · ${chunk.cell_range}` : chunk.sheet_name
  }
  if (chunk.heading_path.length > 0) return chunk.heading_path.join(' › ')
  return `Line ${chunk.sequence_no + 1}`
}

/**
 * Does this fragment correspond to the cited location?
 *
 * Exact, not heuristic: the server built each location from the very fragment
 * below, so the fields round-trip.
 */
function matchesLocation(
  chunk: DocumentChunkRecord,
  location: SourceLocation | null | undefined,
): boolean {
  if (!location) return false
  switch (location.type) {
    case 'page':
      return chunk.page_number === location.page_number
    case 'sheet_cell':
      return chunk.sheet_name === location.sheet_name && chunk.cell_range === location.cell_range
    case 'paragraph':
      return chunk.sequence_no === location.paragraph_index
    default:
      return false
  }
}
