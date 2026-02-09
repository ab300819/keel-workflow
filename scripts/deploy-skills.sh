#!/bin/bash
# Deploy skills to Claude Code, Codex, and OpenCode discovery paths
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_DIR/skills"

echo "Deploying skills from: $SKILLS_DIR"

# Claude Code: ~/.claude/skills/<name>/
mkdir -p ~/.claude/skills
for skill_dir in "$SKILLS_DIR"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name=$(basename "$skill_dir")
    ln -sfn "$skill_dir" ~/.claude/skills/"$skill_name"
    echo "  Claude Code: ~/.claude/skills/$skill_name"
done

# Codex + OpenCode: ~/.agents/skills/<name>/
mkdir -p ~/.agents/skills
for skill_dir in "$SKILLS_DIR"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    skill_name=$(basename "$skill_dir")
    ln -sfn "$skill_dir" ~/.agents/skills/"$skill_name"
    echo "  Codex/OpenCode: ~/.agents/skills/$skill_name"
done

echo "Done. Skills deployed to Claude Code, Codex, and OpenCode."
