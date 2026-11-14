# Privacy

What Crossings keeps, what it never reads, who can read what it keeps, what the person can take back, and what it cannot keep out. Nothing in the plugin calls a model or opens a network connection: what it keeps stays in plain files on this computer, and in a second copy only where the person names a folder for one.

---

### What is kept, and what is never read

| From a transcript | Kept |
| --- | --- |
| what the person typed, or sent while a turn ran | yes, word for word, with its id and time |
| what the person pasted into a message | yes, in the message's line; the index keeps it apart from the person's own words ([The store](store.md)) |
| the session's text to the person | yes, word for word, with the model its row names |
| a reasoning block, a tool call, a tool result | never; a cut's count measures tool traffic by its length alone |
| the harness's notes and reminders, and a note the plugin itself carried | never |
| a prompt another plugin submitted between turns | never |
| a subagent's rows (`isSidechain`), and rows the harness wrote in the session's place (model `<synthetic>`) | never: they are nobody's words to the person |
| the harness's summary at a cut | never: only its length, and digests of its runs keyed with the home's own key |

A text in the person's turn is the harness's only where it is made wholly of blocks under a name the harness is known to write (`transcript.HARNESS_NAMES`), or opens with one of a few fixed openings. Any other text is the person's and is kept: `<3`, a `<div>`, a sentence about a system reminder. A plugin's prompt is known by the harness's own wording at its start and at its end; one the harness wraps otherwise is kept as the person's.

Nothing is archived from a session no person sits in: one the harness does not name `cli` (`claude -p`, the SDK), whose prompts are a tool's. Its hooks keep the ids of its messages in `unattended.txt`, and no word of them, so that a fork or a resume cannot bring them in later. Its cuts are still counted, with no words, and no frame or hand-over is given to it.

A subagent's cut writes nothing at all. A transcript the person hands to `door.py` by its path, from their own terminal, is taken as it is.

Outside every home, the plugin's data folder (`CLAUDE_PLUGIN_DATA`, else `~/.claude/crossing`) holds two logs, each its owner's alone: `errors.log`, a line a failure or a refusal; and `calls.log`, two lines a hook call with sizes and times and never a word (`CROSSING_DEBUG=0` turns it off). `~/.claude/crossing/live/` holds an empty file for each session the plugin is loaded in. Inside a home, `reached.jsonl` notes each pull through `thread`, `mark` and `leave`: when, which verb, which ids, and no words.

---

### The switch

Crossings keeps nothing for a project until the person switches it on there. The switch lives in the person's own record, `~/.claude/crossing/switched` (or the file `CROSSING_SWITCHED` names), outside every project, so no repository can switch it on. A line of it names a project's top and its home, spelled as the disk spells them; switching on writes it, and nothing else does.

Beside the record, under its one lock, lie the mark of each home's index (`switched.indexes`) and the receipts of what the door wrote into each home (`switched.receipts`). The record also keeps, for a home switched off before, what its record of when it was off held (see below).

| Event | Crossings |
| --- | --- |
| a project with no line in the record | was never switched on: nothing is kept, though a `crossings/` folder or an old home is there |
| `/crossings on`, where the home already holds files this computer has no record of | names what it holds and where, and switches nothing on |
| `/crossings adopt` | takes that home as the person's own, and switches it on |
| switching on or adopting a home that holds an index | makes the index anew: no database that came with the folder is read |
| a project's own `crossings` that is a link | is no home: refused in one sentence that names where it leads, and nothing is made in its place |
| a home named outright (`CROSSING_HOME`) that is a link | is believed only where the record names where it leads |
| a setting that names a place inside the project, or no absolute path | is not followed ([Settings](settings.md)) |
| switched off | the line stays; the home is still read, and nothing is added to it |

---

### Off the record

`/crossings off` is a way to speak off the record. From the moment it is switched off until it is switched on again, nothing either voice says, in any session of the project, is kept. None of it can be reached later: not when it is on again, not at a session's end, not from a fork or a resume, and not from a transcript handed to `door.py`.

The switch keeps each span in the home's `off.txt`, in UTC. A message whose time falls inside a span is passed over, and its id alone goes into `unsaid.txt`, so that no later reading keeps it. As it is switched off, the home also notes where each transcript it knows stands (`off-places.jsonl`). Switching on keeps off, by id, whatever those transcripts gained meanwhile, whatever time a row bears.

