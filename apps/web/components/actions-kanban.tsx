"use client";

import { useState } from "react";
import { AlertTriangle, CalendarClock, User } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { EmptyState } from "@/components/empty-state";
import { cn } from "@/lib/utils";
import { api, ApiError } from "@/lib/api-client";
import type { ActionRecord } from "@/lib/types";

const TYPE_STYLES: Record<ActionRecord["type"], string> = {
  SUBMISSION: "border-blue-200 bg-blue-50 text-blue-700",
  IMPROVEMENT: "border-amber-200 bg-amber-50 text-amber-700",
};

function ActionTypeBadge({ type }: { type: ActionRecord["type"] }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-semibold uppercase tracking-wide",
        TYPE_STYLES[type],
      )}
      data-testid="action-type-badge"
    >
      {type}
    </span>
  );
}

function isOverdue(action: ActionRecord): boolean {
  if (!action.deadline_at) return false;
  if (action.status === "COMPLETED") return false;
  return new Date(action.deadline_at).getTime() < Date.now();
}

function CompletionForm({
  caseId,
  action,
  onCompleted,
  onCancel,
}: {
  caseId: string;
  action: ActionRecord;
  onCompleted: (updated: ActionRecord) => void;
  onCancel: () => void;
}) {
  const [note, setNote] = useState("");
  const [closureLinkId, setClosureLinkId] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const needsEvidence = action.requires_closure_evidence;
  const canSubmit = note.trim() !== "" && (!needsEvidence || closureLinkId.trim() !== "");

  async function handleSubmit() {
    if (!canSubmit || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const updated = await api.updateActionStatus(caseId, action.id, {
        status: "COMPLETED",
        completion_note: note.trim(),
        closure_evidence_link_id: needsEvidence ? closureLinkId.trim() : null,
      });
      onCompleted(updated);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Could not reach the BuktiESG API to complete this Action. Is the backend running at the configured API URL?",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="mt-3 flex flex-col gap-2 rounded-md border border-[#DCE4EC] bg-[#F7F9FC] p-3"
      data-testid="completion-form"
    >
      <div className="flex flex-col gap-1.5">
        <Label htmlFor={`completion-note-${action.id}`}>
          Completion note *
        </Label>
        <textarea
          id={`completion-note-${action.id}`}
          className="flex min-h-[60px] w-full rounded-md border border-[#DCE4EC] bg-white px-3 py-2 text-sm text-[#17212B] placeholder:text-[#667085] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#173F68]"
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="What was done to close this out"
          required
        />
      </div>

      {needsEvidence ? (
        <div className="flex flex-col gap-1.5">
          <Label htmlFor={`closure-link-${action.id}`}>
            Closure evidence link ID *
          </Label>
          <Input
            id={`closure-link-${action.id}`}
            placeholder="evidence_001"
            value={closureLinkId}
            onChange={(e) => setClosureLinkId(e.target.value)}
            required
          />
          <p className="text-xs text-amber-700">
            This Action requires closure evidence. There is currently no
            endpoint that lists evidence_links for a question, so this is a
            manual ID entry -- ask the reviewer for the evidence_links row id
            that supports this Action, or wire up a picker once a listing
            endpoint exists.
          </p>
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
          disabled={!canSubmit || submitting}
          onClick={() => void handleSubmit()}
          data-testid="submit-completion"
        >
          {submitting ? "Completing..." : "Mark completed"}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Cancel
        </Button>
      </div>
    </div>
  );
}

function ActionCard({
  caseId,
  action,
  onCompleted,
}: {
  caseId: string;
  action: ActionRecord;
  onCompleted: (updated: ActionRecord) => void;
}) {
  const [showCompletion, setShowCompletion] = useState(false);
  const overdue = isOverdue(action);

  return (
    <li
      className="rounded-lg border border-[#DCE4EC] bg-white p-4"
      data-testid="action-card"
    >
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-[#17212B]">{action.title}</p>
        <ActionTypeBadge type={action.type} />
      </div>

      <div className="mt-2 flex flex-col gap-1 text-xs text-[#667085]">
        <span className="flex items-center gap-1.5">
          <User className="h-3.5 w-3.5" aria-hidden="true" />
          {action.owner_name ?? "No owner set"}
          {action.owner_role ? ` · ${action.owner_role}` : ""}
        </span>
        <span className="flex items-center gap-1.5">
          <CalendarClock className="h-3.5 w-3.5" aria-hidden="true" />
          {action.deadline_at
            ? new Date(action.deadline_at).toLocaleDateString()
            : "No deadline set"}
          {overdue ? (
            <span className="ml-1 inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2 py-0.5 font-semibold text-red-700">
              <AlertTriangle className="h-3 w-3" aria-hidden="true" />
              Overdue
            </span>
          ) : null}
        </span>
      </div>

      <p className="mt-2 text-sm text-[#17212B]">
        {action.next_step ?? "No next step set"}
      </p>

      {action.status === "COMPLETED" ? (
        <div className="mt-2 text-xs text-emerald-700">
          {action.completion_note ? (
            <p>
              <span className="font-medium">Completion note: </span>
              {action.completion_note}
            </p>
          ) : null}
          {action.closure_evidence_link_id ? (
            <p className="mt-1">Closure evidence attached.</p>
          ) : null}
        </div>
      ) : (
        <div className="mt-3">
          {action.requires_closure_evidence ? (
            <p className="mb-1 text-xs text-[#667085]">
              This Action requires closure evidence to complete.
            </p>
          ) : null}
          {showCompletion ? (
            <CompletionForm
              caseId={caseId}
              action={action}
              onCompleted={(updated) => {
                setShowCompletion(false);
                onCompleted(updated);
              }}
              onCancel={() => setShowCompletion(false)}
            />
          ) : (
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setShowCompletion(true)}
              data-testid="open-completion-form"
            >
              Mark complete
            </Button>
          )}
        </div>
      )}
    </li>
  );
}

/**
 * Simple two-column Kanban for Actions on a Case (Main Spec §17 Phase 5):
 * OPEN (TODO/IN_PROGRESS/BLOCKED/NEEDS_REVIEW) and COMPLETED. Gate P5:
 * "Submission and Improvement are displayed separately" -- satisfied here
 * via the type badge on every card rather than separate columns, since a
 * third split axis (type) on top of status would over-build this phase.
 */
export function ActionsKanban({
  caseId,
  actions,
  onActionUpdated,
}: {
  caseId: string;
  actions: ActionRecord[];
  onActionUpdated: (updated: ActionRecord) => void;
}) {
  if (actions.length === 0) {
    return (
      <EmptyState
        title="No Actions yet"
        description="Create a SUBMISSION or IMPROVEMENT action from a question to see it here."
      />
    );
  }

  const open = actions.filter((a) => a.status !== "COMPLETED");
  const completed = actions.filter((a) => a.status === "COMPLETED");

  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#17212B]">
          Open
          <span className="rounded-full bg-[#EAF5FC] px-2 py-0.5 text-xs font-medium text-[#173F68]">
            {open.length}
          </span>
        </h3>
        {open.length === 0 ? (
          <EmptyState title="Nothing open" />
        ) : (
          <ul className="flex flex-col gap-3" data-testid="actions-column-open">
            {open.map((a) => (
              <ActionCard
                key={a.id}
                caseId={caseId}
                action={a}
                onCompleted={onActionUpdated}
              />
            ))}
          </ul>
        )}
      </div>
      <div>
        <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-[#17212B]">
          Completed
          <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
            {completed.length}
          </span>
        </h3>
        {completed.length === 0 ? (
          <EmptyState title="Nothing completed yet" />
        ) : (
          <ul
            className="flex flex-col gap-3"
            data-testid="actions-column-completed"
          >
            {completed.map((a) => (
              <ActionCard
                key={a.id}
                caseId={caseId}
                action={a}
                onCompleted={onActionUpdated}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
