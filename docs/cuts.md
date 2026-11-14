# Cuts

What Crossings does when the harness compacts a session: the count and its page, how the frame crosses, the line about a summary worn down by retelling, and the hand-over. All of it is for a project where Crossings is on; switched off, no cut is counted, noted or answered.

---

### At a cut

| Event | Crossings |
| --- | --- |
| the harness is about to cut (`session.compact`, in the hooks module) | reads the home's `mode` and `carry` through the door, and answers the cut as they ask (below). A subagent's own cut, and one the harness computes ahead of time, are never touched |
| the session starts again (`SessionStart`, source `compact`) | where the hook's input names no subagent, gives a session a person sits in the waking note, about this cut by its number, and, where the home carries the frame as context, the frame |
| the harness hands over its summary (`PostCompact`) | counts the cut and writes its page; for a session a person sits in, brings the archive and the index up to date and renews the second copy where one is set; and shows the person one line where the summary mostly retells the one before; nothing at all where the hook's input names a subagent |

The waking note names this cut by its number whichever of the two hooks the harness calls first. A hook that fails ends quietly, with exit status 0 and a line in the error log, and a failure inside the module leaves the cut to the harness.

---

### The count

Every cut is counted by script, from the session's transcript, and written to a page in the home, `<session>-cut-<n>.md`, with a sidecar beside it, `<session>-cut-<n>.json`. The page holds counts and pointers and no text of either voice:

| The page says | From |
| --- | --- |
| the kind of cut and its trigger | the harness |
| tokens before and after, and how long the cut took | the harness, where it gives them |
| the summary's length in characters, and how much of it repeats the summary of the same session's cut before | the summary, and the earlier cut's sidecar |
| the session, the transcript, and the line the cut stands at | the transcript |
| for each voice: its messages since the cut before, how many the summary holds whole, how much of its text it holds by characters, how many of its sentences of 40 characters or more, and how many messages it holds nothing of | the transcript and the summary |
| how many of the person's messages were typed at the prompt and how many sent while a turn ran | the transcript |
| what share of the record the two voices were by characters, tool calls and their results being the rest | the transcript |
| the ten least held messages of each voice, by id, line, length and share held | the transcript and the summary |

"Word for word" is the whole claim: a run of 24 characters or more that the summary also holds. A message under 12 characters is too short to judge and is counted as not held. A summary can carry a message in other words and get no credit here. The count covers only what stood since the cut before, or since the start, and leaves out every message said while the switch was off, and every row the harness marks as a subagent's.

| Event | The page |
| --- | --- |
| the count runs out of its eight seconds | says not all of it was counted, and gives the numbers for the messages reached |
| the stretch holds no message of either voice (a session just forked) | says it was not counted, and guesses nothing |
| no summary was handed over | says there is nothing to compare against, and how many messages stood before the cut |
| the home's `off.txt` is missing or shorter than the person's record says ([Privacy](privacy.md)) | lists nothing said, by id or by length, and says that what was said off the record cannot be told from the rest |

The sidecar holds every pointer, the session's id and the transcript's path, the figures the retelling line rests on, and the summary's runs of 24 characters as digests keyed with the home's own key (`said/runs.key`), so that no text of either voice is kept anywhere new and a digest cannot be checked against a guess. The next cut of the same session compares its summary with these digests. A sidecar made with another key, or whose digests cannot be read, is compared with nothing.

The count is written for a cut in any session of a home that is on. The archive is brought up to date only for a session a person sits in.

`python3 crossing/show.py [project] [--session ID]` prints the cuts on record in a few lines each, from the sidecars alone. `python3 crossing/read.py <transcript> <id or line>` reads a message back from a transcript, at most 20 a call, and shows only what was said: never a reasoning block, tool traffic or a harness note.

---

### The modes

Two plain files of the home decide how a cut is answered: `mode` and `carry`, one word each.

| `mode` | `carry` | At a cut |
| --- | --- | --- |
| `native`, missing, or a word not known | either | the cut is the harness's as it made it, and no frame crosses; the count and the waking note still come |
| `beside` | `note` | the cut stands as the harness made it, whatever set it off; the hook brings the frame as context when the session starts again. The same files give a session started new its frame |
| `beside` | `message`, or missing | the frame goes into the cut's answer as a message, after the harness's summary |
| `own` | either | at a cut the harness did not start by itself, the frame takes the summary's place; an earlier cut's summary at the head of the conversation is carried on before it. At an automatic cut, as `beside` with `message` |

A home that `/crossings on` makes outside the project starts with `mode` set to `beside` and `carry` to `note`. A project's own `crossings/` folder is switched on as it is: with no `mode` file, its cuts are `native`.

A frame carried as a message is handed to the harness as a user message in the cut's answer. It opens "A note from the Crossings plugin", and the plugin's reader never takes such a row for the person's words, nor one that opens with the older "A note from the Crossing plugin". Carried as a note, nothing is filed as a message.

Where a message is to carry the frame and the door gives none, the home's `hand-over.md` goes instead, with its words page beside it, after a note that says what it is. Where there is neither, the cut is left as the harness made it. The module writes what it did into `last-cut.json`, and the frame hook into `last-carry.json`; neither is needed for the cut to go on.

---

### A summary worn down by retelling

The harness carries its summary from cut to cut and retells it each time. Where most of a long summary now repeats the one before, and the last stretch is marked, the person is shown one line under the turn: that the session has been cut this many times, that most of its summary now retells the one before, and that a new session would start from the store alone with nothing lost.

It is shown once a cut, where all of these hold:

| Condition | Default | Set by |
| --- | --- | --- |
| the summary is at least this many characters | 20,000 (`LONG`) | `retelling-length` |
| at least this share of it repeats the summary of the same session's cut before, by runs of 24 characters | 60% (`MOSTLY`) | `retelling-share` |
| a label rests on a message of the stretch since that cut | | |
| a line was left at the door since that cut | | |

Where any one fails, nothing is said. It blocks nothing, and the session is not handed it. The first cut of a session has no summary before it to compare with. The two figures are whole numbers in one-line files of the home ([Settings](settings.md)).

---

### The hand-over

A hand-over is a label page, `hand-over.md`, carried as a message where no frame can be made. `python3 crossing/handover.py <transcript> <hand-over.md>` writes `hand-over.words.md` beside it: for every message id the page names, what was said there, word for word from the transcript, each cut at 700 characters, and the ids the transcript does not hold. A message the home keeps out is not on it: one struck, one said while Crossings was off, one a session no person sat in held. Where the home's record of when Crossings was off cannot be read, or is missing or shorter than it was, it holds no message. It is written through `within`, for its owner alone. The record is never changed. A strike mends a words page line by line, or takes it away whole where it cannot be mended ([Privacy](privacy.md)).
