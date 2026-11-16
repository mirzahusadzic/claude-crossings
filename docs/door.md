# The door

What a session and the person can reach of the store, what each is told and when, and the frame a session is handed. The door is `crossing/door.py`: a session reaches it through a small server, `crossing/serve.py`, and the person through `/crossings` or their own terminal.

---

### The session's tools

The server is started by the plugin's `.mcp.json` as `python3 -I crossing/serve.py`, one process a session. It speaks MCP over stdio, by hand, with the standard library alone, and asks for its seven tools to be loaded in front of a session rather than searched for. Every tool takes `home`: `here` (the default) or `ours`, the home on this computer ([The store](store.md)).

| Tool | Gives |
| --- | --- |
| `look` | the room, with no word needed: the days and how many messages each voice has on each, the labels by kind and how many, those misaligned or unresolved, the newest line left at the door with the work labels marked after it, and the eight newest labels about the work that are not cooled |
| `labels` | the labels themselves, newest first: with nothing named, those about the work and the lines at the door; or one kind (`relation`, `work`, `next`), one day, or labels by key, a stack with every line beneath it |
| `find` | the messages and labels that hold the words, all of them or, failing that, any; `voice` narrows it to the person's or the session's |
| `thread` | a message by its id in its place: what stood before and after it (`around`, two by default and fifty at most), numbered in the order said, with the labels resting there |
| `mark` | writes a label: one sentence, the ids it rests on, its kind (`relation`, or `work` by default) and whose it is (`his`, `both`, or `session` by default). For the first work label marked after the newest line left at the door, its answer adds, once a line: "The line at the door was left before this label: where it no longer holds, a new one can be left." |
| `leave` | writes a line for the session that wakes after the next cut: the session's own, resting on messages |
| `status` | what the store holds, in one line |

A label's day is the day of the newest message it rests on; a stack's is also the day of its own page.

The server answers from the home of the project it was started for (`CLAUDE_PROJECT_DIR`, else the folder it runs in), or from the folder `CROSSING_HOME` names. It is told neither which session calls nor which model, so it reads no transcript. The hook before each call of a door tool brings the archive up to that moment, and the hook before `mark` hands over the model ([Layers](layers.md)). Given alone to a harness without the plugin's hooks, the server holds only what was archived elsewhere, and its instructions say so.

No answer names a file or a folder: the server asks the door as `--bare`. A refusal is one sentence, and nothing is read or written for it:

| Event | The door's server |
| --- | --- |
| a session no person sits in calls | "The door is for sessions a person sits in, and this one is not, so nothing was read." |
| Crossings was never switched on in the project | "Crossings is not switched on for this project." |
| `home: ours` from a project not switched on, or switched off | the same sentence |
| a setting names a place inside the project, or no absolute path | that the setting was not followed |
| a file of the home is a link | "A file of this project's home is a link, so nothing was written." |
| `mark` or `leave` while the project is switched off | "not marked: Crossings is switched off for this project" |
| `mark` with an anchor the archive does not hold, a sentence over 4,000 characters, a sentence or an anchor that holds a character that is no text, a stack that breaks a rule, or a home another act holds for five seconds | "not marked:" and the reason |
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
| `labels` | the forty newest, and how many older ones there are; a sentence cut at 240 characters in a list, and given whole by its key; its state where it is not carried, and the stack it stands beneath |
| `labels`, nothing named | the standing lines counted by key and not listed: they are listed when asked for by kind or key |
| `look` | the standing lines by key and number alone; how many stand beneath how many stacks; misaligned and unresolved labels by key; a span off the record among the days, by its two moments |

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
| `/crossings status` | whether Crossings is on, and what the store holds |
| `/crossings look`, `frame` | the room, and the frame as it would be made now |
| `/crossings find <words>` | as the tool |
| `/crossings labels [words]` | as the tool; `relation` or `standing`, `work`, `door` or `next`, a day as `YYYY-MM-DD`, or keys |

