import { FileText, MapPin } from "lucide-react";
import type { SourceLocation } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * Renders exactly what the API returned for a source location. Never
 * fabricates a location -- if the API sends null, this renders the "no
 * location provided" state instead of inventing one (AGENTS.md §3.3: the
 * server resolves citations, the client never invents them).
 */
export function SourceLocationChip({
  location,
  className,
}: {
  location: SourceLocation | null | undefined;
  className?: string;
}) {
  if (!location) {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-md border border-dashed border-[#DCE4EC] px-2 py-1 text-xs text-[#667085]",
          className,
        )}
      >
        <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
        No source location provided
      </span>
    );
  }

  let text: string;
  switch (location.type) {
    case "page":
      text = `Page ${location.page_number}`;
      break;
    case "sheet_cell":
      text = `Sheet ${location.sheet_name} · ${location.cell_range}`;
      break;
    case "paragraph":
      text = `${location.heading_path.join(" › ")} · Paragraph ${location.paragraph_index}`;
      break;
    case "manual":
      text = `Manual statement · ${location.description}`;
      break;
    default:
      text = "Unknown location type";
  }

  const isManual = location.type === "manual";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs",
        isManual
          ? "border-purple-200 bg-purple-50 text-purple-700"
          : "border-[#DCE4EC] bg-[#F7F9FC] text-[#17212B]",
        className,
      )}
      title={
        isManual
          ? "A manual location cannot independently qualify an answer as Verified."
          : undefined
      }
    >
      <FileText className="h-3.5 w-3.5" aria-hidden="true" />
      {text}
    </span>
  );
}
