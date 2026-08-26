/**
 * Shared network stubs for the browser specs.
 *
 * `CORS_HEADERS` used to be `const CORS = { 'Access-Control-Allow-Origin': '*' }`
 * copied into five spec files. A wildcard origin is rejected by the browser in
 * a credentialed request, so all five had to change at once when the client
 * started sending the session cookie - which is exactly why it is one module
 * now rather than five constants that happen to agree.
 */
import type { Page } from '@playwright/test'

export const APP_ORIGIN = 'http://localhost:3000'

export const CORS_HEADERS = {
  'Access-Control-Allow-Origin': APP_ORIGIN,
  'Access-Control-Allow-Credentials': 'true',
}

/** The signed-in actor the stubbed specs act as. Matches the backend's
 * `default_org` fixture (`backend/tests/conftest.py:83`) so a spec that is
 * ported between the two suites keeps meaning the same thing. */
export const ACTOR = {
  user_id: 'user-e2e-0001',
  email: 'member@tenggara.example',
  organization_id: 'org-e2e-0001',
  organization_name: 'Tenggara Precision Sdn. Bhd.',
  role: 'ADMIN',
}

/** Stub `GET /api/v1/auth/me` as a live session, so a spec about cases can be
 * about cases. Every workspace spec needs this and none of them are testing
 * it — `auth-gate.spec.ts` is where the gate itself is tested. */
export async function stubActor(page: Page, overrides: Partial<typeof ACTOR> = {}) {
  await page.route('**/api/v1/auth/me', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      headers: CORS_HEADERS,
      body: JSON.stringify({ ...ACTOR, ...overrides }),
    }),
  )
}
