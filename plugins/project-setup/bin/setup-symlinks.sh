#!/usr/bin/env bash
# setup-symlinks.sh — Create AI tool symlinks for the current project/worktree.
# Idempotent: safe to run multiple times. Run from inside the target project.
set -euo pipefail

PROJECT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
SKILLS_DIR="$PROJECT_ROOT/skills"

if [ ! -d "$SKILLS_DIR" ]; then
    echo "⚠️  No skills/ directory at $PROJECT_ROOT — skipping."
    exit 0
fi

# Resolve the git common-dir of a path (shared by all worktrees of one repo).
# Empty when the path is not inside a git repo.
gitcommon() { ( cd "$1" 2>/dev/null && d="$(git rev-parse --git-common-dir 2>/dev/null)" && realpath "$d" 2>/dev/null ) || true; }
PROJECT_REPO="$(gitcommon "$PROJECT_ROOT")"

# Tool → (user config dir to check, symlink path inside project)
declare -a TOOLS=(
    "claude:.claude:.claude/skills"
    "antigravity:.gemini/antigravity:.agents/skills"
    "gemini:.gemini:.gemini/skills"
    "cursor:.cursor:.cursor/skills"
)

for entry in "${TOOLS[@]}"; do
    IFS=":" read -r tool_name config_dir symlink_path <<< "$entry"
    full_config="$HOME/$config_dir"
    full_symlink="$PROJECT_ROOT/$symlink_path"
    parent_dir="$(dirname "$full_symlink")"

    if [ ! -d "$full_config" ]; then
        printf "⊘ %-12s not installed (skipped)\n" "$tool_name"
        continue
    fi

    # Skip the project-scope skills symlink when this tool's GLOBAL user-scope
    # skills dir already resolves into THIS git repo. Otherwise the same skills
    # register twice (user + project scope) and surface as duplicated
    # "(User)/(Project)" entries. Self-detecting: only fires for the repo that is
    # itself the global skills source (e.g. agent-core), never for other projects.
    if [ -e "$full_config/skills" ] && [ -n "$PROJECT_REPO" ]; then
        global_repo="$(gitcommon "$full_config/skills")"
        if [ "$global_repo" = "$PROJECT_REPO" ]; then
            # Self-heal: drop a pre-existing redundant symlink so the duplicate disappears.
            [ -L "$full_symlink" ] && rm "$full_symlink"
            printf "⊘ %-12s %s skipped — global %s/skills already serves this repo\n" "$tool_name" "$symlink_path" "$config_dir"
            continue
        fi
    fi

    mkdir -p "$parent_dir"

    if [ -L "$full_symlink" ]; then
        current_target="$(readlink "$full_symlink")"
        if [ "$current_target" = "../skills" ]; then
            printf "✓ %-12s %s → ../skills (already correct)\n" "$tool_name" "$symlink_path"
            continue
        fi
        rm "$full_symlink"
        printf "↻ %-12s updated (was: %s)\n" "$tool_name" "$current_target"
    elif [ -d "$full_symlink" ]; then
        printf "⚠️  %-12s %s is a real directory — skipping (manual check needed)\n" "$tool_name" "$symlink_path"
        continue
    fi

    (cd "$parent_dir" && ln -s ../skills skills)
    printf "✓ %-12s %s → ../skills\n" "$tool_name" "$symlink_path"
done
