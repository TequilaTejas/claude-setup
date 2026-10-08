#!/bin/bash
# Claude Code status line
# Line 1: model, cwd, git branch + working-tree state
# Line 2: context window usage bar, cost, session duration, rate limits

input=$(cat)

model=$(echo "$input" | jq -r '.model.display_name')
cwd=$(echo "$input" | jq -r '.workspace.current_dir')
dir_display="${cwd/#$HOME/~}"
session_id=$(echo "$input" | jq -r '.session_id')

# --- Colors ---
DIM_CYAN='\033[2;36m'
DIM_YELLOW='\033[2;33m'
DIM_GREEN='\033[2;32m'
DIM_RED='\033[2;31m'
DIM_MAGENTA='\033[2;35m'
DIM_GRAY='\033[2;37m'
RESET='\033[0m'

# --- Git branch + working-tree state (cached per session, refreshed every 5s) ---
CACHE_FILE="/tmp/claude-statusline-git-${session_id}"
CACHE_MAX_AGE=5

cache_is_stale() {
  [ ! -f "$CACHE_FILE" ] && return 0
  local age=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE" 2>/dev/null || stat -c %Y "$CACHE_FILE" 2>/dev/null || echo 0) ))
  [ "$age" -gt "$CACHE_MAX_AGE" ]
}

if cache_is_stale; then
  if git -C "$cwd" --no-optional-locks rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    branch=$(git -C "$cwd" --no-optional-locks branch --show-current 2>/dev/null)
    [ -z "$branch" ] && branch=$(git -C "$cwd" --no-optional-locks rev-parse --short HEAD 2>/dev/null)

    staged=$(git -C "$cwd" --no-optional-locks diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')
    unstaged=$(git -C "$cwd" --no-optional-locks diff --name-only 2>/dev/null | wc -l | tr -d ' ')
    untracked=$(git -C "$cwd" --no-optional-locks ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')

    ahead_behind=$(git -C "$cwd" --no-optional-locks rev-list --left-right --count '@{u}...HEAD' 2>/dev/null)
    behind=$(echo "$ahead_behind" | awk '{print $1+0}')
    ahead=$(echo "$ahead_behind" | awk '{print $2+0}')

    echo "${branch}|${staged}|${unstaged}|${untracked}|${ahead}|${behind}" > "$CACHE_FILE"
  else
    echo "||||||" > "$CACHE_FILE"
  fi
fi

IFS='|' read -r branch staged unstaged untracked ahead behind < "$CACHE_FILE"

git_state=""
if [ -n "$branch" ]; then
  [ "$staged" != "0" ] && git_state="$git_state +$staged"
  [ "$unstaged" != "0" ] && git_state="$git_state ~$unstaged"
  [ "$untracked" != "0" ] && git_state="$git_state ?$untracked"
  [ "$ahead" != "0" ] && git_state="$git_state ↑$ahead"
  [ "$behind" != "0" ] && git_state="$git_state ↓$behind"
  [ -z "$git_state" ] && git_state=" clean"
fi

if [ -n "$branch" ]; then
  if [ "$git_state" = " clean" ]; then
    line1=$(printf "${DIM_CYAN}%s${RESET} ${DIM_YELLOW}%s${RESET} ${DIM_GREEN}(%s%s)${RESET}" "$model" "$dir_display" "$branch" "$git_state")
  else
    line1=$(printf "${DIM_CYAN}%s${RESET} ${DIM_YELLOW}%s${RESET} ${DIM_GREEN}(%s)${RESET}${DIM_RED}%s${RESET}" "$model" "$dir_display" "$branch" "$git_state")
  fi
else
  line1=$(printf "${DIM_CYAN}%s${RESET} ${DIM_YELLOW}%s${RESET}" "$model" "$dir_display")
fi

# --- Context window usage bar ---
pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0' | cut -d. -f1)
[ -z "$pct" ] && pct=0

bar_width=10
filled=$((pct * bar_width / 100))
empty=$((bar_width - filled))
bar=""
[ "$filled" -gt 0 ] && printf -v fill "%${filled}s" && bar="${fill// /█}"
[ "$empty" -gt 0 ] && printf -v pad "%${empty}s" && bar="${bar}${pad// /░}"

if [ "$pct" -ge 90 ]; then
  bar_color="$DIM_RED"
elif [ "$pct" -ge 70 ]; then
  bar_color="$DIM_YELLOW"
else
  bar_color="$DIM_GREEN"
fi

# --- Cost + duration ---
cost=$(echo "$input" | jq -r '.cost.total_cost_usd // 0')
duration_ms=$(echo "$input" | jq -r '.cost.total_duration_ms // 0')
cost_fmt=$(printf '$%.2f' "$cost")
duration_sec=$((duration_ms / 1000))
mins=$((duration_sec / 60))
secs=$((duration_sec % 60))

# --- Rate limits (Pro/Max only, absent otherwise) ---
five_h=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
seven_d=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
rate_str=""
[ -n "$five_h" ] && rate_str="${rate_str} 5h:$(printf '%.0f' "$five_h")%"
[ -n "$seven_d" ] && rate_str="${rate_str} 7d:$(printf '%.0f' "$seven_d")%"

line2=$(printf "${bar_color}%s${RESET} %s%% ${DIM_GRAY}|${RESET} ${DIM_MAGENTA}%s${RESET} ${DIM_GRAY}|${RESET} ${DIM_GRAY}%sm%ss${RESET}" "$bar" "$pct" "$cost_fmt" "$mins" "$secs")
if [ -n "$rate_str" ]; then
  suffix=$(printf " ${DIM_GRAY}|${RESET}${DIM_CYAN}%s${RESET}" "$rate_str")
  line2="${line2}${suffix}"
fi

printf "%s\n%s" "$line1" "$line2"
