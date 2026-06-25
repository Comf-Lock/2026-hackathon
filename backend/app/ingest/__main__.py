"""CLI entrypoint for the ingestion run: ``python -m app.ingest``.

Examples:
    python -m app.ingest --dry-run                 # all sources, no DB write
    python -m app.ingest --source meetup_wue_data  # one source, persisted
    python -m app.ingest --radius-km 80 --center 49.79,9.95

``--dry-run`` runs the full pipeline (live fetch → filter → upsert) against a throwaway in-memory
SQLite database, so the report still shows realistic found/kept/new counts while the configured
database is never touched. Without ``--dry-run`` events are persisted to ``DATABASE_URL`` and the
``(source_adapter, external_id)`` upsert key keeps re-runs from duplicating.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from sqlmodel import Session, SQLModel, create_engine

from ..config import settings
from .core import IngestionReport, default_scope, run_ingestion
from .types import GeoScope


def _build_scope(args: argparse.Namespace) -> GeoScope:
    """Start from the configured default scope, then apply CLI overrides."""
    scope = default_scope()
    if args.radius_km is not None:
        scope.radius_km = args.radius_km
    if args.center:
        parts = [p.strip() for p in args.center.split(",")]
        if len(parts) == 2:
            try:
                scope.center_lat = float(parts[0])
                scope.center_lng = float(parts[1])
                scope.center_label = f"{scope.center_lat:.4f},{scope.center_lng:.4f}"
            except ValueError:
                scope.center_label = args.center
        else:
            scope.center_label = args.center
    return scope


def _memory_session() -> Session:
    """A disposable in-memory SQLite session for dry-runs — schema created, nothing persisted."""
    from .. import models  # noqa: F401  — register tables on SQLModel.metadata

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _persistent_session() -> Session:
    from ..db import engine, init_db

    init_db()
    return Session(engine)


def _print_report(report: IngestionReport, *, dry_run: bool) -> None:
    mode = "DRY-RUN (nothing written)" if dry_run else "LIVE"
    print(f"\nIngestion report — scope: {report.scope_label} — {mode}")
    print("-" * 68)
    print(f"{'source':<26}{'found':>7}{'kept':>7}{'new':>7}{'updated':>9}  status")
    print("-" * 68)
    for r in report.per_source:
        status = "ok" if r.error is None else f"ERROR {r.error}"
        print(f"{r.source:<26}{r.found:>7}{r.kept:>7}{r.new:>7}{r.updated:>9}  {status}")
    print("-" * 68)
    totals_found = sum(r.found for r in report.per_source)
    totals_kept = sum(r.kept for r in report.per_source)
    print(
        f"{'TOTAL':<26}{totals_found:>7}{totals_kept:>7}"
        f"{report.total_new:>7}{report.total_updated:>9}"
    )
    errors = [r for r in report.per_source if r.error]
    if errors:
        print(f"\n{len(errors)} source(s) failed (isolated — run continued).")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="python -m app.ingest",
        description="Fetch Mainfranken IT events from registered source adapters into the DB.",
    )
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        metavar="NAME",
        help="adapter name to run (repeatable); default = all registered adapters",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="run the full pipeline but write to a throwaway DB (no real persistence)",
    )
    parser.add_argument("--radius-km", type=int, default=None, help="override scope radius in km")
    parser.add_argument(
        "--center",
        default=None,
        metavar="LAT,LNG|LABEL",
        help="override scope center as 'lat,lng' coordinates or a place label",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="enable debug logging")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)-7s %(name)s: %(message)s",
    )

    scope = _build_scope(args)
    names = args.sources or None

    session = _memory_session() if args.dry_run else _persistent_session()
    try:
        report = asyncio.run(run_ingestion(session, scope=scope, names=names))
    finally:
        session.close()

    _print_report(report, dry_run=args.dry_run)
    if not args.dry_run:
        print(f"\nDatabase: {settings.database_url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
