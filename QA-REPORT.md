# Verification — 2026-09-23

The ten focused cases below were run against the existing backend tests with
`uv run --frozen pytest -q --basetemp .venv/pytest-tmp-ten-cases` followed by
the ten test IDs. **10 passed.**

| # | Test node (`backend/tests/`) | Expected result | Result |
|---|---|---|---|
| 1 | `test_auth_endpoints.py::test_registration_creates_user_org_and_admin_membership` | User, organization, and admin membership are created | Pass |
| 2 | `test_auth_endpoints.py::test_login_sets_a_session_cookie` | A session cookie is issued | Pass |
| 3 | `test_tenant_isolation.py::test_another_organizations_case_is_not_found` | Return 404 | Pass |
| 4 | `test_tenant_isolation.py::test_a_signed_out_caller_gets_401` | Return 401 | Pass |
| 5 | `test_extraction_job.py::test_running_the_job_writes_the_measurement_onto_the_chunk` | Measurement is persisted on the chunk | Pass |
| 6 | `test_extraction_job.py::test_two_documents_reporting_different_values_make_the_question_conflicting` | Question becomes conflicting | Pass |
| 7 | `test_evidence_accept.py::test_accepting_the_evidence_makes_the_question_verified` | Question becomes verified | Pass |
| 8 | `test_case_delete.py::test_a_draft_case_can_be_deleted` | Case is removed | Pass |
| 9 | `test_document_delete.py::test_an_unreadable_document_can_be_deleted` | Deletion succeeds | Pass |
| 10 | `test_document_delete.py::test_a_document_that_parsed_cannot_be_deleted` | Deletion is refused | Pass |

Other checks: backend **222 passed**, AI
pipeline **58 passed**, frontend browser suite **47 passed / 1 skipped**, and
the opt-in real API browser test **1 passed**. Frontend typecheck and production
build passed. `npm audit` found **0 vulnerabilities** after upgrading Next.js.

Cloud status: the original 2026-08-28 production deployment (commit `fb66668`)
was frontend-only: `/health` and `/api/v1/auth/me` returned 404 and the browser
bundle pointed at `localhost:8000`. The project now builds `frontend/` and
`backend/` together through Vercel Services, with same-origin API routing.
The dedicated Neon PostgreSQL database is migrated to `0010` (head), a private
Vercel Blob store is connected, and Vercel Authentication protects **all**
deployments, including the production domain. The preview and production
deployments are Ready. `/health` returned 200 and signed-out
`/api/v1/auth/me` returned 401. Synthetic smoke tests on **both** deployments
passed registration, login, Case creation, document upload, private Blob
persistence, and authenticated document download. The private Blob store also
passed a direct save/load/delete check. An unsigned request to the production
domain redirected to Vercel login; temporary automation bypass keys used for
verification were revoked afterwards.
An isolated PostgreSQL 16 container migrated from base to `0010` (head), and
the real API browser test passed again against that database. The temporary
container was stopped and removed afterwards.

The project is still incomplete against the historical Main Spec: the protected
priority formula has no server implementation, export is a browser-generated
TXT/CSV draft without the specified PDF or export snapshot/version, and the eight critical E2E IDs
(`TEST-E2E-001`–`008`) have not been implemented as acceptance tests. Existing
browser tests mostly stub the API; the opt-in test checks one live workflow.

This is a controlled **team demo**, not a public release. The historical Main
Spec §13.4 requires managed authentication for public deployment; the backend
still stores passwords itself. Vercel Authentication is the outer team gate.
The hosted build has no extraction worker or DeepSeek key, so `CONFLICTING`
is unreachable there. Upload/download is limited to 4 MiB by the Vercel
Function payload cap. The backend README also documents no login rate limiting
and a registration timing leak; public access must remain disabled.
The repository owner resolved the layout conflict on 2026-09-23 in favor of
retaining `backend/` + `frontend/`; `AGENTS.md` §1a records the ruling.
