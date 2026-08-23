# Sample data

Test data for the BuktiESG workspace: one customer questionnaire, thirteen supporting documents, and two files that fail on purpose.

Every result described here was **observed by uploading these files to a running backend**, not predicted. Where the application behaves poorly, that is written down rather than tuned away.

---

## Data provenance — read this first

This repository is **synthetic data only** (`AGENTS.md` §3.1). The sample set has two kinds of file and they are not mixed:

| Prefix | Content | Provenance |
|---|---|---|
| `reference-*` | Published Malaysian energy and ESG-framework figures | **Real.** Sources named inside each file. |
| everything else | A fictional company, `BuktiPack Manufacturing Sdn. Bhd.` | **Invented by me.** No real company, person, incident or payroll figure. |

`BuktiPack Manufacturing Sdn. Bhd.` does not exist. Its headcount, injury rate, waste tonnage, water volumes and policies are all fabricated. Every synthetic file carries a `SYNTHETIC FIXTURE` marker on its first or second line.

### Real sources used

- **Grid Emission Factor (GEF) in Malaysia** — Energy Commission of Malaysia (Suruhanjaya Tenaga), provisional 2022–2024 series and the earlier 2017–2022 series. Used in `evidence/reference-malaysia-grid-emission-factor.txt`.
- **Regulatory Period 4 electricity tariff** — Tenaga Nasional Berhad / Energy Commission announcements, as reported in Malaysian press. Used in `evidence/reference-tnb-tariff-rp4.txt`. See [TNB news clippings](https://www.tnb.com.my/).
- **Simplified ESG Disclosure Guide (SEDG)** — [Capital Markets Malaysia](https://www.capitalmarketsmalaysia.com/), launched October 2023, 35 priority disclosures.
- **ASEAN Simplified ESG Disclosure Guide (ASEDG) Version 1** — [ASEAN Capital Markets Forum](https://www.theacmf.org/), launched April 2025, 38 priority disclosures. [Media release (PDF)](https://www.theacmf.org/images/downloads/pdf/2025_04_10%20ASEDG%20ACMF%20PR_v110425%20(FINAL).pdf).

Content from these sources was rephrased for compliance with licensing restrictions; figures are reproduced as published.

> **A genuinely useful accident.** The Energy Commission publishes **two different Peninsular values for 2022** — `0.769` in the provisional 2022–2024 series and `0.774` in the earlier 2017–2022 series. Same publisher, same metric, same year, two numbers. That is exactly the problem this product exists to surface, and it is real rather than staged. It is called out inside the file.

---

## Files

### `questionnaire/`

| File | Purpose |
|---|---|
| `customer-esg-questionnaire-2026.xlsx` | 15 questions, 11 required. The one to upload. |
| `broken-questionnaire-wrong-headers.xlsx` | Wrong header row. Must fail cleanly and create **zero** questions. |

The parser requires row 1 to be exactly `external_question_id | question_text | section | is_required`. Anything else is rejected.

### `evidence/`

Formats are deliberately mixed, because the backend has one parser per format and each chunks differently — which changes what a citation looks like:

| Format | Chunk unit | Citation you get |
|---|---|---|
| `.pdf` | one per page | `Page 1` |
| `.docx` | one per heading section | `Policy › Commitments` |
| `.xlsx` | one per row | `Sheet 'FY2025' · A4:B4` |
| `.txt` | one per non-blank line | the line |

| File | Type to upload as | What it holds |
|---|---|---|
| `reference-esg-disclosure-frameworks.txt` | Other | SEDG / ASEDG facts (**real**) |
| `reference-tnb-tariff-rp4.txt` | Other | RP4 tariff 45.40 sen/kWh (**real**) |
| `reference-malaysia-grid-emission-factor.txt` | Other | GEF series + the 2022 discrepancy (**real**) |
| `electricity-bills-jan-mar-2025.pdf` | Utility bill | 3 monthly statements, one per page — Jan–Mar only |
| `water-utility-statement-fy2025.txt` | Utility bill | Quarterly water withdrawal, FY2025 total 4,995 m³ |
| `waste-tracker-fy2025.xlsx` | Waste record | Monthly waste log, FY2025 recycling rate **41%** |
| `weighbridge-summary-q4-fy2025.txt` | Waste record | Contractor weighbridge totals, recycling rate **53%** |
| `environmental-policy-v3-2025.docx` | Policy | v3, approved Dec 2024, effective Jan 2025 |
| `employee-handbook-2022.docx` | Policy | Grievance procedure — **issued 2022, never revised** |
| `anti-bribery-policy-2025.docx` | Policy | Anti-bribery controls + whistleblowing, 2 reports in FY2025 |
| `supplier-code-of-conduct-2025.txt` | Policy | Child/forced labour prohibition; only 12 of 34 suppliers signed |
| `safety-incident-register-fy2025.txt` | Safety record | LTIFR 21.4, 2 injuries, 0 fatalities |
| `hr-workforce-summary-fy2025.txt` | HR data | 45 headcount, 3 of 8 managers women, 14.2 training hours |
| `unreadable-scan.pdf` | Safety record | A corrupt PDF. Must fail and become retryable. |

Three deliberate traps for a reviewer to catch:

1. **Partial coverage.** The electricity bills cover January to March only. The question asks for the annual figure. Nine months are missing.
2. **A contradiction.** The waste tracker says 41% recycled for FY2025; the weighbridge summary says 53% for the same year. Neither is marked correct.
3. **A stale policy.** The employee handbook is from 2022 and has never been revised, so it may no longer describe current practice.

### `build_samples.py`

Regenerates the binary files (`.xlsx`, `.docx`, `.pdf`). The `.txt` files are committed as-is. Edit the script rather than a binary:

```powershell
cd backend
uv run python ../sample/build_samples.py
```

---

## Observed results

Uploaded to a clean database in the order listed above — **reference files first, company records after**.

### Documents

| File | Result |
|---|---|
| `customer-esg-questionnaire-2026.xlsx` | `INDEXED` · 15 questions · columns detected `A/B/C/D` |
| `broken-questionnaire-wrong-headers.xlsx` | `NEEDS_MANUAL_REVIEW` · *"sheet 'Sheet1' is missing required header(s): ['external_question_id', 'question_text']"* · 0 questions created |
| `unreadable-scan.pdf` | `NEEDS_MANUAL_REVIEW` · *"no extractable text found in any PDF page"* |
| all 12 other evidence files | `INDEXED` |

Both failures are **retryable** — those are the only two files in the set that can demonstrate the Retry button, since only `FAILED` and `NEEDS_MANUAL_REVIEW` are retryable.

### Questions

15 questions, 11 required. Readiness starts at **0% (0 of 11 confirmed)**.

Pillar mapping: 5 Environmental, 6 Social, 3 Governance, 1 Uncategorised. **14 of 15** reached a SEDG disclosure code.

Every question comes out **`PARTIAL` / `UNREVIEWED`**. That is not a bug and it is worth understanding:

- `PARTIAL` because a keyword match produced a candidate that no human has accepted. The rule engine's `VERIFIED` requires an accepted evidence link, and **there is no API endpoint that accepts one** — so `VERIFIED` is currently unreachable through the UI.
- `MISSING` only appears when *nothing* matched. In this set everything matched something, so nothing is `MISSING`.
- `CONFLICTING` needs two evidence links for the same question with the same scope and period but different values. The matcher never populates a value, so despite the 41%/53% contradiction being present in the data, **the engine cannot detect it**. A human reading both documents can.

So the demo shows one status. The interesting work is in the Question detail: the excerpt, the location, and the review decision.

One knock-on effect, verified against the running API: because nothing ever reaches `MISSING` or `CONFLICTING`, the server never auto-sets `requires_closure_evidence` on an action, so the closure-evidence gate never fires by itself in this sample set. The create-action form has a **Require closure evidence** tickbox to make that rule reachable.

### Citation accuracy — a real weakness

**8 of 15 questions cite the document they should. 7 do not.**

| Question | Cites | Should cite |
|---|---|---|
| `Q-E-02` GHG / grid factor | Electricity statement, page 1 | ✅ |
| `Q-S-01` LTIFR | LTIFR line of the safety register | ✅ |
| `Q-S-02` headcount | Employment type breakdown | ✅ |
| `Q-S-03` gender diversity | Gender diversity line | ✅ |
| `Q-S-04` training hours | Average training hours line | ✅ |
| `Q-G-01` anti-bribery | Anti-bribery controls section | ✅ |
| `Q-G-02` whistleblowing | Whistleblowing section | ✅ |
| `Q-G-04` child labour | Child labour prohibition line | ✅ |
| `Q-E-01` electricity kWh | *"Total days lost to work-related injury: 11."* | the electricity bills |
| `Q-E-03` water withdrawal | *"Total days lost to work-related injury: 11."* | the water statement |
| `Q-E-04` recycling rate | Environmental policy, Commitments | the waste tracker |
| `Q-E-05` environmental policy | Anti-bribery policy, Whistleblowing | the environmental policy |
| `Q-E-06` renewable energy | Environmental policy, Commitments | nothing — no evidence exists |
| `Q-S-05` grievance mechanism | Supplier code, recruitment fees | the 2022 handbook |
| `Q-G-03` cybersecurity | Supplier code, recruitment fees | nothing — no evidence exists |

**Cause.** `backend/app/schemas.py`, in `QuestionListItem.from_model`:

```python
latest_link = max(links, key=lambda link: link.created_at)
```

The panel shows the **most recently created** candidate link, not the best-scoring one. Every upload re-runs matching, and a document sharing even one common word (`total`, `policy`, `any`) creates a fresh link that displaces a far better earlier match. Upload order therefore decides the citation.

I found this by tuning the sample text three times — removing `Reporting period:`, then a leading `Total`, then another `Total` — and each time a different generic word in a later-uploaded file took over. The data cannot fix it.

**Two things would fix it properly**, both outside the scope of preparing test data:

1. Choose the displayed link by match strength rather than timestamp, or
2. Stop re-analysis from creating a weaker duplicate candidate for a question that already has a stronger one.

Until then: when a citation looks wrong, open the Evidence screen and read the document itself. The excerpt is genuinely from the stored document — it is never fabricated — it is just often the wrong document.

---

## Two limits inherited from the matcher

**A glossary poisons retrieval.** An earlier draft of `reference-esg-disclosure-frameworks.txt` listed all fifteen ASEDG pillar and topic names. Because retrieval is plain keyword overlap, those lines then out-matched real company records for almost every question — a glossary looks relevant to everything and proves nothing. The lines were removed. Worth remembering before adding a framework cheat-sheet to a real evidence library.

**Fact-per-line beats prose.** A `.txt` file with one fact per line produces a precise citation, because each line is its own chunk. A `.docx` produces one chunk per heading section, so `Q-E-04` cites the whole *Commitments* section and the excerpt opens on an unrelated sentence. If you want tight citations, structure the document.

---

## Reset between runs

```powershell
cd backend
uv run python scripts/init_dev_db.py --recreate   # drops all local cases
Remove-Item -Recurse -Force var\storage            # drops stored uploads
New-Item -ItemType Directory -Path var\storage
```
