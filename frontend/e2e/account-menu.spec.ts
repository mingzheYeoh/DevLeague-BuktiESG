import { expect, test } from '@playwright/test'

import { ACTOR, CORS_HEADERS, stubActor } from './support/api-stubs'

test('the account menu names the signed-in user and their organization', async ({ page }) => {
  await stubActor(page)
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
  await page.getByTestId('account-button').click()

  await expect(page.getByText(ACTOR.email)).toBeVisible()
  await expect(page.getByText(ACTOR.organization_name)).toBeVisible()
  await expect(page.getByText('ADMIN')).toBeVisible()
})

test('signing out returns to the sign-in screen', async ({ page }) => {
  let authenticated = true

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
  await page.route('**/api/v1/auth/logout', (route) => {
    authenticated = false
    return route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ status: 'signed out' }),
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
  await page.getByTestId('account-button').click()
  await page.getByTestId('sign-out').click()

  await expect(page.getByTestId('sign-in-form')).toBeVisible()
})

test('the workspace no longer claims the API has no authentication', async ({ page }) => {
  await stubActor(page)
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
  await expect(page.getByText('no authentication')).toHaveCount(0)
})
