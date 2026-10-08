---
name: tejas-intro-page
description: "Scroll-driven self-intro at ~/projects/tejas-intro; v4 (faithful zero.university visual system: green mat, serif+green script, UI cards, board footer) is current; v1/v2/v3 kept"
metadata: 
  node_type: memory
  type: project
  originSessionId: 9f7cfdf9-f201-429e-a88d-1126903dfdde
---

Tejas's scroll-driven self-introduction page. Current version (v4, built 2026-07-13 after he asked to "retry entirely from scratch using zero.university's visual design references"): a faithful transplant of zero.university's visual system onto his verbatim copy, at `~/projects/tejas-intro/index.html`. Their grammar, his story: green cutting-mat hero (#35855c, grid + edge numbers + warning triangle) with a white paper sheet ("Hi, I'm *Tejas.*" serif + green Great Vibes script), desk props (sticky note, stamped envelopes), swaying leaf shadows, SCROLL pill, persistent docked pill nav (spiral orb + dark "The work" pill + menu orb, zero's Join-Beta pattern); careers-style ruled list (mono index numbers + serif roles) struck through in green pen; "half the truth" on a floating white UI card that swings to 45°; role-sheet mask peel; growth items as white pill cards descending the mat; mat grid rotates 90° at "turned the axis"; horizontal travel past zero-style job-brief cards (gradient logo-dot, mono place tag, serif sentence, colored-dot chips echoing copy words) over a soft mint sky; question as giant green script; page-curl into dark green graph-board footer (#1b3a27) with white CTA pill ("tejasdua.com | The work") and drawn light-green arrows.

Fonts: Newsreader / Great Vibes / Caveat / IBM Plex Mono. Stack: single static HTML, GSAP ScrollTrigger + Lenis CDN; reduced-motion/no-JS = static document. Preview port 8644. Gotchas hit: (1) `.mat .p-small` pale color leaked onto text sitting on white sheets inside mat sections — needed `.sheet/.uicard` overrides; (2) relative gsap `rotation:'+=n'` tweens + invalidateOnRefresh compound on every refresh — cards drifted to ±15°, use absolute fromTo or static CSS. Lesson: WebFetch can't see JS-rendered sites — render refs in headless Chromium (playwright-core + cached ms-playwright binary) and screenshot the scroll.

Older versions kept: `v1-film.html` (b/w film + blue pen), `v2-axis.html` (dark+orange axis concept, rejected), `v3-desk.html` (cream desk + ballpoint blue, superseded by the faithful-to-ref v4). Artifact preview of v1: https://claude.ai/code/artifact/95c85299-0771-4113-9fc8-627aea14e6ee.

Testing trick that worked: playwright-core (npm, no browser download) driving the cached `~/Library/Caches/ms-playwright/chromium_headless_shell-*` binary for scroll-position screenshots; plain `--screenshot` headless can't exercise ScrollTrigger. No Chrome on this Mac (Arc/Dia/Safari only).

Likely destination: part of [[tejasdua-com-site]] / [[portfolio-project]] as the intro before case studies.
