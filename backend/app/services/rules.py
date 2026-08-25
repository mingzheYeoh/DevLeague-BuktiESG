"""Deterministic evidence-status rule engine — SPEC-AMD-005 / RULING-02 / C-15.

AGENTS.md §3.2: `evidence_status` and `status_findings` must be computed by a
deterministic rule engine from validated evidence, never set from AI output.
This module is a pure function of plain data (BLOCKER-04: no DB session, no
HTTP client, no provider-specific logic) — the orchestration layer
(app/routers/documents.py) loads persisted rows, builds the dataclasses
below, calls `compute_evidence_status()`, and persists the result.

Implements the exact four-step evaluation from docs/spec/AMENDMENTS.md
SPEC-AMD-005 and docs/decisions/CTO-RULINGS.md RULING-02/C-15:

    1. NOT_APPLICABLE — human-controlled only (reason + reviewer identity).
       Never set or cleared by this engine; if the caller reports the
       current status is already NOT_APPLICABLE, the engine returns it
       unchanged and does not evaluate anything else.

    2. Exclude unreadable/extraction-invalid evidence from the
       evidence-quality computation entirely.

    3. Evaluate the remaining readable evidence using the frozen precedence
       CONFLICTING > OUTDATED > PARTIAL > VERIFIED. Lower-priority findings
       are never discarded — every detected condition is preserved in
       structured `status_findings`, summarized in `status_reason`.

    4. Otherwise: NEEDS_MANUAL_REVIEW if a relevant unreadable document may
       materially affect the question (C-15: exact-token keyword match only,
       no fuzzy/embedding/LLM matching), else MISSING.

Two rules that constrain step 2 (SPEC-AMD-005, easy to violate):
  - An unreadable candidate must never suppress a genuine conflict between
    two other reliable sources — enforced structurally here because
    unreadable/extraction-invalid candidates are filtered out of `readable`
    BEFORE conflict detection runs, so they can never mask a conflict that
    exists between two other readable records.
  - Unreadable OCR output must never create a conflict — enforced the same
    way: an excluded candidate never participates in the conflict-detection
    groups at all, so it cannot manufacture one.

Design decisions made here that the spec does not fully pin down (recorded
explicitly, not silently resolved — AGENTS.md §2):

  * VERIFIED requires the winning candidate's `link_status == "ACCEPTED"`
    (i.e. a human has accepted the evidence link), not just `CANDIDATE`.
    Rationale: Main Spec §17 Gate P4 requires "AI confidence does not
    participate in the Verified determination." An unreviewed
    system-proposed candidate is AI output; treating it as sufficient for
    VERIFIED would let AI confidence drive the highest-trust status. This is
    a CTO judgment call, not something SPEC-AMD-005/RULING-02 states in so
    many words, and should be confirmed by CEO/COO/Ground-Truth Approver
    alongside the rest of SPEC-AMD-005.
  * CONFLICTING/PARTIAL/VERIFIED-period grouping uses (scope_description,
    period_start, period_end) as the "same metric" key, since this
    engine call is always scoped to one question's candidates already (each
    `evidence_links` row already belongs to exactly one question) — there is
    no separate `metric_key` column, and the task scope explicitly excludes
    building the fuller SEDG-mapped data model.
  * The OUTDATED 24-month fallback (DEC-007 / Main Spec §6.2) uses each
    candidate's `source_date` (falling back to `period_end` if absent)
    compared against `reference_date` (defaults to `date.today()`).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from datetime import date


# --------------------------------------------------------------------------- #
# Input data (plain, DB-free per BLOCKER-04)
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class EvidenceCandidate:
    """One `evidence_links` row's data, as needed by the rule engine."""

    link_id: str
    link_status: str = "CANDIDATE"  # CANDIDATE | ACCEPTED | REJECTED | INVALIDATED
    # Step 2: False => this specific evidence's extraction was invalid/
    # unreadable (e.g. garbled OCR). Independent of the parent document's
    # overall processing_status.
    extraction_valid: bool = True
    claim_supported: str | None = None
    quoted_excerpt: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    scope_description: str | None = None
    unit: str | None = None
    value: str | None = None
    # The underlying document's source_date (e.g. a policy's last-approval
    # date), used for the no-explicit-period OUTDATED fallback.
    source_date: date | None = None
    # The server-resolved location (never AI-supplied — AGENTS.md §3.3).
    # Must be non-empty for VERIFIED condition 7.
    source_location: str | None = None


