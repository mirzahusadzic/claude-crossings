# Cuts

What Crossings does when the harness compacts a session: the count and its page, the modes, the retelling line, and the hand-over. All of it is for a project where Crossings is on. Switched off, no cut is counted, noted or answered.

[The words](words.md) says in a line or two what each of the tool's own words means.

---

### At a cut

A cut comes to Crossings at three moments of the harness's. The hooks module answers the first, and the plugin's hooks the other two.

| Moment | Crossings |
| --- | --- |
| the harness is about to cut | Answers the cut as the home's `mode` and `carry` ask ([the modes](#the-modes)). |
| the session starts again (`SessionStart`, source `compact`) | Gives a session a person sits in the waking note, about this cut by its number. Where the home carries the frame as context, the frame too. |
| the harness hands over its summary (`PostCompact`) | Counts the cut and writes its page ([the count](#the-count)). |

A hook that fails ends quietly, with exit status 0 and a line in the error log. A failure inside the module leaves the cut to the harness.

#### As the harness is about to cut

The hooks module answers the cut, and reads the home through the door to do it.

- **The home.** It asks the door where the home is, for the guard on the archive's files ([Privacy](privacy.md#the-archives-own-files)).
- **The words.** It reads the home's `mode` and `carry` through the door, and answers the cut as they ask.
- **A subagent's own cut.** It is never touched.
- **A summary made ahead of time.** Only the home's words are read through the door. Where they answer a cut, the summary is asked for [the ledger](#the-summarys-ledger). Nothing else is done there.

#### As the summary is handed over

The `PostCompact` hook does four things once the summary is handed over. Where the hook's input names a subagent, it does nothing at all.

- **The count.** In any session of a home that is on, it counts the cut and writes its page.
- **The archive.** Only for a session a person sits in, it brings the archive and the index up to date.
- **The second copy.** For such a session, it also renews the second copy where one is set.
- **The retelling line.** It shows the person one line where the summary mostly retells the one before ([below](#a-summary-worn-down-by-retelling)).

#### Which cut it is

The waking note names this cut by its number, whichever of the two hooks the harness calls first. A summary handed over may open as one the transcript already holds:

- **Nothing said since.** It is that cut again only where nothing of either voice was said after it.
- **Something said since.** It is a later cut of its own, with the next number, though it retell the one before word for word.

---

### The count

Every cut is counted by script, from the session's transcript. It is written to a page in the home, `<session>-cut-<n>.md`, with a sidecar beside it, `<session>-cut-<n>.json`. The page holds counts and pointers, and no text of either voice:

| The page says | From |
| --- | --- |
| the kind of cut and its trigger | the harness |
| tokens before and after, and how long the cut took | the harness, where it gives them |
| the summary's length in characters | the summary |
| how much of the summary repeats the summary of the session's cut before | the summary, and the earlier cut's sidecar |
| the session, the transcript, and the line the cut stands at | the transcript |
| for each voice, what the summary holds of it (below) | the transcript and the summary |
| how many of the person's messages were typed at the prompt, and how many sent while a turn ran | the transcript |
| what share of the record the two voices were by characters, tool calls and their results being the rest | the transcript |
| the ten least held messages of each voice, by id, line, length and share held | the transcript and the summary |

For each voice, the page says:

- its messages since the cut before.
- how many of them the summary holds whole.
- how much of its text the summary holds, by characters.
- how many of its sentences of 40 characters or more the summary holds.
- how many of its messages the summary holds nothing of.

"Word for word" is the whole claim: a run of 24 characters or more that the summary also holds. A message under 12 characters is too short to judge, and is counted as not held. A summary can carry a message in other words and get no credit here.

#### What the count covers

The count covers only what stood since the cut before, or since the start, one message a row. It leaves out what the archive leaves out:

- every message said while the switch was off.
- a subagent's rows, with their tool calls and results.
- every row whose id is no name.

Where the count has nothing to stand on, or not all of it, the page says so:

| Event | The page |
| --- | --- |
| the count runs out of its eight seconds | Says not all of it was counted, and gives the numbers for the messages reached. |
| the stretch holds no message of either voice (a session just forked) | Says it was not counted, and guesses nothing. |
| no summary was handed over | Says there is nothing to compare against, and how many messages stood before the cut. |
| the record of when Crossings was off cannot be told ([Privacy](privacy.md#off-the-record)) | Lists nothing said, by id or by length. Says that what was said off the record cannot be told from the rest. |

#### The sidecar

The sidecar beside each page holds what the next cut compares with. Like the page, it keeps no text of either voice.

- **Pointers.** Every pointer, the session's id and the transcript's path.
- **The retelling line.** The figures the retelling line rests on.
- **The summary's runs.** Its runs of 24 characters, as digests keyed with the home's own key (`said/runs.key`). So no text of either voice is kept anywhere new, and a digest cannot be checked against a guess.
- **The next cut.** The next cut of the same session compares its summary with these digests.
- **Another key.** A sidecar made with another key, or whose digests cannot be read, is compared with nothing.

#### The cuts on record

Print the cuts on record, a few lines each, from the sidecars alone:

```sh
python3 crossing/show.py [project] [--session ID]
```

A sidecar that cannot be read, or is of another shape than the count writes, is passed over in one line that names it. The others are shown.

#### Reading a message back

Read up to 20 messages back from a transcript, by id or by line:

```sh
python3 crossing/read.py <transcript> <id or line> [--cwd DIR]
```

- **What it shows.** Only what was said, cleaned as the door shows a message. Never a reasoning block, tool traffic or a harness note.
- **An id.** It gives a message only where its start names one row.
- **What the home keeps out.** In a project the person switched Crossings on for, on or off now, nothing its home keeps out is shown. That is a message struck, said while off, or held by a session no person sat in.
- **A link.** A home with a link below it is refused.
- **Who runs it.** It is the person's to run, from their own terminal, as the door's own verbs are.

---

### The modes

Two plain files of the home decide how a cut is answered, `mode` and `carry`, one word each. What the frame holds is on its own page, [The frame](frame.md).

| `mode` | `carry` | At a cut |
| --- | --- | --- |
| `native`, missing, or a word not known | either | The cut is the harness's as it made it, and no frame crosses. The count and the waking note still come. |
| `beside` | `note` | The cut stands as the harness made it, whatever set it off. The hook brings the frame as context when the session starts again. |
| `beside` | `message`, missing, or a word not known | The frame goes into the cut's answer as a message, after the harness's summary. |
| `own` | either | At a cut the harness did not start by itself, the frame takes the summary's place. An earlier cut's summary at the head of the conversation is carried on before it. |
| `own` | either | At an automatic cut, as `beside` with `message`. |

Under `beside` and `note`, the same files give a session started new its frame.

#### The summary's ledger

Wherever the harness makes the summary under `beside` or `own`, ahead of time too, the module asks it for a ledger and nothing else. The record keeps the words and the frame carries them, so the summary need not retell them. It asks for:

- what the person asked, in their own words.
- whether each task is finished, and where an unfinished one stands.
- the files it touched.
- the section "All user messages" left empty, nothing retold and no next step suggested.
- last, the standing constraints the person set, word for word.

What the person types after `/compact` still applies. It follows the ledger after an empty line, unchanged, and so comes last.

No ledger is asked where nothing would stand beside it. The summary is then asked for what the cut came with:

- **`native`.** No frame crosses, so the summary is left to retell.
- **A subagent's own cut.** It is never touched.
- **A session no person sits in.** Nothing of it is archived, and no frame is carried to it.
- **No frame and no hand-over.** A message was to carry the frame, and the door gave neither.

Under `own`, a cut the person starts has no summary, and so no ledger. The frame stands in its place.

The ledger is a request, given to the harness's summarizer as the cut's instructions. The summarizer is not bound by it, and may not follow it.

Crossings reads the summary only once it is handed over, and then only to count it, as the count above says. Nothing checks whether it is a ledger, and nothing is done where it is not.

#### A home's first modes

A home `/crossings on` makes outside the project starts with `beside` and `note`. So does a project's own `crossings/` folder that is empty as it is first switched on. Switching off and on again never writes either file anew.

- **Empty.** It holds no folder, and no file but those whose names begin with a dot (`.DS_Store`, `.gitkeep`, `.gitignore`). Those do not count.
- **A folder that holds anything else.** Whichever word switches it on, no `mode` or `carry` is written into it. With no `mode` file its cuts are `native`.
- **Taken by `adopt` alone.** A folder that holds a file other than a `.gitignore`, where this computer has no record of switching it on.
- **The frame there.** A person who wants it writes `mode` and `carry` ([Settings](settings.md)).

#### How the frame is carried

A frame carried as a message is handed to the harness as a user message in the cut's answer. Carried as a note, nothing is filed as a message.

- **Its opening.** It opens "A note from the Crossings plugin". The plugin's reader never takes such a row for the person's words, nor one that opens with the older "A note from the Crossing plugin".
- **No frame.** Where a message is to carry the frame and the door gives none, the home's `hand-over.md` goes instead. It goes as `door.py page` gives it (its label rows, with the archive's words for the messages they rest on), after a note that says what it is.
- **Neither.** The cut is left as the harness made it.
- **What was done.** The module writes what it did into `last-cut.json`, and the frame hook into `last-carry.json`. Neither is needed for the cut to go on.

---

### A summary worn down by retelling

The harness carries its summary from cut to cut, and retells it each time. Where most of a long summary repeats the one before, and the last stretch is marked, the person is shown one line under the turn. It says three things:

- that the session has been cut this many times.
- that most of its summary now retells the one before.
- that a new session would start from the store alone, with nothing lost.

It is shown once a cut, where all of these hold:

- **Long.** The summary is at least 20,000 characters, or what `retelling-length` sets.
- **Mostly retold.** At least 60% of it repeats the summary of the session's cut before, by runs of 24 characters, or the share `retelling-share` sets.
- **Marked.** A label other than a line at the door rests on a message of the stretch since that cut.
- **Left at the door.** A line was left at the door since that cut.

Where any one fails, nothing is said. It blocks nothing, and the session is not handed it. The first cut of a session has no summary before it to compare with.

---

### The hand-over

A hand-over is a label page, `hand-over.md`. Its label rows are carried as a message where no frame can be made. Nothing else the page holds is carried.

Write the words page beside it:

```sh
python3 crossing/handover.py <transcript> <hand-over.md>
```

It writes `hand-over.words.md` beside the page. For every message id the page names, it gives what was said there, word for word from the transcript, each cut at 700 characters.

- **Ids not held.** It names the ids the transcript does not hold.
- **A shared id.** An id two messages of the transcript share gives neither, and the page names it as shared.
- **What the home keeps out.** A message struck, said while Crossings was off, or held by a session no person sat in is not on it.
- **A record that cannot be told.** Where the home's record of when Crossings was off cannot be read or told, it holds no message.

#### Where it writes

It is the person's to run, from their own terminal. The record is never changed.

- **For its owner alone.** The words page is written for its owner alone.
- **Only into a home the door believes.** In any other folder, or through a project's `crossings` that is a link, it says so in one sentence. It exits with status 1, and writes nothing.

#### What is carried of it

Where the page is carried, what is given under each id its words page names is what the archive holds. A strike mends a words page line by line, or takes it away whole where it cannot be mended. A whole session's strike takes every words page away ([Privacy](privacy.md#striking)).
