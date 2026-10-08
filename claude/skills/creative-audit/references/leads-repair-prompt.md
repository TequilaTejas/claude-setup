# Leads repair pass

Substitute `{DIR}`, `{FIRST}`, `{LAST}`, `{OUT}`, `{LEADS}` before sending this.

Read every episode from {FIRST} to {LAST} inclusive, as `{DIR}/epNNNN.txt`.
These are audio production scripts: prose narration and dialogue interleaved with
cues like `[SFX: ...]` and `[MUSIC: ...]`. Cues are not story content.

You are recording ONE judgment per episode: the agency of each declared lead.

The declared leads are **{LEADS}**. If a lead appears under another name, alias or
persona and is clearly the same person, record them as that lead and say which name
was on the page in `note`. Do not decide for yourself who the leads are.

For each lead, in each episode, pick exactly one value:

| Value | Means |
|---|---|
| `drives` | makes a choice that changes the situation |
| `present_passive` | appears, but is acted upon — reacts, chooses nothing |
| `absent` | **does not appear in the episode at all** |

**Appearance decides, not circumstance.** Ask only: is this character on the page in
this episode?

- On the page in any form — including imprisoned, chained, unconscious, overpowered,
  ignored, or appearing in a flashback, dream or vision — is `drives` or
  `present_passive`, never `absent`.
- Never on the page is `absent`, however much of the episode is spent discussing,
  remembering or searching for them.

A character who is missing, presumed dead or held somewhere offscreen and only talked
about by others is `absent`. Note it when the call could be misread.

Do not evaluate the show. Do not summarize plot. One line of `note` only when
something would otherwise be misread (a persona change, an appearance only in
flashback, a scene where presence is ambiguous).

Write `{OUT}` as JSON, no prose around it:

```json
{"range": [{FIRST}, {LAST}],
 "episodes": [
   {"ep": 1, "leads": {"<lead A>": "present_passive", "<lead B>": "drives"}, "note": null},
   {"ep": 2, "leads": {"<lead A>": "drives", "<lead B>": "absent"}, "note": null}
 ]}
```

Every episode in range gets an object. Both leads get an entry in every episode.
Never write an episode number outside {FIRST}–{LAST}.

Return only the path you wrote and a count: episodes done, and how many episodes
each lead was `absent` for.

## Rule

0. **Namespace every temporary file you create.** Many agents run at the same time
   against the same scratchpad. A file called `p1.txt` or `notes.txt` will be
   overwritten by another agent mid-task and you will read someone else's work
   without knowing it. Prefix everything with your own range, e.g. `{FIRST}_p1.txt`.
