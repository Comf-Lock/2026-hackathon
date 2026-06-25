"""Event ingestion — quell-agnostische Adapter → kanonischer Store.

The rest of the app never touches a source directly: every source is an adapter that yields
RawEventRecord (see .types). The core (slice 2: .core) filters + upserts those records into the
Event/EventSource tables. See documentation/features/event-sources-mainfranken.md for the source
catalogue and plans/event-radar-slice-2.md for the build plan.
"""
