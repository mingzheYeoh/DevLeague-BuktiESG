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
  ApiErrorBody,
  CaseSummary,
  CreateActionRequest,
  CreateCaseRequest,
  DocumentRecord,
  QuestionListItem,
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
};
