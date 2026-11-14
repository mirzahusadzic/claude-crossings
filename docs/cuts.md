# Cuts

What Crossings does when the harness compacts a session: the count and its page, how the frame crosses, the line about a summary worn down by retelling, and the hand-over. All of it is for a project where Crossings is on; switched off, no cut is counted, noted or answered.

---

### At a cut

| Moment | Crossings |
| --- | --- |
| the harness is about to cut (`session.compact`, in the hooks module) | asks the door where the home is, for the guard on the archive's files ([Privacy](privacy.md)), reads the home's `mode` and `carry` through the door, and answers the cut as they ask (below). A subagent's own cut, and one the harness computes ahead of time, are never touched |
| the session starts again (`SessionStart`, source `compact`) | gives a session a person sits in the waking note, about this cut by its number, and the frame, where the home carries it as context |
| the harness hands over its summary (`PostCompact`) | counts the cut and writes its page. For a session a person sits in, it brings the archive and the index up to date and renews the second copy where one is set. It shows the person one line where the summary mostly retells the one before. Where the hook's input names a subagent, nothing at all |

The waking note names this cut by its number whichever of the two hooks the harness calls first. A summary handed over that opens as one the transcript already holds is that cut again only where nothing of either voice was said after it; otherwise it is a later cut of its own, with the next number, though it retell the one before word for word. A hook that fails ends quietly, with exit status 0 and a line in the error log, and a failure inside the module leaves the cut to the harness.

---

### The count

Every cut is counted by script, from the session's transcript, and written to a page in the home, `<session>-cut-<n>.md`, with a sidecar beside it, `<session>-cut-<n>.json`. The page holds counts and pointers, and no text of either voice:

| The page says | From |
| --- | --- |
| the kind of cut and its trigger | the harness |
| tokens before and after, and how long the cut took | the harness, where it gives them |
| the summary's length in characters, and how much of it repeats the summary of the session's cut before | the summary, and the earlier cut's sidecar |
| the session, the transcript, and the line the cut stands at | the transcript |
| for each voice: its messages since the cut before, how many the summary holds whole, how much of its text it holds by characters, how many of its sentences of 40 characters or more, and how many messages it holds nothing of | the transcript and the summary |
| how many of the person's messages were typed at the prompt, and how many sent while a turn ran | the transcript |
| what share of the record the two voices were by characters, tool calls and their results being the rest | the transcript |
| the ten least held messages of each voice, by id, line, length and share held | the transcript and the summary |

"Word for word" is the whole claim: a run of 24 characters or more that the summary also holds. A message under 12 characters is too short to judge, and is counted as not held. A summary can carry a message in other words and get no credit here.

The count covers only what stood since the cut before, or since the start, one message a row. It leaves out what the archive leaves out: every message said while the switch was off, a subagent's rows with their tool calls and results, and every row whose id is no name.

| Event | The page |
| --- | --- |
| the count runs out of its eight seconds | says not all of it was counted, and gives the numbers for the messages reached |
| the stretch holds no message of either voice (a session just forked) | says it was not counted, and guesses nothing |
| no summary was handed over | says there is nothing to compare against, and how many messages stood before the cut |
| the record of when Crossings was off cannot be told ([Privacy](privacy.md)) | lists nothing said, by id or by length, and says that what was said off the record cannot be told from the rest |

The sidecar holds every pointer, the session's id and the transcript's path, the figures the retelling line rests on, and the summary's runs of 24 characters as digests keyed with the home's own key (`said/runs.key`). So no text of either voice is kept anywhere new, and a digest cannot be checked against a guess. The next cut of the same session compares its summary with these digests; a sidecar made with another key, or whose digests cannot be read, is compared with nothing.

The count is written for a cut in any session of a home that is on. The archive is brought up to date only for a session a person sits in.

`python3 crossing/show.py [project] [--session ID]` prints the cuts on record, a few lines each, from the sidecars alone. A sidecar that cannot be read, or is of another shape than the count writes, is passed over in one line that names it, and the others are shown.

