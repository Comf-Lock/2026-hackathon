"""Manual ingestion trigger — run the scraper against the configured database.

    python -m app.ingest run                 # run all registered adapters
    python -m app.ingest run --source meetup # run only named adapter(s)
    python -m app.ingest list                # show which adapters are registered

This is the manual entry point (a periodic scheduler/worker is deferred — see the slice plan).
It ensures the tables exist (init_db), opens a real DB session against settings.database_url,
runs one ingestion pass live (real network), persists the events, and prints the report.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys

from sqlmodel import Session

from ..db import engine, init_db
from .core import run_ingestion
from .registry import get_adapters


def _print_report(report) -> None:
    print(f"\nscope: {report.scope_label}")
    print(f"{'source':18}{'found':>7}{'kept':>7}{'new':>7}{'updated':>9}   error")
    for r in report.per_source:
        print(f"{r.source:18}{r.found:>7}{r.kept:>7}{r.new:>7}{r.updated:>9}   {r.error or ''}")
    print(f"\ntotal: new={report.total_new} updated={report.total_updated}")


def _cmd_run(names: list[str] | None) -> int:
    init_db()  # idempotent create_all — works even if the API has never started
    with Session(engine) as session:
        report = asyncio.run(run_ingestion(session, names=names))
    _print_report(report)
    return 0


def _cmd_list() -> int:
    for adapter in get_adapters():
        gate = "broad (keyword-gated)" if getattr(adapter, "broad", False) else "IT-native"
        print(f"  {adapter.name:18} {gate}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingest")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a single ingestion pass against the database")
    run.add_argument(
        "--source", action="append", dest="sources", metavar="NAME",
        help="only run this adapter (repeatable); default = all registered adapters",
    )
    sub.add_parser("list", help="list registered adapters")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if args.command == "run":
        return _cmd_run(args.sources)
    if args.command == "list":
        return _cmd_list()
    return 1


if __name__ == "__main__":
    sys.exit(main())
