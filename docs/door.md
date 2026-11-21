# The door

What a session and the person can reach of the store, and what each is told and shown. The door is `crossing/door.py`, which a session reaches through a small server, and the person through `/crossings` or their own terminal. The frame that crosses a cut has a page of its own, [The frame](frame.md).

[The words](words.md) says in a line or two what each of the tool's own words means.

---

### The session's tools

A session reaches the store through eight tools. Every tool takes `home`: `here`, the default, or `ours`, the home on this computer ([The store](store.md)). After a cut, `look` is the place to start, and `labels`, `find` and `thread` go on from there.

| Tool | Gives |
| --- | --- |
| `look` | The room, with no word needed: the days, the labels by kind, and the newest about the work. |
| `labels` | The labels themselves, newest first: by kind, by day or by key. |
| `find` | The messages and labels that hold some words, each by its id. |
| `thread` | A message by its id, in its place among those said before and after it. With a `role`, the pair it stands in (below). |
| `mark` | Writes a label: a short line, the ids it rests on, its kind, and whose it is. |
| `leave` | Writes a line for the session that wakes after the next cut. The line is the session's own, resting on messages. |
| `status` | What the store holds, in one line. |
| `crossing` | The frame the next session would be given if the cut came now, to the last character. It reads and writes nothing else. |

#### What `mark` and `leave` write

`mark` and `leave` are the two tools that write. Both ask for short writing, since a frame has little room. Each answer can carry a sentence more.

- **A label's kind.** `mark` writes a `relation`, `refused` or `silenced` label, or `work` by default.
- **Whose it is.** `mark` takes `their`, `both`, or `session` by default. A refusal is always the session's.
- **A long label.** A work label or a standing line longer than 240 characters gets one sentence more, after its key. It says how long the label is, and that a frame may have no room for it.
- **A label the person is shown.** There the sentence comes from 160 characters, and says the person is shown 160 of it. That holds for a mark through the door's server.
- **A long line.** A line left at the door longer than 900 characters gets one sentence more. It says how long the line is, and that it takes room from the standing lines, the work and the person's own words.
- **Written all the same.** A long label or line is written whole, and nothing is refused or cut for its length below 4,000 characters. A refusal and a silencing are never told so: their sentence is the reason.
- **A line overtaken.** The first work label marked after the newest line left at the door gets one sentence more in `mark`'s answer. It is said once a line: "The line at the door was left before this label: where it no longer holds, a new one can be left."
- **What the record weighs.** `leave`'s answer adds the sentence of [what the record weighs](frame.md#what-the-record-weighs), where there is one.

#### What `crossing` adds

