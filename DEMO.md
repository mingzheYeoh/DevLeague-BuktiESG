# Demo runbook

A local walkthrough of BuktiESG on a developer machine. Roughly twelve minutes.

Everything claimed here was measured against this build and is sourced from
[`sample/README.md`](sample/README.md), which records what the product actually
does with this dataset — including what it does not do. **Read "What not to
promise" before demonstrating to anyone.**

---

## Before you start

**Windows**

```powershell
.\demo.ps1 up
```

**macOS / Linux**

```bash
./demo.sh up
```

Postgres, then migrations, then API / worker / web — three panes in Windows
Terminal, or in `tmux` where it is installed, or backgrounded with logs under
`backend/var/log` where it is not. Either way it waits for the healthcheck and
for both ports to answer before saying it is ready, so when it says ready the
links work.

Sign in at <http://localhost:3000>.

> **`localhost`, not `127.0.0.1`.** They are different origins, and the frontend
> calls `http://localhost:8000` by default — so the `127.0.0.1` form makes every
> API call cross-origin. Not a pedantic distinction: it is how the hanging
> session gate was found, and this line used to name the wrong one.

> **One rule: upload only from `sample/`.**
>
> With `DEEPSEEK_API_KEY` set, chunk text leaves the machine for
> `api.deepseek.com`. The owner's 2026-08-27 ruling permits that for the demo
> **on the condition that no real customer document is uploaded while the key is
> set** (`AGENTS.md` §3.1). Nothing in the code can check the condition. The
> `sample/` evidence is entirely synthetic — *Tenggara Precision Sdn. Bhd.* does
> not exist — which is why it is safe and why nothing else is.

**Pacing.** Extraction runs 12–22 seconds per two or three chunks. The full
21-document case is about 175 chunks, near three minutes of waiting. Upload four
or five documents, not the whole folder.

---

## The case

| | |
|---|---|
| Company answering | Tenggara Precision Sdn. Bhd. — electronics components, Klang |
| Customer asking | Sinar Retail Group Berhad, a listed Main Market issuer |
| Period | FY2025 |
| Scope | **The Klang plant only, not the group** |

That last row is what several documents get wrong on purpose. A listed customer
must report on supply chain management — which is why an SME supplier receives a
questionnaire like this at all.

---

## Act 1 — the questionnaire is real (2 min)

Create the case, then upload `sample/questionnaire/customer-esg-questionnaire-2026.xlsx`.

Twenty questions appear, each carrying its disclosure code. **The codes are
real**: Capital Markets Malaysia's Simplified ESG Disclosure Guide v2 (July
2025), cross-checked against the nine sustainability matters Bursa requires of
Main Market issuers. `SEDG-E1.1` traces back to a published document.

*Optional, and a good one:* upload
`sample/questionnaire/broken-questionnaire-wrong-headers.xlsx`. It is refused,
the missing headers are named, and **zero** questions are created. A partial
import would be worse than a refusal.

---

## Act 2 — the matcher points at a document (3 min)

Upload four: `A-01` (TNB bills), `A-02` (GHG inventory), `A-04` (training
register), `A-05` (anti-bribery policy).

Sixteen of the twenty questions cite a genuinely relevant document, and the
citation shown is chosen by match quality, not upload order.

The part worth saying out loud: **the model never supplies the location.** It
returns a `chunk_id`; the server resolves the citation from `document_chunks`
(§3.3). You are never looking at a page number the AI claimed.

**Be honest about the two that are wrong** — it lands better than hiding them,
and someone will find them:

| Question | Cites | Should cite | Why |
|---|---|---|---|
| `Q-S-02` training hours | `C-02` (FY2022) | `A-04` | An exact tie at 4.55. Both say "average training hours per employee"; only the *year* separates them, and the matcher never extracts a value to compare. Ties break on upload order |
| `Q-E-01` Scope 1 | `A-03` (waste) | `A-02` | `A-02` is chunked one row per line, and no single row contains both "Scope 1" and the units phrase. Matching is per chunk |

Both need value extraction and multi-row aggregation, not a better keyword
score. Tuning the weights until this particular folder looks perfect would be
overfitting to it.

---

## Act 3 — who owns the verdict (2 min) — **the strongest moment**

Stay on `Q-E-01`. It asks for Scope 1 emissions and cites `A-03`, the *waste*
register. That citation is wrong, and you just said so.

Click **Accept this evidence**. The question reads `VERIFIED`.

> The engine checks that a human vouched. It never checks that the human was
> right.

