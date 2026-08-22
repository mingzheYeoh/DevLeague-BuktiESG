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

export interface ActionRecord {
  id: string;
  case_id: string;
  question_id: string;
  type: ActionType;
  title: string;
  owner_name: string;
  owner_role: string | null;
  next_step: string;
  deadline_at: string | null;
  status: ActionStatus;
  completion_note: string | null;
  closure_evidence_document_id: string | null;
  created_at: string;
  updated_at: string;
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
  deadline_at?: string | null;
}