| Event | Crossings |
| --- | --- |
| a message with no time | is kept only where the rows on either side of it are outside every span, with no span between them |
| the clock was set back while it was off | switching on closes the span by the steady clock, and keeps a second span up to that moment, so what was said after the clock went back is off too |
| `off.txt` is there and cannot be read | nothing is archived until it can be |
| the record of when it was off is missing, cut short, damaged, or changed for another | nothing is archived, counted at a cut or given on a words page, and `status` and `look` say why; the next `/crossings on` keeps everything before that moment off the record, and archiving goes on from there |
| a cut comes while it is off | is not counted, noted or answered |
| `mark`, `leave` or `layer` while it is off | refuse, and nothing is written |

The person's record keeps how many spans, ids and places the three files held each time the switch wrote them, with a digest of each, so a file cut short, damaged or changed for another is told. That is the one count kept of what was said off the record: no other count of it, or of its characters, is kept anywhere, and the frame never mentions it.

The store shows that something may have been said, and never what. `status` counts the times it was off, `look` and `thread` show a span by its two moments, and `find` finds nothing of it.

What it does not do:

- It does not reach back. What was kept before it was switched off stays until it is struck.
- It does not touch the harness's own transcript, which still holds everything said, for as long as the harness keeps it.
- It judges a transcript the archive had not met when it was switched off by its rows' times alone, so a clock set forward and back there is not met. Nor is a clock set back after it is on again.
- It tells only the session it was switched off from. Every session's `mark` and `leave` refuse all the same.

---

### Striking

`door.py strike <id>` removes a message, a label or a whole session for good: from the archive, the label pages, the index, the hand-over's words pages and the home's small files. It is the person's, from their own terminal; the door's server does not offer it, and `/crossings` has no word for it.

| Token | Strikes |
| --- | --- |
| a message's id, or its whole id | the message, and every text pasted in it; an id of eight characters that two messages share strikes neither, and the answer names both |
| `session:<id>` | every message of that session, each also by its whole id, so a fork or a resume under any name brings none back |
| a label's key, in any case | the label; a stack struck gives its lines back |
| a pasted text's id (`<id>+1`) | nothing: a pasted text goes with the message it came in |

The token stays in `struck.txt`, so that a transcript that still holds the message cannot bring it back, and a struck key is never given again. A words page is mended line by line, or taken away whole where it cannot be; a whole session's strike takes every words page away. A strike holds the home's lock, and every file it rewrites is written beside itself and put in its place.

A strike names, by key, the labels left resting on what it took, and leaves them for the person to strike too. It ends by naming what no strike can reach: the harness's own transcript, an earlier second copy or a backup, and the history of a repository that holds the home. The pages of the cuts keep ids and sizes, never words. A strike that strikes nothing says why in one sentence, and writes nothing.

The one other way anything is struck is a mark that writes a misaligned stack again ([The store](store.md)). It never strikes a message, and a session's mark cannot so strike a stack of the person's.

---

### Who can read the files

Every folder the plugin makes is its owner's alone (0700), and every file it writes too (0600). A home an older make left readable by other accounts is narrowed the next time `/crossings on` or `status` runs for it. On Windows these modes mean nothing, and none is set.

No file of a home is read or written through a link: one check, `within` in `crossing/record.py`, is used by every piece, and a home with a link anywhere below it is refused whole.

Where a home lies inside a repository and has no `.gitignore`, switching on writes one that keeps out everything but the label pages, `hand-over.md` and the pages of the cuts. An ignore file that is there is left as it is, and `status` says once where it lets in `said/`, where the words are kept.

---

### The second copy

Where the home's `copy` file names a folder, the plain files go there as one encrypted disk image (AES-256, by macOS's `hdiutil`). It is made at each cut of a session a person sits in, at a session's end where `CROSSING_WAIT` is `1`, and with `door.py copy`. The passphrase is a random one, kept in the Keychain under `crossing-archive`. The image is replaced whole each time, and only once it reads back the same; the index never goes.

- No copy is made where the copy's folder lies inside the project, or the temporary folder it stages in lies inside the home, the copy's folder or the project.
- The plain files are staged outside the home, for the owner alone, and taken away file by file; a stage a killed run left is taken away by the next.
- `CROSSING_COPY_KEY` is the passphrase instead only at the person's own terminal; anywhere else it is passed over, with a line in the error log.
- A failure is said in one sentence that names no command, since the Keychain's call holds the passphrase.
- An older image, named by the project's folder alone, is left as it is, and `status` names it once.

