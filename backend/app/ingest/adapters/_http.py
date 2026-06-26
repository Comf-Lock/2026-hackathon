"""Back-compat shim — the shared HTTP layer now lives in ``app.ingest.http``.

This module used to define its own User-Agent/timeout/fetch_text; that was one of five drifting
copies. It now re-exports the single source of truth so existing importers (the static scrapers and
the ingestion smoke test, which monkeypatches ``_http.fetch_text``) keep working unchanged.
"""
from __future__ import annotations

from ..http import HEADERS as DEFAULT_HEADERS  # noqa: F401  (back-compat alias)
from ..http import TIMEOUT as DEFAULT_TIMEOUT  # noqa: F401  (back-compat alias)
from ..http import client, fetch_bytes, fetch_text  # noqa: F401  (re-export)
