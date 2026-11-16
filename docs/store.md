# The store

What Crossings keeps for a project, where it lies, and how it is read. Everything is a plain file of the project's home except `store.db`, an index made from those files that may be deleted at any time.

---

### A home and where it lies

Every piece of the plugin finds a project's home by one rule, `located` in `crossing/record.py`:

1. The nearest `crossings/` folder upward from the project's folder, no higher than the top of its repository: the nearest folder upward that holds `.git`, no higher than the person's own folder. A project in no repository looks in its own folder alone.
2. Otherwise a folder outside the project, `<homes>/<slug>-<digest>`. `<homes>` is the folder `CROSSING_HOMES` names, else `~/.claude/crossing/homes`. The slug comes from the path of the project's top, and the digest is eight characters of that path's SHA-256, so `a-b`, `a_b` and `a.b` never share a home. An older home named by the slug alone is still used where its `project` file names exactly this project.

A `crossings` that is a link, to a folder or to nothing, is found all the same, and is no home: nothing is believed, read or written through it, and no home is made outside the project in its place.

Links in the project's path are followed first, and the path is taken as the disk spells it (`spelled`), so one folder is one project by whichever path or spelling of its letters it was reached. The person's own folder (`~` on these pages) is the one the system's record of their account gives, never the `HOME` variable, which a project's settings can set. On Windows it is the user profile's known folder.

Where a home lies says nothing of whether it is believed: only the person's record of switches says that ([Privacy](privacy.md)). A project whose home is not believed was never switched on. The hooks keep nothing for it, every verb of the door but `switch` and `home` says so in one sentence, with exit status 1, and nothing is made. `door.py home` prints the folder of a believed home, and nothing otherwise.

Where the record names a home outside the project and a `crossings/` folder has since come into the project (a checkout brought one), the home outside is still used. The folder that arrived is neither read nor written, and the person is told so once at a session's start and once by `status`.

The home on this computer, at `CROSSING_OURS` or else `~/.claude/crossing/ours`, belongs to no project and has no switch of its own: `--home ours` from a shell, `home: ours` on a door tool. It is offered only from a project where Crossings is switched on and on. Nothing is archived into it, so a label marked there rests on what it holds itself. `CROSSING_HOME` names a home outright, for a harness with no project to find one by.

No read makes a folder or a database. Only switching on makes a project's home, and only a mark into the home on this computer makes that one.

---

### The files of a home

Every file is reached through one check, `within` in `crossing/record.py`: no file or folder of a home is read or written through a link, and a home with a link anywhere below it is refused whole.

The files a person reads, and some they may write:

| File | Holds | By hand |
| --- | --- | --- |
| `said/<session>.jsonl` | the archive: every message of either voice, one JSON line each | no; a strike removes lines |
| `labels/<day>.md` | the label pages, one row a label, written by `mark`, `leave` and a strike | yes; the store follows at its next build |
| `hand-over.md` | a label page of the same form, read before `labels/`, carried where no frame can be made | yes |
| `*.words.md` | the words a hand-over's labels rest on, written by `crossing/handover.py` | a strike mends it or takes it away |
| `<session>-cut-<n>.md`, `.json` | a cut's count: a page, and its sidecar of pointers and digests | no |
| `models.txt` | which model wrote each label, by its key and its sentence's digest | a later line stands over an earlier one; a line from another hand is followed, and named once by `status` |
| `struck.txt` | what was struck, a token a line, its reason after `#` | no |
| `off.txt` | when the switch was off: a span a line, in UTC | no |
| `store.db` | the index | may be deleted at any time |
| `switch`, `mode`, `carry`, `copy`, `frame-size`, `retelling-length`, `retelling-share`, `project`, `.gitignore` | one-line settings, and the ignore file | see [Settings](settings.md) |

The plugin's own bookkeeping, which the hooks and the door write alone:

