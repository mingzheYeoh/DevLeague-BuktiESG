<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

---

## This is not the project rulebook

The block above is generated and re-added by `next dev` (Next.js 16). It is
framework guidance only.

The binding rules for this repository are in **`../AGENTS.md`** at the repo
root — synthetic data only, the AI never owns a verdict, the AI never supplies a
source location, protected values, and the stop conditions. Read that file
before changing anything here.

Frontend-specific notes:

- The API client lives in `lib/api/`. Its types mirror what `backend/` actually
  returns, not the unfrozen `docs/spec/Shared-Integration-Contract.md`. If the
  server changes, `lib/api/types.ts` changes to match it — never the reverse.
- No screen may invent an `evidence_status`, a `review_status`, a priority score
  or a source location. Where the server sends null, render nothing.
- There is no seeded sample data in this app. A screen that cannot reach the API
  says so.
