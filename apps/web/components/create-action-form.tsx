"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { api, ApiError } from "@/lib/api-client";

/**
 * Creates one SUBMISSION action on a question (contract §6 "Priority and
 * Actions", POST /api/v1/cases/{case_id}/actions). Type is fixed to
 * SUBMISSION for this slice -- IMPROVEMENT actions are out of scope.
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
  const [title, setTitle] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [nextStep, setNextStep] = useState("");
  const [deadlineAt, setDeadlineAt] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const canSubmit =
    title.trim() !== "" && ownerName.trim() !== "" && nextStep.trim() !== "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      await api.createAction(caseId, {
        question_id: questionId,
        type: "SUBMISSION",
        title: title.trim(),
        owner_name: ownerName.trim(),
        next_step: nextStep.trim(),
        deadline_at: deadlineAt ? new Date(deadlineAt).toISOString() : null,
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
          <Label htmlFor={`deadline-${questionId}`}>Deadline</Label>
          <Input
            id={`deadline-${questionId}`}
            type="date"
            value={deadlineAt}
            onChange={(e) => setDeadlineAt(e.target.value)}
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
