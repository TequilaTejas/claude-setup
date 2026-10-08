# Output style (always on)

- Follow the `i-have-adhd` skill (~/.claude/skills/i-have-adhd) in EVERY response, for every kind of message: coding, debugging, planning, explanations, casual chat.
- Core rules: lead with the next concrete action, number multi-step work, restate state each turn ("step 3 of 5 done"), one two-minute next action at the end, no preamble, no recaps, no closing pleasantries, specific time estimates, cap lists at 5, tangents offered separately.

# Local previews

- Whenever you share a localhost URL (dev server, preview, etc.), open it in the browser with `open <url>` so it shows up immediately.

# Design vocabulary

- Use the `vocabulary` skill (~/.agents/skills/vocabulary) whenever naming design or UI concepts: picking the exact term, disambiguating near-synonyms (badge vs tag, tooltip vs popover, kerning vs tracking), or writing specs, design critiques, and commit messages about UI.

# Writing

- For ALL prose writing tasks (docs, blog posts, emails, README files, marketing copy, UI copy, summaries, or any other written content), invoke the `stop-slop` skill (~/.claude/skills/stop-slop) before drafting, and apply its rules when editing or reviewing existing text.
- Follow its core rules in all written output: cut filler phrases and adverbs, use active voice with human subjects, avoid formulaic AI structures (binary contrasts, rhetorical setups, "not X, it's Y"), no em dashes, be specific, vary rhythm, and trust the reader.
