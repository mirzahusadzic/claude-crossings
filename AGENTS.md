# Repository guide

Crossings is a small Claude Code plugin that keeps what was said in a project, word for word, in plain files, gives a session a door back to it, and brings a small frame across a context cut. Prefer focused fixes and plain words; add no runtime dependency, no model call and no network. The plain files are the record and the index is only made from them: keep it that way.

People read the [README](README.md) and `docs/`. This file is for agents and maintainers: rules, where the code is, and what is easy to get wrong.

---

### Standing rules

These hold for every change.

| Rule | Detail |
| --- | --- |
| No dependency | Standard library only, in every file under `crossing/`. The module uses the harness's own API alone. |
| No model, no network | No model is called, and nothing opens a network connection. |
| The plain files are the record | They must keep reading as they do. A page written before keeps reading exactly as before. |
| A test with every change | A change in behaviour comes with a test that fails on the old code and passes after. |
| Made-up data | No real person's name or words in code or tests: made-up sessions, made-up messages. |
| Tests stay home | Tests use made-up transcripts, temporary homes and data folders, and a stand-in that refuses the Keychain. No test reaches the person's own home. |
| The coverage floor | Branch coverage of `crossing/` stays whole, 100 (`.coveragerc`), on Python 3.9, 3.13 and 3.14. A new branch comes with the test that walks it. |
| What a session is told | A change to any sentence a session is told makes `docs/told.md` again in the same commit. |
| A new note | A new sentence a session is told keeps the notes' opening and their tone: as context, asking for no numbers, nothing to report. |
| Drawn by scripts | The README's figure is drawn by `scripts/figure.py`: change the script and run it again, never the SVGs by hand. `docs/told.md` is made by `scripts/told.py` the same way. |
| Loaded from a copy | The plugin is developed in this folder and loaded from a copy of it. The copy is brought up to date only after every test file, `claude plugin test .`, the coverage floor and `claude plugin validate .` pass. |
| Docs | Who reads what, how a page is written and shaped, and how a change to one is checked, are in Docs below. |

---

### Commands

Each runs from the top of the repository. The table says what each needs or does.

```sh
python3 tests/test_<name>.py
pytest
claude plugin test .
sh scripts/coverage.sh
claude plugin validate .
python3 scripts/figure.py
python3 scripts/told.py > docs/told.md
uvx ruff@0.17.4 check .
uvx ruff@0.17.4 format --check .
git diff vX.Y.Z.. -- docs/told.md
```

| Command | Notes |
| --- | --- |
| `python3 tests/test_<name>.py` | Runs one file, offline, on made-up transcripts and temporary homes. Needs a `python3` with FTS5 in its `sqlite3`, and nothing else. |
| `pytest` | Runs them all. |
| `claude plugin test .` | Runs `hooks/crossings.test.ts`, the module's tests. |
| `sh scripts/coverage.sh` | Measures branch coverage of `crossing/` with the hooks' own processes, against the floor in `.coveragerc`. Needs `uv`. `UV_PYTHON` picks the Python it measures on, 3.13 where unset. |
| `claude plugin validate .` | Checks the manifests. |
| `python3 scripts/figure.py` | Draws the README's figure, `docs/images/crossings-light.svg` and `-dark.svg`. |
| `python3 scripts/told.py > docs/told.md` | Makes the page of everything a session is told. `tests/test_told.py` holds it to the code. |
| `uvx ruff@0.17.4 …` | The pipeline's lint and format check, at the version it pins. |
| `git diff vX.Y.Z.. -- docs/told.md` | What a session is told now that it was not at release X.Y.Z, for the release's notes. |

---

### Design invariants

What must stay true, with the code that keeps it where one place does.

#### The switch and the home

