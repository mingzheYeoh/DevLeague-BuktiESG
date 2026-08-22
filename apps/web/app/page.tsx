"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api, ApiError } from "@/lib/api-client";

/**
 * First Vertical Slice, step 1: Create Case.
 *
 * On success, navigates to the Case detail page (upload + questions).
 * Scope is deliberately narrow -- see README-Team-Specs.md "First Vertical
 * Slice" and the CEO task brief. This is not the full Create Case wizard
 * from the Main Spec.
 */
export default function CreateCasePage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [customerName, setCustomerName] = useState("");
  const [deadlineAt, setDeadlineAt] = useState("");
  const [periodStart, setPeriodStart] = useState("");
  const [periodEnd, setPeriodEnd] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = title.trim() !== "" && customerName.trim() !== "";

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit || submitting) return;

    setSubmitting(true);
    setError(null);

    try {
      const created = await api.createCase({
        title: title.trim(),
        customer_name: customerName.trim(),
        deadline_at: deadlineAt ? new Date(deadlineAt).toISOString() : null,
        reporting_period:
          periodStart && periodEnd
            ? { start: periodStart, end: periodEnd }
            : null,
      });
      router.push(`/cases/${created.id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          "Could not reach the BuktiESG API. Is the backend running at the configured API URL?",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main>
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-[#17212B]">
          Create Case
        </h1>
        <p className="mt-1 text-sm text-[#667085]">
          Start a new customer ESG questionnaire response.
        </p>
      </div>

      <Card className="max-w-xl">
        <CardHeader>
          <CardTitle>Case details</CardTitle>
          <CardDescription>
            Fields marked required must be filled before the Case can be
            created.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-4"
            data-testid="create-case-form"
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="title">Case title *</Label>
              <Input
                id="title"
                data-testid="case-title-input"
                placeholder="Major Customer ESG Questionnaire 2026"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="customer_name">Customer name *</Label>
              <Input
                id="customer_name"
                data-testid="customer-name-input"
                placeholder="Demo FMCG Customer"
                value={customerName}
                onChange={(e) => setCustomerName(e.target.value)}
                required
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label htmlFor="deadline_at">Deadline</Label>
              <Input
                id="deadline_at"
                type="date"
                value={deadlineAt}
                onChange={(e) => setDeadlineAt(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="period_start">Reporting period start</Label>
                <Input
                  id="period_start"
                  type="date"
                  value={periodStart}
                  onChange={(e) => setPeriodStart(e.target.value)}
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <Label htmlFor="period_end">Reporting period end</Label>
                <Input
                  id="period_end"
                  type="date"
                  value={periodEnd}
                  onChange={(e) => setPeriodEnd(e.target.value)}
                />
              </div>
            </div>

            {error ? (
              <p role="alert" className="text-sm text-red-700">
                {error}
              </p>
            ) : null}

            <Button
              type="submit"
              disabled={!canSubmit || submitting}
              data-testid="create-case-submit"
            >
              {submitting ? "Creating..." : "Create Case"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
