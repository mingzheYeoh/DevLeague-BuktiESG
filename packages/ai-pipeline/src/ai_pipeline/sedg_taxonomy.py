"""SEDG (Simplified ESG Disclosure Guide) topic/disclosure reference data.

**Honesty caveat — read before trusting this file (Main Spec §17 Phase 3
"Before Starting": "Machine-readable SEDG Topic/Disclosure data").**

The real "Capital Markets Malaysia SEDG v2" document (3 pillars, 15 topics,
38 disclosures, per README.md's "Standards Referenced") is **not present in
this repository**. Nobody on this build has the actual published standard to
transcribe from. What follows is a **working, representative taxonomy** built
to the right *shape* (pillar -> topic -> disclosure -> keywords) and roughly
the right *size* (3 pillars, 15 topics, 38 disclosures) so the mapping
function below has something structurally correct to run against.

It is:
- NOT a verified transcription of the real SEDG v2 standard;
- NOT authoritative for actual SEDG compliance reporting;
- a reasonable placeholder until someone supplies the real document, at
  which point this file should be regenerated from it (topic codes,
  disclosure codes, and names would very likely change).

Every question-to-SEDG mapping produced from this data is, transitively, a
draft recommendation for human review — never a verdict (AGENTS.md §3.2).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SedgDisclosure:
    code: str
    name: str
    # Lowercase keyword/phrase fragments. Substring-matched against tokenized
    # question text by ai_pipeline.mapping.map_question_to_sedg. Deliberately
    # simple (no stemming/synonyms) to stay consistent with the keyword-first
    # philosophy used across this package (BLOCKER-06).
    keywords: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SedgTopic:
    code: str
    name: str
    pillar: str  # "E" | "S" | "G"
    disclosures: tuple[SedgDisclosure, ...]


# --------------------------------------------------------------------------- #
# Environmental (E) — 5 topics, 13 disclosures
# --------------------------------------------------------------------------- #

_E_TOPICS = (
    SedgTopic(
        code="E1",
        name="Energy & Emissions",
        pillar="E",
        disclosures=(
            SedgDisclosure(
                "E1.1", "GHG Emissions (Scope 1 & 2)",
                ("ghg", "greenhouse gas", "scope 1", "scope 2", "carbon emissions", "co2"),
            ),
            SedgDisclosure(
                "E1.2", "Energy Consumption",
                ("energy consumption", "electricity use", "fuel consumption", "kwh", "energy usage"),
            ),
            SedgDisclosure(
                "E1.3", "Emissions Intensity",
                ("emissions intensity", "carbon intensity", "emissions per unit", "per revenue"),
            ),
        ),
    ),
    SedgTopic(
        code="E2",
        name="Water Management",
        pillar="E",
        disclosures=(
            SedgDisclosure(
                "E2.1", "Water Withdrawal",
                ("water withdrawal", "water consumption", "water use", "water usage", "water source"),
            ),
            SedgDisclosure(
                "E2.2", "Water Discharge & Management",
                ("water discharge", "wastewater", "effluent discharge", "water treatment"),
            ),
        ),
    ),
    SedgTopic(
        code="E3",
        name="Waste & Effluents",
        pillar="E",
        disclosures=(
            SedgDisclosure(
                "E3.1", "Waste Generated",
                ("waste generated", "total waste", "solid waste", "waste production"),
            ),
            SedgDisclosure(
                "E3.2", "Waste Diverted from Disposal",
                ("recycl", "waste diverted", "waste recovery", "reuse", "composting"),
            ),
            SedgDisclosure(
                "E3.3", "Hazardous Waste",
                ("hazardous waste", "scheduled waste", "toxic waste", "chemical disposal"),
            ),
        ),
    ),
    SedgTopic(
        code="E4",
        name="Biodiversity",
        pillar="E",
        disclosures=(
            SedgDisclosure(
                "E4.1", "Biodiversity Impact Assessment",
                ("biodiversity", "habitat", "ecosystem impact", "land use impact"),
            ),
            SedgDisclosure(
                "E4.2", "Protected Area Proximity",
                ("protected area", "conservation area", "nature reserve", "sensitive habitat"),
            ),
        ),
    ),
    SedgTopic(
        code="E5",
        name="Climate Risk & Transition",
        pillar="E",
        disclosures=(
            SedgDisclosure(
                "E5.1", "Climate Risk Assessment",
                ("climate risk", "climate scenario", "tcfd", "physical risk", "transition risk"),
            ),
            SedgDisclosure(
                "E5.2", "Climate Transition Plan",
                ("transition plan", "net zero", "decarbonisation", "decarbonization", "climate target"),
            ),
            SedgDisclosure(
                "E5.3", "Renewable Energy Use",
                ("renewable energy", "solar", "green energy", "clean energy"),
            ),
        ),
    ),
)

# --------------------------------------------------------------------------- #
# Social (S) — 6 topics, 16 disclosures
# --------------------------------------------------------------------------- #

_S_TOPICS = (
    SedgTopic(
        code="S1",
        name="Workforce Profile",
        pillar="S",
        disclosures=(
            SedgDisclosure(
                "S1.1", "Total Workforce Profile",
                ("total employees", "headcount", "workforce size", "number of employees"),
            ),
            SedgDisclosure(
                "S1.2", "New Hires & Turnover",
                ("new hires", "employee turnover", "attrition rate", "resignation rate"),
            ),
            SedgDisclosure(
                "S1.3", "Employment Type Breakdown",
                ("full-time", "part-time", "contract employees", "permanent staff", "temporary staff"),
            ),
            SedgDisclosure(
                "S1.4", "Employee Benefits",
                ("employee benefits", "parental leave", "insurance coverage", "retirement benefits"),
            ),
        ),
    ),
    SedgTopic(
        code="S2",
        name="Occupational Safety & Health",
        pillar="S",
        disclosures=(
            SedgDisclosure(
                "S2.1", "Work-related Injuries",
                ("workplace injury", "lost time injury", "ltifr", "accident rate", "work-related injury"),
            ),
            SedgDisclosure(
                "S2.2", "OSH Management System",
                ("osh management", "safety management system", "iso 45001", "health and safety policy"),
            ),
            SedgDisclosure(
                "S2.3", "Fatalities",
                ("fatalit", "workplace death", "occupational death"),
            ),
        ),
    ),
    SedgTopic(
        code="S3",
        name="Training & Development",
        pillar="S",
        disclosures=(
            SedgDisclosure(
                "S3.1", "Average Training Hours",
                ("training hours", "hours of training", "average training"),
            ),
            SedgDisclosure(
                "S3.2", "Training Programs",
                ("training program", "upskilling", "reskilling", "capacity building", "learning program"),
            ),
        ),
    ),
    SedgTopic(
        code="S4",
        name="Diversity & Equal Opportunity",
        pillar="S",
        disclosures=(
            SedgDisclosure(
                "S4.1", "Gender Diversity",
                ("gender diversity", "women in management", "female representation", "gender balance"),
            ),
            SedgDisclosure(
                "S4.2", "Pay Equity",
                ("pay equity", "gender pay gap", "equal pay", "salary parity"),
            ),
        ),
    ),
    SedgTopic(
        code="S5",
        name="Community Engagement",
        pillar="S",
        disclosures=(
            SedgDisclosure(
                "S5.1", "Community Investment",
                ("community investment", "csr spending", "community program", "philanthropy", "donation"),
            ),
            SedgDisclosure(
                "S5.2", "Local Procurement",
                ("local procurement", "local supplier", "local sourcing", "local content"),
            ),
        ),
    ),
    SedgTopic(
        code="S6",
        name="Human Rights & Supply Chain Labour",
        pillar="S",
        disclosures=(
            SedgDisclosure(
                "S6.1", "Supplier Labour Standards",
                ("supplier code of conduct", "supply chain labour", "labor standards", "supplier audit"),
            ),
            SedgDisclosure(
                "S6.2", "Child & Forced Labour Policy",
                ("child labour", "child labor", "forced labour", "forced labor", "modern slavery"),
            ),
            SedgDisclosure(
                "S6.3", "Grievance Mechanism",
                ("grievance mechanism", "whistleblowing channel", "complaint mechanism", "worker grievance"),
            ),
        ),
    ),
)

# --------------------------------------------------------------------------- #
# Governance (G) — 4 topics, 9 disclosures
# --------------------------------------------------------------------------- #

_G_TOPICS = (
    SedgTopic(
        code="G1",
        name="Board Composition",
        pillar="G",
        disclosures=(
            SedgDisclosure(
                "G1.1", "Board Independence",
                ("board independence", "independent director", "board composition"),
            ),
            SedgDisclosure(
                "G1.2", "Board Diversity",
                ("board diversity", "women on board", "female director"),
            ),
        ),
    ),
    SedgTopic(
        code="G2",
        name="Ethics & Anti-Corruption",
        pillar="G",
        disclosures=(
            SedgDisclosure(
                "G2.1", "Anti-Corruption Policy",
                ("anti-corruption", "anti-bribery", "code of ethics", "corruption policy"),
            ),
            SedgDisclosure(
                "G2.2", "Whistleblowing Mechanism",
                ("whistleblowing policy", "whistleblower", "reporting hotline"),
            ),
            SedgDisclosure(
                "G2.3", "Incidents of Corruption",
                ("corruption incident", "bribery case", "fraud incident", "corruption case"),
            ),
        ),
    ),
    SedgTopic(
        code="G3",
        name="Risk Management",
        pillar="G",
        disclosures=(
            SedgDisclosure(
                "G3.1", "Enterprise Risk Management",
                ("enterprise risk management", "risk management framework", "erm"),
            ),
            SedgDisclosure(
                "G3.2", "Internal Audit",
                ("internal audit", "audit committee", "internal control"),
            ),
        ),
    ),
    SedgTopic(
        code="G4",
        name="Data Privacy & Cybersecurity",
        pillar="G",
        disclosures=(
            SedgDisclosure(
                "G4.1", "Data Breach Disclosure",
                ("data breach", "personal data breach", "data leak"),
            ),
            SedgDisclosure(
                "G4.2", "Cybersecurity Governance",
                ("cybersecurity", "cyber security", "information security policy", "it security governance"),
            ),
        ),
    ),
)

SEDG_TAXONOMY: tuple[SedgTopic, ...] = _E_TOPICS + _S_TOPICS + _G_TOPICS

TOPIC_COUNT = len(SEDG_TAXONOMY)
DISCLOSURE_COUNT = sum(len(t.disclosures) for t in SEDG_TAXONOMY)
