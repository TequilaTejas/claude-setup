# Arc-marking prompt — pass this to each arc agent verbatim

Substitute `{DIR}`, `{FIRST}`, `{LAST}`, `{OUT}` and send as the agent's whole task.

**This agent must never be given the hook list, the hook prompt, or any output of the
hook pass.** The two passes exist to be independent. Where their answers later agree,
that agreement is evidence. If an arc agent has seen the hooks, the agreement means
nothing.

---

You are marking where a serialized-audio show turns from one stretch of story into
the next. Read every episode from {FIRST} to {LAST} inclusive, as
`{DIR}/epNNNN.txt`. Read them in order and read each one fully.

An **act** is a stretch the story moves through: a set of episodes that are about the
same thing, in the same situation, with the same people. An act **turns** when that
stops being true.

## What counts as a turn

Three kinds. A strong turn usually shows more than one.

| Kind | A turn looks like |
|---|---|
| **structural** | a flashback begins or ends, the story skips time, the point of view hands over to someone else, the present-day plot stops |
| **situation** | the location changes for good, a major character arrives or leaves or dies, the balance of power flips, a war starts or ends |
| **question** | what the stretch is *about* changes. Not a single scene's question: the thing a listener would name if asked what this part of the show is for |

## What is not a turn

- A single dramatic episode. Something big happening is not the same as the story
  becoming about something else.
- A fight, a reveal or a death that leaves the situation intact.
- A chapter or part heading in the script. Those are production labels, not structure.
- A quiet stretch. Slow is not a turn.

Most 50-episode windows contain **zero, one or two** turns. If you are marking five,
you are marking scenes.

## Output

Write `{OUT}` as JSON, no prose around it:

```json
{
  "window": [{FIRST}, {LAST}],
  "about": "One sentence: what this stretch of the show is about, for someone who has never heard of it.",
  "turns": [
    {
      "ep": 251,
      "confidence": 3,
      "kinds": ["structural", "situation"],
      "why": "Time magic splits the prince into two people who share a body. Everything after this is about which of them she is dealing with.",
      "before": "what the story was about up to here",
      "after": "what it is about from here"
    }
  ]
}
```

| Field | |
|---|---|
| `ep` | the **first** episode of the new stretch, not the last of the old one |
| `confidence` | `3` unmistakable, the show is plainly somewhere else now · `2` clear but a reader could put the line a few episodes either side · `1` something shifts but it may just be a strong episode |
| `kinds` | one or more of `structural`, `situation`, `question` |
| `why` | one sentence, naming what changed. Point at the text |
| `before` / `after` | what the story is about on each side. If you cannot fill both differently, it is not a turn |

## Rules

0. **Namespace every temporary file you create.** Many agents run at the same time
   against the same scratchpad. A file called `p1.txt` or `notes.txt` will be
   overwritten by another agent mid-task and you will read someone else's work
   without knowing it. Prefix everything with your own range, e.g. `{FIRST}_p1.txt`.
1. **Only mark inside {FIRST}–{LAST}.** Never propose an episode outside your window.
2. **The edges are the hard part.** If the story is clearly already mid-turn when your
   window opens, say so in `about` rather than marking a turn at {FIRST}.
3. **Do not evaluate.** Not whether the turn is good, well-handled or well-paced. Only
   that it happens, and where.
4. **Do not count questions, hooks, cliffhangers or promises.** That is a different
   pass and you are not doing it.
5. If a script file is missing, note it in `about` and continue.

Return only the path you wrote and a count: episodes read, turns marked, and their
episode numbers.
