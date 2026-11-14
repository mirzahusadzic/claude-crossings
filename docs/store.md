# The store

What Crossings keeps for a project, where it lies, and how it is read. Everything is a plain file of the project's home except `store.db`, an index made from those files that may be deleted at any time.

---

### A home and where it lies

A project's home is found by one rule, `located` in `crossing/record.py`, which the hooks, the door, its server, the hooks module and the person's command all go through:

1. The nearest `crossings/` folder upward from the project's folder, looked for no higher than the top of its repository. The top is the nearest folder upward that holds `.git`, looked for no higher than the person's own folder. A project in no repository has only its own folder looked in. A `crossings` that is a link, to a folder or to nothing, is found here all the same, and is no home: `switch on` and `adopt` refuse it in one sentence that names where it leads, nothing is believed, read or written through it, and no home is made outside the project in its place.
2. Otherwise a folder outside the project, `<homes>/<slug>-<digest>`. `<homes>` is the folder `CROSSING_HOMES` names, else `~/.claude/crossing/homes`. The slug is made from the path of the project's top, and the digest is eight characters of that path's SHA-256, so that `a-b`, `a_b` and `a.b` never come to one home. A home named `<homes>/<slug>` with no digest is still used where its `project` file names exactly this project's path.

Links in the project's path are followed first, so every piece comes to the same folder by whichever path it was told. The path is then taken as the disk spells it (`spelled`, in `crossing/record.py`, which asks macOS for the folder's own path): on a disk that does not tell the case of letters apart, one folder is one project with one home, by whichever spelling it was reached, and a line of the person's record written with another spelling of the same folders is matched by the files themselves. The person's own folder (`~` on these pages) is the one the system's record of their account gives (`pwd.getpwuid`), never the `HOME` variable, which a project's settings can set. On Windows it is the user profile's known folder (`SHGetKnownFolderPath`). Where neither answers, it is Python's `Path.home()`, with a line in the error log.

`CROSSING_HOME` names a home outright, for a harness with no project to find one by. Every setting that names a place, and what is refused, is in [Settings](settings.md).

Where a home lies says nothing of whether it is believed. A home is believed only where the person's record of switches names it for this project (see [Privacy](privacy.md)). A project whose home is not believed is one where Crossings was never switched on: the hooks keep nothing for it, every verb of the door but `switch` and `home` answers in one sentence with exit status 1, `home` prints nothing with exit status 1, and nothing is made.

Where the record names a home outside the project, and a `crossings/` folder the record does not name has since come into the project (a checkout brought one), the home outside is still used. The folder that arrived is neither read nor written, and the person is told so once by the hook at a session's start and once by `status`.

`door.py home` prints the folder of a project's home where it is believed, and nothing, with exit status 1, where it is not.

The home on this computer lies at the folder `CROSSING_OURS` names, else `~/.claude/crossing/ours`, and is asked for with `--home ours` from a shell or `home: ours` on a door tool. It belongs to no project and has no switch of its own. It is offered only from a project where Crossings is switched on and its switch is on; from any other, every verb answers as for a project never switched on. Nothing is archived into it, so a label marked there must rest on what that home itself holds.

No read makes a folder or a database. Only switching on makes a project's home, and only a mark into the home on this computer makes that one.

---

### The files of a home

Every file is reached through one check, `within` in `crossing/record.py`: no file or folder of a home is read or written through a link, and a home with a link anywhere below it is refused whole (see Privacy).

