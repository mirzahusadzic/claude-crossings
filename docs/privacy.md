# Privacy

What Crossings keeps, what it never reads, who can read what it keeps, what the person can take back, and what it cannot keep out. Nothing in the plugin calls a model or opens a network connection: what it keeps stays in plain files on this computer, and in a second copy only where the person names a folder for one.

---

### What is kept and what is never read

| From a transcript | Kept |
| --- | --- |
| what the person typed, or sent while a turn ran | yes, word for word, with its id and time |
| what the person pasted into a message | yes, in the message's line; the index keeps it apart from the person's words ([The store](store.md)) |
| the session's text to the person | yes, word for word, with the model its row names |
| a reasoning block | parsed with its row, as every row is, and never used or kept |
| a row the harness marks as a subagent's (`isSidechain`) | never kept or counted: its prompt is the session's, not the person's |
| a tool call or a tool result | never kept; the count of a cut measures its length in characters, and nothing else of it |
| a text in the person's turn that begins with `<`, `Caveat:`, `[SYSTEM NOTIFICATION`, `Another Claude session`, `A note from the Crossings plugin` or `A note from the Crossing plugin` (the older words of the same note), or holds `system-reminder` in its first 60 characters: the harness's notes and reminders, and a note the plugin carried | never kept |
| the harness's summary at a cut | never kept: its length, and its runs of 24 characters as keyed digests |

Nothing is archived from a session no person sits in (one the harness does not name `cli` in `CLAUDE_CODE_ENTRYPOINT`, such as `claude -p` or the SDK): its prompts are a tool's. Its hooks keep the ids of what its transcript holds, and no word of it, in `unattended.txt`, with a marker of their own under the transcript's path and `#unattended`, so that a fork or a resume that repeats those messages does not bring them in later. Its cut is still counted: the cut's page and sidecar are written (ids, lengths and keyed digests, no words), with the home's key for the digests where the summary has runs to keep and there is no key yet. A hook whose input names a subagent (`agent_id`) at a cut writes nothing at all, and wakes no one. A transcript the person hands to `door.py` by its path, from their own terminal, is taken as it is. The door's `frame` and `page`, which give what crosses a cut, carry nothing where no person sits in the session and the door stands at no terminal: they answer in one sentence, with exit status 1, and the hooks module hands the door the session's `CLAUDE_CODE_ENTRYPOINT` for this.

The plugin's data folder (`CLAUDE_PLUGIN_DATA`, else `~/.claude/crossing`) holds no home. It holds `errors.log`, a line for each failure and each refusal, and `calls.log`, two lines a hook call in any project, one as it starts and one as it ends: the hook, the moment, the size of the transcript and when it last changed as the file system gives them, the summary's length, and the figures the harness itself gives about its cache. `calls.log` opens no transcript and holds no text, and is not written where `CROSSING_DEBUG` is `0`. Every session the plugin is loaded in is marked by an empty file in `~/.claude/crossing/live/` from its start to its end, in any project.

Within a home, `reached.jsonl` keeps one line for each pull through the door's `thread`, `mark` and `leave`: when, which verb, which ids, and no words.

---

### The switch

The person's switch is kept where no repository can hold it: `~/.claude/crossing/switched`, or the file `CROSSING_SWITCHED` names. It has one line for each project switched on, with the resolved path of the project's top and of its home, spelled as the disk spells them, and, for a home that has been switched off, how many lines its `off.txt` had when the switch last wrote it and the steady clock's reading as it was switched off. Switching on writes the project's line, and nothing else does. Its two writers hold one lock (`switched.lock` beside it), so two switches at once lose no line.

