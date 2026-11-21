# The words

What each of Crossings' own words means, in a line or two, with a link to where it is told in full. The pages use many plain words in a sense of their own, and a reader meets most of them before the page that tells them. Nothing here is a rule of its own: the section each word links to holds the rule.

---

### The record

What Crossings keeps for a project, and where it lies.

- **The store.** What Crossings keeps for a project: plain files, and an index made from them ([The store](store.md)).
- **A home.** The folder that holds the store of one project. It is the project's own `crossings/` folder, or a folder outside the project ([a home and where it lies](store.md#a-home-and-where-it-lies)).
- **Believed.** A home is believed where the person's record of switches names it for this project. A project whose home is not believed was never switched on ([a home that is not believed](store.md#a-home-that-is-not-believed)).
- **The home on this computer.** A home that belongs to no project, reached with `ours`. Nothing is archived into it ([the home on this computer](store.md#the-home-on-this-computer)).
- **A folder below a home's folder.** A folder inside the one a home belongs to. It takes nothing of that home until the person answers with `join` or `here` ([a folder below](store.md#a-folder-below-a-homes-folder)).
- **The archive.** Every message of either voice, word for word, one line each in `said/`. A message is one text of the person's or the session's, under its id ([messages](store.md#messages)).
- **The record.** What was said, as the archive keeps it, and the labels that rest on it ([the files the person reads](store.md#the-files-the-person-reads)). The person's record is another file, which keeps the switches (below).
- **An id.** The name of a message: the first eight characters of its whole id, or more where another message's id begins the same. A pasted text's id adds a number, as `a1b2c3d4+1` ([what an id names](door.md#what-an-id-names)).
- **An id two messages share, and a twin.** Two messages whose first eight characters are the same share that id. A later message under the id a label was marked on is a twin of the first ([an id two share](store.md#a-label-on-an-id-two-messages-share)).
- **A paste.** A text the person pasted into a message. It stays in its message's line, and the index keeps it apart, not counted as the person's words ([what the person pasted](store.md#what-the-person-pasted)).
- **Whose, and the person's side.** A label's `whose` is the person's, the session's, or both. A session names the person's side `their`, and a label of theirs is printed `theirs` ([the person's side, by name](door.md#the-persons-side-by-name)).
- **The index.** `store.db`, a search database made from the plain files and from nothing else. It may be deleted at any time ([the index](store.md#the-index)).
- **Receipts.** What the door wrote into each home, kept outside every project, beside the person's record. A label they do not know, or one reworded since, is noted as come by no mark ([labels that came by no mark](store.md#labels-that-came-by-no-mark)).
- **A message that looks like a key.** A message of the person's that looks like it holds a key or a password. It is kept, its id is noted for the person to strike, and the frame never quotes it ([a message that looks like a secret](privacy.md#a-message-that-looks-like-a-secret)).
- **A session no person sits in.** One the harness does not name `cli`, as `claude -p` or the SDK. Nothing is archived from it ([a session no person sits in](privacy.md#a-session-no-person-sits-in)).

---

### The switch, and what the person takes back

The person's own hand on what is kept.

- **The switch, and the person's record.** The switch says whether Crossings keeps a project. It lives in the person's record, a file outside every project, so no repository can switch it on ([the switch](privacy.md#the-switch)).
- **Adopt.** Switching on a home that already holds what this computer has no record of switching on. `/crossings on` names what such a home holds, and switches nothing on ([a home made, or found empty](settings.md#a-home-made-or-found-empty)).
- **Off the record.** The time a project is switched off. Nothing either voice says then is kept, or can be reached later ([off the record](privacy.md#off-the-record)).
- **A span.** One time off the record, kept as a line of the home's `off.txt`, in UTC. A message said inside a span is passed over, and only its id is kept ([how a span is kept](privacy.md#how-a-span-is-kept)).
- **The steady clock.** The computer's count of the time since it last started, which is never set back. Switching off keeps its reading, so that switching on can tell a clock of the day set back meanwhile ([when the clock was set back](privacy.md#when-the-clock-was-set-back)).
- **A strike.** The person's way to remove a message, a label or a whole session for good, from their own terminal. What was struck stays in `struck.txt`, so no transcript brings it back ([striking](privacy.md#striking)).
- **The second copy.** One encrypted disk image of a home's plain files, where its `copy` file names a folder. It is a backup only ([the second copy](privacy.md#the-second-copy)).
- **The guard.** The hooks module's checks on each of a session's tool calls, which refuse a read of the archive's own files. It decides by string checks, and opens no file ([the archive's own files](privacy.md#the-archives-own-files)).
- **Checks, not walls.** The guards catch what is plain: the terminal, the flags, the module's string checks, the record's counts. The wall is the person's own approval of what a project may set and a session may run ([what it cannot keep out](privacy.md#what-it-cannot-keep-out)).

---

### Labels

What a session writes as the work goes, and how each label stands.

- **A label, and what it rests on.** One sentence about a stretch of the record, resting on the ids of the messages it is about: its anchors. It is a row of a page in `labels/`, named by its key, its kind's letter and a number, as `W14` ([labels](store.md#labels)).
- **A standing line.** A label of the kind `relation`, its key `R`, about the person and the session. A frame holds the standing lines whole while they fit, up to 80% of it ([what a frame holds](frame.md#what-a-frame-holds)).
- **A work label.** A label about the work, its key `W`. It is the kind `mark` writes by default ([what `mark` and `leave` write](door.md#what-mark-and-leave-write)).
- **The line at the door.** The line a session leaves with `leave` for the session that wakes after the next cut, its key `N`. Only the newest crosses, whole where the room allows and 300 characters at the least ([the line at the door](frame.md#the-line-at-the-door)).
- **A refusal.** A label of the kind `refused`, its key `X`, for something the session declined. It rests on the message that asked, and its sentence is the session's reason ([refusals](store.md#refusals)).
- **A judgment, and a silencing.** A judgment is a later label of the kind `refused` on a refusal's key: the refusal judged again. A silencing, of the kind `silenced` and its key `S`, puts a refusal to rest ([judging a refusal again](store.md#judging-a-refusal-again-and-putting-it-to-rest)).
- **A family, and the one that stands.** A refusal with every judgment and silencing of it, named by the key of its first refusal. The one that stands is its newest sound label, and where that is a silencing, the family is silenced ([a family](store.md#a-family)).
- **A stack, and the lines beneath it.** A label that rests on other labels of its kind, which are the lines beneath it. Every line stays in its page, and stacks go two deep at most ([stacks](store.md#stacks)).
- **The four states.** Every build finds each label in one of them, from the pages and the archive alone ([the four states](store.md#the-four-states)).
  - **Carried.** It stands by itself, or is the top of a stack. Of a frame, the pages also say "carried" of the labels it holds.
  - **Cooled.** It stands beneath a sound stack, which is carried in its place. In a family, the labels beneath the one that stands are cooled.
  - **Misaligned.** A stack one of whose lines is gone, or was reworded since. So is a row of a family that names what no family is.
  - **Unresolved.** It rests on a message the archive does not hold, or on nothing.
  - **Sound.** Neither misaligned nor unresolved: carried or cooled. What stands beneath a stack that is not sound is carried.
- **A layer.** The model a line was made by, as the message's own row or `models.txt` names it; the person's lines have none. A layer is only a way of reading the pages, and nothing is moved ([a layer for each model](layers.md#a-layer-for-each-model)).
- **Signing.** Keeping which model wrote a label, as a line of `models.txt`. A label marked through the door is signed with the model of the session that marks it ([how a label is signed](layers.md#how-a-label-is-signed)).
- **The model that is there.** The model a session runs now, as the harness tells the hooks. Where they were never told, it is the model of the session's own newest message ([the model that is there](layers.md#the-model-that-is-there)).
- **Reframing.** A stack over lines another known model wrote, which is that model's own to do. Resting a label on another model's messages is not reframing ([resting on, and restacking](layers.md#resting-on-and-restacking)).

---

### A cut

What happens as the harness compacts a session.

- **A cut.** The harness compacting a long session: a summary takes the conversation's place. Crossings answers it as the home asks, and counts it ([at a cut](cuts.md#at-a-cut)).
- **The ledger.** What the hooks module asks the harness's summary to be: what the person asked, where each task stands, the files touched and the standing constraints. It is a request, and the summarizer may not follow it ([the summary's ledger](cuts.md#the-summarys-ledger)).
- **Mode and carry.** Two one-word files of a home. `mode` says how a cut is answered, and `carry` whether the frame crosses as a message or as a note ([the modes](cuts.md#the-modes)).
- **The count.** A cut's page: how much of each voice the summary held word for word, counted by script. It holds no text of either voice ([the count](cuts.md#the-count)).
- **The retelling line.** One line the person is shown where most of a long summary retells the one before. It blocks nothing, and the session is not handed it ([a summary worn down by retelling](cuts.md#a-summary-worn-down-by-retelling)).
- **The hand-over, and a words page.** `hand-over.md` is a label page, carried as a message where no frame can be made. Its words page gives what was said under each id it names, from the transcript ([the hand-over](cuts.md#the-hand-over)).
- **The waking note.** The note a session is given as it comes through a cut. It says which cut this is, that nothing is gone from the record, and to take its time ([the waking note](door.md#the-waking-note)).
- **The welcome.** The note that says what is kept by itself. It says too that labels and the line at the door are the session's own to write ([the welcome](door.md#the-welcome)).
- **The stretch.** What was said in a session since its last cut, or since its start. The sentence of what the record weighs names messages of it ([which messages it names](frame.md#which-messages-it-names)).

---

### The frame

What crosses a cut with the session.

- **The frame.** About 9,000 characters made from the store, given to a session after a cut, or as it starts new, where the home carries one. It holds the standing lines, the line at the door, what was declined, the work and a few of the person's words ([The frame](frame.md)).
- **Its size.** About 9,000 characters, or what a home's `frame-size` sets, held between 2,400 and 9,500. It never exceeds 9,500, the most a hook may carry ([the frame's size](frame.md#the-frames-size)).
- **Packed, and laid out as before.** In a packed frame, each sentence of the person's it quotes stands with what the session told of it beneath. Only a cut's frame for the session that was cut can be packed; any other is laid out as before ([the packed part](frame.md#the-packed-part)).
- **Both ends of a pair.** The person's sentence, and the session's own turn right before or after it. A line resting on both is the session saying what it told of that sentence ([what the frame quotes](frame.md#what-the-frame-quotes-of-the-person)).
- **The session's turns beside a sentence.** In a packed frame, the session's turn right before or after a quoted sentence, set beneath it. It is set where the line at the door, or a standing line, rests on both ends of that pair ([the session's turns](frame.md#the-sessions-turns-beside-a-sentence)).
- **The ask.** A message of the person's that a refusal, a judgment of one or a silencing rests on. The session's turn right after it is written by its ids alone ([the turn after a refused ask](frame.md#the-turn-after-a-refused-ask)).
- **What the record weighs.** One sentence that names, by id alone, up to five of the person's messages no label rests on. It is said while the session can still do something about them ([what the record weighs](frame.md#what-the-record-weighs)).
- **The sentence after the frame.** One sentence told after a frame and apart from it, where the frame sets the session's turns. It says what the turns take, and what the frame would carry without them ([the sentence after the frame](frame.md#the-sentence-after-the-frame)).

---

### The pieces

What the plugin is made of, and who reaches what through which.

- **The harness.** The program a session runs in, here Claude Code. It runs the hooks, loads the hooks module, starts the server, and compacts a long session.
- **The hooks, the module and the server.** The three parts of the plugin ([how it works](../README.md#how-it-works)).
  - **The hooks.** The plugin's hooks the harness runs, as at a session's start and at a cut. They read the session's transcript into the home's archive.
  - **The hooks module.** The plugin's module the harness loads. It answers a cut where the home asks it to, asks the summary for a ledger, gives the person `/crossings`, and holds the guard.
  - **The server.** A small server that answers the door's tools from the home.
- **The door.** How a session and the person reach the store: eight tools for a session, and `/crossings` and a shell's verbs for the person ([The door](door.md)).
- **The door's tools.** `look`, `labels`, `find`, `thread`, `mark`, `leave`, `status` and `crossing`, which a session calls. After a cut, `look` is the place to start ([the session's tools](door.md#the-sessions-tools)).
- **The room.** What `look` gives with no word needed: the days, the labels by kind, the families of refusals, and the newest about the work ([`look`](door.md#look)).
- **A pair.** A turn of one voice, with the other voice's next turn in the same session beneath it. `thread` with a role gives one ([a pair](door.md#a-pair-thread-with-a-role)).
  - **A turn.** Every message one voice said in a row in one session, until the other spoke.
  - **A role.** Which voice's turn heads the pair: the person's with `pair:them`, the session's with `pair:me`. The roles are named from the session's side.
- **The person's command.** `/crossings`, the person's own command in a session. It turns the switch and shows what the store holds ([the person's command](door.md#the-persons-command)).
- **The person's verbs.** The door's verbs the person runs from a shell, as `python3 crossing/door.py look`. Some are the person's alone, and run only at a real terminal or for the plugin's own hooks and module ([the person's verbs](door.md#the-persons-verbs)).
