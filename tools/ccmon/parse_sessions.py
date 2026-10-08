#!/usr/bin/env python3
"""
Read-only extraction of the Claude Code session model.

Reads, never writes:
  ~/.claude/projects/<encoded-cwd>/<session-id>.jsonl   transcripts
  ~/.claude/jobs/<short-id>/state.json                  authoritative bg state

Deliberately does NOT shell out to `claude agents --json`: that command can
spawn the supervisor daemon, which is a state change. Everything here is a
plain file read.

Transcripts reach tens of MB, so we read a bounded tail rather than the whole
file, and walk the records backward.
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
PROJECTS_DIR = os.path.join(HOME, ".claude", "projects")
JOBS_DIR = os.path.join(HOME, ".claude", "jobs")
WORKSPACE = os.path.join(HOME, "projects")

TAIL_BYTES = 512 * 1024       # enough for recent turns on any real session
IDLE_AFTER_SECONDS = 15 * 60  # interactive session untouched this long => idle
STALE_AFTER_SECONDS = 24 * 60 * 60  # older than this: hide from the live view

# Records that carry a timestamp but say nothing about what the agent is doing.
NOISE_TYPES = {"attachment", "file-history-snapshot", "queue-operation"}

# A turn that ended writes one of these; the agent is then awaiting a prompt.
TURN_END_SUBTYPES = {"turn_duration", "stop_hook_summary", "away_summary"}

# Terminal job states -> our three-state model.
JOB_STATE_MAP = {
    "blocked": "needs-input",
    "working": "working",
    "done": "idle",
    "failed": "idle",
    "stopped": "idle",
}


def read_tail_records(path, tail_bytes=TAIL_BYTES):
    """Return parsed JSON records from the tail of a .jsonl file."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return []
    with open(path, "rb") as fh:
        if size > tail_bytes:
            fh.seek(size - tail_bytes)
            fh.readline()  # discard the partial first line
        blob = fh.read()
    text = blob.decode("utf-8", errors="replace")
    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return records


