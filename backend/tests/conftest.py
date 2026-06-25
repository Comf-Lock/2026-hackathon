"""Shared test helpers: locate the stored HTML/JSON fixtures.

All adapter parsing is tested against these captured pages so the suite never touches the live
network (sources are bot-shy and change over time). Fixtures were captured 2026-06-25.
"""
from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixture_text():
    def _read(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")

    return _read
