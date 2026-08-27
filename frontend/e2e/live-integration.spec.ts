import { expect, test } from '@playwright/test'

/**
 * Full-stack check against a real, running backend. Opt-in.
 *
 * The other specs stub the API so they can run anywhere; this one does not
 * stub anything, so it is the only test that proves the browser, the client in
 * `lib/api/` and the FastAPI service actually agree end to end.
 *
 * The backend has no Docker/Postgres dependency for this run: use the
 * supported SQLite dev path. `cookie_secure` defaults to `True`, and a
 * `Secure` cookie is dropped by the browser over plain `http://localhost`, so
 * it must be overridden to `false` for this process only - never change the
 * default in `app/config.py`.
 *
 *   # terminal 1
 *   cd backend && DATABASE_URL="sqlite:///./buktiesg_live.db" DEEPSEEK_API_KEY="" uv run python scripts/init_dev_db.py
 *   cd backend && DATABASE_URL="sqlite:///./buktiesg_live.db" DEEPSEEK_API_KEY="" COOKIE_SECURE=false uv run uvicorn app.main:app --port 8000
 *   # terminal 2
 *   cd frontend && BUKTIESG_LIVE_API=1 npx playwright test live-integration --reporter=list
 *
 * On Windows PowerShell: `$env:BUKTIESG_LIVE_API=1; npx playwright test live-integration --reporter=list`
 */
const LIVE = process.env.BUKTIESG_LIVE_API === '1'

test.skip(!LIVE, 'Set BUKTIESG_LIVE_API=1 with the backend running on :8000.')

test('register, sign in, and create a case against the real API', async ({ page }) => {
  // A fresh account per run. Registration is not idempotent from the client's
  // point of view - it returns the same body whether or not the address
  // exists, deliberately - so reusing one address would silently start
  // testing "sign in as a user created by an earlier run", which is a
  // different thing and would pass even if registration were broken.
  // `Date.now()` alone is millisecond-resolution: two runs launched in the
  // same millisecond (e.g. parallel CI jobs) would collide on it.
  const runId = `${Date.now()}-${crypto.randomUUID().slice(0, 8)}`
  const email = `live-${runId}@tenggara.example`
  const password = 'live integration passphrase'
  const title = `Live integration ${runId}`

  await page.goto('/')

  await page.getByTestId('show-register').click()
  await page.getByTestId('register-email').fill(email)
  await page.getByTestId('register-org').fill(`Live Integration ${runId}`)
  await page.getByTestId('register-password').fill(password)
  await page.getByTestId('register-submit').click()

  await expect(page.getByText('Account created. Sign in below.')).toBeVisible()

  await page.getByTestId('sign-in-email').fill(email)
  await page.getByTestId('sign-in-password').fill(password)
  await page.getByTestId('sign-in-submit').click()

  // A brand-new organization owns nothing yet, so the list is empty.
  //
  // This is deliberately NOT called a test of tenant isolation - it cannot be
  // one. The browser has no route to another organization's data to be wrong
  // about; a client that failed to send credentials would get 401, not
  // someone else's cases. Isolation lives server-side and is proved by the
  // generated cross-tenant matrix in backend/tests/test_tenant_isolation.py.
  //
  // What this does prove is that signing in established a session the
  // workspace actually reads through. A list rendered from a stale response,
  // a cached fixture, or a global unscoped query would put rows here.
  await expect(page.getByTestId('new-case-button')).toBeVisible()
  await expect(page.locator('[data-testid^="case-row-"]')).toHaveCount(0)

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
