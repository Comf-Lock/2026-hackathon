"""The source-agnostic adapter contract.

Every source — scraper, ICS feed, API — is a SourceAdapter that yields RawEventRecord for a
given GeoScope. The ingestion core (core.py) never knows the concrete source; it only iterates
adapters, filters their records, and upserts. fetch() is async because adapters do network I/O.

`broad` marks calendars that mix non-IT / non-regional events (FRIZZ, Stadt Würzburg, BayStartUP):
the core applies the keyword gate to those. IT-native sources (THWS-FIW, tech Meetups) leave it
False so their events are not dropped just for lacking a keyword in the title.
"""
from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .types import GeoScope, RawEventRecord


@runtime_checkable
class SourceAdapter(Protocol):
    name: str
    broad: bool

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]: ...


class BaseAdapter:
    """Optional convenience base so concrete adapters get sane defaults for the contract attrs."""

    name: str = "base"
    broad: bool = False

    async def fetch(self, scope: GeoScope) -> Sequence[RawEventRecord]:  # pragma: no cover
        raise NotImplementedError
