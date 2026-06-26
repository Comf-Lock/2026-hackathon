"""Concrete source adapters — importing this package self-registers them in the registry.

The registry's loader imports this module lazily, so the ingestion core stays decoupled from the
concrete sources. Each submodule calls ``register(...)`` at import time; listing them here is what
triggers that. Add a new source = add a module + one import line below.
"""
# master adapters (Würzburg/Mainfranken IT-native + broad): eventbrite, meetup, THWS-FIW
from . import eventbrite_wue, meetup, thws_fiw  # noqa: F401  (import side-effect: registration)
# agent-3 adapters (generic ICS calendars + FRIZZ RSS)
from . import ics, rss  # noqa: F401  (import side-effect: registration)
# AI Week Mainfranken (festival per-session program, JSON export — single events found nowhere else)
from . import aiweek  # noqa: F401  (import side-effect: registration)
# THWS university-wide calendar (all faculties/both campuses; reuses the FIW accordion parser)
from . import thws  # noqa: F401  (import side-effect: registration)
