"""Auth helpers — host-aware OAuth redirect_uri derivation.

We unit-test ``_derive_redirect_uri`` directly (a pure function over request headers) rather than
driving the full ``/google/login`` route: ``authorize_redirect`` would fetch Google's OpenID
metadata over the network, which the test environment must not depend on.
"""
from __future__ import annotations

from starlette.requests import Request

from app.auth import _derive_frontend_base, _derive_redirect_uri
from app.config import settings


def _request(headers: dict[str, str]) -> Request:
    scope = {
        "type": "http",
        "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
    }
    return Request(scope)


def test_redirect_uri_uses_forwarded_host():
    req = _request({"x-forwarded-host": "macbook-pro-von-lars.tail7629bb.ts.net"})
    assert (
        _derive_redirect_uri(req)
        == "https://macbook-pro-von-lars.tail7629bb.ts.net/api/auth/google/callback"
    )


def test_redirect_uri_honors_forwarded_proto():
    req = _request({"x-forwarded-host": "example.ts.net", "x-forwarded-proto": "http"})
    assert _derive_redirect_uri(req) == "http://example.ts.net/api/auth/google/callback"


def test_redirect_uri_defaults_without_forwarded_host():
    # Plain local dev (no proxy headers) → the configured localhost default, behaviour unchanged.
    assert _derive_redirect_uri(_request({})) == settings.oauth_redirect_uri


def test_frontend_base_uses_forwarded_host():
    # Post-login redirect over Tailscale lands on the same external host, not localhost.
    req = _request({"x-forwarded-host": "macbook-pro-von-lars.tail7629bb.ts.net"})
    assert _derive_frontend_base(req) == "https://macbook-pro-von-lars.tail7629bb.ts.net"


def test_frontend_base_honors_forwarded_proto():
    req = _request({"x-forwarded-host": "example.ts.net", "x-forwarded-proto": "http"})
    assert _derive_frontend_base(req) == "http://example.ts.net"


def test_frontend_base_defaults_without_forwarded_host():
    # localhost: callback hits :8000 but the frontend lives on :5173 → absolute frontend_url, not
    # a relative redirect onto the backend port.
    assert _derive_frontend_base(_request({})) == settings.frontend_url
