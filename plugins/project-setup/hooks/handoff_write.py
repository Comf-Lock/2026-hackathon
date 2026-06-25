#!/usr/bin/env python3
"""
handoff_write.py — Script-gestützte HANDOFF-Aktualisierung.

Der LLM-Agent liefert einen JSON-Payload (stdin), dieses Script übernimmt
alle Dateimanipulation: Frontmatter-Update, Sektionen ersetzen, History prunen.
Kaltzone (landmarks, read_if_needed) bleibt strukturell unberührt.

Input JSON:
{
  "handoff_path": "/abs/path/HANDOFF_project.md",   # required
  "last_updated":  "2026-05-16-slug",                # required
  "new_status_tags": ["slug"],                        # max 3 tags total after trim
  "current_task":  "...",                             # replaces section content
  "active_plans":  "...",                             # replaces section content
  "iteration_entry": "2026-05-16 · slug · Einzeiler", # appended, history pruned to 5
  "open_questions_add": ["Neue Frage"],
  "open_questions_remove": ["Textfragment der erledigten Frage"],
  "backlog_add": ["**Thema** — kurz"],
  "backlog_remove": ["Textfragment"],
  "decisions_made_set": ["- Anker 1", "- Anker 2"],  # replaces decisions_made with these items (post-promotion)
  # backlog wird immer auf MAX_BACKLOG_ENTRIES (20) gekürzt — unabhängig von backlog_add/remove
}

Nicht geänderte Felder weglassen oder auf [] setzen.

Aufruf:
  echo '<json>' | python3 hooks/handoff_write.py
  python3 hooks/handoff_write.py < payload.json
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

HOT_MARKER = "<!-- /hot-context -->"
MAX_STATUS_TAGS = 3
MAX_HISTORY_ENTRIES = 5
MAX_BACKLOG_ENTRIES = 20

# Rolling-Journal: Konsolidierungs-Marker (Konvention geteilt mit
# rolling-handoff-write Phase 5 und handoff_inject.py Journal-Crash-Inject).
JOURNAL_DIR_RELATIVE = Path("_scrape") / ".session"
JOURNAL_GLOB = "journal-*.md"
JOURNAL_FILES_TO_MARK = 2  # heutiges + ggf. Vortags-Journal (Tageswechsel-Fall)
CONSOLIDATION_MARKER_RE = re.compile(r"^--- konsolidiert .+? ---\s*$", re.MULTILINE)


# ---------------------------------------------------------------------------
# File splitting
# ---------------------------------------------------------------------------

def split_file(content: str) -> tuple[str, str, str]:
    """Split HANDOFF into (frontmatter_raw, hot_body, cold_body).

    cold_body includes the HOT_MARKER itself (for exact round-trip).
    hot_body is everything between frontmatter and HOT_MARKER.
    """
    # Frontmatter: starts with "---\n", ends at second "\n---\n"
    fm_raw = ""
    rest = content
    if content.startswith("---\n"):
        end = content.find("\n---\n", 4)
        if end >= 0:
            fm_raw = content[: end + 5]  # +5 for "\n---\n"
            rest = content[end + 5 :]

    # Hot / cold split — match only a standalone marker line, not embedded occurrences
    marker_re = re.compile(
        r"^" + re.escape(HOT_MARKER) + r"\s*$", re.MULTILINE
    )
    m = marker_re.search(rest)
    if m:
        hot_body = rest[: m.start()]
        cold_body = rest[m.start() :]
    else:
        hot_body = rest
        cold_body = ""

    return fm_raw, hot_body, cold_body


# ---------------------------------------------------------------------------
# Frontmatter
# ---------------------------------------------------------------------------

def _set_working_directory(fm_raw: str, working_directory: str) -> str:
    """Setze ``working_directory`` im Frontmatter auf den Ablageort der Datei.

    Self-Heal pro Write (CWD-Worktree-Wahrheit): eine in ``master`` angelegte HANDOFF,
    die später im Feature-Worktree (``agent-1``) liegt, darf nicht weiter
    ``working_directory: …/master`` tragen — sonst zieht sie Folge-Agents in den
    falschen Worktree (`rolling-worktree-split-arch`). Maschinenagnostisch (Mac/X1):
    immer der tatsächliche Pfad der Datei. Fehlt das Feld, wird es eingefügt.
    Spiegelt ``rolling_handoff_write._set_working_directory`` (bewusster Fork — beide
    Pfade müssen die Invariante durchsetzen)."""
    if re.search(r"^working_directory:.*$", fm_raw, re.MULTILINE):
        return re.sub(
            r"^working_directory:.*$",
            lambda _m: f"working_directory: {working_directory}",
            fm_raw,
            flags=re.MULTILINE,
        )
    new_field = f"working_directory: {working_directory}"
    for anchor in (r"^vorhaben:.*$", r"^type:.*$"):
        m = re.search(anchor, fm_raw, re.MULTILINE)
        if m:
            return fm_raw[: m.end()] + "\n" + new_field + fm_raw[m.end() :]
    if fm_raw.startswith("---\n"):
        return "---\n" + new_field + "\n" + fm_raw[4:]
    return new_field + "\n" + fm_raw


def update_frontmatter(
    fm_raw: str,
    last_updated: str,
    new_tags: list[str],
    working_directory: str | None = None,
) -> str:
    # last_updated
    fm_raw = re.sub(
        r"^(last_updated:\s*).*$",
        f"\\g<1>{last_updated}",
        fm_raw,
        flags=re.MULTILINE,
    )

    # status: append new tags, trim — [ \t]* statt \s*, sonst frisst die Regex
    # bei leerer status-Zeile den Zeilenumbruch und matcht die Folgezeile
    m = re.search(r"^(status:[ \t]*)(.*)$", fm_raw, re.MULTILINE)
    if m:
        current = [t.strip() for t in m.group(2).split("·") if t.strip()]
        for tag in new_tags:
            if tag not in current:
                current.append(tag)
        trimmed = current[-MAX_STATUS_TAGS:]
        new_line = f"status: {' · '.join(trimmed)}"
        fm_raw = re.sub(r"^status:.*$", new_line, fm_raw, flags=re.MULTILINE)

    # working_directory: self-heal auf den CWD-Worktree (Ablageort der Datei)
    if working_directory is not None:
        fm_raw = _set_working_directory(fm_raw, working_directory)

    return fm_raw


# ---------------------------------------------------------------------------
# Section helpers
# ---------------------------------------------------------------------------

def _section_span(body: str, name: str) -> tuple[int, int] | None:
    """Return (content_start, content_end) for a ## section in body.

    content_start is the position after the "## Name\\n" header line.
    content_end is the start of the next ## header line (or end of body).
    Returns None if section not found.
    Matching is case-insensitive to handle legacy lowercase section names.
    """
    pattern = rf"^##\s+{re.escape(name)}\s*\n"
    m = re.search(pattern, body, re.MULTILINE | re.IGNORECASE)
    if not m:
        return None
    content_start = m.end()

    # Next ## header (not ###)
    next_m = re.search(r"^##\s", body[content_start:], re.MULTILINE)
    content_end = content_start + next_m.start() if next_m else len(body)
    return content_start, content_end


def replace_section(body: str, name: str, new_content: str) -> str:
    """Replace section content. Ensures one blank line before next section."""
    span = _section_span(body, name)
    if span is None:
        return body
    s, e = span
    new_content = new_content.rstrip("\n") + "\n\n"
    return body[:s] + new_content + body[e:]


def update_iteration_history(body: str, entry: str) -> str:
    """Append entry to ## Iteration History, prune to MAX_HISTORY_ENTRIES."""
    span = _section_span(body, "Iteration History")
    if span is None:
        return body
    s, e = span
    old = body[s:e]

    # Collect existing list items
    items = [l for l in old.splitlines() if l.strip().startswith("-")]
    new_line = entry if entry.startswith("-") else f"- {entry}"
    items.append(new_line)
    items = items[-MAX_HISTORY_ENTRIES:]

    new_content = "\n".join(items) + "\n\n"
    return body[:s] + new_content + body[e:]


