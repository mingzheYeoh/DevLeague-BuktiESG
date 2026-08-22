import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: true,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.WEB_BASE_URL ?? "http://localhost:3000",
    trace: "on-first-retry",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  // No webServer entry: this suite is meant to run against a dev server
  // (`pnpm dev`) started separately, since a real backend at
  // NEXT_PUBLIC_API_BASE_URL is not guaranteed to be running in this repo
  // yet. Start `pnpm dev` in apps/web, then `pnpm test:e2e`.
});
