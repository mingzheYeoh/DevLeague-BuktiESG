/**
 * Typed fetch wrapper for the Contract-shaped endpoints (see
 * docs/spec/Shared-Integration-Contract.md §6-7).
 *
 * The CTO's backend (apps/api) is being built in parallel and may not be
 * running yet. This client is written strictly against the documented
 * contract shapes -- it does not invent fields, and it never fabricates a
 * source location or evidence status client-side. Every value shown to the
 * user in this slice comes from whatever the API actually returns.
 */
import type {
  ActionRecord,
  AnswerRecord,
  ApiErrorBody,
  CaseSummary,
  CreateActionRequest,
  CreateCaseRequest,
  DocumentRecord,
  QuestionListItem,
  ReviewQuestionRequest,
  UpdateActionStatusRequest,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  details?: Record<string, unknown>;
  requestId?: string;
  status: number;

  constructor(status: number, body: ApiErrorBody) {
    super(body.error.message);
    this.name = "ApiError";
    this.status = status;
    this.code = body.error.code;
    this.details = body.error.details;
    this.requestId = body.error.request_id;
  }
}

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      Accept: "application/json",
      ...(init?.body && !(init.body instanceof FormData)
        ? { "Content-Type": "application/json" }
        : {}),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    let body: ApiErrorBody;
    try {
      body = (await res.json()) as ApiErrorBody;
    } catch {
      body = {
        error: {
          code: "INTERNAL_ERROR",
          message: `Request failed with status ${res.status}`,
        },
      };
    }
    throw new ApiError(res.status, body);
  }

  // 204 No Content, etc.
  if (res.status === 204) {
    return undefined as T;
  }

  return (await res.json()) as T;
}

export const api = {
  /** POST /api/v1/cases */
  createCase(body: CreateCaseRequest): Promise<CaseSummary> {
    return request<CaseSummary>("/api/v1/cases", {
      method: "POST",
      body: JSON.stringify(body),
    });
  },

  /** GET /api/v1/cases/{case_id} */
  getCase(caseId: string): Promise<CaseSummary> {
    return request<CaseSummary>(
      `/api/v1/cases/${encodeURIComponent(caseId)}`,
    );
  },

  /** POST /api/v1/cases/{case_id}/documents (multipart upload) */
  uploadDocument(caseId: string, file: File): Promise<DocumentRecord> {
    const form = new FormData();
    form.append("file", file);
    return request<DocumentRecord>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/documents`,
      {
        method: "POST",
        body: form,
      },
    );
  },

  /** GET /api/v1/cases/{case_id}/documents */
  getDocuments(caseId: string): Promise<DocumentRecord[]> {
    return request<DocumentRecord[]>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/documents`,
    );
  },

  /** POST /api/v1/cases/{case_id}/documents/{document_id}/retry */
  retryDocument(caseId: string, documentId: string): Promise<DocumentRecord> {
    return request<DocumentRecord>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/documents/${encodeURIComponent(documentId)}/retry`,
      { method: "POST" },
    );
  },

  /** GET /api/v1/cases/{case_id}/questions */
  getQuestions(caseId: string): Promise<QuestionListItem[]> {
    return request<QuestionListItem[]>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/questions`,
    );
  },

  /** POST /api/v1/cases/{case_id}/actions */
  createAction(
    caseId: string,
    body: CreateActionRequest,
  ): Promise<ActionRecord> {
    return request<ActionRecord>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/actions`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  },

  /** GET /api/v1/cases/{case_id}/actions (contract §6 "Priority and
   * Actions"; implemented in apps/api/app/routers/actions.py). */
  getActions(caseId: string): Promise<ActionRecord[]> {
    return request<ActionRecord[]>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/actions`,
    );
  },

  /** POST /api/v1/cases/{case_id}/actions/{action_id}/status (apps/api's
   * real Action lifecycle/completion endpoint -- NOT the
   * `POST /actions/{action_id}/complete` shape
   * Shared-Integration-Contract.md §6 documents; see the note on
   * UpdateActionStatusRequest in ./types.ts). Verified live. */
  updateActionStatus(
    caseId: string,
    actionId: string,
    body: UpdateActionStatusRequest,
  ): Promise<ActionRecord> {
    return request<ActionRecord>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/actions/${encodeURIComponent(actionId)}/status`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  },

  /** POST /api/v1/cases/{case_id}/questions/{question_id}/review
   * (apps/api's Human Review endpoint, Main Spec §17 Phase 5). Verified
   * live against apps/api commit 48dbcec -- returns AnswerRecord, not
   * QuestionListItem; see the note on AnswerRecord in ./types.ts for what
   * that does and doesn't expose. */
  reviewQuestion(
    caseId: string,
    questionId: string,
    body: ReviewQuestionRequest,
  ): Promise<AnswerRecord> {
    return request<AnswerRecord>(
      `/api/v1/cases/${encodeURIComponent(caseId)}/questions/${encodeURIComponent(questionId)}/review`,
      {
        method: "POST",
        body: JSON.stringify(body),
      },
    );
  },
};
