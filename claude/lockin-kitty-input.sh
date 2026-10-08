#!/bin/bash
# Claude Code Notification hook → Lockin's kitty input exception.
# When a Claude Code session running inside kitty needs input (permission
# prompt / waiting on you), ping Lockin so a locked focus screen temporarily
# lets kitty through. Filters: kitty sessions only, and only if Lockin is
# already running (never launch it from here).
[ -n "$KITTY_WINDOW_ID" ] || exit 0
pgrep -xq Lockin || exit 0
open -g "lockin://kitty-input"
exit 0
