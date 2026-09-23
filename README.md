# BuktiESG

BuktiESG helps teams answer customer ESG questionnaires with traceable documents, human review, and follow-up actions. This repository is a **team demo**.

## Try the hosted demo

Open <https://buktiesg.vercel.app/> and sign in with a Vercel account that has access to this project. Then register inside BuktiESG; each new account gets its own organization. Use the synthetic files in [`sample/`](sample/). The hosted demo uses Neon PostgreSQL and private Vercel Blob storage, accepts files up to **4 MiB**, and does not have a DeepSeek extraction key configured.

## Run locally

Install Docker Desktop (or Docker Engine with Compose), [uv](https://docs.astral.sh/uv/), and Node.js **22** with npm. uv installs the required Python 3.12. Start the following commands from the repository root.

1. Copy the environment template and set a local database password in `.env`:

   ```powershell
   # Windows PowerShell
   Copy-Item .env.example .env
   ```

   On macOS/Linux, use `cp .env.example .env`. Edit `.env` so `POSTGRES_PASSWORD=` has a value, then start PostgreSQL:

   ```bash
   docker compose up -d --wait
   ```

2. In the first terminal, start the API:

   ```bash
   cd backend
   uv sync
   uv run alembic upgrade head
   uv run uvicorn app.main:app --reload
   ```

   Health check: <http://localhost:8000/health>.

3. Open a second terminal at the repository root and start the web app:

   ```bash
   cd frontend
   npm ci
   npm run dev
   ```

   Open <http://localhost:3000>, register an account, create a case, and upload `sample/questionnaire/customer-esg-questionnaire-2026.xlsx`. If PowerShell blocks `npm.ps1`, use `npm.cmd` in place of `npm`.

4. Optionally, run the extraction worker in a third terminal:

   ```bash
   cd backend
   uv run python worker.py
   ```

   Without `DEEPSEEK_API_KEY`, no document text is sent to a model provider and no values are extracted. If you add that key to the root `.env`, **upload synthetic documents only**: text is sent to `api.deepseek.com`. Remove and rotate the key before uploading any real customer document.

Stop the API, web app, and worker with `Ctrl+C`, then run `docker compose stop` from the repository root. This retains the local database.

## Check the project

```bash
cd backend
uv run pytest -q --basetemp .venv/pytest-tmp

cd ../packages/ai-pipeline
uv sync
uv run pytest -q --basetemp .venv/pytest-tmp

cd ../../frontend
npm run typecheck
npm run build
```

For browser tests, run `npx playwright install chromium` once, then `npm run test:e2e` from `frontend/`. These tests start the web app and stub the API.

`backend/` contains the FastAPI service and migrations; `frontend/` is the Next.js app; `packages/ai-pipeline/` parses and analyzes documents; `sample/` contains synthetic demo data. All API endpoints require sign-in, and case data is isolated by organization. AI output cannot set review or evidence verdicts or invent citation locations: the rule engine computes statuses, and the server resolves citations from stored document chunks.

The historical technical specification is available with `git show bfd45ad:docs/spec/BuktiESG-Technical-Spec-EN.md`. Historical agent rules referenced in source comments are available with `git show 06d2c84:AGENTS.md`; protected formulas, security boundaries, and critical tests still apply.