| Event | Crossings |
| --- | --- |
| a project with no line in the record | is one where Crossings was never switched on, though a `crossings/` folder or a home made earlier is there; nothing is kept for it |
| `/crossings on` where the home is there and holds any file but a `.gitignore`, with no line for it | says how many messages and labels it holds, and what else is there (an index, a hand-over page, a setting file, `models.txt`, how many other files), and where; switches nothing on |
| `/crossings adopt` | takes that home as the person's own and switches it on |
| `/crossings on` or `adopt` where the home holds an index | makes the index anew from the plain files: no database that came with the folder is read |
| a project's own `crossings` that is a link, to a folder or to nothing | is no home: `/crossings on` and `adopt` refuse it in one sentence that names where it leads, nothing is believed, read or written through it, and no home is made outside the project in its place |
| a home named outright (`CROSSING_HOME`) that is a link | believed only where the line names the place it leads to |
| a setting names a place inside the project, or no absolute path | is not followed: the project is one where Crossings was never switched on ([Settings](settings.md)) |
| switched off | the line stays; the home is read through the door, and nothing is added to it |

---

### Off the record

`/crossings off` is a way to speak off the record. From the moment it is switched off until the moment it is switched on again, nothing either voice says, in any session of the project, is kept, and none of it can be reached through the door afterwards: not when it is switched on again, not at a session's end, not from a fork or a resume that repeats it, and not from a transcript handed to `door.py` by its path.

| Event | Crossings |
| --- | --- |
| the switch is turned off | keeps the moment in the home's `off.txt`, in UTC, before the `switch` file is turned; a span opens. It keeps in `off-places.jsonl` where each transcript the archive knows (by its markers) stands |
| it is turned on again | closes the span after the `switch` file is turned; the session it is turned from has what it said meanwhile noted by id in `unsaid.txt`, and so does every message the transcripts in `off-places.jsonl` gained since they stood there, whatever time it bears; that file goes |
| the clock reads earlier as it is turned on than as it was turned off (it was set back meanwhile) | closes the span as far past its opening as the steady clock has run since it was switched off, or, where that cannot be told (the computer was started again), as far past its opening as the clock went back; and keeps a second span, closed at this moment, that begins as far before it as the steady clock ran, or, where that cannot be told, at 1970, so that what was said after the clock went back is off too. What was said in the moments before it was switched off, or in the first moments after it is on, and is not archived yet, may be kept off as well, and `status` counts the two spans as two times off |
| a reading meets a message inside a span, by the time the transcript wrote beside it | passes over it, and what was pasted in it, and keeps its id alone in `unsaid.txt` |
| a message has no time, or one that cannot be read | keeps it only where the rows on either side of it in that file are outside every span and no span begins or ends between them; at the first or last row of a file it is not kept, and a session's end decides the last again once a row has come after it |
| `off.txt` is there and cannot be read | archives nothing, and moves no marker, until it can be |
| `off.txt` is missing, or shorter than the record says (a session, a checkout or a clean took it) | archives nothing for that home, and `status` and `look` say why; the next `/crossings on` keeps everything before that moment off the record, by a span from 1970 to now, and archives again from there |
| a line of `off.txt` is no span (a sync, an editor or a hand damaged it) | passes over it, and `status` says how many; what it held can no longer be told, so the home archives nothing, as where the file is missing, until the next `/crossings on` keeps everything before that moment off the record. A line that is no span before that moment is kept off by it, and is still counted |
| a cut comes while it is off | is not counted, noted or answered |
| a cut comes while `off.txt` is missing, shorter than the record says, or holds a line that is no span since the last `/crossings on` that kept everything before off | is counted with nothing said listed: its page says the record cannot be told |
| `mark` or `leave` while it is off | refuse |

The store shows that something may have been said, and nothing of what: `status` says how many times Crossings was off (how many spans `off.txt` holds), `look` puts a line with the two moments among its days, `thread` puts one in the place of what was said, and `find` finds nothing of it. `unsaid.txt` keeps one id for each message a reading met inside a span, so how many they were can be counted from it; no count of them or of their characters is kept, a cut's count included, and the frame does not mention it.

What it does not do:

