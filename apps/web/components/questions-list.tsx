"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { EvidenceStatusBadge } from "@/components/evidence-status-badge";
import { SourceLocationChip } from "@/components/source-location-chip";
import { AiSuggestionLabel } from "@/components/ai-suggestion-label";
import { EmptyState } from "@/components/empty-state";
import { CreateActionForm } from "@/components/create-action-form";
import type { QuestionListItem } from "@/lib/types";

/**
 * Questions list for the vertical slice. Displays only what the contract's
 * Question List Item (§7.3) documents: question text, required flag,
 * evidence status, and source location -- as returned by the API, never
 * inferred or invented client-side.
 */
export function QuestionsList({
  caseId,
  questions,
}: {
  caseId: string;
  questions: QuestionListItem[];
}) {
  const [actionFormQuestionId, setActionFormQuestionId] = useState<
    string | null
  >(null);

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
                <SourceLocationChip location={q.source_location} />
                {q.evidence_status === "AI_SUGGESTED" ? (
                  <AiSuggestionLabel />
                ) : null}
              </div>
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
              Create SUBMISSION action
            </Button>
          </div>

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
