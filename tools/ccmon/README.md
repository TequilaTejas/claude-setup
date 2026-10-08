# ccmon

A read-only terminal monitor for Claude Code sessions. Tab 1 of `work`.

## Run

```
work         # kitty window: dashboard tab + one tab per project
dashboard    # the same monitor, standalone in any terminal
```

## Keys

| key | action |
|---|---|
| `↑` `↓` or `j` `k` | move selection |
| `Enter` | focus that session's kitty tab, or open it in a **new** tab |
| `p` | pin (pinned sort to the top of their group) |
| `Tab` | filter: all → needs you → working → idle |
| `r` | force reload |
| `q` | quit |

## It never writes to Claude Code state

Reads only:

- `~/.claude/projects/<encoded-cwd>/<session-id>.jsonl` — transcripts
- `~/.claude/jobs/<short-id>/state.json` — authoritative background state

Its own pins live in `~/.config/ccmon/pins.json`, never `~/.claude/jobs/pins.json`.

Monitoring is entirely passive: parsing, watching, and rendering touch nothing.
It never shells out to `claude agents`, which can spawn the supervisor daemon.

`Enter` is the one exception, and only because you pressed it. It opens the
session, which is the point of a jump key:

- a background session (has a `jobs/<id>` entry) → `claude attach <short-id>`
- an interactive session → `claude -r <session-id>`
- a project with no session → plain `claude`

It first looks for a kitty tab already running that session and focuses it,
skipping the dashboard's own window. Only if none exists does it open a new tab
in the project's directory. Outside kitty it copies the command to the clipboard
instead.

## How state is decided

`needs-input` / `working` / `idle` / `no-agent`.

Background sessions have an authoritative `state` in `jobs/<id>/state.json`
(`blocked` → needs-input, `working`, `done`/`failed`/`stopped` → idle). Its
`needs` field supplies the `asking: …` line.

Interactive sessions have no state file, so it is inferred from the transcript:
a finished turn appends a `system/turn_duration` record, so anything newer than
that means the agent is mid-turn. Records of type `attachment`,
`file-history-snapshot`, and `queue-operation` carry timestamps but say nothing
about progress, so they are skipped when finding the newest meaningful record.
A session untouched for 15 minutes is idle regardless.

Sessions older than 24h are hidden unless they need input. `parse_sessions.py --all`
shows everything.

Files touched come from `toolUseResult`: `type: "create"` → `+`, `type: "update"`
or an Edit patch → `~`. Reads are not "touched".

## Live refresh

`watchdog` (FSEvents on macOS) watches the two directories above and coalesces
bursts with a 250ms debounce. There is no file polling. A 1s timer re-renders
elapsed labels from timestamps already in memory. Idle cost is ~1.6% of one core.

## Layout

`parse_sessions.py` — extraction, stdlib only. Prints the whole model as JSON.
`app.py` — Textual UI.
`ccmon` — launcher.

Textual over Bubble Tea because Go was not installed, the work is IO-bound
rather than CPU-bound, and Textual's `run_test()` pilot allows the UI itself to
be tested headlessly.
