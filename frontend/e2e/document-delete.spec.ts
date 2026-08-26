import { expect, test, type Page } from '@playwright/test'

import { CORS_HEADERS as CORS, stubActor } from './support/api-stubs'

/**
 * Deleting a document the parser could not read.
 *
 * `NEEDS_MANUAL_REVIEW` had no exit: retrying re-runs the same parser over the
 * same bytes. The control sits beside Retry in the document drawer, where every
 * other per-document action already lives, and is offered only for a document
 * the server will actually accept a delete for.
 */

const CASE_ID = 'case-doc-delete-0001'

const CASE_SUMMARY = {
  id: CASE_ID,
  title: 'Document delete case',
  customer_name: 'Delete Customer',
  deadline_at: null,
  status: 'DRAFT',
  updated_at: new Date().toISOString(),
  archived_at: null,
  status_before_archive: null,
}

function doc(overrides: Record<string, unknown>) {
  return {
    id: 'doc-default',
    case_id: CASE_ID,
    original_filename: 'file.txt',
    mime_type: 'text/plain',
    size_bytes: 100,
    sha256: 'a'.repeat(64),
    document_type: 'OTHER',
    processing_status: 'INDEXED',
    source_date: null,
    period_start: null,
    period_end: null,
    error: null,
    latest_job_id: null,
    created_at: new Date().toISOString(),
    ...overrides,
  }
}

const BROKEN = doc({
  id: 'doc-broken',
  original_filename: 'C-06-unreadable-scan-safety-records.pdf',
  mime_type: 'application/pdf',
  document_type: 'SAFETY_RECORD',
  processing_status: 'NEEDS_MANUAL_REVIEW',
  error: 'no extractable text found in any PDF page',
})

const GOOD = doc({
  id: 'doc-good',
  original_filename: 'A-03-scheduled-waste-consignment-fy2025.xlsx',
  document_type: 'WASTE_RECORD',
  processing_status: 'INDEXED',
})

async function gotoEvidence(page: Page, documents = [BROKEN, GOOD]) {
  const json = (body: unknown, status = 200) => ({
    status,
    contentType: 'application/json',
    headers: CORS,
    body: JSON.stringify(body),
  })
  await page.addInitScript(() => {
    window.localStorage.clear()
    window.localStorage.setItem('buktiesg.reviewerName', 'Nur Aina')
  })
  await stubActor(page)
  await page.route('**/health', (r) => r.fulfill(json({ status: 'ok' })))
  await page.route('**/api/v1/cases', (r) => r.fulfill(json([CASE_SUMMARY])))
  await page.route(`**/api/v1/cases/${CASE_ID}`, (r) => r.fulfill(json(CASE_SUMMARY)))
  await page.route(`**/api/v1/cases/${CASE_ID}/readiness`, (r) =>
    r.fulfill(json({ confirmed_required_questions: 0, total_required_questions: 4, percentage: 0 })),
  )
  await page.route(`**/api/v1/cases/${CASE_ID}/questions`, (r) => r.fulfill(json([])))
  await page.route(`**/api/v1/cases/${CASE_ID}/actions`, (r) => r.fulfill(json([])))
  await page.route(`**/api/v1/cases/${CASE_ID}/documents`, (r) => r.fulfill(json(documents)))

  await page.goto('/')
  await page.locator('.table-card').getByText('Document delete case', { exact: true }).click()
  await page.getByRole('button', { name: 'Evidence', exact: false }).first().click()
  await expect(page.getByText(BROKEN.original_filename)).toBeVisible()
}

test.describe('Deleting an unreadable document', () => {
  test('the control is offered for a document that could not be read', async ({ page }) => {
    await gotoEvidence(page)
    await page.getByText(BROKEN.original_filename).click()

    await expect(page.getByRole('button', { name: 'Retry processing' })).toBeVisible()
    await expect(page.getByRole('button', { name: 'Delete document' })).toBeVisible()
  })

  test('it is not offered for a document that parsed', async ({ page }) => {
    await gotoEvidence(page)
    await page.getByText(GOOD.original_filename).click()

    // Not merely disabled: for an indexed document deleting is not a thing the
    // server will do at all, and offering a dead control is worse than none.
    await expect(page.getByRole('button', { name: 'Delete document' })).toHaveCount(0)
    await expect(page.getByText('carries evidence that questions may cite')).toBeVisible()
  })

  test('deleting asks first, then removes the row', async ({ page }) => {
    await gotoEvidence(page)
    let deleteCalled = false
    await page.route(`**/api/v1/cases/${CASE_ID}/documents/doc-broken`, (r) => {
      deleteCalled = true
      return r.fulfill({ status: 204, headers: CORS, body: '' })
    })

    await page.getByText(BROKEN.original_filename).click()
    await page.getByRole('button', { name: 'Delete document' }).click()

    const dialog = page.getByRole('alertdialog')
    await expect(dialog).toBeVisible()
    await expect(dialog.getByText('cannot be undone', { exact: false })).toBeVisible()
    expect(deleteCalled).toBe(false)

    await page.route(`**/api/v1/cases/${CASE_ID}/documents`, (r) =>
      r.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: CORS,
        body: JSON.stringify([GOOD]),
      }),
    )
    await dialog.getByRole('button', { name: 'Delete document' }).click()

    await expect(page.getByText(BROKEN.original_filename)).toHaveCount(0)
    expect(deleteCalled).toBe(true)
  })
})
