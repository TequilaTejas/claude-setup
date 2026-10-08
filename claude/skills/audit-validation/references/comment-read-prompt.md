# Comment-read prompt — one agent per episode window

Substitute `{FILE}`, `{FIRST}`, `{LAST}`, `{OUT}` and send as the whole task.

**Do not tell this agent what the Creative Audit says about these episodes.** It is
being asked what listeners said, not whether a theory holds. If it knows the theory
it will find it.

---

Read every listener comment in `{FILE}`. They come from episodes {FIRST} to {LAST} of
a serialized-audio show, tagged by episode, with a like count.

Your job is to report **what these listeners are actually saying**, in their words.

## What to look for

| | |
|---|---|
| **Confusion** | people who cannot follow something: who is speaking, what happened, who a character is, what the timeline is |
| **Complaint** | people annoyed by the story itself: a decision, a character, pacing, a betrayal of what they expected |
| **Production complaint** | audio, narration, episodes out of order, repeats, missing episodes |
| **Money** | anything about coins, paying, episodes no longer being free, unlocking |
| **Leaving** | people saying they are done, skipping ahead, or coming back after a break |
| **Delight** | what they love, and what specifically they love about it |

## Output

Write `{OUT}` as JSON, no prose around it:

```json
{
  "window": [{FIRST}, {LAST}],
  "total_comments": 0,
  "summary": "Two or three sentences: what the mood is here and what listeners keep returning to. Plain words.",
  "themes": [
    {"theme": "confusion about which brother is speaking",
     "kind": "confusion",
     "count": 11,
     "episodes": [290, 291, 295],
     "quotes": [
       {"ep": 291, "text": "exact comment text, trimmed but never reworded", "likes": 4}
     ]}
  ],
  "loudest": [
    {"ep": 291, "likes": 25, "text": "the single most-liked comment in this window"}
  ],
  "mood": {"delight": 0, "complaint": 0, "confusion": 0, "production": 0, "money": 0}
}
```

`mood` counts comments, and they should roughly add up to the total. A comment that
is two things can be counted twice; say so in `summary` if that is common.

## Rules

0. **Namespace any temporary file** you create with `{FIRST}_`. Other agents are
   working in the same scratchpad and generic names get overwritten.
1. **Quote exactly.** Trim for length with an ellipsis, never reword. These quotes go
   into a document and will be checked against the source.
2. **Count, do not estimate.** "Eleven comments ask which brother is speaking" is
   usable. "Many listeners are confused" is not.
3. **A theme needs at least three comments.** One person's opinion is not a theme;
   put it in `loudest` if it is well-liked.
4. **Report delight as carefully as complaint.** A window where people are happy is a
   finding, especially if something else suggested it should not be.
5. **Do not interpret the story.** If listeners are confused, report the confusion.
   Do not explain what the show actually meant.
6. **Say if the window is thin.** Fewer than about twenty comments cannot support a
   theme, and the summary should say so.

Return only the path you wrote, the comment count, and the theme names.
