#!/usr/bin/env bash
# setup-gitignore.sh — Add AI tool entries to .gitignore (idempotent).
# Does not overwrite existing entries; appends only what is missing.
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
GITIGNORE="$PROJECT_ROOT/.gitignore"

HEADER="# AI tool integration (managed by project-setup)"
ENTRIES=(
    ".claude/skills"
    ".agents/skills"
    ".gemini/skills"
    ".cursor/skills"
    "_scrape/"
)

added=()
skipped=()

for entry in "${ENTRIES[@]}"; do
    if grep -qF "$entry" "$GITIGNORE" 2>/dev/null; then
        skipped+=("$entry")
    else
        added+=("$entry")
    fi
done

if [ ${#added[@]} -gt 0 ]; then
    {
        echo ""
        echo "$HEADER"
        for entry in "${added[@]}"; do
            echo "$entry"
        done
    } >> "$GITIGNORE"
    for entry in "${added[@]}"; do
        echo "✓ added: $entry"
    done
fi

if [ ${#skipped[@]} -gt 0 ]; then
    for entry in "${skipped[@]}"; do
        echo "⊘ already present: $entry"
    done
fi

echo ""
echo "✓ .gitignore up to date"
