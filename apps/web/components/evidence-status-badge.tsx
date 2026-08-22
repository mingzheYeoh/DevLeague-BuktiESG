import {
  AlertTriangle,
  Ban,
  CheckCircle2,
  Clock,
  FileSearch,
  MinusCircle,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { EvidenceStatus } from "@/lib/types";

/**
 * Visual treatment follows docs/spec/CEO-Product-Frontend-Sub-Spec.md §9
 * ("Mandatory status presentation") and the Main Spec's evidence display
 * rules: color is never the only signal -- every badge pairs an icon with
 * the literal status text.
 *
 * Hard rule: AI_SUGGESTED must never render with success/verified styling.
 * This component is the single place evidence-status color is decided, so
 * that rule can't be violated ad hoc elsewhere.
 */
const STATUS_CONFIG: Record<
  EvidenceStatus,
  { label: string; icon: React.ElementType; className: string }
> = {
  VERIFIED: {
    label: "Verified",
    icon: CheckCircle2,
    className: "bg-emerald-50 text-emerald-700 border-emerald-200",
  },
  PARTIAL: {
    label: "Partial",
    icon: AlertTriangle,
    className: "bg-amber-50 text-amber-800 border-amber-200",
  },
  OUTDATED: {
    label: "Outdated",
    icon: Clock,
    className: "bg-orange-50 text-orange-800 border-orange-200",
  },
  CONFLICTING: {
    label: "Conflicting",
    icon: AlertTriangle,
    className: "bg-red-50 text-red-700 border-red-200",
  },
  MISSING: {
    label: "Missing",
    icon: FileSearch,
    className: "bg-red-50 text-red-700 border-red-200",
  },
  AI_SUGGESTED: {
    label: "AI suggested",
    icon: Sparkles,
    className: "bg-purple-50 text-purple-700 border-purple-200",
  },
  NOT_APPLICABLE: {
    label: "Not applicable",
    icon: MinusCircle,
    className: "bg-gray-50 text-gray-600 border-gray-200",
  },
  NEEDS_MANUAL_REVIEW: {
    label: "Needs manual review",
    icon: Ban,
    className: "bg-slate-100 text-slate-700 border-slate-300",
  },
};

export function EvidenceStatusBadge({
  status,
  className,
}: {
  status: EvidenceStatus;
  className?: string;
}) {
  const config = STATUS_CONFIG[status];

  if (!config) {
    // Contract rule #6: unknown enum values must produce an explicit
    // compatibility error, not a silent fallback.
    return (
      <span
        role="alert"
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border border-red-400 bg-red-100 px-2.5 py-1 text-xs font-semibold text-red-800",
          className,
        )}
      >
        <AlertTriangle className="h-3.5 w-3.5" />
        Unknown status: {String(status)}
      </span>
    );
  }

  const Icon = config.icon;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        config.className,
        className,
      )}
    >
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {config.label}
    </span>
  );
}
