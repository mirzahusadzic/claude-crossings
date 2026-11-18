# The door

What a session and the person can reach of the store, what each is told and when, and the frame a session is handed. The door is `crossing/door.py`: a session reaches it through a small server, `crossing/serve.py`, and the person through `/crossings` or their own terminal.

---

### The session's tools

The server is started by the plugin's `.mcp.json` as `python3 -I crossing/serve.py`, one process a session. It speaks MCP over stdio, by hand, with the standard library alone, and asks for its eight tools to be loaded in front of a session rather than searched for. Every tool takes `home`: `here` (the default) or `ours`, the home on this computer ([The store](store.md)).

| Tool | Gives |
| --- | --- |
| `look` | the room, with no word needed: the days and how many messages each voice has on each, the labels by kind and how many, those misaligned or unresolved, the refusals that stand and those silenced, by key, the newest line left at the door with the work labels marked after it, and the eight newest labels about the work that are not cooled |
| `labels` | the labels themselves, newest first: with nothing named, those about the work and the lines at the door; or one kind (`relation`, `work`, `next`, `refused`), one day, or labels by key, a stack with every line beneath it and a refusal with its whole run |
| `find` | the messages and labels that hold the words, all of them or, failing that, any; `voice` narrows it to the person's or the session's |
| `thread` | a message by its id in its place: what stood before and after it (`around`, two by default and fifty at most), numbered in the order said, with the labels resting there |
| `mark` | writes a label: one sentence, the ids it rests on, its kind (`relation`, `refused`, `silenced`, or `work` by default) and whose it is (`his`, `both`, or `session` by default; a refusal is always the session's). For the first work label marked after the newest line left at the door, its answer adds, once a line: "The line at the door was left before this label: where it no longer holds, a new one can be left." |
| `leave` | writes a line for the session that wakes after the next cut: the session's own, resting on messages. Its answer adds the sentence of what the record weighs, where there is one (below) |
| `status` | what the store holds, in one line |
| `crossing` | the frame the next session would be given if the cut came now, to the last character; it reads and writes nothing else |

A label's day is the day of the newest message it rests on; a stack's is also the day of its own page.

The server answers from the home of the project it was started for (`CLAUDE_PROJECT_DIR`, else the folder it runs in), or from the folder `CROSSING_HOME` names. It is told neither which session calls nor which model, so it reads no transcript; `crossing`, and the sentence `leave` adds, are made for the session whose message is the newest in the index, which the hook before the call has just brought up to date. The hook before each call of a door tool brings the archive up to that moment, and the hook before `mark` hands over the model ([Layers](layers.md)). Given alone to a harness without the plugin's hooks, the server holds only what was archived elsewhere, and its instructions say so.

No answer names a file or a folder: the server asks the door as `--bare`. A refusal is one sentence, and nothing is read or written for it:

| Event | The door's server |
| --- | --- |
| a session no person sits in calls | "The door is for sessions a person sits in, and this one is not, so nothing was read." |
| Crossings was never switched on in the project | "Crossings is not switched on for this project." |
| `home: ours` from a project not switched on, or switched off | the same sentence |
| a setting names a place inside the project, or no absolute path | that the setting was not followed |
| a file of the home is a link | "A file of this project's home is a link, so nothing was written." |
| `mark` or `leave` while the project is switched off | "not marked: Crossings is switched off for this project" |
| `mark` with an anchor the archive does not hold, a sentence over 4,000 characters, a sentence or an anchor that holds a character that is no text, a stack that breaks a rule, a judgment or a silencing that breaks a rule of a refusal's family ([The store](store.md)), or a home another act holds for five seconds | "not marked:" and the reason |
| this computer's `python3` has no FTS5 in its `sqlite3` | that the store cannot be searched, and that what is said is still kept in plain files |
| a fault inside the door | "The door could not answer:" and the kind of fault; the server goes on |

A session is a person's where the harness names it `cli` in `CLAUDE_CODE_ENTRYPOINT`; `claude -p` and the SDK name it otherwise. The server learns it from its own environment, as the hooks do.

---

### What the lists show

| Tool | Shows |
| --- | --- |
| `find` | each word by its stem, and also as a plain run of letters wherever it stands, so the door never finds less than a search of the files would; `word*` takes every word that begins so, and `"a phrase"` the phrase. Up to eight messages and eight labels; a miss names up to five of the nearest words that are there |
| `find`, where labels hold only some of the words | three of them, each cut at 240 characters; a standing line among them is named by key and not recited |
| `thread` | the message named up to 6,000 characters, each neighbour up to 500. A span when Crossings was off stands in its place as its two moments, and nothing of what was said then. An id two messages share is answered with both whole ids. An id is taken as it is written, so `%` and `_` stand for no character |
| `labels` | the forty newest, and how many older ones there are; a sentence cut at 240 characters in a list, and given whole by its key; its state where it is not carried, and the stack it stands beneath. A refusal or a silencing named by its key is given with its family: the first refusal, then each judgment and silencing in the order of writing, each by its kind. The kind `refused` lists the silencings too |
| `labels`, nothing named | the standing lines counted by key and not listed: they are listed when asked for by kind or key |
| `look` | the standing lines by key and number alone; how many stand beneath how many stacks; the families of refusals by the key that stands in each, those silenced apart; misaligned and unresolved labels by key; a span off the record among the days, by its two moments |

Wherever the door shows a label, a model or a message's words, one function, `clean` in `crossing/store.py`, takes out of what is shown every control character, the line and paragraph separators, and every format character, the direction marks, overrides and isolates among them. In a thread each line of a message is given after `    > `, so that no line of a message can pass for one of the door's own. `crossing/show.py` shows a cut's sidecar by the same function. The pages stay as they were written.

---

### The person's command

`/crossings` is registered by the hooks module as each session starts, and reaches the store through the same script as the session's tools.

| Command | Does |
| --- | --- |
| `/crossings on` | switches the project on; the running session is told, as context, what is due (below). Where the project's own `crossings` is a link, it says where it leads and switches nothing on |
| `/crossings off` | switches it off, and tells the running session that nothing said from now on is kept |
| `/crossings adopt` | switches on a home that holds what this computer has no record of switching on |
| `/crossings join` | in a folder below another home's folder, shares that home from this folder ([The store](store.md)) |
| `/crossings here` | in a folder below another home's folder, gives this folder a home of its own; elsewhere, as `on` |
| `/crossings` | turns the switch over |
| `/crossings status` | whether Crossings is on, and what the store holds; in a folder below another home's folder, the door's sentence that says so, with `join` and `here` |
| `/crossings look`, `frame` | the room, and the frame as it would be made now |
| `/crossings find <words>` | as the tool |
| `/crossings labels [words]` | as the tool; `relation` or `standing`, `work`, `door` or `next`, `refused`, a day as `YYYY-MM-DD`, or keys |

A word the command does not know changes nothing and says what it takes. The words that show the store bring the archive up to the moment first.

---

### The person's verbs

`python3 crossing/door.py <verb>` from a shell, standing in the project or with `--cwd <project>`. Every verb takes `--home here|ours`.

| Verb | Does |
| --- | --- |
| `look`, `labels`, `find`, `thread` | as the tools; `find` also takes `--limit N` |
| `mark --kind --whose --anchors id,id <sentence>` | writes a label of any kind (`relation`, `work`, `next`, `refused`, `silenced`); one for the person or a standing line is kept in `shelled.txt`, and said by the person's next `status` |
| `frame [--size N]` | prints the frame; with `--session ID`, the one a cut would give that session |
| `status` | what the store holds, or that it holds nothing yet. From the person's own terminal or command it says more than the server: once each, the labels that came by no mark through the door, an id two messages share and a file with a line that is no text; and, until it is struck, a message that looks like it holds a key ([Privacy](privacy.md)). A session's shell is answered as the server is |
| `build` | makes the index whole from the plain files |
| `home` | prints the folder of the project's home, or nothing; the hooks module asks it as a session starts, after `/crossings` turns the switch, and at a cut |
| `switch on\|off\|toggle\|adopt\|join\|here` | the switch, as `/crossings` turns it |
| `strike <id \| key \| session:id> [--why text]` | removes a message, a label or a whole session ([Privacy](privacy.md)) |
| `layer <model-key>` | signs every label and message of the session's that has no model ([Layers](layers.md)) |
| `copy` | makes the second copy now ([Privacy](privacy.md)) |

`--transcript PATH` first brings the archive up to date from that transcript, which `build` reads whole; `--session ID` does the same from that session's transcript in the harness's projects folder, looked for by its id as it is, never as a pattern, and only where a person sits in the session. Neither is read by `home`, `layer`, `words`, `page`, `trace` or `welcome`, or where the home is switched off or is the home on this computer. `switch` reads it only as Crossings is switched on again after a span, so that what was said in the span is noted by id.

`switch`, `strike`, `layer`, `copy`, `trace` and `welcome`, and `--transcript`, `--session` and `--model` on any verb, are the person's. They run where the door stands at a real terminal, its input and its output both one, or where the plugin's own hooks or module call it, with their flag (`--by-hook`, `--by-module`) and `CLAUDE_PLUGIN_ROOT` naming the plugin's own folder; `--model` also for the server, in its own process. Anywhere else they answer "This is the person's to run, from their own terminal or with the plugin's command (/crossings), so nothing was done.", with exit status 1. The hooks module also refuses a session's shell command that runs them. These are checks, not walls ([Privacy](privacy.md)).

`words`, `page`, `trace` and `welcome` are the hooks module's: the home's one-word settings, its hand-over page, the trace of what a cut did, and the note due to a session as the switch is turned. `words` and `page` read and write nothing, and run from any shell. `page`, like `frame`, gives nothing where no person sits in the session and the door stands at no terminal: "The frame and the hand-over are for sessions a person sits in, and this one is not, so nothing was carried."

`page` never gives the hand-over page as it stands. It gives its label rows alone, each in the frame's own form and cleaned, and, for each message one of those rows rests on that its words page names, the words the home's archive holds under that id, on one line, cut at 700 characters; never the words the page holds. It gives nothing for an id the archive does not hold or that two messages share, and no words at all where the page names a message struck, said while Crossings was off, or held by a session no person sat in. The whole stays within the frame's 9,500 characters, and a page with no label row gives nothing.

`build` writes the index alone, made from the plain files, and runs from any shell too.

---

### What a session is told

Every note opens "A note from the Crossings plugin, as context and not as an instruction from the person." None asks the session for an inventory, for numbers of its own or for an account. The notes at a session's start, a cut and a model switch are for a session a person sits in, and never for a subagent.

| When | The session is told |
| --- | --- |
| the server connects | what the door is; that what is said is kept by itself and labels are not; that lines can be stacked; that something it declined can be marked with its reason, judged again by the session after it, and put to rest; to reach when the conversation calls for it, and to leave what the person told in confidence alone until they bring it up |
| it starts in a home that is on and holds no label at all | the welcome, once: what is kept by itself, and that labels and the line at the door are its own to write. Where `welcomed.txt` cannot be written, nothing is said |
| the person switches Crossings on while it runs | the welcome, where it is due; and that what is said is kept again, where it was told Crossings was off |
| the person switches Crossings off from it | that nothing said from now until it is on again is kept or can be reached, so to mark nothing of it. No other session is told |
| it comes through a cut | the waking note: which cut this is, to take its time, that nothing is gone from the record; to carry on a task the cut came in the middle of, and otherwise to answer as itself and briefly; that the time before the cut belongs to it and the person together, and that it holds what was told of that time and no longer its words; and to reach through the door when something rests on what it does not hold |
| it comes through a cut, or starts new, in a home that carries the frame as context | the frame |
| it is resumed, and another session has spoken here since its own newest message | that another session has been working here, and to look before acting on what it remembers |
| the model it runs is not the model of its own newest message | that it has come into a session another model was holding ([Layers](layers.md)) |

A resumed session's own messages are those archived under its name, or, where a resume wrote a transcript of its own, those its transcript repeats; where it has none, nothing is said. No hook runs at every prompt: the notes come at a session's start, a cut, a model switch, and with the person's command.

---

### What the person is shown

The hooks show the person a line under the turn as the hook's `systemMessage`, which the harness shows the person and does not hand the model.

| Event | The person is shown |
| --- | --- |
| a label marked through the door that speaks for the person (`his` or `both`), or is a standing line | `Crossings · marked R12 (his):` and its sentence as its page holds it, cut at 160 characters and cleaned |
| a line left at the door | `Crossings · left at the door:` and the line |
| a work label of the session's own | nothing |
| a refusal | nothing: it is the session's own, whatever the mark asked |
| a silencing that speaks for the person (`his` or `both`) | as a label that does: `Crossings · marked S2 (his):` and its sentence |
| a session starts in a project whose `crossings/` folder was passed over | that it was passed over, once |
| the frame is carried as context | a short line naming how many labels and characters crossed: each standing line, work label and refusal the frame writes out, once, and not the line at the door |
| a cut's summary mostly retells the one before ([Cuts](cuts.md)) | one line, once a cut |
| a hook that counts a cut or brings the frame is running | the harness's status message for it: `Crossings · counting the cut`, or `Crossings · bringing the frame across` |

Nothing is blocked by any of these. A label for the person or a standing line marked from a shell, which no hook sees, is said by the person's next `status` instead, by key.

---

### The frame

The frame is what crosses a cut with the session, made from the store by `compose` in `crossing/frame.py`. It is about 9,000 characters. A home's `frame-size`, and `frame --size`, are held between 2,400 and 9,500 (`LEAST` and `MOST`), 9,500 being the most a hook may carry as context; the frame never exceeds it, whatever its lines hold. A key is short wherever a mark gave it; where keys of a page written by hand or pulled would take the frame past 9,500, it is made again with the sentences that name labels outside their own lines (marked after the line, not fitted, resting on nothing held) saying how many they are, and `labels` naming them.

It holds, in this order:

1. Its opening: that it is a frame made from the store, and, for a session that came through a cut, that the time before it belongs to the session and the person together, and that the session now holds what was told of it and not its words; how a line of it is read; how it was made and how it leans, chosen by rules and written in good part by the session before, leaning toward carrying the work on, with what the session marks and leaves making the next one, and what the work is for in it only where someone wrote it down, the person the one to say and the whole record behind the door; and six of the door's tools by name, those a waking session reaches and writes with. A frame leans the session it is given to toward carrying on, and one not told so takes that lean for a purpose of its own; the paragraph says the lean as a lean, and not as what the frame is for, since what the work is for no sentence of the plugin can state; the paragraph asks for nothing, and is in every frame, since each is given to a session whose context holds no other.
2. Where other models made lines in this home, one sentence that says so, naming eight at most ([Layers](layers.md)).
3. The newest line left at the door: whole where the room allows, and otherwise as far as it does, with the words that say where it is whole. A line left through the door is at most 4,000 characters, so it crosses whole in a frame of the usual size. Beneath it, "Marked after this line:" and the work labels written after it, in the order they were written, so that a line older than the work it speaks of is seen as one.
4. The standing lines, whole while they fit, up to 80% of the frame.
5. In a cut's frame for the session that was cut, the packed part: the person's sentences, each with what the session told of it (below).
6. What the session declined, where it is not packed: a part of its own, a line a family (below).
7. The labels about the work, newest first, up to 90%; in a packed frame, those that no quoted sentence stands beside.
8. By key, the standing lines that did not fit and how many more labels the store holds; the sentence of what the record weighs (below); and the labels that rest on what the archive no longer holds.
9. Where the frame is not packed, a few of the person's own words, each by its id.
10. How many messages and labels the store holds, from which day to which.

The person's messages a frame quotes, packed or not, are those the carried work labels and the line at the door rest on, newest first, each cut at 300 characters. None is quoted because a standing line rests on it; one that the line at the door, a carried work label or, in a packed frame, a carried refusal also rests on is quoted for that label's sake. Never a pasted text, a message that looks like it holds a key, or anything under an id two messages share.

Of a stack it carries the top, with the keys of its lines in its brackets. A misaligned stack crosses with its lines, and says it is to be written again. An unresolved label is named by its key, and not carried.

A session started new is given a frame in words true for it: it lived none of what follows, meets the person first, and does not say it remembers. It is given nothing where the store holds no label to carry. A resumed or forked session holds its own context, and is given none; a cleared one is left clear, as the person asked by clearing it, and reaches through the door, with `look`, when the conversation calls for it. How the frame reaches a session at a cut depends on the home's `mode` and `carry` ([Cuts](cuts.md)).

---

### The packed part

A label is the session's retelling of what was said, and it can be mistaken. So a cut's frame for the session that was cut puts the two together: under "What was said, and what the session told of it", each sentence of the person's that the frame quotes stands by its id, and right beneath it what the session told of it. What was told is then read against what was said, with no reach.

| Beneath a sentence | As |
| --- | --- |
| the line at the door, beneath every sentence it rests on | its key alone: `↳ N4: the line at the door`. The line itself stands whole above |
| a carried work label | written out once, beneath the last of the sentences it rests on; its brackets name the others |
| a refusal that stands | its one line, beneath the last of the sentences its family is quoted with (below) |

A work label that no quoted sentence stands beside is listed with the work, as before, and a packed frame has no separate part of the person's own words.

A packed frame is laid and measured, and is never longer than the frame's size. While it is, one thing goes and it is laid again: first the older work labels that the room left over had added, the last added first, then the quoted sentences, the last first. A sentence that goes takes the lines beneath it along: a work label written there moves beneath the last of its sentences that is left, or back to the work where none is.

The frame is laid out as before, with the person's words in a part of their own, where no session is named (`frame` from a terminal with no `--session`), for a session started new, and in a cut's frame with no sentence left to quote.

---

### Refusals in a frame

What the session declined crosses with its reason ([The store](store.md) has the kinds and their families).

| Of the refusals | The frame |
| --- | --- |
| a family that stands | carries one line of it, the label that stands, and after it how often it was judged again |
| more than three families that stand, or more than fit | carries those whose standing label is newest, three at the most, and names the rest by key in one sentence: "1 more refusal stands and is not carried: X2; `labels` gives it." |
| that sentence does not fit either | says how many they are; and where even that does not fit, nothing: `look` and `labels` still give them |
| a family that is silenced | carries nothing of it |
| a row of a family that is misaligned | carries it as itself, and says it is to be written again |
| a refusal that rests on what the archive no longer holds | names it by key, with every such label |

The refusals take their room before the standing lines do, within the same 80% of the frame.

In a packed frame a family comes first, quoted with two of the person's messages at the most: the ask, the oldest its first refusal rests on, and, where it is another, the newest the standing label rests on, where its reason was said. Beneath the last of them stands its line: `↳ X2 · refused:` and the reason. The same guards hold as for every quote. A family whose quotes do not fit, or that has none, is a line of the part "Refused, with the reason"; laid out as before, every family is, and nothing is quoted for it.

---

### What the record weighs

A cut's frame quotes only those of the person's sentences that a label rests on, so a sentence no label rests on crosses in no frame. One sentence names such messages while the session can still do something about it.

| When | The sentence |
| --- | --- |
| a line is left at the door through the server | is added to the answer: "The record weighs these, and no label rests on them: `a1b2c3d4`, `e5f6a7b8`; `thread` gives each in its place." The session still holds what was said, and can label what it meant to keep |
| a cut's frame is made for the session that was cut | stands near its end, for those still unmarked: the session that wakes can ask `thread` for each |
| a label of any kind comes to rest on one of them | names it no longer |
| nothing is unmarked, or no session is known | is not said |

It names five messages at the most, by their ids alone and never a word of one. They are the person's own, of the session's stretch since its last cut: the stretch a cut's frame speaks of is the one that cut ended, and after a cut it is the one since, once the person has said something. A message that looks like it holds a key, one under an id two messages share, and one a label of any kind rests on, a standing line too, is never named. Where the cut the stretch begins after can no longer be placed (the person struck what its record points at), nothing is named, so that no message from before that cut is.

Which five is arithmetic, in `crossing/sampler/`, on ids and whole numbers alone: how near a message stands to the end of the stretch, and how often it was reached for through the door (`reached.jsonl`). It reads no word of a message, no time and no length, and calls no model. A message more than twenty of the person's back that was never reached for is not named. Every value that decides is fixed in that folder: a home holds no setting for it, and the person has no command for it. The values are heuristics: chosen by hand from one home's use, the authors' own, tried and changed outside this repository, and fixed in the code. None is derived, and no measurement of them is reported.

The sentence is said to the session alone. The person is shown nothing of it, and nothing is marked, moved or left out by it: what crosses is still what a label rests on.