def prune_list_section(body: str, name: str, max_entries: int) -> str:
    """Trim a list section to at most max_entries bullets, dropping the oldest."""
    span = _section_span(body, name)
    if span is None:
        return body
    s, e = span
    old = body[s:e]
    lines = old.splitlines(keepends=True)
    bullet_lines = [l for l in lines if l.strip().startswith("-")]
    other_lines = [l for l in lines if not l.strip().startswith("-")]
    if len(bullet_lines) <= max_entries:
        return body
    bullet_lines = bullet_lines[-max_entries:]
    new_content = "".join(bullet_lines) + "".join(other_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    return body[:s] + new_content + body[e:]


def update_list_section(
    body: str, name: str, add: list[str], remove: list[str]
) -> str:
    """Add/remove bullet items in a ## section.

    Non-bullet lines (blockquotes, blank lines) are preserved and placed
    after the bullet list to maintain hints like "> Kaltzone:".
    """
    span = _section_span(body, name)
    if span is None:
        return body
    s, e = span
    old = body[s:e]

    lines = old.splitlines(keepends=True)
    bullet_lines = [l for l in lines if l.strip().startswith("-")]
    other_lines = [l for l in lines if not l.strip().startswith("-")]

    # Remove
    if remove:
        bullet_lines = [
            l for l in bullet_lines
            if not any(frag.lower() in l.lower() for frag in remove)
        ]

    # Add (deduplicated)
    for item in add:
        line = f"- {item}\n" if not item.startswith("-") else f"{item}\n"
        if line not in bullet_lines:
            bullet_lines.append(line)

    new_content = "".join(bullet_lines) + "".join(other_lines)
    if not new_content.endswith("\n"):
        new_content += "\n"
    return body[:s] + new_content + body[e:]


# ---------------------------------------------------------------------------
# Journal-Konsolidierungs-Marker (Option A, entschieden 2026-06-11)
# ---------------------------------------------------------------------------

def mark_journals_consolidated(handoff_path: Path, slug: str) -> list[str]:
    """Append Konsolidierungs-Marker an unkonsolidierte Tagesjournale.

    Der klassische handoff-save konsolidiert denselben Session-Stand wie eine
    Rolling-Rotation — ohne Marker erscheinen seine bereits konsolidierten
    Journal-Einträge beim nächsten SessionStart trotzdem als „unkonsolidiert"
    (Mixed-Mode-Rauschen, kostet Inject-Budget; agent-os real 3,3 KB).

    Idempotent: Journale, die bereits mit einem Marker enden (kein Eintrag nach
    dem letzten Marker), werden übersprungen — gleicher Guard wie
    rolling-handoff-write Phase 5. Fail-quiet: Marker-Fehler dürfen den
    HANDOFF-Write nicht scheitern lassen.
    """
    marked: list[str] = []
    journal_dir = handoff_path.parent / JOURNAL_DIR_RELATIVE
    if not journal_dir.is_dir():
        return marked
    marker = f"\n--- konsolidiert {datetime.now().strftime('%H:%M')} · {slug} ---\n"
    for journal in sorted(journal_dir.glob(JOURNAL_GLOB), reverse=True)[:JOURNAL_FILES_TO_MARK]:
        try:
            content = journal.read_text(encoding="utf-8")
            matches = list(CONSOLIDATION_MARKER_RE.finditer(content))
            tail = content[matches[-1].end():] if matches else content
            if not tail.strip():
                continue  # endet bereits mit Marker — Guard gegen Doppel-Marker
            with journal.open("a", encoding="utf-8") as fh:
                if not content.endswith("\n"):
                    fh.write("\n")
                fh.write(marker)
            marked.append(journal.name)
        except OSError:
            continue
    return marked


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    try:
        raw = sys.stdin.read()
        payload: dict = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"ERROR: JSON parse failed — {exc}", file=sys.stderr)
        return 1

    handoff_path = Path(payload.get("handoff_path", ""))
    if not handoff_path.is_file():
        print(f"ERROR: HANDOFF not found: {handoff_path}", file=sys.stderr)
        return 1

    content = handoff_path.read_text(encoding="utf-8")
    fm_raw, hot_body, cold_body = split_file(content)

    # 1. Frontmatter — working_directory self-heal auf den Ablageort der HANDOFF
    fm_raw = update_frontmatter(
        fm_raw,
        payload["last_updated"],
        payload.get("new_status_tags", []),
        str(handoff_path.parent),
    )

    # 2. current_task
    if ct := payload.get("current_task"):
        hot_body = replace_section(hot_body, "current_task", ct.strip() + "\n")

    # 3. active_plans
    if ap := payload.get("active_plans"):
        hot_body = replace_section(hot_body, "active_plans", ap.strip() + "\n")

    # 4. Iteration History — cold zone preferred; hot zone fallback for legacy HANDOFFs
    if ie := payload.get("iteration_entry"):
        if _section_span(cold_body, "Iteration History"):
            cold_body = update_iteration_history(cold_body, ie)
        else:
            hot_body = update_iteration_history(hot_body, ie)

    # 5. open_questions (hot zone)
    if payload.get("open_questions_add") or payload.get("open_questions_remove"):
        hot_body = update_list_section(
            hot_body,
            "open_questions",
            payload.get("open_questions_add", []),
            payload.get("open_questions_remove", []),
        )

    # 6. backlog (cold zone)
    if payload.get("backlog_add") or payload.get("backlog_remove"):
        cold_body = update_list_section(
            cold_body,
            "backlog",
            payload.get("backlog_add", []),
            payload.get("backlog_remove", []),
        )
    cold_body = prune_list_section(cold_body, "backlog", MAX_BACKLOG_ENTRIES)

    # 7. decisions_made — post-promotion cleanup (hot zone preferred, cold zone fallback)
    if dm_set := payload.get("decisions_made_set"):
        new_content = "\n".join(
            (f"- {d}" if not d.startswith("-") else d) for d in dm_set
        ) + "\n"
        if _section_span(hot_body, "decisions_made"):
            hot_body = replace_section(hot_body, "decisions_made", new_content)
        elif _section_span(cold_body, "decisions_made"):
            cold_body = replace_section(cold_body, "decisions_made", new_content)

    handoff_path.write_text(fm_raw + hot_body + cold_body, encoding="utf-8")

    # 8. Rolling-Journale als konsolidiert markieren (Option A) — der Save
    # destilliert denselben Stand, den auch eine Rotation konsolidieren würde.
    slug = re.sub(r"^\d{4}-\d{2}-\d{2}-?", "", payload["last_updated"]) or "handoff-save"
    marked = mark_journals_consolidated(handoff_path, slug)

    name = handoff_path.name
    entry = payload.get("iteration_entry", "")
    print(f"✓ {name} aktualisiert")
    print(f"  last_updated: {payload['last_updated']}")
    if entry:
        print(f"  iteration:    {entry[:70]}")
    for journal_name in marked:
        print(f"  journal:      {journal_name} → Konsolidierungs-Marker gesetzt")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
