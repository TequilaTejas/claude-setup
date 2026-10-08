# Sentiment prompt — one agent per comment batch

Substitute `{FILE}`, `{OUT}`, `{FIRST}`, `{LAST}` and send as the whole task.

This produces the per-episode reaction curve. It must be counts, not impressions, and
it must be reproducible: two agents given the same batch should return close to the
same numbers. That is why the rules below are mechanical.

---

Read every comment in `{FILE}`. They come from episodes {FIRST} to {LAST} of a
serialized-audio show, grouped under `===== EPISODE n =====` headers.

Classify **every** comment into exactly one bucket.

| bucket | means |
|---|---|
| `positive` | enjoying the story: praise, excitement, love for a character, theorising with pleasure, asking for more |
| `negative` | unhappy with the story: a character they hate, a plot they object to, pacing complaints, disappointment, saying they are leaving |
| `production` | unhappy with something outside the story: narration, audio, episodes out of order, repeats, app faults |
| `money` | coins, paying, episodes no longer free, unlocking |
| `neutral` | plot questions, summaries, greetings, off-topic chat, anything that carries no clear feeling |

## Rules that make this reproducible

1. **One bucket per comment.** When a comment is two things, use this order of
   precedence: money > production > negative > positive > neutral. A comment that
   loves the story but hates the narrator is `production`.
2. **Sarcasm counts as what it means**, not what it says.
3. **A question is `neutral`** unless it carries obvious feeling ("why would she DO
   that??" is negative; "wait is he her brother?" is neutral).
4. **Emoji-only comments**: hearts, fire and laughing are `positive`; angry, crying
   and thumbs-down are `negative`; anything else is `neutral`.
5. **Non-English comments count.** Judge them on the same rules; do not bucket them as
   neutral just because they are not English.
6. **Never skip a comment.** Your per-episode totals must equal the number of comments
   listed under that episode header. The file states the total; check yours matches.

## Output

Write `{OUT}` as JSON, no prose around it:

```json
{"range": [{FIRST}, {LAST}],
 "total": 0,
 "episodes": {
   "291": {"positive": 4, "negative": 11, "production": 88, "money": 2, "neutral": 1,
           "top_negative": "the single most-liked negative comment, verbatim",
           "top_positive": "the single most-liked positive comment, verbatim"}
 }}
```

`top_negative` and `top_positive` are optional per episode: include them only where an
episode has at least three comments in that bucket. Quote exactly, trim with an
ellipsis, never reword.

## Rules

0. **Namespace any temporary file** you create with `{FIRST}_`. Other agents are
   working in the same scratchpad and generic names get overwritten.
1. Counts must add up. State the batch total in `total` and make sure the per-episode
   numbers sum to it.
2. Do not summarise the batch, do not interpret the story, do not say what should
   change. Classify and count.

Return only the path you wrote, the batch total, and the five bucket totals.
