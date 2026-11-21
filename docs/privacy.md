# Privacy

What Crossings keeps, what it never reads, who can read what it keeps, what the person can take back, and what it cannot keep out. Nothing in the plugin calls a model or opens a network connection. What it keeps stays in plain files on this computer, and in a second copy only where the person names a folder for one.

[The words](words.md) says in a line or two what each of the tool's own words means.

---

### What is kept, and what is never read

From a transcript, Crossings keeps what the person and the session said to each other, word for word. The table names each part of a transcript, and what of it is kept.

| From a transcript | Kept |
| --- | --- |
| what the person typed, or sent while a turn ran | Yes, word for word, with its id and time. |
| what the person pasted into a message | Yes, in the message's line. The index keeps it apart from the person's own words ([The store](store.md)). |
| the session's text to the person | Yes, word for word, with the model its row names. |
| a reasoning block, a tool call, a tool result | Never. A cut's count measures tool traffic by its length alone. |
| the harness's notes and reminders, and a note the plugin itself carried | Never. |
| a prompt another plugin submitted between turns | Never. |
| a subagent's rows (`isSidechain`), and rows the harness wrote in the session's place (model `<synthetic>`) | Never. They are nobody's words to the person. |
| the harness's summary at a cut | Never. Only its length is kept, and digests of its runs keyed with the home's own key. |

#### What is the person's

A text in the person's turn is kept as the person's, unless it is the harness's or another plugin's, as below.

- **The harness's.** A text made wholly of blocks under a name the harness is known to write. Or one that opens with one of a few fixed openings.
- **The person's.** Any other text is the person's, and is kept: `<3`, a `<div>`, a sentence about a system reminder.
- **Another plugin's prompt.** It is known by the harness's own wording at its start and in its last paragraph. One the harness wraps otherwise is kept as the person's.

#### A session no person sits in

Nothing is archived from a session no person sits in. That is one the harness does not name `cli`, as `claude -p` or the SDK, whose prompts are a tool's.

- **Its messages.** Its hooks keep their ids in `unattended.txt`, and no word of them. So a fork or a resume cannot bring them in later.
- **Its cuts.** They are still counted, with no words.
- **No frame.** No frame or hand-over is given to it.

A subagent's cut writes nothing at all. A transcript the person hands to `door.py` by its path, from their own terminal, is taken as it is.

#### What is kept beside the words

Beside what was said, the plugin keeps a few records of its own. The logs lie in the plugin's data folder, outside every home: `CLAUDE_PLUGIN_DATA`, else `~/.claude/crossing`.

- **`errors.log`.** A line a failure or a refusal. It is its owner's alone.
- **`calls.log`.** Two lines a hook call: which hook, sizes and times, and never a word of what was said. It is its owner's alone.
- **Turning `calls.log` off.** `CROSSING_DEBUG=0` turns it off. One that cannot be written holds no hook up.
- **`~/.claude/crossing/live/`.** An empty file for each session the plugin is loaded in.
- **`reached.jsonl`.** Inside a home, a line for each pull through `thread`, `mark` and `leave`: when, which verb, which ids, and no words.

---

### The switch

Crossings keeps nothing for a project until the person switches it on there. The switch lives in the person's own record, outside every project, so no repository can switch it on.

- **Where the record lies.** `~/.claude/crossing/switched`, or the file `CROSSING_SWITCHED` names.
- **A line of it.** It names a project's top and its home, spelled as the disk spells them. Switching on writes it, and nothing else does.
- **A folder that shares a home.** A folder below another home's folder that the person shared it from (`/crossings join`) has a line of its own in the record. It names the folder and the home, and no project, so it switches nothing on (see the store page).
- **Beside the record.** The mark of each home's index (`switched.indexes`), and the receipts of what the door wrote into each home (`switched.receipts`).
- **A home switched off before.** The record also keeps what that home's record of when it was off held (below).

