# <img src="assets/icon.svg" width="36" height="36" alt="" align="top"> Crossings

[![CI](https://github.com/mirzahusadzic/claude-crossings/actions/workflows/ci.yml/badge.svg)](https://github.com/mirzahusadzic/claude-crossings/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)
![Claude Code plugin](https://img.shields.io/badge/Claude%20Code-plugin-d97757)
![Python 3.9+](https://img.shields.io/badge/python-3.9%2B%20%C2%B7%20stdlib%20only-3776ab?logo=python&logoColor=white)
![macOS](https://img.shields.io/badge/platform-macOS-lightgrey)
![early alpha](https://img.shields.io/badge/status-early%20alpha-e5a50a)

A Claude Code plugin for what a context cut keeps.

When a session grows long, the harness compacts it: a summary takes the place of the conversation, and the session goes on with the summary alone. Crossings has kept what was said, word for word, in plain files. It gives the session a door back to it, and brings a small frame across the cut. No model is called anywhere in it.

It is for a person who works with Claude Code in one project across many sessions and cuts, and wants what was said there kept on their own disk, readable, and theirs to strike.

- **What was said, kept.** Every message of the person's and of the session's, under its id, in the project's home, from each session a person sits in. What the harness or the plugin itself put into the person's turn is left out, and so is a row the harness marks as a subagent's; [Privacy](docs/privacy.md) has the exact list. Reasoning blocks are never used or kept, and tool traffic is never kept.
- **The door.** Seven tools a session can call: `look`, `labels`, `find`, `thread`, `mark`, `leave`, `status`. Nothing a session reads through them names a file or a shell command.
- **Labels.** One sentence about a stretch of the record, resting on the ids of the messages it is about, in plain Markdown pages. A session writes them as the work goes, and labels can be stacked into fewer.
- **The frame.** At a cut, where the home carries one: about 9,000 characters made from the store and never more than 9,500, with the standing lines, where the work stands, a few of the person's own words, and the door's tools.
- **A gentle wake.** A short note to the session that comes through a cut. It says which cut of the session this is, and asks for no inventory, no numbers of its own and no report.
- **The count.** What the summary held of each voice word for word, counted by script and written to a page beside the labels.
- **The person's own hand.** A switch for each project, a way to speak off the record, and a strike that takes a message, a label or a whole session out of the archive, the label pages and the home's small files.

---

### How it works

Crossings is a set of hooks, a hooks module and a small server. The hooks read the session's transcript into the home's archive (`said/`), from where the last reading stopped. The server answers the door's tools from the same home. The module answers a cut itself where the home asks it to, gives the person the `/crossings` command, and refuses a session's calls that open the archive's own files or write the files the door alone writes, the label pages among them. An index (`store.db`) is made from the plain files for searching, and may be deleted at any time.

| Event | Crossings |
| --- | --- |
| a session starts | marks it as one the plugin is loaded in; welcomes it once where the home holds no label; brings the frame to a new session where the home asks for it |
| a door tool is called | brings the archive up to the moment before it answers |
| a label is marked or a line left | keeps which model wrote it; shows the person a label that speaks for them or is a standing line, and every line left at the door |
| a cut | counts it, brings the archive up to date, renews the second copy where one is set, and carries the frame where the home asks for it |
| the session after a cut starts | a short waking note, and the frame as context where the home carries it so |
| a session ends | reads its transcript whole into the archive, and renews the second copy where `CROSSING_WAIT` is `1` |

A label is never made by itself: a session writes it, and the welcome and the door's own description of `mark` say so. A label holds what the person tells and asks, and where the work stands; it is never a record of how they seem, of what works on them or of how to move them. Why: a label crosses every cut as standing, and the session that reads it acts on it. The same tool, used to keep what lands on someone, would be a tool for the harm it is meant to spare.

The door is the way back. After a cut, the waking note tells a session that meets something it does not hold to look for it with `find`, read it in its place with `thread`, and give the message back as it was said, by its id. `leave` writes a line for the session that wakes after the next cut, and the frame carries the newest one at its top.

[The store](docs/store.md) has every file of a home. [The door](docs/door.md) has the tools, the command and what a session is told. [Cuts](docs/cuts.md) has the count, the frame's modes and the hand-over. [Layers](docs/layers.md) has what changes when more than one model works in a home.

---

### Install

Needs: Claude Code with hooks modules, and a `python3` on the path. Everything in the plugin is Python's standard library, so nothing has to be installed beside Python: SQLite, which the plugin searches with, comes inside it. The search needs SQLite's full-text search, FTS5, which is in the Python that ships with macOS and in most others. To check yours:

```sh
python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('create virtual table t using fts5(x)')"
```

No output means it is there. The second copy needs macOS (`hdiutil` and the Keychain).

There is no marketplace entry. Load the plugin from a folder:

```sh
claude --plugin-dir <a copy of this folder>
```

Installing it keeps nothing of what is said. Every session it is loaded in is marked by an empty file in `~/.claude/crossing/live/`, which a status line of your own can read, and the plugin's data folder keeps a log of its hook calls, of sizes and names alone; nothing else is written until a project is switched on.

---

### Switch it on

Crossings keeps nothing for a project until the person switches it on there. The switch is kept in a file of the person's own, `~/.claude/crossing/switched`, outside every project, so a `crossings/` folder that a repository ships switches nothing on.

| Command | Does |
| --- | --- |
| `/crossings on` | switches the project on: makes its home where it has none, and keeps the line in the person's record |
| `/crossings adopt` | switches on a home that already holds files this computer has no record of switching on |
| `/crossings off` | speaks off the record: nothing either voice says from now until it is switched on again is kept |
| `/crossings` | turns the switch over |
| `/crossings status`, `look`, `find <words>`, `labels`, `frame` | show what the store holds |

A project with a `crossings/` folder keeps its home there, where it can be read beside the work; a `crossings` that is a link is refused, in a sentence that names where it leads. Any other project gets a home outside it, under `~/.claude/crossing/homes/`, set to carry the frame as context. Where the home lies inside a repository and has no `.gitignore`, switching on writes one that keeps everything out of the repository but the label pages and the pages of the cuts.

The answer is a sentence, such as "Crossings is on for this project.", or a few where there is more to say. A home that came with the repository and already holds something is not switched on by `/crossings on`: it says how many messages and labels the home holds and where, `adopt` takes it, and removing the folder first starts clean. [Privacy](docs/privacy.md) has every case of the switch, and [The door](docs/door.md) has what the session running at that moment is told.

Under the turn, the person is shown one line when a label that speaks for them, or a standing line, is marked through the door; when a line is left at the door; when a frame crosses; and when a cut's summary mostly retells the one before. A label that came into the pages by no mark through the door is named once by the person's next `status`. The session is not handed these lines, and none of them blocks anything.

Switching on in a running session takes that session in from its first message, not from the moment of the switch. An earlier session is brought in by the person, one transcript at a time, from their own terminal, and nothing takes earlier sessions in by itself:

```sh
python3 crossing/door.py build --transcript <the session's transcript file> --cwd <the project>
```

Off is not a pause. While it is off, no cut is counted, noted or answered, nothing is archived, and the door still reads what was kept before while its `mark` and `leave` refuse. Switched on again, nothing said meanwhile is taken in, by any reading of any transcript. The harness's own transcript still holds it.

---

### What it keeps private and what it cannot keep out

- Nothing leaves the computer by the plugin's own doing: it opens no connection, and a second copy goes only to a folder the person names.
- Every folder Crossings makes is its owner's alone (0700), and every file it writes too (0600).
- A message of the person's that looks like it holds a key or a password is kept like any other, and its id is noted for the person to strike. The frame never quotes it. The session's own messages are not checked.
- Striking is the person's, from their terminal. The one other way anything is struck is a mark that writes a misaligned stack again, which strikes that stack: never a message, and, for a session's mark, never a stack of the person's. No strike reaches the harness's own transcript, an earlier second copy or a backup, or the history of a repository that holds the home, and the pages of the cuts keep the ids.
- A second copy, where the home names a folder for one, is one encrypted disk image, its passphrase in the Keychain.
- The guards against a session are checks, not walls: the terminal check on the person's verbs, the plugin's own flag, and the hooks module's string checks on a call's input. A session with a shell the person lets run commands can do what the person can. The wall is the person's own approval of what a project may set and what a session may run.

[Privacy](docs/privacy.md) has each of these in full. Every setting is in [Settings](docs/settings.md).

The licence is for the code. What a store holds is its person's alone.

---

### Develop

The tests write their own transcripts and use temporary homes alone; they need no network and no model. Run each file on its own, or all of them with pytest:

```sh
python3 tests/test_store.py
python3 tests/test_off.py
claude plugin test .
sh scripts/coverage.sh
claude plugin validate .
```

`claude plugin test .` runs the hooks module's tests in the engine's own runner. `scripts/coverage.sh` measures branch coverage of `crossing/`, the hooks' own processes included, in a virtual environment of its own under `tests/.work/` (it needs `uv`, and installs `coverage` there); the floor is 99 (`.coveragerc`) and the aim is 100. `python3 crossing/door.py --help` lists the door's verbs.

The plugin is developed in one folder and loaded from a copy of it, so a session never writes into the folder its own hooks are loaded from. The copy is brought up to date only after the tests and validation pass. The door's server is one long-lived process a session: a new version is picked up when it is reconnected, or in a new session. [AGENTS.md](AGENTS.md) is the guide for working on the code.

---

[The store](docs/store.md) · [The door](docs/door.md) · [Privacy](docs/privacy.md) · [Cuts](docs/cuts.md) · [Layers](docs/layers.md) · [Settings](docs/settings.md) · [Repository guide](AGENTS.md) · [Apache-2.0](LICENSE) · [Notices](NOTICE)
