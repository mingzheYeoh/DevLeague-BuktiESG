/**
 * Presentation of backend status values.
 *
 * The server owns every status in here. This module only decides how to spell
 * one and which colour token to give it — it never derives, upgrades or
 * softens a status (AGENTS.md §3.2). In particular there is no mapping that
 * turns anything into "verified" or "confirmed" on the client side.
 *
 * Tone strings are existing CSS classes in `app/globals.css` (`.pill.<tone>`).
 */
import type {
  ActionStatus,
  CaseStatus,
  DocumentProcessingStatus,
  DocumentType,
  EvidenceStatus,
  Pillar,
  ReviewStatus,
} from './types'

export type Tone =
  | 'neutral'
  | 'supported'
  | 'partial'
  | 'missing'
  | 'conflict'
  | 'outdated'
  | 'unreviewed'
  | 'confirmed'
  | 'rejected'
  | 'needs-review'
  | 'in-progress'
  | 'blocked'
  | 'open'
  | 'ready'
  | 'processing'
  | 'failed'
  | 'review'
  | 'warning'

/** `NEEDS_MANUAL_REVIEW` -> `Needs manual review`. */
export function statusLabel(value: string): string {
  const lower = value.toLowerCase().replace(/[_\s]+/g, ' ').trim()
  return lower.charAt(0).toUpperCase() + lower.slice(1)
}

const EVIDENCE_TONES: Record<EvidenceStatus, Tone> = {
  VERIFIED: 'supported',
  PARTIAL: 'partial',
  OUTDATED: 'outdated',
  CONFLICTING: 'conflict',
  MISSING: 'missing',
  NOT_APPLICABLE: 'unreviewed',
  NEEDS_MANUAL_REVIEW: 'review',
}

const REVIEW_TONES: Record<ReviewStatus, Tone> = {
  UNREVIEWED: 'unreviewed',
  HUMAN_CONFIRMED: 'confirmed',
  REJECTED: 'rejected',
  NEEDS_REVISION: 'needs-review',
}

const DOCUMENT_TONES: Record<DocumentProcessingStatus, Tone> = {
  UPLOADED: 'processing',
  PARSING: 'processing',
  PARSED: 'ready',
  INDEXED: 'ready',
  FAILED: 'failed',
  NEEDS_MANUAL_REVIEW: 'review',
}

const ACTION_TONES: Record<ActionStatus, Tone> = {
  TODO: 'open',
  IN_PROGRESS: 'in-progress',
  BLOCKED: 'blocked',
  NEEDS_REVIEW: 'needs-review',
  COMPLETED: 'confirmed',
}

const CASE_TONES: Record<CaseStatus, Tone> = {
  DRAFT: 'unreviewed',
  PROCESSING: 'processing',
  IN_REVIEW: 'partial',
  READY: 'ready',
  EXPORTED: 'confirmed',
  ARCHIVED: 'unreviewed',
}

export const evidenceTone = (s: EvidenceStatus): Tone => EVIDENCE_TONES[s] ?? 'neutral'
export const reviewTone = (s: ReviewStatus): Tone => REVIEW_TONES[s] ?? 'neutral'
export const documentTone = (s: DocumentProcessingStatus): Tone =>
  DOCUMENT_TONES[s] ?? 'neutral'
export const actionTone = (s: ActionStatus): Tone => ACTION_TONES[s] ?? 'neutral'
export const caseTone = (s: CaseStatus): Tone => CASE_TONES[s] ?? 'neutral'

/** Evidence statuses that represent an open coverage gap. Mirrors the
 * server's own grouping in `backend/app/routers/actions.py`
 * (MISSING/CONFLICTING require closure evidence) widened to the statuses a
 * reviewer would call a gap. Used for counting and filtering only — never to
 * change a status. */
export const GAP_EVIDENCE_STATUSES: EvidenceStatus[] = [
  'MISSING',
  'PARTIAL',
  'OUTDATED',
  'CONFLICTING',
  'NEEDS_MANUAL_REVIEW',
]

export function isEvidenceGap(status: EvidenceStatus): boolean {
  return GAP_EVIDENCE_STATUSES.includes(status)
}

const PILLAR_LABELS: Record<Pillar, string> = {
  E: 'Environmental',
  S: 'Social',
  G: 'Governance',
  UNCATEGORIZED: 'Uncategorised',
}

export const pillarLabel = (p: Pillar): string => PILLAR_LABELS[p] ?? 'Uncategorised'

export const PILLAR_ORDER: Pillar[] = ['E', 'S', 'G', 'UNCATEGORIZED']

const DOCUMENT_TYPE_LABELS: Record<DocumentType, string> = {
  QUESTIONNAIRE: 'Customer questionnaire',
  UTILITY_BILL: 'Utility bill',
  POLICY: 'Policy',
  HR_DATA: 'HR data',
  WASTE_RECORD: 'Waste record',
  SAFETY_RECORD: 'Safety record',
  OTHER: 'Other',
}

export const documentTypeLabel = (t: DocumentType): string =>
  DOCUMENT_TYPE_LABELS[t] ?? statusLabel(t)

/** Processing statuses the retry endpoint accepts; anything else gets a 409. */
export function isRetryable(status: DocumentProcessingStatus): boolean {
  return status === 'FAILED' || status === 'NEEDS_MANUAL_REVIEW'
}

/**
 * Render a server-resolved source location as a short human label.
 *
 * Only shapes the server actually emits are spelled out; anything else falls
 * back to the raw `type`. Never fabricates a page or cell reference that the
 * server did not send (AGENTS.md §3.3).
 */
export function sourceLocationLabel(
  location: ({ type: string } & Record<string, unknown>) | null,
): string {
  if (!location) return 'No source location'
  const get = (key: string) => location[key]

  switch (location.type) {
    case 'paragraph': {
      const path = get('heading_path')
      const index = get('paragraph_index')
      const heading = Array.isArray(path) && path.length ? path.join(' › ') : null
      const para = typeof index === 'number' ? `Paragraph ${index + 1}` : null
      return [heading, para].filter(Boolean).join(' · ') || 'Paragraph'
    }
    case 'page': {
      const page = get('page_number')
      return typeof page === 'number' ? `Page ${page}` : 'Page'
    }
    case 'sheet_cell': {
      const sheet = get('sheet_name')
      const range = get('cell_range')
      return [sheet ? `Sheet '${sheet}'` : null, range ? String(range) : null]
        .filter(Boolean)
        .join(' · ') || 'Spreadsheet cell'
    }
    case 'manual': {
      const description = get('description')
      return typeof description === 'string' && description ? description : 'Manual reference'
    }
    default:
      return statusLabel(location.type)
  }
}
