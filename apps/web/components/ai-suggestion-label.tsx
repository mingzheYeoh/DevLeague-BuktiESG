import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Any AI-suggested / unconfirmed content in this app must render through
 * this wrapper. It never uses success/verified (green) styling, and it
 * always carries the literal "Not human confirmed" text -- per Main Spec
 * evidence display rules and AGENTS.md §3.2 (the AI never owns a verdict).
 *
 * There is no real AI content in this vertical slice yet, but the
 * component exists now so any future draft/suggestion content is wired
 * through the correct visual treatment from day one.
 */
export function AiSuggestionLabel({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border border-purple-200 bg-purple-50 px-2.5 py-1 text-xs font-medium text-purple-700",
        className,
      )}
    >
      <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
      System suggestion · Not human confirmed
    </span>
  );
}

export function AiSuggestionPanel({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-lg border border-purple-200 bg-purple-50/60 p-4",
        className,
      )}
    >
      <AiSuggestionLabel className="mb-2" />
      <div className="text-sm text-[#17212B]">{children}</div>
    </div>
  );
}
