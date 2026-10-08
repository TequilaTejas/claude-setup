---
name: ride-scheduler-redesign
description: "Ride-scheduling picker redesign exploration — arrive-by planner concept won over slot grid; files in session scratchpad, served on port 8647"
metadata: 
  node_type: memory
  type: project
  originSessionId: 26dedaf2-46b3-4306-9d0a-d024a01d2e95
  modified: 2026-07-28T14:59:01.675Z
---

Tejas is redesigning a "Schedule your ride" screen (Rapido-style, yellow accent) as a craft exercise, started July 28, 2026. Deep research (5 parallel sweeps) fed a token system: warm neutrals, dark ink on yellow (yellow-on-white fails contrast 1.79:1), tabular-nums everywhere, 4pt spacing, hairline borders, Motion/layoutId-style springs, NumberFlow digit rolls.

Product direction he liked: **the arrive-by planner** — book the arrival, not the pickup; pickup time is the system's output. Draggable ride block on a traffic-heat timeline, odds-based verdicts ("on time 9 of 10 days"), CTA "Lock it — arrive by 10:30". Four variants explored: A uncertainty cone, B vertical calendar drop, C confidence dial (pick odds, system picks time), D three quotes (safe/recommended/last call with honest peak pricing).

Prototype files (session scratchpad, ephemeral — copy out if project continues): ride-craft/{index,screens,rethink,explore}.html, served via python http.server on **port 8647**, opened in Dia. Research synthesis doc is index.html.
