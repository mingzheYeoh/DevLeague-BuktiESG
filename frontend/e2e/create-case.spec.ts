import { expect, test, type Page } from '@playwright/test'

import { CORS_HEADERS as CORS, stubActor } from './support/api-stubs'

/**
 * Smoke test: cases list -> create a case -> land on an honestly empty case.
 *
 * The API is stubbed at the network layer with the shapes the real server
 * returns (`CaseSummary`, `ReadinessSummary`, and bare arrays for questions,
 * documents and actions). Those shapes are the point of the test: if the
 * client starts expecting the richer Contract-shaped CaseSummary again, or
 * stops reading the flat one, this fails.
 *
 * Replacing the previous `apps/web` spec, which stubbed a CaseSummary shape
 * the server never actually sent (nested `readiness`, `evidence_status_counts`,
 * and the removed `AI_SUGGESTED` status).
 */

const CASE_ID = 'case-e2e-0001'

const CASE_SUMMARY = {
  id: CASE_ID,
  title: 'E2E customer questionnaire',
  customer_name: 'E2E Customer',
  deadline_at: null,
  status: 'DRAFT',
  updated_at: new Date().toISOString(),
}


async function stubApi(page: Page, { cases, deleteDelayMs = 0 }: { cases: unknown[]; deleteDelayMs?: number }) {
  const listed = [...cases]

  await stubActor(page)
  await page.route('**/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS,
      body: JSON.stringify({ status: 'ok' }),
    }),
  )

  await page.route('**/api/v1/cases', async (route) => {
    const method = route.request().method()
    if (method === 'OPTIONS') {
      return route.fulfill({
        status: 204,
        headers: {
          ...CORS,
          'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
        },
      })
    }
    if (method === 'POST') {
      listed.unshift(CASE_SUMMARY)
      return route.fulfill({
        status: 201,
        contentType: 'application/json',
        headers: CORS,
        body: JSON.stringify(CASE_SUMMARY),
      })
    }
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS,
      body: JSON.stringify(listed),
    })
  })

  await page.route(`**/api/v1/cases/${CASE_ID}`, async (route) => {
    if (route.request().method() === 'DELETE') {
      await new Promise((resolve) => setTimeout(resolve, deleteDelayMs))
      listed.splice(listed.findIndex((item) => item === CASE_SUMMARY), 1)
      return route.fulfill({ status: 204, headers: CORS })
    }
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS,
      body: JSON.stringify(CASE_SUMMARY),
    })
  })

  await page.route(`**/api/v1/cases/${CASE_ID}/readiness`, (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS,
      body: JSON.stringify({
        confirmed_required_questions: 0,
        total_required_questions: 0,
        percentage: 0.0,
      }),
    }),
  )

  for (const collection of ['questions', 'documents', 'actions']) {
    await page.route(`**/api/v1/cases/${CASE_ID}/${collection}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: CORS,
        body: JSON.stringify([]),
      }),
    )
  }
}

test.beforeEach(async ({ page }) => {
  // The selected case is remembered in localStorage; start each test clean.
  await page.addInitScript(() => window.localStorage.clear())
})

test('an empty case list says so rather than showing sample data', async ({ page }) => {
  await stubApi(page, { cases: [] })
  await page.goto('/')

  await expect(page.getByRole('heading', { name: 'Response cases' })).toBeVisible()
  await expect(page.getByText('No cases yet')).toBeVisible()
})

test('create a case then land on an empty case dashboard', async ({ page }) => {
  await stubApi(page, { cases: [] })
  await page.goto('/')

  await page.getByTestId('new-case-button').click()

  await page.getByTestId('case-title-input').fill('E2E customer questionnaire')
  await page.getByTestId('customer-name-input').fill('E2E Customer')

  // Details -> Reporting scope -> Questionnaire -> Review
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()

  await page.getByTestId('create-case-submit').click()

  await expect(page.getByRole('heading', { name: 'Response readiness' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Upload questionnaire', exact: true })).toBeVisible()
  await expect(page.locator('.readiness, .dashboard-grid')).toHaveCount(0)
  await page.getByRole('button', { name: 'Upload questionnaire', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Documents & evidence' })).toBeVisible()
})

test('a questionnaire with no parsed questions shows the empty state, not a fake list', async ({
  page,
}) => {
  await stubApi(page, { cases: [CASE_SUMMARY] })
  await page.goto('/')

  await page.getByText('E2E customer questionnaire').first().click()
  await page.getByRole('button', { name: 'Questionnaire', exact: false }).first().click()

  await expect(page.getByText('No questions identified yet')).toBeVisible()
})

test('case deletion waits for slow stored-file cleanup', async ({ page }) => {
  await stubApi(page, { cases: [CASE_SUMMARY], deleteDelayMs: 16_000 })
  await page.goto('/')

  await page.getByRole('button', { name: 'Actions for E2E customer questionnaire' }).click()
  await page.getByRole('menuitem', { name: /delete/i }).click()
  await page.getByRole('button', { name: 'Delete case' }).click()

  await expect(page.getByText('No cases yet')).toBeVisible({ timeout: 25_000 })
})

test('the backend being down is reported instead of hidden', async ({ page }) => {
  await stubActor(page)
  await page.route('**/health', (route) => route.abort())
  await page.route('**/api/v1/cases', (route) => route.abort())
  await page.goto('/')

  await expect(page.getByText('Backend unreachable', { exact: false })).toBeVisible()
})


test('creating with a questionnaire also opens Overview', async ({ page }) => {
  await stubApi(page, { cases: [] })
  const document = {
    id: 'questionnaire-upload', case_id: CASE_ID,
    original_filename: 'questionnaire.xlsx', document_type: 'QUESTIONNAIRE',
    processing_status: 'INDEXED', created_at: new Date().toISOString(),
    mime_type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    size_bytes: 4, sha256: 'a'.repeat(64), latest_job_id: null,
  }
  await page.route(`**/api/v1/cases/${CASE_ID}/documents`, route => route.fulfill({
    status: route.request().method() === 'POST' ? 201 : 200,
    contentType: 'application/json', headers: CORS,
    body: JSON.stringify(route.request().method() === 'POST' ? document : [document]),
  }))
  await page.goto('/')
  await page.getByTestId('new-case-button').click()
  await page.getByTestId('case-title-input').fill(CASE_SUMMARY.title)
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  // Network stub isolates navigation from workbook parsing.
  await page.locator('input[type="file"]').setInputFiles({
    name: 'questionnaire.xlsx', mimeType: document.mime_type, buffer: Buffer.from('stub'),
  })
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-submit').click()
  await expect(page.getByRole('heading', { name: 'Response readiness' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Check questionnaire', exact: true })).toBeVisible()
})