def parse_ts(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def content_blocks(rec):
    msg = rec.get("message")
    if not isinstance(msg, dict):
        return []
    content = msg.get("content")
    if isinstance(content, list):
        return [b for b in content if isinstance(b, dict)]
    return []


def short_path(file_path, project_path):
    if not file_path:
        return None
    if project_path and file_path.startswith(project_path + os.sep):
        return file_path[len(project_path) + 1:]
    return file_path.replace(HOME, "~", 1)


def describe_activity(tool_name, tool_input, project_path):
    """One dim line: what the agent last actually did."""
    tool_input = tool_input or {}
    if tool_name == "Bash":
        desc = tool_input.get("description") or tool_input.get("command") or ""
        desc = " ".join(desc.split())
        return "running " + desc[:60] if desc else "running a command"
    if tool_name in ("Edit", "Write", "NotebookEdit"):
        target = short_path(tool_input.get("file_path"), project_path)
        return "editing " + target if target else "editing a file"
    if tool_name == "Read":
        target = short_path(tool_input.get("file_path"), project_path)
        return "reading " + target if target else "reading a file"
    if tool_name in ("Grep", "Glob"):
        return "searching " + str(tool_input.get("pattern") or tool_input.get("query") or "")[:50]
    if tool_name == "WebFetch":
        url = str(tool_input.get("url") or "")
        host = url.split("//")[-1].split("/")[0]
        return "fetching " + host if host else "fetching a page"
    if tool_name == "WebSearch":
        return "searching the web"
    if tool_name == "Agent":
        return "delegating " + str(tool_input.get("description") or "")[:50]
    if tool_name:
        return tool_name.lower()
    return None


def files_touched_from(rec, project_path):
    """(+ created / ~ modified) from a tool result. Reads are not 'touched'."""
    result = rec.get("toolUseResult")
    if not isinstance(result, dict):
        return []
    rtype = result.get("type")
    path = result.get("filePath")
    if rtype == "create" and path:
        return [("+", short_path(path, project_path))]
    if rtype == "update" and path:
        return [("~", short_path(path, project_path))]
    # Edit results carry no `type` but do carry a patch.
    if path and "structuredPatch" in result:
        return [("~", short_path(path, project_path))]
    return []


def load_jobs():
    """Authoritative state for background sessions, keyed by full sessionId."""
    jobs = {}
    if not os.path.isdir(JOBS_DIR):
        return jobs
    for entry in sorted(os.listdir(JOBS_DIR)):
        state_file = os.path.join(JOBS_DIR, entry, "state.json")
        if not os.path.isfile(state_file):
            continue
        try:
            with open(state_file) as fh:
                data = json.load(fh)
        except (OSError, ValueError):
            continue
        sid = data.get("sessionId")
        if sid:
            data["_short_id"] = entry
            jobs[sid] = data
    return jobs


def elapsed_label(seconds):
    """Compact elapsed time: 24s, 3m, 1h, 2d."""
    if seconds is None:
        return None
    if seconds < 60:
        return "%ds" % seconds
    if seconds < 3600:
        return "%dm" % (seconds // 60)
    if seconds < 86400:
        return "%dh" % (seconds // 3600)
    return "%dd" % (seconds // 86400)


def is_worktree(path):
    return "-wt-" in path or "/.claude/worktrees/" in path


def display_name(cwd):
    if not cwd:
        return "unknown"
    if cwd.rstrip("/") == HOME:
        return "~"
    return os.path.basename(cwd.rstrip("/"))


def parse_session(path, jobs, now):
    records = read_tail_records(path)
    if not records:
        return None

    session_id = os.path.basename(path)[: -len(".jsonl")]

    cwd = branch = kind = version = None
    last_ts = None
    last_assistant_text = None
    last_activity = None
    files = []
    seen_files = set()
    last_meaningful = None  # (type, subtype) of the newest non-noise record

    for rec in records:
        cwd = rec.get("cwd") or cwd
        branch = rec.get("gitBranch") or branch
        kind = rec.get("sessionKind") or kind
        version = rec.get("version") or version
        ts = parse_ts(rec.get("timestamp"))
        if not ts:
            continue  # trailing metadata (ai-title, mode, ...) carries no time
        if last_ts is None or ts > last_ts:
            last_ts = ts
        if rec.get("type") not in NOISE_TYPES:
            last_meaningful = (rec.get("type"), rec.get("subtype"))

    # `gitBranch` is "HEAD" when the cwd isn't a real repo (e.g. $HOME).
    if branch == "HEAD":
        branch = None

    project_path = cwd or ""

    # Second pass now that project_path is known (for relative file paths).
    for rec in records:
        rtype = rec.get("type")
        if rtype == "assistant":
            for block in content_blocks(rec):
                if block.get("type") == "text":
                    text = (block.get("text") or "").strip()
                    if text:
                        last_assistant_text = text
                elif block.get("type") == "tool_use":
                    activity = describe_activity(
                        block.get("name"), block.get("input"), project_path
                    )
                    if activity:
                        last_activity = activity
        elif rtype == "user":
            for change, fpath in files_touched_from(rec, project_path):
                if fpath and fpath not in seen_files:
                    seen_files.add(fpath)
                    files.append({"change": change, "path": fpath})

    job = jobs.get(session_id)
    asking = None
    title = None
    detail = None
    state_since = last_ts

    if job:
        raw_state = job.get("state")
        state = JOB_STATE_MAP.get(raw_state, "idle")
        title = job.get("name")
        detail = job.get("detail")
        if state == "needs-input":
            asking = job.get("needs")
        job_ts = parse_ts(job.get("updatedAt"))
        if job_ts:
            state_since = job_ts
        kind = kind or "bg"
    else:
        # Interactive session: no state file, so infer from the transcript.
        # A completed turn appends a `system/turn_duration` record; anything
        # else newer means the agent is still mid-turn.
        age = (now - last_ts).total_seconds() if last_ts else float("inf")
        mtype, msubtype = last_meaningful or (None, None)
        turn_ended = mtype == "system" and msubtype in TURN_END_SUBTYPES
        if not turn_ended and age < IDLE_AFTER_SECONDS:
            state = "working"
        else:
            state = "idle"
        kind = kind or "interactive"

    last_change = state_since or last_ts
    elapsed = int((now - last_change).total_seconds()) if last_change else None
    age_seconds = int((now - last_ts).total_seconds()) if last_ts else None
    stale = age_seconds is not None and age_seconds > STALE_AFTER_SECONDS

    # The one dim line under an active row. Idle rows get nothing — no filler.
    if state == "needs-input":
        last_activity = None
        subtitle = "asking: %s" % asking if asking else "waiting on your reply"
    elif state == "working":
        subtitle = last_activity
    else:
        last_activity = None
        subtitle = None

    return {
        "session_id": session_id,
        "short_id": (job or {}).get("_short_id"),
        "project": display_name(cwd),
        "project_path": cwd,
        "branch": branch,
        "is_worktree": is_worktree(cwd or ""),
        "kind": kind,
        "state": state,
        "stale": stale,
        "state_since": last_change.isoformat() if last_change else None,
        "elapsed_seconds": elapsed,
        "elapsed_label": elapsed_label(elapsed),
        "subtitle": subtitle,
        "last_activity": last_activity,
        "last_change": last_ts.isoformat() if last_ts else None,
        "last_assistant_message": last_assistant_text,
        "asking": asking,
        "title": title,
        "detail": detail,
        "files_touched": files[-12:],
        "cli_version": version,
        "resume_cmd": "claude -r %s" % session_id,
        "transcript": path,
    }


def projects_without_agents(sessions):
    """Real git repos under ~/projects that have no session at all."""
    active = {s["project_path"] for s in sessions if s["project_path"]}
    orphans = []
    if not os.path.isdir(WORKSPACE):
        return orphans
    for entry in sorted(os.listdir(WORKSPACE)):
        path = os.path.join(WORKSPACE, entry)
        if not os.path.isdir(path):
            continue
        if not os.path.isdir(os.path.join(path, ".git")):
            continue
        if path not in active:
            orphans.append({"project": entry, "project_path": path, "state": "no-agent"})
    return orphans


def build_model(show_all=False):
    """The whole session model. Pure reads; safe to call on every file event."""
    now = datetime.now(timezone.utc)
    jobs = load_jobs()

    sessions = []
    if os.path.isdir(PROJECTS_DIR):
        for proj in sorted(os.listdir(PROJECTS_DIR)):
            proj_dir = os.path.join(PROJECTS_DIR, proj)
            if not os.path.isdir(proj_dir):
                continue
            for name in sorted(os.listdir(proj_dir)):
                if not name.endswith(".jsonl"):
                    continue
                parsed = parse_session(os.path.join(proj_dir, name), jobs, now)
                if parsed:
                    sessions.append(parsed)

    if not show_all:
        # A needs-input session always stays visible, however old it is.
        sessions = [s for s in sessions if not s["stale"] or s["state"] == "needs-input"]

    # needs-you first, then working, then idle; most-recent change first.
    order = {"needs-input": 0, "working": 1, "idle": 2}
    sessions.sort(
        key=lambda s: (order.get(s["state"], 3), s["elapsed_seconds"] or 1 << 30)
    )

    counts = {
        "needs_you": sum(1 for s in sessions if s["state"] == "needs-input"),
        "working": sum(1 for s in sessions if s["state"] == "working"),
        "idle": sum(1 for s in sessions if s["state"] == "idle"),
    }

    return {
        "generated_at": now.isoformat(),
        "counts": counts,
        "sessions": sessions,
        "projects_without_agents": projects_without_agents(sessions),
    }


def main():
    model = build_model(show_all="--all" in sys.argv)
    json.dump(model, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
