# Episode-read prompt — explaining what the data singled out

Substitute `{EPS}`, `{DIR}`, `{OUT}` and send as the whole task.

**Do not tell this agent why these episodes were chosen.** It must not know whether the
data showed a drop, a completion collapse or a comment surge, or it will find a reason
for whatever it was told. It reads the episodes and describes them. The matching up
happens afterwards, by whoever sent it.

---

Read these episodes in full from `{DIR}`: **{EPS}**. Files are `epNNNN.txt`,
zero-padded. Read each one completely before writing anything about it.

For each episode, report what is actually on the page.

## What to report per episode

| field | what it means |
|---|---|
| `what_happens` | two or three sentences. The events, in order, in plain words |
| `ends_on` | the last beat. Quote the final line or two |
| `poses_question` | does the ending make the next episode feel necessary? true/false |
| `lead_role` | `drives` · `present_active` · `present_passive` · `absent` — appearance decides, not circumstance: a lead who is imprisoned but arguing is present_active |
| `scene_count` | how many distinct scenes |
| `recap_share` | rough share of the episode that restates what a listener already knows: `none` · `some` · `lots` |
| `shape` | `escalates` · `holds` · `resolves` · `re-runs` · `sets_up` · `digression` |
| `notable` | anything a listener would trip over: a time skip, a POV change, a new character arriving cold, a long stretch of one conversation, an explicit scene, a recap of a scene just heard, a death, a reveal delivered as report rather than scene |
| `odd` | anything structurally strange about this episode compared with normal episodes of this show. Say "nothing" if nothing |

## Output

Write `{OUT}` as JSON, no prose around it:

```json
{"episodes": [
  {"ep": 384, "title": "as printed in the file header",
   "what_happens": "…", "ends_on": "…", "poses_question": true,
   "lead_role": "drives", "scene_count": 3, "recap_share": "some",
   "shape": "escalates", "notable": "…", "odd": "nothing"}
]}
```

## Rules

0. **Namespace any temporary file** you create with the first episode number. Other
   agents are working in the same scratchpad and generic names get overwritten.
1. **Read the whole episode.** Skimming the first page produces a summary of the recap,
   which is the one part of the episode that is not the episode.
2. **Do not guess why you were asked.** No speculation about retention, listeners,
   whether an episode is good, or what a producer should change. Describe it.
3. **Quote for `ends_on`.** Trim with an ellipsis, never reword.
4. **`odd` is the most valuable field.** A structurally strange episode is usually the
   answer to whatever question prompted the read. Be specific: "the entire episode is
   one conversation in a carriage" beats "slow pacing".
5. If an episode file is missing, say so in place of that entry rather than skipping it.

Return only the path you wrote and a one-line note per episode.
