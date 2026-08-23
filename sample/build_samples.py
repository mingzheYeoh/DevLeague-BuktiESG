"""Regenerate the binary sample files in this folder.

The `.txt` files are committed as-is and readable in any editor. The `.xlsx`,
`.docx` and `.pdf` files are binary, so this script is the readable source for
them — edit here and re-run rather than hand-editing a binary.

Run it with the backend's environment, which already has openpyxl, python-docx
and PyMuPDF:

    cd backend
    uv run python ../sample/build_samples.py

Everything it writes is **synthetic**, describing a company that does not
exist, with two exceptions clearly marked `reference-` in `evidence/` — those
carry real published figures with their sources named inside the file.

Why these formats: the backend has one parser per format and they chunk
differently, which changes what a source citation looks like.

    .pdf   one chunk per page          -> location is a page number
    .docx  one chunk per heading       -> location is a heading path
    .xlsx  one chunk per row           -> location is a sheet + cell range
    .txt   one chunk per non-blank line -> location is a line

So each sample file is deliberately laid out with one fact per chunk. A
one-fact-per-line text file produces a precise citation; a wall of prose
produces a vague one.
"""

from __future__ import annotations

from pathlib import Path

import pymupdf
from docx import Document
from openpyxl import Workbook

ROOT = Path(__file__).resolve().parent
QUESTIONNAIRE_DIR = ROOT / "questionnaire"
EVIDENCE_DIR = ROOT / "evidence"

COMPANY = "BuktiPack Manufacturing Sdn. Bhd."
SITE = "Lot 42, Jalan Perindustrian 3, Shah Alam, Selangor"


# --------------------------------------------------------------------------- #
# Questionnaires
# --------------------------------------------------------------------------- #

# (external_question_id, question_text, section, is_required)
#
# Wording is chosen so the keyword mapper in
# packages/ai-pipeline/src/ai_pipeline/sedg_taxonomy.py can actually reach a
# topic — e.g. "kWh" reaches E1.2, "LTIFR" reaches S2.1. Two questions are
# worded so that nothing maps and nothing matches, on purpose: a demo where
# every row lights up green teaches you nothing about the gaps.
QUESTIONS: list[tuple[str, str, str, bool]] = [
    (
        "Q-E-01",
        "Report total annual electricity consumption in kWh for the reporting period.",
        "Environmental",
        True,
    ),
    (
        "Q-E-02",
        "Disclose Scope 1 and Scope 2 greenhouse gas emissions, stating the grid emission factor used.",
        "Environmental",
        True,
    ),
    (
        "Q-E-03",
        "State total water withdrawal by source for the reporting period.",
        "Environmental",
        True,
    ),
    (
        "Q-E-04",
        "What percentage of waste generated was recycled or diverted from disposal?",
        "Environmental",
        True,
    ),
    (
        "Q-E-05",
        "Describe the environmental policy and state when it was last approved.",
        "Environmental",
        True,
    ),
    (
        "Q-E-06",
        "Does the company purchase or generate renewable energy such as solar?",
        "Environmental",
        False,
    ),
    (
        "Q-S-01",
        "Report the work-related injury rate (LTIFR) and any fatalities.",
        "Social",
        True,
    ),
    (
        "Q-S-02",
        "State total workforce headcount and the employment type breakdown.",
        "Social",
        True,
    ),
    (
        "Q-S-03",
        "Report gender diversity, including women in management positions.",
        "Social",
        True,
    ),
    (
        "Q-S-04",
        "State the average training hours per employee.",
        "Social",
        False,
    ),
    (
        "Q-S-05",
        "Describe the grievance mechanism available to workers.",
        "Social",
        False,
    ),
    (
        "Q-G-01",
        "Describe anti-bribery and anti-corruption controls.",
        "Governance",
        True,
    ),
    (
        "Q-G-02",
        "Is there a whistleblowing policy, and how many reports were received?",
        "Governance",
        True,
    ),
    (
        "Q-G-03",
        "Describe cybersecurity governance and disclose any data breach in the period.",
        "Governance",
        False,
    ),
    (
        "Q-G-04",
        "Confirm the supplier code of conduct prohibits child labour and forced labour.",
        "Governance",
        True,
    ),
]


