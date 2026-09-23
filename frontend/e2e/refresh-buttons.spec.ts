import { expect, test } from '@playwright/test'

import { CORS_HEADERS, stubActor } from './support/api-stubs'

test('every Refresh button displays fresh API data', async ({ page }) => {
  const caseId = 'refresh-case'
  let listTitle = 'Before cases refresh'
  let workspaceTitle = 'Before workspace refresh'
  const respond = (body: unknown) => ({
    status: 200,
    contentType: 'application/json',
    headers: CORS_HEADERS,
    body: JSON.stringify(body),
  })
  const summary = (title: string) => ({
    id: caseId,
    title,
    customer_name: 'Refresh Customer',
    deadline_at: null,
    status: 'DRAFT',
    updated_at: new Date().toISOString(),
  })

  await page.addInitScript(() => window.localStorage.clear())
  await stubActor(page)
  await page.route('**/health', (route) => route.fulfill(respond({ status: 'ok' })))
  await page.route('**/api/v1/cases', (route) => route.fulfill(respond([summary(listTitle)])))
  await page.route(`**/api/v1/cases/${caseId}`, (route) =>
    route.fulfill(respond(summary(workspaceTitle))),
  )
  await page.route(`**/api/v1/cases/${caseId}/readiness`, (route) =>
    route.fulfill(
      respond({ confirmed_required_questions: 0, total_required_questions: 0, percentage: 0 }),
    ),
  )
  for (const collection of ['questions', 'documents', 'actions']) {
    await page.route(`**/api/v1/cases/${caseId}/${collection}`, (route) =>
      route.fulfill(respond([])),
    )
  }

  await page.goto('/')
  await expect(page.locator('.table-card').getByText(listTitle)).toBeVisible()
  listTitle = 'After cases refresh'
  await page.getByRole('button', { name: 'Refresh', exact: true }).click()
  await expect(page.locator('.table-card').getByText(listTitle)).toBeVisible()
  await page.locator('.table-card').getByText(listTitle).click()
  await expect(page.getByRole('heading', { name: 'Response readiness' })).toBeVisible()

  for (const [screen, nav] of [
    ['Overview', 'Overview'],
    ['Questionnaire', 'Questionnaire'],
    ['Evidence', 'Evidence'],
    ['Actions', 'Actions'],
  ]) {
    await page.getByRole('button', { name: nav, exact: false }).first().click()
    workspaceTitle = `After ${screen} refresh`
    await page.getByRole('button', { name: 'Refresh', exact: true }).click()
    await expect(page.locator('.crumb')).toContainText(workspaceTitle)
  }
})
