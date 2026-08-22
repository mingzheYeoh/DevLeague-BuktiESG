"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { UploadPanel } from "@/components/upload-panel";
import { QuestionsList } from "@/components/questions-list";
import { ErrorState } from "@/components/empty-state";
import { api, ApiError } from "@/lib/api-client";
import type { QuestionListItem } from "@/lib/types";

/**
 * Case detail page: upload the questionnaire, then review identified
 * questions with their evidence status and source location, and create a
 * SUBMISSION action. Scope: First Vertical Slice only.
 */
export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const caseId = params.id;

  const [questions, setQuestions] = useState<QuestionListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadQuestions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await api.getQuestions(caseId);
      setQuestions(result);
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
    void loadQuestions();
  }, [loadQuestions]);

  return (
    <main className="flex flex-col gap-8">
      <div>
        <h1 className="text-2xl font-semibold text-[#17212B]">
          Case {caseId}
        </h1>
        <p className="mt-1 text-sm text-[#667085]">
          Upload the questionnaire, then review identified questions and
          their evidence status.
        </p>
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[#667085]">
          Intake
        </h2>
        <UploadPanel caseId={caseId} onUploaded={() => void loadQuestions()} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-[#667085]">
          Questions
        </h2>
        {loading ? (
          <p className="text-sm text-[#667085]" data-testid="questions-loading">
            Loading questions...
          </p>
        ) : error ? (
          <ErrorState
            title="Could not load questions"
            description={error}
            onRetry={() => void loadQuestions()}
          />
        ) : (
          <QuestionsList caseId={caseId} questions={questions} />
        )}
      </section>
    </main>
  );
}
