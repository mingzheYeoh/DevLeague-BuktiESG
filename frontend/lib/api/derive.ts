/**
 * Counts and groupings derived from server data, for display only.
 *
 * Everything here is a tally of statuses the server already decided. Nothing
 * in this file assigns, upgrades or infers an `evidence_status`, a
 * `review_status`, or a priority score (AGENTS.md §3.2/§3.5). The case-level
 * readiness number is never computed here either — it comes from
 * `GET /api/v1/cases/{id}/readiness`.
 */
import { isEvidenceGap } from './status'
import type {
  ActionRecord,
  DocumentRecord,
  EvidenceStatus,
  Pillar,
  QuestionListItem,
  ReadinessSummary,
} from './types'

export interface QuestionStats {
  total: number
  requiredCount: number
  /** Server-confirmed required answers. Sourced from the readiness endpoint
   * when available, so the dashboard and the protected formula can never
   * disagree. */
  confirmedRequired: number
  totalRequiredFromServer: number
  /** Percentage straight from the server. Null until readiness has loaded —
   * rendered as "—" rather than as a guess. */
  readinessPercentage: number | null
  /** Answers not yet confirmed by a human. */
  unconfirmedDrafts: number
  evidenceGaps: number
  sourceConflicts: number
  evidenceCounts: Record<EvidenceStatus, number>
}

const EMPTY_EVIDENCE_COUNTS = (): Record<EvidenceStatus, number> => ({
  VERIFIED: 0,
  PARTIAL: 0,
  OUTDATED: 0,
  CONFLICTING: 0,
  MISSING: 0,
  NOT_APPLICABLE: 0,
  NEEDS_MANUAL_REVIEW: 0,
})

export function questionStats(
  questions: QuestionListItem[],
  readiness: ReadinessSummary | null,
): QuestionStats {
  const evidenceCounts = EMPTY_EVIDENCE_COUNTS()
  for (const q of questions) {
    if (q.evidence_status in evidenceCounts) evidenceCounts[q.evidence_status] += 1
  }

  const required = questions.filter((q) => q.is_required)
  const confirmedRequiredLocal = required.filter(
    (q) => q.review_status === 'HUMAN_CONFIRMED',
  ).length

  return {
    total: questions.length,
    requiredCount: required.length,
    confirmedRequired: readiness?.confirmed_required_questions ?? confirmedRequiredLocal,
    totalRequiredFromServer: readiness?.total_required_questions ?? required.length,
    readinessPercentage: readiness ? Math.round(readiness.percentage) : null,
    unconfirmedDrafts: questions.filter((q) => q.review_status !== 'HUMAN_CONFIRMED').length,
    evidenceGaps: questions.filter((q) => isEvidenceGap(q.evidence_status)).length,
    sourceConflicts: evidenceCounts.CONFLICTING,
    evidenceCounts,
  }
}

export interface PillarBreakdown {
  pillar: Pillar
  total: number
  required: number
  confirmedRequired: number
  /** The same confirmed-required/total-required ratio the server applies at
   * case level, narrowed to one pillar. A display breakdown of the protected
   * readiness formula, not a second formula — the headline number always
   * comes from the server. Null when the pillar has no required questions. */
  percentage: number | null
}

export function pillarBreakdown(questions: QuestionListItem[], pillar: Pillar): PillarBreakdown {
  const inPillar = questions.filter((q) => q.pillar === pillar)
  const required = inPillar.filter((q) => q.is_required)
  const confirmedRequired = required.filter(
    (q) => q.review_status === 'HUMAN_CONFIRMED',
  ).length
  return {
    pillar,
    total: inPillar.length,
    required: required.length,
    confirmedRequired,
    percentage: required.length === 0 ? null : Math.round((confirmedRequired / required.length) * 100),
  }
}

/** Questions worth a reviewer's attention first.
 *
 * `priority_score` is server-owned and currently always null, and the
 * priority formula is a protected value we must not reimplement here. So this
 * is an explicit, labelled *ordering* — evidence gaps and unconfirmed answers
 * float up — and it is never presented as a priority score.
 */
export function attentionOrder(questions: QuestionListItem[]): QuestionListItem[] {
  const rank = (q: QuestionListItem) => {
    let r = 0
    if (q.is_required) r -= 4
    if (q.evidence_status === 'CONFLICTING') r -= 3
    if (q.evidence_status === 'MISSING') r -= 2
    if (isEvidenceGap(q.evidence_status)) r -= 1
    if (q.review_status !== 'HUMAN_CONFIRMED') r -= 1
    return r
  }
  return [...questions].sort((a, b) => rank(a) - rank(b))
}

export function openActions(actions: ActionRecord[]): ActionRecord[] {
  return actions.filter((a) => a.status !== 'COMPLETED')
}

export function documentsNeedingAttention(documents: DocumentRecord[]): DocumentRecord[] {
  return documents.filter(
    (d) => d.processing_status === 'FAILED' || d.processing_status === 'NEEDS_MANUAL_REVIEW',
  )
}
