"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import { ActionsKanban } from "@/components/actions-kanban";
import { ErrorState } from "@/components/empty-state";
import { api, ApiError } from "@/lib/api-client";
import type { ActionRecord } from "@/lib/types";

/**
 * Actions Kanban for a Case (Main Spec §17 Phase 5, "Human Review and
 * Action Tracking"). OPEN/COMPLETED columns; SUBMISSION vs IMPROVEMENT
 * shown via a badge on every card. See lib/api-client.ts getActions() and
 * updateActionStatus() -- both verified live against apps/api commit
 * 48dbcec ("feat(api): Phase 5 backend -- human review and action
 * tracking"), which landed while this page was being built.
 */
export default function ActionsPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;

  const [actions, setActions] = useState<ActionRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadActions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getActions(caseId);
      setActions(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Could not reach the BuktiESG API. Is the backend running at the configured API URL?",
        );
      }
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    void loadActions();
  }, [loadActions]);

  return (
    <main className="flex flex-col gap-6">
      <div>
        <Link
          href={`/cases/${caseId}`}
          className="mb-2 inline-flex items-center gap-1 text-sm font-medium text-[#173F68]"
        >
          <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
          Back to Case
        </Link>
        <h1 className="text-2xl font-semibold text-[#17212B]">
          Actions for Case {caseId}
        </h1>
        <p className="mt-1 text-sm text-[#667085]">
          Track SUBMISSION and IMPROVEMENT actions from open through
          completion, with the completion note (and closure evidence, where
          required) the Main Spec requires before an Action can be closed.
        </p>
      </div>

      {loading ? (
        <p className="text-sm text-[#667085]" data-testid="actions-loading">
          Loading actions...
        </p>
      ) : error ? (
        <ErrorState
          title="Could not load actions"
          description={error}
          onRetry={() => void loadActions()}
        />
      ) : (
        <ActionsKanban
          caseId={caseId}
          actions={actions}
          onActionUpdated={(updated) =>
            setActions((prev) =>
              prev.map((a) => (a.id === updated.id ? updated : a)),
            )
          }
        />
      )}
    </main>
  );
}
