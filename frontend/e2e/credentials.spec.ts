import { expect, test } from '@playwright/test'

import { CORS_HEADERS } from './support/api-stubs'

/**
 * The session cookie must actually leave the browser.
 *
 * This is the one thing no other spec can catch: every other test stubs the
 * API and does not care who is calling. A `fetch` without
 * `credentials: 'include'` omits cookies on a cross-origin request, silently,
 * and every response still arrives - stubbed. The app would look fine here and
 * be 401 everywhere in real life.
 *
 * The cookie is set on domain `localhost` with no port, which is not a
 * shortcut: cookies are scoped by host and ignore port (RFC 6265), unlike
 * CORS, which is scoped by origin. One cookie covers :3000 and :8000.
 */
test('API requests carry the session cookie', async ({ context, page }) => {
  await context.addCookies([
    { name: 'bukti_session', value: 'test-session-token', domain: 'localhost', path: '/' },
  ])

  let healthCookie: string | undefined
  await page.route('**/health', (route) => {
    healthCookie = route.request().headers()['cookie']
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ status: 'ok' }),
    })
  })

  await page.route('**/api/v1/**', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify([]),
    }),
  )

  await page.goto('/')
  await expect.poll(() => healthCookie).toContain('bukti_session=test-session-token')
})