def build_questionnaire() -> None:
    """The header row is load-bearing: the parser requires exactly
    `external_question_id | question_text | section | is_required` on row 1.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Questionnaire"
    ws.append(["external_question_id", "question_text", "section", "is_required"])
    for qid, text, section, required in QUESTIONS:
        ws.append([qid, text, section, required])
    ws.column_dimensions["A"].width = 12
    ws.column_dimensions["B"].width = 95
    ws.column_dimensions["C"].width = 16
    ws.column_dimensions["D"].width = 12
    wb.save(QUESTIONNAIRE_DIR / "customer-esg-questionnaire-2026.xlsx")


def build_broken_questionnaire() -> None:
    """Deliberately wrong headers, to exercise the parse-failure path.

    Uploading this as a QUESTIONNAIRE should leave the document FAILED with a
    readable error, and must not create a single question. Silently producing
    zero questions from an unreadable file would be the actual bug.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["No.", "Question", "Category", "Mandatory?"])
    ws.append(["1", "Report total annual electricity consumption.", "Environment", "Yes"])
    ws.append(["2", "Describe the environmental policy.", "Environment", "Yes"])
    wb.save(QUESTIONNAIRE_DIR / "broken-questionnaire-wrong-headers.xlsx")


# --------------------------------------------------------------------------- #
# Evidence — PDF (one chunk per page)
# --------------------------------------------------------------------------- #

BILL_MONTHS = [
    ("January 2025", "01/01/2025 - 31/01/2025", 12840, "5,829.36"),
    ("February 2025", "01/02/2025 - 28/02/2025", 12610, "5,724.94"),
    ("March 2025", "01/03/2025 - 31/03/2025", 12970, "5,888.38"),
]


def build_electricity_bills_pdf() -> None:
    """Three monthly statements, one per page, so each month cites its own page.

    The 45.40 sen/kWh tariff is the real published RP4 rate (see
    evidence/reference-tnb-tariff-rp4.txt); the account, premise and kWh
    figures are invented.
    """
    doc = pymupdf.open()
    for month, period, kwh, amount in BILL_MONTHS:
        page = doc.new_page()
        lines = [
            "ELECTRICITY STATEMENT (SYNTHETIC SAMPLE - NOT A REAL BILL)",
            "",
            f"Account holder: {COMPANY}",
            f"Premise: {SITE}",
            "Account number: 0123456789 (synthetic)",
            f"Billing month: {month}",
            f"Billing period: {period}",
            "",
            f"Total electricity consumption: {kwh:,} kWh",
            "Applicable tariff: 45.40 sen/kWh (Peninsular Malaysia base tariff, RP4)",
            f"Amount payable: RM {amount}",
            "",
            "Meter reading basis: actual",
            "This statement covers grid-supplied electricity only.",
            "No renewable energy purchase is recorded on this account.",
        ]
        page.insert_text((60, 70), "\n".join(lines), fontsize=10, fontname="helv")
    doc.save(EVIDENCE_DIR / "electricity-bills-jan-mar-2025.pdf")
    doc.close()


def build_unreadable_pdf() -> None:
    """A file that claims to be a PDF and is not.

    Exercises the failure path end to end: the upload succeeds, processing
    fails, the document lands in FAILED with an error message, and the Retry
    button becomes available. Only FAILED and NEEDS_MANUAL_REVIEW are
    retryable, so this is the only sample that can demonstrate Retry.
    """
    payload = (
        b"%PDF-1.4\n"
        b"% Synthetic sample: a deliberately corrupt PDF with no valid xref\n"
        b"% table and no extractable text layer. Stands in for a phone photo\n"
        b"% of a paper record, which is the common real-world case.\n"
        b"1 0 obj << /Type /Catalog >> endobj\n"
        b"trailer << /Root 1 0 R >>\n"
    )
    (EVIDENCE_DIR / "unreadable-scan.pdf").write_bytes(payload)


# --------------------------------------------------------------------------- #
# Evidence — XLSX (one chunk per row)
# --------------------------------------------------------------------------- #


