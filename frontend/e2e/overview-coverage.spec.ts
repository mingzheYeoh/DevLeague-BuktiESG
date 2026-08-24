import { expect, test, type Page } from '@playwright/test'

/**
 * Evidence coverage panel on the Overview screen.
 *
 * The panel counts questions. The warning inside it counts documents. Both
 * were labelled "needs manual review", so a case with one unreadable file and
 * no question blocked by it read as a contradiction: a row saying 0 directly
 * above a warning saying 1.
 *
 * Both numbers were correct. The panel was not.
 */

const CASE_ID = 'case-coverage-0001'
const CORS = { 'Access-Control-Allow-Origin': '*' }

const CASE_SUMMARY = {
  id: CASE_ID,
  title: 'Coverage case',
  customer_name: 'Coverage Customer',
  deadline_at: null,
  status: 'DRAFT',
  updated_at: new Date().toISOString(),
  archived_at: null,
  status_before_archive: null,
}

/** Every question has readable evidence, so none is blocked by the bad scan. */
const QUESTIONS = Array.from({ length: 20 }, (_, i) => ({
  id: `q-${i}`,
  external_question_id: `Q-E-${String(i + 1).padStart(2, '0')}`,
  question_text: 'Report something measurable for the reporting period.',
  is_required: i < 14,
  pillar: 'E',
  sedg_topic_code: 'E1',
  sedg_disclosure_code: 'E1.1',
  evidence_status: 'PARTIAL',
  review_status: 'UNREVIEWED',
  priority_score: null,
  owner_name: null,
  source_location: null,
  status_reason: 'Evidence exists but coverage is incomplete.',
  status_points: [],
  evidence_location: null,
  mapping_rationale: null,
  evidence_excerpt: null,
  evidence_claim_supported: null,
  evidence_document_id: null,
  evidence_document_name: null,
  evidence_link_id: null,
  evidence_accepted_by: null,
  evidence_candidate_count: 1,
}))

/** One document the parser could not read at all. */
const DOCUMENTS = [
  {
    id: 'doc-scan',
    case_id: CASE_ID,
    original_filename: 'C-06-unreadable-scan-safety-records.pdf',
    mime_type: 'application/pdf',
    size_bytes: 651,
    sha256: 'a'.repeat(64),
    document_type: 'SAFETY_RECORD',
    processing_status: 'NEEDS_MANUAL_REVIEW',
    source_date: null,
    period_start: null,
    period_end: null,
    error: 'no extractable text found in any PDF page',
    latest_job_id: null,
    created_at: new Date().toISOString(),
  },
]

async function gotoOverview(page: Page) {
  const json = (body: unknown) => ({
    status: 200,
    contentType: 'application/json',
    headers: CORS,
    body: JSON.stringify(body),
  })
  await page.addInitScript(() => {
    window.localStorage.clear()
    window.localStorage.setItem('buktiesg.reviewerName', 'Nur Aina')
  })
  await page.route('**/health', (r) => r.fulfill(json({ status: 'ok' })))
  await page.route('**/api/v1/cases', (r) => r.fulfill(json([CASE_SUMMARY])))
  await page.route(`**/api/v1/cases/${CASE_ID}`, (r) => r.fulfill(json(CASE_SUMMARY)))
  await page.route(`**/api/v1/cases/${CASE_ID}/readiness`, (r) =>
    r.fulfill(json({ confirmed_required_questions: 0, total_required_questions: 14, percentage: 0 })),
  )
  await page.route(`**/api/v1/cases/${CASE_ID}/questions`, (r) => r.fulfill(json(QUESTIONS)))
  await page.route(`**/api/v1/cases/${CASE_ID}/documents`, (r) => r.fulfill(json(DOCUMENTS)))
  await page.route(`**/api/v1/cases/${CASE_ID}/actions`, (r) => r.fulfill(json([])))

  await page.goto('/')
  await page.locator('.table-card').getByText('Coverage case', { exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Evidence coverage' })).toBeVisible()
}

test.describe('Evidence coverage panel', () => {
  test('the question-scoped row says what it counts', async ({ page }) => {
    await gotoOverview(page)

    // "Needs manual review" is the document processing_status verbatim, so a
    // row carrying it cannot be read as anything but the document count.
    await expect(page.getByText('Needs manual review', { exact: true })).toHaveCount(0)
    await expect(
      page.getByText('Questions blocked by an unreadable file', { exact: true }),
    ).toBeVisible()
  })

  test('the warning explains why no question is blocked', async ({ page }) => {
    await gotoOverview(page)

    await expect(page.getByText('1 document could not be processed')).toBeVisible()
    // The 0 above it is the answer to the reader's obvious next question.
    await expect(
      page.getByText('No question is blocked by it', { exact: false }),
    ).toBeVisible()
  })
})

