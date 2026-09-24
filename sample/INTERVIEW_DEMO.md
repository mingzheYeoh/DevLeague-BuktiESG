# BuktiESG Interview Demo

Use this guide to walk an interviewer through one complete, **synthetic** FY2025 ESG questionnaire. Open the [hosted demo](https://buktiesg.vercel.app/) and keep this guide beside it. The goal is a traceable, human-reviewed draft response, not an audit or automatic compliance decision.

| Prepare | Use |
| --- | --- |
| Questionnaire | [customer-esg-questionnaire-2026.xlsx](questionnaire/customer-esg-questionnaire-2026.xlsx) |
| Supporting documents | The **16 files beginning A-** in [sample/evidence](evidence/) |
| Keep out of the first run | Files beginning B-, C-, or reference-; use those later to demonstrate gaps and conflicts |
| Expected result | 20 imported questions, 14 required; 16 indexed evidence files; 14/14 required answers confirmed after you write and record them |

**What is actually AI?** OpenRouter's Luna model reads evidence text to extract measurements (value, unit, scope, period) and to judge whether a keyword-matched passage appears to answer a question. Its relevance labels are suggestions backed by verbatim source quotes. Questionnaire import, E/S/G category suggestions, initial candidate retrieval, status rules, and answer confirmation use ordinary code and human review. The model does not write final answers or approve evidence.

## Follow the demo

### Step 1 — Create a case

Open [BuktiESG](https://buktiesg.vercel.app/). Sign in with an account that belongs to the project's Vercel team, then register or sign in inside BuktiESG. Choose **Cases → New case** and complete the four screens:

| Screen | Enter or select |
| --- | --- |
| **1. Case details** | **Case title:** Tenggara Precision FY2025 ESG trial · **Customer:** Demo customer · **Deadline:** leave blank for this trial |
| **2. Reporting scope** | **Period start:** 2025-01-01 · **Period end:** 2025-12-31 |
| **3. Questionnaire** | Select [customer-esg-questionnaire-2026.xlsx](questionnaire/customer-esg-questionnaire-2026.xlsx) |
| **4. Review** | Check the entries, then choose **Create case** |

**Check:** The case opens with its questionnaire. Upload the questionnaire now, before evidence: matching uses the questions that exist when each evidence file is uploaded.

### Step 2 — Check the imported questions

Open **Questionnaire**. You should see **20 questions, 14 required**, in the spreadsheet's row order. Q-E-10 and Q-S-07 appear near the end. Open Q-E-02 to show the customer’s original Scope 2 question.

The application reads these questions from spreadsheet rows; it does not invent them. Each sample question starts with a SEDG code, which the app reads directly. For questions without a code, it falls back to keywords. **Uncategorized** means neither method found a category, not that Luna failed.

### Step 3 — Upload the 16 supporting files

Open **Evidence** and leave **Upload as: Other**. Set **Evidence dated** *before* selecting each file or group. This date is when the source was prepared or approved; it can be in 2026 even though the figures describe FY2025.

| Files to select from [sample/evidence](evidence/) | Evidence dated |
| --- | --- |
| A-01, A-02, A-03, A-04, A-07 | 2025-12-31 |
| A-05, A-16 | 2025-02-14 |
| A-06 | 2026-01-12 |
| A-08 | 2026-01-16 |
| A-09 | 2026-01-18 |
| A-10 | 2026-01-20 |
| A-11 | 2026-01-19 |
| A-12 | 2026-01-22 |
| A-13 | 2026-01-21 |
| A-14 | 2026-01-17 |
| A-15 | 2026-01-23 |

Use **Upload evidence** for each group. Files sharing a date can be selected together; the app processes them one at a time. A-01 through A-04 and A-07 have no later approval date, so this trial uses the reporting-period end for them. Do not upload the B-, C-, or reference- files in this first case.

**Check:** All **16 uploaded A- files** are marked **Indexed**. The Evidence library also lists the questionnaire, so its total file count may be 17. Indexed means readable text was saved and can be searched. Luna's measurement and relevance checks run separately in the background and may finish a little later. Use **Refresh** on Questionnaire to see updated suggestions.

### Step 4 — Show the original and the extracted text

In **Evidence**, open A-01 (PDF), A-02 (spreadsheet), A-05 (Word), and A-10 (text). For each file, choose **Open preview** and switch between **Extracted text** and **Original file**.

**Extracted text** is the set of passages the matcher searched, with page, sheet/cell, or paragraph locations. It is a view of stored text, not a second generated file. PDFs can open inline as originals; Word and Excel originals are offered as downloads. A questionnaire can be marked Indexed while its evidence-text preview is empty because its output is the question list.

### Step 5 — Review and answer the questions

Return to **Questionnaire** and open Q-E-02. The **Evidence** panel shows the top candidate passage, its filename, location, and excerpt. Choose **Open document** and check the original against the [answer and evidence sheet](#answer-and-evidence-sheet) below. For Q-E-02, compare A-08 and A-02, and use A-01 to cross-check electricity use.

If the shown passage really supports the claim, choose **Accept this evidence**. Then choose **Write the answer**, enter the reviewed response, and select **Record decision**. Repeat for the other questions using the sheet below. **Confirm draft** is not useful for this trial: this build has no prewritten draft text, so that button can confirm an empty answer.

These are two separate decisions. Accepting a source records who vouched for it; writing an answer records what you are willing to submit. Do not accept a weak match merely to make a status turn green. If the top candidate covers only part of a multi-part question, inspect the other listed source files yourself and state the limits in your written answer.

### Step 6 — Check progress and export

After writing and recording all **14 required** answers, open **Overview**. It should show **14 of 14 required answers confirmed**. The questionnaire has 20 questions in total; the other six are optional. Evidence may still show Partial or another gap because answer confirmation and evidence quality are separate.

Open **Export → Generate marked-up draft → Download package**. The package contains one text response summary and three CSV registers. It is labelled as a draft and is **not** sent to the customer.

If an important source is missing or contradictory, show **Create submission action** on the question: assign an owner, next step, and deadline instead of pretending the gap is solved. For a second case, the B- and C- files deliberately demonstrate incomplete, old, wrong-entity, contradictory, or unreadable material.

## What happens behind each click

1. **Case separation.** Sign-in identifies your organization. Each case keeps its own questionnaire, evidence, answers, and review decisions. A match cannot silently use another organization's files.

2. **Original storage and duplicates.** The system keeps the uploaded file privately. It calculates a SHA-256 fingerprint, like a digital file ID; uploading identical bytes again to the same case reuses the document. The hosted demo accepts files up to **4 MiB each**.

3. **Question extraction.** The spreadsheet reader finds the external question ID and question-text columns, then turns each nonblank row into a question. It keeps the row order, required flag, section, and source cell so you can trace the result back to the original. This sample has **20 questions, 14 required**. If required columns are missing, the file needs manual review rather than producing invented questions.

4. **Category suggestions.** If the question starts with a SEDG code, the app copies its pillar, topic, and disclosure code. Otherwise, a small keyword list suggests them from the wording. Both paths need human review: the supplied code is not checked against the official standard, and a keyword match is only a sorting aid. With neither, the question stays **Uncategorized**.

5. **Readable evidence text.** The parser reads a PDF page by page, a Word file by heading section, a spreadsheet by populated row, and a text file by nonblank line. A scanned page without selectable text has no OCR fallback in this demo, so a person must review it.

6. **Indexing.** Each readable piece is saved with its source location. Think of the index as a shelf of searchable passages, each with an address back to its file. **Indexed** means the shelf was filled; it says nothing about whether a claim is accurate, current, or approved. This demo does not use embeddings or a vector database.

7. **Evidence matching.** The matcher compares words in a question with words in indexed passages. Reporting filler such as “report” is ignored; in a multi-question workbook, a candidate needs at least two meaningful shared words. Distinctive words count more, and the strongest candidates are kept. This first pass is weighted keyword search, **not a model call**. Similar wording can still point to the wrong company, year, unit, or a passage that answers only part of the question.

8. **Citations.** A candidate names its original file and location and shows a short excerpt. Open the original to verify the full context; an excerpt is a pointer, not proof on its own.

9. **AI measurement and relevance checks.** After indexing, a Vercel Queue worker sends text passages to OpenRouter's **GPT-6 Luna**. The model can return one measurement per passage (value, unit, scope, period), then label keyword candidates as **likely relevant**, **partly relevant**, or **likely unrelated**, with a source quote and any missing fact. The app rejects a claimed supporting quote unless it appears verbatim in the saved passage. These background checks do not block upload. Labels affect which suggestion appears first; they do not accept evidence or set its status. **Use synthetic files for this demo:** document text leaves BuktiESG for OpenRouter and its selected model provider.

10. **Evidence rules.** Ordinary code compares candidates with the question and reporting context. No usable source can mean **Missing**; unreadable material can mean **Needs manual review**; an unaccepted match is usually **Partial**; dates can mean **Outdated**. **Conflicting** requires comparable but incompatible extracted values, so it will not catch every real-world contradiction. **Verified** also needs a suitable source accepted by a person.

11. **Human review.** **Accept this evidence** records who checked a source. **Write the answer** records the answer and reviewer. These are independent: a source can be accepted without an answer, and an answer can be confirmed while an evidence gap remains. Neither is an independent audit opinion.

12. **Readiness and export.** Readiness counts *confirmed required answers*, not all questions or all indexed files. Here the target is **14/14**. Export assembles the saved answers, statuses, and unresolved items into a marked-up draft and registers; downloading it does not certify or submit anything.

## Answer and evidence sheet

Use these as **review prompts**, not as answers to copy without opening the documents. A-01–A-16 are filename prefixes in [sample/evidence](evidence/). A related file in parentheses provides a cross-check; the app shows the highest-ranked candidate and lets you expand the other matched files.

### Environmental questions

| Question | Evidence to inspect | Synthetic response to confirm |
| --- | --- | --- |
| Q-E-01 | A-08 (A-02) | Scope 1: **58.8 tCO2e** in FY2025. |
| Q-E-02 | A-08, A-02 (A-01) | Scope 2: **1,367.0 tCO2e** from 1,847.3 MWh of grid electricity and the Energy Commission's provisional **2024 Peninsular factor, 0.740 tCO2e/MWh**. |
| Q-E-03 | A-08 (A-02) | Scope 1 + 2 intensity: **0.0057032 tCO2e per finished unit**, using 1,425.8 tCO2e and 250,000 units. |
| Q-E-04 | A-09 (A-01, A-02) | **2,081,380 kWh** total: 1,847,300 grid electricity; 0 renewable fuel; 234,080 non-renewable fuel. Fuel-energy conversion factors are synthetic internal assumptions. |
| Q-E-05 | A-10 | **118,000 kWh** saved: LED 52,000; compressed air 41,000; chiller scheduling 25,000. |
| Q-E-06 | A-11 | **8,000 m³** water withdrawal, all municipal supply; groundwater and surface water 0. |
| Q-E-07 | A-03 | Waste: **214.7 tonnes generated**, **138.2 diverted**, **76.5 directed to disposal**. |
| Q-E-08 | A-03 | **12.6 tonnes** scheduled waste: SW410 4.8, SW305 2.9, SW110 3.1, SW409 1.8 tonnes. |
| Q-E-09 | A-12 | Recycled input materials: **190 of 800 tonnes = 23.75%** by mass. |
| Q-E-10 | A-14 | Packaging materials: **44 tonnes**: cardboard 22, paper 4, plastic 3, wood 15. |

For Q-E-02, the 2024 Peninsular grid factor comes from the [Energy Commission's provisional publication](https://myenergystats.st.gov.my/documents/d/guest/grid-emission-factor-gef-in-malaysia-2022-2024-provisional-).

### Social questions

| Question | Evidence to inspect | Synthetic response to confirm |
| --- | --- | --- |
| Q-S-01 | A-07 | **0 child-labour** and **0 forced-labour** incidents. |
| Q-S-02 | A-04 | **12.0 training hours per employee**: 3,216 hours / 268 employees. |
| Q-S-03 | A-07 | **268 employees**; **12.7% turnover**: 34 leavers / 268 employees. |
| Q-S-04 | A-07 | Women **35.8%**, men 64.2%; age under 30 **27.6%**, 30–50 **59.0%**, over 50 **13.4%**; women in management **37.5%**. |
| Q-S-05 | A-06 | **0 fatalities**, **4 injuries**; LTIFR **5.35** per million hours, based on 3 lost-time injuries / 561,000 hours. |
| Q-S-06 | A-06 | **268 of 268 employees**, or **100%**, received health-and-safety training. |
| Q-S-07 | A-15 | Community investments and donations: **RM48,000** total, RM42,000 cash and RM6,000 in kind. |

### Governance questions

| Question | Evidence to inspect | Synthetic response to confirm |
| --- | --- | --- |
| Q-G-01 | A-16 (A-05) | Code of Conduct **v2.0** and anti-corruption/whistleblowing policies **v4.0**, approved **14 February 2025**. |
| Q-G-02 | A-05 | Anti-bribery and anti-corruption training: **254 of 268 employees = 94.8%**. |
| Q-G-03 | A-13 | **0 substantiated privacy complaints** and **0 confirmed customer-data losses**; one encrypted-device theft was investigated and should still be explained. |

## A short interview talk track

> “I create a case and upload the customer's spreadsheet. BuktiESG reads its 20 existing questions, including 14 required ones. I then upload 16 synthetic supporting files. The system keeps the originals, extracts searchable passages with source locations, and suggests candidate evidence through keyword matching. Luna extracts measurements and checks whether each candidate passage seems to answer its question, quoting the saved text. I open the actual source, check the company, year, unit, and calculation, then accept suitable evidence and write the answer under my own name. The dashboard counts confirmed required answers, and I export a draft with its evidence trail. The final judgement remains with the reviewer.”

**Be candid if asked:** these records are synthetic; categories and first-pass matches are rule-based; scanned PDFs need manual handling; the model may misjudge relevance or a figure; a candidate excerpt may cover only part of a question; and a reviewer still has to catch contradictions that structured extraction did not expose.