def build_waste_tracker_xlsx() -> None:
    """Monthly waste log. One row per month means one citable chunk per month.

    The FY2025 recycling rate here (41%) deliberately contradicts
    weighbridge-summary-q4-fy2025.txt (53%). Both are plausible; neither is
    marked as correct. Resolving that is a human's job.
    """
    wb = Workbook()
    ws = wb.active
    ws.title = "FY2025"
    ws.append(["Month", "Total waste generated (kg)", "Recycled (kg)", "Recycling rate (%)"])
    rows = [
        ("2025-01", 18400, 7360, 40),
        ("2025-02", 17900, 7160, 40),
        ("2025-03", 19100, 8022, 42),
        ("2025-04", 18700, 7667, 41),
        ("2025-05", 19400, 7954, 41),
        ("2025-06", 18200, 7280, 40),
        ("2025-07", 19800, 8316, 42),
        ("2025-08", 20100, 8442, 42),
        ("2025-09", 19300, 7913, 41),
        ("2025-10", 18900, 7749, 41),
        ("2025-11", 19600, 8036, 41),
        ("2025-12", 17600, 7216, 41),
    ]
    for row in rows:
        ws.append(list(row))
    total_waste = sum(r[1] for r in rows)
    total_recycled = sum(r[2] for r in rows)
    ws.append([])
    ws.append(
        [
            "FY2025 total",
            total_waste,
            total_recycled,
            round(total_recycled / total_waste * 100),
        ]
    )
    ws.append(
        [
            "Note",
            f"FY2025 recycling rate {round(total_recycled / total_waste * 100)}% "
            "per this internal tracker. Synthetic data.",
        ]
    )
    ws.column_dimensions["A"].width = 16
    ws.column_dimensions["B"].width = 26
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 20
    wb.save(EVIDENCE_DIR / "waste-tracker-fy2025.xlsx")


# --------------------------------------------------------------------------- #
# Evidence — DOCX (one chunk per heading section)
# --------------------------------------------------------------------------- #


def _write_docx(path: Path, title: str, sections: list[tuple[str, list[str]]]) -> None:
    doc = Document()
    doc.add_heading(title, level=0)
    for heading, paragraphs in sections:
        doc.add_heading(heading, level=1)
        for paragraph in paragraphs:
            doc.add_paragraph(paragraph)
    doc.save(path)


def build_environmental_policy_docx() -> None:
    _write_docx(
        EVIDENCE_DIR / "environmental-policy-v3-2025.docx",
        f"Environmental Policy v3 - {COMPANY}",
        [
            (
                "Document control",
                [
                    "SYNTHETIC FIXTURE. Fictional entity, invented content.",
                    "Version 3, effective 1 January 2025, superseding version 2 of 2021.",
                    "Approved by the Board of Directors on 12 December 2024.",
                    "Next scheduled review: December 2026.",
                ],
            ),
            (
                "Purpose and scope",
                [
                    "This environmental policy applies to all operations at the Shah Alam "
                    "manufacturing site, including contractors working on site.",
                ],
            ),
            (
                "Commitments",
                [
                    "Measure and reduce energy consumption year on year.",
                    "Segregate waste at source and increase the share diverted from landfill.",
                    "Monitor water withdrawal and investigate any month-on-month increase "
                    "above ten percent.",
                    "Comply with all applicable Malaysian environmental legislation.",
                ],
            ),
            (
                "Accountability",
                [
                    "The Operations Manager owns day-to-day implementation and reports "
                    "quarterly to the Board Sustainability Committee.",
                ],
            ),
        ],
    )


def build_employee_handbook_docx() -> None:
    """Dated 2022 on purpose — old enough that a reviewer should question
    whether it still describes current practice."""
    _write_docx(
        EVIDENCE_DIR / "employee-handbook-2022.docx",
        f"Employee Handbook 2022 - {COMPANY}",
        [
            (
                "Document control",
                [
                    "SYNTHETIC FIXTURE. Fictional entity, invented content.",
                    "Issued March 2022. No revision has been issued since.",
                ],
            ),
            (
                "Grievance procedure",
                [
                    "Any worker may raise a grievance through the confidential telephone "
                    "line, by writing to Human Resources, or through the anonymous "
                    "suggestion box at the canteen entrance.",
                    "The grievance mechanism guarantees no retaliation against a worker "
                    "who raises a concern in good faith.",
                    "Human Resources acknowledges a grievance within five working days.",
                ],
            ),
            (
                "Working hours and leave",
                [
                    "Standard working hours are 8.30am to 5.30pm, Monday to Friday.",
                    "Annual leave entitlement starts at 14 days and rises with service.",
                ],
            ),
        ],
    )


