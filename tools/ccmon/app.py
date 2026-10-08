#!/usr/bin/env python3
"""
ccmon — a read-only monitor for Claude Code sessions.

Reads ~/.claude transcripts and job state. Writes nothing there. Its own pin
state lives in ~/.config/ccmon/pins.json.

Refreshes on filesystem events (watchdog/FSEvents), debounced 250ms. The only
timer is a 1s tick that re-renders elapsed labels from timestamps already in
memory; it touches no files.
"""

import os
import sys
import json
import subprocess
import threading

from rich.text import Text
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Static
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from parse_sessions import build_model, elapsed_label, PROJECTS_DIR, JOBS_DIR

HOME = os.path.expanduser("~")
PIN_FILE = os.path.join(HOME, ".config", "ccmon", "pins.json")
DEBOUNCE_SECONDS = 0.25

RED = "#ef6b5e"     # needs you
BLUE = "#4c9aff"    # working
DIM = "#7a7a7a"     # idle
FAINT = "#5a5a5a"
BRIGHT = "#e8e8e8"
ADDED = "#4ade80"
MODIFIED = "#eab308"

GLYPH = {"needs-input": "●", "working": "●", "idle": "○", "no-agent": "○"}
COLOR = {"needs-input": RED, "working": BLUE, "idle": DIM, "no-agent": FAINT}
GROUPS = [
    ("needs-input", "NEEDS YOU"),
    ("working", "WORKING"),
    ("idle", "IDLE"),
]
FILTERS = [None, "needs-input", "working", "idle"]


def load_pins():
    try:
        with open(PIN_FILE) as fh:
            return set(json.load(fh))
    except (OSError, ValueError):
        return set()


def save_pins(pins):
    os.makedirs(os.path.dirname(PIN_FILE), exist_ok=True)
    tmp = PIN_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(sorted(pins), fh)
    os.replace(tmp, PIN_FILE)


def strip_markdown(text):
    """Emphasis and code fences add noise to a one-glance summary."""
    for token in ("**", "`", "__"):
        text = text.replace(token, "")
    return text


