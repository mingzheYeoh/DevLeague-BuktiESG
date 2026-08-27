import { expect, test, type Page } from '@playwright/test'

import { CORS_HEADERS as CORS, stubActor } from './support/api-stubs'

/**
 * Panels that count questions, and the denominators they count against.
 *
 * The panel counts questions. The warning inside it counts documents. Both
 * were labelled "needs manual review", so a case with one unreadable file and
 * no question blocked by it read as a contradiction: a row saying 0 directly
 * above a warning saying 1.
 *
 * Both numbers were correct. The panel was not. The readiness tiles and the
 * questionnaire summary strip had the same shape of defect: readiness is
 * required-only while review is every question, so `0 of 14` sat beside a bare
 * `20` and the pair implied a shared denominator that does not exist.
 */

const CASE_ID = 'case-coverage-0001'

const CASE_SUMMARY = {
  id: CASE_ID,
  title: 'Coverage case',
  customer_name: 'Coverage Customer',
  deadline_at: null,
  status: 'DRAFT',
  updated_at: new Date().toISOString(),
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
  })
  await stubActor(page)
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


test.describe('Readiness stats', () => {
  test('each tile names the population it counts', async ({ page }) => {
    // 20 questions, 14 of them required, none reviewed. So "Confirmed" is out
    // of 14 and "Awaiting review" is out of 20, and side by side without their
    // denominators the pair reads as 0 + 20 = 20 against a stated total of 14.
    await gotoOverview(page)

    const stats = page.locator('.readiness-stats')
    await expect(stats.getByText('of 14 required', { exact: true })).toBeVisible()
    await expect(stats.getByText('of 20 questions', { exact: true })).toBeVisible()

    // The old sub-labels named neither population.
    await expect(stats.getByText('Required answers', { exact: true })).toHaveCount(0)
    await expect(stats.getByText('Human review needed', { exact: true })).toHaveCount(0)
  })
})


test.describe('Questionnaire summary strip', () => {
  test('the review count names its population too', async ({ page }) => {
    await gotoOverview(page)
    await page.getByRole('button', { name: 'Questionnaire', exact: false }).first().click()
    await expect(page.getByRole('heading', { name: 'Customer questionnaire' })).toBeVisible()

    const strip = page.locator('.summary-strip')
    await expect(strip.getByText('required confirmed', { exact: true })).toBeVisible()
    // Every other figure in the strip counts all 20 questions, not the 14 the
    // first one does. Each says so rather than borrowing the first's total.
    await expect(strip.getByText('of 20 awaiting human review', { exact: true })).toBeVisible()
    await expect(strip.getByText('of 20 with an evidence gap', { exact: true })).toBeVisible()
    await expect(strip.getByText('of 20 reporting a source conflict', { exact: true })).toBeVisible()
  })
})


test.describe('Row menu alignment', () => {
  test('every item in the menu starts at the same left edge', async ({ page }) => {
    await stubActor(page)
    await page.route('**/health', (r) =>
      r.fulfill({ status: 200, contentType: 'application/json', headers: CORS, body: '{"status":"ok"}' }),
    )
    await page.route('**/api/v1/cases', (r) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: CORS,
        body: JSON.stringify([{ ...CASE_SUMMARY, id: 'c-draft', title: 'Draft case', status: 'DRAFT' }]),
      }),
    )
    await page.goto('/')
    await page.getByTestId('case-menu-c-draft').click()

    const menu = page.getByRole('menu')
    const del = menu.getByRole('menuitem', { name: 'Delete' })
    await expect(del).toBeVisible()

    // `.danger` carries `justify-content: center` from the shared button rule,
    // and the menu rule never overrode it — so Delete centred its icon and
    // label inside a full-width button instead of starting at the left edge.
    //
    // This used to compare Delete against Archive. Archiving is gone and Delete
    // is the only item left, so there is no sibling to misalign against — but
    // the defect is still reachable, because it is about one button centring
    // its own contents. Measured directly instead: a left-aligned item starts
    // its icon within the button's padding; a centred one pushes it far in.
    const button = await del.boundingBox()
    const icon = await del.locator('svg').boundingBox()
    expect(button).not.toBeNull()
    expect(icon).not.toBeNull()
    expect(icon!.x - button!.x).toBeLessThan(24)
  })
})