@dataclass(frozen=True)
class UnreadableDocument:
    """A Document this engine could not read (processing_status ==
    NEEDS_MANUAL_REVIEW), relevant only to step 4 / the C-15 relevance test.

    `extracted_tokens` must contain ONLY normalized tokens from content that
    DID successfully extract (filename, metadata, heading text) — never body
    text a failed extraction could not produce. That is what keeps the C-15
    relevance test evaluable despite the document being unreadable.
    """

    document_id: str
    document_type: str
    processing_status: str
    original_filename: str
    extracted_tokens: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceRequirement:
    """What the question requires, per Main Spec §6.2 / C-15.

    All fields optional: an absent requirement simply means that check is
    skipped (never invented). `accepted_document_types` and `keywords` come
    from `questions.evidence_requirement_json` (C-15).
    """

    required_period_start: date | None = None
    required_period_end: date | None = None
    required_scope: str | None = None
    accepted_document_types: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    # DEC-007: provisional MVP threshold, a product decision not a legal
    # conclusion (Main Spec §6.2).
    outdated_threshold_months: int = 24


@dataclass(frozen=True)
class EvidenceStatusResult:
    status: str
    status_reason: str
    status_findings: list[dict]


# --------------------------------------------------------------------------- #
# C-15 normalization — deterministic, exact-token only
# --------------------------------------------------------------------------- #

_NON_WORD_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WHITESPACE_RE = re.compile(r"\s+", re.UNICODE)


def normalize_tokens(text: str | None) -> frozenset[str]:
    """C-15 normalization: unicode normalize, case-fold, punctuation -> space,
    collapse whitespace, split into tokens. NO fuzzy/embedding/LLM matching
    anywhere in this module — exact token equality only.
    """
    if not text:
        return frozenset()
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = _NON_WORD_RE.sub(" ", normalized)
    normalized = _WHITESPACE_RE.sub(" ", normalized).strip()
    if not normalized:
        return frozenset()
    return frozenset(normalized.split(" "))


def _normalize_value(value: str) -> str:
    return value.strip().casefold().replace(",", "")


def _scope_key(scope_description: str | None) -> str:
    return (scope_description or "").strip().casefold()


# --------------------------------------------------------------------------- #
# Why a candidate fell short of VERIFIED
#
# Two separate things, kept in separate fields on purpose:
#
#   * the REASON — one short phrase a reviewer can act on. This is what a UI
#     shows. It says what is wrong, not which clause says so.
#   * the BASIS — the normative citation behind that reason. Preserved in the
#     finding's `basis` map so the rule is auditable, and deliberately kept out
#     of the reason phrase.
#
# They used to be one string. The citation was inlined into the phrase, so the
# only user-facing text available was a 460-character sentence carrying
# "Main Spec §17 Gate P4: AI confidence does not participate in the VERIFIED
# determination" — accurate, and useless to the person deciding what to do next.
# Splitting them loses nothing and lets a UI render a readable bullet.
# --------------------------------------------------------------------------- #

REASON_PERIOD_NOT_COVERED = "reporting period does not fully cover the required period"
REASON_SCOPE_MISMATCH = "scope does not match the required scope"
REASON_CLAIM_UNCLEAR = "evidence does not clearly support the claim"
REASON_NO_UNIT = "numerical value has no explainable unit"
REASON_NO_LOCATION = "source location is empty"
REASON_NOT_ACCEPTED = "evidence has not been accepted by a human reviewer"

#: reason phrase -> the normative clause it comes from.
REASON_BASIS: dict[str, str] = {
    REASON_NOT_ACCEPTED: (
        "An unreviewed AI-proposed candidate cannot, by itself, satisfy VERIFIED "
        "— Main Spec §17 Gate P4: AI confidence does not participate in the "
        "VERIFIED determination."
    ),
    REASON_PERIOD_NOT_COVERED: "Main Spec §6.2 VERIFIED conditions (period coverage).",
    REASON_SCOPE_MISMATCH: "Main Spec §6.2 VERIFIED conditions (scope match).",
    REASON_NO_UNIT: "Main Spec §6.2 VERIFIED conditions (explainable unit).",
    REASON_NO_LOCATION: (
        "A VERIFIED record needs a server-resolved source location "
        "(AGENTS.md §3.3 — the AI never supplies one)."
    ),
}