| Event | What follows |
| --- | --- |
| a project with no line in the record | It was never switched on. Nothing is kept, though a `crossings/` folder or an old home is there. |
| `/crossings on`, where the home already holds files this computer has no record of | It names what the home holds and where, and switches nothing on. |
| `/crossings adopt` | It takes that home as the person's own, and switches it on. |
| a session or the door in a folder below another home's folder | Nothing of that home is kept or read until the person answers for that folder. `join` shares it, and `here` gives the folder its own. |
| switching on or adopting a home that holds an index | The index is made anew. No database that came with the folder is read. |
| a project's own `crossings` that is a link | It is no home. It is refused in one sentence that names where it leads, and nothing is made in its place. |
| a home named outright (`CROSSING_HOME`) that is a link | It is believed only where the record names where it leads. |
| a setting that names a place inside the project | It is not followed ([Settings](settings.md)). |
| a setting that names no absolute path | It is not followed either. |
| switched off | The line stays. The home is still read, and nothing is added to it. |

#### What `on` and `adopt` take

What `on` and `adopt` each do with a home this computer has no record of switching on depends on what the home holds:

| The home holds | `/crossings on` | `/crossings adopt` |
| --- | --- | --- |
| nothing, or a `.gitignore` alone, or it is not there yet | Makes it where it is not there, switches it on, and sets `beside` and `note`. | As `on`. |
| no folder, and only files whose names begin with a dot, as `.DS_Store` or `.gitkeep` | Names what it holds and where, and switches nothing on. | Switches it on, and sets `beside` and `note`. |
| folders with no file in them, and no file but a `.gitignore` | Switches it on, and sets neither. | As `on`. |
| any other file, at its top or in a folder below | Names what it holds and where, and switches nothing on. | Switches it on, and sets neither. An index it holds is made anew. |

---

### Off the record

`/crossings off` is a way to speak off the record. From the moment it is switched off until it is switched on again, nothing either voice says, in any session of the project, is kept. None of it can be reached later:

- not when it is on again.
- not at a session's end.
- not from a fork or a resume.
- not from a transcript handed to `door.py`.

#### How a span is kept

The switch keeps each span in the home's `off.txt`, in UTC.

- **A message inside a span.** It is passed over, and its id alone goes into `unsaid.txt`. So no later reading keeps it.
- **Where each transcript stood.** As it is switched off, the home notes where each transcript it knows stands (`off-places.jsonl`).
- **What they gained meanwhile.** Switching on keeps off, by id, whatever those transcripts gained meanwhile, whatever time a row bears.

| Event | What follows |
| --- | --- |
| a message with no time | It is kept only where the rows on either side of it are outside every span, with no span between them. |
| `off.txt` is there and cannot be read | Nothing is archived until it can be. |
| a cut comes while it is off | It is not counted, noted in the home, or answered. |
| `mark`, `leave` or `layer` while it is off | Each refuses, and nothing is written. |

#### When the clock was set back

The clock may be set back while it is off, by any amount the steady clock can tell. That is the computer's count of the time since it last started, which is never set back. Switching on then closes the span by the steady clock.

- **A second span.** Switching on also keeps a second span, up to that moment. So what was said after the clock went back is off too.
- **Before switching off.** What was said before switching off, in a transcript the archive had not met, is kept off as well.
- **After switching on.** So is what is said after switching on, in any transcript.
- **For how long.** Each way, for as long as the clock was set back.

#### When the record of it is lost

The record of when it was off is three files: `off.txt`, `unsaid.txt` and `off-places.jsonl`. Each time the switch writes them, the person's record keeps how many spans, ids and places they held, with a digest of each. So a file cut short, damaged or changed for another is told.

- **The record missing, cut short, damaged, or changed for another.** Nothing is archived, counted at a cut or given on a words page. `status` and `look` say why.
- **The next `/crossings on`.** It keeps everything before that moment off the record, and archiving goes on from there.
- **The one count.** That is the one count kept of what was said off the record.
- **No other.** No other count of it, or of its characters, is kept anywhere. The frame never mentions it.

#### What the store shows of it

