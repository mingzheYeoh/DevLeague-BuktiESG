import { defineConfig, devices } from '@playwright/test'

/**
 * Browser tests for the workspace UI.
 *
 * The specs stub the BuktiESG API at the network layer using the shapes the
 * real server returns (`backend/app/schemas.py`), so they run without a live
 * backend and still fail if the client stops matching the server's contract.
 * `webServer` starts the Next dev server, so `npm run test:e2e` is
 * self-contained apart from the browser binary (`npx playwright install
 * chromium`).
 */
export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  fullyParallel: true,
  retries: 0,
  reporter: [['list']],
  use: {
    baseURL: process.env.WEB_BASE_URL ?? 'http://localhost:3000',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run dev',
    url: process.env.WEB_BASE_URL ?? 'http://localhost:3000',
    reuseExistingServer: true,
    timeout: 120_000,
  },
})
