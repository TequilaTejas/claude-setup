#!/usr/bin/env bash
# Set up Tejas's Claude Code + terminal environment on a fresh Mac.
# Safe to re-run. Existing files are moved to ~/.dotfiles-backup/<timestamp>/ before linking.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
LINKS_ONLY=0; [ "${1:-}" = "--links-only" ] && LINKS_ONLY=1   # used for testing
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
BACKUP="$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)"

step() { printf "\n\033[1;36m==> %s\033[0m\n" "$1"; }

link() {  # link <repo-path> <target>
  local src="$REPO/$1" dst="$2"
  mkdir -p "$(dirname "$dst")"
  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then return; fi
  if [ -e "$dst" ] || [ -L "$dst" ]; then
    mkdir -p "$BACKUP"; mv "$dst" "$BACKUP/$(echo "$dst" | sed "s#$HOME/##; s#/#__#g")"
  fi
  ln -s "$src" "$dst"; echo "  linked $dst"
}

if [ $LINKS_ONLY = 0 ]; then
step "1/6 Homebrew"
if ! command -v brew >/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi
brew bundle --file="$REPO/Brewfile" || echo "  (some brew items failed; continuing)"

step "2/6 Claude Code + Codex CLIs"
command -v claude >/dev/null || curl -fsSL https://claude.ai/install.sh | bash
command -v codex  >/dev/null || npm install -g @openai/codex || true
fi

step "3/6 Fix hardcoded home paths (only if username differs)"
if [ "$HOME" != "/Users/tejas" ]; then
  grep -rlI "/Users/tejas" "$REPO" --exclude-dir=.git | xargs sed -i '' "s#/Users/tejas#$HOME#g"
fi

step "4/6 Link Claude config"
link claude/CLAUDE.md                ~/.claude/CLAUDE.md
link claude/settings.json            ~/.claude/settings.json
link claude/settings.local.json      ~/.claude/settings.local.json
link claude/statusline-command.sh    ~/.claude/statusline-command.sh
link claude/tmux-git-status.sh       ~/.claude/tmux-git-status.sh
link claude/lockin-kitty-input.sh    ~/.claude/lockin-kitty-input.sh
for s in "$REPO"/claude/skills/*/; do
  n=$(basename "$s"); link "claude/skills/$n" ~/.claude/skills/"$n"
done
link agents-skills/vocabulary        ~/.agents/skills/vocabulary
link agents-skills/vocabulary        ~/.claude/skills/vocabulary
# Memory lives under a path-derived project key (/Users/tejas -> -Users-tejas)
MEMKEY="$(echo "$HOME" | sed 's#/#-#g')"
link claude/memory                   ~/.claude/projects/"$MEMKEY"/memory

step "5/6 Link terminal + shell config"
link kitty/kitty.conf                ~/.config/kitty/kitty.conf
link kitty/work.session              ~/.config/kitty/work.session
link tmux/tmux.conf                  ~/.tmux.conf
link zsh/zshrc                       ~/.zshrc
link cmux/cmux.json                  ~/.config/cmux/cmux.json
link ccmon-config/pins.json          ~/.config/ccmon/pins.json
[ -e ~/projects/ccmon ] || link tools/ccmon ~/projects/ccmon

step "6/6 MCP servers + project repos"
if [ $LINKS_ONLY = 0 ] && command -v claude >/dev/null; then
  claude mcp add --scope user playwright -- npx @playwright/mcp@latest --browser chromium 2>/dev/null || true
  claude mcp add --scope user --transport http mobbin https://api.mobbin.com/mcp 2>/dev/null || true
fi

# Repos the `work` kitty layout opens
if [ $LINKS_ONLY = 0 ] && [ ! -d ~/projects/tejasdua.com ]; then
  git clone -q https://github.com/TequilaTejas/tejasdua.com.git ~/projects/tejasdua.com || true
fi

cat <<'MSG'

All set. Two logins left, both open in your browser:
  1. Claude Code  -> starting now. Pick "Claude account" and approve in the browser.
  2. Codex        -> run `codex` whenever you want it.
Inside Claude, type /mcp and pick mobbin once to connect it.
MSG
[ -d "$BACKUP" ] && echo "Old files backed up to $BACKUP"
if [ $LINKS_ONLY = 0 ] && [ -t 0 ] && command -v claude >/dev/null; then
  cd ~ && exec claude
fi