The store shows that something may have been said, and never what. `status` counts the times it was off, and `look` and `thread` show a span by its two moments. `find` finds nothing of it.

#### What it does not do

- **It does not reach back.** What was kept before it was switched off stays until it is struck.
- **It does not touch the harness's own transcript.** That still holds everything said, for as long as the harness keeps it.
- **A transcript the archive had not met.** Where the archive had not met a transcript when it was switched off, it judges that transcript by its rows' times alone. So a clock set forward and back there is not met.
- **A clock set back later.** Nor is a clock set back after it is on again.
- **The net of a setback.** The steady clock tells only the net of a setback at the moment of switching on. So a clock set back and then partly forward again can leave a row said while off to be kept from such a transcript.
- **A computer started again.** Any setback on a computer that was started again meanwhile can do the same.
- **Only one session is told.** It tells only the session it was switched off from. Every session's `mark` and `leave` refuse all the same.

---

### Striking

`door.py strike <id>` removes a message, a label or a whole session for good. It is the person's, from their own terminal. Neither the door's server nor `/crossings` offers it.

| Token | Strikes |
| --- | --- |
| a message's id, or its whole id | The message, and every text pasted in it. |
| an id of eight characters that two messages share | Neither. The answer names both. |
| one of two such messages, struck by its whole id | That one. The other keeps its note of looking like it holds a key, and the pulls that name it. |
| `session:<id>` | Every message of that session, each also by its whole id. So a fork or a resume under any name brings none back. |
| a label's key, in any case | The label. A stack struck gives its lines back. |
| a pasted text's id (`<id>+1`) | Nothing. A pasted text goes with the message it came in. |

#### What a strike takes

A strike takes what it names from the archive, the label pages, the index, the hand-over's words pages and the home's small files.

- **A words page.** It is mended line by line, or taken away whole where it cannot be. A whole session's strike takes every words page away.
- **The pages of the cuts.** They keep ids and sizes, never words.

#### What stays in `struck.txt`

What was struck stays in `struck.txt`. So a transcript that still holds the message cannot bring it back, and a struck key is never given again.

- **A message.** It is kept there by its whole id, as `<whole id>  # of <what was given>`. So a later message whose first eight characters are the same is kept as any other.
- **A line an earlier make wrote.** A line of eight characters keeps hiding every message whose id begins so. The whole id of the one it struck was not kept.

#### What a strike says

A strike's answer names what it left, and what no strike can reach.

- **The labels left.** It names, by key, the labels left resting on what it took. It leaves them for the person to strike too.
- **What no strike can reach.** The answer ends by naming it. That is the harness's own transcript, an earlier second copy or a backup, and the history of a repository that holds the home.
- **A strike that strikes nothing.** It says why in one sentence, and writes nothing.

The one other way anything is struck is a mark that writes a misaligned stack again (see the store page). It never strikes a message. A session's mark cannot so strike a stack of the person's.

---

### Who can read the files

What the plugin writes is its owner's alone, and no file of a home is read or written through a link. A home inside a repository is given an ignore file, where it has none.

- **Modes.** Every folder the plugin makes is its owner's alone (0700), and every file it writes too (0600).
- **A home left wider.** A home an older make left readable by other accounts is narrowed as it is next switched on. Its `status`, asked anywhere but through the door's server, narrows it too.
- **Windows.** These modes mean nothing there, and none is set.
- **Links.** One check is used by every piece. A home with a link anywhere below it is refused whole.

#### The ignore file

`said/` is where the words are kept. A home's ignore file decides whether git leaves it out.

- **No `.gitignore` there.** Where a home lies inside a repository and has none, switching on writes one. It keeps out everything but the label pages, `hand-over.md` and the pages of the cuts.
- **One that is there.** It is left as it is. `status` says once where it lets in `said/`.
- **Where it lets `said/` in.** Where no line of it leaves out the folder or what it holds. Or where a later line takes the pages back: `!said/*.jsonl`, or a line such as `!*.jsonl` that git reads in every folder.
- **How it is read.** By those lines alone. A line of any other pattern is not read, and is taken as not leaving `said/` out.