That is the division of authority working as designed — `AGENTS.md` §3.2, *the
AI never owns a verdict*. Acceptance is also refused without a reviewer label:
an acceptance nobody signed is indistinguishable from one the AI issued.

Then show what it did **not** do: readiness has not moved. Readiness counts
`review_status == HUMAN_CONFIRMED` and ignores evidence status entirely.
Vouching for a citation and confirming an answer are separate judgements, and
the second is not implied by the first.

---

## Act 4 — unreadable is not the same as absent (2 min)

Needs a **fresh case**. Create one, upload the questionnaire, then upload
**only** `sample/evidence/C-06-unreadable-scan-safety-records.pdf`.

Nineteen questions report `MISSING`. `Q-S-06` alone reports
`NEEDS_MANUAL_REVIEW`, naming the file.

Why only that one: the rule matches by exact token equality against the filename
and extracted metadata — no fuzzy matching, no embeddings — and `safety` is the
only word `Q-S-06` and that filename share. Deliberately narrow. A rule that
guessed which unreadable file mattered would be asserting something it cannot
know.

That state has an exit. Retrying re-runs the same parser over the same bytes, so
a scan with no extractable text never recovers. The document drawer offers
**Delete document**, which removes the file, its bytes, and the hold it had on
`Q-S-06` — offered only for a document that failed to parse. One that parsed is
refused with 409: it has chunks, something cites them, and destroying it would
destroy a review decision.

---

## Act 5 — staleness is measured, not guessed (1 min)

On the Evidence screen set **Evidence dated** to `2022-12-31`, *then* upload
`sample/evidence/C-02-energy-and-emissions-fy2022.txt`. Its question moves to
`OUTDATED` — the question states no required period, and the file is past the
24-month threshold (DEC-007).

Upload the same file with no date and it stays `PARTIAL`. The engine has nothing
to measure and says so rather than guessing.

The date field is optional on purpose: a reviewer working a batch will not always
know it, a required field gets answered with a guess, and an absent date and a
wrong one are not equally recoverable.

---

## What not to promise

Read this before you pitch.

- **`CONFLICTING` will not fire.** `A-03` reports 12.6 tonnes of scheduled waste
  and `C-01` reports 18.4 for the same site and year. It is the most useful
  contradiction in the dataset and **the engine does not report it.** Values are
  read correctly; grouping them across links is the open problem. Do not upload
  `C-01` expecting fireworks.
- **`MISSING` does not appear once the full set is uploaded.** Almost everything
  reads `PARTIAL`, because a question can usually find *some* chunk sharing a
  distinctive word — even the two questions written to be unanswerable.
- **Period-coverage and scope-match checks are skipped, not met.** This build
  populates neither `required_period` nor `required_scope`, so two of the six
  `VERIFIED` conditions never apply. `backend/tests/test_evidence_requirement.py`
  pins why: inheriting the case period reads like the obvious next step and is a
  regression — no link carries a period, so every `VERIFIED` would fall back to
  `PARTIAL`.

So the honest pitch is not *watch the engine sort good evidence from bad*. It is:

> **The matcher points you at the right document. Everything after that is still
> yours to judge.**

Provenance over prose — stated as a limitation rather than a claim. For an
auditable ESG workflow that is the stronger story anyway, and it is the one this
build can actually stand behind.

---

## When something is wrong

| Symptom | Look at |
|---|---|
| Upload succeeds, values never appear | The **worker** pane. Without it running, evidence still links; only values stay null |
| Worker logs "outside Malaysia" once at startup | Expected. `DeepSeekExtractor` is selected and says so |
| Every value is null and no warning appeared | `DEEPSEEK_API_KEY` unset — the worker is on `NullExtractor`. both `up` commands warn about this |
| UI says it cannot reach the backend | The **API** pane, then <http://localhost:8000/health> |
| Port still held after closing a pane | `down` kills the whole process group; `npm run dev` and `uvicorn --reload` both leave children behind |

---

## After the demo

```powershell
.\demo.ps1 reset   # deletes every case, keeps the account and organization
.\demo.ps1 down    # stops Postgres, frees 8000 and 3000
```

```bash
./demo.sh reset
./demo.sh down
```

Both read `DEMO_EMAIL` / `DEMO_PASSWORD` from the environment or the root `.env`,
and prompt if neither is set. Neither script generates or stores a password.

`reset` goes through the API rather than truncating tables, because nothing in
the database owns the uploaded bytes — the row cascade alone would leave them on
disk. It re-reads the case list afterwards and checks `backend/var/storage` is
empty rather than trusting the endpoint that did the deleting.
