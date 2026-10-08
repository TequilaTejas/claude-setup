---
name: portfolio-project
description: "Tejas's personal portfolio site — private repo TequilaTejas/portfolio, Next.js, minimal /life-style aesthetic"
metadata: 
  node_type: memory
  type: project
  originSessionId: 93f6f515-44c9-4f0d-82ac-d6fd0327198f
---

Personal portfolio at `~/portfolio` (private repo github.com/TequilaTejas/portfolio), started 2026-07-03. Next.js 15 + Tailwind v4 + Framer Motion. Design direction settled on the quiet Codrops-demo aesthetic (small 0.875rem letter-spaced type, #111 on white, corner-anchored chrome, masked line reveals, `.link-line` underline wipe) — Tejas explicitly rejected the earlier bold PhonePe-style landing as "too much". `/life` is an immersive WebGPU gallery (people, travel, his doggo) adapted from bnpne/page-transitions-with-webgpu-vanilla-js (MIT, attributed); its photos are Unsplash placeholders awaiting his real ones, content in `lib/life/content.js`.

**Why:** he loves this minimal style — keep future additions in that language, not loud/colorful.

`/franky` (added 2026-07-09) is a memorial page for his dog Franky — light-themed infinite draggable canvas (he explicitly asked to keep the site's light theme; no dark pages) (Codrops Infinite Canvas by Edoardo Lunardi, MIT, ported to R3F without drei in `lib/franky/`), text "Designing in memory of Franky.", spatial Web Audio (HRTF-panned dog clips + brown-noise bed, unlocked by the Enter click). Not yet linked from any nav — Tejas deferred the route/navigation decision.

Interactive case study v1 at `/work/presentations-ai` (added 2026-07-09): doc-style layout modeled on prompt-kit.com docs (numbered scroll-tracking side nav, Demo frames with Preview/Notes tabs in `components/study/`), three playable placeholder demos (prompt→outline, theme engine, before/after layout slider). All prose is placeholder — real content lives in his Figma file "Case study - Presentations.ai" (Dn2YkB3ynSZ6NNbOMThUO2); he wants that storytelling kept as-is, lightly adapted. Figma MCP was disconnected when built — needs reconnecting or exported content to fill in.

`/story` (2026-07-11) is an interview piece, deliberately NOT part of the portfolio site (no nav links to/from it) — a six-scene GSAP scrollytelling intro that alternates all-white/all-black themes (his explicit ask; the one sanctioned exception to the light-theme rule). Effects: SplitText char scatter, word reveal, scrubbed counter + marquee, ScrambleText, typewriter, sentence assembly ("I design products people actually use."). Lenis + pointer parallax. Theme flip is rect-based (viewport-center test), because ScrollTrigger range-based toggles desync under pinning.

**How to apply:** placeholders still to replace: project list links (`#`), highlight lines, Hotstar/Navi years, LinkedIn URL, /life photos + stories, /franky photos (Unsplash golden retrievers in `public/franky/photos/`, manifest in `lib/franky/content.ts`). Card-visuals idea (SVG or ChatGPT-generated) is parked. See [[tejas-profile]].
