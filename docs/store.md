# The store

What Crossings keeps for a project, where it lies, and how it is read. Everything is a plain file of the project's home except `store.db`, an index made from those files that may be deleted at any time.

[The words](words.md) says in a line or two what each of the tool's own words means.

---

### A home and where it lies

A home is the folder that holds what Crossings keeps for a project. Every piece of the plugin finds a project's home by one rule, in this order:

1. **A `crossings/` folder.** The nearest `crossings/` folder upward from the project's folder, no higher than the top of its repository. A project in no repository looks in its own folder alone.
2. **A folder outside the project.** Otherwise the home is `<homes>/<slug>-<digest>`.

The parts of that rule:

- **The top of a repository.** The nearest folder upward that holds `.git`, no higher than the person's own folder.
- **`<homes>`.** The folder `CROSSING_HOMES` names, else `~/.claude/crossing/homes`.
- **The slug and the digest.** The slug comes from the path of the project's top. The digest is eight characters of that path's SHA-256, so `a-b`, `a_b` and `a.b` never share a home.
- **An older home.** One named by the slug alone is still used where its `project` file names exactly this project.
- **A `crossings` that is a link.** One that leads to a folder, or to nothing, is found all the same, and is no home. Nothing is believed, read or written through it, and no home is made outside the project in its place.
- **One folder, one project.** Links in the project's path are followed first, and the path is taken as the disk spells it. So one folder is one project, by whichever path or spelling of its letters it was reached.
- **The person's own folder, `~` on these pages.** It is the one the system's record of their account gives, never the `HOME` variable, which a project's settings can set. On Windows it is the user profile's known folder. Where neither can be had, it is the folder Python's own rule gives, and the error log says so once a process.
- **A home named outright.** `CROSSING_HOME` names one, for a harness with no project to find one by. It is never below another home's folder (below).

#### A home that is not believed

Where a home lies says nothing of whether it is believed. Only the person's record of switches says that ([Privacy](privacy.md)). A project whose home is not believed was never switched on:

- **The hooks.** They keep nothing for it.
- **The door.** Every verb but `switch` and `home` says so in one sentence, with exit status 1, and nothing is made.
- **`door.py home`.** It prints the folder of a believed home, or of the one a folder below it waits on (below). Otherwise it prints nothing.

#### A folder below a home's folder

A folder below the folder its home belongs to does not take that home by finding it on the way up. A session started there keeps nothing and reads nothing of that home, and neither does the door asked from there. That holds until the person answers once for that folder.

The folder a home belongs to is the one that holds its `crossings/` folder. For a home outside the project, it is the project's top.

The person answers with one of two words:

- **`/crossings join`.** It shares the home from that folder. The person's record keeps it as a line that names the folder and the home, and no project.
- **`/crossings here`.** It gives the folder a home of its own. That home lies outside the project, as the home of a project with no `crossings/` folder does, and is named by the folder's path.

Until the person answers:

- **A session starting there.** It is told in one sentence that it holds nothing of that home.
- **The person.** They are shown the two words.
- **The door.** Every verb but `home`, and `switch` with one of the two words, says so in one sentence, with exit status 1.
- **`door.py home`.** It still names that home, so that the guard on the archive's files knows it.

Switching on from such a folder, where no home was believed yet, makes the project's home and shares it from there.

#### A `crossings/` folder that comes later

The record may name a home outside the project, and a `crossings/` folder may come into the project since, as a checkout brings one. The home outside is still used. The folder that arrived is neither read nor written, and the person is told so once at a session's start and once by `status`.

#### The home on this computer

The home on this computer belongs to no project, and has no switch of its own. It lies at `CROSSING_OURS`, or else at `~/.claude/crossing/ours`.

- **Reaching it.** `--home ours` from a shell, and `home: ours` on a door tool.
- **Where it is offered.** Only from a project where Crossings is switched on, and on.
- **What it holds.** Nothing is archived into it, so a label marked there rests on what it holds itself.

#### What makes a home

No read makes a folder or a database. Only switching on makes a project's home. A mark into the home on this computer is refused while its folder is not there, and makes none.

---

### The files of a home

A home holds the files the person reads, and the plugin's own bookkeeping. Every file is reached through one check, so no file or folder of a home is read or written through a link. A home with a link anywhere below it is refused whole.

#### The files the person reads

