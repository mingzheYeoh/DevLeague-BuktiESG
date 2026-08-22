# buktiesg-ai-pipeline

COO-owned AI pipeline core for BuktiESG — **First Vertical Slice (Phase 1)** scope only.

## Structural boundary (non-negotiable)

Per `AGENTS.md` §3.2/3.3 and `docs/decisions/CTO-RULINGS.md` `BLOCKER-04`, this package's core
functions (`parse_document`, `analyze_question`) are **pure**:

- No database session, no ORM import, no HTTP/persistence client, no credentials.
- No other Case's data — inputs are passed in explicitly by the caller.
- No human-confirmation permission and no verdict fields (`evidence_status`,
  `review_status=HUMAN_CONFIRMED`, `final_compliance_status`, etc.) — those are computed
  server-side by the CTO's deterministic rule engine, never here.
- No source location is ever returned — only a `chunk_id`. The server resolves the location
  from `document_chunks`.

The CTO's backend orchestration layer (`apps/api`) is responsible for loading files/jobs,
calling into this package, validating the result against the shared schema, and persisting it.

## Scope of this slice

1. `parse_document()` — parses a single `.xlsx` questionnaire into question rows.
2. `analyze_question()` — keyword-first matching (no embeddings, no LLM call — `BLOCKER-06`,
   `BLOCKER-08`) of one question against a provided list of document chunks, returning an
   `AnalysisResult` shaped per `docs/spec/Shared-Integration-Contract.md` §8.
3. `FixtureProvider` — a deterministic stand-in for a future LLM-backed step, so nothing in
   this package depends on a live model call. Not exercised by the current matching logic
   (which is pure keyword logic), but present so a future LLM step can plug in behind the
   same `LLMProvider` interface without moving the purity boundary.

Not in scope for this slice: SEDG taxonomy mapping (`packages/taxonomy` does not exist yet),
priority-factor scoring, embeddings/fuzzy retrieval, `fixtures/ground_truth/**` content.
