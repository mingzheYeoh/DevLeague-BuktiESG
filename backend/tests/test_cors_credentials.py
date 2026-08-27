"""The browser will not send the session cookie unless the server says it may.

`Access-Control-Allow-Credentials: true` and a concrete origin are both
required, and a wildcard origin is forbidden in a credentialed exchange. Those
are browser rules, invisible to every other test in this suite: pytest sends
the cookie regardless of what the headers say. Without this test the first sign
that CORS is wrong is a browser silently dropping the cookie.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

ALLOWED_ORIGIN = "http://localhost:3000"


def test_preflight_allows_credentials():
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/cases",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.status_code == 200
    assert response.headers["access-control-allow-credentials"] == "true"


def test_preflight_echoes_the_origin_and_never_a_wildcard():
    """A wildcard origin is rejected by the browser when credentials are on.

    Asserted separately from the flag above because these fail for different
    reasons: the flag missing is a forgotten setting, a wildcard here is a
    `cors_allow_origins` that was widened to `["*"]` by someone who did not
    know the two are incompatible.
    """
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/cases",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["access-control-allow-origin"] != "*"


def test_an_unlisted_origin_is_not_granted_credentials():
    """Credentials plus an open origin list is the whole cookie given away."""
    with TestClient(app) as client:
        response = client.options(
            "/api/v1/cases",
            headers={
                "Origin": "https://evil.example",
                "Access-Control-Request-Method": "GET",
            },
        )
    assert response.headers.get("access-control-allow-origin") != "https://evil.example"


def test_the_configured_origins_are_still_only_local():
    """A guard, not a preference. If this list grows to a public hostname, the
    session cookie becomes reachable from that hostname, and that is a decision
    with an owner - not an edit."""
    assert settings.cors_allow_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
