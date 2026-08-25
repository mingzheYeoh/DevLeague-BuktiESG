"""Carry document chunks to a model, and survive it not answering.

The only module in this codebase that holds an HTTP client and a credential
for a model provider. `ai_pipeline.extract` builds the request and validates
the response; that package is declared pure (no DB, no HTTP, no credentials)
and this split is what keeps it so.

Extraction is an enrichment, never a precondition. A provider that is down,
rate-limited, slow, or answering outside its contract must leave the upload
exactly as it would have been without extraction at all: the document stored,
the chunks indexed, the values absent. Losing evidence is a real failure;
missing a value is a gap the reviewer can already see and act on.

That is also what makes `NullExtractor` the important half. With no key
configured the system behaves precisely as it did before any of this existed,
which is what makes introducing a model reversible and what lets CI exercise
this path with no credential and no bill.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

import httpx

from ai_pipeline import Extracted, ExtractionRefused, build_extraction_prompt, parse_extraction

logger = logging.getLogger(__name__)

# DeepSeek's API is OpenAI-shaped, so this is a chat completion with a forced
# JSON response, not a bespoke protocol.
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-v4-pro"

# Extraction runs in `worker.py`, not in the upload request, so nothing is
# waiting on this. The ceiling is generous because the measured cost of
# expiring is a batch of nulls that will not be retried; a batch of 20 chunks
# has been seen to take over a minute.
REQUEST_TIMEOUT_SECONDS = 180.0

# Chunks per request. Batching amortises the ~400-token instruction prefix,
# which is the whole cost lever: it repeats verbatim, so it caches. Kept small
# because one malformed response discards the whole batch - a bigger batch
# means more work lost when that happens.
BATCH_SIZE = 20


class Extractor(Protocol):
    """One measurement per chunk, in the order given.

    Always returns exactly `len(chunk_texts)` results. Callers match by
    position, so a shorter list would attach results to the wrong chunks.
    """

    def extract(self, chunk_texts: list[str]) -> list[Extracted]: ...


class NullExtractor:
    """No provider configured: every chunk yields no measurement.

    Not an error and not a warning. An absent value is the state the rule
    engine has always seen, and it reads it correctly - a question with no
    comparable values is PARTIAL, which is exactly what it was before.
    """

    def extract(self, chunk_texts: list[str]) -> list[Extracted]:
        return [Extracted() for _ in chunk_texts]


class DeepSeekExtractor:
    """Extraction through DeepSeek's chat completions API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = DEEPSEEK_MODEL,
        base_url: str = DEEPSEEK_BASE_URL,
        timeout: float = REQUEST_TIMEOUT_SECONDS,
    ) -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _post(self, system: str, user: str) -> str:
        """The single network call. Isolated so tests can replace it without a
        transport layer, and so every failure mode below is reachable."""
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system},
                    # Document text travels only here. It is never concatenated
                    # into the system message, so no wording inside a document
                    # can join the instructions (AGENTS.md 3.4 / TB-3).
                    {"role": "user", "content": user},
                ],
                # Extraction, not generation. This reduces variation; it does
                # not remove it. Two live runs over identical input returned
                # the same numbers but different `scope` and `period` - once
                # inferring "Klang plant" and FY2025 for a chunk that names
                # neither, once honestly leaving both null. The second answer
                # is the better one, which is exactly why this cannot be
                # treated as a guarantee.
                #
                # Anything that depends on two independent extractions
                # agreeing on a *string* is therefore unsafe. Conflict
                # grouping does, and that is a known open problem, not
                # something temperature settles.
                "temperature": 0,
                "response_format": {"type": "json_object"},
            },
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]

    def extract(self, chunk_texts: list[str]) -> list[Extracted]:
        results: list[Extracted] = []
        for start in range(0, len(chunk_texts), BATCH_SIZE):
            batch = chunk_texts[start : start + BATCH_SIZE]
            results.extend(self._extract_batch(batch))
        return results

    def _extract_batch(self, batch: list[str]) -> list[Extracted]:
        if not batch:
            return []
        system, user = build_extraction_prompt(batch)
        try:
            raw = self._post(system, user)
        except Exception:
            # Deliberately broad. Every failure here - timeout, connection
            # refused, 401, 429, a malformed envelope - has the same correct
            # answer: no values for this batch, and the upload proceeds. A
            # narrower catch would let one unforeseen error class turn a
            # document upload into a 500.
            logger.warning("extraction provider failed for a batch of %d", len(batch), exc_info=True)
            return [Extracted() for _ in batch]

        try:
            return parse_extraction(raw, expected=len(batch))
        except ExtractionRefused as exc:
            # The response is discarded whole rather than partially used. A
            # model returning a verdict field or the wrong number of results
            # is not following the contract, and taking the parts that look
            # right would be trusting a source that has just proved unreliable.
            logger.warning("extraction response refused: %s", exc)
            return [Extracted() for _ in batch]


def build_extractor(settings) -> Extractor:
    """Pick an extractor from configuration.

    Absence of a key is a supported configuration, not a misconfiguration:
    the fallback is silent because a local run without a provider is the
    normal case, and a warning on every upload would train people to ignore
    warnings.
    """
    key = getattr(settings, "deepseek_api_key", None)
    if not key or not key.strip():
        return NullExtractor()
    return DeepSeekExtractor(api_key=key.strip())