| File | Holds |
| --- | --- |
| `markers.jsonl` | how far each transcript was read |
| `unsaid.txt`, `off-places.jsonl` | the ids of what was said while the switch was off, and where each transcript stood as it was switched off ([Privacy](privacy.md)) |
| `unattended.txt` | the ids of what sessions no person sat in held |
| `flagged.txt` | the ids of messages that look like they hold a key or a password |
| `collided.txt` | ids of eight characters that two messages share, until the person's `status` says them |
| `labelled.txt`, `arrived.txt` | the labels the home has met, and those a build found that came by no mark through the door; no proof alone (see Labels) |
| `models-met.txt`, `models-arrived.txt` | the same for the lines of `models.txt` |
| `shelled.txt` | labels marked from a shell for the person, until their `status` says them |
| `there.txt`, `calling.txt` | the model each session runs, and the model behind a call of `mark` ([Layers](layers.md)) |
| `welcomed.txt`, `told.txt` | the sessions welcomed, and those told the switch was turned |
| `passed-over.txt`, `ignore-told.txt`, `copy-told.txt`, `damaged-told.txt` | that a sentence meant once was said |
| `reached.jsonl` | what was pulled through the door: when, which verb, which ids |
| `said/runs.key` | the home's key for the digests of a summary's runs, made at the first cut that needs it |
| `archive.lock` | held by one act at a time (see below) |
| `copy.lock` | held by one second copy at a time, from its first file read to its image's place |
| `copy-stage.txt` | where a second copy stages its files, while it is made or after one was killed, with the token a file beside the stage holds |
| `last-carry.json`, `last-cut.json` | a trace of the last frame carried, and of what the module did at the last cut |

`<session>` is the first eight characters of the session's id. An id that becomes part of a file's name, or a line of these small files, is letters, digits, `-` and `_` alone, 128 at most (`ident`, in `crossing/record.py`). Any other is refused, and says so; a row of a transcript whose id is not one is passed over by every reading.

