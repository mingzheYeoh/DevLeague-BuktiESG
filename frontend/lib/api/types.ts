/**
 * Wire types for the BuktiESG backend (`backend/`, FastAPI).
 *
 * These mirror what the server actually returns — `backend/app/schemas.py`
 * and `backend/app/enums.py` — not the still-unfrozen
 * `docs/spec/Shared-Integration-Contract.md`. Where the two disagree, this
 * file follows the running server, because that is what the browser will
 * receive. Divergences are called out inline so they stay visible instead of
 * quietly becoming "the contract".
 *
 * AGENTS.md §3.2/§3.3 apply to every type here: the frontend never computes
 * an `evidence_status`, never sets `review_status = HUMAN_CONFIRMED` on its
 * own, and never invents a source location. It renders what the server sends
 * and shows nothing where the server sends null.
 */

// ---- Enums (backend/app/enums.py) --------------------------------------
//
// These are plain Python tuples backing TEXT + CHECK columns server-side, so
// they never appear as enums in OpenAPI. They are transcribed here by hand
// and must be kept in step with enums.py.

export type CaseStatus =
  | 'DRAFT'
  | 'PROCESSING'
  | 'IN_REVIEW'
  | 'READY'
  | 'EXPORTED'
  | 'ARCHIVED'

export type DocumentType =
  | 'QUESTIONNAIRE'
  | 'UTILITY_BILL'
  | 'POLICY'
  | 'HR_DATA'
  | 'WASTE_RECORD'
  | 'SAFETY_RECORD'
  | 'OTHER'

export type DocumentProcessingStatus =
  | 'UPLOADED'
  | 'PARSING'
  | 'PARSED'
  | 'INDEXED'
  | 'FAILED'
  | 'NEEDS_MANUAL_REVIEW'

export type Pillar = 'E' | 'S' | 'G' | 'UNCATEGORIZED'

/** 7 values. `AI_SUGGESTED` was removed by SPEC-AMD-006 / RULING-03 — an AI
 * suggestion is never an evidence status. */
export type EvidenceStatus =
  | 'VERIFIED'
  | 'PARTIAL'
  | 'OUTDATED'
  | 'CONFLICTING'
  | 'MISSING'
  | 'NOT_APPLICABLE'
  | 'NEEDS_MANUAL_REVIEW'

export type ReviewStatus =
  | 'UNREVIEWED'
  | 'HUMAN_CONFIRMED'
  | 'REJECTED'
  | 'NEEDS_REVISION'

export type DraftProvenance =
  | 'NONE'
  | 'AI_GENERATED'
  | 'AI_ASSISTED_EDIT'
  | 'USER_ENTERED'

export type EvidenceLinkStatus =
  | 'CANDIDATE'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'INVALIDATED'

/** The human action that converts a draft into (or out of) a confirmed
 * state. The AI never owns a verdict — AGENTS.md §3.2. */
export type ReviewAction = 'ACCEPT' | 'EDIT' | 'REJECT' | 'NOT_APPLICABLE' | 'REOPEN'

export type ActionType = 'SUBMISSION' | 'IMPROVEMENT'

export type ActionStatus =
  | 'TODO'
  | 'IN_PROGRESS'
  | 'BLOCKED'
  | 'NEEDS_REVIEW'
  | 'COMPLETED'

export const DOCUMENT_TYPES: DocumentType[] = [
  'QUESTIONNAIRE',
  'UTILITY_BILL',
  'POLICY',
  'HR_DATA',
  'WASTE_RECORD',
  'SAFETY_RECORD',
  'OTHER',
]

export const ACTION_STATUSES: ActionStatus[] = [
  'TODO',
  'IN_PROGRESS',
  'BLOCKED',
  'NEEDS_REVIEW',
  'COMPLETED',
]

// ---- Source location ---------------------------------------------------

/**
 * A server-resolved location inside a stored document. Deliberately loose:
 * `backend/app/schemas.py::SourceLocation` is `extra="allow"` with only
 * `type` declared, and this slice only ever emits the `paragraph` and
 * `manual` shapes.
 *
 * This value always originates from `document_chunks` on the server. The AI
 * pipeline returns a `chunk_id` and nothing else (AGENTS.md §3.3), so a
 * location that reaches the browser cannot be a hallucinated one.
 */
