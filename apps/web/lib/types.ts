/**
 * Types mirrored from docs/spec/Shared-Integration-Contract.md.
 *
 * These are the CTO's contract-owned shapes. This file must not invent
 * fields the contract doesn't document. If the contract changes, this
 * file changes to match it -- never the other way around.
 */

// ---- Shared enums (contract §3) ----------------------------------------

export type CaseStatus =
  | "DRAFT"
  | "PROCESSING"
  | "IN_REVIEW"
  | "READY"
  | "EXPORTED"
  | "ARCHIVED";

export type DocumentType =
  | "QUESTIONNAIRE"
  | "UTILITY_BILL"
  | "POLICY"
  | "HR_DATA"
  | "WASTE_RECORD"
  | "SAFETY_RECORD"
  | "OTHER";

export type DocumentProcessingStatus =
  | "UPLOADED"
  | "PARSING"
  | "PARSED"
  | "INDEXED"
  | "FAILED"
  | "NEEDS_MANUAL_REVIEW";

export type EvidenceStatus =
  | "VERIFIED"
  | "PARTIAL"
  | "OUTDATED"
  | "CONFLICTING"
  | "MISSING"
  | "AI_SUGGESTED"
  | "NOT_APPLICABLE"
  | "NEEDS_MANUAL_REVIEW";

export type ReviewStatus =
  | "UNREVIEWED"
  | "HUMAN_CONFIRMED"
  | "REJECTED"
  | "NEEDS_REVISION";

export type ActionType = "SUBMISSION" | "IMPROVEMENT";

export type ActionStatus =
  | "TODO"
  | "IN_PROGRESS"
  | "BLOCKED"
  | "NEEDS_REVIEW"
  | "COMPLETED";

// ---- Source location contract (contract §4) ----------------------------

export type SourceLocation =
  | { type: "page"; page_number: number; bounding_box: unknown | null }
  | { type: "sheet_cell"; sheet_name: string; cell_range: string }
  | {
      type: "paragraph";
      heading_path: string[];
      paragraph_index: number;
    }
  | { type: "manual"; description: string };

// ---- Error envelope (contract §5) --------------------------------------

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id?: string;
  };
}

// ---- Response shapes (contract §7) -------------------------------------

export interface CaseSummary {
  id: string;
  title: string;
  customer_name: string;
  deadline_at: string | null;
  reporting_period: { start: string; end: string } | null;
  status: CaseStatus;
  readiness: {
    confirmed_required_questions: number;
    total_required_questions: number;
    percentage: number;
  };
  evidence_status_counts: Record<EvidenceStatus, number>;
  unconfirmed_answer_count: number;
  updated_at: string;
}

export interface DocumentRecord {
  id: string;
  case_id: string;
  original_filename: string;
  mime_type: string;
  size_bytes: number;
  sha256: string | null;
  document_type: DocumentType;
  processing_status: DocumentProcessingStatus;
  source_date: string | null;
  period_start: string | null;
  period_end: string | null;
  /** apps/api's DocumentRecord.error is a plain message string, not the
   * shared error envelope shape. */
  error: string | null;
  /** SPEC-AMD-001: the most recent processing_jobs row for this Document. */
  latest_job_id: string | null;
  created_at: string;
  /** Main Spec §17 Phase 3 "column-mapping confirmation UI": header name ->
   * spreadsheet column letter, as detected while parsing a QUESTIONNAIRE
   * document. Only present on the response to the upload/retry request
   * that actually parsed the file (server-side it is a transient,
   * non-persisted value) -- null on a later GET /documents, and always
   * null for a non-QUESTIONNAIRE document. */
  detected_columns: Record<string, string> | null;
}

export interface QuestionListItem {
  id: string;
  external_question_id: string | null;
  question_text: string;
  is_required: boolean;
  pillar: string | null;
  sedg_topic_code: string | null;
  sedg_disclosure_code: string | null;
  evidence_status: EvidenceStatus;
  review_status: ReviewStatus;
  priority_score: number | null;
  owner_name: string | null;
  source_location: SourceLocation | null;
  /** Human-readable reason behind the current evidence_status (e.g. how a
   * candidate match was found). Null until the backend has a reason to give. */
  status_reason: string | null;
  /** Server-resolved location of the most recent evidence candidate for this
   * question -- distinct from `source_location`, which is where the
   * QUESTION itself was found in the questionnaire, not where its evidence
   * was found. Never fabricated client-side. */
  evidence_location: SourceLocation | null;
  /** Draft rationale from ai_pipeline.map_question_to_sedg() for this
   * question's pillar/SEDG mapping -- a human-reviewable recommendation,
   * never a verdict. Must never be treated as equivalent to
   * evidence_status or review_status. */
  mapping_rationale: string | null;
  /** Quoted excerpt text and claim from the most recent evidence_links
   * candidate for this question -- the actual excerpt, not just its
   * location chip. Same AI-suggestion status as evidence_location. */
  evidence_excerpt: string | null;
  evidence_claim_supported: string | null;
}

