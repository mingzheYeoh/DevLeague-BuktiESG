"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EvidenceStatusBadge } from "@/components/evidence-status-badge";
import { SourceLocationChip } from "@/components/source-location-chip";
import { AiSuggestionLabel, AiSuggestionPanel } from "@/components/ai-suggestion-label";
import { EmptyState } from "@/components/empty-state";
import { CreateActionForm } from "@/components/create-action-form";
import { ReviewControls } from "@/components/review-controls";
import { cn } from "@/lib/utils";
import type { AnswerRecord, QuestionListItem } from "@/lib/types";

const PILLAR_LABELS: Record<string, string> = {
  E: "Environmental",
  S: "Social",
  G: "Governance",
  UNCATEGORIZED: "Uncategorized",
};

const PILLAR_STYLES: Record<string, string> = {
  E: "border-emerald-200 bg-emerald-50 text-emerald-700",
  S: "border-blue-200 bg-blue-50 text-blue-700",
  G: "border-amber-200 bg-amber-50 text-amber-700",
  UNCATEGORIZED: "border-[#DCE4EC] bg-[#F7F9FC] text-[#667085]",
};

/**
 * SEDG pillar/topic badge -- a draft, AI-suggested mapping (never a
 * verdict; see ai_pipeline.map_question_to_sedg() and its taxonomy's
 * honesty caveat). Distinct from EvidenceStatusBadge, which reflects the
 * deterministic rule engine.
 */
function SedgPillarBadge({ pillar, topicCode }: { pillar: string; topicCode: string | null }) {
  const style = PILLAR_STYLES[pillar] ?? PILLAR_STYLES.UNCATEGORIZED;
  const label = PILLAR_LABELS[pillar] ?? pillar;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium",
        style,
      )}
    >
      {label}
      {topicCode ? ` · ${topicCode}` : ""}
    </span>
  );
}

/**
 * Questions list for the vertical slice. Displays only what the contract's
 * Question List Item (§7.3) documents: question text, required flag,
 * evidence status, and source location -- as returned by the API, never
 * inferred or invented client-side.
 */
export function QuestionsList({
  caseId,
  questions,
  onQuestionUpdated,
}: {
  caseId: string;
  questions: QuestionListItem[];
  /** Called with the server's AnswerRecord after a Human Review action
   * (Accept/Edit/Reject/Not Applicable) succeeds, so the parent can merge
   * review_status/evidence_status/status_reason into its list state
   * without a full reload. Optional so existing callers that haven't
   * wired this up yet keep working. */
  onQuestionUpdated?: (answer: AnswerRecord) => void;
}) {
  const [actionFormQuestionId, setActionFormQuestionId] = useState<
    string | null
  >(null);
  const [expandedQuestionId, setExpandedQuestionId] = useState<string | null>(
    null,
  );

  if (questions.length === 0) {
    return (
      <EmptyState
        title="No questions yet"
        description="Upload a questionnaire above. Once it is parsed, identified questions will appear here."
      />
    );
  }

  return (
    <ul className="flex flex-col gap-3" data-testid="questions-list">
      {questions.map((q) => (
        <li
          key={q.id}
          className="rounded-lg border border-[#DCE4EC] bg-white p-4"
          data-testid="question-row"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex-1 min-w-[240px]">
              <div className="flex items-center gap-2 text-xs text-[#667085]">
                <span>{q.external_question_id}</span>
                {q.is_required ? (
                  <span className="rounded-full bg-[#EAF5FC] px-2 py-0.5 font-medium text-[#173F68]">
                    Required
                  </span>
                ) : null}
              </div>
              <p className="mt-1 text-sm font-medium text-[#17212B]">
                {q.question_text}
              </p>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <EvidenceStatusBadge status={q.evidence_status} />
                <SedgPillarBadge
                  pillar={q.pillar ?? "UNCATEGORIZED"}
                  topicCode={q.sedg_topic_code}
                />
                {q.evidence_location ? (
                  <SourceLocationChip location={q.evidence_location} />
                ) : (
                  <SourceLocationChip location={q.source_location} />
                )}
                {q.evidence_status === "AI_SUGGESTED" ? (
                  <AiSuggestionLabel />
                ) : null}
              </div>
              {q.status_reason ? (
                <p className="mt-1.5 text-xs text-[#667085]">{q.status_reason}</p>
              ) : null}
              <Button
                variant="ghost"
                size="sm"
                className="mt-1.5 h-auto p-0 text-xs font-medium text-[#173F68]"
                onClick={() =>
                  setExpandedQuestionId(
                    expandedQuestionId === q.id ? null : q.id,
                  )
                }
                data-testid="toggle-question-detail"
              >
                <span className="flex items-center gap-1">
                  {expandedQuestionId === q.id ? (
                    <ChevronUp className="h-3.5 w-3.5" aria-hidden="true" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5" aria-hidden="true" />
                  )}
                  {expandedQuestionId === q.id
                    ? "Hide detail"
                    : "Show detail / review"}
                </span>
              </Button>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onClick={() =>
                setActionFormQuestionId(
                  actionFormQuestionId === q.id ? null : q.id,
                )
              }
              data-testid="create-submission-action-trigger"
            >
              Create action
            </Button>
          </div>

          {expandedQuestionId === q.id ? (
            <div
              className="mt-3 flex flex-col gap-3 border-t border-[#DCE4EC] pt-3"
              data-testid="question-detail"
            >
              {q.mapping_rationale ? (
                <AiSuggestionPanel>
                  <p className="font-medium text-[#17212B]">
                    SEDG mapping suggestion
                  </p>
                  <p className="mt-1">{q.mapping_rationale}</p>
                </AiSuggestionPanel>
              ) : null}
              {q.evidence_excerpt ? (
                <AiSuggestionPanel>
                  <p className="font-medium text-[#17212B]">
                    Candidate evidence excerpt
                  </p>
                  {q.evidence_claim_supported ? (
                    <p className="mt-1 text-[#667085]">
                      {q.evidence_claim_supported}
                    </p>
                  ) : null}
                  <blockquote className="mt-1 border-l-2 border-purple-300 pl-2 italic text-[#17212B]">
                    &ldquo;{q.evidence_excerpt}&rdquo;
                  </blockquote>
                </AiSuggestionPanel>
              ) : null}
              <ReviewControls
                caseId={caseId}
                question={q}
                onReviewed={(updated) => onQuestionUpdated?.(updated)}
              />
            </div>
          ) : null}

          {actionFormQuestionId === q.id ? (
            <div className="mt-4 border-t border-[#DCE4EC] pt-4">
              <CreateActionForm
                caseId={caseId}
                questionId={q.id}
                onCreated={() => setActionFormQuestionId(null)}
                onCancel={() => setActionFormQuestionId(null)}
              />
            </div>
          ) : null}
        </li>
      ))}
    </ul>
  );
}
