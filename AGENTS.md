# Repository guide

Crossings is a small Claude Code plugin that keeps what was said in a project, word for word, in plain files, gives a session a door back to it, and brings a small frame across a context cut. Prefer focused fixes and plain words; add no runtime dependency, no model call and no network. The plain files are the record and the index is only made from them: keep it that way.

---

### Map

- Docs: `README.md` (what it is, install, the switch, develop), `docs/store.md` (homes, files, messages, labels, stacks, states, the index, markers), `docs/door.md` (tools, the command, the person's verbs, what a session is told, the frame), `docs/cuts.md` (the count, modes, the retelling line, the hand-over), `docs/layers.md` (models), `docs/privacy.md` (what is kept, off the record, striking, the guard, what it cannot keep out), `docs/settings.md` (variables and one-line files). The README's figure, `docs/images/crossings-light.svg` and `-dark.svg`, is drawn by `scripts/figure.py`: change the script and run it again, never the SVGs by hand.
- Dev: a `python3` with FTS5 in its `sqlite3`, and nothing else. `python3 tests/test_<name>.py` runs one file, offline, on made-up transcripts and temporary homes; pytest runs them all. `claude plugin test .` runs `hooks/crossings.test.ts`.

  `sh scripts/coverage.sh` measures branch coverage of `crossing/` with the hooks' own processes, against the floor in `.coveragerc`; it needs `uv`. `claude plugin validate .` checks the manifests. `tsconfig.json` extends the types the harness lays in `.claude-plugin/types/` when the plugin is loaded, which git ignores on purpose.

| Task | Source |
| --- | --- |
| The one entry for every hook; the notes a session is told; the line shown to the person; the retelling line; the frame hook | `crossing/hook.py`, started by `hooks/run.sh`, wired in `hooks/hooks.json` |
| The door's verbs, the person's gate, every sentence the door answers with | `crossing/door.py` |
| The door's server: tools, their descriptions, its instructions, refusals | `crossing/serve.py`, started by `.mcp.json` |
| Finding and believing a home, the switch, the archive, markers and the lock, secrets, labels, stacks, states, the index, find, thread, look, mark, strike, the ignore file | `crossing/store.py` |
| Where a home lies, links (`within`, `sound`), ids (`ident`), the person's folder, file modes, the terminal and plugin checks, settings inside the project (`astray`, `lies_in`), the logs, a cut's page and sidecar, the runs key | `crossing/record.py` |
| The frame | `crossing/frame.py` |
| Which model is there: `there.txt`, `calling.txt` | `crossing/layer.py` |
| Off the record: spans, `unsaid.txt`, judging a row by its time | `crossing/off.py` |
| Counting a cut, digests of a summary's runs | `crossing/count.py` |
| What a transcript row is: who said what, pastes, models, cuts | `crossing/transcript.py` |
| The second copy | `crossing/second.py` |
| A hand-over's words page | `crossing/handover.py` |
| Reading a message back from a transcript | `crossing/read.py` |
| The cuts on record, in a few lines | `crossing/show.py` |
| The cut in the module, `/crossings`, the guard on the archive's files | `hooks/crossings.ts`, tested in `hooks/crossings.test.ts` |
| The manifest | `.claude-plugin/plugin.json` |
| Coverage | `scripts/coverage.sh`, `.coveragerc` |

---

### Preserve these behaviors

- No model is called, and nothing opens a network connection.
- Standard library only, in every file under `crossing/`; the module uses the harness's own API alone.
- Nothing is kept for a project until the person switches it on there: no archive, no label, no database, no record of a cut. No read makes a folder or a database.
- The switch lives outside every project, in the person's record (`store.switched`). A home is believed only where that record names it for this project. A setting that names a place inside the project, or no absolute path, is not followed.
- No file of a home is read or written through a link: every path inside a home goes through `record.within`, and a home with a link below it is refused whole (`record.sound`). A project's own `crossings` that is a link is no home: nothing is believed, located or switched on through it (`store.linked`).
- One folder is one home by whichever spelling of its letters it is reached: paths are taken as the disk spells them (`record.spelled`), and the person's record is matched by the files (`store.believed`).
- A line of a home's files that cannot be read as text is passed over by every reader (`record.lines_in`, `record.decoded`) and logged; nothing stops for it, and the person's next `status` names the file once. `off.txt` is the one exception: a line of it that is no span means what it held cannot be told, and nothing is archived until the person switches on again (`store.lost`); so too where it, `unsaid.txt` or `off-places.jsonl` holds fewer spans, ids or places than the person's record keeps (`held`), or as many with one changed for another (`sealed`, a digest of each in its order), or cannot be read.
- An id that becomes part of a path or a line of a small file passes `record.ident`.
- The door's server offers no verb of the person's (`switch`, `strike`, `layer`, `copy`), nor `home`, `trace` or `welcome`, and its answers name no file or folder (`--bare`).
- The person's verbs and options (`door.PERSONAL`, which holds `trace` and `welcome` too, and `--transcript`, `--session`, `--model`) run only at a real terminal or for the plugin's own hooks and module (`door.personal`), and `--model` also for the server in its own process; so does `crossing/handover.py`, which writes only into a home the door believes (`handover.believed`), and `crossing/read.py`, which gives a message only for an id that names one row and nothing the believed home keeps out; the module refuses a session's shell command that calls them.
- Reasoning blocks and tool traffic are never used or kept: each transcript row is parsed whole, `transcript.session` takes text blocks alone, and the count measures tool traffic by length only.
- A pasted text is not the person's words: it is a row of its own in the index, it is not counted, and the frame does not quote it.
- A strike stays struck: the token stays in `struck.txt`, with the whole id of every message a session's strike took, every build obeys it, a hand-over's words page leaves it out, and a struck key is never given again. An id of eight characters two messages share strikes neither. A mark strikes nothing but a misaligned stack it writes again, and a session's mark never strikes the person's own (`his`).
- Nothing said while the switch is off is kept, by any reading of any transcript, nor given on a hand-over's words page, also where the clock was set back meanwhile (`off.closed`), and, in a transcript the archive knew as it was switched off, whatever time a row bears (`store.PLACES`), as in every transcript it knows where switching on restores a lost record (`store._unsaid_by_id`); `unsaid.txt` keeps one id a message a reading met, and no count of them is kept but the one the person's record keeps to tell a file cut short; a cut counted while the record of the spans is lost (missing, holding fewer spans, ids or places, or a line that is no span) lists nothing said.
- Nothing is archived from a session no person sits in, nor given on a hand-over's words page, nor carried by `door.py frame` or `page`; no row marked `isSidechain`, and no row whose model is `<synthetic>` (the harness's, in the session's place), is anyone's words; no note at a session's start, a cut or a model switch is given to one, or to a subagent; a subagent's cut writes nothing; and the server answers such a session in one sentence.
- Every hook failure ends quietly: `hook.main` returns 0 and writes the error log; the module's handlers fall back to the harness.
- No hook runs at every prompt (`UserPromptSubmit` is not wired).
- A note to a session asks for no inventory, no numbers of its own and no account.
- A cut's page and sidecar hold no text of either voice; a summary's runs are kept only as digests keyed with the home's own key.
- The frame stays within `frame.MOST` characters, cutting the line at the door to the room left where it must, and names only the door's tools that exist. A label's sentence is at most `store.LONGEST` characters.
- What is shown is cleaned by `store.clean` alone, a message's or a label's words and every scalar a transcript or the harness gave (a time, a trigger, a transcript's path) alike; the pages keep what was written, and the archive keeps a row's time only where it has the shape of a moment (`off.SHAPE`).
- A label that speaks for the person, a standing line, and a line left at the door are shown to the person when marked through the door; a label that came into the pages any other way is noted by a build and named once by the person's next `status`, and so is a line of `models.txt` no signing wrote: what the door wrote is known only by the receipts kept beside the person's record (`store.RECEIPTS`), never by a file of the home; nothing is blocked.
- An archive, a mark, a strike, `layer`, the switch and every build of the index hold the home's lock (`store._locked`; a build asked for under it is made there, `store._built`), and a second copy holds it while it stages the plain files and as it puts its image in place, which it does only where each staged file still begins as it was staged; one second copy of a home is made at a time (`second.COPYING`), and every file a strike or `layer` rewrites is written beside itself and put in its place; the person's record has one lock for its two writers (`store._recording`), taken after the home's and never before it.
- An index added to is the database a whole build makes from the same files; where that cannot be trusted, it is made whole. `door.py build` always makes it whole. An index is believed only where its mark is the one its last build kept outside every project (`store.MINTED`), or, where that mark could not be kept, the one the same process made (`store._unkept_marks`), and switching on and `adopt` make it anew; `switch on` takes only a home that holds no file but a `.gitignore` (`store.unclaimed`).
- The module opens no file of a home itself: it reads and writes a home through `door.py`.
- The module asks the door where this project's home is (`door.py home`) only as a session starts, after its own `/crossings` has turned the switch, and at a cut, and keeps the answer for the session; a tool call starts no process and opens no file.
- Every folder the plugin makes is 0700 and every file 0600, except on Windows.

---

### Conventions

- A change in behaviour comes with a test that fails on the old code and passes after. Tests run with or without pytest: each file runs its own `test_` functions in a temporary folder.
- Tests use made-up transcripts, temporary homes and data folders, and a stand-in that refuses the Keychain; no test reaches the person's own home.
- No real person's name or words in code or tests: made-up sessions, made-up messages.
- Branch coverage of `crossing/` stays at or above 99 (`.coveragerc`), as `scripts/coverage.sh` measures it; the aim is 100.
- The plain files are the record, and they must keep reading as they do. A label row, an archive line, a line of `models.txt`, `off.txt` or the person's record keeps its form; something new goes beside them in a file of its own (as `models.txt` went beside the pages), or as an optional field (as `model` went into the archive's lines). A page written before keeps reading exactly as before.
- The index may change freely: raise `store.MADE`, and an index of another make is built again before it is read.
- A new small file of a home that a session must neither write nor name in a shell is added to the module's `KEPT` pattern, one it may read and must not write to `WRITTEN_BY_DOOR` and to `READABLE`, and one it must not read to `ARCHIVE`, each with a test in `hooks/crossings.test.ts`. A path below a home the guard knows (those the settings name or the plugin keeps by default, and this project's home as the door last named it) that `READABLE` does not name is refused to every call of a session's; below any other folder named `crossings/`, only `said/` one step below it, `store.db` and a words page are refused, and every other path there runs.
- A new sentence a session is told keeps the notes' opening and their tone: as context, asking for no numbers, nothing to report.
- Docs: the README stays short and the detail goes to `docs/`. Top-level sections are `###` headings under a `---` rule; tables where a reader looks something up, prose where something is explained; every behaviour a page states is one the code or a test makes true, and a check is called a check, not a wall.
- The plugin is developed in this folder and loaded from a copy of it. The copy is brought up to date only after every test file, `claude plugin test .`, the coverage floor and `claude plugin validate .` pass. The door's server is one long-lived process a session: a new version is picked up when it is reconnected or in a new session.
