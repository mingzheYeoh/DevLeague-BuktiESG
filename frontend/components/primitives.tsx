'use client'

/**
 * Shared presentational primitives.
 *
 * Class names match `app/globals.css`. Extracted from the original
 * single-file prototype so the screens stay readable.
 */
import {
  AlertTriangle,
  FileSpreadsheet,
  FileText,
  Image as ImageIcon,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  X,
} from 'lucide-react'
import type { ReactNode } from 'react'

import {
  actionTone,
  caseTone,
  documentTone,
  evidenceTone,
  reviewTone,
  statusLabel,
  type Tone,
} from '@/lib/api'
import type {
  ActionStatus,
  CaseStatus,
  DocumentProcessingStatus,
  EvidenceStatus,
  ReviewStatus,
} from '@/lib/api'
import type { FileKind } from '@/lib/format'

export function Mark() {
  return (
    <div className="mark" aria-hidden="true">
      <ShieldCheck />
    </div>
  )
}

export function Pill({
  children,
  tone = 'neutral',
}: {
  children: ReactNode
  tone?: Tone | string
}) {
  return <span className={`pill ${tone}`}>{children}</span>
}

/** A status straight from the server, spelled for humans. */
export function EvidencePill({ value }: { value: EvidenceStatus }) {
  return <Pill tone={evidenceTone(value)}>{statusLabel(value)}</Pill>
}

export function ReviewPill({ value }: { value: ReviewStatus }) {
  return <Pill tone={reviewTone(value)}>{statusLabel(value)}</Pill>
}

export function DocumentPill({ value }: { value: DocumentProcessingStatus }) {
  return <Pill tone={documentTone(value)}>{statusLabel(value)}</Pill>
}

export function ActionPill({ value }: { value: ActionStatus }) {
  return <Pill tone={actionTone(value)}>{statusLabel(value)}</Pill>
}

export function CasePill({ value }: { value: CaseStatus }) {
  return <Pill tone={caseTone(value)}>{statusLabel(value)}</Pill>
}

export function Meter({ value }: { value: number | null }) {
  const pct = value ?? 0
  return (
    <div className="meter" aria-label={value === null ? 'Not available' : `${pct}% complete`}>
      <span style={{ width: `${pct}%` }} />
    </div>
  )
}

export function SearchField({
  placeholder,
  value,
  onChange,
  grow = false,
}: {
  placeholder: string
  value: string
  onChange: (value: string) => void
  grow?: boolean
}) {
  return (
    <label className={`input${grow ? ' grow' : ''}`}>
      <Search />
      <input
        type="search"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  )
}

export function PageTitle({
  eyebrow,
  title,
  desc,
  actions,
}: {
  eyebrow?: string
  title: string
  desc: string
  actions?: ReactNode
}) {
  return (
    <div className="page-title">
      <div>
        {eyebrow && <div className="eyebrow">{eyebrow}</div>}
        <h1>{title}</h1>
        <p>{desc}</p>
      </div>
      {actions && <div className="title-actions">{actions}</div>}
    </div>
  )
}

export function Summary({
  label,
  value,
  sub,
  tone,
}: {
  label: string
  value: string
  sub: string
  tone?: string
}) {
  return (
    <div className="summary">
      <span>{label}</span>
      <strong className={tone}>{value}</strong>
      <small>{sub}</small>
    </div>
  )
}

export function Key({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="key">
      <span>{label}</span>
      <b>{value}</b>
    </div>
  )
}

export function Drawer({
  eyebrow = 'Details',
  title,
  close,
  children,
}: {
  eyebrow?: string
  title: string
  close: () => void
  children: ReactNode
}) {
  return (
    <div className="drawer-overlay" onClick={close}>
      <aside className="drawer" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-head">
          <div>
            <span>{eyebrow}</span>
            <h2>{title}</h2>
          </div>
          <button className="icon-btn" type="button" onClick={close} aria-label="Close">
            <X />
          </button>
        </div>
        {children}
      </aside>
    </div>
  )
}

export function FileKindIcon({ kind }: { kind: FileKind }) {
  if (kind === 'image') return <ImageIcon />
  if (kind === 'spreadsheet') return <FileSpreadsheet />
  return <FileText />
}

export function EmptyState({
  icon,
  title,
  children,
}: {
  icon: ReactNode
  title: string
  children?: ReactNode
}) {
  return (
    <div className="empty">
      {icon}
      <b>{title}</b>
      {children && <span>{children}</span>}
    </div>
  )
}

export function Loading({ label = 'Loading from the API…' }: { label?: string }) {
  return (
    <div className="empty" role="status" aria-live="polite">
      <Loader2 className="spin" />
      <b>{label}</b>
    </div>
  )
}

/**
 * An API failure, shown as itself.
 *
 * No silent fallback to sample data: a screen that cannot reach the server
 * says so, because quietly showing plausible-looking numbers in an
 * evidence-provenance tool is worse than showing nothing.
 */
export function ErrorNotice({
  message,
  onRetry,
}: {
  message: string
  onRetry?: () => void
}) {
  return (
    <div className="callout warning" role="alert">
      <AlertTriangle />
      <div>
        <b>Could not load this from the API</b>
        <p>{message}</p>
      </div>
      {onRetry && (
        <button className="link" type="button" onClick={onRetry}>
          <RefreshCw />
          Retry
        </button>
      )}
    </div>
  )
}

/** A value the backend does not provide yet. Named so it is obvious in the UI
 * that nothing was inferred to fill the hole. */
export function NotAvailable({ title }: { title?: string }) {
  return (
    <span className="not-available" title={title}>
      —
    </span>
  )
}