The person reads these, and may write some of them by hand.

| File | Holds | By hand |
| --- | --- | --- |
| `said/<session>.jsonl` | The archive: every message of either voice, one JSON line each. | No. A strike removes lines. |
| `labels/<day>.md` | The label pages, one row a label, written by `mark`, `leave` and a strike. | Yes. The store follows at its next build. |
| `hand-over.md` | A label page of the same form, read before `labels/`. It is carried where no frame can be made. | Yes. |
| `*.words.md` | The words a hand-over's labels rest on, written by `crossing/handover.py`. | A strike mends it or takes it away. |
| `<session>-cut-<n>.md`, `.json` | A cut's count: a page, and its sidecar of pointers and digests. | No. |
| `models.txt` | Which model wrote each label, by its key and its sentence's digest. | A later line stands over an earlier one. A line from another hand is followed, and named once by `status`. |
| `struck.txt` | What was struck, a token a line, its reason after `#`. A message is struck by its whole id. | No. |
| `off.txt` | When the switch was off: a span a line, in UTC. | No. |
| `store.db` | The index. | It may be deleted at any time. |
| `switch`, `mode`, `carry`, `copy`, `frame-size`, `retelling-length`, `retelling-share`, `project`, `.gitignore` | One-line settings, and the ignore file. | See [Settings](settings.md). |

#### The plugin's own bookkeeping

The hooks and the door write these alone.

