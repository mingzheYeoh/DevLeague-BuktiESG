import { expect, test } from '@playwright/test'

import { ACTOR, CORS_HEADERS, stubActor } from './support/api-stubs'

/**
 * A session dying mid-use.
 *
 * The behaviour under test is that the workspace is *not* unmounted: this app
 * has long forms — a review justification, an action description — and losing
 * them to a 14-day session expiry is a worse outcome than the expiry itself.
 */
test('a mid-session 401 raises the overlay and leaves typed input intact', async ({ page }) => {
  await stubActor(page)
  await page.route('**/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ status: 'ok' }),
    }),
  )

  let casesAuthorised = true
  await page.route('**/api/v1/cases', (route) =>
    casesAuthorised
      ? route.fulfill({
          status: 200,
          contentType: 'application/json',
          headers: CORS_HEADERS,
          body: JSON.stringify([]),
        })
      : route.fulfill({
          status: 401,
          contentType: 'application/json',
          headers: CORS_HEADERS,
          body: JSON.stringify({
            detail: { error: { code: 'NOT_AUTHENTICATED', message: 'Sign in to continue.' } },
          }),
        }),
  )

  await page.goto('/')
  await page.getByTestId('new-case-button').click()
  await page.getByTestId('case-title-input').fill('Half-written case title')

  // The session dies. The next request the user makes finds out.
  casesAuthorised = false
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-submit').click()

  await expect(page.getByTestId('reauth-overlay')).toBeVisible()

  // A dialog that does not take focus gives a screen-reader user no signal it
  // opened, and the visible scrim gives a keyboard user none either.
  await expect(page.getByTestId('sign-in-email')).toBeFocused()

  // aria-modal="true" tells assistive tech the rest of the page is inert.
  // Make that true rather than merely claimed: tab past everything the
  // overlay offers and confirm focus never lands in the workspace behind it.
  for (let i = 0; i < 8; i += 1) await page.keyboard.press('Tab')
  const focusStayedInTheDialog = await page.evaluate(() => {
    const active = document.activeElement
    if (!active || active === document.body) return true
    return Boolean(active.closest('[data-testid="reauth-overlay"]'))
  })
  expect(focusStayedInTheDialog).toBe(true)

  // The point of the whole design: the tree underneath is still mounted. Read
  // the title from the review step, which renders it - rather than from step
  // one's input, which the wizard unmounts on the way here. That the value is
  // still being RENDERED is the stronger claim anyway: a detached DOM node
  // holding the right string would prove less.
  await expect(page.getByText('Half-written case title')).toBeVisible()
})

test('signing in again dismisses the overlay and leaves the user where they were', async ({
  page,
}) => {
  let authorised = true

  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify(ACTOR),
    }),
  )
  await page.route('**/api/v1/auth/login', (route) => {
    authorised = true
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ status: 'signed in' }),
    })
  })
  await page.route('**/health', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ status: 'ok' }),
    }),
  )
  await page.route('**/api/v1/cases', (route) =>
    authorised
      ? route.fulfill({
          status: 200,
          contentType: 'application/json',
          headers: CORS_HEADERS,
          body: JSON.stringify([]),
        })
      : route.fulfill({
          status: 401,
          contentType: 'application/json',
          headers: CORS_HEADERS,
          body: JSON.stringify({
            detail: { error: { code: 'NOT_AUTHENTICATED', message: 'Sign in to continue.' } },
          }),
        }),
  )

  await page.goto('/')
  await page.getByTestId('new-case-button').click()
  await page.getByTestId('case-title-input').fill('Survives the overlay')

  authorised = false
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-continue').click()
  await page.getByTestId('create-case-submit').click()
  await expect(page.getByTestId('reauth-overlay')).toBeVisible()

  await page.getByTestId('sign-in-email').fill('member@tenggara.example')
  await page.getByTestId('sign-in-password').fill('fixture passphrase')
  await page.getByTestId('sign-in-submit').click()

  await expect(page.getByTestId('reauth-overlay')).toHaveCount(0)
  await expect(page.getByText('Survives the overlay')).toBeVisible()
})
