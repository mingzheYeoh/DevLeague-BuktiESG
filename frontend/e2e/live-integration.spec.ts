import { expect, test } from '@playwright/test'

/**
 * Full-stack check against a real, running backend. Opt-in.
 *
 * The other specs stub the API so they can run anywhere; this one does not
 * stub anything, so it is the only test that proves the browser, the client in
 * `lib/api/` and the FastAPI service actually agree end to end.
 *
 *   # terminal 1
 *   cd backend && uv run python scripts/init_dev_db.py && uv run uvicorn app.main:app --port 8000
 *   # terminal 2
 *   cd frontend && BUKTIESG_LIVE_API=1 npx playwright test live-integration
 *
 * On Windows PowerShell: `$env:BUKTIESG_LIVE_API=1; npx playwright test live-integration`
 */
const LIVE = process.env.BUKTIESG_LIVE_API === '1'

test.skip(!LIVE, 'Set BUKTIESG_LIVE_API=1 with the backend running on :8000.')

test('create a case against the real API and see it in the real list', async ({ page }) => {
  const title = `Live integration ${Date.now()}`

  await page.addInitScript(() => window.localStorage.clear())
  await page.goto('/')

  // The offline banner must not be showing: the API is up.
  await expect(page.getByText('Backend unreachable', { exact: false })).toHaveCount(0)

  await page.getByTestId('new-case-button').click()
  await page.getByTestId('case-title-input').fill(title)
  await page.getByTestId('customer-name-input').fill('Live Integration Customer')
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-submit').click()

  // Landed on the case dashboard, with readiness fetched from the server.
  await expect(page.getByRole('heading', { name: 'Response readiness' })).toBeVisible()

  // And the case is really persisted: it comes back in the server's list.
  // Scoped to the table, because the title also appears in the breadcrumb.
  const listedCase = page.locator('.table-card').getByText(title, { exact: true })
  await page.getByRole('button', { name: 'Cases', exact: true }).click()
  await expect(listedCase).toBeVisible()

  // Surviving a reload proves nothing was only in React state.
  await page.reload()
  await expect(listedCase).toBeVisible()
})
