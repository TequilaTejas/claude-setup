---
name: verify-visual-output
description: "Always render and visually inspect compressed/converted files (PDFs, images) before delivering — Tejas called out an unchecked ugly result"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b0c81fe2-1895-4ac2-b135-06ecde807682
  modified: 2026-07-31T16:31:06.181Z
---

When compressing or converting visual files (PDFs, images), render the output and compare it against the original side by side before saving to the user's folders.

**Why:** Delivered a Ghostscript-compressed resume without looking at it; the profile photo came out dark and muddy (blind downsampling + stripped ICC profile). Tejas was rightly annoyed ("have you checked how shit it looks?").

**How to apply:** Render before/after crops at 300 dpi with gs → PNG, Read them, compare. For PDFs prefer targeted per-image recompression with pikepdf (keep vector text and original /ColorSpace ICC profiles) over blanket Ghostscript presets.
