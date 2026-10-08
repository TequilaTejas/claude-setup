---
name: onething-app
description: "OneThing — Tejas's native macOS single-task focus app at ~/projects/onething (Swift/SPM, menu bar)"
metadata: 
  node_type: memory
  type: project
  originSessionId: fc2c2b6c-947d-4b4b-80ab-ba9bd3bd6165
---

Tejas has ADHD and built (2026-07-06) **OneThing**, a native macOS focus app at `~/projects/onething`. Swift Package Manager + SwiftUI/AppKit, no Xcode project; `./build.sh` assembles `build/OneThing.app` (ad-hoc signed, LSUIElement menu-bar app).

Key product decisions he chose: sessions are **task-completion based, not timer based**; blocking is a mix of firm and hard — giving up requires retyping the task verbatim; web blocking uses **both** browser tab-watching (AppleScript, 2s poll) and optional "ironclad" /etc/hosts mode.

Related: [[tejas-profile]]
