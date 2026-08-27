"""The adapter that carries chunks to a provider, and the fallback when none
is configured.

`ai_pipeline.extract` builds the request and validates the response; this is
the only place that holds an HTTP client or a credential.

The fallback matters more than the adapter. With no key configured the system
must behave exactly as it did before extraction existed - not degrade, not
warn on every upload, not fail. That is what makes introducing a model
reversible, and it is what lets CI run this code path without a credential or
a bill.
"""

from __future__ import annotations

import pytest

from app.services.extractor import NullExtractor, build_extractor


def test_with_no_key_configured_the_null_extractor_is_used(monkeypatch):
    from app.config import Settings

    settings = Settings(deepseek_api_key=None)
    assert isinstance(build_extractor(settings), NullExtractor)


def test_the_null_extractor_returns_one_empty_result_per_chunk():
    """One per chunk, not an empty list. Callers index by position, so a
    shorter list would silently attach the wrong result to the wrong chunk -
    the same failure the length check in `parse_extraction` exists to stop."""
    results = NullExtractor().extract(["a", "b", "c"])

    assert len(results) == 3
    assert all(r.value is None and r.unit is None for r in results)


def test_the_null_extractor_accepts_an_empty_batch():
    assert NullExtractor().extract([]) == []


def test_a_configured_key_selects_the_deepseek_extractor(caplog):
    """A key means chunk text leaves the machine, and the log says so.

    This assertion has now been written both ways. It selected DeepSeek; then
    the owner ruled that document text may not reach a provider outside
    Malaysia and it asserted the opposite; then the owner reversed that for the
    demo. The test is not flip-flopping - it tracks a governance decision that
    genuinely changed twice, and each version was correct while it stood.

    What is pinned alongside the type is the warning. The condition attached to
    the reversal - no real customer document while the key is set - is not
    something code can check, so the least this can do is refuse to be quiet
    about the state. A silent DeepSeekExtractor and a silent NullExtractor look
    identical from outside, and the difference is whether documents are leaving
    the country.
    """
    from app.config import Settings
    from app.services.extractor import DeepSeekExtractor

    settings = Settings(deepseek_api_key="sk-not-a-real-key")

    with caplog.at_level("WARNING"):
        extractor = build_extractor(settings)

    assert isinstance(extractor, DeepSeekExtractor)
    assert any("outside Malaysia" in r.message for r in caplog.records), caplog.text


def test_no_key_stays_silent(caplog):
    """The quiet half. A local run without a provider is the normal case, so it
    must not warn - otherwise the warning that matters gets ignored."""
    from app.config import Settings

    with caplog.at_level("WARNING"):
        extractor = build_extractor(Settings(deepseek_api_key=None))

    assert isinstance(extractor, NullExtractor)
    assert caplog.records == []


def test_a_provider_failure_degrades_to_no_values_rather_than_failing_upload(monkeypatch):
    """Extraction is an enrichment. A provider that is down, rate-limited or
    slow must never stop a document being stored and indexed - losing the
    evidence is a real failure, missing a value is not."""
    from app.services.extractor import DeepSeekExtractor

    extractor = DeepSeekExtractor(api_key="sk-not-a-real-key")

    def explode(*_args, **_kwargs):
        raise TimeoutError("provider did not respond")

    monkeypatch.setattr(extractor, "_post", explode)
    results = extractor.extract(["Total scheduled waste: 12.6 tonnes."])

    assert len(results) == 1
    assert results[0].value is None


def test_a_response_breaking_the_contract_degrades_the_same_way(monkeypatch):
    """A model returning a verdict field is refused by `parse_extraction`. The
    adapter must treat that as "no values", never as a reason to fail the
    upload, and never by using the response anyway."""
    from app.services.extractor import DeepSeekExtractor

    extractor = DeepSeekExtractor(api_key="sk-not-a-real-key")
    monkeypatch.setattr(
        extractor,
        "_post",
        lambda *a, **k: '{"results": [{"value": "12.6", "evidence_status": "VERIFIED"}]}',
    )

    results = extractor.extract(["Total scheduled waste: 12.6 tonnes."])
    assert results[0].value is None
