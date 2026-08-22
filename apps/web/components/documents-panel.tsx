"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/empty-state";
import { api, ApiError } from "@/lib/api-client";
import type { DocumentRecord } from "@/lib/types";

/**
 * Minimal processing-status / retry surface for a Case's Documents.
 *
 * Main Spec §17 Phase 2 item 5 ("retry, failure, manual-review UI"): shows
 * each Document's processing_status and error (nothing invented
 * client-side -- see lib/api-client.ts's contract-shape rule), and a Retry
 * button for anything FAILED / NEEDS_MANUAL_REVIEW, wired to
 * POST /api/v1/cases/{case_id}/documents/{document_id}/retry.
 */
export function DocumentsPanel({
  caseId,
  documents,
  onChanged,
}: {
  caseId: string;
  documents: DocumentRecord[];
  onChanged: () => void;
}) {
  const [retryingId, setRetryingId] = useState<string | null>(null);
  const [retryError, setRetryError] = useState<string | null>(null);

  if (documents.length === 0) {
    return (
      <EmptyState
        title="No documents yet"
        description="Uploaded questionnaires and evidence documents will appear here with their processing status."
      />
    );
  }

  async function handleRetry(documentId: string) {
    setRetryingId(documentId);
    setRetryError(null);
    try {
      await api.retryDocument(caseId, documentId);
      onChanged();
    } catch (err) {
      setRetryError(
        err instanceof ApiError
          ? err.message
          : "Could not reach the BuktiESG API to retry this document.",
      );
    } finally {
      setRetryingId(null);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {retryError ? (
        <p role="alert" className="text-xs text-red-700">
          {retryError}
        </p>
      ) : null}
      <ul className="flex flex-col gap-2" data-testid="documents-list">
        {documents.map((doc) => {
          const isRetryable =
            doc.processing_status === "FAILED" ||
            doc.processing_status === "NEEDS_MANUAL_REVIEW";
          return (
            <li
              key={doc.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-[#DCE4EC] bg-white p-3"
              data-testid="document-row"
            >
              <div className="min-w-[200px] flex-1">
                <p className="text-sm font-medium text-[#17212B]">
                  {doc.original_filename}
                </p>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                  <span
                    className="rounded-full bg-[#EAF5FC] px-2 py-0.5 font-medium text-[#173F68]"
                    data-testid="document-status"
                  >
                    {doc.processing_status}
                  </span>
                  <span className="text-[#667085]">{doc.document_type}</span>
                </div>
                {doc.error ? (
                  <p
                    className="mt-1 text-xs text-red-700"
                    data-testid="document-error"
                  >
                    {doc.error}
                  </p>
                ) : null}
              </div>
              {isRetryable ? (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  disabled={retryingId === doc.id}
                  onClick={() => void handleRetry(doc.id)}
                  data-testid="retry-document"
                >
                  <RefreshCw className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                  {retryingId === doc.id ? "Retrying..." : "Retry"}
                </Button>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}
