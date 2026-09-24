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

from app.services.extractor import NullExtractor, build_extractor


def test_with_no_key_configured_the_null_extractor_is_used():
    from app.config import Settings

    settings = Settings(openrouter_api_key=None)
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


def test_a_configured_key_selects_the_openrouter_extractor(caplog):
    """A key selects the remote provider and logs where document text goes."""
    from app.config import Settings
    from app.services.extractor import OpenRouterExtractor

    settings = Settings(openrouter_api_key="sk-not-a-real-key")

    with caplog.at_level("WARNING"):
        extractor = build_extractor(settings)

    assert isinstance(extractor, OpenRouterExtractor)
    assert any("openrouter.ai" in r.message for r in caplog.records), caplog.text


def test_no_key_stays_silent(caplog):
    """The quiet half. A local run without a provider is the normal case, so it
    must not warn - otherwise the warning that matters gets ignored."""
    from app.config import Settings

    with caplog.at_level("WARNING"):
        extractor = build_extractor(Settings(openrouter_api_key=None))

    assert isinstance(extractor, NullExtractor)
    assert caplog.records == []


def test_a_provider_failure_degrades_to_no_values_rather_than_failing_upload(monkeypatch):
    """Extraction is an enrichment. A provider that is down, rate-limited or
    slow must never stop a document being stored and indexed - losing the
    evidence is a real failure, missing a value is not."""
    from app.services.extractor import OpenRouterExtractor

    extractor = OpenRouterExtractor(api_key="sk-not-a-real-key")

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
    from app.services.extractor import OpenRouterExtractor

    extractor = OpenRouterExtractor(api_key="sk-not-a-real-key")
    monkeypatch.setattr(
        extractor,
        "_post",
        lambda *a, **k: '{"results": [{"value": "12.6", "evidence_status": "VERIFIED"}]}',
    )

    results = extractor.extract(["Total scheduled waste: 12.6 tonnes."])
    assert results[0].value is None


def test_openrouter_request_uses_luna_json_mode(monkeypatch):
    from app.services.extractor import OpenRouterExtractor

    seen = {}

    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": '{"results": [{"value": "12.6"}]}'}}]}

    def fake_post(url, **kwargs):
        seen.update(url=url, **kwargs)
        return Response()

    monkeypatch.setattr("app.services.extractor.httpx.post", fake_post)
    result = OpenRouterExtractor(api_key="test-key").extract(["12.6 tonnes of waste."])

    assert result[0].value == "12.6"
    assert seen["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer test-key"
    assert seen["json"]["model"] == "openai/gpt-6-luna"
    assert seen["json"]["reasoning_effort"] == "none"
    assert seen["json"]["response_format"] == {"type": "json_object"}
    assert seen["json"]["provider"] == {"data_collection": "deny", "require_parameters": True}
    assert "store" not in seen["json"]
    assert "temperature" not in seen["json"]


def test_relevance_response_must_quote_the_stored_source(monkeypatch):
    from app.services.extractor import OpenRouterExtractor

    extractor = OpenRouterExtractor(api_key="test-key")
    pair = ("How many staff trained?", "254 staff completed training.")
    monkeypatch.setattr(
        extractor,
        "_post",
        lambda *args: '{"results":[{"verdict":"SUPPORTS","quote":"254 staff completed training.","missing":null}]}',
    )
    assert extractor.assess_matches([pair])[0].verdict == "SUPPORTS"

    monkeypatch.setattr(
        extractor,
        "_post",
        lambda *args: '{"results":[{"verdict":"SUPPORTS","quote":"999 staff completed training.","missing":null}]}',
    )
    assert extractor.assess_matches([pair]) == [None]