def long_elapsed(seconds):
    """'3m 12s' for the detail pane."""
    if seconds is None:
        return "unknown"
    if seconds < 60:
        return "%ds" % seconds
    if seconds < 3600:
        return "%dm %ds" % (seconds // 60, seconds % 60)
    if seconds < 86400:
        return "%dh %dm" % (seconds // 3600, (seconds % 3600) // 60)
    return "%dd %dh" % (seconds // 86400, (seconds % 86400) // 3600)


class _Debouncer(FileSystemEventHandler):
    """Collapse a burst of write events into one callback."""

    def __init__(self, callback):
        self._callback = callback
        self._timer = None
        self._lock = threading.Lock()

    def on_any_event(self, event):
        if event.is_directory:
            return
        path = getattr(event, "dest_path", "") or event.src_path
        if not (path.endswith(".jsonl") or path.endswith("state.json")):
            return
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(DEBOUNCE_SECONDS, self._callback)
            self._timer.daemon = True
            self._timer.start()


class SessionList(Static):
    pass


class DetailPane(Static):
    pass


class CCMon(App):
    CSS = """
    Screen { background: #0d0d0d; }

    #header {
        height: 3;
        padding: 1 2 0 2;
        background: #0d0d0d;
    }
    #body { height: 1fr; }
    #left {
        width: 58%;
        padding: 0 1 0 2;
        border-right: solid #262626;
        scrollbar-size: 1 1;
    }
    #right {
        width: 1fr;
        padding: 0 2 0 2;
        scrollbar-size: 1 1;
    }
    #footer {
        height: 2;
        padding: 0 2;
        color: #5a5a5a;
        border-top: solid #262626;
    }
    """

    BINDINGS = [
        Binding("up,k", "cursor_up", "move", show=False),
        Binding("down,j", "cursor_down", "move", show=False),
        Binding("enter", "jump", "jump", show=False),
        Binding("p", "pin", "pin", show=False),
        # Textual reserves Tab for focus traversal; priority takes it back.
        Binding("tab", "cycle_filter", "filter", show=False, priority=True),
        Binding("r", "reload", "reload", show=False),
        Binding("q,escape,ctrl+c", "quit", "quit", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.model = {"counts": {}, "sessions": [], "projects_without_agents": []}
        self.rows = []          # flattened selectable rows
        self.selected = 0
        self.filter_index = 0
        self.pins = load_pins()
        self.notice = ""
        self._observer = None

    # ---------- layout ----------

    def compose(self) -> ComposeResult:
        yield Static(id="header")
        with Horizontal(id="body"):
            with VerticalScroll(id="left"):
                yield SessionList(id="list")
            with VerticalScroll(id="right"):
                yield DetailPane(id="detail")
        yield Static(id="footer")

    def on_mount(self):
        self.reload_model()
        self.set_interval(1.0, self.render_all)  # elapsed ticks; no file IO
        self._start_watching()

    def on_unmount(self):
        if self._observer:
            self._observer.stop()

    def _start_watching(self):
        handler = _Debouncer(lambda: self.call_from_thread(self.reload_model))
        observer = Observer()
        for path in (PROJECTS_DIR, JOBS_DIR):
            if os.path.isdir(path):
                observer.schedule(handler, path, recursive=True)
        observer.daemon = True
        observer.start()
        self._observer = observer

    # ---------- data ----------

    def reload_model(self):
        self.model = build_model()
        self.render_all()

    def _visible_sessions(self):
        wanted = FILTERS[self.filter_index]
        items = list(self.model["sessions"])
        if wanted in (None, "idle"):
            for orphan in self.model["projects_without_agents"]:
                items.append(
                    {
                        "session_id": "noagent:" + orphan["project_path"],
                        "project": orphan["project"],
                        "project_path": orphan["project_path"],
                        "branch": None,
                        "state": "no-agent",
                        "subtitle": None,
                        "elapsed_seconds": None,
                        "last_assistant_message": None,
                        "files_touched": [],
                        "resume_cmd": None,
                    }
                )
        if wanted:
            # "no agent open" projects belong to the idle bucket.
            keep = {"idle", "no-agent"} if wanted == "idle" else {wanted}
            items = [s for s in items if s["state"] in keep]
        return items

    def _grouped(self):
        """[(group_label, [session, ...]), ...] with pinned first in each group."""
        items = self._visible_sessions()
        out = []
        for state, label in GROUPS:
            members = [s for s in items if s["state"] == state]
            if state == "idle":
                members += [s for s in items if s["state"] == "no-agent"]
            if not members:
                continue
            members.sort(
                key=lambda s: (
                    s["session_id"] not in self.pins,
                    s["elapsed_seconds"] if s["elapsed_seconds"] is not None else 1 << 30,
                )
            )
            out.append((label, members))
        return out

    # ---------- rendering ----------

    def render_all(self):
        groups = self._grouped()
        self.rows = [s for _, members in groups for s in members]
        if self.rows:
            self.selected = max(0, min(self.selected, len(self.rows) - 1))
        else:
            self.selected = 0
        self._render_header()
        self._render_list(groups)
        self._render_detail()
        self._render_footer()

    def _render_header(self):
        counts = self.model.get("counts", {})
        active = FILTERS[self.filter_index]
        segments = [
            ("needs-input", counts.get("needs_you", 0), "needs you", RED),
            ("working", counts.get("working", 0), "working", BLUE),
            ("idle", counts.get("idle", 0), "idle", DIM),
        ]

        right = Text()
        for i, (state, n, label, color) in enumerate(segments):
            if i:
                right.append("  ·  ", style=FAINT)
            faded = active is not None and active != state
            style = color if not faded else FAINT
            right.append(GLYPH[state] + " ", style=style)
            right.append(
                "%d %s" % (n, label),
                style=("bold " + style) if state != "idle" else style,
            )

        title = Text("agents", style="bold %s" % BRIGHT)
        # #header has 2 cells of padding on each side.
        room = max(1, self.size.width - 4 - title.cell_len - right.cell_len)
        line = Text.assemble(title, " " * room, right)
        self.query_one("#header", Static).update(line)

    def _list_width(self):
        """Usable cells inside the left column, minus its padding."""
        width = self.query_one("#left").size.width
        return max(24, width - 3)

    def _row_text(self, session, is_selected):
        state = session["state"]
        color = COLOR[state]
        needs = state == "needs-input"

        bar = "▌ " if needs else "  "
        bar_style = RED if needs else ""

        text = Text()
        text.append(bar, style=bar_style)
        text.append(GLYPH[state] + " ", style=color)

        name_style = "bold %s" % (BRIGHT if state != "no-agent" else FAINT)
        text.append(session["project"], style=name_style)

        if session["branch"]:
            text.append(" " + session["branch"], style=FAINT)
        elif state == "no-agent":
            text.append(" — no agent open", style=FAINT)

        if session["session_id"] in self.pins:
            text.append(" ▪", style=DIM)

        elapsed = elapsed_label(session["elapsed_seconds"])
        if elapsed:
            right = elapsed + (" ⏎" if is_selected else "  ")
            gap = max(1, self._list_width() - text.cell_len - len(right))
            text.append(" " * gap)
            text.append(right, style=("bold " + color) if needs else DIM)
        return text

    def _render_list(self, groups):
        body = Text()
        index = 0
        for gi, (label, members) in enumerate(groups):
            if gi:
                body.append("\n")
            body.append(label + "\n", style=FAINT)
            for session in members:
                is_selected = index == self.selected
                row = self._row_text(session, is_selected)
                needs = session["state"] == "needs-input"
                if is_selected:
                    row.stylize("on #2a2a2a" if not needs else "on #2e1a1a")
                elif needs:
                    row.stylize("on #211414")
                body.append(row)
                body.append("\n")

                subtitle = session.get("subtitle")
                if subtitle:
                    room = max(10, self._list_width() - 6)
                    sub = Text()
                    sub.append("    " if not needs else "▌   ", style=RED if needs else "")
                    sub.append(self._clip(subtitle, room), style=DIM)
                    if needs:
                        sub.stylize("on #2e1a1a" if is_selected else "on #211414")
                    body.append(sub)
                    body.append("\n")
                index += 1
        if not self.rows:
            body.append("\nno sessions\n", style=FAINT)
        self.query_one("#list", SessionList).update(body)

    def _render_detail(self):
        detail = self.query_one("#detail", DetailPane)
        if not self.rows:
            detail.update(Text("nothing selected", style=FAINT))
            return
        s = self.rows[self.selected]
        state = s["state"]
        color = COLOR[state]

        out = Text()
        out.append("SELECTED\n\n", style=FAINT)
        out.append(s["project"], style="bold %s" % BRIGHT)
        if s["branch"]:
            out.append(" / ", style=FAINT)
            out.append(s["branch"], style=DIM)
        out.append("\n\n")

        status = {
            "needs-input": "waiting on your reply",
            "working": "working",
            "idle": "idle",
            "no-agent": "no agent open",
        }[state]
        bar = Text()
        bar.append("▌ ", style=color)
        bar.append(status, style="bold %s" % color if state != "idle" else color)
        if s["elapsed_seconds"] is not None:
            bar.append(" · elapsed %s" % long_elapsed(s["elapsed_seconds"]), style=DIM)
        if state == "needs-input":
            bar.stylize("on #211414")
        out.append(bar)
        out.append("\n\n")

        message = s.get("last_assistant_message")
        if message:
            out.append("last message\n", style=FAINT)
            out.append('"%s"\n\n' % self._clip(strip_markdown(message), 300), style=BRIGHT)

        files = s.get("files_touched") or []
        if files:
            out.append("files touched\n", style=FAINT)
            for entry in files:
                mark = entry["change"]
                out.append(mark + " ", style=ADDED if mark == "+" else MODIFIED)
                out.append(entry["path"] + "\n", style=ADDED if mark == "+" else MODIFIED)
            out.append("\n")

        if state != "no-agent":
            out.append("enter runs\n", style=FAINT)
            out.append(self.jump_command(s) + "\n", style=DIM)

        detail.update(out)

    @staticmethod
    def _clip(text, limit):
        text = " ".join(text.split())
        return text if len(text) <= limit else text[: limit - 1] + "…"

    def _render_footer(self):
        line = Text()
        keys = [
            ("↑↓/jk", "move"),
            ("⏎", "jump to session"),
            ("p", "pin"),
            ("tab", "filter"),
            ("r", "reload"),
            ("q", "quit"),
        ]
        for i, (key, label) in enumerate(keys):
            if i:
                line.append("  ·  ", style="#3a3a3a")
            line.append(key + " ", style=DIM)
            line.append(label, style=FAINT)
        active = FILTERS[self.filter_index]
        if active:
            line.append("   [filter: %s]" % active, style=COLOR[active])
        if self.notice:
            line.append("   " + self.notice, style=BLUE)
        self.query_one("#footer", Static).update(line)

    # ---------- actions ----------

    def action_cursor_up(self):
        if self.rows:
            self.selected = (self.selected - 1) % len(self.rows)
            self.render_all()

    def action_cursor_down(self):
        if self.rows:
            self.selected = (self.selected + 1) % len(self.rows)
            self.render_all()

    def action_cycle_filter(self):
        self.filter_index = (self.filter_index + 1) % len(FILTERS)
        self.selected = 0
        self.render_all()

    def action_reload(self):
        self.reload_model()

    def action_pin(self):
        if not self.rows:
            return
        sid = self.rows[self.selected]["session_id"]
        self.pins.symmetric_difference_update({sid})
        save_pins(self.pins)
        self.render_all()

    @staticmethod
    def jump_command(session):
        """The shell command that opens this session."""
        if session["state"] == "no-agent":
            return "claude"
        if session.get("short_id"):  # background session, hosted by the supervisor
            return "claude attach %s" % session["short_id"]
        return "claude -r %s" % session["session_id"]

    def _kitty_tabs(self):
        listing = subprocess.run(
            ["kitty", "@", "ls"], capture_output=True, text=True, timeout=2
        )
        return json.loads(listing.stdout or "[]")

    def _find_tab(self, session):
        """Tab id already showing this session, or None. Never our own window."""
        try:
            me = int(os.environ.get("KITTY_WINDOW_ID", "-1"))
        except ValueError:
            me = -1
        path = (session.get("project_path") or "").rstrip("/")
        sid = session.get("session_id") or ""
        short = session.get("short_id") or ""

        exact = fallback = None
        for os_window in self._kitty_tabs():
            for tab in os_window.get("tabs", []):
                for window in tab.get("windows", []):
                    if window.get("id") == me:
                        continue  # the dashboard's own tab
                    cmdline = " ".join(window.get("cmdline") or [])
                    if "ccmon" in cmdline:
                        continue
                    if (sid and sid in cmdline) or (short and short in cmdline):
                        exact = tab["id"]
                    elif (
                        fallback is None
                        and path
                        and (window.get("cwd") or "").rstrip("/") == path
                        and "claude" in cmdline
                    ):
                        fallback = tab["id"]
        return exact or fallback

    def action_jump(self):
        """Focus the session's existing kitty tab, else open it in a NEW tab."""
        if not self.rows:
            return
        session = self.rows[self.selected]
        command = self.jump_command(session)
        path = session.get("project_path") or HOME

        if not os.environ.get("KITTY_LISTEN_ON"):
            try:
                subprocess.run(["pbcopy"], input=command, text=True, timeout=2)
                self._flash("copied: %s" % command)
            except Exception:
                self._flash(command)
            return

        try:
            existing = self._find_tab(session)
            if existing is not None:
                subprocess.run(
                    ["kitty", "@", "focus-tab", "--match", "id:%s" % existing],
                    capture_output=True,
                    timeout=2,
                )
                self._flash("jumped to %s" % session["project"])
                return

            subprocess.run(
                [
                    "kitty", "@", "launch",
                    "--type=tab",
                    "--tab-title", session["project"],
                    "--cwd", path,
                    "zsh", "-ic", command,
                ],
                capture_output=True,
                timeout=5,
            )
            self._flash("opened %s in a new tab" % session["project"])
        except Exception as exc:
            self._flash("could not jump: %s" % exc)

    def _flash(self, message):
        self.notice = message
        self._render_footer()
        self.set_timer(3.0, self._clear_notice)

    def _clear_notice(self):
        self.notice = ""
        self._render_footer()


def main():
    # Without a terminal, Textual's driver spins and burns a core. Refuse.
    if not sys.stdout.isatty():
        sys.stderr.write(
            "ccmon needs a terminal. For scriptable output use:\n"
            "  python3 %s\n" % os.path.join(os.path.dirname(__file__), "parse_sessions.py")
        )
        raise SystemExit(1)
    CCMon().run()


if __name__ == "__main__":
    main()