# --------------------------------------------------------------------------- #
# The engine
# --------------------------------------------------------------------------- #


def compute_evidence_status(
    candidates: list[EvidenceCandidate] | None = None,
    *,
    requirement: EvidenceRequirement | None = None,
    unreadable_documents: list[UnreadableDocument] | None = None,
    current_status: str | None = None,
    not_applicable_reason: str | None = None,
    reviewer_name: str | None = None,
    reference_date: date | None = None,
) -> EvidenceStatusResult:
    """Compute `evidence_status` for one question, per SPEC-AMD-005's four
    steps and the frozen precedence CONFLICTING > OUTDATED > PARTIAL >
    VERIFIED.

    `current_status` is the answer's evidence_status as currently persisted.
    If it is already `"NOT_APPLICABLE"`, this function returns that
    unchanged and does not look at any evidence at all — step 1 of
    SPEC-AMD-005 requires this engine never set or clear that status.
    """
    if current_status == "NOT_APPLICABLE":
        detail = "Marked NOT_APPLICABLE by a human reviewer; the rule engine never recomputes or clears this status."
        finding = {
            "condition": "NOT_APPLICABLE",
            "detail": detail,
            "reason": not_applicable_reason,
            "reviewer_name": reviewer_name,
        }
        reason = detail if not not_applicable_reason else f"{detail} Reason: {not_applicable_reason}"
        return EvidenceStatusResult(
            status="NOT_APPLICABLE", status_reason=reason, status_findings=[finding]
        )

    requirement = requirement or EvidenceRequirement()
    unreadable_documents = unreadable_documents or []
    reference_date = reference_date or date.today()
    candidates = candidates or []

    findings: list[dict] = []

    # Step 2: drop rejected/invalidated links (no longer live evidence), then
    # exclude unreadable/extraction-invalid evidence from the computation.
    live = [c for c in candidates if c.link_status not in ("REJECTED", "INVALIDATED")]
    excluded = [c for c in live if not c.extraction_valid]
    readable = [c for c in live if c.extraction_valid]

    for c in excluded:
        findings.append(
            {
                "condition": "EXCLUDED_UNREADABLE",
                "link_id": c.link_id,
                "detail": "Evidence excluded from the evidence-quality computation: "
                "extraction invalid/unreadable (SPEC-AMD-005 step 2).",
            }
        )

    # Step 3: evaluate the remaining readable evidence.
    #
    # Main Spec §6.2 requires "two records for the same metric, scope, and
    # period". It does not say what an *unstated* scope or period means, and
    # this engine used to treat `None` as a distinct key value -- so "unknown"
    # behaved as "different", and two records could not conflict unless both
    # spelled out matching strings. On the sample set that silently hid the
    # one real contradiction: `A-03` is tabular and names Klang plant, `C-01`
    # is prose that says only "in FY2025".
    #
    # Ruled by the repository owner on 2026-08-25: **unknown is compatible
    # with anything**. A record that does not name its site is silent, not
    # asserting a different one, and every candidate here is already an answer
    # to the same question -- which is what stands in for "same metric", as
    # the module docstring notes. A stated difference still separates them.
    #
    # This is a deliberate, recorded departure from the literal reading of
    # §6.2, made because the alternative failure is worse for this product: a
    # false CONFLICTING costs a reviewer one look, a missed one lets a
    # contradiction reach a customer. See `sample/README.md`.
    #
    # Compatibility is not transitive -- A(Klang) and B(silent) are
    # compatible, B and C(Ipoh) are compatible, A and C are not -- so this
    # cannot be a partition into groups. It is a pairwise test, which is also
    # what §6.2's "two records" describes.
    def _separated(a: EvidenceCandidate, b: EvidenceCandidate) -> bool:
        """True when something positively distinguishes these two records."""
        if a.scope_description and b.scope_description:
            if _scope_key(a.scope_description) != _scope_key(b.scope_description):
                return True
        if a.period_start and b.period_start and a.period_start != b.period_start:
            return True
        if a.period_end and b.period_end and a.period_end != b.period_end:
            return True
        return False

    measured = [c for c in readable if c.value is not None and c.value.strip()]
    conflicting_candidates: dict[str, EvidenceCandidate] = {}
    for i, first in enumerate(measured):
        for second in measured[i + 1 :]:
            if _normalize_value(first.value) == _normalize_value(second.value):
                continue
            if _separated(first, second):
                continue
            # Only the records that actually disagree are named. A silent
            # candidate sitting beside a conflict is not part of it.
            conflicting_candidates[first.link_id] = first
            conflicting_candidates[second.link_id] = second

    has_conflict = bool(conflicting_candidates)
    for c in conflicting_candidates.values():
        findings.append(
            {
                "condition": "CONFLICTING",
                "link_id": c.link_id,
                "value": c.value,
                # Carried so a summary can say "12.6 t" rather than "12.6".
                # A bare number is not a measurement.
                "unit": c.unit,
                "scope_description": c.scope_description,
                "period_start": c.period_start.isoformat() if c.period_start else None,
                "period_end": c.period_end.isoformat() if c.period_end else None,
                "detail": "Two or more records report different values and nothing "
                "distinguishes what they cover; not auto-resolved to a "
                "'more credible' one (RULING-02).",
            }
        )

    def _is_outdated(c: EvidenceCandidate) -> bool:
        if requirement.required_period_start and requirement.required_period_end:
            if c.period_end and c.period_end < requirement.required_period_start:
                return True
            if c.period_start and c.period_start > requirement.required_period_end:
                return True
            return False
        basis_date = c.source_date or c.period_end
        if basis_date is None:
            return False
        months = (reference_date.year - basis_date.year) * 12 + (
            reference_date.month - basis_date.month
        )
        return months > requirement.outdated_threshold_months

    outdated_candidates = [c for c in readable if _is_outdated(c)]
    has_outdated = bool(outdated_candidates)
    for c in outdated_candidates:
        findings.append(
            {
                "condition": "OUTDATED",
                "link_id": c.link_id,
                "source_date": c.source_date.isoformat() if c.source_date else None,
                "period_end": c.period_end.isoformat() if c.period_end else None,
                "detail": "Evidence is outside the question's required period, or "
                "(no explicit period) older than the "
                f"{requirement.outdated_threshold_months}-month provisional "
                "threshold (DEC-007).",
            }
        )

    def _partial_reasons(c: EvidenceCandidate) -> list[str]:
        reasons: list[str] = []
        if requirement.required_period_start and requirement.required_period_end:
            covers = (
                c.period_start is not None
                and c.period_end is not None
                and c.period_start <= requirement.required_period_start
                and c.period_end >= requirement.required_period_end
            )
            if not covers:
                reasons.append(REASON_PERIOD_NOT_COVERED)
        if requirement.required_scope:
            scope_ok = bool(c.scope_description) and (
                requirement.required_scope.strip().casefold()
                in c.scope_description.strip().casefold()  # type: ignore[union-attr]
            )
            if not scope_ok:
                reasons.append(REASON_SCOPE_MISMATCH)
        if not c.claim_supported or not c.claim_supported.strip():
            reasons.append(REASON_CLAIM_UNCLEAR)
        if c.value is not None and c.value.strip() and (not c.unit or not c.unit.strip()):
            reasons.append(REASON_NO_UNIT)
        if not c.source_location or not c.source_location.strip():
            reasons.append(REASON_NO_LOCATION)
        if c.link_status != "ACCEPTED":
            reasons.append(REASON_NOT_ACCEPTED)
        return reasons

    verified_candidates: list[EvidenceCandidate] = []
    for c in readable:
        reasons = _partial_reasons(c)
        if reasons:
            finding: dict = {
                "condition": "PARTIAL",
                "link_id": c.link_id,
                "reasons": reasons,
                "detail": "Coverage exists but is incomplete: " + "; ".join(reasons) + ".",
            }
            # The citations stay on the finding so the rule remains auditable,
            # without being inlined into the reason phrases above.
            basis = {r: REASON_BASIS[r] for r in reasons if r in REASON_BASIS}
            if basis:
                finding["basis"] = basis
            findings.append(finding)
        else:
            verified_candidates.append(c)
            findings.append(
                {
                    "condition": "VERIFIED",
                    "link_id": c.link_id,
                    "detail": "Satisfies all Main Spec §6.2 VERIFIED conditions.",
                }
            )

    if has_conflict:
        status = "CONFLICTING"
    elif has_outdated:
        status = "OUTDATED"
    elif verified_candidates:
        status = "VERIFIED"
    elif readable:
        status = "PARTIAL"
    else:
        # Step 4: no readable evidence at all.
        relevant = _find_relevant_unreadable(unreadable_documents, requirement)
        if relevant is not None:
            doc, keyword = relevant
            status = "NEEDS_MANUAL_REVIEW"
            findings.append(
                {
                    "condition": "NEEDS_MANUAL_REVIEW",
                    "document_id": doc.document_id,
                    "document_type": doc.document_type,
                    # Carried as its own key so a UI can name the file without
                    # having to parse it back out of `detail`.
                    "original_filename": doc.original_filename,
                    "matched_keyword": keyword,
                    "detail": f"Unreadable {doc.document_type} document "
                    f"'{doc.original_filename}' may be relevant to this question "
                    f"(C-15: exact-token match on keyword '{keyword}').",
                }
            )
        else:
            status = "MISSING"
            findings.append(
                {
                    "condition": "MISSING",
                    "detail": "No readable evidence and no relevant unreadable document "
                    "found (C-15).",
                }
            )

    return EvidenceStatusResult(
        status=status,
        status_reason=_summarize(status, findings),
        status_findings=findings,
    )


