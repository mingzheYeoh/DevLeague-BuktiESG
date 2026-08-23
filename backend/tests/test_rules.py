"""Unit tests for the deterministic Evidence Status engine (SPEC-AMD-005 /
RULING-02 / C-15) — app/services/rules.py.

Covers at least one fixture producing each of MISSING, PARTIAL, VERIFIED,
OUTDATED, CONFLICTING, and NEEDS_MANUAL_REVIEW, plus NOT_APPLICABLE
(human-set, never recomputed by the engine) and the two step-2 constraints
called out in SPEC-AMD-005:

  - an unreadable candidate must not suppress a genuine conflict between two
    other reliable sources;
  - unreadable OCR output must never create a conflict.
"""

from __future__ import annotations

from datetime import date

from app.services.rules import (
    EvidenceCandidate,
    EvidenceRequirement,
    UnreadableDocument,
    compute_evidence_status,
    normalize_tokens,
)


REFERENCE_DATE = date(2026, 8, 22)


def test_missing_when_no_evidence_and_no_relevant_unreadable_document():
    result = compute_evidence_status(candidates=[], reference_date=REFERENCE_DATE)
    assert result.status == "MISSING"
    assert any(f["condition"] == "MISSING" for f in result.status_findings)


def test_partial_when_coverage_exists_but_is_incomplete():
    # A CANDIDATE (not yet human-accepted) evidence link with a claim.
    # Per this engine's judgment call (documented in rules.py), an
    # un-accepted candidate can never be VERIFIED, so this falls back to
    # PARTIAL — matching the First Vertical Slice's original MISSING/PARTIAL
    # behavior for a bare automated keyword match.
    candidate = EvidenceCandidate(
        link_id="link-1",
        link_status="CANDIDATE",
        claim_supported="Keyword overlap with question terms: electricity",
        source_location='{"type": "paragraph", "paragraph_index": 1}',
    )
    result = compute_evidence_status(candidates=[candidate], reference_date=REFERENCE_DATE)
    assert result.status == "PARTIAL"
    partial_findings = [f for f in result.status_findings if f["condition"] == "PARTIAL"]
    assert partial_findings
    assert any("human-accepted" in r for r in partial_findings[0]["reasons"])


def test_verified_requires_all_seven_conditions_and_human_acceptance():
    candidate = EvidenceCandidate(
        link_id="link-verified",
        link_status="ACCEPTED",
        claim_supported="Total electricity consumption for FY2025 confirmed by finance.",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        scope_description="All Malaysia sites",
        unit="kWh",
        value="128400",
        source_date=date(2025, 12, 31),
        source_location='{"type": "paragraph", "paragraph_index": 3}',
    )
    requirement = EvidenceRequirement(
        required_period_start=date(2025, 1, 1),
        required_period_end=date(2025, 12, 31),
        required_scope="Malaysia",
    )
    result = compute_evidence_status(
        candidates=[candidate], requirement=requirement, reference_date=REFERENCE_DATE
    )
    assert result.status == "VERIFIED"
    assert any(f["condition"] == "VERIFIED" for f in result.status_findings)


def test_verified_fails_to_partial_when_numeric_value_has_no_unit():
    candidate = EvidenceCandidate(
        link_id="link-no-unit",
        link_status="ACCEPTED",
        claim_supported="Total electricity consumption for FY2025.",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="128400",
        unit=None,  # numeric value present but no explainable unit
        source_location='{"type": "paragraph", "paragraph_index": 3}',
    )
    result = compute_evidence_status(candidates=[candidate], reference_date=REFERENCE_DATE)
    assert result.status == "PARTIAL"
    reasons = next(f for f in result.status_findings if f["condition"] == "PARTIAL")["reasons"]
    assert any("explainable unit" in r for r in reasons)


def test_outdated_when_no_explicit_period_and_older_than_24_months():
    candidate = EvidenceCandidate(
        link_id="link-old-policy",
        link_status="ACCEPTED",
        claim_supported="Anti-bribery policy, board-approved.",
        source_date=date(2023, 1, 1),  # > 24 months before REFERENCE_DATE
        source_location='{"type": "paragraph", "paragraph_index": 0}',
    )
    result = compute_evidence_status(candidates=[candidate], reference_date=REFERENCE_DATE)
    assert result.status == "OUTDATED"
    assert any(f["condition"] == "OUTDATED" for f in result.status_findings)


