"""Concrete source adapters.

Importing this package self-registers every adapter (each module calls ``register()`` at import
time). The registry imports this package lazily, so the ingestion core never depends on a concrete
source module. Add a new source by creating a module here and importing it below.
"""
from . import ics, rss  # noqa: F401  (import side-effect: registration)
