---
name: emi-success-screen
description: "EMI payment states prototype at ~/projects/emi-success; LIVE at tequilatejas.github.io/emi-success (TequilaTejas/emi-success), port 8650 local"
metadata: 
  node_type: memory
  type: project
  originSessionId: 2d3d8cdf-33b2-4358-9666-416c9fab238b
  modified: 2026-08-10T01:42:03.568Z
---

EMI payment success screen ("Lightfall" direction, picked over Receipt Rise / Orbit Ledger / Passbook Flip via [[crazy-four-skill]]). Single file `~/projects/emi-success/index.html`, preview `python3 -m http.server 8650` + `open -a "Dia"`.

Locked decisions (as of 10 Aug 2026):
- Clean/slick over decorative: cream + ink + one green (#0e7a41), gold dust particles only. Tejas rejected the first busier version ("NOT GOOD, MAKE IT CLEAN AND MORE SLICK").
- Hero background = "aurora" gradient (deep color fading to cream, grain + drifting glow, white hero text, white tick) after Tejas called the flat cream "bland". 3 preview themes via top-right dots: fern green (default), dawn amber, ink navy; pick one and remove the switcher before shipping.
- No share/receipt button; single "Done" CTA.
- Calendar = 24-month oval-chip carousel (Journey-app reference style), NOT a day-grid month view; paid months get pop-in green checks, current month is the big black chip.
- Data: ₹12,500 EMI, 5/24 paid, Apr '26–Mar '28, due 9th, HDFC ····4821 autopay, outstanding ₹2,37,500.
- Production details included: principal/interest split card, status/loan-account rows, help row, reduced-motion path, full-bleed mobile breakpoint.
- Tap tick to replay the celebration.
- 4 states as separate files with a bottom switcher pill, ALL on the locked base: index (success, green), partial.html (amber, amber-check icon, ₹7,500 of 12,500, amber-tip bar, banner "Pay by 16 Aug", pay-remaining CTA), failed.html (red, X, one-line retry banner, summary leads with red due amount, NO progress bar or carousel, Get support row), prepay.html (renamed from duplicate2.html; "Prepay": principal prepayment, EMI fixed, tail absorbs adjustment — impact card with before→after rows (Loan ends, Last EMI) + "You save ₹X in interest"; 3 scenario pills top-right (₹5k = tenure unchanged/last EMI ₹6,620, ₹12.5k = 1 month early/₹10,300, ₹40k = 3 months early/₹2,100) that recompute the whole screen incl. carousel length; arithmetic rule: prepay + saved interest = amount removed from the tail).
- LOCKED (10 Aug 2026): fern green theme final, preview dots removed. Screen simplified after agentation rounds: every card is a chevron nav row (loan summary, "You're on track" timeline, payment details all toast a next screen), single track+fill progress bar (no 24 segments), only outstanding+next-EMI rows, no sub-lines or status lines beyond one dot-sub on payment details, uniform 14px card rhythm, 20px headers. partial.html and failed.html rebuilt from this base (partial has amber .fillp tip on the bar); double.html still on the OLD pre-lock design, needs the same rebuild if used.
- Agentation feedback toolbar loaded on all pages via esm.sh (React 18, desktop only) so Tejas can annotate elements and paste structured feedback.
