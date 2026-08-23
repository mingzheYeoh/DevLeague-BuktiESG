'use client'

/**
 * BuktiESG workspace.
 *
 * This component owns navigation and data wiring only; each screen lives in
 * `components/screens/`. Every value it passes down comes from the API layer
 * in `lib/api` — there is no seeded sample data anywhere in the tree, so a
 * screen with nothing to show says so instead of rendering something
 * plausible.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import type { CreateCaseRequest, DocumentRecord, DocumentType, QuestionListItem } from '@/lib/api'
import {
  api,
  errorMessage,
  questionStats,
  useApiHealth,
  useCaseWorkspace,
  useCases,
  useSelectedCaseId,
} from '@/lib/api'
import { daysLeftLabel } from '@/lib/format'
import { useReviewer } from '@/lib/reviewer'

import { Drawer, ErrorNotice, Key } from './primitives'
import { ActionsScreen, type ActionPrefill } from './screens/actions-screen'
import { CasesScreen } from './screens/cases-screen'
import { CreateCaseScreen } from './screens/create-case-screen'
import { EvidenceScreen } from './screens/evidence-screen'
import { ExportScreen } from './screens/export-screen'
import { QuestionDetailScreen } from './screens/question-detail-screen'
import { QuestionsScreen } from './screens/questions-screen'
import { OverviewScreen } from './screens/overview-screen'
import { Header, Sidebar, type Screen } from './shell'

export default function BuktiApp() {
  const [screen, setScreen] = useState<Screen>('cases')
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [activeQuestionId, setActiveQuestionId] = useState<string | null>(null)
  const [actionPrefill, setActionPrefill] = useState<ActionPrefill | null>(null)
  const [reviewerModalOpen, setReviewerModalOpen] = useState(false)
  const [creatingCase, setCreatingCase] = useState(false)
  const [createError, setCreateError] = useState<unknown>(null)
  const [lastUpload, setLastUpload] = useState<DocumentRecord | null>(null)
  const [sessionUrls, setSessionUrls] = useState<Record<string, string>>({})
  const [attentionFirst, setAttentionFirst] = useState(false)

  const { online } = useApiHealth()
  const { cases, loading: casesLoading, error: casesError, reload: reloadCases } = useCases()
  const [selectedCaseId, setSelectedCaseId] = useSelectedCaseId(cases)
  const workspace = useCaseWorkspace(selectedCaseId)
  const { reviewerName, setReviewerName } = useReviewer()

  const {
    caseSummary,
    readiness,
    questions,
    documents,
    actions,
    loading,
    busy,
    error,
    refresh,
  } = workspace

  // Object URLs created for files uploaded in this session, revoked on unmount.
  const urlsRef = useRef<string[]>([])
  useEffect(
    () => () => {
      urlsRef.current.forEach((url) => URL.revokeObjectURL(url))
    },
    [],
  )

  const stats = questionStats(questions, readiness)

  const go = useCallback((next: Screen) => {
    setScreen(next)
    setMobileOpen(false)
  }, [])

  const openCase = useCallback(
    (caseId: string) => {
      setSelectedCaseId(caseId)
      setActiveQuestionId(null)
      go('overview')
    },
    [go, setSelectedCaseId],
  )

  const openQuestion = useCallback(
    (questionId: string) => {
      setActiveQuestionId(questionId)
      go('detail')
    },
    [go],
  )

  const rememberSessionFile = useCallback((doc: DocumentRecord, file: File) => {
    const url = URL.createObjectURL(file)
    urlsRef.current.push(url)
    setSessionUrls((prev) => ({ ...prev, [doc.id]: url }))
  }, [])

  const handleUpload = useCallback(
    async (file: File, documentType: DocumentType) => {
      const doc = await workspace.uploadDocument(file, documentType)
      rememberSessionFile(doc, file)
      setLastUpload(doc)
    },
    [rememberSessionFile, workspace],
  )

  const handleCreateCase = useCallback(
    async (body: CreateCaseRequest, questionnaire: File | null) => {
      setCreateError(null)
      setCreatingCase(true)
      try {
        const created = await api.createCase(body)
        if (questionnaire) {
          // Uploaded directly rather than through the workspace hook, which is
          // still bound to the previously selected case at this point.
          const doc = await api.uploadDocument(created.id, questionnaire, 'QUESTIONNAIRE')
          rememberSessionFile(doc, questionnaire)
          setLastUpload(doc)
        }
        await reloadCases()
        setSelectedCaseId(created.id)
        setActiveQuestionId(null)
        go(questionnaire ? 'intake' : 'overview')
      } catch (err) {
        setCreateError(err)
        throw err
      } finally {
        setCreatingCase(false)
      }
    },
    [go, rememberSessionFile, reloadCases, setSelectedCaseId],
  )

  const startActionForQuestion = useCallback(
    (question: QuestionListItem) => {
      setActionPrefill({
        questionId: question.id,
        title: `Close evidence gap: ${question.question_text.slice(0, 80)}`,
      })
      go('actions')
    },
    [go],
  )

  const activeQuestion = useMemo(
    () => questions.find((q) => q.id === activeQuestionId) ?? null,
    [questions, activeQuestionId],
  )

  // A question id from a previous case cannot survive a case switch.
  useEffect(() => {
    if (screen === 'detail' && !activeQuestion && !loading) setScreen('questions')
  }, [screen, activeQuestion, loading])

  const dueLabel = daysLeftLabel(caseSummary?.deadline_at)
  const caseTitle = caseSummary?.title ?? (selectedCaseId ? 'Loading…' : 'No case selected')
  const needsCase = !selectedCaseId && screen !== 'cases' && screen !== 'create'

  return (
    <div className="app-shell">
      {mobileOpen && <div className="nav-scrim" onClick={() => setMobileOpen(false)} />}
      <Sidebar
        screen={screen}
        setScreen={go}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        open={mobileOpen}
        workflowLabel={selectedCaseId ? `Response workflow · ${dueLabel}` : 'No case selected'}
        reviewCount={stats.unconfirmedDrafts}
        workspaceName={caseSummary?.customer_name ?? 'BuktiESG workspace'}
        workspaceSub={
          selectedCaseId
            ? `${stats.total} question${stats.total === 1 ? '' : 's'} · ${documents.length} document${
                documents.length === 1 ? '' : 's'
              }`
            : 'Synthetic data only'
        }
      />
      <div className="app-main">
        <Header
          onMenu={() => setMobileOpen(!mobileOpen)}
          onOpenReviewQueue={() => {
            setAttentionFirst(true)
            go('questions')
          }}
          caseTitle={caseTitle}
          dueLabel={selectedCaseId ? dueLabel : 'No deadline'}
          reviewCount={stats.unconfirmedDrafts}
          reviewerName={reviewerName}
          onEditReviewer={() => setReviewerModalOpen(true)}
          apiOnline={online}
        />
        <main className="content">
          {needsCase ? (
            <div className="callout info">
              <div>
                <b>Select a case first</b>
                <p>This screen shows data for one case.</p>
              </div>
              <button className="link" type="button" onClick={() => go('cases')}>
                Go to cases
              </button>
            </div>
          ) : null}

          {screen === 'cases' && (
            <CasesScreen
              cases={cases}
              loading={casesLoading}
              error={casesError}
              reload={reloadCases}
              onOpenCase={openCase}
              onNewCase={() => go('create')}
            />
          )}

          {screen === 'create' && (
            <>
              {createError ? <ErrorNotice message={errorMessage(createError)} /> : null}
              <CreateCaseScreen
                onCancel={() => go('cases')}
                onCreate={handleCreateCase}
                busy={creatingCase}
              />
            </>
          )}

          {screen === 'overview' && selectedCaseId && (
            <OverviewScreen
              caseSummary={caseSummary}
              readiness={readiness}
              questions={questions}
              documents={documents}
              actions={actions}
              loading={loading}
              error={error}
              refresh={refresh}
              go={go}
              onOpenQuestion={openQuestion}
            />
          )}

          {screen === 'intake' && selectedCaseId && (
            <EvidenceScreen
              documents={documents}
              loading={loading}
              error={error}
              busy={busy}
              refresh={refresh}
              onUpload={handleUpload}
              onRetry={async (documentId) => {
                const doc = await workspace.retryDocument(documentId)
                setLastUpload(doc)
              }}
              sessionUrls={sessionUrls}
              lastUpload={lastUpload}
              onDismissMapping={() => setLastUpload(null)}
            />
          )}

          {screen === 'questions' && selectedCaseId && (
            <QuestionsScreen
              questions={questions}
              readiness={readiness}
              loading={loading}
              error={error}
              refresh={refresh}
              onOpenQuestion={openQuestion}
              attentionFirst={attentionFirst}
            />
          )}

          {screen === 'detail' && activeQuestion && (
            <QuestionDetailScreen
              question={activeQuestion}
              reviewerName={reviewerName}
              onEditReviewer={() => setReviewerModalOpen(true)}
              busy={busy}
              onReview={workspace.reviewQuestion}
              onCreateAction={startActionForQuestion}
              onBack={() => go('questions')}
            />
          )}

          {screen === 'actions' && selectedCaseId && (
            <ActionsScreen
              actions={actions}
              questions={questions}
              loading={loading}
              error={error}
              busy={busy}
              refresh={refresh}
              onCreate={workspace.createAction}
              onUpdateStatus={workspace.updateActionStatus}
              prefill={actionPrefill}
              onConsumePrefill={() => setActionPrefill(null)}
            />
          )}

          {screen === 'export' && selectedCaseId && (
            <ExportScreen
              caseSummary={caseSummary}
              readiness={readiness}
              questions={questions}
              documents={documents}
              actions={actions}
            />
          )}
        </main>
      </div>

      {reviewerModalOpen && (
        <ReviewerDrawer
          reviewerName={reviewerName}
          setReviewerName={setReviewerName}
          close={() => setReviewerModalOpen(false)}
        />
      )}
    </div>
  )
}

function ReviewerDrawer({
  reviewerName,
  setReviewerName,
  close,
}: {
  reviewerName: string
  setReviewerName: (name: string) => void
  close: () => void
}) {
  const [draft, setDraft] = useState(reviewerName)

  return (
    <Drawer eyebrow="Reviewer" title="Who is reviewing?" close={close}>
      <label>
        Reviewer label
        <input
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="e.g. Nur Aina, Sustainability Lead"
          autoFocus
        />
      </label>
      <div className="callout info">
        <div>
          <b>This is a label, not an identity</b>
          <p>
            The API has no authentication and no user accounts. Whatever you type is stored verbatim
            on each review as <code>reviewer_name</code>. It proves nothing and grants nothing — real
            attribution needs authentication on the server first.
          </p>
        </div>
      </div>
      <Key label="Stored in" value="This browser only (localStorage)" />
      <button
        className="primary full"
        type="button"
        onClick={() => {
          setReviewerName(draft)
          close()
        }}
      >
        Save
      </button>
    </Drawer>
  )
}