def test_outdated_when_source_is_outside_explicit_required_period():
    candidate = EvidenceCandidate(
        link_id="link-wrong-period",
        link_status="ACCEPTED",
        claim_supported="Electricity bill for January 2024.",
        period_start=date(2024, 1, 1),
        period_end=date(2024, 1, 31),
        source_location='{"type": "paragraph", "paragraph_index": 0}',
    )
    requirement = EvidenceRequirement(
        required_period_start=date(2025, 1, 1), required_period_end=date(2025, 12, 31)
    )
    result = compute_evidence_status(
        candidates=[candidate], requirement=requirement, reference_date=REFERENCE_DATE
    )
    assert result.status == "OUTDATED"


def test_conflicting_when_two_records_same_scope_and_period_differ_in_value():
    hr_record = EvidenceCandidate(
        link_id="link-hr",
        link_status="ACCEPTED",
        claim_supported="Employee headcount, HR system export.",
        scope_description="All Malaysia sites",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="482",
        unit="employees",
        source_location='{"type": "sheet", "sheet_name": "HR"}',
    )
    management_record = EvidenceCandidate(
        link_id="link-mgmt",
        link_status="ACCEPTED",
        claim_supported="Employee headcount, management report.",
        scope_description="All Malaysia sites",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="510",
        unit="employees",
        source_location='{"type": "sheet", "sheet_name": "Mgmt"}',
    )
    result = compute_evidence_status(
        candidates=[hr_record, management_record], reference_date=REFERENCE_DATE
    )
    assert result.status == "CONFLICTING"
    conflict_findings = [f for f in result.status_findings if f["condition"] == "CONFLICTING"]
    # Both sides of the conflict must be surfaced, never auto-resolved.
    assert {f["link_id"] for f in conflict_findings} == {"link-hr", "link-mgmt"}


def test_conflicting_precedence_beats_outdated_and_verified():
    # A CONFLICTING pair plus an unrelated, otherwise-VERIFIED candidate on
    # the same question: the frozen precedence CONFLICTING > OUTDATED >
    # PARTIAL > VERIFIED means the overall status is CONFLICTING, but the
    # VERIFIED finding for the third candidate is still preserved (findings
    # are never discarded).
    conflict_a = EvidenceCandidate(
        link_id="link-a",
        link_status="ACCEPTED",
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="100",
        unit="tonnes",
        claim_supported="Waste total per waste log.",
        source_location='{"type": "paragraph"}',
    )
    conflict_b = EvidenceCandidate(
        link_id="link-b",
        link_status="ACCEPTED",
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="140",
        unit="tonnes",
        claim_supported="Waste total per sustainability report.",
        source_location='{"type": "paragraph"}',
    )
    unrelated_verified = EvidenceCandidate(
        link_id="link-c",
        link_status="ACCEPTED",
        scope_description="Branch office",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        claim_supported="Recycling programme confirmed operational.",
        source_location='{"type": "paragraph"}',
    )
    result = compute_evidence_status(
        candidates=[conflict_a, conflict_b, unrelated_verified], reference_date=REFERENCE_DATE
    )
    assert result.status == "CONFLICTING"
    conditions = {f["condition"] for f in result.status_findings}
    assert "CONFLICTING" in conditions
    assert "VERIFIED" in conditions  # lower-priority finding preserved, not discarded


def test_needs_manual_review_when_relevant_unreadable_document_exists_c15():
    unreadable = UnreadableDocument(
        document_id="doc-1",
        document_type="POLICY",
        processing_status="NEEDS_MANUAL_REVIEW",
        original_filename="anti-bribery-policy-2025.pdf",
        extracted_tokens=(),
    )
    requirement = EvidenceRequirement(
        accepted_document_types=("POLICY",),
        keywords=("bribery",),
    )
    result = compute_evidence_status(
        candidates=[],
        requirement=requirement,
        unreadable_documents=[unreadable],
        reference_date=REFERENCE_DATE,
    )
    assert result.status == "NEEDS_MANUAL_REVIEW"
    finding = next(f for f in result.status_findings if f["condition"] == "NEEDS_MANUAL_REVIEW")
    assert finding["document_type"] == "POLICY"
    assert finding["matched_keyword"] == "bribery"


def test_missing_not_needs_manual_review_when_document_type_not_accepted_c15():
    # C-15 requires ALL three conditions; document_type mismatch alone must
    # not trigger NEEDS_MANUAL_REVIEW.
    unreadable = UnreadableDocument(
        document_id="doc-2",
        document_type="HR_DATA",
        processing_status="NEEDS_MANUAL_REVIEW",
        original_filename="bribery-policy.pdf",
        extracted_tokens=(),
    )
    requirement = EvidenceRequirement(accepted_document_types=("POLICY",), keywords=("bribery",))
    result = compute_evidence_status(
        candidates=[],
        requirement=requirement,
        unreadable_documents=[unreadable],
        reference_date=REFERENCE_DATE,
    )
    assert result.status == "MISSING"


