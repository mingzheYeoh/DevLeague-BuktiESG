/**
 * Typed fetch client for the BuktiESG backend.
 *
 * One function per real route in `backend/app/routers/**`. Nothing here
 * invents a field, a status or a source location — if the server does not
 * send it, the UI does without it.
 */
import type {
  ActionRecord,
  AnswerRecord,
  ApiErrorDetail,
  CaseSummary,
  CreateActionRequest,
  CreateCaseRequest,
  DocumentChunkRecord,
  DocumentRecord,
  DocumentType,
  EvidenceLinkRecord,
  QuestionListItem,
  ReadinessSummary,
  ReviewQuestionRequest,
  UpdateActionStatusRequest,
} from './types'

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

/**
 * A failed API call, normalised across the three error shapes the server can
 * produce.
 */
export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: Record<string, unknown>
  readonly requestId: string | null

  constructor(status: number, detail: ApiErrorDetail) {
    super(detail.message)
    this.name = 'ApiError'
    this.status = status
    this.code = detail.code
    this.details = detail.details ?? {}
    this.requestId = detail.request_id ?? null
  }

  /** Field names the server rejected, when it told us (`missing_fields`). */
  get missingFields(): string[] {
    const raw = this.details.missing_fields
    return Array.isArray(raw) ? raw.map(String) : []
  }

  /** Allowed values, when the server rejected an enum (`allowed`). */
  get allowedValues(): string[] {
    const raw = this.details.allowed
    return Array.isArray(raw) ? raw.map(String) : []
  }
}

/** True when the backend could not be reached at all (server down, wrong
 * NEXT_PUBLIC_API_BASE_URL, CORS). Worth distinguishing from a 4xx, because
 * the fix is completely different. */
export class ApiUnreachableError extends Error {
  readonly cause?: unknown

  constructor(baseUrl: string, cause?: unknown) {
    super(
      `Could not reach the BuktiESG API at ${baseUrl}. Start the backend ` +
        `(uv run uvicorn app.main:app --reload) or check NEXT_PUBLIC_API_BASE_URL.`,
    )
    this.name = 'ApiUnreachableError'
    this.cause = cause
  }
}

/**
 * The server produces three different error bodies, and the browser has to
 * cope with all of them:
 *
 * 1. `{ detail: { error: {...} } }` — the project envelope, nested under
 *    `detail` because `errors.py` raises it as `HTTPException(detail=...)`.
 * 2. `{ detail: [ {loc, msg, ...} ] }` — FastAPI's own request-validation
 *    failure (e.g. a missing multipart `file`).
 * 3. Anything else / unparseable — a proxy error page, a 500 traceback.
 */