`python3 crossing/read.py <transcript> <id or line> [--cwd DIR]` reads up to 20 messages back from a transcript, and shows only what was said, cleaned as the door shows a message: never a reasoning block, tool traffic or a harness note. An id gives a message only where its start names one row. Where Crossings is on for the project, nothing its home keeps out is shown (a message struck, said while off, or held by a session no person sat in), and a home with a link below it is refused. It is the person's to run, from their own terminal, as the door's own verbs are.

---

### The modes

Two plain files of the home decide how a cut is answered, `mode` and `carry`, one word each.

| `mode` | `carry` | At a cut |
| --- | --- | --- |
| `native`, missing, or a word not known | either | the cut is the harness's as it made it, and no frame crosses; the count and the waking note still come |
| `beside` | `note` | the cut stands as the harness made it, whatever set it off, and the hook brings the frame as context when the session starts again. The same files give a session started new its frame |
| `beside` | `message`, or missing | the frame goes into the cut's answer as a message, after the harness's summary |
| `own` | either | at a cut the harness did not start by itself, the frame takes the summary's place, and an earlier cut's summary at the head of the conversation is carried on before it; at an automatic cut, as `beside` with `message` |

A home `/crossings on` makes outside the project starts with `beside` and `note`, and so does a project's own `crossings/` folder that is empty as it is first switched on; files whose names begin with a dot (`.DS_Store`, `.gitkeep`, `.gitignore`) do not count. A folder that holds anything else is taken by `adopt` as it is, and nothing is written into it: with no `mode` file its cuts are `native`, and a person who wants the frame there writes `mode` and `carry` ([Settings](settings.md)). Switching off and on again never writes either file anew.

A frame carried as a message is handed to the harness as a user message in the cut's answer. It opens "A note from the Crossings plugin", and the plugin's reader never takes such a row for the person's words, nor one that opens with the older "A note from the Crossing plugin". Carried as a note, nothing is filed as a message.

Where a message is to carry the frame and the door gives none, the home's `hand-over.md` goes instead, as `door.py page` gives it ([The door](door.md)), after a note that says what it is. Where there is neither, the cut is left as the harness made it. The module writes what it did into `last-cut.json`, and the frame hook into `last-carry.json`; neither is needed for the cut to go on.

---

### A summary worn down by retelling

The harness carries its summary from cut to cut, and retells it each time. Where most of a long summary now repeats the one before, and the last stretch is marked, the person is shown one line under the turn: that the session has been cut this many times, that most of its summary now retells the one before, and that a new session would start from the store alone with nothing lost.

It is shown once a cut, where all of these hold:

| Condition | Default | Set by |
| --- | --- | --- |
| the summary is at least this many characters | 20,000 (`LONG`) | `retelling-length` |
| at least this share of it repeats the summary of the session's cut before, by runs of 24 characters | 60% (`MOSTLY`) | `retelling-share` |
| a label rests on a message of the stretch since that cut | | |
| a line was left at the door since that cut | | |

Where any one fails, nothing is said. It blocks nothing, and the session is not handed it. The first cut of a session has no summary before it to compare with.

---

### The hand-over

A hand-over is a label page, `hand-over.md`, whose label rows are carried as a message where no frame can be made; nothing else the page holds is carried.

`python3 crossing/handover.py <transcript> <hand-over.md>` writes `hand-over.words.md` beside it: for every message id the page names, what was said there, word for word from the transcript, each cut at 700 characters, and the ids the transcript does not hold. An id two messages of the transcript share gives neither, and the page names it as shared. A message the home keeps out is not on it: one struck, said while Crossings was off, or held by a session no person sat in. Where the home's record of when Crossings was off cannot be read or told, it holds no message.

It writes through `within`, for its owner alone, and only into a home the door believes: in any other folder, or through a project's `crossings` that is a link, it says so in one sentence, with exit status 1, and writes nothing. It is the person's to run, from their own terminal. The record is never changed.

Where the page is carried, what is given under each id its words page names is what the archive holds. A strike mends a words page line by line, or takes it away whole where it cannot be mended, and a whole session's strike takes every words page away ([Privacy](privacy.md)).
