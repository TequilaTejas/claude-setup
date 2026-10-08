#!/bin/bash
# Compact git status for the tmux status bar. Usage: tmux-git-status.sh <path>
dir="${1:-.}"

git -C "$dir" --no-optional-locks rev-parse --is-inside-work-tree >/dev/null 2>&1 || exit 0

branch=$(git -C "$dir" --no-optional-locks branch --show-current 2>/dev/null)
[ -z "$branch" ] && branch=$(git -C "$dir" --no-optional-locks rev-parse --short HEAD 2>/dev/null)

staged=$(git -C "$dir" --no-optional-locks diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
unstaged=$(git -C "$dir" --no-optional-locks diff --name-only 2>/dev/null | wc -l | tr -d ' ')
untracked=$(git -C "$dir" --no-optional-locks ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

ahead_behind=$(git -C "$dir" --no-optional-locks rev-list --left-right --count '@{u}...HEAD' 2>/dev/null)
ahead=0
behind=0
if [ -n "$ahead_behind" ]; then
  behind=$(echo "$ahead_behind" | awk '{print $1}')
  ahead=$(echo "$ahead_behind" | awk '{print $2}')
fi

out="$branch"
[ "$staged" != "0" ] && out="$out +$staged"
[ "$unstaged" != "0" ] && out="$out ~$unstaged"
[ "$untracked" != "0" ] && out="$out ?$untracked"
[ "$ahead" != "0" ] && out="$out ↑$ahead"
[ "$behind" != "0" ] && out="$out ↓$behind"

printf "%s" "$out"