function normaliseError(status: number, body: unknown): ApiErrorDetail {
  if (body && typeof body === 'object') {
    const detail = (body as { detail?: unknown }).detail

    if (detail && typeof detail === 'object' && !Array.isArray(detail)) {
      const inner = (detail as { error?: unknown }).error
      if (inner && typeof inner === 'object') {
        return inner as ApiErrorDetail
      }
    }

    // Some deployments unwrap `detail`; accept the bare envelope too.
    const bare = (body as { error?: unknown }).error
    if (bare && typeof bare === 'object') {
      return bare as ApiErrorDetail
    }

    if (Array.isArray(detail)) {
      const message = detail
        .map((item) => {
          if (!item || typeof item !== 'object') return String(item)
          const loc = (item as { loc?: unknown[] }).loc
          const msg = (item as { msg?: unknown }).msg
          const field = Array.isArray(loc) ? loc.filter((p) => p !== 'body').join('.') : ''
          return field ? `${field}: ${msg}` : String(msg)
        })
        .join('; ')
      return {
        code: 'VALIDATION_ERROR',
        message: message || 'The request was rejected as invalid.',
        details: { fastapi_validation: detail },
      }
    }
  }

  return {
    code: 'INTERNAL_ERROR',
    message: `Request failed with status ${status}.`,
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const isFormData =
    typeof FormData !== 'undefined' && init?.body instanceof FormData

  let res: Response
  try {
    res = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        Accept: 'application/json',
        // Let the browser set the multipart boundary itself.
        ...(init?.body && !isFormData ? { 'Content-Type': 'application/json' } : {}),
        ...init?.headers,
      },
    })
  } catch (cause) {
    throw new ApiUnreachableError(API_BASE_URL, cause)
  }

  if (!res.ok) {
    let body: unknown = null
    try {
      body = await res.json()
    } catch {
      // Leave body null; normaliseError falls back to the status code.
    }
    throw new ApiError(res.status, normaliseError(res.status, body))
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

const enc = encodeURIComponent

export const api = {
  /** GET /health */
  health(): Promise<{ status: string }> {
    return request<{ status: string }>('/health')
  },

  // ---- Cases -----------------------------------------------------------

  /** GET /api/v1/cases */
  listCases(): Promise<CaseSummary[]> {
    return request<CaseSummary[]>('/api/v1/cases')
  },

  /** POST /api/v1/cases */
  createCase(body: CreateCaseRequest): Promise<CaseSummary> {
    return request<CaseSummary>('/api/v1/cases', {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  /** GET /api/v1/cases/{case_id} */
  getCase(caseId: string): Promise<CaseSummary> {
    return request<CaseSummary>(`/api/v1/cases/${enc(caseId)}`)
  },

  /** POST /api/v1/cases/{case_id}/archive
   *
   * Retires a case without destroying anything. Refused with 409
   * CASE_ALREADY_ARCHIVED if it is already archived. */
  archiveCase(caseId: string): Promise<CaseSummary> {
    return request<CaseSummary>(`/api/v1/cases/${enc(caseId)}/archive`, { method: 'POST' })
  },

  /** POST /api/v1/cases/{case_id}/unarchive
   *
   * Restores the status the case held before it was archived. Refused with 409
   * CASE_NOT_ARCHIVED if it is not archived. */
  unarchiveCase(caseId: string): Promise<CaseSummary> {
    return request<CaseSummary>(`/api/v1/cases/${enc(caseId)}/unarchive`, { method: 'POST' })
  },

  /** DELETE /api/v1/cases/{case_id} — 204, no body.
   *
   * Permanent, and cascades to the case's documents, questions, answers,
   * actions and stored files. The server refuses it with 409
   * CASE_NOT_DELETABLE unless the case is DRAFT or ARCHIVED; the error details
   * carry `deletable_from`, so the caller can say "archive it first". */
  deleteCase(caseId: string): Promise<void> {
    return request<void>(`/api/v1/cases/${enc(caseId)}`, { method: 'DELETE' })
  },

  /** GET /api/v1/cases/{case_id}/readiness */
  getReadiness(caseId: string): Promise<ReadinessSummary> {
    return request<ReadinessSummary>(`/api/v1/cases/${enc(caseId)}/readiness`)
  },

  // ---- Documents -------------------------------------------------------

  /** POST /api/v1/cases/{case_id}/documents (multipart: file, document_type)
   *
   * Re-uploading identical bytes to the same Case returns the existing
   * Document rather than creating a duplicate (checksum de-duplication), so
   * this is safe to retry. */
  uploadDocument(
    caseId: string,
    file: File,
    documentType: DocumentType = 'OTHER',
  ): Promise<DocumentRecord> {
    const form = new FormData()
    form.append('file', file)
    form.append('document_type', documentType)
    return request<DocumentRecord>(`/api/v1/cases/${enc(caseId)}/documents`, {
      method: 'POST',
      body: form,
    })
  },

  /** GET /api/v1/cases/{case_id}/documents */
  listDocuments(caseId: string): Promise<DocumentRecord[]> {
    return request<DocumentRecord[]>(`/api/v1/cases/${enc(caseId)}/documents`)
  },

  /** GET /api/v1/cases/{case_id}/documents/{document_id}/chunks
   *
   * The document as the server parsed it. Empty for a document that failed to
   * parse — its `error` field says why. */
  getDocumentChunks(caseId: string, documentId: string): Promise<DocumentChunkRecord[]> {
    return request<DocumentChunkRecord[]>(
      `/api/v1/cases/${enc(caseId)}/documents/${enc(documentId)}/chunks`,
    )
  },

  /** URL of GET /api/v1/cases/{case_id}/documents/{document_id}/content.
   *
   * A URL rather than a fetch, because the point is to hand it to `<iframe>`,
   * `<img>` or a download link. The server decides inline vs attachment from an
   * extension allow-list, so pointing a browser at this is safe even for an
   * uploaded `.html` — it comes back as an opaque download. */
  /** A direct URL to the stored bytes.
   *
   * Pass `download` for a save rather than a preview. The `download`
   * attribute on an `<a>` is ignored cross-origin, and this API is on a
   * different origin from the app, so a plain link to a PDF or image opens it
   * in the tab and throws away the app's state. `?download=1` makes the
   * server send `Content-Disposition: attachment` instead. */
  documentContentUrl(
    caseId: string,
    documentId: string,
    options: { download?: boolean } = {},
  ): string {
    const base = `${API_BASE_URL}/api/v1/cases/${enc(caseId)}/documents/${enc(documentId)}/content`
    return options.download ? `${base}?download=1` : base
  },

  /** POST /api/v1/cases/{case_id}/documents/{document_id}/retry
   *
   * Only valid while processing_status is FAILED or NEEDS_MANUAL_REVIEW;
   * anything else returns 409 DOCUMENT_NOT_RETRYABLE. */
  retryDocument(caseId: string, documentId: string): Promise<DocumentRecord> {
    return request<DocumentRecord>(
      `/api/v1/cases/${enc(caseId)}/documents/${enc(documentId)}/retry`,
      { method: 'POST' },
    )
  },

  // ---- Questions -------------------------------------------------------

  /** GET /api/v1/cases/{case_id}/questions */
  listQuestions(caseId: string): Promise<QuestionListItem[]> {
    return request<QuestionListItem[]>(`/api/v1/cases/${enc(caseId)}/questions`)
  },

  /** POST /api/v1/cases/{case_id}/questions/{question_id}/review
   *
   * The human review verdict. Returns an AnswerRecord, so the caller must
   * refetch the questions list to pick up any recomputed evidence status. */
  reviewQuestion(
    caseId: string,
    questionId: string,
    body: ReviewQuestionRequest,
  ): Promise<AnswerRecord> {
    return request<AnswerRecord>(
      `/api/v1/cases/${enc(caseId)}/questions/${enc(questionId)}/review`,
      { method: 'POST', body: JSON.stringify(body) },
    )
  },

  // ---- Actions ---------------------------------------------------------

  /** POST /api/v1/cases/{case_id}/actions */
  createAction(caseId: string, body: CreateActionRequest): Promise<ActionRecord> {
    return request<ActionRecord>(`/api/v1/cases/${enc(caseId)}/actions`, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },

  /** GET /api/v1/cases/{case_id}/actions */
  listActions(caseId: string): Promise<ActionRecord[]> {
    return request<ActionRecord[]>(`/api/v1/cases/${enc(caseId)}/actions`)
  },

  /** POST /api/v1/cases/{case_id}/actions/{action_id}/status */
  updateActionStatus(
    caseId: string,
    actionId: string,
    body: UpdateActionStatusRequest,
  ): Promise<ActionRecord> {
    return request<ActionRecord>(
      `/api/v1/cases/${enc(caseId)}/actions/${enc(actionId)}/status`,
      { method: 'POST', body: JSON.stringify(body) },
    )
  },

  // ---- Evidence links --------------------------------------------------

  /** POST /api/v1/cases/{case_id}/evidence-links/{id}/invalidate
   *
   * Cascades server-side: reopens any COMPLETED Action closed by this link
   * and recomputes the owning Answer's evidence status. Refetch questions and
   * actions afterwards. */
  invalidateEvidenceLink(
    caseId: string,
    evidenceLinkId: string,
  ): Promise<EvidenceLinkRecord> {
    return request<EvidenceLinkRecord>(
      `/api/v1/cases/${enc(caseId)}/evidence-links/${enc(evidenceLinkId)}/invalidate`,
      { method: 'POST' },
    )
  },
}

export type Api = typeof api
