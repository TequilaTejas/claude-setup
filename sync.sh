#!/usr/bin/env bash
# Commit and push any config changes (new skills, memory, settings) from this Mac.
set -euo pipefail
cd "$(dirname "$0")"
git pull --rebase --autostash -q
# Pick up skills added directly in ~/.claude/skills that aren't in the repo yet
for d in ~/.claude/skills/*/; do
  n=$(basename "$d")
  [ "$n" = "synced" ] && continue
  [ -L "${d%/}" ] && continue
  [ -e "claude/skills/$n" ] && continue
  mv "${d%/}" "claude/skills/$n" && ln -s "$PWD/claude/skills/$n" ~/.claude/skills/"$n"
  echo "adopted new skill: $n"
done
git add -A
git diff --cached --quiet && { echo "nothing to sync"; exit 0; }
git commit -qm "sync from $(scutil --get ComputerName 2>/dev/null || hostname) $(date +%F)"
git push -q && echo "synced"