- **Nothing before the switch.** Nothing is kept for a project until the person switches it on there: no archive, no label, no database, no record of a cut. No read makes a folder or a database.
- **The switch is the person's.** It lives outside every project, in the person's record (`store.switched`). A home is believed only where that record names it for this project. A setting that names a place inside the project, or no absolute path, is not followed.
- **Inside, by the files.** A place, its links followed, and each folder above it are compared with the project's top by device and inode (`record.lies_in`). The second copy's stage is judged the same way.
- **One rule finds a home.** `record.located` is the one rule by which every piece finds a project's home.
- **A folder below a home.** It takes nothing of that home until the person answers for it, at their own keystroke. `join` shares it; `here` gives the folder a home of its own outside the project (`store._found`, `store.waiting`). Until then a session there is told so in one sentence, and the guard still knows that home (`door.py home`).
- **No links.** No file of a home is read or written through a link: every path inside a home goes through `record.within`. A home with a link below it is refused whole (`record.sound`). A project's own `crossings` that is a link is no home: nothing is believed, located or switched on through it (`store.linked`).
- **One folder, one home.** A folder is one home by whichever spelling of its letters reached it. Paths are taken as the disk spells them (`record.spelled`), and the person's record is matched by the files (`store.believed`).
- **The person's own folder.** It is read from the account by `record.own`, never from `HOME`.
- **Ids in paths.** An id that becomes part of a path or a line of a small file passes `record.ident`.
- **Modes.** Every folder the plugin makes is 0700 and every file 0600, except on Windows.

#### Damaged files and the record of the switch

- **A line that is no text.** Every reader passes it over (`record.lines_in`, `record.decoded`) and logs it. Nothing stops for it, and the person's next `status` names the file once.
- **`off.txt` is the exception.** A line of it that is no span means what it held cannot be told. Nothing is archived until the person switches on again (`store.lost`).
- **A record of spans cut short.** So too where `off.txt`, `unsaid.txt` or `off-places.jsonl` holds fewer spans, ids or places than the person's record keeps (`held`). So too where it holds as many with one changed for another (`sealed`, a digest of each in its order), or cannot be read.
- **`switch on` takes an empty home.** It takes only a home that holds no file but a `.gitignore` (`store.unclaimed`).

#### What is kept, and whose

- **Off is off.** Nothing said while the switch is off is kept, by any reading of any transcript, nor given on a hand-over's words page. That holds also where the clock was set back meanwhile (`off.closed`).
- **Off, by place.** In a transcript the archive knew as it was switched off, it holds whatever time a row bears (`store.PLACES`). So it does in every transcript it knows where switching on restores a lost record (`store._unsaid_by_id`).
- **`unsaid.txt`.** It keeps one id a message a reading met. No count of them is kept but the one the person's record keeps to tell a file cut short.
- **A lost record lists nothing.** A cut counted while the record of the spans is lost (missing, holding fewer spans, ids or places, or a line that is no span) lists nothing said.
- **No person, nothing kept.** Nothing is archived from a session no person sits in, nor given on a hand-over's words page, nor carried by `door.py frame` or `page`. The server answers such a session in one sentence.
- **Nobody's words.** No row marked `isSidechain`, and no row whose model is `<synthetic>` (the harness's, in the session's place), is anyone's words.
- **No note to a subagent.** No note at a session's start, a cut or a model switch is given to a session no person sits in, or to a subagent. A subagent's cut writes nothing.
- **No reasoning, no tool traffic.** Reasoning blocks and tool traffic are never used or kept. Each transcript row is parsed whole, `transcript.session` takes text blocks alone, and the count measures tool traffic by length only.
- **A paste is not the person's.** A pasted text is a row of its own in the index. It is not counted, and the frame does not quote it.
- **`his` on disk.** The person's side is kept as `his` in every file of a home and in the index, as every make has written it, so that each make reads every home (`store.HIS`, told by `store.theirs` alone).
- **`his` never shown.** A session is offered `their` and `pair:them`, and a label's owner is printed `theirs` (`store.owner`). `his` and `pair:him` are still taken and mean the same.
- **Cut pages hold no words.** A cut's page and sidecar hold no text of either voice. A summary's runs are kept only as digests keyed with the home's own key.

#### Strikes and marks

- **A strike stays struck.** Its token stays in `struck.txt`, a message's as its whole id, so that a later message sharing its first eight characters is kept. The whole id of every message a session's strike took stays beside it.
- **Everything obeys it.** Every build obeys a strike, a hand-over's words page leaves it out, and a struck key is never given again.
- **A shared id.** An id of eight characters two messages share strikes neither.
- **A mark strikes little.** A mark strikes nothing but a misaligned stack it writes again. A session's mark never strikes the person's own.
- **A label's length.** A label's sentence is at most `store.LONGEST` characters (4,000).
- **Short writing.** `mark` and `leave` ask for short writing. A long label or line is still written whole, and the answer says how long it is (`door.long_said`). A refusal and a silencing are never told so.
- **Where long begins.** At `store.SHOWN` (160) for a label the person is shown, at `door.SHORT` (240) for another, and at `door.TENTH` (900) for a line left at the door.

