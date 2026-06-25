"""Concrete source adapters — importing this package self-registers them in the registry.

The registry's `_load_adapters()` imports this module lazily, so the ingestion core stays
decoupled from the concrete sources. Each submodule calls `register(...)` at import time; listing
them here is what triggers that. Add a new source = add a module + one import line.
"""
from . import eventbrite_wue, meetup, thws_fiw  # noqa: F401  (import side-effect: registration)
