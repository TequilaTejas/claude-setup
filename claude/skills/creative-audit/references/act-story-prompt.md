# Act-story prompt — one agent per act

Substitute `{DIR}`, `{FIRST}`, `{LAST}`, `{ACT_NO}`, `{OUT}` and send as the whole task.

Each act gets its own agent, reading exactly that act's episodes. No agent writes
about a stretch it has not read, and none of them see the hook list.

---

You are writing the story of one act of a serialized-audio show, for a report that
someone will read who has never heard of this show and knows none of its characters.

Read every episode from {FIRST} to {LAST} inclusive, as `{DIR}/epNNNN.txt`. Read them
in order and read each one fully. This act is act number {ACT_NO}.

## What to write

**A name for the act.** Two to four words, concrete, drawn from what actually happens.
"The Throne War", "Two Men, One Body", "The Long Absence". Not "Rising Action", not
"Act Two", not a theme.

**Three paragraphs of story.** Between 700 and 1,100 characters in total. What
happens, in order, told straight.

- Name people the first time and say who they are: "Evie, the human noblewoman
  married into the vampire court", not "Evie".
- Use specifics. Episode numbers for the moments that matter, real names, real
  places, real objects. "At episodes 348 to 350 they hold a conversation inside one
  skull" beats "the two selves confront each other".
- Present tense.
- **No evaluation.** Not whether it works, whether it drags, whether it is clever or
  a mistake. Only what happens.

**One line of judgment**, and only one. This is the only place an opinion belongs:
what a reader should take away about this act as craft. "The biggest idea in the
show, told in a way a listener cannot follow by ear."

## Output

Write `{OUT}` as JSON, no prose around it:

```json
{
  "act": {ACT_NO},
  "range": [{FIRST}, {LAST}],
  "name": "Two Men, One Body",
  "story": [
    "First paragraph.",
    "Second paragraph.",
    "Third paragraph."
  ],
  "note": "One line of judgment, or null if the act is unremarkable."
}
```

## Rules

0. **Namespace every temporary file you create.** Many act agents run at the same
   time against the same scratchpad. A file called `p1.txt` or `notes.txt` will be
   overwritten by another agent mid-task, and you will read someone else's act
   without knowing it. Prefix everything with the act number: `act{ACT_NO}_p1.txt`.
1. **Only this act.** Do not summarise what came before or tease what comes after,
   beyond the minimum needed for a sentence to make sense.
2. **Three paragraphs.** Not two, not five.
3. **Do not count or name hooks, questions, cliffhangers, promises or trouble.** Those
   are other passes. If you find yourself writing "this raises the question of", stop
   and write what happens instead.
4. **The judgment line is one sentence.** If you have three opinions, pick the one a
   writer could act on.
5. If a script file is missing, say so in the last paragraph and continue.

Return only the path you wrote, the act name, and the story's character count.