- It does not reach back. A span is kept from the moment the switch is turned, so what was archived before, or said in a time off that no span was kept for (a switch written by hand, or a time off with no span in `off.txt`), stays until it is struck.
- It does not touch the harness's own transcript, which still holds everything said, for as long as the harness keeps it.
- It judges a message by the time the harness wrote beside it in the transcript being read, by this computer's clock, and by its place in a transcript the archive knew as the switch was turned off (above). A clock set back while it is off is met by the two spans switching on keeps; only a transcript the archive had not met when the switch was turned off (a session begun while it was off, or one never read before) is judged by its rows' times alone, so a clock set forward and back again while it was off is not met there. A clock set back after it is on again is not met either.
- It does not tell a session other than the one it was switched off from. Nothing that session says is kept, and its `mark` and `leave` refuse all the same.

---

### Striking

`door.py strike <id>` removes a message, a label or a whole session from the archive, the label pages and the home's small files named below, and it does not come back at a rebuild. The pages of the cuts and their sidecars keep the ids. It is the person's, from their own terminal; the door's server does not offer it, and `/crossings` has no word for it. The one other way anything is struck is a mark that writes a misaligned stack again, which strikes that stack in the same act ([The store](store.md)): it never strikes a message, and a session's mark, through the server or a shell, is refused where the stack's whose is `his`. A session's mark can so strike a misaligned stack whose whose is `session` or `both`, and, where its model is known, only one of its own model's or of no known model.

| Token | Strikes |
| --- | --- |
| a message's id, or its whole id | the message, and every text pasted in it; an id of eight characters that two messages share strikes neither, and the answer names both whole ids |
| `session:<id>` | every message of that session, and each of them by its whole id, so that a fork or a resume in a transcript of any name brings none back; a whole id the harness gives is cut to the eight characters the archive names a session by |
| a label's key, in any case | the label; a stack struck gives its lines back |
| a pasted text's id (`<id>+1`) | nothing: a pasted text is struck with the message it came in |

A message leaves the archive, the log of what was pulled, `flagged.txt`, `unattended.txt`, and every hand-over words page of the home (`*.words.md`). A words page as `crossing/handover.py` writes it, one line a message, is mended line by line; a page that is not (words that run over a line, or a page edited by hand), or that still names the id once mended, goes whole, and the answer says so. A whole session's strike takes every words page of the home away whole, since a page may give a message of that session the archive does not hold yet, and the answer names them; the next hand-over makes a page again from the record. A label leaves its page and `models.txt`. A whole session leaves, besides, the lines that name it in `welcomed.txt`, `told.txt` and `there.txt`, and the markers of its transcripts. The token stays in `struck.txt`, so that a transcript which still holds the message cannot bring it back, and a struck key is never given again; a whole session's strike also keeps there the whole id of each message it took, so that neither the archive, the index, a words page nor `door.py page` gives one again from a transcript of another name. The index is made whole after it. A strike holds the home's lock from its first write to its build, and every file it rewrites is written beside itself and put in its place; one that cannot have the lock within five seconds strikes nothing and says so.