def _find_relevant_unreadable(
    unreadable_documents: list[UnreadableDocument],
    requirement: EvidenceRequirement,
) -> tuple[UnreadableDocument, str] | None:
    """C-15: an unreadable document may materially affect a question only
    when ALL three hold: processing_status == NEEDS_MANUAL_REVIEW,
    document_type is in the question's accepted_document_types, and at
    least one normalized required keyword exactly matches a token found in
    the filename or successfully extracted metadata/heading text.

    Exact-token matching only — no fuzzy matching, no embeddings, no LLM
    classification (C-15 "Normalization — deterministic").
    """
    if not requirement.keywords:
        return None
    for doc in unreadable_documents:
        if doc.processing_status != "NEEDS_MANUAL_REVIEW":
            continue
        if (
            requirement.accepted_document_types
            and doc.document_type not in requirement.accepted_document_types
        ):
            continue
        haystack = set(doc.extracted_tokens) | normalize_tokens(doc.original_filename)
        for keyword in requirement.keywords:
            keyword_tokens = normalize_tokens(keyword)
            if keyword_tokens and keyword_tokens.issubset(haystack):
                return doc, keyword
    return None


def summarize_points(
    status: str,
    findings: list[dict],
    *,
    source_labels: dict[str, str] | None = None,
) -> list[str]:
    """Short, action-oriented bullets explaining one `evidence_status`.

    The companion to `_summarize()`. That one produces `status_reason`, a prose
    sentence for the audit trail; this one produces the handful of phrases a
    reviewer actually needs to read. Neither decides the status — both only
    describe findings the engine already produced.

    Pure and stateless, taking the findings list rather than an
    `EvidenceStatusResult`, so it works equally on a freshly computed result and
    on a persisted `answers.status_findings_json`. That is what lets the API
    expose these without a new column.

    `source_labels` maps `link_id` to something a reviewer recognises, usually
    a filename. Supplied by the caller because this module is DB-free
    (BLOCKER-04) and must never look one up itself. Optional: a caller that
    cannot resolve them still gets the values, because a bullet that
    disappears is worse than a bullet without a name.
    """
    points: list[str] = []

    def add(point: str) -> None:
        if point and point not in points:
            points.append(point)

    by_condition = lambda name: [f for f in findings if f.get("condition") == name]  # noqa: E731

    if status == "NOT_APPLICABLE":
        finding = next(iter(by_condition("NOT_APPLICABLE")), None)
        reviewer = (finding or {}).get("reviewer_name")
        add(
            f"Marked not applicable by {reviewer}"
            if reviewer
            else "Marked not applicable by a human reviewer"
        )
    elif status == "CONFLICTING":
        conflicting = by_condition("CONFLICTING")
        labels = source_labels or {}

        # "12.6 vs 18.4" is two numbers with no provenance, which is the thing
        # this product exists to refuse. A reviewer's first question is which
        # document said which, and this bullet is where they read it.
        seen: list[str] = []
        for f in conflicting:
            value = f.get("value")
            if not value:
                continue
            measurement = f"{value} {f['unit']}".strip() if f.get("unit") else str(value)
            label = labels.get(f.get("link_id", ""))
            phrase = f"{label} says {measurement}" if label else measurement
            if phrase not in seen:
                seen.append(phrase)

        distinct_values = {str(f.get("value")) for f in conflicting if f.get("value")}
        if len(distinct_values) > 1 and seen:
            add("sources disagree: " + ", ".join(seen) if labels else
                "sources disagree: " + " vs ".join(seen))
        # Same correction as `_summarize`: under the 2026-08-25 ruling the pair
        # that triggers this need not share a scope at all - one of them may
        # state none. Claiming they do would assert something the evidence
        # does not say, to the one person whose job is to check that.
        add("two or more records report different values, and nothing in them says "
            "they cover different things")
        add("a human has to decide which source is right — this is never resolved automatically")
    elif status == "OUTDATED":
        add("evidence falls outside the required reporting period, or is more than 24 months old")
    elif status == "MISSING":
        add("no readable evidence is linked to this question")
    elif status == "NEEDS_MANUAL_REVIEW":
        finding = next(iter(by_condition("NEEDS_MANUAL_REVIEW")), None)
        filename = (finding or {}).get("original_filename")
        add(
            f"'{filename}' could not be read and may be relevant"
            if filename
            else "a document that could not be read may be relevant"
        )
        add("open the document and either re-upload a readable copy or link the evidence by hand")
    elif status == "PARTIAL":
        for finding in by_condition("PARTIAL"):
            for reason in finding.get("reasons", []):
                add(reason)
    # VERIFIED needs no caveat; the status already says it.

    # Applies under any status: a record the engine had to set aside is
    # something the reviewer should know about.
    excluded = by_condition("EXCLUDED_UNREADABLE")
    if excluded:
        add(
            f"{len(excluded)} evidence record(s) were set aside because their text "
            "could not be read"
        )

    return points


