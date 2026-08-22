"use client";

import { useState } from "react";
import { Check, Edit3, MinusCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AiSuggestionPanel } from "@/components/ai-suggestion-label";
import { api, ApiError } from "@/lib/api-client";
import type { AnswerRecord, QuestionListItem, ReviewAction } from "@/lib/types";

/**
 * Human Review controls for a question's draft answer (Main Spec §17
 * Phase 5). Accept, Edit, Reject, and Not Applicable are the only ways an
 * unconfirmed AI draft is converted out of that state -- per AGENTS.md §3
 * the AI never owns a verdict, so every path here ends in a server call
 * carrying a human-entered reviewer_name (and, per action, the reviewer's
 * own text), never a value invented on this side.
 *
 * Endpoint verified live against apps/api commit 48dbcec: POST
 * .../questions/{id}/review returns an AnswerRecord (lib/types.ts), which
 * is NOT the same shape as QuestionListItem -- notably, GET .../questions
 * (the list this component's `question` prop comes from) does not expose
 * draft_answer/confirmed_answer/reviewer_name/reviewed_at at all, and
 * there is no GET question-detail endpoint implemented yet either. So
 * this component has no way to preview the draft answer before a
 * reviewer acts on it -- it can only show the AnswerRecord it gets back
 * *after* a review call in this session. That is a real backend gap, not
 * something worked around here.
 */
export function ReviewControls({
  caseId,
  question,
  onReviewed,
}: {
  caseId: string;
  question: QuestionListItem;
  onReviewed: (answer: AnswerRecord) => void;
}) {
  const [openAction, setOpenAction] = useState<ReviewAction | null>(null);
  const [reviewerName, setReviewerName] = useState("");
  const [editedAnswer, setEditedAnswer] = useState("");
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAnswer, setLastAnswer] = useState<AnswerRecord | null>(null);

  function openForm(action: ReviewAction) {
    setOpenAction(action);
    setError(null);
    setReviewerName(lastAnswer?.reviewer_name ?? "");
    setEditedAnswer(lastAnswer?.draft_answer ?? "");
    setReason("");
  }

  function closeForm() {
    setOpenAction(null);
    setError(null);
  }

  function canSubmit(): boolean {
    if (reviewerName.trim() === "") return false;
    if (openAction === "EDIT") return editedAnswer.trim() !== "";
    // Server requires `reason` for both REJECT and NOT_APPLICABLE.
    if (openAction === "REJECT" || openAction === "NOT_APPLICABLE") {
      return reason.trim() !== "";
    }
    return true;
  }

  async function handleSubmit() {
    if (!openAction || !canSubmit() || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.reviewQuestion(caseId, question.id, {
        action: openAction,
        reviewer_name: reviewerName.trim(),
        ...(openAction === "EDIT" ? { edited_answer: editedAnswer.trim() } : {}),
        ...(openAction === "REJECT" || openAction === "NOT_APPLICABLE"
          ? { reason: reason.trim() }
          : {}),
      });
      setLastAnswer(updated);
      onReviewed(updated);
      setOpenAction(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Could not reach the BuktiESG API for review. Is the backend running at the configured API URL?",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  const actionButtons: { action: ReviewAction; label: string; icon: React.ElementType }[] = [
    { action: "ACCEPT", label: "Accept", icon: Check },
    { action: "EDIT", label: "Edit", icon: Edit3 },
    { action: "REJECT", label: "Reject", icon: X },
    { action: "NOT_APPLICABLE", label: "Not applicable", icon: MinusCircle },
  ];

  return (
    <div
      className="rounded-lg border border-[#DCE4EC] bg-[#F7F9FC] p-3"
      data-testid="review-controls"
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-semibold uppercase tracking-wide text-[#667085]">
          Human review
        </p>
        {lastAnswer?.reviewer_name ? (
          <p className="text-xs text-[#667085]">
            Last reviewed by {lastAnswer.reviewer_name}
            {lastAnswer.reviewed_at
              ? ` on ${new Date(lastAnswer.reviewed_at).toLocaleString()}`
              : ""}
          </p>
        ) : null}
      </div>

      {lastAnswer ? (
        lastAnswer.review_status === "HUMAN_CONFIRMED" && lastAnswer.confirmed_answer ? (
          <p className="mt-2 text-sm text-emerald-800">
            <span className="font-medium">Confirmed answer: </span>
            {lastAnswer.confirmed_answer}
          </p>
        ) : lastAnswer.draft_answer ? (
          <AiSuggestionPanel className="mt-2">
            <p className="font-medium text-[#17212B]">Draft answer</p>
            <p className="mt-1">{lastAnswer.draft_answer}</p>
          </AiSuggestionPanel>
        ) : null
      ) : (
        <p className="mt-2 text-xs italic text-[#667085]">
          No answer preview available yet -- this slice has no endpoint that
          returns the draft answer before a review action is taken. Submit
          an action below to see the server&apos;s recorded result.
        </p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {actionButtons.map(({ action, label, icon: Icon }) => (
          <Button
            key={action}
            type="button"
            variant={openAction === action ? "default" : "secondary"}
            size="sm"
            onClick={() => (openAction === action ? closeForm() : openForm(action))}
            data-testid={`review-action-${action.toLowerCase()}`}
          >
            <Icon className="mr-1.5 h-3.5 w-3.5" aria-hidden="true" />
            {label}
          </Button>
        ))}
      </div>

      {openAction ? (
        <div
          className="mt-3 flex flex-col gap-2 rounded-md border border-[#DCE4EC] bg-white p-3"
          data-testid="review-form"
        >
          <div className="flex flex-col gap-1.5">
            <Label htmlFor={`reviewer-${question.id}`}>Reviewer name *</Label>
            <Input
              id={`reviewer-${question.id}`}
              placeholder="Finance Manager"
              value={reviewerName}
              onChange={(e) => setReviewerName(e.target.value)}
              required
            />
          </div>

          {openAction === "EDIT" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={`edited-answer-${question.id}`}>
                Corrected answer *
              </Label>
              <textarea
                id={`edited-answer-${question.id}`}
                className="flex min-h-[80px] w-full rounded-md border border-[#DCE4EC] bg-white px-3 py-2 text-sm text-[#17212B] placeholder:text-[#667085] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#173F68]"
                value={editedAnswer}
                onChange={(e) => setEditedAnswer(e.target.value)}
                required
              />
            </div>
          ) : null}

          {openAction === "REJECT" || openAction === "NOT_APPLICABLE" ? (
            <div className="flex flex-col gap-1.5">
              <Label htmlFor={`reason-${question.id}`}>Reason *</Label>
              <textarea
                id={`reason-${question.id}`}
                className="flex min-h-[60px] w-full rounded-md border border-[#DCE4EC] bg-white px-3 py-2 text-sm text-[#17212B] placeholder:text-[#667085] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#173F68]"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder={
                  openAction === "REJECT"
                    ? "Why this draft answer is being rejected"
                    : "Why this question does not apply"
                }
                required
              />
            </div>
          ) : null}

          {error ? (
            <p role="alert" className="text-sm text-red-700">
              {error}
            </p>
          ) : null}

          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              disabled={!canSubmit() || submitting}
              onClick={() => void handleSubmit()}
              data-testid="submit-review"
            >
              {submitting ? "Submitting..." : `Confirm ${openAction.toLowerCase()}`}
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={closeForm}>
              Cancel
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