A strike that strikes nothing (nothing named, nothing in the home that matches, an id two messages share, a pasted text's id, a home held by another act, or a home not made yet) says why in one sentence, writes nothing, and exits with status 1. A strike that struck something names, by key, every label that rests on a message it took, and leaves them as they are for the person to strike too; its answer ends by naming what no strike can reach: the harness's own transcript, an earlier second copy or a backup, and the history of a repository that holds the home. The pages of the cuts keep the ids and sizes of messages, and keyed digests of their summaries' runs, never their words, and are left as they are.

---

### Who can read the files

Every folder the plugin makes, for a home, for the home on this computer, for the record and for its own data and live folders, is its owner's alone (0700), and every file it writes there is too (0600). Each entry (`hook.py`, `door.py`, `serve.py`, `handover.py`, the second copy) sets the process's umask first, and the hooks module reaches a home only through `door.py`. A home readable by other accounts (0755, and 0644 for its files) is narrowed file by file the next time `/crossings on` or `status` is run for that project. On Windows these modes mean nothing, and none is set.

No file or folder of a home is read or written through a link: one check (`within`, in `crossing/record.py`) is used by every piece. A home with a link anywhere below it is refused whole: the hooks do nothing and say so in the error log, and the door says in one sentence that a file of the home is a link and nothing was written. A project's own `crossings` that is a link is no home at all (see The switch); a home named outright may be a link, and whether it is believed is the switch's to say.

Where the home lies inside a repository and has no `.gitignore`, switching on and `adopt` write one: everything in the home is ignored but the label pages, the pages of the cuts and the ignore file itself. An ignore file that is there is left as it is, and `status` says once where it does not leave out `said/`, where the words are kept.

---

### The second copy

If the home's `copy` file names a folder, the plain files go there as one encrypted disk image (AES-256, by macOS's `hdiutil`) at each cut of a session a person sits in, at the end of one where `CROSSING_WAIT` is `1`, and at `door.py copy`. The plain files are the archive's pages, the label pages, `struck.txt`, `models.txt` and `off.txt`; the index never goes. The image is `<folder>-<digest>.dmg`, named by the project's folder and eight characters of the SHA-256 of its whole path, as a default home's folder is, so two projects of one name never share an image. It is replaced whole each time, and read back and compared file by file before it replaces the last. An image named by the project's folder alone (`<folder>.dmg`) is never renamed, written or taken away, and the person's `status` names it once as no longer renewed.

| Event | The second copy |
| --- | --- |
| the files are staged | in a folder made for the owner alone in the folder `TMPDIR` names (else `TEMP` or `TMP`, else the system's default), never in the home, and taken away file by file once the image is made; a project whose settings set `TMPDIR` is trusted with where that is |
| a run is killed before its end | the home kept the stage's path in `copy-stage.txt`, and the next run takes that stage away, file by file, following no link |
| that folder lies inside the home, the copy's folder or the project | no copy is made |
| the `copy` file names a place inside the project | no copy is made: the door says so in a sentence, and a cut's hook in a line of the error log |
| the image does not read back the same | it replaces nothing |
| the Keychain will not keep the passphrase, or `hdiutil` cannot make the image | no copy is made: the door says so in one sentence, with exit status 1, and a cut's hook in a line of the error log; neither names the command it ran, whose Keychain call holds the passphrase |
| the passphrase | a random one, made the first time and kept in the Keychain under `crossing-archive` |
| `CROSSING_COPY_KEY` is set and the door stands at a real terminal | it is the passphrase instead, and `status` from a shell says that every program the session starts can read it |
| `CROSSING_COPY_KEY` is set anywhere else | it is passed over, with one line in the error log |

An earlier image, or a backup of the folder, keeps what was struck since.

---

### A message that looks like a secret

A message of the person's that looks like it holds a key or a password is kept: the plugin keeps what was said, and is no filter. Its id, and nothing of it, goes into the home's `flagged.txt`. The patterns are few, so that talk about passwords is not taken for one:

- a PEM private key's first line
- an AWS access key id: `AKIA` and sixteen capitals or digits
- a GitHub token: `ghp_`, `gho_`, `ghs_`, `github_pat_`
- an `sk-` key of twenty key characters or more
- a token after `Authorization: Bearer`
- an assignment such as `password=`, `passwd:` or `api_key=` with a value of eight characters or more

Until the message is struck, `status` and `look` from a shell or the person's command say, a sentence a message, that a kept message looks like it holds a key or a password, its id, and that `door.py strike <id>` removes it. The door's server and the frame never say it, and the frame never quotes such a message among the person's own words. `find` and `thread` still give it: the session heard it when it was said.

---

### What labels are for

A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them. The welcome and the door's own descriptions of `mark` and of `leave` say so, a line left at the door being held to the same. A label crosses every cut as standing, and the session that reads it acts on it.

Text a session reads, a page or a tool's output, can steer it to mark such a label. So a label marked through the door that speaks for the person (`his` or `both`) or about the two of them (a standing line) is shown to the person in one line under the turn, as its page holds it, and so is every line left at the door ([The door](door.md)). A work label of the session's own is not shown, and nothing is blocked. A label that comes into the pages by no mark through the door (a pull, a branch switch, a hand) is named once by the person's next `status` instead, after the build that finds it ([The store](store.md)).

---

### The archive's own files

A session reaches what was said through the door. The hooks module refuses a call of the session's whose input names a file of the archive (a home's `said/` folder, or its `store.db`), in one sentence that names the door's tools. It looks at a file tool's paths (Read, Edit, Write, Grep and the like), at a Glob pattern and a Grep `glob`, and at a shell command's text. The homes it knows are those outside a project (the folder `CROSSING_HOMES` names, else `~/.claude/crossing/homes`), the home on this computer, a home named outright, and a project's own `crossings/`, wherever it stands. The label pages, the pages of the cuts and the other plain files stay readable, and a shell call of `door.py` runs.