def test_missing_not_needs_manual_review_without_exact_token_match_c15():
    # "brib" is a substring of "bribery" but not an exact token match —
    # C-15 requires exact-token matching only, no fuzzy matching.
    unreadable = UnreadableDocument(
        document_id="doc-3",
        document_type="POLICY",
        processing_status="NEEDS_MANUAL_REVIEW",
        original_filename="brib-policy.pdf",
        extracted_tokens=(),
    )
    requirement = EvidenceRequirement(accepted_document_types=("POLICY",), keywords=("bribery",))
    result = compute_evidence_status(
        candidates=[],
        requirement=requirement,
        unreadable_documents=[unreadable],
        reference_date=REFERENCE_DATE,
    )
    assert result.status == "MISSING"


def test_not_applicable_is_never_recomputed_by_the_engine():
    # Even with clean, fully-VERIFIED-looking evidence available, the engine
    # must return NOT_APPLICABLE unchanged once a human has set it — RULING-02
    # step 1: "the rule engine may never set or clear it."
    candidate = EvidenceCandidate(
        link_id="link-x",
        link_status="ACCEPTED",
        claim_supported="Would otherwise verify cleanly.",
        source_location='{"type": "paragraph"}',
    )
    result = compute_evidence_status(
        candidates=[candidate],
        current_status="NOT_APPLICABLE",
        not_applicable_reason="Company has no employees at this site; question does not apply.",
        reviewer_name="Jane Reviewer",
        reference_date=REFERENCE_DATE,
    )
    assert result.status == "NOT_APPLICABLE"
    assert result.status_findings == [
        {
            "condition": "NOT_APPLICABLE",
            "detail": (
                "Marked NOT_APPLICABLE by a human reviewer; the rule engine "
                "never recomputes or clears this status."
            ),
            "reason": "Company has no employees at this site; question does not apply.",
            "reviewer_name": "Jane Reviewer",
        }
    ]


def test_unreadable_candidate_never_creates_a_conflict():
    # SPEC-AMD-005 step-2 constraint: "unreadable OCR output must never
    # create a conflict." One readable, otherwise-clean candidate plus one
    # extraction-invalid candidate with a different value in the same
    # scope/period must NOT be reported as CONFLICTING.
    readable = EvidenceCandidate(
        link_id="link-readable",
        link_status="ACCEPTED",
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="100",
        unit="tonnes",
        claim_supported="Waste total per waste log.",
        source_location='{"type": "paragraph"}',
    )
    garbled_ocr = EvidenceCandidate(
        link_id="link-garbled",
        link_status="CANDIDATE",
        extraction_valid=False,  # OCR output deemed unreadable/invalid
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="9999",  # garbage value that would otherwise "conflict"
        unit="tonnes",
        claim_supported="???",
    )
    result = compute_evidence_status(
        candidates=[readable, garbled_ocr], reference_date=REFERENCE_DATE
    )
    assert result.status != "CONFLICTING"
    assert any(f["condition"] == "EXCLUDED_UNREADABLE" for f in result.status_findings)


def test_unreadable_candidate_never_suppresses_a_genuine_conflict():
    # SPEC-AMD-005 step-2 constraint: "an unreadable candidate must not
    # suppress a genuine conflict found between two other reliable sources."
    conflict_a = EvidenceCandidate(
        link_id="link-a",
        link_status="ACCEPTED",
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="100",
        unit="tonnes",
        claim_supported="Waste total per waste log.",
        source_location='{"type": "paragraph"}',
    )
    conflict_b = EvidenceCandidate(
        link_id="link-b",
        link_status="ACCEPTED",
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="140",
        unit="tonnes",
        claim_supported="Waste total per sustainability report.",
        source_location='{"type": "paragraph"}',
    )
    unreadable_third = EvidenceCandidate(
        link_id="link-unreadable",
        link_status="CANDIDATE",
        extraction_valid=False,
        scope_description="HQ",
        period_start=date(2025, 1, 1),
        period_end=date(2025, 12, 31),
        value="100",  # same as conflict_a; must not "resolve" the conflict away
        unit="tonnes",
    )
    result = compute_evidence_status(
        candidates=[conflict_a, conflict_b, unreadable_third], reference_date=REFERENCE_DATE
    )
    assert result.status == "CONFLICTING"


def test_c15_normalize_tokens_is_case_and_punctuation_insensitive():
    assert normalize_tokens("Anti-Bribery, Policy!") == frozenset({"anti", "bribery", "policy"})
    assert normalize_tokens(None) == frozenset()
    assert normalize_tokens("") == frozenset()
