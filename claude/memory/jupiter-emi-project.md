---
name: jupiter-emi-project
description: "Jupiter Money overdue-EMI assistant design at ~/projects/jupiter-emi; approved home base saved, intervention entry being designed via crazy-four rounds"
metadata: 
  node_type: memory
  type: project
  originSessionId: 189580db-1c2e-4e80-bd41-a687c5d527be
  modified: 2026-08-09T03:58:09.275Z
---

Design exploration (started 7 Aug 2026): AI assistant for an overdue EMI inside a Jupiter Money-style super app. User Priya, ₹4,500 EMI due 3 Aug + ₹90 fee, 14 of 24 paid on time. Approved base: super-app home screen at ~/projects/jupiter-emi/home-base (React UMD + Tailwind CDN + esbuild-compiled app.jsx, no Babel; serve with http.server and open in Dia).

Locked design decisions from earlier rounds (two full variant generations were scrapped):
- Info hierarchy at the fact moment: ₹4,590 hero, days-overdue chip, breakdown line, two protective rows (fee grows daily; nothing on credit report until 30 days, 2 Sep)
- Pay dominant; reschedule (5-day limit visible) and hardship pause behind progressive disclosure
- Checking shown as prompt-kit-style chain-of-thought (named steps, streamed items that stay readable), never a spinner
- Human help resolves LIVE in-app (Anita, "here now", quick-reply chips, resolution card, zero waiting language); a pure chat-thread approach as the whole intervention was REJECTED
- Copy: no exclamation marks/emoji/em dashes, dates "8 Aug", never shaming; coral #E14A28 single accent
- Present one flow at a time; Replay-only chrome, no jump-pill clutter
- ENTRY (picked 8 Aug 2026): inline card expansion — the "Needs attention" card FLIPs from its row to a CENTERED card over a 35% scrim, auto-fires once at 1.4s; slightly rigid: no scrim-dismiss (shake nudge instead), only exits are filled "Pay ₹4,590" and ghost "I can't pay right now". Rejected entries: assistant ribbon, peek sheet, plain arrival-moment modal

HARD RULE (8 Aug 2026): never report back on this project without first verifying the change in a real browser (Playwright MCP or headless script — click the actual path, screenshot, eyeball). Report only what was seen working.

Serving (9 Aug 2026): detached nohup http.servers from the DURABLE copies — prototype http://localhost:8654/ from ~/projects/jupiter-emi/entry-inline, wireframe board http://localhost:8655/ from ~/projects/jupiter-emi/wireframes. Edit files in ~/projects (not scratchpad), recompile there with esbuild. Session-background servers get killed on session end; use nohup+disown. Port 8656 is squatted by an old server from another session; do not reuse it.

FLAGSHIP BUILD (9 Aug 2026, evening): full production prototype at ~/projects/jupiter-emi/flagship (vanilla HTML/CSS/JS, no build step), served at http://localhost:8657/. Visual language from root DESIGN.md (Wise analysis: lime #9fe870 CTA, ink #0e0f0c, sage #e8ebe6 canvas, Inter-900 display, 24px radii; dark ink+lime reserved for Jupiter Trust, Anita, and the dock). Covers every flow of the brief: home 4 write-back states, chooser, 5-day date strip (past disabled, today default, far dates route to authority screen), pause 1/2/3 with 3 Oct/Nov/Dec, Anita session (handover ticks → live presence header → reason chips incl. silent prefer-not-to-say → consent approve/decline → watchable checks coherent with verdict → outcome panels), approve/partial/reject × pause+far, partial returns to thread with history, reject offers instant reschedule + care, success receipts FLIP back into the home loan card. Demo rail: Anita-decision segment (approve/partial/decline) + replay. Numbers per final brief: fee ₹300 (not ₹90), overdue ₹4,500, score 823, counter-offer 22 Aug.

SURFACE PIVOT (9 Aug 2026, later): Tejas rejected the centered-popup/modal entry. Now a FULL-SCREEN assistant surface that FLIP-expands from the loan card, with a persistent BOTTOM DOCK (dark ink bar, radius 26) that is the assistant's own element: lime status line (spark icon, or live dot while Anita reviews), all primary actions, and Anita's reply chips live in the dock; content states morph above it; header carries back/eyebrow → Anita presence. No scrim, no shake nudge anymore. Engine: delegated click handler on #phone — data-act MUST be dispatched before data-day/data-months (seal buttons carry both; wrong order re-routes confirms to the date picker; this bug was hit and fixed). All paths re-verified with Playwright after the pivot; zero console errors.

Related: [[crazy-four-skill]], [[model-split-build-vs-plan]], [[previews-in-dia]], [[verify-visual-output]].

RM NAME CHANGE (10 Aug 2026): "Anita" is retired. The relationship manager in the entry-inline build is now "Meera". Older builds (flagship 8657) may still say Anita. Global copy rule [[no-names-before-join]] applies: no name until the join event. Chat status label is "Active" (not "here now"). Chat thread is resumable via module-level CHAT_CACHE; "Continue chatting with Meera" resumes the original thread and offers "Back to the offer".

LIVE LINK (10 Aug 2026): public repo TequilaTejas/jupiter-emi, branch Fable5-designs, GitHub Pages from /docs → https://tequilatejas.github.io/jupiter-emi/ (snapshot of entry-inline; re-copy entry-inline/* to docs/ and push to refresh). Local canon remains http://localhost:8654/ served from entry-inline/.