| File | Holds | Written by | By hand |
| --- | --- | --- | --- |
| `said/<session>.jsonl` | the archive: every message of either voice, one JSON line each | the hooks, at a door call, a cut and a session's end; `door.py --transcript` | no; a strike removes lines |
| `said/runs.key` | the home's key for the digests of a summary's runs | the first cut whose summary is 24 characters or more | no |
| `labels/<day>.md` | the label pages, one row a label | `mark`, `leave`, a strike; the hooks module refuses a session's tool or shell command that writes one | yes; the store follows at its next build |
| `hand-over.md` | a label page of the same form, read before `labels/` | nothing in the plugin but a strike | yes |
| `*.words.md` | the words a hand-over's labels rest on, one line a message, leaving out what the home keeps out | `crossing/handover.py`, from the person's own terminal, into a home the door believes | a strike mends it or takes it away |
| `models.txt` | which model wrote each label, by its key and its sentence's digest | a mark through the door, the hook after it, `door.py layer` | a later line stands over an earlier one |
| `there.txt` | the model each session runs, as its hooks were told it | the hooks | no |
| `calling.txt` | the model behind a call of `mark`, by the call's digest | the hook before the call; the server takes its line out, and keeps the newest 64 | no |
| `markers.jsonl` | how far each transcript was read | every archive | no; a line that is no marker reads that transcript from its start |
| `unattended.txt` | the ids of what sessions no person sat in held | the hooks of those sessions | no |
| `struck.txt` | what was struck, one token a line, with the reason after `#`; a session's strike adds the whole id of each message it took | `door.py strike`, and a mark that writes a misaligned stack again | no |
| `flagged.txt` | the ids of messages that look like they hold a key or a password | the archive | no |
| `off.txt` | when the switch was off: a line a span, its two moments in UTC | the switch alone | no |
| `unsaid.txt` | the ids of what was said while the switch was off | the archive, and switching on again | no |
| `welcomed.txt`, `told.txt` | the sessions welcomed, and those told the switch was turned | the hooks, the person's command | no |
| `shelled.txt` | labels marked from a shell for the person, until their `status` says them | `door.py mark` | no |
| `labelled.txt` | every label the home has met, by its key and its sentence's digest | a mark, and every build | no |
| `arrived.txt` | labels a build found in the pages that came by no mark through the door, until the person's `status` names them | builds | no |
| `collided.txt` | ids of eight characters that two messages of the archive share, until the person's `status` says them | the archive | no |
| `passed-over.txt`, `ignore-told.txt`, `copy-told.txt`, `damaged-told.txt` | that a sentence meant once was said | the hooks, `status` | no |
| `reached.jsonl` | what was pulled through the door: when, which verb, which ids | `thread`, `mark` and `leave` through the server, or with `--touch` from a shell | no |
| `archive.lock` | held by one archive, mark, strike, `layer` or switch at a time | each of those | no |
| `copy-stage.txt` | where a second copy stages its files, while it is made or after one was killed | the second copy | no |
| `<session>-cut-<n>.md`, `.json` | a cut's count: a page, and its sidecar of pointers and digests | the hook after a cut | no |
| `last-carry.json`, `last-cut.json` | the trace of the last frame carried by the hook, and of what the module did at the last cut | the hook, the module | no |
| `store.db` | the index | builds and additions | may be deleted at any time |
| `switch`, `mode`, `carry`, `project`, `copy`, `frame-size`, `retelling-length`, `retelling-share`, `.gitignore` | one-line settings, and the ignore file | see Settings | see there |

