import { expect, test } from '@playwright/test'

import { ACTOR, CORS_HEADERS } from './support/api-stubs'

/**
 * The gate. Three behaviours, each closing a defect that exists today.
 */

test('an unauthenticated visit shows the sign-in screen, not an empty workspace', async ({
  page,
}) => {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({
        detail: { error: { code: 'NOT_AUTHENTICATED', message: 'Sign in to continue.' } },
      }),
    }),
  )

  await page.goto('/')

  await expect(page.getByTestId('sign-in-form')).toBeVisible()
  // The specific regression: today this renders the workspace with an error
  // box claiming the backend is unreachable, and a Retry that 401s forever.
  await expect(page.getByText('Could not load this from the API')).toHaveCount(0)
  await expect(page.getByRole('button', { name: 'Cases' })).toHaveCount(0)
})

test('correct credentials open the workspace', async ({ page }) => {
  let authenticated = false

  await page.route('**/api/v1/auth/me', (route) =>
    authenticated
      ? route.fulfill({
          status: 200,
          contentType: 'application/json',
          headers: CORS_HEADERS,
          body: JSON.stringify(ACTOR),
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
  await page.route('**/api/v1/auth/login', (route) => {
    authenticated = true
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
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify([]),
    }),
  )

  await page.goto('/')
  await page.getByTestId('sign-in-email').fill('member@tenggara.example')
  await page.getByTestId('sign-in-password').fill('fixture passphrase')
  await page.getByTestId('sign-in-submit').click()

  await expect(page.getByRole('button', { name: 'Cases' })).toBeVisible()
  await expect(page.getByTestId('sign-in-form')).toHaveCount(0)
})

test('a wrong password is shown in the form and does not stack a second prompt', async ({
  page,
}) => {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({
        detail: { error: { code: 'NOT_AUTHENTICATED', message: 'Sign in to continue.' } },
      }),
    }),
  )
  await page.route('**/api/v1/auth/login', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({
        detail: {
          error: {
            code: 'INVALID_CREDENTIALS',
            message: 'That email and password do not match.',
          },
        },
      }),
    }),
  )

  await page.goto('/')
  await page.getByTestId('sign-in-email').fill('member@tenggara.example')
  await page.getByTestId('sign-in-password').fill('wrong')
  await page.getByTestId('sign-in-submit').click()

  await expect(page.getByText('That email and password do not match.')).toBeVisible()
  // An auth failure must not be dressed as a backend outage. The body text
  // being right is not enough - that assertion passed while the heading above
  // it said the API could not be reached.
  await expect(page.getByText('Could not load this from the API')).toHaveCount(0)
  await expect(page.getByText('Sign-in failed')).toBeVisible()
  // Forward-looking: ReauthOverlay does not exist until the next task, so this
  // line cannot fail yet. It is here so that the moment an overlay CAN render,
  // a 401 from `login` reaching the session-lost announcement is caught. The
  // next task proves it has teeth by removing the guard and watching this go
  // red.
  await expect(page.getByTestId('reauth-overlay')).toHaveCount(0)
  await expect(page.getByTestId('sign-in-form')).toHaveCount(1)
})

test('registration tells the user to sign in, not to check an email that does not exist', async ({
  page,
}) => {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 401,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({
        detail: { error: { code: 'NOT_AUTHENTICATED', message: 'Sign in to continue.' } },
      }),
    }),
  )
  await page.route('**/api/v1/auth/register', (route) =>
    route.fulfill({
      status: 201,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ status: 'check your email to finish signing up' }),
    }),
  )

  await page.goto('/')
  await page.getByTestId('show-register').click()
  await page.getByTestId('register-email').fill('new@tenggara.example')
  await page.getByTestId('register-org').fill('Tenggara Precision Sdn. Bhd.')
  await page.getByTestId('register-password').fill('a sufficiently long passphrase')
  await page.getByTestId('register-submit').click()

  await expect(page.getByText('Account created. Sign in below.')).toBeVisible()
  // Task 11 has not landed. Repeating the server's line would strand the user
  // in front of an inbox nothing will arrive in.
  await expect(page.getByText('check your email')).toHaveCount(0)
  await expect(page.getByTestId('sign-in-email')).toHaveValue('new@tenggara.example')
})