#### The door and the person's verbs

- **The server's verbs.** The door's server offers no verb of the person's (`switch`, `strike`, `layer`, `copy`), nor `home`, `trace` or `welcome`. Its answers name no file or folder (`--bare`).
- **The person's gate.** The person's verbs and options (`door.PERSONAL`, which holds `trace` and `welcome` too, and `--transcript`, `--session`, `--model`) run only at a real terminal or for the plugin's own hooks and module (`door.personal`). `--model` runs also for the server in its own process.
- **The person's scripts.** The same gate holds `crossing/handover.py`, which writes only into a home the door believes (`handover.believed`). It holds `crossing/read.py`, which gives a message only for an id that names one row and nothing the believed home keeps out. The module refuses a session's shell command that calls them.
- **The protocol.** The server speaks MCP over stdio, by hand, with the standard library alone. Its eight tools are loaded in front of a session, not searched for.
- **An id as written.** An id is taken as it is written: `%` and `_` stand for no character.
- **Cleaned by one rule.** What is shown is cleaned by `store.clean` alone. That covers a message's or a label's words, and every scalar a transcript or the harness gave (a time, a trigger, a transcript's path). `crossing/show.py` shows a cut's sidecar by the same `clean`.
- **The pages keep what was written.** The archive keeps a row's time only where it has the shape of a moment (`off.SHAPE`).
- **Shown as marked.** A label that speaks for the person, a standing line, and a line left at the door are shown to the person when marked through the door. A text longer than `store.SHOWN` is cut there, and the line ends with its whole length.
- **Lines that came another way.** A label that came into the pages any other way is noted by a build and named once by the person's next `status`. So is a line of `models.txt` no signing wrote. Nothing is blocked.
- **The receipts.** What the door wrote is known only by the receipts kept beside the person's record (`store.RECEIPTS`), never by a file of the home.
- **The model of a `mark`.** The hook before a call of `mark` writes the call's digest and the model into `calling.txt`. The server takes the line of the same digest out.

#### Hooks and the module

- **Quiet failures.** Every hook failure ends quietly: `hook.main` returns 0 and writes the error log. The module's handlers fall back to the harness.
- **No hook at every prompt.** `UserPromptSubmit` is not wired.
- **A note asks nothing.** A note to a session asks for no inventory, no numbers of its own and no account.
- **The module opens no file.** The module opens no file of a home itself: it reads and writes a home through `door.py`.
- **When the module asks `home`.** It asks `door.py home` only as a session starts, after its own `/crossings` has turned the switch, and at a cut. It keeps the answer for the session: a tool call starts no process and opens no file.
- **A cut's frame, carried whole.** The module asks for it as `frame --session` does, and carries what it gives whole. So the sentence after the frame comes only at a terminal, through the server, or with `--trade`, which `/crossings frame` gives.

#### Locks and the index

- **The home's lock.** An archive, a reading of a session no person sits in (`store.unattended`), a mark, a signing (`store.sign`), a strike, `layer`, the switch and every build of the index hold the home's lock (`store._locked`). A build asked for under it is made there (`store._built`).
- **Written beside itself.** Every file a strike or `layer` rewrites is written beside itself and put in its place.
- **The second copy's lock.** A second copy holds the home's lock while it stages the plain files and as it puts its image in place. It puts it in place only where each staged file still begins as it was staged. One second copy of a home is made at a time (`second.COPYING`).
- **The second copy's stage.** It is taken away file by file. A killed run's stage is known as the copy's by a token beside it.
- **The record's lock.** The person's record, `switched.indexes` and `switched.receipts` are written under one lock (`store._recording`). It serves both writers of the record, `consent` and `_spans_kept`. It is taken after the home's lock and never before it.
- **An index added to.** It is the database a whole build makes from the same files. Where that cannot be trusted, it is made whole. `door.py build` always makes it whole.
- **Which index is believed.** One whose mark is the one its last build kept outside every project (`store.MINTED`). Where that mark could not be kept, the one the same process made (`store._unkept_marks`). Switching on and `adopt` make it anew.

#### The frame

- **Its bounds.** The frame stays within `frame.MOST` characters (9,500), cutting the line at the door to the room left where it must. `frame.LEAST` (2,400) is the least a size is held to. It names only the door's tools that exist.
- **A long work label.** In the room left once the person's words are chosen, a work label that does not fit is passed over, and each older one that fits is carried. The standing lines, and the first pass over the work, stop at the first that does not fit.
- **No turn, byte for byte.** A frame where no turn is set is the frame as it was before turns were set, byte for byte.
- **Turns cost no more than a line.** Take a frame without turns whose line at the door is as long as the line with its turns. At every size, the frame with turns carries every label that one carries, and stays within its size.
- **No filler.** A label added only to fill room the turns had reserved is none that a line at the door as long would keep.
- **The sentence after the frame.** It is counted from the same making as the frame it follows (`frame.with_trade`). That frame is not made again for it.
- **No sentence that contradicts.** Handed a frame the home no longer gives, `frame.trade` says nothing. Where a mark or a strike comes between the frame's making and the one it is measured against, the frame is given, and no sentence.

---

### Source map

Which file holds what, and the names to look for.

| Path | Holds |
| --- | --- |
| `hooks/hooks.json`, `hooks/run.sh` | The wired hooks, and the one entry that starts `crossing/hook.py` for every hook. A word after it (`frame`) asks for the frame hook. |
| `crossing/hook.py` | Every hook: the notes a session is told, the line shown to the person, the retelling line, the frame hook. `main`; `LONG` and `MOSTLY`, the retelling line's 20,000 characters and 60%. |
| `crossing/door.py` | The door's verbs, the person's gate (`PERSONAL`, `personal`), every sentence the door answers with (`UNSEATED` for a session no person sits in). |
| `crossing/door.py`, the module's verbs | `for_the_module`: `words` (the one-word settings), `page`, `trace` (writes `last-cut.json`). `words` and `page` read and write nothing and run from any shell. `welcome`: the note due as the switch is turned. |
| `crossing/door.py`, `handed_over` | What `page` gives: the hand-over page's label rows, and the archive's words for what they rest on (`store.worded`), within `frame.MOST`. |
| `crossing/serve.py` | The door's server, started by `.mcp.json`: tools, their descriptions, its instructions, refusals. `tool` marks each tool to be loaded (`anthropic/alwaysLoad`). |
| `crossing/store.py`, the home | Finding and believing a home (`_found`, `believed`, `linked`, `waiting`), the switch (`switch`, `switched`, `unclaimed`), the ignore file. |
| `crossing/store.py`, the record | The archive, markers, the lock (`_locked`, `_recording`), secrets, off-the-record readings (`lost`, `PLACES`, `_unsaid_by_id`), receipts (`RECEIPTS`). |
| `crossing/store.py`, labels | Labels, stacks, states, mark, strike, signing (`sign`), the person's side (`HIS`, `theirs`, `owner`), `clean`, `LONGEST`. |
| `crossing/store.py`, the index | Build (`_built`), `MADE`, `MINTED`, `_unkept_marks`; the full-text tokenizer `TOKENS`; find, thread (`_named_row`), look. |
| `crossing/record.py` | Where a home lies (`located`), links (`within`, `sound`), ids (`ident`), spellings (`spelled`), adding lines (`add`), the person's folder (`own`). |
| `crossing/record.py`, the rest | File modes, the terminal and plugin checks (`terminal`, `attended`), settings inside the project (`astray`, `lies_in`), damaged lines (`lines_in`, `decoded`), the logs, a cut's page and sidecar, the runs key. |
| `crossing/frame.py` | The frame: `compose`, `_made`, `_composed`, `with_trade`, `trade`, `_stamp`; `SIZE`, `LEAST`, `MOST`, `DOOR`. |
| `crossing/sample.py`, `crossing/sampler/` | What the record weighs: a stretch's events and `unmarked`. The arithmetic on ids and whole numbers, with its settings in `core.SETTINGS`. |
| `crossing/layer.py` | Which model is there: `there.txt`, and `calling.txt` by the call's `digest`. |
| `crossing/off.py` | Off the record: spans, `unsaid.txt`, judging a row by its time (`closed`, `SHAPE`). |
| `crossing/count.py` | Counting a cut, digests of a summary's runs. |
| `crossing/transcript.py` | Every rule about what a transcript row is: who said what, pastes, models, cuts. `session`; `HARNESS_NAMES`, the names the harness is known to write. |
| `crossing/second.py` | The second copy: `make`, `COPYING`, its stage (`emptied`, `mark_of`). |
| `crossing/handover.py` | A hand-over's words page, written through `record.within`; `believed`; `MOST`, the 700 characters of one message. |
| `crossing/read.py` | Reading a message back from a transcript. |
| `crossing/show.py` | The cuts on record, in a few lines. |
| `hooks/crossings.ts` | The cut in the module (`session.compact`), `/crossings`, `askHome`, and the guard on the archive's files (`KEPT`, `WRITTEN_BY_DOOR`, `READABLE`, `ARCHIVE`). Tested in `hooks/crossings.test.ts`. |
| `.claude-plugin/plugin.json` | The manifest. |
| `scripts/coverage.sh`, `.coveragerc` | Coverage. |
| `scripts/figure.py`, `scripts/told.py` | The README's figure; `docs/told.md`. |
| `.github/workflows/ci.yml` | The pipeline. |
| `README.md` | What it is, install, the switch, develop. |
| `docs/store.md` | Homes, files, messages, labels, stacks, refusals, states, the index, markers. |
| `docs/door.md` | Tools, a pair, what the lists show, the server, its refusals, the command, the person's verbs, what a session is told and what the person is shown. |
| `docs/frame.md` | Who is given a frame, what it holds, its size, its packed part, the session's turns, refusals in it, what the record weighs. |
| `docs/cuts.md`, `docs/layers.md` | The count, modes, the retelling line, the hand-over; models. |
| `docs/privacy.md` | What is kept, off the record, striking, the guard, what it cannot keep out. |
| `docs/settings.md` | Variables and one-line files. |
| `docs/words.md` | The tool's own words, a line or two each, with a link to the section that tells each in full. |

---

### Gotchas

What is easy to get wrong.

| Area | What to know |
| --- | --- |
| A new form in the plain files | A label row, an archive line, a line of `models.txt`, `off.txt` or the person's record keeps its form. Something new goes beside them in a file of its own (as `models.txt` went beside the pages), or as an optional field (as `model` went into the archive's lines). |
| The index's make | The index may change freely: raise `store.MADE`. An index of another make is made again from the plain files before it is read. |
| A new small file of a home | One a session must neither write nor name in a shell goes in the module's `KEPT` pattern. One it may read and must not write goes in `WRITTEN_BY_DOOR` and `READABLE`; one it must not read, in `ARCHIVE`. Each comes with a test in `hooks/crossings.test.ts`. |
| What the guard refuses | A path below a home the guard knows that `READABLE` does not name is refused to every call of a session's. It knows the homes the settings name or the plugin keeps by default, and this project's home as the door last named it. |
| Other `crossings/` folders | Below any other folder named `crossings/`, only `said/` one step below it, `store.db` and a words page are refused. Every other path there runs. |
| Two `spelled` | `record.spelled` gives a path as the disk spells it. `store.spelled` resolves it first and gives the text the person's record names a folder by. |
| Adding a line | `record.add` is the one way to add lines to a file of a home, a log or the person's record. It first ends a last line that has no line feed. |
| The turns' room | How the line at the door's turns are reserved and given back, and how a standing line's turns are fitted, is said in the code (`frame._made`, `frame._composed`). Read it there before changing what gives way first. |
| A change during the count | `frame._stamp` sees a change by each file's name, size, time and inode. A change made in place that keeps them is not seen. |
| What a session is told | It is read whole, not only piece by piece. Each sentence is reviewed on its own, and what they do together shows only where they are read together. |
| The server's process | The door's server is one long-lived process a session. A new version is picked up when it is reconnected or in a new session. |
| The ledger, with `note` | Under `beside` with `note` the module asks for the ledger before the hook makes the frame. It cannot see whether one comes. |
| The types | `tsconfig.json` extends the types the harness lays in `.claude-plugin/types/` when the plugin is loaded. Git ignores that folder on purpose. |
| One suite at a time | Run one suite at a time on a machine. A test of the second copy counts the stage folders in the system's temporary folder, and fails where another run makes one meanwhile. |
| Pages read by tests | `tests/test_seams.py` holds two phrases of the Labels section of `docs/store.md`, on how a mark bounds a sentence's length. It also holds a sentence on `adopt` in `README.md` and `docs/settings.md`. |
| The scale test | `CROSSING_SCALE=0` leaves out the scale test of `tests/test_reading.py`. It is unset by default, and is for the tests alone. |
| Coverage on 3.9 | The script picks coverage 7.10.7 on 3.9 and 7.17.2 from 3.11 on, with a venv for each Python. 3.9's compiler steps over a bare `continue` or `break` that a jump lands on, so that line is reported never run on 3.9 alone. Write such a branch as an `if`/`else`, and see that a test makes each half of an `or` true by itself. No `pragma: no cover`, no exclusion. |