A word the command does not know changes nothing and says what it takes. The words that show the store bring the archive up to the moment first.

---

### The person's verbs

`python3 crossing/door.py <verb>` from a shell, standing in the project or with `--cwd <project>`. Every verb takes `--home here|ours`.

| Verb | Does |
| --- | --- |
| `look`, `labels`, `find`, `thread` | as the tools; `find` also takes `--limit N` |
| `mark --kind --whose --anchors id,id <sentence>` | writes a label; one for the person or a standing line is kept in `shelled.txt`, and said by the person's next `status` |
| `frame [--size N]` | prints the frame |
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
| the server connects | what the door is; that what is said is kept by itself and labels are not; that lines can be stacked; to reach when the conversation calls for it, and to leave what the person told in confidence alone until they bring it up |
| it starts in a home that is on and holds no label at all | the welcome, once: what is kept by itself, and that labels and the line at the door are its own to write. Where `welcomed.txt` cannot be written, nothing is said |
| the person switches Crossings on while it runs | the welcome, where it is due; and that what is said is kept again, where it was told Crossings was off |
| the person switches Crossings off from it | that nothing said from now until it is on again is kept or can be reached, so to mark nothing of it. No other session is told |
| it comes through a cut | the waking note: which cut this is, to take its time, that nothing is gone from the record; to carry on a task the cut came in the middle of, and otherwise to answer as itself and briefly; and to reach through the door when something rests on what it does not hold |
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
| a session starts in a project whose `crossings/` folder was passed over | that it was passed over, once |
| the frame is carried as context | a short line naming how many labels and characters crossed |
| a cut's summary mostly retells the one before ([Cuts](cuts.md)) | one line, once a cut |
| a hook that counts a cut or brings the frame is running | the harness's status message for it: `Crossings · counting the cut`, or `Crossings · bringing the frame across` |

Nothing is blocked by any of these. A label for the person or a standing line marked from a shell, which no hook sees, is said by the person's next `status` instead, by key.

---

### The frame

The frame is what crosses a cut with the session, made from the store by `compose` in `crossing/frame.py`. It is about 9,000 characters. A home's `frame-size`, and `frame --size`, are held between 2,000 and 9,500 (`LEAST` and `MOST`), 9,500 being the most a hook may carry as context; the frame never exceeds it, whatever its lines hold.

It holds, in this order:

1. Its opening: that it is a frame made from the store, held as read and not as lived; how a line of it is read; and the door's tools by name.
2. Where other models made lines in this home, one sentence that says so, naming eight at most ([Layers](layers.md)).
3. The newest line left at the door: whole where the room allows, and otherwise as far as it does, with the words that say where it is whole. A line left through the door is at most 4,000 characters, so it crosses whole in a frame of the usual size. Beneath it, "Marked after this line:" and the work labels written after it, in the order they were written, so that a line older than the work it speaks of is seen as one.
4. The standing lines, whole while they fit, up to 80% of the frame.
5. The labels about the work, newest first, up to 90%.
6. By key, the standing lines that did not fit, how many more labels the store holds, and the labels that rest on what the archive no longer holds.
7. A few of the person's own words: their messages that the carried work labels and the line at the door rest on, newest first, each cut at 300 characters. Never a standing line's messages, a pasted text, a message that looks like it holds a key, or anything under an id two messages share.
8. How many messages and labels the store holds, from which day to which.

Of a stack it carries the top, with the keys of its lines in its brackets. A misaligned stack crosses with its lines, and says it is to be written again. An unresolved label is named by its key, and not carried.

A session started new is given a frame in words true for it: it lived none of what follows, meets the person first, and does not say it remembers. It is given nothing where the store holds no label to carry. A resumed or forked session holds its own context, and is given none; a cleared one is left clear, as the person asked by clearing it, and reaches through the door, with `look`, when the conversation calls for it. How the frame reaches a session at a cut depends on the home's `mode` and `carry` ([Cuts](cuts.md)).