export type SourceLocation = { type: string } & Record<string, unknown>

// ---- Error envelope ----------------------------------------------------

export interface ApiErrorDetail {
  code: string
  message: string
  details?: Record<string, unknown>
  request_id?: string | null
}

// ---- Responses ---------------------------------------------------------

/** `GET /api/v1/cases`, `GET /api/v1/cases/{id}`, `POST /api/v1/cases`.
 *
 * Flat and small on purpose. The Contract documents a richer CaseSummary
 * (nested `readiness`, `evidence_status_counts`, `reporting_period`); the
 * server does not send those. Readiness comes from its own endpoint, and the
 * status counts are derived in the browser from the questions list. */
export interface CaseSummary {
  id: string
  title: string
  customer_name: string | null
  deadline_at: string | null
  status: CaseStatus
  updated_at: string
  /** Set only while `status` is `ARCHIVED`. */
  archived_at: string | null
  /** The status the case held when it was archived, so a restore can name its
   * target instead of offering an unlabelled undo. Null unless archived. */
  status_before_archive: CaseStatus | null
}

/** `GET /api/v1/cases/{id}/readiness`. Computed server-side from the
 * protected readiness formula (AGENTS.md §3.5) — never recomputed here. */
export interface ReadinessSummary {
  confirmed_required_questions: number
  total_required_questions: number
  percentage: number
}

export interface DocumentRecord {
  id: string
  case_id: string
  original_filename: string
  mime_type: string
  size_bytes: number
  sha256: string
  document_type: DocumentType
  processing_status: DocumentProcessingStatus
  source_date: string | null
  period_start: string | null
  period_end: string | null
  /** A plain failure message, not the shared error envelope. */
  error: string | null
  latest_job_id: string | null
  created_at: string
  /** Header name -> spreadsheet column letter, detected while parsing a
   * QUESTIONNAIRE. Transient server-side: present only on the response to
   * the upload/retry call that actually parsed the file, null on any later
   * `GET /documents`. */
  detected_columns: Record<string, string> | null
}

export interface QuestionListItem {
  id: string
  external_question_id: string | null
  question_text: string
  is_required: boolean
  pillar: Pillar
  sedg_topic_code: string | null
  sedg_disclosure_code: string | null
  evidence_status: EvidenceStatus
  review_status: ReviewStatus
  /** Always null in this slice — the priority formula is a protected value
   * (AGENTS.md §3.5) and is not implemented server-side yet. The UI shows
   * "not scored" rather than inventing a number. */
  priority_score: number | null
  /** Always null in this slice. */
  owner_name: string | null
  /** Where the QUESTION was found in the questionnaire. */
  source_location: SourceLocation | null
  /** The audit sentence. Complete, precise, and too long to put in front of a
   * reviewer — use `status_points` for that and keep this for the detail view
   * and the export. */
  status_reason: string | null
  /**
   * The same findings as `status_reason`, as short separate phrases.
   *
   * Derived server-side by the rule engine from the persisted findings, so the
   * browser never parses prose to work out why a status was reached. Empty for
   * `VERIFIED` (the status already says it) and empty when the server sent no
   * findings.
   */
  status_points: string[]
  /** Where this question's most recent candidate EVIDENCE was found —
   * a different thing from `source_location`. */
  evidence_location: SourceLocation | null
  /** Draft rationale for the pillar/SEDG mapping. A reviewable
   * recommendation, never a verdict. */
  mapping_rationale: string | null
  evidence_excerpt: string | null
  evidence_claim_supported: string | null
  /** Which document the excerpt came out of. A location like "Paragraph 8" is
   * meaningless without it. */
  evidence_document_id: string | null
  evidence_document_name: string | null
  /** Which evidence_links row the fields above describe. `/accept` and
   *  `/invalidate` are both addressed by it, so a screen showing a citation
   *  it cannot name cannot act on it. */
  evidence_link_id: string | null
  /** Who vouched for that link, if anyone. Acceptance is the sixth
   *  VERIFIED condition and the only one a human owns. */
  evidence_accepted_by: string | null
  /** Total candidate links on this question. The `evidence_*` fields above
   * describe exactly one of them, so this has to be shown — otherwise the UI
   * implies the excerpt is the only evidence. */
  evidence_candidate_count: number
}