It is a backup only. A home restored from it by hand is taken in with `adopt`, and an earlier image, or a backup of the folder, keeps what was struck since.

---

### A message that looks like a secret

A message of the person's that looks like it holds a key or a password is kept: the plugin keeps what was said, and is no filter. Its id alone goes into `flagged.txt`, and the person's own `status` and `look` name it, with the strike that removes it.

The session is never told, and the frame never quotes it; `find` and `thread` still give it, since the session heard it when it was said. The patterns are few, so that talk about passwords is not taken for one: a PEM private key, an AWS access key id, a GitHub token, an `sk-` key, a bearer token, and an assignment such as `password=` or `api_key=` with a value of eight characters or more.

---

### What labels are for

A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them. The welcome and the door's own descriptions of `mark` and `leave` say so. A label crosses every cut as standing, and the session that reads it acts on it.

Text a session reads, a page or a tool's output, can steer it to mark such a label. So a label marked through the door that speaks for the person (`his` or `both`), or about the two of them, is shown to the person as it is written, and so is every line left at the door. Nothing is blocked.

A label that came into the pages any other way (a pull, a branch switch, a hand) is named once by the person's next `status`, and so is every label of a home as it is adopted. Which labels came through the door is believed only from the receipts beside the person's record, never from a file inside the home.

---

### The archive's own files

A session reaches what was said through the door. The hooks module looks at each of the session's tool calls (a file tool's paths, a search's pattern, a shell command's text) and refuses:

- a read of the archive itself: a home's `said/`, its `store.db`, a words page (`*.words.md`), or any other path below a home that is none of the files a session may read there;
- a write of a file the door alone writes (the label pages, `hand-over.md`, `struck.txt`, the pages of the cuts, the one-line settings), by a writing tool or a shell command that is not a plain read;
- a write, or any shell command, that names a file a hook or the door keeps for itself (`off.txt`, `unsaid.txt`, `models.txt`, the markers and the rest), or the person's record of switches;
- a shell command that runs `door.py` with one of the person's verbs or options, or runs `crossing/handover.py` or `crossing/read.py`.

The lists are the module's own, `KEPT`, `WRITTEN_BY_DOOR` and `READABLE`, in `hooks/crossings.ts`. The label pages, the pages of the cuts and the settings stay readable, and a shell call of `door.py` with the door's own verbs runs. Below any other folder named `crossings/` (a program's own package, or a project where Crossings was never switched on) only the archive's own names are refused: `said/`, `store.db` and a words page.

The module decides by string checks at every call, and opens no file. It knows the homes the settings name, those the plugin keeps by default, and this project's home as the door names it: it asks the door as a session starts, after `/crossings` turns the switch, and at a cut. A command's quotes and backslashes are taken out first, as the shell takes them out, and a `..` is taken as the step back it is.

---

### What it cannot keep out

- A project whose settings the person has let the harness trust can run programs as the person, and those can read any store on this computer, the record of switches included.
- A session with a shell the person lets run commands can do what the person can: stand the door at a made-up terminal, set the plugin's flags itself, or reach a file by a path no check sees (a variable, a `cd`, a whole folder at once).
- A project whose settings set `PATH` decides which `python3`, `security` and `hdiutil` run, and one that sets `TMPDIR` decides where the second copy stages; both are trusted.
- A home switched on from a terminal in the middle of a session is guarded by the archive's own names alone until that session's next start, switch or cut.
- A home put back by hand from the second copy lacks `flagged.txt`, `unattended.txt` and `unsaid.txt`. It may quote a message that looks like a key, keep a prompt of a session no person sat in, or keep a row said while off whose time a clock moved, where the old transcripts are still there.
- A block the harness puts into the person's turn under a name the plugin does not know is kept as the person's words.
- An id a reading adds to `unsaid.txt` after the switch last wrote the person's record is not in its count or digest, so one taken away before the next switch is not missed.

The guards are checks: the terminal, the flags, the module's string checks, the record's counts. They catch what is plain, and are no walls. The wall is the person's own approval of what a project may set and what a session may run.
