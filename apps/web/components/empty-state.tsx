import { AlertTriangle, Inbox } from "lucide-react";
import { Button } from "@/components/ui/button";

export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed border-[#DCE4EC] bg-[#F7F9FC] px-6 py-12 text-center">
      <Inbox className="h-8 w-8 text-[#667085]" aria-hidden="true" />
      <p className="text-sm font-medium text-[#17212B]">{title}</p>
      {description ? (
        <p className="max-w-sm text-sm text-[#667085]">{description}</p>
      ) : null}
    </div>
  );
}

export function ErrorState({
  title,
  description,
  onRetry,
}: {
  title: string;
  description?: string;
  onRetry?: () => void;
}) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-6 py-12 text-center"
    >
      <AlertTriangle className="h-8 w-8 text-red-600" aria-hidden="true" />
      <p className="text-sm font-medium text-red-800">{title}</p>
      {description ? (
        <p className="max-w-sm text-sm text-red-700">{description}</p>
      ) : null}
      {onRetry ? (
        <Button variant="secondary" size="sm" className="mt-2" onClick={onRetry}>
          Retry
        </Button>
      ) : null}
    </div>
  );
}