// ---- Human Review (Main Spec §17 Phase 5) --------------------------------
//
// Verified live against apps/api commit 48dbcec ("feat(api): Phase 5
// backend -- human review and action tracking"), which landed mid-session
// while this frontend work was in progress -- these types mirror the
// actual running server's OpenAPI schema, not a guess. Confirmed by
// starting apps/api locally and reading /openapi.json; see the CEO
// handoff note for the exact reconciliation this produced against the
// still-unfrozen Shared-Integration-Contract.md.

/**
 * Human Review action on a question's draft answer. AGENTS.md §3: the AI
 * never owns a verdict -- this is the human action that converts an
 * unconfirmed draft into (or out of) a confirmed state. Matches
 * apps/api/app/enums.py REVIEW_ACTION exactly.
 */
export type ReviewAction = "ACCEPT" | "EDIT" | "REJECT" | "NOT_APPLICABLE";

export interface ReviewQuestionRequest {
  action: ReviewAction;
  /** The wire schema (QuestionReviewRequest) marks this nullable, but the
   * live route rejects a blank/missing reviewer_name with 422 for every
   * action -- kept required here so the client can't even attempt the
   * call without it. */
  reviewer_name: string;
  /** Required when action === "EDIT" (server 422s otherwise). */
  edited_answer?: string;
  /** Required when action === "REJECT" **and** action === "NOT_APPLICABLE"
   * (server 422s otherwise for both -- NOT_APPLICABLE needing a reason is
   * not what the orchestrating task assumed, but it's what the live route
   * enforces). */
  reason?: string;
}

export type DraftProvenance =
  | "NONE"
  | "AI_GENERATED"
  | "AI_ASSISTED_EDIT"
  | "USER_ENTERED";

/**
 * Response of POST /cases/{case_id}/questions/{question_id}/review --
 * mirrors apps/api's AnswerRecord schema exactly. Note this is NOT the
 * same shape as QuestionListItem: the list endpoint does not expose
 * draft_answer/confirmed_answer/reviewer_name/reviewed_at at all, so
 * there is currently no way for the frontend to preview a question's
 * draft answer before a reviewer takes an action on it (no
 * GET /questions/{id} detail endpoint is implemented, though the Contract
 * documents one) -- flagged as a gap for the CTO, not something this
 * frontend can route around.
 */
export interface AnswerRecord {
  id: string;
  question_id: string;
  draft_answer: string | null;
  confirmed_answer: string | null;
  evidence_status: EvidenceStatus;
  status_reason: string | null;
  review_status: ReviewStatus;
  review_reason: string | null;
  reviewer_name: string | null;
  reviewed_at: string | null;
  not_applicable_reason: string | null;
  draft_provenance: DraftProvenance;
  updated_at: string;
}

export interface ActionRecord {
  id: string;
  case_id: string;
  question_id: string | null;
  type: ActionType;
  title: string;
  owner_name: string | null;
  owner_role: string | null;
  next_step: string | null;
  deadline_at: string | null;
  status: ActionStatus;
  completion_note: string | null;
  /** REQ-033 / Gate P5: whether this Action cannot go to COMPLETED without
   * closure_evidence_link_id set. Confirmed live field (apps/api's
   * ActionRecord schema) -- server defaults it from the question's
   * evidence_status (MISSING/CONFLICTING) at creation time unless the
   * creator overrides it explicitly. */
  requires_closure_evidence: boolean;
  /** The evidence_links row id actually used to close this Action --
   * distinct from closure_evidence_document_id below, which is a resolved
   * document id for display. Completing an Action references this id, not
   * a raw document id. */
  closure_evidence_link_id: string | null;
  closure_evidence_document_id: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

// ---- Request bodies -----------------------------------------------------

export interface CreateCaseRequest {
  title: string;
  customer_name: string;
  deadline_at?: string | null;
  reporting_period?: { start: string; end: string } | null;
}

export interface CreateActionRequest {
  question_id: string;
  type: ActionType;
  title: string;
  owner_name: string;
  owner_role?: string | null;
  next_step: string;
  /** Gate P5: "An Action cannot be created without an owner, next step,
   * and deadline" -- required here; apps/api's create_action enforces the
   * same rule at 422 even though its ActionCreate wire schema marks these
   * fields nullable (nullable at the column level only so a pre-Phase-5
   * row is never invalidated). */
  deadline_at: string;
  /** Optional override of the server's default (question's evidence_status
   * in MISSING/CONFLICTING => true). Omit to let the server decide. */
  requires_closure_evidence?: boolean | null;
}

/**
 * Body of POST /cases/{case_id}/actions/{action_id}/status -- the real
 * completion/lifecycle endpoint (apps/api's ActionStatusUpdate schema).
 * NOT the `POST /actions/{action_id}/complete` shape
 * Shared-Integration-Contract.md §6 documents -- the CTO's implementation
 * uses a case-scoped, status-driven endpoint instead. Following the live
 * server here, not the unfrozen contract text.
 */
export interface UpdateActionStatusRequest {
  status: ActionStatus;
  /** Required by the server when status === "COMPLETED". */
  completion_note?: string | null;
  /** References an evidence_links row id, not a document id. Required by
   * the server when status === "COMPLETED" and the Action's
   * requires_closure_evidence is true. There is currently no endpoint
   * that lists evidence_links for a case/question, so the frontend has no
   * way to let a reviewer browse and pick one -- see the note on
   * ActionsKanban's completion form. */
  closure_evidence_link_id?: string | null;
}
