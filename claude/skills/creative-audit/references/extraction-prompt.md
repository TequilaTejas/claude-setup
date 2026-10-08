# Extraction prompt — pass this to each batch agent verbatim

Substitute `{DIR}`, `{FIRST}`, `{LAST}`, `{OUT}`, `{LEADS}`, `{PROMISE}` and send
as the agent's whole task.
Do not paraphrase it. The schema is what makes eleven independent batches mergeable.

---

You are extracting hook data from the production scripts of a serialized-audio show.
**The show promised this in its opening minutes:**

> {PROMISE}

You will score every episode's ending against that promise. Read it twice before you
start. It is not the plot. It is what the show told a stranger they would get to
feel.

The show's declared leads are: **{LEADS}**. Track each of them by name, every
episode. Do not decide for yourself who the protagonist is.

Read every episode from {FIRST} to {LAST} inclusive, as `{DIR}/epNNNN.txt`
(zero-padded to four digits). These are prose narrative scripts, roughly 8 KB each.

Read them in order. Read each one fully — do not skim, do not sample, do not infer an
episode's content from its neighbours.

## What you are looking for

A **hook** is a burning question the script plants that makes the next episode feel
necessary. Not a topic, not a theme — a question with an answer the listener wants.
"Will she get the beast egg back before the trial?" is a hook. "Revenge" is not.

## Hard boundary

You see episodes {FIRST}–{LAST} and nothing else. You do **not** know what happened
before {FIRST} or after {LAST}.

- Report a question as **opened** when this batch is where you first see it posed. If
  it is clearly already running when your first episode begins, record it in
  `inherited` instead — name it, do not guess where it started.
- Report a question as **closed** only if you read the episode that answers it.
- Never write an episode number outside {FIRST}–{LAST}. Never speculate about
  cross-batch continuity. Dedup across batches is someone else's job; guessing at it
  corrupts the merge.

## Output

Write `{OUT}` — a JSON file, one object per episode, in episode order, no prose
around it:

```json
{
  "batch": [{FIRST}, {LAST}],

  "summary": "250-350 words of plain English telling what happens in these 25 episodes, in order. Write it for someone who has never heard of this show and does not know any character's name yet. Introduce people the first time you mention them ('Mara, the woman married off to the enemy prince to buy a peace'). No jargon. Short sentences. Say what happens, not whether it is good.",

  "open_at_start": [
    {"q": "a question already running when episode {FIRST} began", "why": "the line or moment that shows it is already live"}
  ],
  "open_at_end": [
    {"q": "a question still unanswered when episode {LAST} finishes", "last_touched": 273, "why": "where it was last raised"}
  ],

  "inherited": [
    {"q": "question already running when this batch opened", "note": "how you can tell"}
  ],
  "episodes": [
    {
      "ep": 37,
      "title": "A Man, She Needed a Man",
      "opens": [
        {"q": "Will Mara take the egg back before the trial?",
         "kind": "threat",
         "force": 3,
         "evidence": "she swears it on her shattered Core"}
      ],
      "closes": [
        {"q": "Who destroyed her body?",
         "how": "onscreen",
         "note": "Sera confesses in front of the court"}
      ],
      "cliff": {
        "text": "Sera claims the hatching as her own before the whole Academy",
        "type": "reveal",
        "posed_as_question": true,
        "strength": 3,
        "alignment": 2,
        "alignment_why": "her standing is stolen in public, which is the exact humiliation the promise says she will overturn"
      },
      "leads": {"Mara": "drives", "Kel": "absent"},
      "pov": ["Mara"],
      "new_names": ["Dean Aldric"],
      "stated_promises": [
        {"text": "the Academy trial is in three days"}
      ],
      "beat": "escalates",
      "flag": null
    }
  ]
}
```

## Field definitions — use these exact values

| Field | Values | Meaning |
|---|---|---|
| `opens[].kind` | `threat` `mystery` `relationship` `identity` `goal` `debt` `decision` `choice` | what sort of question it is. Used when clustering, to keep two different questions about the same character apart |
| `opens[].force` | `1` `2` `3` | how hard this episode pushes it. 3 = it is the reason to continue |
| `opens[].evidence` | short phrase | the concrete moment in the text. Not a summary of the episode |
| `closes[].how` | `onscreen` `offscreen` `deflected` `dropped` | `offscreen` = answered in a gap or reported after the fact. `deflected` = a different question answered in its place |
| `cliff.text` | one sentence | what the episode leaves hanging. `null` if it simply stops |
| `cliff.type` | `threat` `reveal` `arrival` `decision` `mystery` `question` `none` | |
| `cliff.posed_as_question` | `true` `false` | does the ending make the listener want an answer, or just stop |
| `cliff.strength` | `0`-`3` | how hard the ending pushes for the next episode. **3** something is about to happen to someone we care about and it could go either way · **2** a real question, but predictable or low stakes · **1** stops somewhere mildly interesting · **0** simply ends |
| `cliff.alignment` | `0`-`2` | whether it pulls on **the promise above**. **2** directly on the promised fantasy, emotion or transformation · **1** on the world or plot, but not on what the listener was promised to feel · **0** strong about something they never signed up for |
| `cliff.alignment_why` | one short phrase | what in the ending connects to the promise, or what it pulls on instead |
| `leads` | object: one entry per name in {LEADS} | each lead's agency this episode. Every declared lead gets an entry every episode, no exceptions |
| `leads[name]` | `drives` | makes a choice that changes the situation |
| | `present_passive` | appears, but is acted upon — reacts, chooses nothing |
| | `absent` | **does not appear on the page at all** — including a character who is imprisoned, missing or presumed dead somewhere offscreen and only discussed by others |

