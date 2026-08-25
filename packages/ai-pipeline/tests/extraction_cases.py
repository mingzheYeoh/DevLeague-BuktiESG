"""The acceptance set for value extraction.

Fixed here, before a model is wired up, so the bar is set by what the product
needs rather than by what the first model that gets tried happens to manage.
Each case is real text from `sample/evidence`, and each exists because a
measured deterministic attempt got it wrong.

Nothing in this module calls a model. `test_extract.py` uses it to check the
cases are well formed; the adapter's own suite runs them against a live
provider once one is configured, and skips when none is.

The three deterministic attempts, measured across all 231 links in the sample
case:

  every number in the chunk        20 of 20 questions flagged CONFLICTING
  numbers on a question-matched line   20 of 20
  number immediately followed by a unit the question asks for
                                    1 of 20, and the wrong one

So the bar is not "extracts something". It is these three, together: the two
the last attempt missed, and the one it wrongly flagged.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    name: str
    why: str
    chunks: tuple[str, ...]
    #: Expected `value` per chunk. `None` means the chunk carries no
    #: measurement, which is an answer, not an abstention.
    values: tuple[str | None, ...]
    #: Expected `unit` per chunk, same positions.
    units: tuple[str | None, ...]


#: The unit lives in a column header, in a different chunk from the value it
#: governs. Adjacency cannot reach it: the value chunk contains no unit at all.
#: This is the harder half of the real contradiction in the sample set.
TABULAR_UNIT = Case(
    name="tabular unit inherited from a header",
    why=(
        "A-03 is a spreadsheet. The header row and the data rows are separate "
        "chunks, so the unit that governs 12.6 is not in the chunk that holds "
        "it. Every deterministic attempt missed this."
    ),
    chunks=(
        "Waste code / line | Description | Metric tonnes | Year | Scope",
        "Total scheduled waste | All codes above, FY2025 | 12.6 | 2025 | Klang plant",
        "Total waste generated | Hazardous plus non-hazardous | 214.7 | 2025 | Klang plant",
    ),
    values=(None, "12.6", "214.7"),
    units=(None, "t", "t"),
)

#: An adjective between the number and its unit. Cheap to patch with a regex,
#: kept because the pair with TABULAR_UNIT is what makes the contradiction
#: visible: 12.6 t against 18.4 t, same site, same year.
ADJECTIVE_BEFORE_UNIT = Case(
    name="unit separated from its number by an adjective",
    why="C-01 writes '18.4 metric tonnes', so a unit-adjacency rule does not fire.",
    chunks=(
        "Total scheduled waste despatched in FY2025: 18.4 metric tonnes.",
        "Total waste generated in FY2025: 229.5 metric tonnes.",
    ),
    values=("18.4", "229.5"),
    units=("t", "t"),
)

#: The reverse test, and the one that matters most. These four figures share a
#: unit and a subject and are NOT in conflict: a month, a running subtotal, an
#: annual total and a three-site total. The strictest deterministic rule
#: flagged exactly this question. A model that "extracts well" but cannot
#: separate them is worse than no extraction, because it manufactures a
#: contradiction a reviewer would then have to disprove.
GRANULARITY_NOT_CONFLICT = Case(
    name="different granularities are not a contradiction",
    why=(
        "Q-E-04 was the one question the unit-anchored rule flagged, on a "
        "month, a subtotal, an annual total and a group total. Telling them "
        "apart needs the period, not a better number-finder."
    ),
    chunks=(
        "January 2025 | Klang plant | 148,600 kWh",
        "FY2025 total | Klang plant | 1,847,300 kWh",
        "FY2025 total | Klang, Shah Alam and Ipoh combined | 4,912,600 kWh",
    ),
    values=("148600", "1847300", "4912600"),
    units=("kWh", "kWh", "kWh"),
)

ACCEPTANCE_CASES: tuple[Case, ...] = (
    TABULAR_UNIT,
    ADJECTIVE_BEFORE_UNIT,
    GRANULARITY_NOT_CONFLICT,
)