`<session>` is the first eight characters of the session's id, as the archive names it. An id that becomes part of a file's name, or a line of these small files (a session's id, a label page's day, a token to strike, a message's id in `unattended.txt`, `unsaid.txt` or `flagged.txt`), is letters, digits, `-` and `_` alone, 128 at most (`ident`, in `crossing/record.py`). Any other is refused: the hooks do nothing and say so in the error log, and the door says in one sentence that nothing was written. A row of a transcript whose id is not one is passed over by every reading, and so is never archived and never a line.

A file written whole (`markers.jsonl`, `off.txt`, `calling.txt`, every file a strike rewrites, an archive page `layer` signs, the person's record where the switch rewrites it) is written beside itself as `<name>.new` and put in its place, so it is never left half written. A plain file is read in lines broken at line feeds alone, so a message that holds U+2028 stays one line of the archive. A line that is not what such a line must be is passed over, and nothing stops for it; `status` says how many lines of the archive could not be read, where any could not. A line that cannot be read as text at all (a character cut short, a byte from another hand) is passed over the same way by every reader of a home's files, with a line in the error log, and archiving and the door go on; a page whose last line was cut short is ended before the archive appends to it; the person's next `status` names once each file that holds such a line. A line of `struck.txt` whose reason holds such a byte still strikes its token. A strike or `layer` writes back such a line as it was, unless it is struck.

---

### Messages

Each line of `said/<session>.jsonl` is one message:

| Field | Holds |
| --- | --- |
| `uuid` | the message's id, as the transcript gives it |
| `id` | its first eight characters, by which the door names it |
| `session` | the first eight characters of the transcript's name |
| `voice` | `his` for the person, `session` for the session |
| `at` | the time the transcript wrote beside it, where it has the shape of a moment (`2026-11-11T09:01:00.000Z`, its zone given or not); empty where it has not, as for a row that gives none. A time an older make kept as it came is still read, and shown cleaned |
| `text` | what was said, as it was sent |
| `model` | for the session's voice, the model its row names; left out where it names none, or one with a space, a line break or a `#` in it, which is no model's key |

From a transcript the archive takes the person's text at the prompt, a message the person sent while a turn ran, and the session's text blocks. It never takes a reasoning block, a tool call or a tool result, a compaction summary, the harness's own notes, a note the plugin itself carried across a cut, or a row the harness marks as a subagent's (`isSidechain`). Every rule about what a row is lives in `crossing/transcript.py`; a row these rules do not know is passed over, never guessed at.

A fork or a resume writes a new transcript that repeats earlier messages under the same ids. A message the archive holds already, from any session, is not written twice, and one an archive holds twice is read once. Two messages whose whole ids differ and whose first eight characters are the same are both kept; the archive notes that id in `collided.txt`, the person's next `status` says it once, `thread` on it names both whole ids, and a strike by it strikes neither and names both, so that each is struck by its whole id.

What the person pasted into a message stays in the archive's line as it was sent. The index keeps it apart: each pasted text becomes a row of its own beside the message, `<id>+1`, `<id>+2`, in the voice `pasted`, and the message keeps a note of its size in its place, `[pasted: N characters]`. A pasted text is not counted as the person's words, the frame does not quote it, and a label may rest on it by its id. It is struck with the message it came in.

---

### Labels

A label is one row of a page in `labels/`, named by the day it was marked:

```text
| W14 | The release waits for the second test run. | session | `a1b2c3d4`, `e5f6a7b8` |
```

| Cell | Holds |
| --- | --- |
| key | its kind by its letter and a number: `R` a standing line about the person and the session, `W` about the work, `N` a line left at the door. A mark takes the next number after every key of its letter the pages hold and every key struck, under the home's lock, so a row written by hand has its key already and two marks at once take two keys. A struck key is never given again |
| sentence | one sentence on one line, of 4,000 characters at most; a `|` in it is written `/` |
| whose | `his` (the person's), `session` or `both` |
| anchors | what it rests on, each in backticks: the ids of messages, a pasted text's `<id>+<n>`, or, for a stack, the keys of the lines beneath it |

A label whose anchor the archive does not hold is refused, and so is one with no sentence or no anchor, or a sentence longer than 4,000 characters.

A label that comes into the pages by no mark through the door (a pull, a branch switch, a hand) crosses cuts as any other. Every label the home has met is kept in `labelled.txt` by its key and its sentence's digest; a build that finds one it has not met, or one reworded since, notes it in `arrived.txt`, and the person's next `status` names it once. The first build of a home with no `labelled.txt` meets every label there is, and notes none. A line left at the door rests on messages alone, and one left through the door's `leave` is always the session's.

---

### Stacks

A label that rests on other labels of its kind is a stack, and they are the lines beneath it. Its row names each line by its key and six characters of the digest of the line's sentence as it stood when the stack was marked: `R13@1a2b3c`. Six, because a message's id has eight, so neither is read as the other. Nothing is lost by stacking: every line stays in its page, whole, and `labels <key>` gives a stack with every line beneath it.

| Event | Crossings |
| --- | --- |
| a stack names a label that is not there, or of another kind | refuses it in one sentence, and writes nothing |
| a line already stands beneath a stack that is not misaligned | refuses it: a line stands beneath one stack |
| a line is itself a stack over stacks | refuses it: stacks go two deep at most |
| a `leave` names a label | refuses it: a line at the door is neither a stack nor beneath one |
| a new stack stands over a line of a misaligned stack | the new stack takes the old one's place, and the old one is struck in the same act; the answer names it. A session's mark, through the server or a shell, is refused where the old stack's whose is `his`: only the person writes it again |
| a stack is struck | its lines are carried again as themselves |
| a line beneath a stack is struck or reworded | the stack is misaligned |

Where the model that marks is known, a stack is also kept within its layer ([Layers](layers.md)).

---

### The four states

Every build finds each label in one of four states, from the pages and the archive alone:

| State | The label |
| --- | --- |
| carried | stands by itself, or is the top of a stack |
| cooled | stands beneath a sound stack, which is carried in its place |
| misaligned | is a stack one of whose lines is gone, or was reworded since |
| unresolved | rests on a message the archive does not hold, or on nothing |

A label's own trouble is said before its place: one that is misaligned or unresolved is called so though it stands beneath a sound stack. What stands beneath a stack that is not sound is carried. `status` and `look` count the states.

---

### The index

`store.db` is SQLite, made from the plain files and from nothing else, with full-text search (`porter unicode61`, so a word is found by its stem). It is made whole by `door.py build`, a stack, a strike and `layer`. A `store.db` that is missing, of another make, or no database at all is read as none: a read makes the index in memory and writes nothing, and the next archive or build makes it on disk. Where the computer's `python3` has no FTS5 in its `sqlite3`, the index cannot be made: the archive in `said/` is still written, the switch adds one sentence that says so to its answer, and the person's `status` and the door's tools give that sentence in place of theirs.

An archive that keeps new messages adds them to the index in one transaction, and the result is the database a whole build would make from the same files. A plain label just marked, and a label's model just signed, are added the same way. For this the index keeps how each file it was made from stood: its size and when it last changed, and for a page of the archive how many lines it had and a digest of its last 4,096 bytes. The index is made whole instead wherever an addition cannot be trusted:

| Event | Crossings |
| --- | --- |
| no index, or one of another make | makes it whole |
| a label page, `models.txt`, `struck.txt`, `off.txt` or `flagged.txt` is there, gone or changed since | makes it whole |
| a page of the archive is gone, shorter, changed in place, older than its record, or grown where the bytes before its old end are not those read | makes it whole |
| a new message is one the index holds already, or would stand before its newest in the order of time | makes it whole |
| a new message is one a label rests on | makes it whole: the label's state would change |
| a mark makes a stack, or is not the last label of the last page | makes it whole |
| the addition fails | makes it whole |
| an archive finds a page changed by any other way than its own appends | marks the index as of no make, so what it appends next is not taken for growth |

A page made longer by hand more than 4,096 bytes before its old end may not be seen; `door.py build` makes the index whole. A whole build waits up to five seconds for an addition under way before it takes the old one's place.

---

### Markers and the lock

A transcript only grows, so each archive reads only what was added since the last one. `markers.jsonl` keeps a line a transcript, by its resolved path: the byte just after the last whole line read (`offset`), the SHA-256 of the 4,096 bytes before it (`check`), and the time of the last row read that had one (`at`). The next archive reads on from the offset where the file is at least that long and those bytes are the ones read; otherwise it reads the transcript from its start. A last line with no line feed yet is read the next time, once it is whole. The marker moves only after what it steps over is in the archive.

A session's end reads its transcript whole, so nothing a marker stepped over is lost. The hooks of a session no person sits in keep a marker of their own, under the transcript's path with `#unattended` after it.

One archive at a time is made in a home. It holds `archive.lock` from reading the record of when Crossings was off and what is held until the append and the marker's move are done, and the switch holds it while it writes a span and the `switch` file, so a switch waits for an archive under way, and nothing said after it turns is kept by that archive. A switch that cannot have it within five seconds says so in one sentence, and `status` says how it stands. One that cannot have it within five seconds does nothing that time, with a line in the error log, and the next reads on from the marker. A mark (from what it reads to decide whether it may stand, through the choice of its key, to its build), a strike and `layer` hold the same lock; one that cannot have it within five seconds writes nothing and says so in one sentence. The person's record of switches has a lock of its own, `switched.lock` beside it, held by each of its two writers, so that two switches at once lose no line; it is taken after the home's lock and never before it. Where there is no `flock` (Windows), the lock is a file made only where none is there, and one older than 120 seconds is taken for one a process left.