| File | Holds |
| --- | --- |
| `markers.jsonl` | How far each transcript was read (see Markers and the lock). |
| `unsaid.txt`, `off-places.jsonl` | The ids of what was said while the switch was off, and where each transcript stood as it was switched off (see Privacy). |
| `unattended.txt` | The ids of what sessions no person sat in held. |
| `flagged.txt` | The ids of the person's messages that look like they hold a key or a password. |
| `collided.txt` | Ids of eight characters that two messages share, until the person's `status` says them. |
| `labelled.txt`, `arrived.txt` | The labels the home has met, and those a build found that came by no mark through the door. Neither is proof alone (see Labels). |
| `models-met.txt`, `models-arrived.txt` | The same for the lines of `models.txt`. |
| `shelled.txt` | Labels for the person, and standing lines, marked from a shell, until the person's `status` says them. |
| `there.txt`, `calling.txt` | The model each session runs, and the model behind a call of `mark` ([Layers](layers.md)). |
| `welcomed.txt`, `told.txt` | The sessions welcomed, and those told the switch was turned. |
| `passed-over.txt`, `ignore-told.txt`, `copy-told.txt`, `damaged-told.txt` | That a sentence meant once was said. |
| `reached.jsonl` | What was pulled through the door: when, which verb, which ids. It is read again where [the record weighs](frame.md#what-the-record-weighs) what no label rests on. |
| `said/runs.key` | The home's key for the digests of a summary's runs, made at the first cut that needs it. |
| `archive.lock` | Held by one act at a time (see Markers and the lock). |
| `copy.lock` | Held by one second copy at a time, from its first file read to its image's place. |
| `copy-stage.txt` | Where a second copy stages its files, while it is made or after one was killed. It holds the stage's path, and the token a file beside the stage holds. |
| `last-carry.json`, `last-cut.json` | A trace of the last frame carried, and of what the module did at the last cut. |

#### Names, and how a file is written

Every file of a home follows a few rules for its name and its lines.

- **`<session>`.** The first eight characters of the session's id.
- **An id in a name or a line.** An id that becomes part of a file's name, or a line of these small files, is letters, digits, `-` and `_` alone. It is 128 characters at most. Any other is refused, and says so.
- **A transcript's row with any other id.** It is passed over by every reading.
- **Written whole.** `markers.jsonl`, `off.txt`, `calling.txt`, every file a strike or `layer` rewrites, and the person's record. Each is written beside itself as `<name>.new` and put in its place, so it is never left half written.
- **Read in lines.** A plain file is read in lines broken at line feeds alone. So a message that holds U+2028 stays one line of the archive.
- **A line added.** Where a file's last line has no line feed, a line added to it becomes a line of its own. Such a file is a page cut short, or one an editor or a sync left so.

#### A damaged line

A line that is not what such a line must be is passed over, and nothing stops for it.

- **A line that is no text.** It is passed over too, with a line in the error log. The person's next `status` names that file once.
- **In the archive.** `status` counts the lines of the archive that could not be read.
- **Written back.** A strike or `layer` writes a damaged line back as it was, unless it is struck.
- **The record of when Crossings was off.** It is the exception. A damaged line there means what it held can no longer be told. Nothing is archived until the person switches on again (see Privacy).

---

### Messages

Each line of `said/<session>.jsonl` is one message. The archive takes from a transcript the person's text, typed at the prompt or sent while a turn ran, and the session's text blocks. It takes nothing else (see Privacy for what it never takes).

| Field | Holds |
| --- | --- |
| `uuid` | The message's id, as the transcript gives it. |
| `id` | Its first eight characters. The door names it by them where no other message's begin the same. |
| `session` | The first eight characters of the transcript's name. |
| `voice` | `his` for the person, `session` for the session (below). |
| `at` | The time the transcript wrote beside it, where it has the shape of a moment, as `2026-11-11T09:01:00.000Z`. Empty otherwise. |
| `text` | What was said, as it was sent. |
| `model` | For the session's voice, the model its row names (below). |

- **The person's voice.** It is written `his`, as every make has written it, so that each make reads every archive. `his` is never shown, and the door shows such a message as the person's. `find` takes the person's voice as `their`, or as `his` still.
- **A model left out.** `model` is left out where the row names none. It is left out too for a name with a space, a line break or a `#` in it, or one that begins with `<`. The harness's `<synthetic>` is such a name.
- **A row of another shape.** A row of a shape the archive's rules do not know is passed over, never guessed at. The rows around it are read as ever.
- **A cut's boundary.** One whose figures are of the wrong kind is still the cut, and its page is written without them.

#### A message kept twice, and an id two share

A fork or a resume repeats earlier messages under the same ids. A message the archive holds already is not written twice, and one it holds twice is read once. Two messages whose whole ids differ, but whose first eight characters are the same, are both kept:

- **Noted.** The id goes into `collided.txt`, and `status` says it once.
- **`thread`.** On that id, it names each of them.
- **A strike.** One by that id strikes neither.
- **Their names.** Each is named by the shortest beginning of its whole id that no other message's whole id begins with. That name is never fewer than eight characters, as `a1b2c3d4-1`. It stands wherever the door prints a message's id: `find`, `thread`, a pair, its pointers.
- **A whole id.** It always names its own message, also where it begins another's.
- **Every other message.** It is named by its eight characters, as before.

#### What the person pasted

What the person pasted stays in the archive's line as it was sent. In the index it is a row of its own.

- **One paste whole.** The harness wraps a paste in a pair of tags that carry one id. A paste runs on to the closing tag of its own id. So a pasted text that holds the tags itself, as a session's log or a program's source may, is one paste whole.
- **Its row.** Each pasted text is kept as `<id>+1`, `<id>+2`, in the voice `pasted`. The message keeps a note of its size in its place, `[pasted: N characters]`.
- **Not the person's words.** A paste is not counted as the person's words, and the frame does not quote it.
- **A label on it.** A label may rest on a paste by its id.
- **Struck.** A paste is struck with the message it came in.

---

### Labels

A label is one row of a page in `labels/`, named by the day it was marked. Its four cells hold its key, its sentence, whose it is, and what it rests on.

A row reads like this:

```text
| W14 | The release waits for the second test run. | session | `a1b2c3d4`, `e5f6a7b8` |
```

- **The key.** Its kind by its letter, and a number. A mark takes the next number after every key of its letter, in the pages and among the struck, under the home's lock. A struck key is never given again.
- **The sentence.** Meant as one sentence, on one line, and a `|` in it is written `/`. A mark bounds its length alone, at 4,000 characters, and does not count its sentences. A row written by hand is read as it stands.
- **A long sentence.** A mark's answer says how long a long one is ([the door](door.md#what-mark-and-leave-write)). Nothing is refused or cut for it.
- **Whose.** `his` (the person's), `session` or `both`, and a refusal is always written as the session's. The person's is written `his` whether a mark gives it as `their` or as `his`, as every make has written it. It is printed `theirs`.
- **The anchors.** What it rests on, each in backticks: message ids, or a pasted text's `<id>+<n>`. For a stack, the keys of the lines beneath it. For a judgment of a refusal or a silencing, the key of the first refusal of its family.

The key's letter says the label's kind:

| Letter | The label |
| --- | --- |
| `R` | A standing line about the person and the session. |
| `W` | About the work. |
| `N` | A line left at the door. |
| `X` | Something the session declined. |
| `S` | A silencing, which puts a refusal to rest (see Refusals). |

#### When a mark is refused

A mark is refused where:

- it has no sentence, or no anchor.
- its sentence is longer than 4,000 characters (how many sentences it holds is not looked at).
- an anchor is one the archive does not hold.
- an anchor is an id two messages share. That refusal names both whole ids.
- its sentence or an anchor holds a character that is no text (a lone surrogate), which no page can hold.

A model's name that holds such a character is taken as no model known. A line left through `leave` is always the session's.

#### A label on an id two messages share

An anchor names every message whose id is its eight characters. A mark takes one only where the archive holds one message so named. A second that comes later is a twin of the one the label was marked on.

The label rests on the one the record can prove it meant:

- **Said after the mark.** A twin said after the label was marked is not it.
- **The mark's moment.** It is the one `reached.jsonl` keeps for the label's key, to the second, where it is there. Otherwise it is the end of the day its page is named by. That is 36 hours after the day began in UTC, since the day is the marking computer's own.
- **One twin left.** The label rests on it alone. `thread` shows the label on that one and not on the other. `labels` gives the anchor with its name, as `a1b2c3d4 (a1b2c3d4-0)`.
- **The record cannot tell.** The label rests on neither, and is carried by its sentence. No frame quotes either twin for it. `labels` gives the anchor with each one's name, as `a1b2c3d4 (a1b2c3d4-0 or a1b2c3d4-1)`.
- **A twin struck.** One struck by its whole id has no time left in the record, and may be the one. `labels` then gives `one struck` among the names. So a strike of one twin never moves a label to the other.
- **Only the struck twin.** Where it is the only one the label can rest on, the label is unresolved.

An example, with made-up moments, of a label W5 marked on `a1b2c3d4`:

- **The mark.** W5 is marked at 10:00 UTC on 11 November, and `reached.jsonl` keeps that moment.
- **A twin said later.** Another message under that id, said at 11:00, is said after the mark. W5 rests on the first alone.
- **A twin said earlier.** One said at 09:00, and archived only later, leaves the record unable to tell. W5 rests on neither.
- **No moment kept.** The mark's moment is then the end of its page's day: for `2026-11-11.md`, 12:00 UTC on 12 November. The twin said at 11:00 then leaves the record unable to tell too.

#### Labels that came by no mark

A label can also come into the pages by no mark through the door (a pull, a branch switch, a hand). It crosses cuts as any other. What the door wrote is known from receipts kept outside every project, beside the person's record (`switched.receipts`).

- **The receipts.** Every label the home has met, by its key and its sentence's digest, and every line of `models.txt`.
- **The files inside the home.** `labelled.txt` and `models-met.txt` are written too. They are no proof alone, since a pull can bring a line of either with the label it names.
- **A label that arrived.** A build that finds one the receipts do not know, or one reworded since, notes it in `arrived.txt`. The person's next `status` names it once.
- **What `status` lets go.** Only what it said, under the home's lock, so a label noted while it spoke is named by the next. So too for `models-arrived.txt`, `collided.txt` and `shelled.txt`.
- **A home with no receipts yet.** Its next build makes them, silently, from `labelled.txt` or from every label there is.
- **Switching on.** Switching on a home that is not believed yet takes away any receipt kept for its folder before.
- **A home adopted.** One adopted with `/crossings adopt` has met none of its labels. `status` names each once, and says a standing line, or one that speaks for the person, as such.
- **Receipts that cannot be written.** The error log says so once a process. What was not kept is named as arrived later.

---

### Stacks

A label that rests on other labels of its kind is a stack, and they are the lines beneath it. Nothing is lost by stacking. Every line stays in its page, whole, and `labels <key>` gives a stack with every line beneath it.

A stack's row names each line by its key and six characters of a digest, as `R13@1a2b3c`. The digest is of the line's sentence as it stood when the stack was marked. Six, because a message's id has eight, so neither is read as the other.

| Event | Crossings |
| --- | --- |
| a stack names a label that is not there, or of another kind | Refuses it in one sentence, and writes nothing. |
| a line already stands beneath a stack that is not misaligned | Refuses it. A line stands beneath one stack. |
| a line is itself a stack over stacks | Refuses it. Stacks go two deep at most. |
| a line left at the door names a label | Refuses it. A line at the door rests on messages alone, and is neither a stack nor beneath one. |
| a new stack stands over a line of a misaligned stack | Takes the old stack's place. The old one is struck in the same act, and named. |
| a session's mark would take the place of a misaligned stack of the person's | Refuses it. |
| a stack is struck | Carries its lines again, as themselves. |
| a line beneath a stack is struck or reworded | Finds the stack misaligned. |

A mark over other labels decides from the pages as they stand. Where the index no longer stands for them, as after a row written by hand since it was made, it is made whole first. So no stack is struck for a state the pages no longer hold.

Where the model that marks is known, a stack is also kept within its layer (see Layers).

---

### Refusals

What a session declined is part of where the work stands: what was asked, and why it was not done. A session marks it as a label of the kind `refused`, which rests on the message that asked, its sentence the session's reason. Without it, a session that wakes after a cut finds the ask in the record and no account of the answer.

#### Judging a refusal again, and putting it to rest

A later session may judge a refusal again, or put it to rest. Each move is a label of its own.

- **A judgment.** Another label of the kind `refused`. It rests on the refusal's key, and on the message where its own reason was said.
- **A silencing.** A label of the kind `silenced`, which puts a refusal to rest. It rests on the key of one refusal and on the message where the reason was said, and its sentence says why.
- **Whose.** A refusal is the session's own, and is written as `session` whatever a mark asks. A silencing keeps whose it is given, since the person may be the one who put the refusal to rest.

#### A family

A refusal, every judgment of it and every silencing of it are one family. The family is named by the key of its first refusal, whichever of them a later mark names. It keeps that name whether or not that first label is still there.

- **Its rows.** A row of the family names the first refusal as a stack names a line, as `X3@1a2b3c`.
- **No stack.** A family is no stack. None of a stack's rules is asked of it, and it never gets deeper.
- **The one that stands.** The newest sound label of a family, in the order of writing, is the one that stands. A sound label is neither misaligned nor unresolved ([the four states](#the-four-states)). The others are cooled beneath it.
- **Silenced.** Where the one that stands is a silencing, the family is silenced. It crosses no more, and stays in the pages with its whole run.
- **Standing again.** A later label of the kind `refused` on the same family makes it stand again.

What Crossings does with a judgment, a silencing and a family:

| Event | Crossings |
| --- | --- |
| a judgment or a silencing names no message | Refuses it. Each rests on the message where its reason was said. |
| a silencing names no refusal | Refuses it. It rests on the key of the refusal it puts to rest. |
| a judgment or a silencing names a label of another kind | Refuses it. |
| either names refusals of two families | Refuses it. A judgment judges one alone, and a silencing puts one alone to rest. |
| the first refusal of a family is struck | Keeps the family one all the same, named by that key as its rows name it. Its newest sound label still stands. |
| a row of a family, written by hand, names what no family is | Finds it misaligned, and carries it as itself. |

#### How a family is shown

The door gives a family whole, and counts the families by where they stand.

- **`labels`.** On any key of a family, it gives the whole run. That is the first refusal, then each judgment and silencing in the order of writing, each by its kind.
- **`look` and `status`.** They count the families that stand apart from those that are silenced.
- **For the model that asks.** `labels` gives each label's state for the model that asks. A session's own silencing written under another model puts the family to rest for that model alone. The person's puts it to rest for every model (see Layers).
- **In a frame.** What a frame carries of them is in [The frame](frame.md#refusals-in-a-frame).

Label pages written before these kinds were known read as they did. An index made then is of another make, and is made again from the plain files before it is read.

---

### The four states

Every build finds each label in one of four states, from the pages and the archive alone. `status` and `look` count the states.

| State | The label |
| --- | --- |
| carried | Stands by itself, or is the top of a stack. |
| cooled | Stands beneath a sound stack, which is carried in its place. |
| misaligned | Is a stack one of whose lines is gone, or was reworded since. |
| unresolved | Rests on a message the archive does not hold, or on nothing. Resting on the struck one of two messages that share an id is resting on nothing (see Labels). |

- **Its own trouble first.** A label's own trouble is said before its place. One misaligned or unresolved is called so, though it stands beneath a sound stack.
- **Beneath a stack that is not sound.** What stands there is carried.
- **A refusal's family.** It is read by the same four. The label that stands in it is carried, and the others are cooled beneath that one. A row of the family that names what no family is is misaligned (see Refusals).

---

### The index

`store.db` is SQLite, made from the plain files and from nothing else. It has full-text search, so a word is found by its stem.

#### Which index is believed

Each build marks the index it makes. The mark is kept in the index, and outside every project, beside the person's record (`switched.indexes`).

- **A mark that is not the one kept.** Such an index is not believed, and is made again before it is read. One a pull or a copy brought is such an index, and so is an older make's.
- **A mark that cannot be kept.** The process that made the index believes its own, and the error log says so once a process.
- **Switching on, and `adopt`.** They make the index anew wherever the folder holds one. Where no index can be made, they take away the one there.

#### An index read as none

A `store.db` that is missing, of another make, or no database at all is read as none. A read then makes the index in memory and writes nothing, and the next archive or build makes it on disk.

- **A home switched off.** No read there puts an index in place or keeps a mark.
- **No FTS5.** Where `python3` has no FTS5 in its `sqlite3`, no index can be made. The archive in `said/` is still written, and the switch, `status` and the door's tools say so in one sentence.

#### Adding to the index

An archive adds what it keeps to the index in one transaction, and so do a plain mark and a signing. The result is the database a whole build would make from the same files.

For this the index keeps each file's size, and when it last changed. For a page of the archive it also keeps its count of lines, and a digest of its last 4,096 bytes. The index is made whole wherever an addition cannot be trusted:

- there is no index, or one of another make.
- a label page, `models.txt`, `struck.txt`, `off.txt` or `flagged.txt` is new, gone or changed since.
- a page of the archive is gone, shorter, changed in place, or older than its record.
- a page of the archive grew, and the bytes before its old end are not those read.
- a new message is one the index holds already.
- a new message would stand before the index's newest in time.
- a new message is one a label rests on, whose state would change.
- a mark makes a stack, or is not the last label of the last page.
- the addition fails.

An archive that finds a page changed by other means than its own appends marks the index as of no make. So what it appends next is not taken for growth.

A page made longer by hand more than 4,096 bytes before its old end may not be seen. `door.py build` makes the index whole, and so do a stack, a strike and `layer`. A whole build waits up to five seconds for an addition under way before it takes the old one's place.

---

### Markers and the lock

A transcript only grows, so each archive reads only what was added since the last. A marker keeps how far each transcript was read. A lock keeps each act that writes a home apart from the others.

#### Markers

`markers.jsonl` keeps a line a transcript, by its resolved path:

| Field | Holds |
| --- | --- |
| `offset` | The byte just after the last whole line read. |
| `check` | The SHA-256 of the 4,096 bytes before it. |
| `at` | The time of the last row read that had one. |

- **Reading on.** The next archive reads on from the offset, where the file is that long and those bytes are the ones read. Otherwise it reads from the start.
- **A last line not yet whole.** A last line with no line feed yet is read once it is whole.
- **The marker's move.** The marker moves only after what it steps over is in the archive.
- **A session's end.** It reads its transcript whole, so nothing a marker stepped over is lost.
- **A session no person sits in.** Its hooks keep a marker of their own, under the transcript's path with `#unattended` after it.

#### The home's lock

One act at a time writes a home, holding `archive.lock`. So a switch waits for an archive under way, and two marks take two keys. Two reads that each find a stale index make it one at a time.

These acts hold it:

- an archive, from reading the record of when Crossings was off to the marker's move.
- a reading of a session no person sits in, from its read of the markers to its own marker's move.
- a mark, from what it reads to decide whether it may stand, through the choice of its key, to its build.
- a signing of the model behind a mark.
- a strike, `layer` and the switch.
- every build of the index.
- a second copy, while it reads and stages the plain files, and again as it puts its image in place. It does not hold it while the image is made.

An act that cannot have the lock within five seconds writes nothing, and says so in one sentence where someone asked for it. An archive then reads on from its marker the next time. A read whose build cannot have the lock makes the index in memory for itself.

#### The person's record's lock

The person's record of switches has a lock of its own, `switched.lock` beside it. It is taken after the home's lock, and never before it.

Where there is no `flock`, as on Windows, a lock is a file made only where none is there. One older than 120 seconds is taken for one a process left.
