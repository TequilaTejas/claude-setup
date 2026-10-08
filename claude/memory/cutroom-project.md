---
name: cutroom-project
description: "Cutroom at ~/projects/cutroom — agentic IG-reels cutting room; pipeline v2 with 4 craft stages, every review a video opened in QuickTime, Sonnet execution agents"
metadata: 
  node_type: memory
  type: project
  originSessionId: afb04a45-76fe-435c-a591-330288ddd8da
  modified: 2026-07-30T22:09:52.972Z
---

Tejas is building **Cutroom** (`~/projects/cutroom`), an agentic cutting room for Instagram reels, scaffolded 2026-07-10. He shoots camera footage (sometimes with a script) and wants reels in the style of reference reels he likes (specs in `style/specs/`, favorite: Chalchitra Talks violet-pill system). Free tools only, no paid services.

Architecture (pipeline v2, redesigned by Tejas 2026-07-10 after disliking the first AIB draft): main Claude session is the director; subagents in `.claude/agents/` (ingest, rough-cutter, asset-researcher, visual-designer, caption-designer, sound-designer, qc-reviewer, style-analyst, retro), all pinned `model: sonnet` — execution on Sonnet, direction on the session model. Agents write decisions as data; deterministic tools in `tools/` execute (ffmpeg, faster-whisper, PySceneDetect, Pillow, via `uv run` with PEP 723 inline deps). Nothing renders except `tools/render.py` from a schema-valid `workspace/edl.json`; clip start times come from `render.py --timeline` (transitions overlap clips).

Four craft stages, each gated by Tejas WATCHING VIDEO (always `open` the draft in QuickTime — never gate on paper artifacts like beat sheets or EDL tables): (1) rough story cut with filler words removed and every sentence clean, (2) assets found free and placed unstyled, (3) all visual styling — color, lighting, pip backgrounds, transitions, 1–2 word captions (his stated preference) with typography exploration, (4) sound design — voice cleaned with very subtle depth, music, SFX, level matching. Self-improvement: notes per project in `notes.md`, retro promotes patterns into `LEARNINGS.md` and proposes agent diffs (his approval); goldens in `evals/`. First project `bring-back-aib` is ON HOLD after the redesign.

Series intro: `projects/maximalist-intro/exports/maximalist-intro-3s-final.mp4` is the APPROVED 3.0s IBGP series intro (2026-07-31; 1080x1920 HLG, instrumental jingle). Toolchain: workspace `intro-3s.html` → `render_frames_3s.py` → ffmpeg asset → `edl-3s.json` → `tools/render.py`. TTS voiceover was tried (edge-tts Prabhat, macOS Rishi) and firmly rejected — don't propose free-TTS VO again.

Gotchas: Homebrew ffmpeg 8.x is minimal — no `drawtext`/`ass`/`fifo` filters; captions are Pillow PNGs composited via `overlay`. ffmpeg's scheduler deadlocks on xfade graphs unless every input gets `-thread_queue_size 4096`, and flat-color pip backgrounds must use `pad` (a lavfi color source feeding xfade deadlocks). Whisper needs `large-v3` for Hinglish. Related: [[tejas-profile]], [[ascii-orchestration-diagrams]].