def build_anti_bribery_policy_docx() -> None:
    _write_docx(
        EVIDENCE_DIR / "anti-bribery-policy-2025.docx",
        f"Anti-Bribery and Whistleblowing Policy 2025 - {COMPANY}",
        [
            (
                "Document control",
                [
                    "SYNTHETIC FIXTURE. Fictional entity, invented content.",
                    "Version 2, effective 1 February 2025. Signed by the Managing Director.",
                ],
            ),
            (
                "Anti-bribery and anti-corruption controls",
                [
                    "Facilitation payments and kickbacks are prohibited without exception.",
                    "Gifts or hospitality above RM 500 require written approval from the "
                    "Compliance Officer before being offered or accepted.",
                    "All commercial agents are screened before appointment and re-screened "
                    "every two years.",
                    "Anti-corruption training is mandatory for all staff in procurement, "
                    "sales and finance roles.",
                ],
            ),
            (
                "Whistleblowing",
                [
                    "The whistleblowing policy allows any employee, supplier or contractor "
                    "to raise a concern to the Compliance Officer or directly to the Audit "
                    "Committee chair.",
                    "Two whistleblowing reports were received in FY2025. Both were "
                    "investigated and closed; neither was substantiated.",
                ],
            ),
        ],
    )


# --------------------------------------------------------------------------- #
# Evidence — plain text (one chunk per non-blank line)
# --------------------------------------------------------------------------- #