/** Response of the review endpoint. Not the same shape as
 * `QuestionListItem`: the list endpoint exposes no draft/confirmed answer
 * text at all, and there is no question-detail endpoint, so a reviewer
 * cannot preview a draft answer before acting on it. Gap in the backend,
 * not something the frontend can route around. */
export interface AnswerRecord {
  id: string
  question_id: string
  draft_answer: string | null
  confirmed_answer: string | null
  evidence_status: EvidenceStatus
  status_reason: string | null
  review_status: ReviewStatus
  review_reason: string | null
  reviewer_name: string | null
  reviewed_at: string | null
  not_applicable_reason: string | null
  draft_provenance: DraftProvenance
  updated_at: string
}

export interface ActionRecord {
  id: string
  case_id: string
  question_id: string | null
  type: ActionType
  title: string
  owner_name: string | null
  owner_role: string | null
  next_step: string | null
  deadline_at: string | null
  status: ActionStatus
  completion_note: string | null
  /** True when this Action cannot reach COMPLETED without a valid
   * `closure_evidence_link_id`. Derived server-side at creation from the
   * linked question's evidence_status (MISSING/CONFLICTING). */
  requires_closure_evidence: boolean
  closure_evidence_link_id: string | null
  closure_evidence_document_id: string | null
  created_at: string
  updated_at: string
  completed_at: string | null
}

/**
 * One parsed fragment of a stored document.
 *
 * Every format ends up here, which makes this the one preview that works for
 * all of them — and it is the text the evidence matcher actually read, so it is
 * what a citation should be checked against. A rendered original can look
 * different from what extraction produced.
 */
export interface DocumentChunkRecord {
  id: string
  sequence_no: number
  text: string
  /** Set for PDFs (1-based). */
  page_number: number | null
  /** Set for spreadsheets. */
  sheet_name: string | null
  cell_range: string | null
  /** Set for DOCX: the stack of enclosing headings. */
  heading_path: string[]
}

export interface EvidenceLinkRecord {
  id: string
  question_id: string
  document_id: string
  link_status: EvidenceLinkStatus
  value: string | null
  scope_description: string | null
  period_start: string | null
  period_end: string | null
  accepted_by: string | null
  accepted_at: string | null
}

// ---- Request bodies ----------------------------------------------------

export interface CreateCaseRequest {
  title: string
  customer_name?: string | null
  /** ISO 8601 datetime. */
  deadline_at?: string | null
  /** ISO 8601 date (YYYY-MM-DD). Flat fields, not a nested
   * `reporting_period` object — that is what the server accepts. */
  reporting_period_start?: string | null
  reporting_period_end?: string | null
}

export interface ReviewQuestionRequest {
  action: ReviewAction
  /** Required when action is EDIT. */
  edited_answer?: string
  /** Required when action is REJECT, NOT_APPLICABLE or REOPEN. */
  reason?: string
}

export interface CreateActionRequest {
  question_id?: string | null
  type: ActionType
  title: string
  /** Gate P5: an Action cannot exist without an owner, a next step and a
   * deadline. The wire schema marks these nullable (so pre-Phase-5 rows stay
   * valid) but the route 422s without them, so they are required here. */
  owner_name: string
  owner_role?: string | null
  next_step: string
  deadline_at: string
  /** Omit to let the server derive it from the question's evidence_status. */
  requires_closure_evidence?: boolean | null
}

export interface UpdateActionStatusRequest {
  status: ActionStatus
  /** Required by the server when status is COMPLETED. */
  completion_note?: string | null
  /** An `evidence_links` row id, not a document id. Required when status is
   * COMPLETED and the Action has requires_closure_evidence. */
  closure_evidence_link_id?: string | null
}

// ---- Authentication -----------------------------------------------------

/** `GET /api/v1/auth/me` — the signed-in actor, from `ActorSummary` in
 * `backend/app/schemas.py`. */
export interface ActorSummary {
  user_id: string
  email: string
  organization_id: string
  organization_name: string
  role: string
}

/** `POST /api/v1/auth/login` */
export interface LoginRequest {
  email: string
  password: string
}

/** `POST /api/v1/auth/register`
 *
 * `password` is rejected by the server below 12 characters
 * (`RegistrationRequest.password = Field(min_length=12)`). */
export interface RegistrationRequest {
  email: string
  password: string
  organization_name: string
}
