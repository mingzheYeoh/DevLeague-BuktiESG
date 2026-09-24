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

import logging
from typing import Protocol

import httpx

from ai_pipeline import (
    Extracted, ExtractionRefused, RelevanceAssessment,
    build_extraction_prompt, build_relevance_prompt, parse_extraction, parse_relevance,
)

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-6-luna"

# Extraction runs in `worker.py`, not in the upload request, so nothing is
# waiting on this. A timeout yields empty measurements without losing evidence.
REQUEST_TIMEOUT_SECONDS = 180.0

# Chunks per request. A malformed response discards its batch, so keep it small.
BATCH_SIZE = 20


class Extractor(Protocol):
    """One measurement per chunk, in the order given.

    Always returns exactly `len(chunk_texts)` results. Callers match by
    position, so a shorter list would attach results to the wrong chunks.
    """

    def extract(self, chunk_texts: list[str]) -> list[Extracted]: ...

    def assess_matches(
        self, pairs: list[tuple[str, str]]
    ) -> list[RelevanceAssessment | None]: ...


class NullExtractor:
    """No provider configured: every chunk yields no measurement.

    Not an error and not a warning. An absent value is the state the rule
    engine has always seen, and it reads it correctly - a question with no
    comparable values is PARTIAL, which is exactly what it was before.
    """

    def extract(self, chunk_texts: list[str]) -> list[Extracted]:
        return [Extracted() for _ in chunk_texts]

    def assess_matches(
        self, pairs: list[tuple[str, str]]
    ) -> list[RelevanceAssessment | None]:
        return [None for _ in pairs]


class OpenRouterExtractor:
    """Extraction through OpenRouter's chat completions API."""

    def __init__(
        self,
        api_key: str,
        *,
        model: str = OPENROUTER_MODEL,
        base_url: str = OPENROUTER_BASE_URL,
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
                "reasoning_effort": "none",
                "response_format": {"type": "json_object"},
                "provider": {"data_collection": "deny", "require_parameters": True},
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

    def assess_matches(
        self, pairs: list[tuple[str, str]]
    ) -> list[RelevanceAssessment | None]:
        results: list[RelevanceAssessment | None] = []
        for start in range(0, len(pairs), BATCH_SIZE):
            batch = pairs[start : start + BATCH_SIZE]
            system, user = build_relevance_prompt(batch)
            try:
                results.extend(parse_relevance(self._post(system, user), pairs=batch))
            except Exception:
                logger.warning("relevance provider failed for a batch of %d", len(batch), exc_info=True)
                results.extend([None] * len(batch))
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

    A key selects `OpenRouterExtractor`; no key selects `NullExtractor`.
    When enabled, extracted document text leaves this deployment. Only use
    synthetic documents for this demo; never put a credential in source code.
    """
    key = getattr(settings, "openrouter_api_key", None)
    if not key or not key.strip():
        return NullExtractor()

    logger.warning(
        "OPENROUTER_API_KEY is set: document chunk text will be sent to "
        "openrouter.ai and its selected model provider. Use synthetic documents only."
    )
    return OpenRouterExtractor(api_key=key.strip())
