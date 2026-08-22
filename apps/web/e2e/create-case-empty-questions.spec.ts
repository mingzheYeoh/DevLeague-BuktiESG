import { expect, test } from "@playwright/test";

/**
 * First Vertical Slice smoke test: load create-case page -> fill form ->
 * see empty questions state.
 *
 * The CTO's backend (apps/api) may not exist yet or may still be changing,
 * so this test stubs the two contract endpoints it touches
 * (POST /api/v1/cases, GET /api/v1/cases/{id}/questions) at the network
 * layer, using exactly the shapes documented in
 * docs/spec/Shared-Integration-Contract.md §7.1 and §7.3. It does not
 * start or require a real backend process.
 *
 * This test was run and passes against a local dev server (see
 * apps/web build/verification notes). Run with:
 *   pnpm --dir apps/web dev   (in one terminal)
 *   pnpm --dir apps/web test:e2e   (in another)
 */
test("create case then see empty questions state", async ({ page }) => {
  const caseId = "case_e2e_test";

  await page.route("**/api/v1/cases", async (route) => {
    if (route.request().method() === "OPTIONS") {
      // CORS preflight, since the app origin (web) and API base URL
      // differ in this test environment.
      return route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }
    if (route.request().method() !== "POST") {
      return route.fallback();
    }
    await route.fulfill({
      status: 201,
      contentType: "application/json",
      headers: { "Access-Control-Allow-Origin": "*" },
      body: JSON.stringify({
        id: caseId,
        title: "Major Customer ESG Questionnaire 2026",
        customer_name: "Demo FMCG Customer",
        deadline_at: null,
        reporting_period: null,
        status: "DRAFT",
        readiness: {
          confirmed_required_questions: 0,
          total_required_questions: 0,
          percentage: 0,
        },
        evidence_status_counts: {
          VERIFIED: 0,
          PARTIAL: 0,
          OUTDATED: 0,
          CONFLICTING: 0,
          MISSING: 0,
          AI_SUGGESTED: 0,
          NOT_APPLICABLE: 0,
          NEEDS_MANUAL_REVIEW: 0,
        },
        unconfirmed_answer_count: 0,
        updated_at: new Date().toISOString(),
      }),
    });
  });

  await page.route(`**/api/v1/cases/${caseId}/questions`, async (route) => {
    if (route.request().method() === "OPTIONS") {
      return route.fulfill({
        status: 204,
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET,POST,PATCH,DELETE,OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type",
        },
      });
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      headers: { "Access-Control-Allow-Origin": "*" },
      body: JSON.stringify([]),
    });
  });

  await page.goto("/");

  await page.getByTestId("case-title-input").fill(
    "Major Customer ESG Questionnaire 2026",
  );
  await page.getByTestId("customer-name-input").fill("Demo FMCG Customer");
  await page.getByTestId("create-case-submit").click();

  await expect(page).toHaveURL(`/cases/${caseId}`);
  await expect(page.getByText("No questions yet")).toBeVisible();
});