A file written whole (`markers.jsonl`, `off.txt`, `calling.txt`, every file a strike or `layer` rewrites, the person's record) is written beside itself as `<name>.new` and put in its place, so it is never left half written. A plain file is read in lines broken at line feeds alone, so a message that holds U+2028 stays one line of the archive.

A line that is not what such a line must be is passed over, and nothing stops for it; so is a line that cannot be read as text at all, with a line in the error log, and the person's next `status` names that file once. The exception is the record of when Crossings was off: a damaged line there means what it held can no longer be told, and nothing is archived until the person switches on again ([Privacy](privacy.md)). `status` counts the lines of the archive that could not be read.

A line added to a file whose last line has no line feed (a page cut short, a file an editor or a sync left so) becomes a line of its own (`add`, in `crossing/record.py`). A strike or `layer` writes a damaged line back as it was, unless it is struck.

---

### Messages

Each line of `said/<session>.jsonl` is one message:

| Field | Holds |
| --- | --- |
| `uuid` | the message's id, as the transcript gives it |
| `id` | its first eight characters, by which the door names it |
| `session` | the first eight characters of the transcript's name |
| `voice` | `his` for the person, `session` for the session |
| `at` | the time the transcript wrote beside it, where it has the shape of a moment (`2026-11-11T09:01:00.000Z`); empty otherwise |
| `text` | what was said, as it was sent |
| `model` | for the session's voice, the model its row names; left out where it names none, or a name with a space, a line break or a `#` in it |

From a transcript the archive takes the person's text, typed at the prompt or sent while a turn ran, and the session's text blocks; nothing else ([Privacy](privacy.md) has what it never takes). Every rule about what a row is lives in `crossing/transcript.py`. A row of a shape those rules do not know is passed over, never guessed at, and the rows around it are read as ever. A cut's boundary whose figures are of the wrong kind is still the cut, and its page is written without them.

A fork or a resume repeats earlier messages under the same ids: a message the archive holds already is not written twice, and one it holds twice is read once. Two messages whose whole ids differ but whose first eight characters are the same are both kept. The id is noted in `collided.txt` and said once by `status`, `thread` on it names both whole ids, and a strike by it strikes neither.

What the person pasted stays in the archive's line as it was sent. The index keeps each pasted text as a row of its own, `<id>+1`, `<id>+2`, in the voice `pasted`, and the message keeps a note of its size in its place, `[pasted: N characters]`. A paste is not counted as the person's words and the frame does not quote it; a label may rest on it by its id, and it is struck with the message it came in.

---

### Labels

A label is one row of a page in `labels/`, named by the day it was marked:

```text
| W14 | The release waits for the second test run. | session | `a1b2c3d4`, `e5f6a7b8` |
```

| Cell | Holds |
| --- | --- |
| key | its kind by its letter, and a number: `R` a standing line about the person and the session, `W` about the work, `N` a line left at the door. A mark takes the next number after every key of its letter in the pages and among the struck, under the home's lock; a struck key is never given again |
| sentence | meant as one sentence, on one line; a `|` in it is written `/`. A mark bounds its length alone, at 4,000 characters, and does not count its sentences; a row written by hand is read as it stands |
| whose | `his` (the person's), `session` or `both` |
| anchors | what it rests on, each in backticks: message ids, a pasted text's `<id>+<n>`, or, for a stack, the keys of the lines beneath it |

A mark is refused where it has no sentence or no anchor, where its sentence is longer than 4,000 characters (how many sentences it holds is not looked at), where an anchor is one the archive does not hold, where an anchor is an id two messages share (that refusal names both whole ids), or where its sentence or an anchor holds a character that is no text (a lone surrogate), which no page can hold; a model's name of that kind is taken as no model known. A line left at the door rests on messages alone, and one left through `leave` is always the session's.

A label can also come into the pages by no mark through the door (a pull, a branch switch, a hand), and it crosses cuts as any other. What the door wrote is known from receipts kept outside every project, beside the person's record (`switched.receipts`): every label the home has met, by its key and its sentence's digest, and every line of `models.txt`. `labelled.txt` and `models-met.txt` inside the home are written too, and are no proof alone, since a pull can bring a line of either with the label it names.

A build that finds a label the receipts do not know, or one reworded since, notes it in `arrived.txt`, and the person's next `status` names it once. A `status` lets go only of what it said, under the home's lock, so a label noted while it spoke is named by the next; so too for `models-arrived.txt`, `collided.txt` and `shelled.txt`. A home with no receipts yet has them made at its next build, silently, from `labelled.txt` or from every label there is. Switching on a home that is not believed yet takes away any receipt kept for its folder before.

A home adopted with `/crossings adopt` has met none of its labels: each is named once by `status`, a standing line and one that speaks for the person said as such. Where the receipts cannot be written, the error log says so once a process, and what was not kept is named as arrived later.

---

### Stacks

A label that rests on other labels of its kind is a stack, and they are the lines beneath it. Its row names each line by its key and six characters of the digest of the line's sentence as it stood when the stack was marked: `R13@1a2b3c`. Six, because a message's id has eight, so neither is read as the other. Nothing is lost by stacking: every line stays in its page, whole, and `labels <key>` gives a stack with every line beneath it.

| Event | Crossings |
| --- | --- |
| a stack names a label that is not there, or of another kind | refuses it in one sentence, and writes nothing |
| a line already stands beneath a stack that is not misaligned | refuses it: a line stands beneath one stack |
| a line is itself a stack over stacks | refuses it: stacks go two deep at most |
| a `leave` names a label | refuses it: a line at the door is neither a stack nor beneath one |
| a new stack stands over a line of a misaligned stack | the new stack takes its place, and the old one is struck in the same act, and named. A session's mark is refused where the old stack is the person's (`his`) |
| a stack is struck | its lines are carried again as themselves |
| a line beneath a stack is struck or reworded | the stack is misaligned |

A mark over other labels decides from the pages as they stand: where the index no longer stands for them (a row written by hand since it was made), it is made whole first, so that no stack is struck for a state the pages no longer hold.

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

A label's own trouble is said before its place: one misaligned or unresolved is called so though it stands beneath a sound stack. What stands beneath a stack that is not sound is carried. `status` and `look` count the states.

---

### The index

`store.db` is SQLite, made from the plain files and from nothing else, with full-text search (`porter unicode61`, so a word is found by its stem).

Each build marks the index it makes, in the index and outside every project, beside the person's record (`switched.indexes`). An index whose mark is not the one kept there (one a pull or a copy brought, or an older make's) is not believed, and is made again before it is read. Where the mark cannot be kept, the process that made the index believes its own, and the error log says so once a process. Switching on and `adopt` make the index anew wherever the folder holds one.

A `store.db` that is missing, of another make, or no database at all is read as none: a read makes the index in memory and writes nothing, and the next archive or build makes it on disk. In a home switched off, no read puts an index in place or keeps a mark. Where `python3` has no FTS5 in its `sqlite3`, no index can be made: the archive in `said/` is still written, and the switch, `status` and the door's tools say so in one sentence.

An archive adds what it keeps to the index in one transaction, and so does a plain mark and a signing; the result is the database a whole build would make from the same files. For this the index keeps how each file stood: its size and when it last changed, and for a page of the archive its count of lines and a digest of its last 4,096 bytes. Wherever an addition cannot be trusted, the index is made whole:

| Event | Crossings |
| --- | --- |
| no index, or one of another make | makes it whole |
| a label page, `models.txt`, `struck.txt`, `off.txt` or `flagged.txt` is there, gone or changed since | makes it whole |
| a page of the archive is gone, shorter, changed in place, older than its record, or grown where the bytes before its old end are not those read | makes it whole |
| a new message is one the index holds already, or would stand before its newest in time | makes it whole |
| a new message is one a label rests on, whose state would change | makes it whole |
| a mark makes a stack, or is not the last label of the last page | makes it whole |
| the addition fails | makes it whole |
| an archive finds a page changed by other means than its own appends | marks the index as of no make, so what it appends next is not taken for growth |

A page made longer by hand more than 4,096 bytes before its old end may not be seen; `door.py build` makes the index whole, and so do a stack, a strike and `layer`. A whole build waits up to five seconds for an addition under way before it takes the old one's place.

---

### Markers and the lock

A transcript only grows, so each archive reads only what was added since the last. `markers.jsonl` keeps a line a transcript, by its resolved path: the byte just after the last whole line read (`offset`), the SHA-256 of the 4,096 bytes before it (`check`), and the time of the last row read that had one (`at`). The next archive reads on from the offset where the file is that long and those bytes are the ones read, and from the start otherwise.

A last line with no line feed yet is read once it is whole, and the marker moves only after what it steps over is in the archive. A session's end reads its transcript whole, so nothing a marker stepped over is lost. The hooks of a session no person sits in keep a marker of their own, under the transcript's path with `#unattended` after it.

One act at a time writes a home, holding `archive.lock`: an archive, from reading the record of when Crossings was off to the marker's move; a reading of a session no person sits in, from its read of the markers to its own marker's move; a mark, from what it reads to decide whether it may stand, through the choice of its key, to its build; a signing of the model behind a mark; a strike; `layer`; the switch; every build of the index; and a second copy, while it reads and stages the plain files and again as it puts its image in place, but not while the image is made. So a switch waits for an archive under way, two marks take two keys, and two reads that each find a stale index make it one at a time.

An act that cannot have the lock within five seconds writes nothing, and says so in one sentence where someone asked for it; an archive reads on from its marker the next time, and a read whose build cannot have it makes the index in memory for itself.

The person's record of switches has a lock of its own, `switched.lock` beside it, taken after the home's and never before it. Where there is no `flock` (Windows), a lock is a file made only where none is there, and one older than 120 seconds is taken for one a process left.
