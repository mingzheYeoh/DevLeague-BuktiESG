'use client'

/**
 * React data layer over `client.ts`.
 *
 * Deliberately plain: `useState` + `useEffect` + explicit refetch, no query
 * library. Every mutation refetches the collections the server may have
 * changed, because several endpoints cascade (invalidating an evidence link
 * reopens Actions; a review recomputes an Answer's evidence status), and
 * guessing the new state client-side would mean inventing statuses.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { ApiError, ApiUnreachableError, api } from './client'
import type {
  ActionRecord,
  AnswerRecord,
  CaseSummary,
  CreateActionRequest,
  CreateCaseRequest,
  DocumentRecord,
  DocumentType,
  QuestionListItem,
  ReadinessSummary,
  ReviewQuestionRequest,
  UpdateActionStatusRequest,
} from './types'

/** A user-facing message for anything the API layer can throw. */
export function errorMessage(error: unknown): string {
  if (error instanceof ApiUnreachableError) return error.message
  if (error instanceof ApiError) {
    const missing = error.missingFields
    if (missing.length) return `${error.message} (missing: ${missing.join(', ')})`
    const allowed = error.allowedValues
    if (allowed.length) return `${error.message} (allowed: ${allowed.join(', ')})`
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Something went wrong.'
}

export function isUnreachable(error: unknown): boolean {
  return error instanceof ApiUnreachableError
}

/** Backend reachability, so the UI can say "the API is down" instead of
 * silently rendering an empty workspace. */
export function useApiHealth() {
  const [online, setOnline] = useState<boolean | null>(null)

  const check = useCallback(() => {
    let cancelled = false
    api
      .health()
      .then(() => {
        if (!cancelled) setOnline(true)
      })
      .catch(() => {
        if (!cancelled) setOnline(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => check(), [check])

  return { online, recheck: check }
}

// ---- Cases -------------------------------------------------------------

export function useCases() {
  const [cases, setCases] = useState<CaseSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<unknown>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    try {
      setCases(await api.listCases())
      setError(null)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void reload()
  }, [reload])

  const createCase = useCallback(
    async (body: CreateCaseRequest): Promise<CaseSummary> => {
      const created = await api.createCase(body)
      // Optimistic insert plus a reload: the insert keeps the new Case
      // visible immediately, the reload keeps the list authoritative.
      setCases((prev) => [created, ...prev.filter((c) => c.id !== created.id)])
      void reload()
      return created
    },
    [reload],
  )

  /** Replace one row from the server's response. No optimistic write: archiving
   * changes three fields at once (`status`, `archived_at`,
   * `status_before_archive`) and the server is the only thing that knows what
   * `status_before_archive` should be. */
  const replace = useCallback((updated: CaseSummary) => {
    setCases((prev) => prev.map((c) => (c.id === updated.id ? updated : c)))
  }, [])

  const archiveCase = useCallback(
    async (caseId: string): Promise<CaseSummary> => {
      const updated = await api.archiveCase(caseId)
      replace(updated)
      return updated
    },
    [replace],
  )

  const unarchiveCase = useCallback(
    async (caseId: string): Promise<CaseSummary> => {
      const updated = await api.unarchiveCase(caseId)
      replace(updated)
      return updated
    },
    [replace],
  )

  /** Drops the row locally on success. The reload that follows is what proves
   * it: if the delete did not take, the row comes straight back. */
  const deleteCase = useCallback(
    async (caseId: string): Promise<void> => {
      await api.deleteCase(caseId)
      setCases((prev) => prev.filter((c) => c.id !== caseId))
      void reload()
    },
    [reload],
  )

  return { cases, loading, error, reload, createCase, archiveCase, unarchiveCase, deleteCase }
}

// ---- One case's workspace ----------------------------------------------

export interface CaseWorkspace {
  caseSummary: CaseSummary | null
  readiness: ReadinessSummary | null
  questions: QuestionListItem[]
  documents: DocumentRecord[]
  actions: ActionRecord[]
  loading: boolean
  /** True while a mutation is in flight. */
  busy: boolean
  error: unknown
  refresh: () => Promise<void>
  uploadDocument: (
    file: File,
    documentType: DocumentType,
    sourceDate?: string,
  ) => Promise<DocumentRecord>
  retryDocument: (documentId: string) => Promise<DocumentRecord>
  reviewQuestion: (
    questionId: string,
    body: ReviewQuestionRequest,
  ) => Promise<AnswerRecord>
  createAction: (body: CreateActionRequest) => Promise<ActionRecord>
  updateActionStatus: (
    actionId: string,
    body: UpdateActionStatusRequest,
  ) => Promise<ActionRecord>
  invalidateEvidenceLink: (evidenceLinkId: string) => Promise<void>
}

export function useCaseWorkspace(caseId: string | null): CaseWorkspace {
  const [caseSummary, setCaseSummary] = useState<CaseSummary | null>(null)
  const [readiness, setReadiness] = useState<ReadinessSummary | null>(null)
  const [questions, setQuestions] = useState<QuestionListItem[]>([])
  const [documents, setDocuments] = useState<DocumentRecord[]>([])
  const [actions, setActions] = useState<ActionRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<unknown>(null)

  // Guards against a slow response for a previously selected case landing
  // after the user has already switched to another one.
  const activeCaseId = useRef<string | null>(caseId)
  useEffect(() => {
    activeCaseId.current = caseId
  }, [caseId])

  const load = useCallback(async (id: string) => {
    const [summary, readinessResult, questionsResult, documentsResult, actionsResult] =
      await Promise.all([
        api.getCase(id),
        api.getReadiness(id),
        api.listQuestions(id),
        api.listDocuments(id),
        api.listActions(id),
      ])
    if (activeCaseId.current !== id) return
    setCaseSummary(summary)
    setReadiness(readinessResult)
    setQuestions(questionsResult)
    setDocuments(documentsResult)
    setActions(actionsResult)
  }, [])

  const refresh = useCallback(async () => {
    if (!caseId) return
    try {
      await load(caseId)
      setError(null)
    } catch (err) {
      setError(err)
    }
  }, [caseId, load])

  useEffect(() => {
    if (!caseId) {
      setCaseSummary(null)
      setReadiness(null)
      setQuestions([])
      setDocuments([])
      setActions([])
      setError(null)
      setLoading(false)
      return
    }
    setLoading(true)
    load(caseId)
      .then(() => setError(null))
      .catch((err) => setError(err))
      .finally(() => {
        if (activeCaseId.current === caseId) setLoading(false)
      })
  }, [caseId, load])

  /** Run a mutation, then resync from the server. */
  const mutate = useCallback(
    async <T,>(fn: (id: string) => Promise<T>): Promise<T> => {
      if (!caseId) throw new Error('No case selected.')
      setBusy(true)
      try {
        const result = await fn(caseId)
        await load(caseId)
        setError(null)
        return result
      } finally {
        setBusy(false)
      }
    },
    [caseId, load],
  )

  const uploadDocument = useCallback(
    (file: File, documentType: DocumentType, sourceDate?: string) =>
      mutate((id) => api.uploadDocument(id, file, documentType, sourceDate)),
    [mutate],
  )

  const retryDocument = useCallback(
    (documentId: string) => mutate((id) => api.retryDocument(id, documentId)),
    [mutate],
  )

  const reviewQuestion = useCallback(
    (questionId: string, body: ReviewQuestionRequest) =>
      // The review endpoint returns an AnswerRecord, which is a different
      // shape from QuestionListItem and can also change the question's
      // evidence status (NOT_APPLICABLE). `mutate` refetches, so the table
      // shows the server's new state rather than a locally patched row. The
      // record is returned as well, because it is the only place the
      // confirmed answer text is ever exposed.
      mutate((id) => api.reviewQuestion(id, questionId, body)),
    [mutate],
  )

  const createAction = useCallback(
    (body: CreateActionRequest) => mutate((id) => api.createAction(id, body)),
    [mutate],
  )

  const updateActionStatus = useCallback(
    (actionId: string, body: UpdateActionStatusRequest) =>
      mutate((id) => api.updateActionStatus(id, actionId, body)),
    [mutate],
  )

  const invalidateEvidenceLink = useCallback(
    async (evidenceLinkId: string) => {
      await mutate((id) => api.invalidateEvidenceLink(id, evidenceLinkId))
    },
    [mutate],
  )

  return useMemo(
    () => ({
      caseSummary,
      readiness,
      questions,
      documents,
      actions,
      loading,
      busy,
      error,
      refresh,
      uploadDocument,
      retryDocument,
      reviewQuestion,
      createAction,
      updateActionStatus,
      invalidateEvidenceLink,
    }),
    [
      caseSummary,
      readiness,
      questions,
      documents,
      actions,
      loading,
      busy,
      error,
      refresh,
      uploadDocument,
      retryDocument,
      reviewQuestion,
      createAction,
      updateActionStatus,
      invalidateEvidenceLink,
    ],
  )
}

/** Remembers the selected case across reloads. The Case list comes from the
 * server; only the *selection* is local. */
const SELECTED_CASE_KEY = 'buktiesg.selectedCaseId'

/**
 * @param loaded whether `cases` reflects a successful load. Required, because
 * an empty array is ambiguous on its own: it means both "not fetched yet" and
 * "there really are no cases", and the stale-selection check below must fire
 * for the second and not the first.
 */
export function useSelectedCaseId(cases: CaseSummary[], loaded: boolean) {
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null)
  const restored = useRef(false)

  useEffect(() => {
    if (restored.current || typeof window === 'undefined') return
    restored.current = true
    const stored = window.localStorage.getItem(SELECTED_CASE_KEY)
    if (stored) setSelectedCaseId(stored)
  }, [])

  useEffect(() => {
    if (typeof window === 'undefined') return
    if (selectedCaseId) window.localStorage.setItem(SELECTED_CASE_KEY, selectedCaseId)
    else window.localStorage.removeItem(SELECTED_CASE_KEY)
  }, [selectedCaseId])

  // Drop a stale selection once the authoritative list has loaded.
  //
  // This used to bail on `cases.length === 0`, which was standing in for "not
  // loaded yet". It also caught the case where the list is genuinely empty —
  // so a selection left in localStorage for a case that no longer exists could
  // never be cleared, and the workspace refetched and 404ed against it on
  // every render. `loaded` says what was actually meant. A failed load leaves
  // it false, so a network error does not throw away a valid selection.
  useEffect(() => {
    if (!loaded || !restored.current || !selectedCaseId) return
    if (!cases.some((c) => c.id === selectedCaseId)) setSelectedCaseId(null)
  }, [cases, loaded, selectedCaseId])

  return [selectedCaseId, setSelectedCaseId] as const
}
