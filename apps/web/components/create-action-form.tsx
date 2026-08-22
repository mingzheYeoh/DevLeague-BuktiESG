"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api-client";
import type { ActionType } from "@/lib/types";

/**
 * Creates one Action (SUBMISSION or IMPROVEMENT) on a question (contract
 * §6 "Priority and Actions", POST /api/v1/cases/{case_id}/actions). Gate
 * P5: "An Action cannot be created without an owner, next step, and
 * deadline" -- all three are required here, not just owner/next step.
 */
export function CreateActionForm({
  caseId,
  questionId,
  onCreated,
  onCancel,
}: {
  caseId: string;
  questionId: string;
  onCreated: () => void;
  onCancel: () => void;
}) {
  const [type, setType] = useState<ActionType>("SUBMISSION");
  const [title, setTitle] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [deadlineAt, setDeadlineAt] = useState("");
  const [requiresClosureEvidence, setRequiresClosureEvidence] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const canSubmit =
    title.trim() !== "" &&
    ownerName.trim() !== "" &&
    nextStep.trim() !== "" &&
    deadlineAt.trim() !== "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      await api.createAction(caseId, {
        question_id: questionId,
        type,
        title: title.trim(),
        owner_name: ownerName.trim(),
        next_step: nextStep.trim(),
        deadline_at: new Date(deadlineAt).toISOString(),
        requires_closure_evidence: requiresClosureEvidence ? true : undefined,
      });
      setSuccess(true);
      onCreated();
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Could not reach the BuktiESG API. Is the backend running at the configured API URL?",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="flex flex-col gap-3"
      data-testid="create-action-form"
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`type-${questionId}`}>Type *</Label>
        <select
          id={`type-${questionId}`}
          className="flex h-10 w-full rounded-md border border-[#DCE4EC] bg-white px-3 py-2 text-sm text-[#17212B] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#173F68]"
          value={type}
          onChange={(e) => setType(e.target.value as ActionType)}
        >
          <option value="SUBMISSION">Submission</option>
          <option value="IMPROVEMENT">Improvement</option>
        </select>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`title-${questionId}`}>Title *</Label>
        <Input
          id={`title-${questionId}`}
          placeholder="Collect missing electricity bills"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`owner-${questionId}`}>Owner *</Label>
          <Input
            id={`owner-${questionId}`}
            placeholder="Finance Manager"
            value={ownerName}
            onChange={(e) => setOwnerName(e.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`deadline-${questionId}`}>Deadline *</Label>
          <Input
            id={`deadline-${questionId}`}
            type="date"
            value={deadlineAt}
            onChange={(e) => setDeadlineAt(e.target.value)}
            required
          />
        </div>
      </div>
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`next-step-${questionId}`}>Next step *</Label>
        <Input
          id={`next-step-${questionId}`}
          placeholder="Download April to December 2025 bills."
          value={nextStep}
          onChange={(e) => setNextStep(e.target.value)}
          required
        />
      </div>

      <label className="flex items-center gap-2 text-sm text-[#17212B]">
        <input
          type="checkbox"
          checked={requiresClosureEvidence}
          onChange={(e) => setRequiresClosureEvidence(e.target.checked)}
        />
        Require closure evidence to complete this Action
      </label>
      <p className="text-xs text-[#667085]">
        Leave unchecked to let the server decide automatically (it defaults
        to required when the question&apos;s evidence is MISSING or
        CONFLICTING).
      </p>

      {error ? (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      ) : null}
      {success ? (
        <p className="text-sm text-emerald-700">Action created.</p>
      ) : null}

      <div className="flex gap-2">
        <Button
          type="submit"
          size="sm"
          disabled={!canSubmit || submitting}
          data-testid="submit-action"
        >
          {submitting ? "Creating..." : "Create action"}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </form>
  );
}
