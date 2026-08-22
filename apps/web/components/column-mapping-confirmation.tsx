"use client";

import { useState } from "react";
import { CheckCircle2, TableProperties } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const FIELD_LABELS: Record<string, string> = {
  external_question_id: "Question ID",
  question_text: "Question text",
  section: "Section",
  is_required: "Required flag",
};

/**
 * Column-mapping confirmation UI (Main Spec §17 Phase 3 "Before Starting" /
 * AI Agent Work item 2). Auto-detected columns are already imported by the
 * time this renders (this slice's upload path parses synchronously -- see
 * app/services/jobs.py) -- this is a transparency/confirmation step, not a
 * blocking gate on import. It exists so the detected header->column mapping
 * is never *silently* trusted: the user sees exactly what was matched
 * before treating the imported questions as reliable, and can flag a
 * mis-detection for a re-upload with corrected headers.
 */
export function ColumnMappingConfirmation({
  columnMapping,
  className,
}: {
  columnMapping: Record<string, string>;
  className?: string;
}) {
  const [confirmed, setConfirmed] = useState(false);
  const entries = Object.entries(columnMapping);

  if (entries.length === 0) {
    return null;
  }

  return (
    <div
      className={cn(
        "rounded-lg border border-[#DCE4EC] bg-[#F7F9FC] p-4 text-left",
        className,
      )}
      data-testid="column-mapping-confirmation"
    >
      <div className="flex items-center gap-2 text-xs font-medium text-[#17212B]">
        <TableProperties className="h-3.5 w-3.5" aria-hidden="true" />
        Detected column mapping
      </div>
      <p className="mt-1 text-xs text-[#667085]">
        These columns were matched by header name in the uploaded file.
        Check they look right -- if not, re-upload with corrected headers.
      </p>
      <ul className="mt-2 flex flex-col gap-1">
        {entries.map(([field, column]) => (
          <li
            key={field}
            className="flex items-center justify-between text-xs text-[#17212B]"
          >
            <span>{FIELD_LABELS[field] ?? field}</span>
            <span className="rounded bg-white px-1.5 py-0.5 font-mono text-[#173F68]">
              Column {column}
            </span>
          </li>
        ))}
      </ul>
      <Button
        type="button"
        variant={confirmed ? "secondary" : "default"}
        size="sm"
        className="mt-3"
        disabled={confirmed}
        onClick={() => setConfirmed(true)}
        data-testid="confirm-column-mapping"
      >
        {confirmed ? (
          <span className="flex items-center gap-1.5">
            <CheckCircle2 className="h-3.5 w-3.5" aria-hidden="true" />
            Mapping confirmed
          </span>
        ) : (
          "This mapping looks correct"
        )}
      </Button>
    </div>
  );
}
