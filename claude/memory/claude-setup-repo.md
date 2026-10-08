---
name: claude-setup-repo
description: Private dotfiles repo TequilaTejas/claude-setup at ~/projects/claude-setup; install.sh symlinks Claude/kitty/tmux/zsh config onto a new Mac
metadata:
  type: project
---

Created 2026-10-08. New Mac entry point: public TequilaTejas/mac-setup go.sh one-liner (brew, gh web login, clone, install.sh, opens claude). Holds CLAUDE.md, settings, 9 personal skills + vocabulary, auto-memory, kitty/tmux/zshrc, cmux, ccmon, Brewfile, MCP servers. `install.sh` symlinks into place (backs up to ~/.dotfiles-backup); `sync.sh` adopts new skills, commits, pushes. Repo is PRIVATE because memory has client notes.

**Why:** Tejas is moving to a new Mac and wants the same setup on multiple laptops.
**How to apply:** when adding a skill or changing config, remind to run sync.sh. As of creation, the ORIGINAL Mac still uses plain files, not symlinks, unless install.sh was later run there.