def _collapse_identical(details: list[str]) -> list[tuple[str, int]]:
    """Group byte-identical detail strings, keeping first-seen order.

    Only exact equality collapses. Two findings whose wording differs at all
    are kept separately, because a difference in wording here means a
    difference in the underlying reasons list — never a rephrasing.

    Returns `(detail, occurrences)` pairs so the summary can say how many
    evidence records a finding applies to instead of silently dropping the
    duplicates.
    """
    counts: dict[str, int] = {}
    for detail in details:
        counts[detail] = counts.get(detail, 0) + 1
    return list(counts.items())  # dict preserves insertion order (3.7+)


def _summarize(status: str, findings: list[dict]) -> str:
    if status == "CONFLICTING":
        n = sum(1 for f in findings if f["condition"] == "CONFLICTING")
        # Not "share the same scope and period": under the 2026-08-25 ruling a
        # record that states neither still conflicts, and saying they share a
        # scope when one of them is silent would put a claim in front of a
        # reviewer that the evidence does not support.
        return (
            f"{n} evidence record(s) report different values, and nothing in them "
            "distinguishes what they cover; all are shown rather than auto-resolved."
        )
    if status == "OUTDATED":
        return (
            "Evidence is outside the required reporting period, or "
            "(no explicit period) older than the provisional 24-month threshold "
            "(DEC-007)."
        )
    if status == "VERIFIED":
        return "At least one accepted evidence record satisfies all Main Spec §6.2 VERIFIED conditions."
    if status == "PARTIAL":
        # One PARTIAL finding is produced per readable candidate, and candidates
        # overwhelmingly fail VERIFIED for the same reason (nothing has been
        # human-accepted yet). Joining them verbatim therefore repeated one
        # identical sentence once per evidence link — 9 times, 2,327 characters,
        # for a question with 9 candidates. Collapse exact duplicates and state
        # the multiplicity instead. `status_findings` still carries one entry
        # per link with its own link_id, so SPEC-AMD-005 step 3 ("lower-priority
        # findings are never discarded") is unaffected: nothing is dropped from
        # the structured record, only from the prose summary.
        collapsed = _collapse_identical(
            [f["detail"] for f in findings if f["condition"] == "PARTIAL"]
        )
        sentences = [
            detail
            if occurrences == 1
            else f"{detail.rstrip('.')} (same finding on {occurrences} evidence records)."
            for detail, occurrences in collapsed
        ]
        return "Evidence exists but coverage is incomplete. " + " ".join(sentences)
    if status == "NEEDS_MANUAL_REVIEW":
        finding = next(f for f in findings if f["condition"] == "NEEDS_MANUAL_REVIEW")
        return finding["detail"]
    return "No evidence link found for this question, and no unreadable document was identified as relevant (C-15)."