Where the frame sets the session's turns beside the person's sentences, one sentence follows it, apart from it. It says how many characters the turns, the sentences quoted for them alone and the opening's words for them take. It also names the labels and the person's sentences the frame would carry without them ([the sentence after the frame](frame.md#the-sentence-after-the-frame)).

#### A pair: `thread` with a role

With a `role`, `thread` gives the pair a message stands in, in place of the messages around it. A pair is a turn of one voice, with the other voice's next turn in the same session beneath it, in answer. `around` then does nothing.

- **A turn.** Every message one voice said in a row in one session, until the other spoke. A text the person pasted belongs to the message it came in, and breaks no turn.
- **The roles.** They are named from the session's side, since the session calls. `pair:them` is the pair headed by the person's turn, and `pair:me` the one headed by the session's.
- **When to ask `pair:them`.** A session asks it to read what it answered to something the person said.
- **When to ask `pair:me`.** A session asks it to read how the person took something it said.
- **The pair an id gives.** Named by a message of the heading voice, or a text pasted into one, it is the pair that message's turn heads. Named by one of the other voice, it is the pair its turn answers, headed by the turn right before it.
- **One pair at most.** So an id and a role give one pair at most. Every id of a pair's head or of its answer gives that pair, with that role.
- **No pair.** A message of the session's first turn has no pair with `pair:them`, nor one of the person's first turn with `pair:me`. One sentence says so, and names the role that gives the pair it heads.
- **A role that is neither.** It is refused in one sentence.
- **No message.** An id that names no message, or one two messages share, is answered as without a role. So is a call with no id.

In [the made-up store](told.md#thread-id-dddddddd-role-pairthem), the session said `bbbbbbbb`, the person then `dddddddd`, and the session `eeeeeeee`:

- **`pair:them`, on `dddddddd` or on `eeeeeeee`.** The person's `dddddddd` heads it, with the session's `eeeeeeee` beneath.
- **`pair:me`, on `bbbbbbbb` or on `dddddddd`.** The session's `bbbbbbbb` heads it, with the person's `dddddddd` beneath.
- **`pair:me`, on `eeeeeeee`.** The session's `eeeeeeee` heads it, and one sentence says the person said nothing after it.

The answer holds, in this order:

1. A first line: what was asked, the id and the role, whose turn heads the pair, and how many messages each side holds.
2. Each message, numbered through the pair in the order said, with the one named marked.
3. After a message of the person's, each text pasted into it, by its id and its length alone, never its text.
4. Where the answer is empty, a sentence that the other voice said nothing after it in that session.
5. A closing line with the ids the pair before this one and the pair after it begin at, each where there is one. It names the role that gives them, the other role, since the other voice's turn heads each.
6. The labels resting on any message of the pair, by key alone. Two or more lines left at the door among them are counted, not listed, with the newest by its key.
7. One more line, only where a label rests on a text pasted into the pair. It names each such paste by its id with the keys on it, counting lines left at the door alike.

A pasted text is no message of the pair. A label on a paste alone stands on that line alone, and one on a message of the pair as well stands on both. Both lines speak of the whole pair, whichever id named it, also on a page.

#### The person's side, by name

Wherever a label's owner is printed, the person's is `theirs`. A session names the person's side `their`, in `voice` and `whose`. It names the pair the person's turn heads `pair:them`.

`his` and `pair:him`, as they were spelled before, are still taken and mean the same. An answer names a role back as `pair:them`. Neither spelling changes what a home keeps.

---

### What the lists show

What `find`, `thread`, `labels` and `look` show, and where each stops. Whatever they show is cleaned first (below). A label's state, as cooled or misaligned, is one of [the four states](store.md#the-four-states).

#### `find`

`find` looks for the messages and labels that hold the words: all of them, or failing that, any.

- **A word.** Each is found by its stem, and also as a plain run of letters wherever it stands. So the door never finds less than a search of the files would.
- **A prefix or a phrase.** `word*` takes every word that begins so, and `"a phrase"` takes the phrase.
- **One voice.** `voice` narrows it to the person's messages or the session's.
- **How many.** Up to eight messages and eight labels.
- **A message.** It is shown by a stretch around the words, with the labels resting on it.
- **An excerpt.** Where a message is shown in part, `…` stands where it was cut. The answer then closes with "These are excerpts where … stands; the record holds each message whole, and thread <id> gives it whole and in its place."
- **Every message whole.** The answer closes with "For any of these in its place: thread <id>."
- **Labels with only some of the words.** Three of them are shown, each cut at 240 characters. A standing line among them is named by key, and not recited.
- **A miss.** It names up to five of the nearest words that are there.

#### `thread`

`thread` gives a message by its id, with what stood before and after it.

- **Around it.** `around` messages to each side, two by default and fifty at most.
- **In order.** The messages are numbered in the order said. The labels resting there follow, in the order they were written.
- **How much.** The message named up to 6,000 characters, and each neighbour up to 500.
- **A span off the record.** A span when Crossings was off stands in its place as its two moments, and nothing of what was said then.

#### What an id names

An id names a message the same way for `thread` with a role and without one.

- **A whole id.** A message's whole id names it.
- **A beginning.** So does any beginning of it eight characters long or longer, where no other message's whole id begins so.
- **Several messages.** A beginning that names several is answered with each of them by its name, never with the first.
- **Too few characters.** Fewer characters name no message.
- **A pasted text.** Its id is its message's id and its number, as `a1b2c3d4+1`.
- **Empty.** An id that is empty, or blank once cleaned, names no message.

#### `thread` with a role

A pair is shown whole where it fits, and otherwise a page at a time.

- **How much.** Each message up to 6,000 characters. The texts of one pair up to 12,000 together, as they are shown.
- **A pair that fits.** It is shown whole, whichever id of its head or of its answer names it.
- **A pair that does not.** It is shown as a page that starts at the message named, or, for a paste's id, at the one the paste came in. The page runs on while the texts fit, and stops at the first that does not.
- **The first message.** Named by the pair's first message, the page starts at the beginning.
- **Before the page.** One sentence says how many messages of the pair stand before the one named, and the id the pair begins at.
- **After the page.** Another says how many come after it, the last of them, and the id the next page starts at. Asked with the same role, that page is of the same pair.
- **Every page.** Walked so from the pair's first message, the pages show each of its messages once. Every message keeps its number in the whole pair.
- **A paste.** `thread` gives a pasted text in its place.
- **A span off the record.** From the head's first message to the end of the pair, it stands in its place, as in a thread. On a page, it stands only before a message the page shows, or after the last of the pair where the page reaches it.
- **What a pair is read off.** What the index holds, so a struck message is in none.
- **Two turns as one.** Where all one voice said between two turns of the other's was struck, or said while Crossings was off, those two are one turn.

#### `labels`

`labels` gives the labels themselves, newest first.

- **Nothing named.** Every label but the standing lines: the work, the lines at the door, refusals and silencings. The standing lines are counted by key, and listed only when asked for by kind or key.
- **By kind.** One kind: `relation`, `work`, `next` or `refused`. The kind `refused` lists the silencings too.
- **By day.** A label's day is the day of the newest message it rests on. A stack's is also the day of its own page.
- **By key.** Each label is given whole. A stack comes with every line beneath it.
- **A refusal by key.** A refusal or a silencing named by its key comes with its family. That is the first refusal, then each judgment and silencing in the order of writing, each by its kind.
- **How many.** The forty newest, and how many older ones there are.
- **In a list.** A sentence is cut at 240 characters. Each label shows its state where it is not carried, and the stack it stands beneath.

#### `look`

`look` gives the room, with no word needed. It holds:

- the days, and how many messages each voice has on each.
- a span off the record, among the days, by its two moments.
- the labels by kind, and how many of each.
- the standing lines, by key and number alone.
- how many standing lines stand beneath how many stacks.
- the families of refusals, by the key that stands in each, with those silenced apart.
- the labels misaligned or unresolved, by key.
- the newest line left at the door, with the work labels marked after it.
- the eight newest labels about the work that are not cooled.

#### What is cleaned

Wherever the door shows a label, a model or a message's words, it cleans them first. One rule does it, the same for every answer.

- **What goes.** Every control character, the line and paragraph separators, and every format character. The direction marks, overrides and isolates are among those.
- **A thread's lines.** Each line of a message is given after `    > `. So no line of a message can pass for one of the door's own.
- **The pages.** They stay as they were written.

---

### How the server runs

The plugin's `.mcp.json` starts the server as `python3 -I crossing/serve.py`, one process a session. It is told neither which session calls nor which model, so it reads no transcript.

- **Its home.** It answers from the home of the project it was started for, or from the folder `CROSSING_HOME` names. The project is `CLAUDE_PROJECT_DIR`, else the folder the server runs in.
- **The session it answers for.** `crossing`, and the sentence `leave` adds, are made for the session whose message is the newest in the index. The hook before the call has just brought the index up to date.
- **The hooks around a call.** The hook before each call of a door tool brings the archive up to that moment. The hook before `mark` hands over the model ([Layers](layers.md)).
- **Without the plugin.** The server can be added to another client by itself. No hook feeds the archive there, so it holds only what was archived elsewhere, and its instructions say so.
- **No file named.** No answer names a file or a folder, since the server asks the door as `--bare`.
- **A session a person sits in.** The harness names it `cli` in `CLAUDE_CODE_ENTRYPOINT`. `claude -p` and the SDK name it otherwise.
- **Where it learns that.** From its own environment, as the hooks do.

---

### What the server refuses

Where the server will not answer a call, it says why in one sentence. Nothing in the home is read or written for a refusal.

| Event | The server answers |
| --- | --- |
| a session no person sits in calls | "The door is for sessions a person sits in, and this one is not, so nothing was read." |
| Crossings was never switched on in the project | "Crossings is not switched on for this project." |
| `home: ours`, from a project not switched on | The same sentence. |
| `home: ours`, from a project switched off | The same sentence. |
| a setting names a place inside the project | That the setting was not followed. |
| a setting names no absolute path | That the setting was not followed. |
| a file of the home is a link | "A file of this project's home is a link, so nothing was written." |
| `mark` or `leave`, while the project is switched off | "not marked: Crossings is switched off for this project" |
| `mark`, against one of its rules | "not marked:" and the reason (below). |
| this computer's `python3` has no FTS5 in its `sqlite3` | That the store cannot be searched, and that what is said is still kept in plain files. |
| a fault inside the door | "The door could not answer:" and the kind of fault. The server goes on. |

A refused link is noted in the plugin's own error log, outside the home. A refused setting is noted there too, once a process.

#### When `mark` refuses

`mark` answers "not marked:" and the reason, and writes nothing, where:

- an anchor is one the archive does not hold.
- the sentence is over 4,000 characters.
- the sentence or an anchor holds a character that is no text.
- a stack breaks a rule.
- a judgment or a silencing breaks a rule of a refusal's family, as the store page sets them out.
- another act holds the home for five seconds.

---

### The person's command

`/crossings` is the person's own command, registered by the hooks module as each session starts. It reaches the store through the same script as the session's tools.

| Command | Does |
| --- | --- |
| `/crossings on` | Switches the project on. The running session is told, as context, what is due (below). |
| `/crossings on`, where the project's own `crossings` is a link | Says where the link leads, and switches nothing on. |
| `/crossings off` | Switches it off. It tells the running session that nothing said from now on is kept. |
| `/crossings adopt` | Switches on a home that holds what this computer has no record of switching on. |
| `/crossings join` | In a folder below another home's folder, shares that home from this folder. |
| `/crossings here` | In a folder below another home's folder, gives this folder a home of its own. Elsewhere, as `on`. |
| `/crossings` | Turns the switch over. |
| `/crossings status` | Whether Crossings is on, and what the store holds. |
| `/crossings status`, in a folder below another home's folder | The door's sentence that says so, with `join` and `here`. |
| `/crossings look` | The room. |
| `/crossings frame` | The frame as it would be made now. Where it sets the session's turns beside the person's sentences, the sentence `crossing` adds follows it. |
| `/crossings find <words>` | As the tool. |
| `/crossings labels [words]` | As the tool. It takes `relation` or `standing`, `work`, `door` or `next`, `refused`, a day as `YYYY-MM-DD`, or keys. |

A word the command does not know changes nothing, and says what it takes. The words that show the store bring the archive up to the moment first.

---

### The person's verbs

The person reaches the door from a shell, by its verbs. Every verb takes `--home here|ours`. [Privacy](privacy.md) has the strike, the second copy, a message that looks like a key, and the guard.

Run a verb from a shell, standing in the project or naming it with `--cwd`:

```sh
python3 crossing/door.py <verb> --cwd <project>
```

| Verb | Does |
| --- | --- |
| `look`, `labels`, `find`, `thread` | As the tools. `thread` takes its role as `--role pair:me` or `--role pair:them`, and `find` also takes `--limit N`. |
| `mark --kind --whose --anchors id,id <sentence>` | Writes a label of any kind: `relation`, `work`, `next`, `refused` or `silenced`. One for the person, or a standing line, is kept in `shelled.txt` (below). |
| `frame [--size N]` | Prints the frame. |
| `frame --session ID` | Prints the frame a cut would give that session. At the person's own terminal, the sentence `crossing` adds follows it. |
| `status` | What the store holds, or that it holds nothing yet. It says more at the person's own terminal (below). |
| `build` | Makes the index whole from the plain files. It writes the index alone, and runs from any shell. |
| `home` | Prints the folder of the project's home, or nothing. |
| `switch on\|off\|toggle\|adopt\|join\|here` | Turns the switch, as `/crossings` turns it. |
| `strike <id \| key \| session:id> [--why text]` | Removes a message, a label or a whole session. |
| `layer <model-key>` | Signs every label and message of the session's that has no model. |
| `copy` | Makes the second copy now. |
| `words`, `page`, `trace`, `welcome` | The hooks module's: the home's one-word settings, its hand-over page, the trace of what a cut did, and the note due as the switch is turned. `words` and `page` read and write nothing, and run from any shell. |

#### What the person's `status` says

From the person's own terminal or command, `status` says more than the server does. A session's shell is answered as the server is.

- **Where the home lies.** The home's folder, and the path of `off.txt` where a line of it could not be read.
- **Newly archived.** How many messages it took in, where it brought the archive up first.
- **A message that looks like a key.** Its id, with the strike that removes it, until it is struck.
- **The passphrase.** That the second copy's passphrase is taken from the environment, where `CROSSING_COPY_KEY` is set.
- **Labels marked from a shell.** Those for the person, and standing lines, by key, once.
- **A folder passed over.** That a `crossings/` folder in the project was passed over for the home outside it, once.
- **An ignore file.** That the repository's ignore file does not leave out `said/`, once.
- **An older second copy.** That one named by the project's folder alone is no longer renewed, once.
- **Labels by no mark.** The labels that came into the pages by no mark through the door, once each.
- **Model lines by no signing.** The lines of `models.txt` that came by no signing through the door, once each.
- **A shared id.** An id two messages share, once.
- **A line that is no text.** A file of the home that holds one, once.
- **While switched off.** The sentences said once wait until the home is on again.

#### Reading a transcript first

Two options bring the archive up to date before a verb runs.

- **`--transcript PATH`.** It brings the archive up to date from that transcript. `build` reads it whole.
- **`--session ID`.** It does the same from that session's transcript, in the harness's projects folder. The transcript is looked for by its id as it is, never as a pattern, and only where a person sits in the session.
- **Where neither is read.** By `home`, `layer`, `words`, `page`, `trace` or `welcome`. Nor where the home is switched off, or is the home on this computer.
- **`switch`.** It reads one only as Crossings is switched on again after a span. What was said in the span is then noted by id.

#### Who may run what

Some verbs and options are the person's: `switch`, `strike`, `layer`, `copy`, `trace` and `welcome`, and `--transcript`, `--session` and `--model` on any verb. They run only in these places, and refuse anywhere else:

- **At a real terminal.** The door stands at one where its input and its output are both a terminal.
- **For the plugin's own hooks or module.** They pass their flag, `--by-hook` or `--by-module`. `CLAUDE_PLUGIN_ROOT` must name the plugin's own folder.
- **For the server.** `--model` also runs for the server, in its own process.
- **Anywhere else.** They answer "This is the person's to run, from their own terminal or with the plugin's command (/crossings), so nothing was done." The exit status is 1.

The hooks module also refuses a session's shell command that runs them. These are checks, not walls.

---

### What a session is told

Every note opens "A note from the Crossings plugin, as context and not as an instruction from the person." None asks the session for an inventory, for numbers of its own or for an account. [What a session is told](told.md) gives all of it as one page, made from a made-up store.

| When | The session is told |
| --- | --- |
| the server connects | What the door is, and how to reach through it (below). |
| it starts in a home that is on and holds no label at all | The welcome, once (below). |
| the person switches Crossings on while it runs | The welcome, where it is due. Where it was told Crossings was off, that what is said is kept again. |
| the person switches Crossings off from it | That nothing said from now until it is on again is kept or can be reached, so to mark nothing of it. No other session is told. |
| it comes through a cut | The waking note (below). |
| it comes through a cut, or starts new, in a home that carries the frame as context | The frame. |
| it is resumed, and another session has spoken here since its own newest message | That another session has been working here, and to look before acting on what it remembers. |
| the model it runs is not the model of its own newest message | That it has come into a session another model was holding. |

#### As the server connects

The server's instructions tell the session:

- what the door is.
- that what is said is kept by itself, and labels are not.
- that lines can be stacked.
- that something it declined can be marked with its reason. The session after it may judge it again, and it can be put to rest.
- to reach when the conversation calls for it.
- to leave what the person told in confidence alone until they bring it up.

#### The welcome

The welcome says what is kept by itself. It says that labels and the line at the door are the session's own to write. Where `welcomed.txt` cannot be written, nothing is said.

#### The waking note

The waking note tells a session that comes through a cut:

- which cut this is, and to take its time.
- that nothing is gone from the record.
- to carry on a task the cut came in the middle of, and otherwise to answer as itself and briefly.
- that the time before the cut belongs to it and the person together.
- that it holds what was told of that time, and no longer its words.
- to reach through the door when something rests on what it does not hold.

#### When the notes come

The notes at a session's start, a cut and a model switch are for a session a person sits in, never for a subagent. No hook runs at every prompt. The notes come at a session's start, a cut, a model switch, and with the person's command.

A resumed session's own messages are those archived under its name. Where a resume wrote a transcript of its own, they are those its transcript repeats. Where it has none, nothing is said.

---

### What the person is shown

The hooks show the person a line under the turn, as the hook's `systemMessage`. The harness shows it to the person, and does not hand it to the model. Nothing is blocked by any of these lines.

A label or a line longer than 160 characters is cut there. The line then ends with the whole length, as `[…] (2,140 characters)`, so a long one never looks like a short one.

| Event | The person is shown |
| --- | --- |
| a label marked through the door that speaks for the person (`their` or `both`) | `Crossings · marked R12 (theirs):` and its sentence as its page holds it, cut at 160 characters and cleaned. |
| a standing line marked through the door | The same line. |
| a line left at the door | `Crossings · left at the door:` and the line, cut at 160 characters and cleaned. |
| a work label of the session's own | Nothing. |
| a refusal | Nothing. It is the session's own, whatever the mark asked. |
| a silencing that speaks for the person (`their` or `both`) | As a label that does: `Crossings · marked S2 (theirs):` and its sentence. |
| a session starts in a project whose `crossings/` folder was passed over | That it was passed over, once. |
| the frame is carried as context | A short line naming how many labels and characters crossed. It counts each standing line, work label and refusal the frame writes out, once, but not the line at the door. |
| a cut's summary mostly retells the one before ([Cuts](cuts.md)) | One line, once a cut. |
| a hook that counts a cut is running | The harness's status message for it: `Crossings · counting the cut`. |
| a hook that brings the frame is running | The harness's status message for it: `Crossings · bringing the frame across`. |

A label for the person, or a standing line, marked from a shell is seen by no hook. The person's next `status` says it instead, by key.