TEXT_FILES: dict[str, list[str]] = {
    # -- REAL published reference data. Sources named in-file. ----------------
    "reference-malaysia-grid-emission-factor.txt": [
        "MALAYSIA GRID EMISSION FACTOR - REAL PUBLISHED REFERENCE DATA",
        "Figures below are real. Source: Grid Emission Factor (GEF) in Malaysia,"
        " published by the Energy Commission of Malaysia (Suruhanjaya Tenaga)."
        " Retrieved 2026-08-23. Content was rephrased for compliance with"
        " licensing restrictions.",
        "Unit: Gg CO2e/GWh, numerically equal to tCO2e/MWh.",
        "Provisional series 2022-2024: 2024 Peninsular 0.740, Sabah 0.539, Sarawak 0.199.",
        "Provisional series 2022-2024: 2023 Peninsular 0.760, Sabah 0.545, Sarawak 0.206.",
        "Provisional series 2022-2024: 2022 Peninsular 0.769, Sabah 0.531, Sarawak 0.199.",
        "Earlier series 2017-2022: 2022 Peninsular 0.774, Sabah 0.525, Sarawak 0.199.",
        "Earlier series 2017-2022: 2021 Peninsular 0.757, Sabah 0.524, Sarawak 0.198.",
        "Earlier series 2017-2022: 2020 Peninsular 0.821, Sabah 0.503, Sarawak 0.203.",
        "Earlier series 2017-2022: 2019 Peninsular 0.753, Sabah 0.548, Sarawak 0.222.",
        "Earlier series 2017-2022: 2018 Peninsular 0.797, Sabah 0.500, Sarawak 0.193.",
        "Earlier series 2017-2022: 2017 Peninsular 0.767, Sabah 0.530, Sarawak 0.213.",
        "DISCREPANCY WORTH NOTING: the two published series give different"
        " Peninsular values for 2022 - 0.769 provisional against 0.774 earlier."
        " Both come from the same publisher. This is a real example of the"
        " problem this product exists to surface: two credible sources, one"
        " metric, two numbers, and no automatic way to decide which is right.",
        "A Scope 2 location-based calculation multiplies grid electricity"
        " consumption in MWh by the grid emission factor for the year and region.",
        "Scope 1 covers direct combustion the company controls, such as diesel"
        " burned in its own generator or forklift; the grid emission factor does"
        " not apply to it.",
    ],
    "reference-tnb-tariff-rp4.txt": [
        "PENINSULAR MALAYSIA ELECTRICITY TARIFF - REAL PUBLISHED REFERENCE DATA",
        "Figures below are real. Source: Tenaga Nasional Berhad and Energy"
        " Commission announcements on Regulatory Period 4, as reported in"
        " Malaysian press releases retrieved 2026-08-23. Content was rephrased"
        " for compliance with licensing restrictions.",
        "Regulatory Period 4 (RP4) runs from 2025 to 2027.",
        "The RP4 base tariff for Peninsular Malaysia was set at 45.40 sen/kWh.",
        "That figure was a revision of the 45.62 sen/kWh approved in December 2024.",
        "The preceding base tariff was 39.95 sen/kWh, so RP4 represents an increase.",
        "A tariff is a price per unit of electricity. It is not an emission"
        " factor and cannot be substituted for one.",
    ],
    "reference-esg-disclosure-frameworks.txt": [
        "ESG DISCLOSURE FRAMEWORKS FOR SMES - REAL PUBLISHED REFERENCE DATA",
        "Facts below are real. Sources: Capital Markets Malaysia announcements on"
        " the Simplified ESG Disclosure Guide, and the ASEAN Capital Markets"
        " Forum media release on the ASEAN Simplified ESG Disclosure Guide."
        " Retrieved 2026-08-23. Content was rephrased for compliance with"
        " licensing restrictions.",
        "The Simplified ESG Disclosure Guide (SEDG) was launched by Capital"
        " Markets Malaysia in October 2023 with 35 priority disclosures, tiered"
        " into basic, intermediate and advanced levels.",
        "The ASEAN Simplified ESG Disclosure Guide (ASEDG) Version 1 was launched"
        " by the ASEAN Capital Markets Forum in April 2025 with 38 priority"
        " disclosures, consolidating IFRS Sustainability Disclosure Standards,"
        " GRI Standards and the local frameworks of ten ASEAN member states.",
        "Both guides are tiered so a smaller supplier can start with a basic set"
        " and add depth later.",
        "CAVEAT: the taxonomy this application maps against lives in"
        " packages/ai-pipeline/src/ai_pipeline/sedg_taxonomy.py and is a"
        " representative structure of the right shape and size, not a verified"
        " transcription of either published guide. Its own docstring says so."
        " A mapping produced by this application is not proof of compliance.",
        "NOTE ON THIS FILE: it deliberately contains no list of pillar or topic"
        " names. An earlier draft listed all fifteen, and because retrieval here"
        " is plain keyword overlap, those lines then out-matched real company"
        " records for almost every question - a glossary looks relevant to"
        " everything and proves nothing. Worth remembering before adding a"
        " framework cheat-sheet to a real evidence library.",
    ],
    # -- SYNTHETIC company records. Invented. --------------------------------
    "water-utility-statement-fy2025.txt": [
        f"WATER UTILITY SUMMARY FY2025 - {COMPANY} (SYNTHETIC SAMPLE)",
        "SYNTHETIC FIXTURE. Invented volumes.",
        f"Premise: {SITE}",
        "Sole source: licensed municipal supply. No groundwater abstraction and no"
        " surface water intake at this site.",
        "Q1 2025 water withdrawal from municipal supply: 1,240 cubic metres.",
        "Q2 2025 water withdrawal from municipal supply: 1,310 cubic metres.",
        "Q3 2025 water withdrawal from municipal supply: 1,180 cubic metres.",
        "Q4 2025 water withdrawal from municipal supply: 1,265 cubic metres.",
        "FY2025 total water withdrawal: 4,995 cubic metres from municipal supply.",
        "Trade effluent is discharged to the industrial sewerage network under a"
        " standing consent; no effluent volume is metered separately.",
    ],
    "weighbridge-summary-q4-fy2025.txt": [
        f"WEIGHBRIDGE RECONCILIATION Q4 FY2025 - {COMPANY} (SYNTHETIC SAMPLE)",
        "SYNTHETIC FIXTURE. Invented tonnages.",
        "Prepared by the appointed waste contractor from weighbridge tickets, not"
        " from the internal tracker.",
        "Q4 FY2025 total waste collected and weighed: 56,100 kg.",
        "Q4 FY2025 material sent for recycling: 29,733 kg.",
        "Recycling rate for FY2025 calculated on weighbridge tickets: 53 percent.",
        "CONTRADICTION: the internal spreadsheet waste-tracker-fy2025.xlsx states"
        " a FY2025 recycling rate of 41 percent. This document states 53 percent"
        " for the same year. Both cannot be right and neither is marked correct.",
        "The contractor attributes the gap to mixed recyclables recorded as"
        " general waste in the internal log, but this has not been reconciled.",
    ],
    "safety-incident-register-fy2025.txt": [
        f"SAFETY INCIDENT REGISTER FY2025 - {COMPANY} (SYNTHETIC SAMPLE)",
        "SYNTHETIC FIXTURE. Invented incidents; no real person is described.",
        # Not "Reporting period: ..." — that phrasing overlapped almost every
        # question in the set and stole their citations.
        "Register covers 1 January 2025 to 31 December 2025.",
        # Avoids a leading "Total", which stole the electricity and water
        # questions from their own documents.
        "Hours worked across all employees and contractors: 93,600.",
        "Number of recordable work-related injuries resulting in lost time: 2.",
        "Lost time injury frequency rate (LTIFR) per million hours worked: 21.4.",
        "Number of work-related fatalities: 0.",
        "Total days lost to work-related injury: 11.",
        "Incident 1, March 2025: laceration to the hand at the carton former."
        " Machine guard interlock replaced. Case closed.",
        "Incident 2, August 2025: sprain while manually lifting a pallet."
        " Mechanical lift assist introduced at that station. Case closed.",
        "No occupational illness case was recorded in FY2025.",
    ],
    "hr-workforce-summary-fy2025.txt": [
        f"WORKFORCE SUMMARY FY2025 - {COMPANY} (SYNTHETIC SAMPLE)",
        "SYNTHETIC FIXTURE. Invented aggregates; no real person is described.",
        "Workforce headcount at 31 December 2025: 45 employees.",
        "Employment type breakdown: 38 permanent full-time, 4 fixed-term"
        " contract, 3 part-time.",
        "Gender diversity across the whole workforce: 19 women and 26 men.",
        "Women in management positions: 3 of 8 management roles, which is 37.5"
        " percent.",
        "Average training hours per employee in FY2025: 14.2 hours.",
        "Training hours delivered across FY2025: 639 hours.",
        "New hires during FY2025: 6. Voluntary departures during FY2025: 4.",
        # Avoids the bare word "rate", which collided with the injury-rate question.
        "Employee turnover for FY2025: 8.9 percent.",
        "All employees are paid at or above the Malaysian statutory minimum wage.",
    ],
    "supplier-code-of-conduct-2025.txt": [
        f"SUPPLIER CODE OF CONDUCT 2025 - {COMPANY} (SYNTHETIC SAMPLE)",
        "SYNTHETIC FIXTURE. Fictional entity, invented content.",
        "Version 1, issued 1 March 2025. Acceptance is a condition of order.",
        "The code prohibits child labour at every tier of the supply chain, with"
        " no exception for family or seasonal work.",
        "The code prohibits forced labour, bonded labour and the retention of"
        " worker identity documents or passports as a condition of employment.",
        "Recruitment fees may not be charged to workers under any circumstances.",
        "Suppliers must permit announced social compliance audits on request.",
        "12 of 34 active suppliers had returned a signed copy of this code as at"
        " 31 December 2025, so coverage is incomplete.",
        "No supplier audit had been completed at the time of writing.",
    ],
}


def build_text_files() -> None:
    for name, lines in TEXT_FILES.items():
        (EVIDENCE_DIR / name).write_text("\n".join(lines) + "\n", encoding="utf-8")


# --------------------------------------------------------------------------- #


def main() -> None:
    QUESTIONNAIRE_DIR.mkdir(parents=True, exist_ok=True)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    build_questionnaire()
    build_broken_questionnaire()
    build_electricity_bills_pdf()
    build_unreadable_pdf()
    build_waste_tracker_xlsx()
    build_environmental_policy_docx()
    build_employee_handbook_docx()
    build_anti_bribery_policy_docx()
    build_text_files()

    for directory in (QUESTIONNAIRE_DIR, EVIDENCE_DIR):
        rel = directory.relative_to(ROOT)
        for path in sorted(directory.iterdir()):
            print(f"  {rel}/{path.name}  ({path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