---

### The second copy

Where the home's `copy` file names a folder, the plain files go there as one encrypted disk image (AES-256, by macOS's `hdiutil`). The passphrase is a random one, kept in the Keychain under `crossing-archive`.

#### When it is made

- **At a cut.** At each cut of a session a person sits in.
- **At a session's end.** Where `CROSSING_WAIT` is `1`, in a process of its own, since the hook has five seconds.
- **By hand.** With `door.py copy`.

#### What it holds

A copy holds the plain files, and the index never goes.

- **Replaced whole.** The image is replaced whole each time, and only once it reads back the same.
- **Between two acts.** The plain files are read and staged while no other act writes the home. So a copy holds the home as it stood between two acts, never halfway through a strike.
- **A strike meanwhile.** The image is put in place only where every file still begins as it was staged. Where a strike took or rewrote words meanwhile, the image before stands, and the next copy takes the home as it stands.
- **One at a time.** One copy of a home is made at a time. One that finds another under way, or the home held for five seconds, makes none, and `door.py copy` says so.

#### Where no copy is made

- **Inside the project.** No copy is made where the copy's folder lies inside the project.
- **Its temporary folder.** Nor where the temporary folder it stages in lies inside the home, the copy's folder or the project.
- **No file locks.** Nor where the system keeps no file locks of its own, as macOS does, since two copies there could not be kept apart. `door.py copy` says so in one sentence.

#### The stage, the passphrase and failures

- **The stage.** The plain files are staged outside the home, for the owner alone, and taken away after.
- **A killed run.** A stage a killed run left is taken away by the next, in whatever temporary folder it lies.
- **`CROSSING_COPY_KEY`.** It is the passphrase instead only at the person's own terminal. Anywhere else it is passed over, with a line in the error log.
- **A failure.** It is said in one sentence that names no command, since the Keychain's call holds the passphrase. A copy a hook could not make, or gave up on, is a line in the error log.
- **An older image.** One named by the project's folder alone is left as it is, and `status` names it once.

#### A backup only

It is a backup only. A home restored from it by hand is taken in with `adopt`. An earlier image, or a backup of the folder, keeps what was struck since.

---

### A message that looks like a secret

A message of the person's that looks like it holds a key or a password is kept. The plugin keeps what was said, and is no filter.

- **Noted by id.** Its id alone goes into `flagged.txt`. The person's own `status` and `look` name it, with the strike that removes it.
- **The session.** It is never told, and the frame never quotes it.
- **`find` and `thread`.** They still give it, since the session heard it when it was said.

The patterns are few, so that talk about passwords is not taken for one:

- a PEM private key.
- an AWS access key id.
- a GitHub token.
- an `sk-` key.
- a bearer token in an `Authorization:` header.
- an assignment such as `password=` or `api_key=`, with a value of eight characters or more.

---

### What labels are for

The welcome and the door's own descriptions of `mark` and `leave` say what a label is for: "A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them." A label crosses every cut as standing, and the session that reads it acts on it.

#### What the person is shown

Text a session reads, a page or a tool's output, can steer it to mark such a label. So these are shown to the person as they are written, and nothing is blocked:

- a label marked through the door that speaks for the person (`their` or `both`).
- a label marked through the door about the two of them.
- every line left at the door.

