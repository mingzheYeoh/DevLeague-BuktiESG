"use client";

import { useRef, useState } from "react";
import { UploadCloud } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ColumnMappingConfirmation } from "@/components/column-mapping-confirmation";
import { api, ApiError } from "@/lib/api-client";
import type { DocumentRecord } from "@/lib/types";

/**
 * Upload control for the one questionnaire file in the vertical slice.
 * Contract: POST /api/v1/cases/{case_id}/documents (multipart).
 */
export function UploadPanel({
  caseId,
  onUploaded,
}: {
  caseId: string;
  onUploaded: (doc: DocumentRecord) => void;
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "error">(
    "idle",
  );
  const [error, setError] = useState<string | null>(null);
  const [lastUploaded, setLastUploaded] = useState<DocumentRecord | null>(
    null,
  );

  async function handleFile(file: File) {
    setStatus("uploading");
    setError(null);
    try {
      const doc = await api.uploadDocument(caseId, file);
      setLastUploaded(doc);
      setStatus("idle");
      onUploaded(doc);
    } catch (err) {
      setStatus("error");
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Could not reach the BuktiESG API. Is the backend running at the configured API URL?",
        );
      }
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-[#DCE4EC] bg-white p-6">
      <div className="flex flex-col items-center gap-3 text-center">
        <UploadCloud className="h-8 w-8 text-[#173F68]" aria-hidden="true" />
        <div>
          <p className="text-sm font-medium text-[#17212B]">
            Upload the questionnaire
          </p>
          <p className="text-xs text-[#667085]">
            PDF, DOCX, XLSX, or CSV. One file for this slice.
          </p>
        </div>
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          data-testid="questionnaire-file-input"
          accept=".pdf,.docx,.xlsx,.csv"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) void handleFile(file);
          }}
        />
        <Button
          type="button"
          variant="secondary"
          size="sm"
          disabled={status === "uploading"}
          onClick={() => inputRef.current?.click()}
          data-testid="upload-trigger"
        >
          {status === "uploading" ? "Uploading..." : "Choose file"}
        </Button>
        {lastUploaded ? (
          <p className="text-xs text-[#667085]" data-testid="upload-result">
            Uploaded: {lastUploaded.original_filename} ·{" "}
            {lastUploaded.processing_status}
          </p>
        ) : null}
        {lastUploaded?.detected_columns ? (
          <ColumnMappingConfirmation
            className="w-full"
            columnMapping={lastUploaded.detected_columns}
          />
        ) : null}
        {error ? (
          <p role="alert" className="text-xs text-red-700">
            {error}
          </p>
        ) : null}
      </div>
    </div>
  );
}
