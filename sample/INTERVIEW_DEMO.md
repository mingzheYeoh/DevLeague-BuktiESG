# BuktiESG: complete questionnaire demo

This is an interview walkthrough for the [hosted demo](https://buktiesg.vercel.app/). It uses one [sample questionnaire](questionnaire/customer-esg-questionnaire-2026.xlsx) and the **16 files whose names start with `A-`** in [sample/evidence](evidence/). The company, activity records, bills, policies, and answers are synthetic. The 2024 Peninsular grid factor used in the example is from the [Energy Commission's provisional grid-emission-factor publication](https://myenergystats.st.gov.my/documents/d/guest/grid-emission-factor-gef-in-malaysia-2022-2024-provisional-).

The goal is to show a complete *human-reviewed* questionnaire response, not to claim that an automated match proves a disclosure or that the export is an audit.

## Run the demo

1. Sign in and choose **Cases → New case**. Use a title such as “Tenggara Precision FY2025 ESG trial”, customer “Demo customer”, and reporting period **1 January–31 December 2025**. At the Questionnaire step, attach `customer-esg-questionnaire-2026.xlsx` and create the case.
2. Open **Questionnaire**. Expect **20 questions, 14 required**. They remain in the spreadsheet's row order, including Q-E-10 and Q-S-07 at the end. This is question extraction, not an AI-generated question list.
3. Open **Evidence** and leave **Upload as: Other**. Upload the 16 `A-` files. Set **Evidence dated** to the approval/preparation date printed in each file; for A-01 through A-04 and A-07, which have no later approval date, use the reporting-period end, **2025-12-31**. A-05 and A-16 are dated **2025-02-14**; A-06 is **2026-01-12**; A-08 through A-15 show their dates on their second line. The picker accepts several files with the same date; processing happens one file at a time. Expect all **16** documents to say **Indexed**.
4. Preview A-01 (PDF), A-02 (spreadsheet), A-05 (Word document), and A-10 (text). Switch between **Original file** and **Extracted text**. The extracted view shows the text fragments the matcher actually saw; it is not a newly created file. A questionnaire can say **Indexed** while its extracted-text preview is empty: its output is the question list, not evidence fragments.
5. Return to **Questionnaire**. Expect every question to have at least one **Candidate** and initially show **Partial** evidence. For each question, open its detail, check the cited file and the full original against the answer sheet below, then choose **Accept this evidence**. Use **Edit answer** to enter the reviewed response. Evidence acceptance and answer confirmation are separate human actions.
6. When all 20 have been reviewed, **Overview** should show **14 of 14 required answers confirmed**. **Export → Generate marked-up draft → Download package** produces one text summary and three CSV registers. It remains a labelled draft; the product does not send it to the customer.

Upload the questionnaire **before** the evidence. Matching is performed against questions that exist at upload time; earlier evidence is not automatically rematched when a questionnaire is added later. Keep the `B-`, `C-`, and `reference-` files out of this first run. They are useful for a separate second case that demonstrates incomplete, stale, conflicting, or unreadable material.

## How the system works, step by step

Think of Q-E-02 as an example: the customer asks for Scope 2 emissions. BuktiESG finds that question in the spreadsheet, finds a passage about Scope 2 in an uploaded emissions record, and shows where the passage came from. A person still checks the calculation and confirms the answer.

1. **Keep each case separate.** You sign in before opening a case. Its questionnaire, files, and review decisions belong to your organization. Matching searches evidence within that case, so another customer's files do not become its sources.

2. **Keep the original file.** On upload, the system stores the original privately. It also calculates a SHA-256 fingerprint, like a file's digital ID: if the exact same bytes are uploaded again to the same case, it reuses the existing document. The hosted demo accepts files up to 4 MiB each.

3. **Read the questionnaire's existing questions.** For a spreadsheet, the reader looks for the `external_question_id` and `question_text` columns. It reads nonblank rows across worksheets and also keeps each question's section, required flag, row order, and source cell. The sample gives 20 questions, 14 required. No AI invents or rewrites them; missing required columns send the file for manual review.

4. **Suggest an ESG label.** The system checks question wording against a small ESG disclosure keyword list and suggests an E, S, or G category and disclosure. This helps a reviewer sort questions. It is a suggestion, not an official standards interpretation or compliance verdict.

5. **Turn evidence into readable pieces.** An uploaded PDF is read page by page; a Word file by heading section; a spreadsheet by populated row; and a text file by nonblank line. **Original file** shows what was uploaded. **Extracted text** shows the pieces the matcher can read. A scanned image without selectable text has no OCR fallback here and needs manual review.

6. **Index those pieces.** The system saves each readable piece with its location, such as a PDF page, spreadsheet sheet and cells, or Word section and paragraph. That saved text is the index searched later. **Indexed** means searchable text was stored; it does not mean the source is accurate, recent, sufficient, or approved. This demo does not use embeddings or a vector database.

7. **Find possible evidence.** The matcher compares words in a question with words in each indexed piece. More distinctive shared words count more than common words. It proposes the strongest piece from each matching document; the question page shows the highest-scoring candidate. This is weighted keyword search, not an AI judgement: a similar phrase can still belong to the wrong company, year, unit, or an incomplete figure.

8. **Show where the claim came from.** Each candidate points back to a stored piece. The page shows its filename, location, and short excerpt so you can open the original and check it. An excerpt helps you find the passage; it does not prove that the whole question has been answered.

9. **Apply evidence rules.** With no usable source, a question can be **Missing**; unreadable relevant material can mean **Needs manual review**; an unaccepted match is usually **Partial**. Dates and reporting periods can make evidence **Outdated**. **Conflicting** requires incompatible values to have been extracted, so the hosted demo cannot be relied on to detect every contradiction. **Verified** requires a suitable source accepted by a person.

10. **Record two human decisions.** **Accept this evidence** records who checked and accepted the source. **Edit answer** separately records the response and its reviewer. A verified source is not the same as a confirmed answer, and neither is an independent audit opinion.

11. **Treat AI value extraction as optional.** The project can queue a later job to extract numeric values, but this hosted deployment has no DeepSeek key or separate worker. Question reading, indexing, keyword matching, and this full trial work without it. The reviewer must reconcile figures and catch contradictions that the current data has not exposed.

12. **Count readiness and export a draft.** The dashboard counts confirmed *required* answers: here, 14 out of 14, even though the questionnaire has 20 questions. The browser builds a marked-up draft and registers from the case data, including unresolved items. Downloading it does not submit anything to the customer or certify the figures.

## Answer and evidence sheet

Use these as **review prompts**, not as answers to copy without opening the documents. `A-01`–`A-16` are filename prefixes in the evidence folder. A related file in parentheses provides a cross-check, but the app may display only its highest-scoring candidate.

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
| Q-S-01 | A-07 | **0 child-labour** and **0 forced-labour** incidents. |
| Q-S-02 | A-04 | **12.0 training hours per employee**: 3,216 hours / 268 employees. |
| Q-S-03 | A-07 | **268 employees**; **12.7% turnover**: 34 leavers / 268 employees. |
| Q-S-04 | A-07 | Women **35.8%**, men 64.2%; age under 30 **27.6%**, 30–50 **59.0%**, over 50 **13.4%**; women in management **37.5%**. |
| Q-S-05 | A-06 | **0 fatalities**, **4 injuries**; LTIFR **5.35** per million hours, based on 3 lost-time injuries / 561,000 hours. |
| Q-S-06 | A-06 | **268 of 268 employees**, or **100%**, received health-and-safety training. |
| Q-S-07 | A-15 | Community investments and donations: **RM48,000** total, RM42,000 cash and RM6,000 in kind. |
| Q-G-01 | A-16 (A-05) | Code of Conduct **v2.0** and anti-corruption/whistleblowing policies **v4.0**, approved **14 February 2025**. |
| Q-G-02 | A-05 | Anti-bribery and anti-corruption training: **254 of 268 employees = 94.8%**. |
| Q-G-03 | A-13 | **0 substantiated privacy complaints** and **0 confirmed customer-data losses**; one encrypted-device theft was investigated and should still be explained. |

## A short interview talk track

> “I upload the customer's spreadsheet first. BuktiESG reads its rows into 20 traceable questions, with 14 marked required. Then I upload 16 supporting records in four formats. Each record is broken into source-located text fragments and indexed. A transparent keyword matcher proposes passages, but it does not decide whether a figure is correct. I open the original, check the scope, year, unit and calculation, accept the source, and write the answer under my own name. Finally, the dashboard counts the confirmed required answers and I export a draft with the evidence trail. The system speeds up finding evidence while leaving the final judgement with a person.”

**Honest limits to mention if asked:** the sample records are synthetic; the classifier is a keyword suggestion; scanned PDFs need manual handling; the hosted demo does not run LLM value extraction; a candidate excerpt may cover only part of a multi-part question; and conflicts between believable documents still require a reviewer when structured values have not been extracted.