A `..` after a folder is taken as the step back it is before any of this is decided, so `crossings/labels/../said/` is `crossings/said/`.

By the same checks it refuses, as the person's to run, a shell command that runs `door.py`, or the module `crossing.door`, with one of the person's verbs or options, a verb that writes a kept file for the module (`trace`, `welcome`), `--model`, or the plugin's flags: a word of theirs anywhere after `door.py` or `crossing.door` in that command, so `find "the switch"` is refused too. It also refuses a shell command, or a call of a tool that writes a file, that names the person's record of switches or a home's `off.txt`, `unsaid.txt`, `models.txt`, `welcomed.txt`, `told.txt`, `there.txt`, `unattended.txt`, `shelled.txt`, `labelled.txt`, `arrived.txt`, `collided.txt`, `markers.jsonl`, `off-places.jsonl`, `reached.jsonl`, `passed-over.txt`, `ignore-told.txt`, `copy-told.txt`, `damaged-told.txt`, `copy-stage.txt`, `archive.lock`, `last-carry.json`, `last-cut.json`, `models-met.txt` or `models-arrived.txt`. The files the door alone writes, the label pages (`labels/`), `hand-over.md` and every words page (`*.words.md`), `struck.txt`, `calling.txt`, `flagged.txt`, the pages of the cuts and their sidecars (`<session>-cut-<n>.md`, `.json`), the one-line settings `copy`, `switch`, `mode`, `carry`, `frame-size`, `retelling-length`, `retelling-share` and `project`, and the home's `.gitignore`, are refused to a tool that writes a file (Write, Edit, MultiEdit, NotebookEdit) wherever a home stands, and to a shell command that names one in any part that is not a plain read (`cat`, `grep`, `head`, `ls` and the like, with no `>`). A shell command that runs `crossing/handover.py`, which writes a words page into a home, is refused as the person's to run. Reading them stays open: labels are written through the door alone.

It runs in the module's own process at every tool call, so it decides by string checks on the call's input alone, and starts no process and opens no file. A shell command's quotes and backslashes are taken out before its paths are looked at, as the shell takes them out, so `crossings/'said'` and `crossings/sa\id` are `crossings/said`. It is a check, not a wall: a path it cannot see in the call's text (a `cd` into a home and a relative name after it, a search over a whole home) is not caught.

---

### What it cannot keep out

A project whose settings the person has let the harness trust can run programs as the person, by its hooks or its own settings. Such a program can read any store on this computer, the record of switches included, and nothing here can tell it from the person.

A session with a shell that the person lets run commands can do whatever the person can. It can stand the door at a made-up terminal (`script`), set the plugin's folder and flag itself, or open a file by a path no check reads. A project whose settings set `PATH` decides which `python3`, `security` and `hdiutil` run, and one that sets `TMPDIR` decides where the second copy stages its plain files; both are trusted.

The hooks module's string checks still do not see a path that a variable spells (`crossings/sa${X}id`), one a command builds or reaches after a `cd`, or a command on the whole home folder (`rm -r crossings`, a search of all of it). The guards against both are checks: the terminal, the flags, the string checks of the hooks module, the record's counts. They catch what is plain and are no walls. The wall is the person's own approval of what a project may set and what a session may run.