---

### Docs

The model is the README and AGENTS.md of `unified-model-router`: a brief README, detail in `docs/`.

| Page | Shape |
| --- | --- |
| README | `# Name`, badges, one intro paragraph, the figure with its caption, bold-label bullets; then `###` sections under `---` rules; a footer that is the whole map: the words and what a session is told first, then every other page, the guide, the licence and the notices, joined by " · " |
| `docs/` page | `# Title`, a lead saying where it fits, `---`, then `###` sections, each opening with a lead; parts are `####` |
| `docs/told.md` | Made by `scripts/told.py`, never by hand |
| Release notes | As a `docs/` page: what is not ready first, then Fixed, Changed, Install, Cite |

- Leads and paragraphs of two or three sentences; short plain sentences, one thought each, about 25 words; no marketing words.
- Tables only for what is looked up, a cell a sentence or two; run-in lists otherwise; an ordered list for an order.
- Explanation before a code block, no comments inside it.
- One alert per section at most; each link once per page, links to different anchors counting as different. The README's footer is the map and repeats the body's links.
- The pages tell what a thing is, when a reader cares, and what happens. Code knowledge stays in this file: names of functions and constants, how a procedure runs inside, what a test guarantees.
- Move text, never drop it. Where a page and the code disagree, the page follows the code. A check is called a check, not a wall.
- A docs change is counted first (paragraphs, sentences, cells, links), then checked against the page before, fact by fact. Before a release, a reader with no context answers questions from the pages alone, and the answers are checked against the code.
- Docs-only changes need the tests that read a page (`test_seams.py`, `test_serve.py`, `test_spared.py`, `test_told.py`), not the full suite.
- Before a release, each statement of a page is checked as a claim against the code, as a paper's claims are: a row for a claim, with the file and line that settles it. Where a claim fails, the page is mended to follow the code.

