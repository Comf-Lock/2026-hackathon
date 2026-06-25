#!/usr/bin/env bash
# setup-scrape-buckets.sh — Create _scrape/ bucket structure (Lifecycle-Schema v2).
# Idempotent: existing directories and .gitkeep files are left unchanged.
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SCRAPE_DIR="$PROJECT_ROOT/_scrape"

BUCKETS=(inbox captured processed work out promote)

for bucket in "${BUCKETS[@]}"; do
    bucket_dir="$SCRAPE_DIR/$bucket"
    media_dir="$bucket_dir/_media"
    gitkeep="$bucket_dir/.gitkeep"

    mkdir -p "$media_dir"

    if [ ! -f "$gitkeep" ]; then
        touch "$gitkeep"
        printf "✓ _scrape/%s/ (created)\n" "$bucket"
    else
        printf "⊘ _scrape/%s/ (already exists)\n" "$bucket"
    fi
done

echo ""
echo "✓ _scrape/ structure complete (Lifecycle-Schema v2)"
echo "  Buckets: ${BUCKETS[*]}"
echo "  Each bucket has _media/ for binaries."