[The door](door.md#what-the-person-is-shown) has the line each is shown.

#### Labels that came another way

- **Any other way.** A label that came into the pages by a pull, a branch switch or a hand is named once by the person's next `status`.
- **A home adopted.** So is every label of a home as it is adopted.
- **What is believed.** Which labels came through the door is believed only from the receipts beside the person's record. It is never believed from a file inside the home.

---

### The archive's own files

A session reaches what was said through the door. The hooks module looks at each of the session's tool calls, and refuses those below. It looks at a file tool's paths, a search's pattern and a shell command's text.

#### What it refuses

- **A read of the archive itself.** A home's `said/`, its `store.db` or a words page (`*.words.md`). Or any other path below a home that is none of the files a session may read there.
- **A write of a file the door alone writes.** The label pages, `hand-over.md`, `struck.txt`, the pages of the cuts and the one-line settings. It is refused to a writing tool, and to a shell command that is not a plain read.
- **A file a hook or the door keeps for itself.** A write, or any shell command, that names one: `off.txt`, `unsaid.txt`, `models.txt`, the markers and the rest. So too for the person's record of switches.
- **The person's verbs.** A shell command that runs `door.py` with one of the person's verbs or options.
- **The person's scripts.** A shell command that runs `crossing/handover.py` or `crossing/read.py`.

#### What it lets through

- **What stays readable.** The label pages, the pages of the cuts and the settings.
- **The door's own verbs.** A shell call of `door.py` with them runs.
- **Any other folder named `crossings/`.** A program's own package, or a project where Crossings was never switched on. Below one, only the archive's own names are refused: `said/`, `store.db` and a words page.

#### How it decides

The module decides by string checks at every call, and opens no file.

- **The homes it knows.** Those the settings name, those the plugin keeps by default, and this project's home as the door names it.
- **When it asks the door.** As a session starts, after `/crossings` turns the switch, and at a cut.
- **This project's home.** It is known by its whole path, and by the path to it from the folder the shell stands in.
- **Where the shell stands.** Above the home, beside it or further down (`../crossings/`, `../../crossings/`). A name given after a `cd` into the home is not known.
- **Quotes and steps.** A command's quotes and backslashes are taken out first, as the shell takes them out. A `..` is taken as the step back it is.

---

### What it cannot keep out

The guards are checks, not walls: the terminal, the flags, the module's string checks, the record's counts. They catch what is plain. The wall is the person's own approval of what a project may set and what a session may run.

- **A project the harness trusts.** A project whose settings the person has let the harness trust can run programs as the person. Those can read any store on this computer, the record of switches included.
- **A session with a shell.** A session with a shell the person lets run commands can do what the person can. It can stand the door at a made-up terminal, or set the plugin's flags itself.
- **A path no check sees.** Such a session can reach a file by such a path: a variable, a `cd`, a whole folder at once.
- **`PATH`.** A project whose settings set `PATH` decides which `python3`, `security` and `hdiutil` run. It is trusted.
- **`TMPDIR`.** One that sets `TMPDIR` decides where the second copy stages. It is trusted too.
- **A home switched on mid-session.** One switched on from a terminal in the middle of a session is guarded by the archive's own names alone. That lasts until that session's next start, switch or cut.
- **A home put back from the second copy.** One put back by hand lacks `flagged.txt`, `unattended.txt` and `unsaid.txt`. So it may quote a message that looks like a key.
- **Where the old transcripts are still there.** It may also keep a prompt of a session no person sat in, or a row said while off whose time a clock moved.
- **A block of a name the plugin does not know.** A block the harness puts into the person's turn under such a name is kept as the person's words.
- **An id added to `unsaid.txt` later.** One a reading adds after the switch last wrote the person's record is not in its count or digest. So one taken away before the next switch is not missed.
- **Nothing proves who wrote a line.** A label, a line at the door and a message in the session's voice are plain text in the home's files. Whoever can write those files can write one.
  - **The model.** The model named beside a label ([Layers](layers.md)) is a name, and no proof either.
  - **The record around it.** What holds a line is the record around it, and that is no wall.
  - **What can show.** A label rests on the ids of messages. The session's own words are kept as said beside the person's, and the session can read both in their place. So a line that was changed and no longer fits what was said can show.
  - **What is not seen.** A change that fits is not seen.
  - **A line that looks wrong.** Where a line looks wrong, the session may refuse what it is asked on the strength of it. Its refusal crosses whole.
  - **What the person is shown.** Every label that speaks for the person is shown to the person as it is written, up to 160 characters. A longer one is cut there, and the line says how long the whole is.