**Appearance decides, not circumstance.** Ask only: is this character on the page in
this episode? If yes, they are `drives` or `present_passive` — imprisoned, chained,
unconscious, overpowered and ignored are all `present_passive`. If they are merely
talked about, remembered, or searched for while never appearing, they are `absent`,
however much of the episode is spent discussing them. A character appearing in a
flashback, dream or vision **is on the page**.
| `pov` | names | whose head the episode sits in |
| `new_names` | names | named characters appearing for the first time **in this batch**. Include a note if two names are confusable in audio |
| `stated_promises[].text` | quote or close paraphrase | the script stating something **will** happen. These are what later get broken |
| `beat` | `new` `escalates` `re-runs` | `re-runs` = the same kind of beat as a recent episode with the lead's position unchanged |
| `flag` | string or `null` | anything a reader would notice: a dead stretch, a confusing timeline, a scene with no goal, a conversation spread across episodes |

## The handoff lists are the most important thing you write

You are one of many agents, each reading a different 25 episodes. None of us can see
the whole show. The only way the pieces get joined back together is `open_at_start`
and `open_at_end`.

Think of it as a relay. The agent before you finished with some questions still
hanging. You pick them up. When you finish, you hand yours to the next agent.

- **`open_at_start`** is what you inherited. When your first episode begins, some
  questions are clearly already running: people refer to a plan you never saw made,
  or a person you never saw arrive. List those. Do not guess which episode they
  started in.
- **`open_at_end`** is what you are handing on. When your last episode finishes,
  some questions have not been answered. List every one that still matters, with the
  episode where it was last raised.

Write each question the same way both times, in plain words, so the two lists can be
matched by whoever joins them. "Will he find out she lied about the letter?" is
matchable. "The letter thing" is not.

## Strength and alignment are separate. Do not let one drag the other.

An episode can end on a thrilling battle and score **strength 3, alignment 0**, if
the show promised a love story. That pairing is the single most useful thing you can
record, so be willing to write it.

Score alignment against **the promise quoted at the top of this task**, never against
what the show has become by your block. If your episodes are all war and the promise
was a romance, that is an alignment 0 stretch, and saying so is the job. Do not
rescore the promise to fit the episodes in front of you.

Judge the ending only. Not the episode.

## Rules

0. **Namespace every temporary file you create.** Many agents run at the same time
   against the same scratchpad. A file called `p1.txt` or `notes.txt` will be
   overwritten by another agent mid-task and you will read someone else's work
   without knowing it. Prefix everything with your own range, e.g. `{FIRST}_p1.txt`.
1. **Every episode in range gets an object**, even a quiet one. A missing episode
   fails the merge. An empty episode is `"opens": [], "closes": []` with a `flag`.
2. **Quote or name, never summarize.** `evidence` and `stated_promises` must point at
   something in the text.
3. **Phrase every question as a question**, in the listener's voice.
4. **The summary is for a stranger.** Someone reading it has never heard of this
   show. Do not assume they know who anyone is, what the world's rules are, or what
   happened before your block. Name people the first time and say who they are. Use
   ordinary words. If you find yourself writing a term the show invented, explain it
   in the same sentence.
5. **Do not evaluate the show.** No "this is strong", no "listeners would lose
   interest". `flag` records what you observed; judgment happens downstream.
6. **`absent` is literal — appearance decides.** On the page in any form (including
   flashback, dream or vision) means `drives` or `present_passive`. Never on the
   page means `absent`, even if the whole episode is about them. This distinction
   drives the drift analysis downstream; getting it loose makes that section
   worthless.
7. If a script file is missing or unreadable, record
   `{"ep": N, "flag": "FILE MISSING"}` and continue.

Return only the path you wrote and a one-line count: episodes read, opens, closes,
flags, how many questions you handed on in `open_at_end`, and the average strength
and alignment of your 25 endings.
