# claude-setup

My Claude Code, kitty, tmux and shell setup. Clone it on a new Mac, run one script, and you get the same environment.

## New Mac

Open Terminal and paste:

```bash
bash -c "$(curl -fsSL https://raw.githubusercontent.com/TequilaTejas/mac-setup/main/go.sh)"
```

You approve two things: your Mac password (Homebrew) and GitHub in the browser. The script then installs everything and opens Claude Code for you to log in.

`install.sh` symlinks each file from this repo into place. When Claude Code edits `settings.json`, writes a memory, or you add a skill, the change lands in this repo. Any file it replaces goes to `~/.dotfiles-backup/<timestamp>/`.

## Keep Macs in sync

```bash
~/projects/claude-setup/sync.sh   # pull, adopt new skills, commit, push
```

Run it on the Mac you changed, then `git pull` on the other one.

## What's in here

| Path | Lands at | What it is |
|---|---|---|
| `claude/CLAUDE.md` | `~/.claude/CLAUDE.md` | Global instructions (ADHD output style, stop-slop, vocabulary) |
| `claude/settings.json` | `~/.claude/settings.json` | Model, statusline, Lockin notification hook, figma plugin, env |
| `claude/settings.local.json` | `~/.claude/settings.local.json` | Permission allowlist |
| `claude/*.sh` | `~/.claude/` | Statusline, tmux git status, Lockin hook |
| `claude/skills/*` | `~/.claude/skills/` | 9 personal skills |
| `agents-skills/vocabulary` | `~/.agents/skills/` + `~/.claude/skills/` | Design vocabulary skill |
| `claude/memory/` | `~/.claude/projects/-Users-<you>/memory/` | Auto-memory (project notes, preferences) |
| `claude/mcp-servers.json` | added via `claude mcp add` | Playwright + Mobbin MCP servers (reference copy) |
| `kitty/` | `~/.config/kitty/` | Theme, keymaps, `work` session layout |
| `tmux/tmux.conf` | `~/.tmux.conf` | tmux config |
| `zsh/zshrc` | `~/.zshrc` | `yolo`, `wt`/`wtls`/`wtrm`, `work`, `dashboard` |
| `cmux/`, `ccmon-config/` | `~/.config/` | cmux and ccmon settings |
| `tools/ccmon` | `~/projects/ccmon` | Session-monitor dashboard used by `work` |
| `Brewfile` | `brew bundle` | CLI tools and apps |

## Left out on purpose

- Session transcripts, history and caches (`~/.claude/projects/*.jsonl`, 1.5 GB)
- `~/.claude.json`: login tokens and machine IDs. Claude recreates it on first login.
- claude.ai synced skills (`~/.claude/skills/synced`) and plugin caches. They download on first login.
- Codex config: the Codex app manages it and it points at machine-local paths.
- Project repos (`onething`, `tejasdua.com`, etc.). Clone the ones you need; `work` opens tabs for those two.

Keep this repo private. The memory folder holds notes about clients and projects.