---

### Tests and the pipeline

Each test file runs its own `test_` functions in a temporary folder, with or without pytest. The pipeline, `.github/workflows/ci.yml`, runs on every push and pull request.

- **Tests.** On macOS and Linux, on Python 3.9, 3.13 and 3.14: ruff's lint and format check, a check that `sqlite3` has FTS5, and each test file on its own.
- **Coverage.** On macOS and Linux, on Python 3.9, 3.13 and 3.14: `scripts/coverage.sh`, held to the floor of 100 in each of the six cells.
- **Module and manifests.** On macOS and Linux: `claude plugin validate .` and `claude plugin test .`, with the Claude Code version the module is tested with.

---

### Releases

A release is the commit `version: X.Y.Z` and an annotated tag `vX.Y.Z` on it.

1. `docs/told.md` is read whole and cold, by the person and by a session with no context of the work, with three questions. What all of it together leans the model toward. How it reads on its words alone, without the intent that wrote it: a sentence that slips in is written in good faith, by authors who read it through what they meant. Which of it is scaffolding that can retire, and which a guard that must stay.
2. What they find is written beside the release.
3. The pages' claims are checked against the code and mended (Docs, above).
4. The commit `version: X.Y.Z` changes the version in `.claude-plugin/plugin.json`, in `CITATION.cff` and on the README's status badge. A test holds them to one another.
5. The tag's message is its title, `Crossings vX.Y.Z`, a blank line, one line of what the release is, and then `Fixed:` and `Changed:`. Each fix or change is a line of its own, as the release's notes say them. A tag of its title alone is not made.
6. The branch and the tag are pushed first.
7. The GitHub release is made only when the pipeline's runs on both have ended green. It says the same as the tag at length, and what has not run for real comes first under its own heading. Its notes carry what a session is told now that it was not before (`git diff vX.Y.Z.. -- docs/told.md`).
8. The release is what is archived under a DOI, and what is archived stays.
