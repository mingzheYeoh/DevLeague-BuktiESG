import { expect, test, type Page } from '@playwright/test'

/**
 * The generated `customer-response-summary.txt`.
 *
 * This is the one artefact that leaves the building, so a figure in it that
 * needs explaining is worse than one on screen. Its readiness line counts
 * required answers and its unresolved line counted a mixture — required
 * answers, then every question, then every question again — with no
 * denominators, so "14 required answers unconfirmed, 20 evidence gaps" read as
 * more gaps than there are answers.
 */

const CASE_ID = 'case-export-0001'
const CORS = { 'Access-Control-Allow-Origin': '*' }

const CASE_SUMMARY = {
  id: CASE_ID,
  title: 'Export case',
  customer_name: 'Export Customer',
  deadline_at: null,
  status: 'DRAFT',
  updated_at: new Date().toISOString(),
  archived_at: null,
  status_before_archive: null,
}

/** 20 questions, 14 required, all PARTIAL and unreviewed — the sample shape. */
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

async function gotoExport(page: Page) {
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
  await page.route(`**/api/v1/cases/${CASE_ID}/documents`, (r) => r.fulfill(json([])))
  await page.route(`**/api/v1/cases/${CASE_ID}/actions`, (r) => r.fulfill(json([])))

  await page.goto('/')
  await page.locator('.table-card').getByText('Export case', { exact: true }).click()
  await page.getByRole('button', { name: 'Export', exact: false }).first().click()
  await expect(page.getByRole('button', { name: /marked-up draft/ })).toBeVisible()
}

test('every figure in the summary states what it counts', async ({ page }) => {
  await gotoExport(page)
  await page.getByRole('button', { name: /marked-up draft/ }).click()

  const download = await Promise.race([
    page.waitForEvent('download'),
    page.getByRole('button', { name: 'Download package' }).click().then(() => page.waitForEvent('download')),
  ])
  expect(download.suggestedFilename()).toBe('customer-response-summary.txt')

  const stream = await download.createReadStream()
  const text = await new Promise<string>((resolve, reject) => {
    let out = ''
    stream.on('data', (c) => (out += c))
    stream.on('end', () => resolve(out))
    stream.on('error', reject)
  })

  // The readiness line already named its denominator; the unresolved figures did not.
  expect(text).toContain('0 of 14 required answers confirmed')
  expect(text).toContain('14 of 14 required answers unconfirmed')
  expect(text).toContain('20 of 20 questions have an unresolved evidence gap')
  expect(text).toContain('0 of 20 questions report a source conflict')

  // The old bare-number form must be gone.
  expect(text).not.toContain('20 evidence gaps')
})
