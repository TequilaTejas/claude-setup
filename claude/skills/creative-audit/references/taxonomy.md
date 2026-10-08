# The three things, and how to tell them apart

They are not the same size and they do not do the same job. Marking them separately
is the point of this document.

---

## 1 · The opening promise

> **What fantasy, emotion, or transformation is being promised in the first few
> minutes?**

The promise is not a question. It is the deal the show offers a stranger in the
first few minutes: *stay with me and you will get to feel this.*

It has three parts, and a strong opening names all three:

| Part | The reader's question | Example shape |
|---|---|---|
| **Fantasy** | What will I get to imagine? | being wanted by someone dangerous |
| **Emotion** | What will I get to feel? | the thrill of being chosen over everyone |
| **Transformation** | Who will I watch someone become? | a girl who was sold becomes the one who rules |

Written out: *"A powerless girl is handed to her family's enemy, and you will watch
her become the most feared woman in the empire."*

**Where to find it.** Episodes 1 to 3, and mostly the first few minutes of episode 1.
Not the plot of those episodes. What those episodes make a listener want.

**One show has one promise.** If you find yourself writing two, either the show
genuinely re-promises later (record that as a re-promise with its episode), or you
have written down the plot instead of the promise.

**The promise is the yardstick for everything else.** Every arc either serves it,
complicates it, or wanders from it. Every cliffhanger is either aligned with it or
is not. That is what makes it worth naming precisely.

---

## 2 · The hook

> **What grabs attention immediately and makes a listener stay?**

The hook is the grab. The promise is what is being dangled; the hook is the hand
that takes hold. In practice a hook is a specific, unresolved thing a listener is
carrying: a question, a threat, a wanting, a thing they know that a character does
not.

**Two kinds, and they behave differently:**

| | **Opening hook** | **Running hook** |
|---|---|---|
| Where | first few episodes | anywhere |
| Job | make them stay past episode 1 | make them keep going at episode 300 |
| Lives | often minutes | often hundreds of episodes |
| Fails by | being slow or vague | going quiet, or being dropped |

**Write a hook as the thing a listener is holding**, in their words:
*"Why is he warm when every vampire she has met was cold?"*
Not *"the mystery of his nature."*

**A hook that nobody mentions is not a hook.** Being unanswered and being alive are
different. A question the show has not raised in fifty episodes is holding nobody,
however open it remains on paper. This is measured, not judged: see `hook_health.py`.

---

## 3 · The cliffhanger

> **How does the ending guarantee continuation? Is it strong and emotionally
> aligned?**

Per episode. Its whole job is the next press of play.

It is scored on **two axes that are independent**, and the second one is the one
that gets missed:

### Strength — does it compel continuation?

| | |
|---|---|
| **3 · Grips** | Something is about to happen to someone we care about, and the listener cannot guess which way |
| **2 · Pulls** | A real question is posed, but the answer feels predictable or the stakes are modest |
| **1 · Nudges** | The episode stops somewhere mildly interesting |
| **0 · Stops** | The episode simply ends. Nothing is asked |

### Alignment — is it strong about the right thing?

Aligned means the ending pulls on **the same fantasy, emotion or transformation the
show promised at the start.**

| | |
|---|---|
| **2 · On promise** | Pulls directly on the promised fantasy, emotion or transformation |
| **1 · Adjacent** | Pulls on the world or the plot, but not on what the listener was promised to feel |
| **0 · Off promise** | Strong about something the listener never signed up for |

**This is the pairing that matters.** A cliffhanger can be a 3 for strength and a 0
for alignment: a thrilling battle at the end of a show that promised a love story.
The listener is gripped by an episode and still drifts away from the show, and no
single "was it a good cliffhanger" score would ever show you why.

```
              ALIGNED                    OFF PROMISE
           ┌────────────────────────┬────────────────────────┐
  STRONG   │  working as designed   │  gripping, wrong show  │
           │                        │  ← the dangerous one   │
           ├────────────────────────┼────────────────────────┤
  WEAK     │  right idea, no teeth  │  nothing holding them  │
           └────────────────────────┴────────────────────────┘
```

The top-right quadrant is invisible to every other measure in this skill. A show
sitting there looks healthy: questions open, cliffhangers land, arcs resolve. And
people still leave, because the thing they were promised stopped being the thing
they were given.

---

## How the three sit together

```
  PROMISE      ◄──────────────── one, for the whole show ────────────────►
                                          │
                                 every arc serves it,
                                complicates it, or wanders
                                          │
  ARC          ┌─────────────┬────────────┴───┬──────────────┐
               │    A1       │      A2        │      A3      │

  HOOK         ●━━━━━━━━━━━━━┿━━━━━━━━━━○     ░░░●━━━━━━━━━━━━━━━━━
               carried across a boundary       opened by a new arc

  CLIFFHANGER  │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │ │
               strength × alignment, one pair per episode
```

Read it downward and you have the whole diagnosis:

- **The promise** says what the show owes.
- **The arcs** say whether it is still trying to pay.
- **The hooks** say whether anyone is still holding on.
- **The cliffhangers** say whether each individual episode earns the next one, and
  whether it earns it for the right reason.
