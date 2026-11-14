"""The store: what was said, kept in plain files, and a database made from them that can be searched.

Three things live in a home (a project's `crossings/` folder; or, for a project that has none,
a folder outside it; or the one on this computer that is the person's and the session's):

  said/<session>.jsonl   the archive: every message of either voice, word for word, under its id.
                         The harness deletes transcripts after a month by default, so this is the
                         record that is kept.
  hand-over.md, labels/  the label pages: one sentence about a stretch, and the ids it rests on,
                         which are messages or, for a stack, other labels of its kind.
  models.txt             which model wrote a label, by its key and its sentence's digest, beside
                         the pages so that they read as they always did. A message of the session's
                         keeps the model that said it in its own line of the archive.
  there.txt, calling.txt which model a session runs now, and which model is behind a call of the
                         door's server: see crossing/layer.py. Neither says who wrote a line.
  markers.jsonl          how far each transcript was read, so that the next archive reads only what
                         was added to it since.
  unattended.txt         the ids of what sessions no person sat in held, by the hooks of those
                         sessions: never archived, from their own transcript or from any other.
  struck.txt             what was struck, by id; a session's strike adds the whole id of each message
                         it took. Every build obeys it, so nothing struck comes back.
  flagged.txt            the ids of messages of the person's that look like they hold a key or a
                         password, by id alone: the person's `status` and `look` say so until each
                         is struck. The message itself is kept: the archive keeps what was said.
  archive.lock           held by one archive, mark, strike, layering or switch at a time, from what
                         it reads to the last file it writes.
  labelled.txt,          every label the home has met, by key and digest; and those a build found that
  arrived.txt            came by no mark through the door, for the person's next `status`.
  collided.txt           ids of eight characters that two messages share, for the person's next `status`.
  off.txt                when the person's switch was off: a line a span, its two moments in UTC.
                         Nothing said inside a span is archived, from any transcript (see crossing/off.py).
  reached.jsonl          what was pulled through the door, one line a pull: when, how, which ids.
  store.db               SQLite, made from the files above and from nothing else. It may be deleted
                         at any time; `build` makes it again, and with it which label stands beneath
                         which and the state each is in. What an archive keeps is added to it where
                         nothing else changed since it was made (see `refresh`).

No model is called anywhere here. Only what the person wrote and what the session answered is
ever read from a transcript, through the same reader as the rest of the plugin.
"""

from __future__ import annotations

import contextlib
import datetime
import difflib
import hashlib
import json
import os
import re
import secrets
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows: the lock is a file made only where none is there (see `_locked`)
    fcntl = None

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import off, record, transcript  # noqa: E402
from crossing.handover import named  # noqa: E402
from crossing.record import Linked, within  # noqa: E402,F401  (every file of a home is reached through `within`)

HIS, OWN, PASTED = "his", "session", "pasted"
# A label's key says its kind: R a standing line about the two of them, W about the work, N a
# line the session left at the door for the one who wakes after the next cut.
KINDS = {"R": "relation", "W": "work", "N": "next"}
LETTER = {kind: letter for letter, kind in KINDS.items()}
ROW = re.compile(r"^\|\s*([RWN]\d+)\s*\|\s*(.+?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*$")
KEY = re.compile(r"[RWN]\d+")
# A label may rest on other labels of its kind, which makes it a stack and them the lines beneath
# it. A stack's row names each line by its key and six characters of the digest of the line's
# sentence as it stood when the stack was marked: `R13@1a2b3c`. Six, because a message's id has
# eight, so that neither is ever read as the other.
BENEATH = re.compile(r"\b([RW]\d+)@([0-9a-f]{6})\b")
# What a build finds each label to be. Carried: it stands by itself, or is the top of a stack.
# Cooled: it stands beneath a stack that is sound, which is carried in its place. Misaligned: a
# stack with a line beneath it gone, or changed since the stack was marked, so that it no longer
# stands for its lines. Unresolved: it rests on a message the archive does not hold, or on nothing.
STATES = ("carried", "cooled", "misaligned", "unresolved")
# A pasted text's id, as an anchor is written: its message's id and a number, between backticks.
PASTED_ID = re.compile(r"`([0-9a-f]{8}\+\d+)`")
MADE = 4  # the make of the database: one of another make is built again before it is read
# Which model wrote a label is kept beside the pages, not in them, so that every page reads as it did.
MODELS = "models.txt"
SIGNED = re.compile(r"^([RWN]\d+)@([0-9a-f]{6})\s+(\S+)$")
LINE_TO_ID = re.compile(r"^\|\s*(\d{3,})\s*\|\s*`([0-9a-f]{8})`\s*\|")
# Word stems, so that "paint" finds "painted".
TOKENS = "porter unicode61 remove_diacritics 2"
TERM = re.compile(r'"([^"]*)"|(\w+\*?)')  # a phrase in quotes, or a word, which a * may end
NEAR = 500  # characters of a neighbour shown in a thread
AROUND = 50  # messages before and after the one a thread is about, at most
TRIED = 5  # words of a miss whose nearest words are looked for: the answer names five at most
WHOLE = 6000  # characters of the message a thread is about


def place(cwd: Path) -> tuple[Path, Path | None]:
    """The home of the project `cwd` stands in, with the project's folder where the home lies
    outside it (see record.place); or the folder CROSSING_HOME names, for a harness that has
    no project of its own to be found. A home named outright is believed, as any other, only
    where the person's record names it for this project (see `kept`).

    Where the record names a home outside the project and a `crossings/` folder the record does
    not name now stands in the project (one a repository brought since), the home outside is
    still the project's: a folder that arrived is not let hide the one the person switched on
    (see `passed_over`)."""
    named = os.environ.get("CROSSING_HOME")
    if named:
        return Path(named), None
    folder, top, out = record.located(cwd)
    if not out and not believed(top, folder):
        away = record.outside(top)
        if away.is_dir() and believed(top, away):
            return away, top
    return folder, top if out else None


def spelled(path: Path) -> str:
    """A folder as the person's record names it: resolved, and spelled as the disk spells it (see
    record.spelled), so that one folder is named one way by whichever spelling it was reached."""
    return str(record.spelled(path.resolve()))


def believed(top: Path, folder: Path) -> bool:
    """Whether the person's record names this home for the project whose top this is: by the same
    text, or, for a line written with another spelling of the same folders, by the files themselves
    (os.path.samefile). A home that is no longer there is named by no line."""
    held = consented()
    if (str(top), spelled(folder)) in held:
        return True
    return any(record._same(Path(project), top) and record._same(Path(home_), folder) for project, home_ in held)


def linked(cwd: Path) -> Path | None:
    """The project's own `crossings` where it is a link, to a folder or to nothing: found as the
    project's home (see record.located), and neither believed nor switched on, so that nothing is
    kept, read or located through it. A home named outright (CROSSING_HOME) is not asked about."""
    if os.environ.get("CROSSING_HOME"):
        return None
    folder, _, out = record.located(cwd)
    return folder if not out and folder.is_symlink() else None


def passed_over(cwd: Path) -> Path | None:
    """The `crossings/` folder in the project `cwd` stands in that was passed over because the
    person's record names a home outside the project (see `place`); or nothing."""
    if os.environ.get("CROSSING_HOME"):
        return None
    folder, _, out = record.located(cwd)
    return folder if not out and place(cwd)[0] != folder else None


PASSED = "passed-over.txt"  # the `crossings/` folders the person was told were passed over, by who told them
PASSING = (
    "A crossings/ folder in this project was passed over: Crossings goes on keeping this project's home "
    "where you switched it on, outside the project."
)


def passed_note(cwd: Path, folder: Path, by: str) -> str | None:
    """Where a `crossings/` folder in the project was passed over for the home the person switched
    on outside it (see `passed_over`): the sentence that says so, once for each of the hooks and
    `status` (`by`), kept in the home's `passed-over.txt`; or nothing."""
    found = passed_over(cwd)
    return PASSING if found is not None and once(folder, PASSED, f"{by} {found.resolve()}") else None


def here(cwd: Path) -> Path:
    """Where the home of the project `cwd` stands in lies, believed or not: see `kept`, which is
    how the hooks, the door and its server come to a project's home."""
    return place(cwd)[0]


def switched() -> Path:
    """The person's own record of the projects they switched Crossing on in: a file in their
    own folder, outside every project, so that no repository can hold it. CROSSING_SWITCHED
    names another, for a test."""
    return Path(os.environ.get("CROSSING_SWITCHED") or record.own() / ".claude" / "crossing" / "switched")


def _record_objects() -> list[dict]:
    """The lines of the person's record that are objects, in its order. A line that is not one
    is passed over."""
    try:
        lines = record.lines_in(switched())
    except OSError:
        return []
    found = []
    for line in lines:
        try:
            given = json.loads(line)
        except ValueError:
            continue
        if isinstance(given, dict) and isinstance(given.get("home"), str):
            found.append(given)
    return found


def _record_lines() -> list[dict]:
    """The lines of the person's record that switch a project on: a project's top and its home."""
    return [given for given in _record_objects() if isinstance(given.get("project"), str)]


def consented() -> set[tuple[str, str]]:
    """Each line of the record, as the resolved path of a project's top and of its home. A line
    that is not one is passed over."""
    return {(given["project"], given["home"]) for given in _record_lines()}


def consent(cwd: Path) -> None:
    """Keep in the person's record that they switched Crossing on in the project `cwd` stands
    in, for the home it has (see `place`: a home named outright by CROSSING_HOME too). `switch
    on` is the one act that calls this."""
    folder, _ = place(cwd)
    top = record.located(cwd)[1]
    with _recording():
        if believed(top, folder):
            return
        with open(switched(), "a", encoding="utf-8") as handle:
            handle.write(json.dumps({"project": str(top), "home": spelled(folder)}, ensure_ascii=False) + "\n")


@contextlib.contextmanager
def _recording():
    """The person's record of switches, held by one writer at a time: a line `consent` appends
    and the record `_spans_kept` writes whole would otherwise be read and written at once, and
    the one line lost. The lock is a file beside the record (`switched.lock`); one not had within
    WAIT seconds is said as an OSError, which the switch says to the person."""
    switched().parent.mkdir(parents=True, exist_ok=True)
    held = _held_at(switched().with_name(switched().name + ".lock"))
    if held is None:
        raise OSError(f"the person's record of switches was held by another switch for {WAIT:.0f} seconds")
    try:
        yield
    finally:
        _let_go(switched().with_name(switched().name + ".lock"), held)


# The person's record also keeps, for a home that has a record of when Crossing was off, how many
# lines that record had when the switch last wrote it: a line {"home": ..., "spans": N} beside the
# project's own, which names no project and so switches nothing on. A spans file that is then
# missing or shorter was taken away or cut by something other than the switch (a session, a
# checkout or a clean of a home inside a repository), and what it said can no longer be told:
# nothing is archived for that home until the person switches it on. So too where a line of it
# is damaged, so that it is no span: what that line held can no longer be told either.


def spanned(folder: Path) -> int:
    """How many lines the home's record of when Crossing was off had when the switch last wrote
    it, as the person's record keeps it; nought where it keeps none."""
    found = _spans_line(folder)
    count = found.get("spans")
    return count if type(count) is int and count >= 0 else 0


def _spans_line(folder: Path) -> dict:
    """The person's record's last line of counts for this home (see `spanned`), or nothing: named
    by its folder as the record names it, or by another spelling of the same folder."""
    home = spelled(folder)
    lines = [
        given
        for given in _record_objects()
        if "spans" in given and (given["home"] == home or record._same(Path(given["home"]), folder))
    ]
    return lines[-1] if lines else {}


def steadied(folder: Path) -> float | None:
    """The steady clock's reading (see off.steady) as the switch kept it in the person's record when
    it last switched this home off; nothing where none was kept."""
    found = _spans_line(folder).get("steady")
    return float(found) if type(found) in (int, float) else None


def _spans_kept(folder: Path, steady: float | None = None) -> None:
    """Keep in the person's record how many lines the home's record of when Crossing was off has
    now, and, as the switch turns it off, the steady clock's reading at that moment (`steady`, see
    off.closed). The switch calls this once it has written that file, and once the project's own
    line is in the record. The record is written whole beside itself and put in its place, under
    its lock (see `_recording`); its other lines stay as they are."""
    home = spelled(folder)
    count = len(lines_of(within(folder, off.FILE).read_text(encoding="utf-8", errors="surrogateescape")))
    with _recording():
        kept = []
        for line in lines_of(switched().read_text(encoding="utf-8", errors="surrogateescape")):
            try:
                given = json.loads(line)
            except ValueError:
                given = None
            if not (
                isinstance(given, dict)
                and isinstance(given.get("home"), str)
                and "spans" in given
                and "project" not in given
                and (given["home"] == home or record._same(Path(given["home"]), folder))
            ):
                kept.append(line)  # all but the count written before this one
        kept.append(
            json.dumps(
                {"home": home, "spans": count, **({"steady": steady} if steady is not None else {})}, ensure_ascii=False
            )
        )
        fresh = switched().with_name(switched().name + ".new")
        fresh.write_text("".join(line + "\n" for line in kept), encoding="utf-8", errors="surrogateescape")
        os.replace(fresh, switched())


def lost(folder: Path) -> bool:
    """Whether what the home's record of when Crossing was off held can no longer be told: it is
    missing, or shorter than it was when the switch last wrote it (see `spanned`), or it holds a
    line that is no span since the switch last kept everything before that moment off (see
    off.untold). Nothing is then archived for it, until the person switches Crossing on again. A
    record that is there and cannot be read is said by its own rule (see `archive`)."""
    was = spanned(folder)
    try:
        lines = lines_of(within(folder, off.FILE).read_text(encoding="utf-8", errors="surrogateescape"))
    except FileNotFoundError:
        return bool(was)
    except OSError:
        return False
    return len(lines) < was or off.untold(lines)


def kept(cwd: Path) -> Path | None:
    """The home of the project `cwd` stands in, where the person switched Crossing on there; or
    nothing. A home is believed only where the person's record names it for this project: a
    folder a repository ships, or one put in a home's place since, is no home, and the project is
    one where Crossing was never switched on. A project's own `crossings` that is a link is no
    home either, wherever it leads and whatever the record names (see `linked`). A home named
    outright (CROSSING_HOME) is believed by the same rule: only where the record holds a line for
    this project that names it, which `switch on` writes while that setting stands. Another
    project's home, whose name can be told from its path, is not opened by naming it."""
    if record.astray(cwd):  # a setting that names a place inside the project is not followed
        return None
    folder, _ = place(cwd)
    if folder.is_symlink() and folder == linked(cwd):  # a project's crossings that is a link is no home
        return None
    top = record.located(cwd)[1]
    return folder if folder.is_dir() and believed(top, folder) else None


def offered(cwd: Path) -> Path | None:
    """The home on this computer (see `ours`), as the project `cwd` stands in may reach it: only
    where the person switched Crossing on there and its switch is on. Any other project is one
    where Crossing was never switched on, and the home that is the whole computer's is no more
    open to it than its own."""
    folder = kept(cwd)
    return ours() if folder is not None and active(folder) else None


def ours() -> Path:
    """The home on this computer that belongs to the person and the session, reached only from a
    project where Crossing is switched on and on (see `offered`)."""
    return Path(os.environ.get("CROSSING_OURS") or record.own() / ".claude" / "crossing" / "ours")


def home(cwd: Path, which: str = "here") -> Path:
    return ours() if which == "ours" else here(cwd)


# --- the person's switch --------------------------------------------------------------------


def word(folder: Path, name: str) -> str:
    """One of a home's plain files of one word (`switch`, `mode`, `carry`)."""
    try:
        return "\n".join(record.lines_in(within(folder, name))).strip().lower()
    except OSError:
        return ""


def active(folder: Path) -> bool:
    """Whether Crossing keeps anything in this home: the folder is there, and its switch does
    not say off. A project whose home was never made is one where Crossing was never switched
    on; nothing is kept for it, and no folder is made by looking."""
    return folder.is_dir() and word(folder, "switch") != "off"


SETTINGS = ("mode", "carry", "frame-size", "copy")  # the setting files `unclaimed` names by name


def unclaimed(cwd: Path) -> dict | None:
    """Where the home of the project `cwd` stands in is there already, holds any file but a
    `.gitignore`, and the person's record has no line for it: a `crossings/` folder that came with
    a repository, or a home made by hand. What it holds, and where; or nothing. Beside its messages
    and labels: whether it holds an index (`store.db`), a hand-over page, which setting files of
    SETTINGS, whether `models.txt`, and how many other files. A home named outright
    (CROSSING_HOME) is asked about as any other."""
    folder, _ = place(cwd)
    top = record.located(cwd)[1]
    if not folder.is_dir() or believed(top, folder):
        return None
    record.sound(folder)
    files = [path.relative_to(folder).as_posix() for path in folder.rglob("*") if path.is_file()]
    files = [name for name in files if name != ".gitignore"]
    if not files:
        return None
    named = {"store.db", "hand-over.md", MODELS, *SETTINGS}
    held = {
        "folder": folder,
        "messages": len(_archived(folder)),
        "labels": len(labels(folder)),
        "index": "store.db" in files,
        "page": "hand-over.md" in files,
        "settings": [name for name in SETTINGS if name in files],
        "models": MODELS in files,
    }
    kept = {f"said/{page.name}" for page in said_pages(folder)} | {
        f"labels/{page.name}" for page in pages(folder) if page.parent.name == "labels"
    }
    held["others"] = sum(1 for name in files if name not in named and name not in kept)
    return held


def switch(cwd: Path, to: str) -> str:
    """Turn the person's switch for the project `cwd` stands in: `on`, `off`, or `toggle` to
    turn it over; or `adopt`, which switches on a home that holds what this computer has no
    record of switching on. Gives how it now stands: on, off, or never, where a project the
    person never switched on was to be switched off, which changes nothing and writes nothing;
    `unclaimed`, where switching on was asked of such a home (see `unclaimed`), which is then
    not switched on, and nothing is written; or `astray`, where a setting names a place inside
    the project (see record.astray), and nothing is written either; or `linked`, where switching
    on was asked and the project's own `crossings` is a link (see `linked`): nothing is written,
    in it, where it leads, or outside the project.

    Switching on is the one act that makes a home, and the one that keeps in the person's
    record (see `switched`) that this project's home is believed. A project with a `crossings/`
    folder has one already, and a home made earlier is there: either is only switched, and
    nothing else in it is changed. Any other project gets one outside it, set to cut beside the
    harness's summary and to carry the frame as a note, with a plain file `project` that holds
    the path of the project it belongs to, so that a person can tell the homes apart.

    Switching off keeps the line in the record and turns the home's own switch, and keeps the
    moment in the home's `off.txt`: a span opens, which switching on again closes (see
    crossing/off.py). Nothing said inside a span is ever archived. The span is opened before the
    switch is turned off, and closed only after it is turned on: an act cut short between the
    two leaves the span the wider. Switching on gives `again` where it closed a span. Switching
    off also keeps the steady clock's reading in the person's record, so that what was said while
    it was off is kept off where the clock was set back meanwhile (see off.closed).

    The person's record keeps how many lines `off.txt` has each time the switch writes it (see
    `lost`). Where that file is since missing or shorter, or holds a line that is no span (see
    off.untold), switching on keeps everything before this moment as off the record, by a span
    from the first moment there is to now, and archiving goes on from here; it gives `restored`.

    Where the home lies inside a repository and holds no ignore file, switching on writes one
    (see `ignored`)."""
    if record.astray(cwd):
        return "astray"
    folder, project = place(cwd)
    believed = kept(cwd) is not None
    on = to in ("on", "adopt") or (to == "toggle" and not (believed and active(folder)))
    if not on and not believed:
        return "never"
    if on and folder.is_symlink() and folder == linked(cwd):
        return "linked"  # nothing is located, made or switched on through it
    record.sound(folder)  # nothing is switched in a home with a link in it
    adopted = on and unclaimed(cwd) is not None
    if adopted and to != "adopt":
        return "unclaimed"  # content someone else made is not trusted with no word said
    if not folder.is_dir():
        folder.mkdir(parents=True, exist_ok=True)  # two sessions may switch one project on at the same moment
        within(folder, "mode").write_text("beside\n", encoding="utf-8")
        within(folder, "carry").write_text("note\n", encoding="utf-8")
        if project is not None:
            within(folder, "project").write_text(f"{project}\n", encoding="utf-8")
    # The span and the switch file are written with the home's lock held, as an archive reads them
    # (see `archive`): an archive under way as the switch turns has read the spans as they now stand.
    # One lock order for every act: the home's lock first, then the person's record's (`_recording`,
    # which `consent` and `_spans_kept` take within it); nothing takes them the other way about.
    held = _locked(folder)
    if held is None:
        raise OSError(f"the home was held by another act for {WAIT:.0f} seconds")
    try:
        return _switched(cwd, folder, on, adopted)
    finally:
        _unlocked(folder, held)


def _switched(cwd: Path, folder: Path, on: bool, adopted: bool = False) -> str:
    """`switch`, from its span on, with the home's lock held. A home `adopted` has met no line of
    its `models.txt`: none of them was signed through the door (see `_signs_unmet`)."""
    if adopted:
        _signs_unmet(folder)
    if not on:
        reached = _reached_now(folder)  # where each transcript the archive knows stands, before the span opens
        if off.opened(folder) or not within(folder, PLACES).exists():  # from this moment nothing said is kept
            _places_kept(folder, reached)
        _spans_kept(folder, steady=off.steady())
    within(folder, "switch").write_text("on\n" if on else "off\n", encoding="utf-8")
    if not on:
        return "off"
    consent(cwd)
    ignored(folder)
    was_lost = lost(folder)  # a home adopted with a damaged record is restored as it is switched on, too
    closed = off.closed(folder, since=steadied(folder))
    _unsaid_by_place(folder)  # what the transcripts it knew gained meanwhile is off, by its place, whatever its time
    if was_lost:
        off.everything_before(folder)  # what the missing record may have held is kept off, all of it
    if closed or was_lost or within(folder, off.FILE).exists():
        _spans_kept(folder)
    if within(folder, "store.db").exists():  # whatever index the folder held, it is made anew from the plain files
        if searchable():
            build(folder)
        else:  # it cannot be made here, and one that came from elsewhere is not read: it goes, as it may at any time
            within(folder, "store.db").unlink()
    return "restored" if was_lost else "again" if closed else "on"


# Where each transcript the archive knows stood as the switch was turned off: one line a transcript,
# by its resolved path as its marker names it, the byte just after its last whole line then and the
# digest of the bytes before it (as `markers`). Switching on again keeps off, by id in unsaid.txt,
# every row those transcripts gained between that place and the place they stand at then, whatever
# time a row bears: a clock set forward and back while it was off moves no row out of the span. A
# transcript the archive never met is judged by its rows' times alone (see off.judged).
PLACES = "off-places.jsonl"


def _reached(path: Path) -> int | None:
    """The byte just after the last whole line of a transcript as it stands; nothing where it
    cannot be read."""
    try:
        with open(path, "rb") as handle:
            end = os.fstat(handle.fileno()).st_size
            while end > 0:
                start = max(0, end - 65536)
                handle.seek(start)
                at = handle.read(end - start).rfind(b"\n")
                if at >= 0:
                    return start + at + 1
                end = start
            return 0
    except OSError:
        return None


def _reached_now(folder: Path) -> dict[str, dict]:
    """Where each transcript the home's markers name stands now (see PLACES), by its path."""
    found = {}
    for key in markers(folder):
        name = key[: -len("#unattended")] if key.endswith("#unattended") else key  # a session no person sat in
        try:
            with open(name, "rb") as handle:
                at = _reached(Path(name))
                if at is not None:
                    found[name] = {"offset": at, "check": _check(handle, at)}
        except OSError:  # a transcript that is gone: nothing more is said in it
            continue
    return found


def _places_kept(folder: Path, reached: dict[str, dict]) -> None:
    """Keep PLACES whole, written beside itself and put in its place; where the archive knows no
    transcript, no file is made."""
    if not reached:
        return
    fresh = within(folder, PLACES + ".new")
    fresh.write_text(
        "".join(json.dumps({"path": name, **at}, ensure_ascii=False) + "\n" for name, at in reached.items()),
        encoding="utf-8",
    )
    os.replace(fresh, within(folder, PLACES))


def _places(folder: Path) -> dict[str, dict]:
    """The places PLACES keeps, by path. A line that is not one is passed over."""
    try:
        lines = record.lines_in(within(folder, PLACES))
    except OSError:
        return {}
    found = {}
    for line in lines:
        try:
            at = json.loads(line)
        except ValueError:
            continue
        if (
            isinstance(at, dict)
            and isinstance(at.get("path"), str)
            and type(at.get("offset")) is int
            and at["offset"] >= 0
            and isinstance(at.get("check"), str)
        ):
            found[at["path"]] = {"offset": at["offset"], "check": at["check"]}
    return found


def _unsaid_by_place(folder: Path) -> None:
    """As the switch turns on: keep in unsaid.txt the id of every message, of either voice, that a
    transcript PLACES names gained since the switch was turned off, up to its last whole line now;
    then PLACES goes. A transcript that is shorter now, or whose bytes before its place are not
    those that were there, is another one, and its rows are judged by their times alone."""
    ids = []
    for name, at in _places(folder).items():
        path, end = Path(name), _reached(Path(name))
        try:
            if end is None or end < at["offset"]:
                continue
            with open(path, "rb") as handle:
                if _check(handle, at["offset"]) != at["check"]:
                    continue
            for offset, row in transcript.appended(path, at["offset"]):
                if offset > end:
                    break
                uuid = str(row.get("uuid") or "") if row is not None else ""
                if record.nameable(uuid) and (
                    transcript.person(row, whole=True) or transcript.session(row, whole=True)
                ):
                    ids.append(uuid)
        except OSError:  # gone since: its rows are judged by their times alone
            continue
    off.keep_unsaid(folder, ids)
    try:
        within(folder, PLACES).unlink()
    except FileNotFoundError:
        pass


# What a home inside a repository is given as its ignore file, where it has none: everything in it
# is ignored but the label pages, the pages of the cuts and the file itself, which the person may
# want read beside the work. The words in said/, the database and every small file of ids, spans,
# markers, signatures and flags stay out of the repository.
IGNORE = """# Written by Crossings as it was switched on: what was said stays out of the repository.
# Only the label pages, the pages of the cuts and this file may be kept beside the work.
*
!.gitignore
!hand-over.md
!labels/
!labels/*.md
!*-cut-*.md
"""
IGNORED_TOLD = "ignore-told.txt"  # that `status` said, once, that an ignore file there leaves said/ in


def repository(folder: Path) -> Path | None:
    """The top of the repository a folder lies in (one that holds `.git`), looked for upward from
    it and no further than the person's own folder; or nothing."""
    house = record.own().resolve()
    for each in (folder.resolve(), *folder.resolve().parents):
        if (each / ".git").exists():
            return each
        if each == house:
            break
    return None


def ignored(folder: Path) -> bool:
    """Write the home's ignore file (IGNORE) where the home lies inside a repository and has none.
    An ignore file that is there is left as it is. Gives whether one was written."""
    path = within(folder, ".gitignore")
    if path.exists() or repository(folder) is None:
        return False
    path.write_text(IGNORE, encoding="utf-8")
    return True


def leaves_said(folder: Path) -> bool:
    """Whether the home lies inside a repository and its ignore file, there already, does not
    cover `said/` by any plain line of its own (`*`, `said`, `said/`, `/said`, `/said/`, `said/*`
    or `/said/*`) with no later line that takes it back (`!said` and the like). A rule made of
    other patterns is not read, and is taken as not covering it."""
    path = within(folder, ".gitignore")
    if repository(folder) is None or not path.is_file():
        return False
    covered = False
    for line in lines_of(path.read_text(encoding="utf-8", errors="replace")):
        line = line.strip()
        bare = line.lstrip("!").rstrip("/").lstrip("/")
        if bare in ("*", "said", "said/*", "said/**", "**"):
            covered = not line.startswith("!")
    return not covered


# --- what was struck -------------------------------------------------------------------------


def struck(folder: Path) -> set[str]:
    """What struck.txt names: the token of each line, before any `#` and its reason. A line whose
    reason holds a byte that is no text still strikes its token; one whose token is no text is
    passed over, with a line in the log (see record.decoded)."""
    path = within(folder, "struck.txt")
    try:
        lines = lines_of(path.read_bytes().decode("utf-8", errors="surrogateescape"))
    except OSError:
        return set()
    found = set()
    for line in lines:
        token = line.split("#")[0].strip()
        try:
            token.encode("utf-8")
        except UnicodeEncodeError:
            record.passed(path)
            continue
        found |= {token} if token else set()
    return found


def _is_struck(row: dict, gone: set[str]) -> bool:
    return bool(gone) and (row["id"] in gone or row["uuid"] in gone or f"session:{row['session']}" in gone)


def kept_out_ids(folder: Path) -> set[str]:
    """The ids, by their first eight characters, of the messages this home keeps out of all it
    gives by id: struck, said while Crossing was off (`unsaid.txt`), and held by a session no
    person sat in (`unattended.txt`). A hand-over's words page that names one is not given."""
    named = struck(folder) | off.unsaid(folder) | unheld(folder)
    return {each[:8] for each in named if re.match(r"[0-9a-f]{8}(?![0-9a-f])", each)}


# --- the archive ------------------------------------------------------------------------------


def said_pages(folder: Path) -> list[Path]:
    """The archive's files, each one reached through `within`."""
    return [within(folder, "said", page.name) for page in sorted(within(folder, "said").glob("*.jsonl"))]


def _said(row) -> bool:
    """Whether a line of the archive is a message as the archive writes one: an object whose id,
    session, voice and text are strings, its voice one of the two, and its time and model, where
    it has them, strings too. Any other line is passed over wherever the archive is read."""
    if not isinstance(row, dict):
        return False
    get = row.get  # read once a message, for every message the archive holds: kept plain, as it is often run
    return (
        isinstance(get("uuid"), str)
        and isinstance(get("id"), str)
        and isinstance(get("session"), str)
        and isinstance(get("text"), str)
        and get("voice") in (HIS, OWN)
        and isinstance(get("at", ""), str)
        and isinstance(get("model", ""), str)
    )


def _kept(folder: Path, stood: dict | None = None) -> tuple[list[dict], int]:
    """Every message the archive holds, each with its line's number in its page; and how many
    lines of it are no message and were passed over (an empty line is not counted). Where
    `stood` is given, how each page stood as it was read goes into it (see `_since`)."""
    rows, unread = [], 0
    for page in said_pages(folder):
        with open(page, "rb") as handle:
            seen = os.fstat(handle.fileno())  # before it is read: a page changed after this is changed for the record
            data = handle.read()
        lines = record.decoded(data, page)  # a line that is no text is passed over, and costs that line alone
        if stood is not None:
            stood[f"said/{page.name}"] = (len(data), seen.st_mtime_ns, len(lines), _tail(data))
        more, passed = _read(lines)
        rows += more
        unread += passed
    return rows, unread


lines_of = record.lines_of  # a plain file's lines, broken at line feeds alone: the one rule, record's


def _read(lines: list[str], first: int = 0) -> tuple[list[dict], int]:
    """The messages among these lines of a page, each with its line's number, the first being
    `first`; and how many of the lines are no message (an empty line is not counted)."""
    rows, unread = [], 0
    for n, line in enumerate(lines, first):
        try:
            row = json.loads(line)
        except ValueError:
            row = None
        if _said(row):
            rows.append({**row, "_n": n})
        elif line.strip():
            unread += 1
    return rows, unread


def _tail(data: bytes) -> str:
    """The digest of the last bytes of a page as it was read, up to CHECKED of them."""
    return hashlib.sha256(data[-CHECKED:]).hexdigest()


def _archived(folder: Path) -> list[dict]:
    return _kept(folder)[0]


def _ends_a_line(path: Path) -> bool:
    """Whether a file that is not empty ends with a line feed."""
    with open(path, "rb") as handle:
        handle.seek(-1, os.SEEK_END)
        return handle.read(1) == b"\n"


def _twinned(folder: Path, ids: list[str]) -> None:
    """Keep in COLLIDED the ids of eight characters that a message just archived shares with
    another the archive holds: each once, by id alone, for the person's next `status`."""
    there = set(collided(folder))
    new = [each for each in dict.fromkeys(ids) if each not in there and record.nameable(each)]
    if new:
        fresh = not within(folder, COLLIDED).exists()
        with open(within(folder, COLLIDED), "a", encoding="utf-8") as handle:
            if fresh:
                handle.write("# Ids of eight characters that two messages share, by id alone: status says them.\n")
            handle.write("".join(each + "\n" for each in new))


COLLIDED = "collided.txt"


def collided(folder: Path) -> list[str]:
    """The ids kept in COLLIDED, each once, in its order. A line that is no such id is passed over."""
    try:
        lines = record.lines_in(within(folder, COLLIDED))
    except OSError:
        return []
    return list(dict.fromkeys(line.strip() for line in lines if re.fullmatch(r"[0-9a-f]{8}", line.strip())))


def _text(path: Path) -> str:
    """A file of the home as it stands, for an act that writes it again: a byte that is no text is
    kept as it is (surrogateescape), and written back as it was read (see `_replaced`)."""
    return path.read_bytes().decode("utf-8", errors="surrogateescape")


def _whole(line: str) -> bool:
    """Whether a line read by `_text` is text throughout: no byte of it was kept as it was."""
    try:
        line.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _replaced(folder: Path, path: Path, text: str) -> None:
    """A file of the home written whole beside itself and then put in its place, so that no reader
    ever finds it half written and an act cut short leaves it as it was. Bytes that were no text
    are written back as they were read (see `_text`)."""
    fresh = within(folder, *path.relative_to(folder).parts[:-1], path.name + ".new")
    fresh.write_text(text, encoding="utf-8", errors="surrogateescape")
    os.replace(fresh, path)


# How far each transcript was read, so that the next archive reads only what was added since: a
# plain file of the home, one line a transcript, by its resolved path, as JSON.
MARKERS = "markers.jsonl"
CHECKED = 4096  # bytes before the marker whose digest says the file is still the one that was read


def markers(folder: Path) -> dict[str, dict]:
    """Each transcript's marker: the byte just after the last whole line read (`offset`), and the
    SHA-256 of the bytes before it, up to CHECKED of them (`check`). A line that is not one is
    passed over, and the transcript it was for is read from its first line again."""
    try:
        lines = record.lines_in(within(folder, MARKERS))
    except OSError:
        return {}
    found = {}
    for line in lines:
        try:
            mark = json.loads(line)
        except ValueError:
            continue
        if (
            isinstance(mark, dict)
            and isinstance(mark.get("path"), str)
            and type(mark.get("offset")) is int
            and mark["offset"] >= 0
            and isinstance(mark.get("check"), str)
        ):
            found[mark["path"]] = {"offset": mark["offset"], "check": mark["check"]}
            if isinstance(mark.get("at"), str) and mark["at"]:  # the time of the last row read that had one
                found[mark["path"]]["at"] = mark["at"]
    return found


def _check(handle, offset: int) -> str:
    """The digest of the bytes of an open transcript just before `offset`."""
    handle.seek(max(0, offset - CHECKED))
    return hashlib.sha256(handle.read(offset - max(0, offset - CHECKED))).hexdigest()


def _resume(path: Path, mark: dict | None) -> int:
    """Where to read a transcript from: its marker's offset, where the file is at least that long
    and the bytes before it are those that were read; otherwise its first byte."""
    if mark is None:
        return 0
    with open(path, "rb") as handle:
        if os.fstat(handle.fileno()).st_size < mark["offset"] or _check(handle, mark["offset"]) != mark["check"]:
            return 0
    return mark["offset"]


def _moved(folder: Path, key: str, path: Path, offset: int, at: str = "") -> None:
    """Keep the marker of the transcript at `path` at `offset`, with `at`, the time of the last
    row read that had one, where there was one (see off.last). The file is written whole beside
    itself and put in its place, so that a marker file is never left half written."""
    with open(path, "rb") as handle:
        check = _check(handle, offset)
    held = {**markers(folder), key: {"offset": offset, "check": check, **({"at": at} if at else {})}}
    folder.mkdir(parents=True, exist_ok=True)
    fresh = within(folder, MARKERS + ".new")
    fresh.write_text(
        "".join(json.dumps({"path": name, **mark}, ensure_ascii=False) + "\n" for name, mark in held.items()),
        encoding="utf-8",
    )
    os.replace(fresh, within(folder, MARKERS))


UNHELD = "unattended.txt"
# One archive at a time in a home: two at once (a door call's hook and a session's end) would each
# read what is held before the other appended, and keep a message twice. The lock is held from
# that read until the append and the marker's move are done; one that is not had within WAIT
# seconds does nothing this time, and the next reads on from its marker. Where there is no flock
# (Windows), the lock is a file made only where none is there, and one older than STALE seconds
# was left by a process that ended before it could remove it.
LOCK = "archive.lock"
WAIT = 5.0
STALE = 120.0


def _locked(folder: Path):
    """The home's lock, held; or nothing, where another process held it for WAIT seconds. Held by
    an archive, a mark, a strike, `layered` and the switch, each from what it reads to the last file
    it writes. It is taken before the person's record's lock (`_recording`), never after it."""
    return _held_at(within(folder, LOCK))


def _unlocked(folder: Path, held) -> None:
    _let_go(within(folder, LOCK), held)


def _held_at(path: Path):
    """A lock file, held (see LOCK); or nothing, where another process held it for WAIT seconds."""
    until = time.monotonic() + WAIT
    if fcntl is not None:
        handle = open(path, "a")
        while True:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return handle
            except OSError:
                if time.monotonic() >= until:
                    handle.close()
                    return None
                time.sleep(0.02)
    while True:
        try:
            return os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            if not _left(path):
                if time.monotonic() >= until:
                    return None
                time.sleep(0.02)


def _left(path: Path) -> bool:
    """Whether a lock file is no longer held: gone already, or older than STALE seconds, and then
    taken away."""
    try:
        if time.time() - path.stat().st_mtime <= STALE:
            return False
        path.unlink()
    except FileNotFoundError:
        pass
    return True


def _let_go(path: Path, held) -> None:
    if fcntl is not None:
        fcntl.flock(held.fileno(), fcntl.LOCK_UN)
        held.close()
    else:
        os.close(held)
        path.unlink()


# What a message of the person's may hold that is a key or a password. Few and specific, so that
# talk about passwords is not taken for one: the archive keeps the message all the same, and only
# its id is noted, for the person to strike it.
SECRETS = (
    re.compile(r"-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pos]_[A-Za-z0-9]{36,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82,}"),
    re.compile(r"(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"\bAuthorization:\s*Bearer\s+[A-Za-z0-9._~+/-]{8,}", re.I),
    re.compile(r"\b(?:password|passwd|api[_-]?key)\s*[:=]\s*[\"']?[^\s\"'`]{8,}", re.I),
)
FLAGGED = "flagged.txt"


def secret(text: str) -> bool:
    """Whether a text looks like it holds a key or a password (see SECRETS)."""
    return any(pattern.search(text) for pattern in SECRETS)


def flagged(folder: Path) -> list[str]:
    """The ids noted in `flagged.txt`, in its order, each once. A line that is no id is passed over."""
    try:
        lines = record.lines_in(within(folder, FLAGGED))
    except OSError:
        return []
    return list(dict.fromkeys(line.strip() for line in lines if re.fullmatch(r"[0-9a-f]{8}", line.strip())))


def unheld(folder: Path) -> set[str]:
    """The ids of the messages sessions no person sat in held, as their hooks kept them (see
    `unattended`). A line that is no id is passed over."""
    try:
        lines = record.lines_in(within(folder, UNHELD))
    except OSError:
        return set()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def unattended(path: Path, folder: Path) -> int:
    """Keep, by their ids alone, the messages the transcript at `path` holds, for a session no
    person sits in (see record.attended): what its prompts said is not the person's, and no
    archive takes it, from this transcript or from a fork or a resume that repeats it under the
    same ids. Nothing of what was said is written. The transcript is read from where the last
    such reading stopped, by a marker of its own. Gives how many ids were added."""
    key = str(path.resolve()) + "#unattended"
    stored = markers(folder).get(key)
    start = _resume(path, stored)
    listed: set[str] | None = None
    new, end = [], start
    for offset, row in transcript.appended(path, start):
        end = offset  # how far the reading got: the marker is moved there, after the loop
        uuid = str(row.get("uuid") or "") if row is not None else ""
        if not record.nameable(uuid) or not (transcript.person(row, whole=True) or transcript.session(row, whole=True)):
            continue  # an id that is no name is no line of the file, and is archived by no reading either
        if listed is None:
            listed = unheld(folder)
        if uuid not in listed:
            new.append(uuid)
            listed.add(uuid)
    if new:
        fresh = not within(folder, UNHELD).exists()
        with open(within(folder, UNHELD), "a", encoding="utf-8") as handle:
            if fresh:
                handle.write("# What sessions no person sat in held, by id: never archived.\n")
            handle.write("".join(uuid + "\n" for uuid in new))
    if end != start or (stored or {}).get("offset") != end:
        _moved(folder, key, path, end)
    return len(new)


def archive(path: Path, folder: Path, whole: bool = False, taken: bool = False) -> int:
    """Append to the archive what the transcript at `path` holds and the archive does not.

    A fork or a resume writes a new transcript that repeats earlier messages under the same
    ids; a message already archived, from any session, is not written twice.

    A transcript only grows, so it is read from where the last archive of it stopped (see
    `markers`), and only whole lines: one still being written is read the next time. `whole`
    reads it from its first line, as a session's end does, so that no message is passed over
    for good. What the archive holds is read only where the transcript gave a message to keep.

    A message a session no person sat in held is not archived (see `unattended`), unless the
    transcript was `taken`: handed to the door by its path, from a shell, by the person.

    Nothing said while the person's switch was off is archived, however the transcript comes:
    a message of either voice, and what was pasted in it, whose own time falls inside a span
    of the home's `off.txt` (see crossing/off.py), or which has no time and may have been said
    in one, is passed over, and the marker moves past it all the same. Where that file is there
    and cannot be read, nothing is archived and no marker moves. The ids of the rows a reading
    finds inside a span are kept in the home's `unsaid.txt` (see off.UNSAID), and no row whose id
    is there is ever archived, whether `off.txt` is there or not. Where the person's record says
    `off.txt` had more lines than it has now, or that it was there and it is gone (see `lost`),
    nothing is archived at all, until the person switches Crossing on again.

    The archive's page is named by the transcript's, as a session is: a name that cannot name a
    file is refused (record.ident). One archive at a time is made in a home (see `_locked`): one
    that cannot have the lock in time does nothing, with a line in the log.

    A message of the person's that looks like it holds a key or a password (see SECRETS) is kept
    as any other, and its id, and nothing of it, is noted in `flagged.txt`."""
    session = record.ident(path.stem[:8])
    folder.mkdir(parents=True, exist_ok=True)
    held = _locked(folder)
    if held is None:
        record.log(f"busy: another archive held {folder} for {WAIT:.0f} seconds, so {path.name} was not read this time")
        return 0
    try:
        # Read with the lock held, which the switch holds too (see `switch`): a span opened while an
        # archive is under way is opened before it reads them, or after it has appended.
        if lost(folder):  # what the record of the spans held cannot be told: nothing is kept
            return 0
        try:
            kept_off, _ = off.spans(folder)
        except OSError:
            return 0
        return _archive(path, folder, whole, taken, kept_off, session)
    finally:
        _unlocked(folder, held)


def its_time(row: dict) -> str:
    """A row's time as the archive keeps it: as the transcript wrote it, where it has the shape of a
    moment (off.SHAPE); else no time, as for a row that gives none."""
    at = row.get("timestamp")
    return at if isinstance(at, str) and off.SHAPE.fullmatch(at) else ""


def _archive(path: Path, folder: Path, whole: bool, taken: bool, kept_off: list, session: str) -> int:
    """`archive`, with the home's lock held."""
    key = str(path.resolve())
    stored = markers(folder).get(key)
    start = 0 if whole else _resume(path, stored)
    before = off.moment((stored or {}).get("at")) if start else None  # the last row with a time, before the marker
    known: set[str] | None = None  # the ids no person's session held, and those added this time
    holds, shares, index = None, None, None
    gone = struck(folder)
    unsaid = off.unsaid(folder)  # what a reading found said while the switch was off, spans file or no
    new, end, at, offs, twins = [], start, before, [], []
    try:
        for offset, row, its, inside in off.judged(transcript.appended(path, start), kept_off, before):
            end = offset  # how far the reading got: the marker is moved there, after the loop
            at = its or at
            uuid = str(row.get("uuid") or "") if row is not None else ""
            if not record.nameable(uuid) or uuid in unsaid:
                continue  # an id that is no name could be noted in no small file, and so is not kept at all
            his, own = transcript.person(row, whole=True), transcript.session(row, whole=True)
            if not (his or own):
                continue
            if inside:  # said while the person's switch was off: never kept; by its own time, its id is noted
                offs += [uuid] if its is not None else []  # one with no time may be decided again later
                continue
            if holds is None:
                holds, shares, index = _holding(folder)
                known = set() if taken else unheld(folder)
            if uuid in known or holds(uuid):
                continue
            said = {
                "uuid": uuid,
                "id": uuid[:8],
                "session": session,
                "voice": HIS if his else OWN,
                "at": its_time(row),
                "text": "\n\n".join(his or own),
            }
            if own and transcript.model(row):  # which model spoke; a row that names none keeps none
                said["model"] = transcript.model(row)
            if not _is_struck(said, gone):
                twins += [said["id"]] if shares(said["id"]) or said["id"] in {each["id"] for each in new} else []
                new.append(said)
                known.add(uuid)
    finally:
        if index is not None:
            index.close()
    if new:
        page = within(folder, "said", f"{session}.jsonl")
        page.parent.mkdir(parents=True, exist_ok=True)
        with open(page, "a", encoding="utf-8") as handle:
            if handle.tell() and not _ends_a_line(page):  # a last line cut short is ended first, and left as it is
                handle.write("\n")
            for said in new:
                handle.write(json.dumps(said, ensure_ascii=False) + "\n")
        noted = [
            said["id"] for said in new if said["voice"] == HIS and secret(said["text"]) and record.nameable(said["id"])
        ]
        if noted:  # by id alone: nothing of what the message holds is copied
            fresh = not within(folder, FLAGGED).exists()
            with open(within(folder, FLAGGED), "a", encoding="utf-8") as handle:
                if fresh:
                    handle.write(
                        "# Messages kept that look like they hold a key or a password, by id alone: "
                        "door.py strike <id> removes one.\n"
                    )
                handle.write("".join(said + "\n" for said in noted))
        _twinned(folder, twins)
    off.keep_unsaid(folder, offs)  # by id alone: nothing of what was said then is written
    # The marker moves only once what it steps over is in the archive: cut short before this,
    # the next archive reads those lines again, and what it holds already is not written twice.
    if end != start or (stored or {}).get("offset") != end:
        _moved(folder, key, path, end, off.last(at, kept_off))
    return len(new)


# --- the label pages ----------------------------------------------------------------------------

# What a label is for, said in the welcome (hook.welcome) and in the door's own description of `mark`
# (crossing/serve.py): the same tool, used to keep what lands on someone, would be a tool for the harm
# it is meant to spare.
FOR = (
    "A label holds what the person tells and asks, and where the work stands; it is never a record of how "
    "they seem, of what works on them or of how to move them."
)


def pages(folder: Path) -> list[Path]:
    """The label pages, each one reached through `within`."""
    found = [within(folder, "hand-over.md")] if within(folder, "hand-over.md").exists() else []
    return found + [within(folder, "labels", page.name) for page in sorted(within(folder, "labels").glob("*.md"))]


def digest(sentence: str) -> str:
    """Six characters that change when a sentence does. A stack keeps them beside each line it
    stands over, so that a build can tell a line that was reworded since from one that was not."""
    return hashlib.sha256(sentence.encode("utf-8")).hexdigest()[:6]


def plain(text: str) -> str:
    """A label's sentence as its row holds it: on one line, with no bar that would end its cell."""
    return re.sub(r"\s+", " ", text.replace("|", "/")).strip()


def clean(text: object, lines: bool = False) -> str:
    """A text as the door and the frame show it, to the person or to a session: no control
    character (a line break and a tab are kept where `lines` asks for a text shown on lines), no
    line or paragraph separator (U+2028, U+2029), and no format character, which holds every
    direction mark, override and isolate (U+200E, U+200F, U+061C, U+202A to U+202E, U+2066 to
    U+2069) and the other invisible ones. A label's sentence and a message's words can be written
    by anyone who can write a page or a transcript, and such a character reorders or hides what
    is read beside it. The plain pages are left as they are: only what is shown is cleaned."""
    kept = "\n\t" if lines else ""
    return "".join(ch for ch in str(text) if ch in kept or unicodedata.category(ch) not in ("Cc", "Cf", "Zl", "Zp"))


def models(folder: Path) -> dict[tuple[str, str], str]:
    """Which model wrote each label, from the home's `models.txt`, by the label's key and the
    digest of its sentence (`W2@1a2b3c claude-…`). The pages are left as they were: a label with
    no line here, or one reworded since its line was written, is of a model not known. Where a
    label has two lines, the later one stands."""
    try:
        lines = record.lines_in(within(folder, MODELS))
    except OSError:
        return {}
    return {
        (m.group(1), m.group(2)): m.group(3) for m in (SIGNED.match(line.split("#")[0].strip()) for line in lines) if m
    }


def _signed(folder: Path, key: str, text: str, model: str) -> None:
    """One line in `models.txt`: this label, as its sentence stands now, was written by this model.
    Written so, by the door's signing or the person's `layer`, the line is one the home has met
    (see SIGNS_MET): no build takes it for one that arrived."""
    _signs_known(folder, [f"{key}@{digest(text)} {model}"])
    fresh = not within(folder, MODELS).exists()
    with open(within(folder, MODELS), "a", encoding="utf-8") as handle:
        if fresh:
            handle.write(
                "# Which model wrote each label: its key, six characters of its sentence's digest, the model.\n"
            )
        handle.write(f"{key}@{digest(text)} {model}\n")


def newest(folder: Path, session: str) -> dict:
    """The newest message of the session's own voice that the archive holds of this session, or
    nothing where there is none: its time and its model, as the index holds them, in the order a
    build numbers messages (their time, then their line). The index is read, not the archive's
    pages: a hook asks this before every call of `mark`, and the hook brought the index up to that
    moment just before. Where there is no index of this make, one is made in memory (see `_open`)."""
    db = _open(folder)
    found = db.execute(
        "select at, model from said where session = ? and voice = ? order by seq desc limit 1", (session, OWN)
    ).fetchone()
    db.close()
    return dict(found) if found is not None else {}


def spoke(folder: Path, session: str) -> str:
    """The model of the newest message of the session's own voice that the archive holds of this
    session, or nothing where that message names none or there is no such message."""
    return str(newest(folder, session).get("model") or "")


def moved_on(folder: Path, session: str, path: Path | None = None) -> bool:
    """Whether the archive holds a message of another session that is newer than this session's
    own newest: another session has been working in the home since this one last spoke. A
    session's own messages are those archived under its name; a resume written into a transcript
    of its own repeats them under their ids, so where none is archived under its name they are
    the ones its transcript at `path` holds. Where it has none at all, there is no moment for
    anything to be newer than, and nothing is said."""
    gone = struck(folder)
    rows = [row for row in _archived(folder) if not _is_struck(row, gone)]
    own = {row["uuid"] for row in rows if row["session"] == session}
    if not own and path is not None and path.is_file():
        held = {row["uuid"] for row in rows}
        own = {str(row.get("uuid") or "") for _, row in transcript.appended(path) if row is not None} & held
    last = max((row.get("at") or "" for row in rows if row["uuid"] in own), default="")
    return bool(last) and any(row["uuid"] not in own and (row.get("at") or "") > last for row in rows)


# --- layers ---------------------------------------------------------------------------------------
#
# Every line of the session's voice belongs to the layer of the model that made it: a message by
# its own `model`, a label by its line in `models.txt`. The person's own words, and a plain label
# whose `whose` is the person's, belong to no layer and are there for whichever model faces the
# person. A stack is the sentence of the model that wrote it, whoever it is about. A line whose
# model is not known is of no known layer, and is read as every line was before layers.


def persons(label: dict) -> bool:
    """Whether a label is the person's: theirs by its `whose`, and no stack."""
    return label.get("whose") == HIS and not label.get("beneath")


def foreign(label: dict, model: str) -> bool:
    """Whether a label is of another model's layer than `model`'s: written by a known model other
    than it, and not the person's. Where `model` is not known, no label is."""
    return bool(model and label.get("model") and label["model"] != model and not persons(label))


def known(folder: Path) -> list[str]:
    """Every model this home knows a line of: a label's writer, or the model of a message of the
    session's voice."""
    db = _open(folder)
    found = sorted(
        {
            r[0]
            for r in db.execute(
                "select model from label where model != '' union "
                "select model from said where voice = 'session' and model != ''"
            )
        }
    )
    db.close()
    return found


def layered(folder: Path, model: str) -> tuple[int, int] | None:
    """Sign as made with `model` every label and every message of the session's voice in this home
    that has no model: what was kept before models were. One that has a model is never changed,
    nor is a line of the archive that is no text. Gives how many labels and how many messages were
    signed; nothing, where another act held the home's lock for WAIT seconds (see `_locked`), and
    then nothing is signed. The person's verb, from a shell."""
    held = _locked(folder)
    if held is None:
        return None
    try:
        return _layered(folder, model)
    finally:
        _unlocked(folder, held)


def _layered(folder: Path, model: str) -> tuple[int, int]:
    """`layered`, with the home's lock held."""
    by, gone = models(folder), struck(folder)
    signed = 0
    for label in labels(folder):
        if label["id"] not in gone and (label["id"], digest(label["text"])) not in by:
            _signed(folder, label["id"], label["text"], model)
            signed += 1
    spoken = 0
    for page in said_pages(folder):
        lines = lines_of(_text(page))
        out = []
        for line in lines:
            try:
                row = json.loads(line) if _whole(line) else None
            except ValueError:
                row = None
            if _said(row) and row["voice"] == OWN and not row.get("model"):
                line = json.dumps({**row, "model": model}, ensure_ascii=False)
                spoken += 1
            out.append(line)
        if out != lines:  # written whole beside itself and put in its place, so that no page is left half written
            _replaced(folder, page, "".join(line + "\n" for line in out))
    if signed or spoken:
        build(folder)
    return signed, spoken


def sign(folder: Path, key: str, sentence: str, model: str) -> bool:
    """Keep beside a label which model wrote it, where that was not kept when it was marked: the
    door's server is not told which session calls it, and a hook that is told signs the label
    after it. Only the label of that key and that sentence is signed, and only once."""
    label = next((each for each in labels(folder) if each["id"] == key), None)
    if not model or label is None or label["text"] != plain(sentence) or (key, digest(label["text"])) in models(folder):
        return False
    before = _sources(folder)
    _signed(folder, key, label["text"], model)
    # The index follows the line just written, as a build would make it: with the record of models.txt
    # where it stood for the plain files before (see `_current`), so that what is archived next is added;
    # else as before, and the next archive finds models.txt changed and makes the index whole.
    db = _current(folder, before)
    current = db is not None
    db = db if current else _open(folder)
    try:
        db.execute("update label set model = ? where id = ?", (model, key))
        if current:
            _restood(folder, db, before)
        db.commit()
    finally:
        db.close()
    return True


def _current(folder: Path, before: dict) -> sqlite3.Connection | None:
    """The index on disk, held for one change (begin immediate), where it stood for the plain files
    as they were `before` this act wrote any: of this make, made with their record, the label
    pages, `models.txt`, `struck.txt`, `off.txt` and `flagged.txt` as it recorded them, and the
    archive's pages as they were. Nothing otherwise, or where it cannot be opened."""
    made = within(folder, "store.db")
    within(folder, "store.db-journal")
    if not made.exists():
        return None
    stood = os.stat(made).st_ino
    db = sqlite3.connect(made, timeout=WAIT)
    try:
        db.execute("begin immediate")
        recorded = (
            {
                r[0]: (r[1], r[2])
                for r in db.execute("select name, size, changed from source where name not like 'said/%'")
            }
            if _trusted(db) and _believed_index(db, folder)
            else None
        )
        found = _since(folder, db) if recorded == before else None
        if os.stat(made).st_ino == stood and found is not None and not found[0] and not found[2]:
            return db
    except (sqlite3.Error, OSError, ValueError):
        pass
    db.close()
    return None


def _restood(folder: Path, db: sqlite3.Connection, before: dict) -> None:
    """Keep in the index's record how the plain files that this act changed stand now."""
    db.executemany(
        "insert or replace into source values (?,?,?,?,?)",
        [(name, *was, None, None) for name, was in _sources(folder).items() if before.get(name) != was],
    )


def _label_added(folder: Path, before: dict, key: str) -> bool:
    """Add a label just marked to the index, as archiving adds messages: where the index stood for
    the plain files as they were before the mark (see `_current`), the label is a plain one (no
    stack, taking no stack's place, named beneath none), and it is the last label of the last page,
    so that a whole build numbers it as it is numbered here. Its row, its full-text row and its
    anchors go in, with the record of the page and of `models.txt` as they now stand, in one
    transaction. Gives whether it was added; where it was not, the caller makes the index whole."""
    db = _current(folder, before)
    if db is None:
        return False
    try:
        kept = [label for label in labels(folder) if label["id"] not in struck(folder)]
        label = kept[-1] if kept else {}
        changed = {name for name, was in _sources(folder).items() if before.get(name) != was}
        if (
            label.get("id") != key
            or label["beneath"]
            or not changed <= {f"labels/{label['page']}", MODELS}
            or db.execute("select 1 from beneath where line = ?", (key,)).fetchone()
            or db.execute("select 1 from label where id = ?", (key,)).fetchone()
        ):
            return False
        held = all(db.execute("select 1 from said where id = ?", (each,)).fetchone() for each in label["anchors"])
        n = db.execute("select coalesce(max(n), 0) from label").fetchone()[0] + 1
        db.execute(
            "insert into label values (?,?,?,?,?,?,?,?,?,?)",
            (
                n,
                key,
                label["kind"],
                label["whose"],
                label["text"],
                label["page"],
                None,
                folder.name,
                "carried" if label["anchors"] and held else "unresolved",
                models(folder).get((key, digest(label["text"])), ""),
            ),
        )
        db.execute("insert into label_fts(rowid, text) values (?,?)", (n, label["text"]))
        db.executemany("insert into anchor values (?,?)", [(key, each) for each in label["anchors"]])
        _restood(folder, db, before)
        db.commit()
        return True
    except (sqlite3.Error, OSError, ValueError):
        return False
    finally:
        db.close()


def labels(folder: Path) -> list[dict]:
    """Every label of every page, in the pages' order: key, kind, whose, its sentence, the
    messages it rests on (`anchors`) and the lines stacked beneath it, each with the digest its
    row gives (`beneath`)."""
    found, seen = [], set()
    for page in pages(folder):
        lines = record.lines_in(page)  # a row that is no text is passed over, and the rest read as before
        by_line = {m.group(1): m.group(2) for m in map(LINE_TO_ID.match, lines) if m}
        for line in lines:
            m = ROW.match(line)
            if not m or m.group(1) in seen:
                continue
            key, text, whose, cell = m.groups()
            beneath: dict[str, str] = {}
            for line_key, was in BENEATH.findall(cell):
                beneath.setdefault(line_key, was)  # a line named twice is beneath once
            # The lines beneath are taken out first. What is left of the cell names messages, and a
            # digest of digits alone is then no line's number in an early page's table.
            # A pasted text's id is read whole and in its place. Read as its message's id, the label
            # would rest on the message; and where that id has no letter in it, it would not be read
            # at all, so that a label marked on such a paste would rest on nothing.
            # what lies between pasted texts' ids, and those ids, in turn
            parts = PASTED_ID.split(BENEATH.sub(" ", cell))
            cell = " ".join(parts[::2])
            ids = [each for n, part in enumerate(parts) for each in ([part] if n % 2 else named(part))]
            # an early page named its anchors by line and gave a table from line to id
            anchors = list(dict.fromkeys(ids + [by_line[n] for n in re.findall(r"\b\d{3,}\b", cell) if n in by_line]))
            seen.add(key)
            found.append(
                {
                    "id": key,
                    "kind": KINDS[key[0]],
                    "whose": whose.strip(),
                    "text": text.strip(),
                    "anchors": anchors,
                    "beneath": list(beneath.items()),
                    "page": page.name,
                }
            )
    return found


def rests(label: dict) -> str:
    """What a label rests on, as its brackets give it: the lines stacked beneath it by their
    keys, then the ids of messages."""
    return ", ".join([*label.get("beneath", ()), *label["anchors"]])


def some(keys: list[str], most: int = 24) -> str:
    """Keys in a row, for a line that names labels and recites none. A long row is cut short
    and says how many more there are: the line stands in a frame or an outline, which stay small
    however many labels it has to name."""
    return ", ".join(keys[:most]) + (f" and {len(keys) - most} more" if len(keys) > most else "")


# --- the database ---------------------------------------------------------------------------------


def _voices(row: dict) -> list[dict]:
    """An archived message as the store holds it. What the person pasted into a message is not
    what the person said: it becomes a row of its own beside the message, under the message's
    id with a number, and the message keeps a note of how much was pasted. Held as the person's,
    a paste would be counted and quoted as theirs."""
    if row["voice"] != HIS:
        return [row]
    typed, pastes = transcript.unpasted(row["text"])
    if not pastes:
        return [row]
    own = {**row, "text": re.sub(r"\n{3,}", "\n\n", typed).strip()}
    return [own] + [
        {**row, "uuid": f"{row['uuid']}+{n}", "id": f"{row['id']}+{n}", "voice": PASTED, "text": paste}
        for n, paste in enumerate(pastes, 1)
    ]


def _stood(kept: list[dict], held: set[str]) -> tuple[dict[str, str], dict[str, str]]:
    """Which stack each line stands beneath, and the state of every label, from the pages'
    rows and the ids the archive holds. See STATES.

    A stack stands over a line that is there, of its own kind and older than itself. The door
    marks no other; a page edited by hand may name one, and a ring of labels that each stood
    for the other would hide them all, so a build takes no such line for one beneath. Where
    two stacks name a line, the first in the pages is the one above it.

    A stack that is misaligned or unresolved is not sound, and what stands beneath it is
    carried: a stack that is not carried itself must not keep its lines from being carried.
    A label's own trouble is said before its place: one that is misaligned or unresolved is
    called so though it stands beneath a sound stack."""
    by_key = {label["id"]: label for label in kept}

    def under(stack: dict, key: str) -> bool:
        line = by_key.get(key)
        return line is not None and line["kind"] == stack["kind"] and int(key[1:]) < int(stack["id"][1:])

    parent: dict[str, str] = {}
    for stack in kept:
        for key, _ in stack["beneath"]:
            if under(stack, key):
                parent.setdefault(key, stack["id"])
    wrong: dict[str, str] = {}
    for label in kept:
        if not all(under(label, key) and digest(by_key[key]["text"]) == was for key, was in label["beneath"]):
            wrong[label["id"]] = "misaligned"
        elif not (label["anchors"] or label["beneath"]) or not held.issuperset(label["anchors"]):
            wrong[label["id"]] = "unresolved"
    state = {
        key: wrong.get(key) or ("cooled" if key in parent and parent[key] not in wrong else "carried") for key in by_key
    }
    return parent, state


def build(folder: Path) -> dict:
    """Make the database again from the plain files, whole. Returns what it now holds."""
    _built(folder)
    return status(folder)


def _built(folder: Path) -> None:
    """`build`, without what it gives back: made, put in its place, marked (see MINTED), and with
    the labels and the lines of models.txt that arrived noted."""
    folder.mkdir(parents=True, exist_ok=True)
    fresh, made = within(folder, "store.db.new"), within(folder, "store.db")
    if fresh.exists():
        fresh.unlink()
    db = sqlite3.connect(fresh)
    minted = secrets.token_hex(16)
    try:
        _index(folder, db)
        db.execute("create table minted(mark text)")
        db.execute("insert into minted values (?)", (minted,))
        db.commit()
    finally:
        db.close()
    _put(fresh, made)
    _mint(folder, minted)
    _noticed(folder)


# Which index a home's builds made is kept outside every project, beside the person's record (see
# `switched`): a line a home, {"home": ..., "index": <mark>}, and the same mark in the index itself
# (its table `minted`). An index whose mark is not the one kept there did not come from a build on
# this computer (a pull into a home that lies in a repository, a copy, a hand): it is not believed,
# and is made again before it is read. An index an older make wrote has no mark, and is made again
# once.
MINTED = "indexes"


def _minted_path() -> Path:
    return switched().with_name(switched().name + "." + MINTED)


def _minted_lines() -> list[dict]:
    try:
        lines = record.lines_in(_minted_path())
    except OSError:
        return []
    found = []
    for line in lines:
        try:
            given = json.loads(line)
        except ValueError:
            continue
        if isinstance(given, dict) and isinstance(given.get("home"), str) and isinstance(given.get("index"), str):
            found.append(given)
    return found


def _kept_mark(folder: Path) -> str:
    """The mark kept for this home's index, by its folder as the record names it or by another
    spelling of the same folder; nothing where none is kept."""
    home = spelled(folder)
    marks = [
        given["index"]
        for given in _minted_lines()
        if given["home"] == home or record._same(Path(given["home"]), folder)
    ]
    return marks[-1] if marks else ""


def _mint(folder: Path, mark: str) -> None:
    """Keep the mark of the index just made for this home, under the record's lock (see
    `_recording`, taken after the home's); its other lines stay as they are. Where it cannot be
    written, the log says so, and the index is made again at its next reading."""
    home = spelled(folder)
    try:
        with _recording():
            lines = [
                json.dumps(given, ensure_ascii=False)
                for given in _minted_lines()
                if not (given["home"] == home or record._same(Path(given["home"]), folder))
            ]
            lines.append(json.dumps({"home": home, "index": mark}, ensure_ascii=False))
            fresh = _minted_path().with_name(_minted_path().name + ".new")
            fresh.write_text("".join(line + "\n" for line in lines), encoding="utf-8")
            os.replace(fresh, _minted_path())
    except OSError as err:
        record.log(f"the mark of a home's index could not be kept: {err}")


def _believed_index(db: sqlite3.Connection, folder: Path) -> bool:
    """Whether an index is the one this computer's last build of the home made: its mark is the one
    kept beside the person's record (see MINTED)."""
    try:
        found = db.execute("select mark from minted").fetchone()
    except sqlite3.Error:
        return False
    return found is not None and bool(found[0]) and found[0] == _kept_mark(folder)


def _put(fresh: Path, made: Path) -> None:
    """Put a database made whole in the place of the one there, once no addition is being made to
    that one (see `refresh`): an addition keeps its change in `store.db-journal` beside it, which
    would be read as the new one's, so the old one is held while it is replaced. A journal left by
    an addition that was cut short is put back into the old one as it is held. Where it cannot be
    held within WAIT seconds, or is no database, it is replaced all the same."""
    held = sqlite3.connect(made, timeout=WAIT) if made.exists() else None
    if held is not None:
        try:
            held.execute("begin exclusive")
        except sqlite3.Error:
            held.close()
            held = None
    try:
        os.replace(fresh, made)
    finally:
        if held is not None:
            held.close()


def refresh(folder: Path) -> bool:
    """Bring the database up to what the plain files hold, after an archive kept new messages:
    by adding them to it, where nothing else of the home changed since it was made; otherwise
    by making it again whole (see `build`). Either gives the same database. Gives whether it was
    added to (and so also where there was nothing to add); False where it was made whole.

    Added to only where all of this holds: the index is there, of this make, and was made with a
    record of the plain files as they stood (the table `source`); no label page, `models.txt`,
    `struck.txt`, `off.txt` or `flagged.txt` is there, gone or changed since, by its size and the
    time it last changed; every page of the archive is as it was or only grew, with the bytes
    before its old end those that were read and that end the end of a line, and none is gone,
    shorter, or older than its record (see `_since`); no new message is one the index holds
    already, or would stand before its newest in the order of time (`_order`), or is named by a
    label as an anchor, whose state would change; and the addition, in one transaction, does not
    fail. Nothing of this is guessed at: where any one fails, the whole is made again."""
    made = within(folder, "store.db")
    within(folder, "store.db-journal")  # where the addition keeps its change while it is made
    db = None
    try:
        if made.exists():
            stood = os.stat(made).st_ino
            db = sqlite3.connect(made, timeout=WAIT)
            db.execute("begin immediate")  # one addition at a time, and a build waits for it (see `_put`)
            # A build that put another database in its place since it was opened: this one is no longer the index.
            if os.stat(made).st_ino == stood and _trusted(db) and _believed_index(db, folder) and _add(folder, db):
                db.commit()
                return True
    except (sqlite3.Error, OSError, ValueError):
        pass  # an addition that fails is made whole, as one that could not be trusted
    finally:
        if db is not None:
            db.close()  # what was not committed is rolled back
    try:
        build(folder)
    except sqlite3.OperationalError as err:  # no FTS5 here: the archive stands, and the index waits for it
        if not unsearchable(err):
            raise
    return False


def _trusted(db: sqlite3.Connection) -> bool:
    """Whether the database is of this make and was made with the record of its plain files."""
    named = {r[0] for r in db.execute("select name from sqlite_master where type = 'table'")}
    return db.execute("pragma user_version").fetchone()[0] == MADE and {"source", "ordered"} <= named


def _order(row: dict) -> tuple:
    """Where a message stands in the database: by its time, its session, and its line in its page."""
    return (row.get("at") or "", row["session"], row["_n"])


def _sources(folder: Path) -> dict[str, tuple[int, int]]:
    """The plain files besides the archive's pages that a build reads, or that the store reads
    beside the database: the label pages, `models.txt`, `struck.txt`, `off.txt` and `flagged.txt`,
    each that is there by its size and the time it last changed (in nanoseconds), as they stand
    before they are read."""
    found = {}
    for path in pages(folder) + [within(folder, name) for name in (MODELS, "struck.txt", off.FILE, FLAGGED)]:
        try:
            seen = path.stat()
        except FileNotFoundError:
            continue
        found[path.relative_to(folder).as_posix()] = (seen.st_size, seen.st_mtime_ns)
    return found


def _since(folder: Path, db: sqlite3.Connection) -> tuple[list[dict], int, dict] | None:
    """What the archive's pages hold beyond what the database was made from: the messages on the
    lines added since, each with its line's number, how many added lines are no message, and how
    each page that grew stands now. A page the record does not name is new, and is read whole.

    Nothing where the record cannot be trusted to stand for the pages: a page gone, shorter than
    its record, changed in place (the same size, another time), older than its record, or one
    whose bytes before the record's end are not those that were read, or do not end a line."""
    record_of = {
        r[0]: r[1:] for r in db.execute("select name, size, changed, lines, tail from source where name like 'said/%'")
    }
    rows, unread, stood, there = [], 0, {}, set()
    for page in said_pages(folder):
        name = f"said/{page.name}"
        there.add(name)
        was = record_of.get(name)
        with open(page, "rb") as handle:
            seen = os.fstat(handle.fileno())
            if was is None:
                size, lines, before = 0, 0, b""
            else:
                size, changed, lines, tail = was
                if (seen.st_size, seen.st_mtime_ns) == (size, changed):
                    continue
                if seen.st_size <= size or seen.st_mtime_ns < changed:
                    return None
                handle.seek(max(0, size - CHECKED))
                before = handle.read(size - max(0, size - CHECKED))
                if hashlib.sha256(before).hexdigest() != tail or (size and not before.endswith(b"\n")):
                    return None
            added = handle.read()
        text = record.decoded(added, page)
        more, passed = _read(text, lines)
        rows += more
        unread += passed
        stood[name] = (size + len(added), seen.st_mtime_ns, lines + len(text), _tail(before + added))
    return (rows, unread, stood) if there >= set(record_of) else None


def _add(folder: Path, db: sqlite3.Connection) -> bool:
    """Add to the database what the archive's pages hold beyond it (see `refresh`), inside the
    transaction the caller holds; or nothing, where the result would not be what a build gives."""
    recorded = {
        r[0]: (r[1], r[2]) for r in db.execute("select name, size, changed from source where name not like 'said/%'")
    }
    if _sources(folder) != recorded:
        return False
    found = _since(folder, db)
    if found is None:
        return False
    rows, unread, stood = found
    gone = struck(folder)
    passed = sum(1 for row in rows if _is_struck(row, gone))
    once: dict[str, dict] = {}
    for row in rows:  # as a build reads them: a message kept twice is the first of its rows
        if not _is_struck(row, gone):
            once.setdefault(row["uuid"], row)
    if any(db.execute("select 1 from said where uuid = ?", (uuid,)).fetchone() for uuid in once):
        return False  # which of the two a build keeps depends on the pages' order, which the index does not keep
    fresh = sorted(once.values(), key=_order)
    newest = db.execute("select at, session, line from ordered").fetchone()
    if fresh and newest[0] is not None and _order(fresh[0]) <= tuple(newest):
        return False  # it would stand among what is there: a build numbers every message again
    voiced = [each for row in fresh for each in _voices(row)]
    if (
        voiced
        and db.execute(
            f"select 1 from anchor where said in ({','.join('?' * len(voiced))}) limit 1",
            [each["id"] for each in voiced],
        ).fetchone()
    ):
        return False  # a label resting on it would change its state
    last = db.execute("select coalesce(max(seq), 0) from said").fetchone()[0]
    for seq, row in enumerate(voiced, last + 1):
        _said_row(db, seq, row)
        db.executemany(
            "insert into word values (?, 1) on conflict(term) do update set n = n + 1",
            [(term,) for term in sorted(_words(row["text"]))],
        )
    db.execute("update unread set lines = lines + ?", (unread,))
    if fresh:
        db.execute("update ordered set at = ?, session = ?, line = ?", _order(fresh[-1]))
    db.execute("update ordered set struck = struck + ?", (passed,))
    db.executemany("insert or replace into source values (?,?,?,?,?)", [(name, *was) for name, was in stood.items()])
    return True


def _said_row(db: sqlite3.Connection, seq: int, row: dict) -> None:
    """One message into the database, under its number in the order, with its full-text row."""
    db.execute(
        "insert into said values (?,?,?,?,?,?,?,?)",
        (
            seq,
            row["uuid"],
            row["id"],
            row["session"],
            row["voice"],
            row.get("at") or "",
            row["text"],
            row.get("model") or "",
        ),
    )
    db.execute("insert into said_fts(rowid, text) values (?,?)", (seq, row["text"]))


def _words(text: str) -> set[str]:
    """The words of a message, as the index counts them for a miss: three letters or more."""
    return set(re.findall(r"[^\W\d_]{3,}", text.lower()))


def _holding(folder: Path):
    """Whether the archive holds a message, by its uuid, as an archive asks it: of the database
    and the lines added to the pages since it was made (see `_since`), where the database stands
    for the pages and passed over no message as struck; otherwise of every page, read whole.
    Gives the question, a second one, whether the archive holds a message of this id of eight
    characters (see `_archive`, which asks it of a message it does not hold), and the database
    they ask, to be closed; or no database."""
    made = within(folder, "store.db")
    if made.exists():
        db = None
        try:
            db = sqlite3.connect(f"{made.resolve().as_uri()}?mode=ro", uri=True)  # read alone: no database is made
            if (
                _trusted(db)
                and _believed_index(db, folder)
                and not db.execute("select struck from ordered").fetchone()[0]
            ):
                found = _since(folder, db)
                if found is not None:
                    added = {row["uuid"] for row in found[0]}
                    named = {row["id"] for row in found[0]}
                    return (
                        (
                            lambda uuid: (
                                uuid in added
                                or db.execute(
                                    "select 1 from said where uuid = ? and voice != 'pasted'", (uuid,)
                                ).fetchone()
                                is not None
                            )
                        ),
                        (
                            lambda said: (
                                said in named
                                or db.execute(
                                    "select 1 from said where id = ? and voice != 'pasted'", (said,)
                                ).fetchone()
                                is not None
                            )
                        ),
                        db,
                    )
                db.close()
                db = None
                _unmade(made)
        except (sqlite3.Error, OSError, ValueError):
            pass
        if db is not None:
            db.close()
    rows = _archived(folder)
    held, named = {row["uuid"] for row in rows}, {row["id"] for row in rows}
    return held.__contains__, named.__contains__, None


def _unmade(made: Path) -> None:
    """Mark the database as of no make, where an archive finds that it no longer stands for the
    archive's pages (a page changed by another way than an archive's append): every read then
    makes the index in memory, and the build after the archive makes it whole, though what the
    archive appends next would leave the page looking as if it had only grown."""
    db = sqlite3.connect(made, timeout=WAIT)
    try:
        db.execute("begin immediate")
        db.execute("pragma user_version = 0")
        db.commit()
    finally:
        db.close()


def _index(folder: Path, db: sqlite3.Connection) -> None:
    """The database, made from the plain files into `db`: a file a build puts in its place, or
    one in memory alone, for a read that finds no index of this make on disk. Beside what is read,
    it keeps a record of how each plain file it was made from stood (`source`) and where the
    newest message stands (`ordered`), so that what an archive adds can be added to it."""
    sources = _sources(folder)  # before anything is read: a file changed after this is changed for the record
    gone = struck(folder)
    pages_were: dict = {}
    said, unread = _kept(folder, pages_were)
    passed = sum(1 for row in said if _is_struck(row, gone))
    once: dict[str, dict] = {}
    for row in said:  # a message an older make kept twice is the first of its rows; the second is passed over
        if not _is_struck(row, gone):
            once.setdefault(row["uuid"], row)
    said = list(once.values())
    said.sort(key=_order)
    newest = _order(said[-1]) if said else (None, None, None)
    said = [voiced for row in said for voiced in _voices(row)]
    kept = [label for label in labels(folder) if label["id"] not in gone]
    parent, state = _stood(kept, {row["id"] for row in said})
    by = models(folder)
    db.executescript(f"""
        pragma journal_mode = off; pragma secure_delete = on; pragma user_version = {MADE};
        create table said(seq integer primary key, uuid text unique, id text, session text, voice text, at text,
                          text text, model text);
        create index said_id on said(id);
        create virtual table said_fts using fts5(text, tokenize='{TOKENS}');
        create table label(n integer primary key, id text unique, kind text, whose text, text text, page text,
                           parent text, home text, state text, model text);
        create virtual table label_fts using fts5(text, tokenize='{TOKENS}');
        create table anchor(label text, said text);
        create index anchor_said on anchor(said);
        create table beneath(stack text, line text, digest text);
        create index beneath_stack on beneath(stack);
        create table word(term text primary key, n integer);
        create table unread(lines integer);
        create table source(name text primary key, size integer, changed integer, lines integer, tail text);
        create table ordered(at text, session text, line integer, struck integer);
    """)
    db.execute("insert into unread values (?)", (unread,))  # lines of the archive that are no message
    db.execute("insert into ordered values (?,?,?,?)", (*newest, passed))
    db.executemany(
        "insert into source values (?,?,?,?,?)",
        [(name, *was) for name, was in pages_were.items()]
        + [(name, size, changed, None, None) for name, (size, changed) in sources.items()],
    )
    words: dict[str, int] = {}
    for seq, row in enumerate(said, 1):
        _said_row(db, seq, row)
        for term in _words(row["text"]):
            words[term] = words.get(term, 0) + 1
    for n, label in enumerate(kept, 1):
        db.execute(
            "insert into label values (?,?,?,?,?,?,?,?,?,?)",
            (
                n,
                label["id"],
                label["kind"],
                label["whose"],
                label["text"],
                label["page"],
                parent.get(label["id"]),
                folder.name,
                state[label["id"]],
                by.get((label["id"], digest(label["text"])), ""),
            ),
        )
        db.execute("insert into label_fts(rowid, text) values (?,?)", (n, label["text"]))
        db.executemany("insert into anchor values (?,?)", [(label["id"], a) for a in label["anchors"]])
        db.executemany("insert into beneath values (?,?,?)", [(label["id"], key, was) for key, was in label["beneath"]])
    db.executemany("insert into word values (?,?)", sorted(words.items()))  # every word that is there, for a miss
    db.commit()


# What is said where this computer's sqlite3 has no FTS5, the full-text search the index is made
# with: the index cannot be made, and the archive in said/, written before any index, is kept all
# the same.
NO_SEARCH = (
    "This computer's python3 has no full-text search (FTS5) in its sqlite3, so the store cannot be "
    "searched; what is said is still kept in plain files."
)


def unsearchable(err: BaseException) -> bool:
    """Whether an error is SQLite's for a missing FTS5 ("no such module: fts5")."""
    return isinstance(err, sqlite3.OperationalError) and "fts5" in str(err).lower()


def searchable() -> bool:
    """Whether this computer's sqlite3 can make the index's full-text tables: one is made in
    memory, and nothing is written. Any other failure is not taken for a missing FTS5."""
    db = sqlite3.connect(":memory:")
    try:
        db.execute("create virtual table probe using fts5(text)")
        return True
    except sqlite3.OperationalError as err:
        return not unsearchable(err)
    finally:
        db.close()


def _open(folder: Path) -> sqlite3.Connection:
    """The database. Where there is none, or another make of the plugin left one (an older one
    has no states in it to read), it is made in memory from the plain files, and nothing is
    written: no read of a home makes a folder or a database. A build makes the one on disk,
    as the hooks, a mark and a strike do. A `store.db` that is no database at all (cut short, or
    written over) is read as none: the index is made in memory, and the next build or archive
    makes the one on disk again."""
    made = within(folder, "store.db")
    within(folder, "store.db-journal")  # where the index keeps a change while it is made
    if made.exists():
        db = sqlite3.connect(made)
        stranger = False
        try:
            if db.execute("pragma user_version").fetchone()[0] == MADE and _trusted(db):
                if _believed_index(db, folder):
                    db.row_factory = sqlite3.Row
                    return db
                stranger = True
        except sqlite3.DatabaseError:  # not a database: made again from the plain files, here in memory
            pass
        db.close()
        if stranger:  # an index no build here made, or an older make's: made again on disk, and read
            _built(folder)
            db = sqlite3.connect(made)
            db.row_factory = sqlite3.Row
            return db
    db = sqlite3.connect(":memory:")
    _index(folder, db)
    db.row_factory = sqlite3.Row
    return db


def _counted(db: sqlite3.Connection) -> dict[str, int]:
    """How many labels are in each state: every state is named, at nought too."""
    return {
        **dict.fromkeys(STATES, 0),
        **{r[0]: r[1] for r in db.execute("select state, count(*) from label group by state")},
    }


def status(folder: Path) -> dict:
    db = _open(folder)
    one = lambda sql: db.execute(sql).fetchone()[0]  # noqa: E731
    held = {
        "his": one("select count(*) from said where voice = 'his'"),
        "session": one("select count(*) from said where voice = 'session'"),
        "pasted": one("select count(*) from said where voice = 'pasted'"),
        "characters": one("select coalesce(sum(length(text)), 0) from said"),
        "from": one("select coalesce(min(substr(at, 1, 10)), '') from said"),
        "to": one("select coalesce(max(substr(at, 1, 10)), '') from said"),
        "labels": one("select count(*) from label"),
        "struck": len(struck(folder)),
        "states": _counted(db),
        # how many of each say which model wrote them; of the rest it is not known
        "models": {
            "labels": one("select count(*) from label where model != ''"),
            "session": one("select count(*) from said where voice = 'session' and model != ''"),
        },
        "unread": one("select coalesce(sum(lines), 0) from unread"),
        "flagged": _flagged(folder, db),
    }
    db.close()
    # When the switch was off, and how many lines of that record could not be read: never what was said then.
    kept_off, held["off_unread"] = off.told(folder)
    held["off"], held["off_now"] = len(kept_off), bool(kept_off) and kept_off[-1][1] is None
    held["lost"] = lost(folder)
    held["shelled"] = shelled(folder)
    held["arrived"], held["collided"] = arrived(folder), collided(folder)
    held["signs_arrived"] = signs_arrived(folder)
    return held


# The small files of a home that the plugin reads as lines, beside the archive's pages and the label
# pages: a line of any of them that is no text is passed over where it is read (see record.decoded).
LINED = (
    "struck.txt",
    MODELS,
    MARKERS,
    UNHELD,
    off.UNSAID,
    PLACES,
    FLAGGED,
    "shelled.txt",
    "welcomed.txt",
    "told.txt",
    "there.txt",
    "calling.txt",
    "labelled.txt",
    "arrived.txt",
    "collided.txt",
    "models-met.txt",
    "models-arrived.txt",
    "mode",
    "carry",
    "switch",
    "copy",
    "project",
)
DAMAGED_TOLD = "damaged-told.txt"  # the files the person's status said hold a line that is no text, and how many


def damaged(folder: Path) -> list[str]:
    """The files of the home that hold a line that is no text, by their names from the home: the
    archive's pages, the label pages, and the small files read as lines (LINED). Each is said once,
    for as many such lines as it holds, through `once`: the person's `status` asks this."""
    found = []
    for path in said_pages(folder) + pages(folder) + [within(folder, name) for name in LINED]:
        bad = record.undecodable(path)
        name = path.relative_to(folder).as_posix()
        if bad and once(folder, DAMAGED_TOLD, f"{name} {bad}"):
            found.append(name)
    return found


# A label marked from a shell, not through the door's server, that speaks for the person or about
# the two of them: no hook shows it to the person as it is marked, so its key is kept in a small
# file of the home, and the person's `status` says it the next time.
SHELLED = "shelled.txt"


def shell_marked(folder: Path, key: str) -> None:
    """Keep that the label of this key was marked from a shell."""
    path = within(folder, SHELLED)
    fresh = not path.exists()
    with open(path, "a", encoding="utf-8") as handle:
        if fresh:
            handle.write(
                "# Labels marked from a shell as the person's or about the two of them, by key: status says them.\n"
            )
        handle.write(key + "\n")


def shelled(folder: Path) -> list[str]:
    """The keys kept in SHELLED, each once, in its order, of the labels that are still there."""
    try:
        lines = record.lines_in(within(folder, SHELLED))
    except OSError:
        return []
    there = {label["id"] for label in labels(folder)}
    return [key for key in dict.fromkeys(line.strip() for line in lines) if KEY.fullmatch(key) and key in there]


def once(folder: Path, name: str, line: str) -> bool:
    """Whether this line is to be said now: it is not yet in the home's small file `name`, and is
    written there. Where that file cannot be written, nothing is said: said at every call, a
    sentence meant once would be worse than none."""
    path = within(folder, name)
    try:
        if line in record.lines_in(path):
            return False
    except FileNotFoundError:
        pass
    except OSError:
        return False
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
    except OSError:
        return False
    return True


# Which labels came into the pages by the door's own mark is kept beside them: LABELLED holds every
# label the home has met, by its key and its sentence's digest, and a build that finds one it has
# not met (a pull, a checkout, a hand) notes it in ARRIVED, for the person's next `status`. The first
# build of a home that has no LABELLED meets every label there is, and notes none.
LABELLED, ARRIVED = "labelled.txt", "arrived.txt"


def _met(folder: Path) -> set[str] | None:
    """The labels the home has met, as LABELLED keeps them; nothing where it keeps none yet."""
    try:
        return {
            line.strip() for line in record.lines_in(within(folder, LABELLED)) if SIGNED_KEY.fullmatch(line.strip())
        }
    except FileNotFoundError:
        return None


SIGNED_KEY = re.compile(r"[RWN]\d+@[0-9a-f]{6}")


def _known(folder: Path, entries: list[str]) -> list[str]:
    """Add these labels, each as `key@digest`, to those the home has met; where it has met none
    yet, every label its pages hold now is met first. Gives those that were new to it."""
    met = _met(folder)
    if met is None:
        held = [f"{label['id']}@{digest(label['text'])}" for label in labels(folder)]
        with open(within(folder, LABELLED), "a", encoding="utf-8") as handle:
            handle.write("# The labels this home has met, by key and digest: a build notes any other in arrived.txt.\n")
            handle.write("".join(each + "\n" for each in dict.fromkeys(held)))
        met = set(held)
    new = [each for each in dict.fromkeys(entries) if each not in met]
    if new:
        with open(within(folder, LABELLED), "a", encoding="utf-8") as handle:
            handle.write("".join(each + "\n" for each in new))
    return new


# As for labels, so for the lines of `models.txt`: SIGNS_MET holds every line the home has met, as
# `key@digest model`, and a build that finds one it has not met (a pull, a checkout, a hand) notes it
# in SIGNS_ARRIVED, for the person's next `status`. The line is followed all the same, as an arrived
# label is carried. The first build of a home that has no SIGNS_MET meets every line there is; a home
# that is adopted has met none of them (see `_signs_unmet`).
SIGNS_MET, SIGNS_ARRIVED = "models-met.txt", "models-arrived.txt"


def _model_lines(folder: Path) -> list[str]:
    """The lines of `models.txt` that sign a label, as `key@digest model`."""
    try:
        lines = record.lines_in(within(folder, MODELS))
    except OSError:
        return []
    found = (SIGNED.match(line.split("#")[0].strip()) for line in lines)
    return [f"{m.group(1)}@{m.group(2)} {m.group(3)}" for m in found if m]


def _signs_met(folder: Path) -> set[str] | None:
    try:
        return {line.strip() for line in record.lines_in(within(folder, SIGNS_MET)) if not line.startswith("#")}
    except FileNotFoundError:
        return None


def _signs_known(folder: Path, entries: list[str]) -> list[str]:
    """Add these lines to those the home has met; where it has met none yet, every line `models.txt`
    holds now is met first. Gives those that were new to it."""
    met = _signs_met(folder)
    if met is None:
        held = _model_lines(folder)
        with open(within(folder, SIGNS_MET), "a", encoding="utf-8") as handle:
            handle.write(
                "# The lines of models.txt this home has met: a build notes any other in models-arrived.txt.\n"
            )
            handle.write("".join(each + "\n" for each in dict.fromkeys(held)))
        met = set(held)
    new = [each for each in dict.fromkeys(entries) if each not in met]
    if new:
        with open(within(folder, SIGNS_MET), "a", encoding="utf-8") as handle:
            handle.write("".join(each + "\n" for each in new))
    return new


def _signs_unmet(folder: Path) -> None:
    """As a home is adopted: where it holds `models.txt`, it has met none of its lines, whatever a
    SIGNS_MET that came with it says, so that the next build notes every one in SIGNS_ARRIVED for the
    person's `status`, as any line that came by no signing through the door. SIGNS_MET is written
    whole, beside itself, with its header alone."""
    if not within(folder, MODELS).exists():
        return
    fresh = within(folder, SIGNS_MET + ".new")
    fresh.write_text(
        "# The lines of models.txt this home has met: a build notes any other in models-arrived.txt.\n",
        encoding="utf-8",
    )
    os.replace(fresh, within(folder, SIGNS_MET))


def signs_arrived(folder: Path) -> list[str]:
    """The lines noted in SIGNS_ARRIVED that `models.txt` still holds, each once, in its order."""
    try:
        lines = record.lines_in(within(folder, SIGNS_ARRIVED))
    except OSError:
        return []
    there = set(_model_lines(folder))
    return list(dict.fromkeys(line.strip() for line in lines if line.strip() in there))


def signs_arrived_told(folder: Path) -> None:
    """The person was told the lines of `models.txt` that arrived: the file goes."""
    within(folder, SIGNS_ARRIVED).unlink(missing_ok=True)


def _noticed(folder: Path) -> None:
    """At a build: the labels of the pages the home has not met, which came by no mark through the
    door, noted in ARRIVED, by key and digest, and met from now on. A struck key is not noted. And so
    the lines of `models.txt` the home has not met, in SIGNS_ARRIVED."""
    if _signs_met(folder) is None:
        _signs_known(folder, [])
    else:
        came = _signs_known(folder, _model_lines(folder))
        if came:
            with open(within(folder, SIGNS_ARRIVED), "a", encoding="utf-8") as handle:
                handle.write("".join(each + "\n" for each in came))
    if _met(folder) is None:
        _known(folder, [])
        return
    gone = struck(folder)
    came = _known(
        folder, [f"{label['id']}@{digest(label['text'])}" for label in labels(folder) if label["id"] not in gone]
    )
    if came:
        with open(within(folder, ARRIVED), "a", encoding="utf-8") as handle:
            handle.write("".join(each + "\n" for each in came))


def arrived(folder: Path) -> list[str]:
    """The keys of the labels noted in ARRIVED that the pages still hold as they were noted, each
    once, in its order."""
    try:
        lines = record.lines_in(within(folder, ARRIVED))
    except OSError:
        return []
    there = {f"{label['id']}@{digest(label['text'])}" for label in labels(folder)}
    return list(dict.fromkeys(line.strip().split("@")[0] for line in lines if line.strip() in there))


def arrived_told(folder: Path) -> None:
    """The person was told the labels that arrived: the file goes, file by file."""
    within(folder, ARRIVED).unlink(missing_ok=True)


def collided_told(folder: Path) -> None:
    """The person was told the ids two messages share: the file goes, file by file."""
    within(folder, COLLIDED).unlink(missing_ok=True)


def shelled_told(folder: Path) -> None:
    """The person was told the labels marked from a shell: the file goes, file by file."""
    within(folder, SHELLED).unlink(missing_ok=True)


def _flagged(folder: Path, db: sqlite3.Connection) -> list[str]:
    """The ids noted as looking like they hold a key or a password whose message the store still
    holds: one struck is gone from the store, and is not said again."""
    return [said for said in flagged(folder) if db.execute("select 1 from said where id = ?", (said,)).fetchone()]


def not_by(folder: Path, model: str) -> list[str]:
    """The keys of the labels that a model other than this one wrote, in the pages' order. A label
    whose model is not known is not among them: it may have been this one's."""
    db = _open(folder)
    keys = [r[0] for r in db.execute("select id from label where model != '' and model != ? order by n", (model,))]
    db.close()
    return keys


def _resting(db: sqlite3.Connection, ids: list[str]) -> dict[str, list[str]]:
    """The labels that rest on each of these messages."""
    found: dict[str, list[str]] = {}
    for said in ids:
        found[said] = [r[0] for r in db.execute("select label from anchor where said = ? order by label", (said,))]
    return found


def _anchors(db: sqlite3.Connection, label: str) -> list[str]:
    return [r[0] for r in db.execute("select said from anchor where label = ?", (label,))]


def _beneath(db: sqlite3.Connection, label: str) -> list[str]:
    """The keys of the lines a stack's row names, in the row's order; none for a plain label."""
    return [r[0] for r in db.execute("select line from beneath where stack = ? order by rowid", (label,))]


# --- find -----------------------------------------------------------------------------------------


def _terms(words: str) -> list[tuple[str, str]]:
    """What was looked for, piece by piece: how the index is to be asked for it, and the run
    of letters itself. A phrase stands in quotes; a `*` after a word's beginning takes every
    word that begins so."""
    found = []
    for phrase, word in TERM.findall(words):
        letters = " ".join(re.findall(r"\w+", phrase or word))
        if letters:  # a pair of quotes may hold no word at all
            found.append((f'"{letters}"' + ("*" if word.endswith("*") else ""), letters.lower()))
    return found


def _part(text: str, runs: list[str]) -> str:
    """The stretch of a text around the first of these runs of letters, with the run in brackets."""
    low = text.lower()
    at, run = min((low.find(run), run) for run in runs if run in low)
    start, end = max(0, at - 70), at + len(run)
    return (
        ("… " if start else "")
        + text[start:at]
        + "["
        + text[at:end]
        + "]"
        + text[end : end + 110]
        + (" …" if end + 110 < len(text) else "")
    )


def find(folder: Path, words: str, voice: str | None = None, limit: int = 8) -> dict:
    """Messages and labels that hold these words: all of them, or failing that any of them.

    Each is looked for on its own: where labels hold every word, a message that holds only
    some of them is still shown.

    A word is found by its stem, and also as a plain run of letters wherever it stands, so
    that the door never finds less than a search of the files would: a word inside a longer
    one is no word to an index."""
    db = _open(folder)
    out = {"asked": words, "all_words": True, "labels_all": True, "labels": [], "said": [], "nearest": []}
    terms = _terms(words)
    if not terms:
        db.close()
        return out
    runs = [run for _, run in terms]

    def held(every: bool, table: str, by_index: str, by_letters: str, more: tuple = ()) -> list[dict]:
        rows = [
            dict(r) for r in db.execute(by_index, ((" " if every else " OR ").join(q for q, _ in terms), *more, limit))
        ]
        have = {r["id"] for r in rows}
        letters = (" and " if every else " or ").join("instr(lower(text), ?)" for _ in runs)
        for r in db.execute(by_letters.format(letters), (*runs, *more, limit)):
            if r["id"] not in have and len(rows) < limit:
                rows.append(
                    {
                        **{k: r[k] for k in r.keys() if k != "text"},
                        **({"text": r["text"]} if table == "label" else {"part": _part(r["text"], runs)}),
                    }
                )
        return rows

    def labelled(every: bool) -> list[dict]:
        return held(
            every,
            "label",
            "select l.id, l.kind, l.whose, l.text, l.model from label_fts f join label l on l.n = f.rowid "
            "where label_fts match ? order by bm25(label_fts) limit ?",
            "select id, kind, whose, text, model from label where ({}) order by n desc limit ?",
        )

    def said(every: bool) -> list[dict]:
        only = " and s.voice = ?" if voice else ""
        return held(
            every,
            "said",
            "select s.id, s.voice, s.at, s.model, snippet(said_fts, 0, '[', ']', ' … ', 28) as part "
            "from said_fts f "
            "join said s on s.seq = f.rowid where said_fts match ?" + only + " order by bm25(said_fts) limit ?",
            "select s.id, s.voice, s.at, s.model, s.text from said s where ({})"
            + only
            + " order by s.seq desc limit ?",
            (voice,) if voice else (),
        )

    out["labels"] = labelled(True)
    if not out["labels"]:
        out["labels"], out["labels_all"] = labelled(False), False
    out["said"] = said(True)
    if not out["said"]:
        out["said"] = said(False)
        # Nothing to qualify where no message was found and a label holds every word.
        out["all_words"] = not out["said"] and bool(out["labels"]) and out["labels_all"]
    if not (out["labels"] or out["said"]):
        # A miss names the nearest words that are there, so the next reach is not a guess.
        # The words that are there, listed once; and the nearest to a few of the words asked alone, so
        # that a long miss costs no more than a short one.
        known = dict(db.execute("select term, n from word").fetchall())
        listed = list(known)
        tried = list(dict.fromkeys(runs))[:TRIED]
        near = [w for run in tried for w in difflib.get_close_matches(run, listed, n=3, cutoff=0.7)]
        out["nearest"] = [(w, known[w]) for w in dict.fromkeys(near)][:5]
    for label in out["labels"]:
        label["anchors"], label["beneath"] = _anchors(db, label["id"]), _beneath(db, label["id"])
    resting = _resting(db, [r["id"] for r in out["said"]])
    for row in out["said"]:
        row["labels"] = resting[row["id"]]
    db.close()
    return out


def thread(folder: Path, said_id: str, around: int = 2) -> dict:
    """A message in its place: what stood before and after it, and the labels that rest on any of them.
    An id of eight characters that two messages share is no one place: the whole ids of both are
    given (`twins`), and either is threaded by its own. It reaches AROUND messages to either side
    at most, however many are asked for."""
    around = max(0, min(around, AROUND))
    db = _open(folder)
    twins = (
        [
            r[0]
            for r in db.execute(
                "select distinct uuid from said where id = ? and voice != 'pasted' order by uuid", (said_id,)
            )
        ]
        if re.fullmatch(r"[0-9a-f]{8}", said_id)
        else []
    )
    if len(twins) > 1:
        db.close()
        return {"asked": said_id, "found": False, "said": [], "labels": [], "twins": twins}
    centre = db.execute(
        "select seq from said where id = ? or uuid like ? order by seq limit 1", (said_id, said_id + "%")
    ).fetchone()
    if centre is None:
        db.close()
        return {"asked": said_id, "found": False, "said": [], "labels": []}
    rows = [
        dict(r)
        for r in db.execute(
            "select seq, id, voice, at, text, model from said where seq between ? and ? order by seq",
            (centre["seq"] - around, centre["seq"] + around),
        )
    ]
    for row in rows:
        row["is_asked"] = row["seq"] == centre["seq"]
        most = WHOLE if row["is_asked"] else NEAR
        if len(row["text"]) > most:
            row["text"] = row["text"][:most].rstrip() + " […]"
    resting = _resting(db, [r["id"] for r in rows])
    keys = sorted({k for ks in resting.values() for k in ks})
    held = (
        [
            dict(r)
            for r in db.execute(
                f"select id, kind, whose, text, model from label where id in ({','.join('?' * len(keys))}) order by n",
                keys,
            )
        ]
        if keys
        else []
    )
    for label in held:
        label["beneath"] = _beneath(db, label["id"])
    for row in rows:
        row["labels"] = resting[row["id"]]
    gaps = _gaps(folder, db, rows[0]["seq"], rows[-1]["seq"])
    db.close()
    return {"asked": said_id, "found": True, "said": rows, "labels": held, "gaps": gaps}


def _gaps(folder: Path, db: sqlite3.Connection, first: int, last: int) -> list[dict]:
    """The spans when the switch was off that stand among the messages from `first` to `last`, or
    right before or after them, each with the message it stands before (`before`, nothing after
    the newest): what was said then is not kept, and the place says only that something may
    have been. The messages are in the order of their times, and a span is put by its beginning."""
    found = []
    for span in off.told(folder)[0]:
        after = db.execute("select min(seq) from said where at > ?", (off.said_at(span[0]),)).fetchone()[0]
        place = after if after is not None else db.execute("select coalesce(max(seq), 0) + 1 from said").fetchone()[0]
        if first <= place <= last + 1:
            start, end = off.shown(span)
            found.append({"before": after, "off": start, "on": end})
    return found


# --- the room -------------------------------------------------------------------------------------


def look(folder: Path, newest: int = 8) -> dict:
    """The store in outline, with no word needed: its days, its kinds of label, the newest
    labels about the work, and the line left at the door.

    The standing lines about the person are given by id and number alone. An outline nobody
    asked a question of does not recite what was told in confidence. A stack over standing
    lines is as quiet as they are: how many stand beneath how many stacks is said, and what
    is misaligned or unresolved is named by its key. Of the work, the newest are those that
    are not cooled: a stack stands there for its lines."""
    db = _open(folder)
    one = lambda sql: db.execute(sql).fetchone()[0]  # noqa: E731
    out = {
        "days": [
            dict(r)
            for r in db.execute(
                "select substr(at, 1, 10) as day, sum(voice = 'his') as his, sum(voice = 'session') as session, "
                "sum(voice = 'pasted') as pasted from said group by day order by day"
            )
        ],
        "standing": [r[0] for r in db.execute("select id from label where kind = 'relation' order by n")],
        "work": [r[0] for r in db.execute("select id from label where kind = 'work' order by n")],
        "newest": [
            dict(r)
            for r in db.execute(
                "select id, whose, text, state, parent, model from label where kind = 'work' and state != 'cooled' "
                "order by n desc limit ?",
                (newest,),
            )
        ],
        "left": None,
        "struck": len(struck(folder)),
        "states": _counted(db),
        "stacks": {
            "lines": one("select count(*) from label where kind = 'relation' and state = 'cooled'"),
            "stacks": one("select count(distinct parent) from label where kind = 'relation' and state = 'cooled'"),
        },
        "misaligned": [r[0] for r in db.execute("select id from label where state = 'misaligned' order by n")],
        "unresolved": [r[0] for r in db.execute("select id from label where state = 'unresolved' order by n")],
        "last": db.execute("select coalesce(max(at), '') from said").fetchone()[0],  # how far the archive is kept
        # when the switch was off, by the day each span began: a line in the days' place, and nothing of what was said
        "off": [
            {"day": off.said_at(span[0])[:10], "off": shown[0], "on": shown[1]}
            for span in off.told(folder)[0]
            for shown in [off.shown(span)]
        ],
        "flagged": _flagged(folder, db),  # for the person's own look alone: the door's server is not told it
        "lost": lost(folder),  # the record of when Crossing was off cannot be told: nothing is archived
    }
    left = db.execute("select id, text from label where kind = 'next' order by n desc limit 1").fetchone()
    if left is not None:
        out["left"] = {**dict(left), "anchors": _anchors(db, left["id"])}
    for label in out["newest"]:
        label["anchors"], label["beneath"] = _anchors(db, label["id"]), _beneath(db, label["id"])
    db.close()
    return out


def listed(folder: Path, kind: str | None = None, day: str | None = None, ids: tuple = (), limit: int = 40) -> dict:
    """The labels themselves, newest first: those named by id; or those of a kind, or of a day.

    A label's day is the day of the newest message it rests on; a stack's is also the day of
    its own page, so that a stack that rests on labels alone is found by a day. With no kind named, the
    standing lines about the person are counted and not shown: they are listed when asked
    for by their kind or by id.

    Each label comes with its state, the stack it stands beneath (`parent`), the keys of
    the lines its own row names (`beneath`) and the model that wrote it, or nothing (`model`).
    A stack named by id is given with every line beneath it, right under it and one `depth`
    further in; a line named beside its stack is given once, there. By kind or by day each
    label is a row of its own."""
    db = _open(folder)
    rows = [
        dict(r)
        for r in db.execute(
            "select l.id, l.kind, l.whose, l.text, l.state, l.parent, l.model, l.page, "
            "(select max(substr(s.at, 1, 10)) from anchor a "
            "join said s on s.id = a.said where a.label = l.id) as day from label l order by l.n desc"
        )
    ]
    for row in rows:
        row["anchors"], row["beneath"] = _anchors(db, row["id"]), _beneath(db, row["id"])
    db.close()
    wanted = {i.upper() for i in ids}
    if wanted:
        by_key = {r["id"]: r for r in rows}

        def under(stack: dict, depth: int) -> list[dict]:
            found = []
            for key in stack["beneath"]:
                line = by_key.get(key)
                if line is not None and line["parent"] == stack["id"]:  # gone, or beneath another, is not given here
                    found += [{**line, "depth": depth}] + under(line, depth + 1)
            return found

        beneath = {r["id"]: under(r, 1) for r in rows if r["id"] in wanted}
        below = {line["id"] for lines in beneath.values() for line in lines}
        shown, quiet = (
            [
                each
                for r in rows
                if r["id"] in beneath and r["id"] not in below
                for each in [{**r, "depth": 0}, *beneath[r["id"]]]
            ],
            [],
        )
    else:
        shown = [
            r
            for r in rows
            if (r["kind"] == kind if kind else r["kind"] != "relation")
            and (not day or r["day"] == day or (r["beneath"] and r["page"] == f"{day}.md"))
        ]
        quiet = [] if kind else [r["id"] for r in rows if r["kind"] == "relation"][::-1]
    return {
        "labels": shown[:limit],
        "more": max(0, len(shown) - limit),
        "quiet": quiet,
        "missing": sorted(wanted - {r["id"] for r in rows}),
    }


# --- writing ---------------------------------------------------------------------------------------


def mark(
    folder: Path,
    kind: str,
    whose: str,
    text: str,
    anchors: list[str],
    day: str | None = None,
    model: str = "",
    facing: str = "",
    persons: bool = True,
) -> dict:
    """Write a label with its anchors into the day's plain page. A label whose anchor the archive
    does not hold is refused: a label that rests on nothing is not to be believed.

    An anchor may be another label's key. The label is then a stack, and those labels the lines
    beneath it: they stay in their pages, whole, and the stack is carried in their place. A
    stack holds lines of its own kind, each beneath one stack alone, and stacks go two deep and
    no deeper; a line left at the door is neither a stack nor beneath one. Each is refused in
    a sentence, and nothing is written.

    A line beneath a misaligned stack is free to be stacked again. Such a stack no longer
    stands for its lines and is to be written again: the stack marked over any of them takes
    its place, and the old one is struck in the same act, as `strike` would strike it.
    `replaced` names it. Lines of it that the new stack did not take are carried again. That is
    all a mark ever strikes: a stack, never a message. Where the mark is not the person's own
    (`persons` false: a session's, through the door's server or a shell), a misaligned stack
    whose `whose` is the person's (`his`) is not taken over, and the mark is refused.

    `model` is the model that wrote the label, where whoever marks it knows (see `spoke`): it is
    kept beside the pages, in `models.txt`, and the row itself is written as it always was.

    `facing` is the model that marks now, where that is known. A stack is then scoped to its own
    layer: it is refused where any line it would stand over, at any depth, or a misaligned stack
    it would take the place of, is of another model's layer (see `foreign`). The person's lines,
    its own and those of no known model it may stand over. Where `facing` is not known, nothing
    of this is asked."""
    text = plain(text)
    given = list(dict.fromkeys(a.strip().strip("`") for a in anchors if a.strip()))
    lines = list(dict.fromkeys(a.upper() for a in given if KEY.fullmatch(a.upper())))
    anchors = [a for a in given if not KEY.fullmatch(a.upper())]
    if not text or not given:
        return {"written": False, "why": "a label needs a sentence and at least one anchor"}
    if len(text) > LONGEST:
        return {"written": False, "why": f"a label is one sentence, and this one is longer than {LONGEST:,} characters"}
    day = record.ident(day or datetime.date.today().isoformat())  # the page's name
    letter = LETTER.get(kind, "W")
    if not folder.is_dir():  # a home not made yet holds nothing to rest on: refused as it stands, and none is made
        return {"written": False, "why": _unmarked(folder, letter, lines, anchors, facing, persons)[0]}
    # Decided with the lock held, from the index opened under it: two marks at once over one line
    # would otherwise both find it beneath no stack, and both stand over it.
    held = _locked(folder)  # one mark, strike, archive or layering at a time: two marks at once take two keys
    if held is None:
        return {"written": False, "why": BUSY.format("marked")}
    try:
        why, beneath = _unmarked(folder, letter, lines, anchors, facing, persons)
        if why:
            return {"written": False, "why": why}
        return _marked(folder, letter, whose, text, lines, anchors, beneath, day, model)
    finally:
        _unlocked(folder, held)


def _unmarked(
    folder: Path, letter: str, lines: list[str], anchors: list[str], facing: str, persons: bool
) -> tuple[str, dict]:
    """Why `mark` refuses, or nothing; and each label named as a line beneath, as the store holds
    it. The caller holds the home's lock, where there is a home."""
    db = _open(folder)
    missing = [a for a in anchors if db.execute("select 1 from said where id = ?", (a,)).fetchone() is None]
    beneath = {
        key: db.execute(
            "select l.kind, l.text, l.parent, "
            "(select p.state from label p where p.id = l.parent) as above, "
            "(select p.whose from label p where p.id = l.parent) as owner "
            "from label l where l.id = ?",
            (key,),
        ).fetchone()
        for key in lines
    }
    deep = [
        key
        for key in lines
        if db.execute("select 1 from beneath b join beneath c on c.stack = b.line where b.stack = ?", (key,)).fetchone()
    ]

    # Whose layer each line it would stand over is in, and each stack above them: by the parents a
    # build made, so that what is read is what the frame and the lists read.
    def layer(key: str) -> dict:
        found = db.execute("select whose, model from label where id = ?", (key,)).fetchone()
        return {"id": key, "whose": found["whose"], "model": found["model"], "beneath": _beneath(db, key)}

    over: list[dict] = []
    todo = [key for key in lines if beneath[key] is not None] if facing else []
    while todo:  # the lines, and every line beneath them: stacks go two deep, and a line stands beneath one
        over.append(layer(todo.pop(0)))
        todo += [r[0] for r in db.execute("select id from label where parent = ? order by n", (over[-1]["id"],))]
    above = [
        layer(key)
        for key in dict.fromkeys(beneath[k]["parent"] for k in lines if facing and beneath[k] and beneath[k]["parent"])
    ]
    db.close()
    if missing:
        return "no such message in the archive: " + ", ".join(missing), beneath
    why = _unstackable(KINDS[letter], beneath, deep) or _scoped(over, above, facing)
    theirs = (
        []
        if persons
        else list(
            dict.fromkeys(
                line["parent"]
                for line in beneath.values()
                if line is not None and line["parent"] and line["owner"] == HIS
            )
        )
    )
    return why or (
        f"{theirs[0]} is a stack of the person's, and only the person writes it again" if theirs else ""
    ), beneath


LONGEST = 4000  # characters of a label's sentence, at most: a frame has room for the line left at the door
BUSY = "another act was writing this home, so nothing was {}: try again in a moment"


def _marked(
    folder: Path,
    letter: str,
    whose: str,
    text: str,
    lines: list[str],
    anchors: list[str],
    beneath: dict,
    day: str,
    model: str,
) -> dict:
    """`mark`, from the choice of its key on, with the home's lock held. The key is the next of its
    letter after every key the pages hold, and every key struck: a row written by hand since the
    index was made has its key already, and a struck key is never given again."""
    taken = [int(label["id"][1:]) for label in labels(folder) if label["id"][0] == letter]
    taken += [int(k[1:]) for k in struck(folder) if re.fullmatch(letter + r"\d+", k)]
    key = f"{letter}{max(taken, default=0) + 1}"
    page = within(folder, "labels", f"{day}.md")
    before = _sources(folder)  # how the plain files a build reads stood before this mark: see `_label_added`
    page.parent.mkdir(parents=True, exist_ok=True)
    if not page.exists():
        page.write_text(
            f"# Labels marked on {day}\n\nEach row is one sentence about a stretch of the record and "
            "the ids it rests on: messages, or other labels, each with a mark of its sentence as it stood. "
            "Strike any row; the store follows at its next build.\n\n"
            "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n",
            encoding="utf-8",
        )
    cell = [f"`{line}@{digest(beneath[line]['text'])}`" for line in lines] + [f"`{a}`" for a in anchors]
    with open(page, "a", encoding="utf-8") as handle:
        handle.write(f"| {key} | {text} | {whose} | {', '.join(cell)} |\n")
    if model:
        _signed(folder, key, text, model)
    _known(folder, [f"{key}@{digest(text)}"])  # marked through the door: no build takes it for one that arrived
    # The new row is written first: were the act cut short here, both stacks would stand in the
    # pages and nothing would be lost. Only a misaligned stack gets this far (see _unstackable).
    replaced = list(dict.fromkeys(beneath[line]["parent"] for line in lines if beneath[line]["parent"]))
    for old in replaced:
        _struck_out(folder, old, f"written again as {key}")
    if lines or replaced or not _label_added(folder, before, key):
        build(folder)
    return {
        "written": True,
        "id": key,
        "page": str(page),
        "anchors": anchors,
        "beneath": lines,
        "replaced": replaced,
        "model": model,
    }


def _unstackable(kind: str, beneath: dict, deep: list[str]) -> str:
    """The sentence that refuses a stack, or none: `beneath` is each label named as a line, by
    its key, as the store holds it (nothing where it holds none) with the state of the stack
    above it (`above`), and `deep` those of them that stand over stacks already.

    A line beneath a misaligned stack is not refused: the new stack takes that stack's place.
    A stack that is unresolved has lost a message and none of its lines, so it is still the
    stack above them."""
    gone = [key for key, line in beneath.items() if line is None]
    if gone:
        return "no such label: " + ", ".join(gone)
    if beneath and kind == "next":
        return "a line left at the door rests on messages alone, never on labels"
    other = [key for key, line in beneath.items() if line["kind"] != kind]
    if other:
        return "a stack holds labels of its own kind alone, and of another kind here: " + ", ".join(other)
    for key, line in beneath.items():
        if line["parent"] and line["above"] != "misaligned":
            return f"{key} already stands beneath {line['parent']}, and a line stands beneath one stack alone"
        if line["parent"] in beneath:
            return (
                f"{line['parent']} is misaligned and this stack would take its place, "
                "so it cannot also stand beneath it"
            )
    if deep:
        return f"{deep[0]} already stands over stacks, and stacking goes no deeper than that"
    return ""


def _scoped(over: list[dict], above: list[dict], facing: str) -> str:
    """The sentence that refuses a stack for the layer it would reach into, or none: `over` is
    every line it would stand over, at any depth, and `above` each misaligned stack it would take
    the place of. Reframing is a model's own to do: it stands over the person's lines, its own and
    those of no known model, and writes again only a stack of its own."""
    for line in over:
        if foreign(line, facing):
            return (
                f"{line['id']} was written by another model, {line['model']}, and a stack stands over the person's "
                "lines, its own model's and those of no known model alone"
            )
    for stack in above:
        if foreign(stack, facing):
            return (
                f"{stack['id']} is a stack of another model's, {stack['model']}, "
                "and is written again by that model alone"
            )
    return ""


def reached(folder: Path, verb: str, ids: list[str]) -> None:
    """One plain line for a pull through the door: when, by which verb, which ids. Nothing of
    what was said is in it. It is what cooling will need: what keeps being pulled stays near."""
    folder.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    with open(within(folder, "reached.jsonl"), "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": now, "verb": verb, "ids": ids}) + "\n")


def strike(folder: Path, token: str, why: str = "") -> dict:
    """Remove a message, a label or a whole session (`session:<id>`) for good: from the archive,
    from its label page, from the hand-over's words, from the log of what was pulled, from the
    notes of what looked like a key, and from the database; a whole session also from the small
    files that name sessions (welcomed, told, there) and from the markers of its transcripts. The
    token stays in struck.txt so that a transcript which still holds the message cannot bring it
    back; a whole session's strike also keeps there the whole id of every message it took, so that
    a transcript of any other name that repeats them (a fork, a resume) brings none of them back.
    An id that is no name (record.ident) is refused, and nothing is written. An id of eight
    characters that two messages share strikes neither: the answer names both whole ids, and
    either is struck by its own. One strike at a time is made in a home, under the archive's lock
    (see `_locked`); one that cannot have it within WAIT seconds strikes nothing, and says so.

    What a strike cannot reach: the harness's own transcript, an earlier second copy or a backup,
    and the history of a repository that holds the home (see REACH)."""
    token = token.strip().strip("`")
    if not token:
        return {"struck": False, "why": "nothing named"}
    if not folder.is_dir():  # a home not made yet holds nothing to strike, and is not made by striking
        return {"struck": False, "why": "nothing is kept there yet"}
    if re.fullmatch(r"[0-9a-f]{8}\+\d+", token):
        if not matches(folder, token[:8]):
            return {
                "struck": False,
                "matched": False,
                "why": f"nothing in this home is named {token}, so nothing was struck",
            }
        return {"struck": False, "why": f"a pasted text is struck with the message it came in: strike {token[:8]}"}
    record.ident(token[len("session:") :] if token.lower().startswith("session:") else token)  # one line of struck.txt
    token = kept_form(token)
    if not matches(folder, token):
        return {
            "struck": False,
            "matched": False,
            "why": f"nothing in this home is named {token}, so nothing was struck",
        }
    twins = (
        sorted({row["uuid"] for row in _archived(folder) if row["id"] == token})
        if re.fullmatch(r"[0-9a-f]{8}", token)
        else []
    )
    if len(twins) > 1:
        named_ = ", ".join(twins[:-1]) + " and " + twins[-1]
        return {
            "struck": False,
            "twins": twins,
            "why": f"{token} names {'two' if len(twins) == 2 else len(twins)} messages, "
            f"{named_}, so nothing was struck: strike the one you mean by its whole id",
        }
    held = _locked(folder)
    if held is None:
        return {"struck": False, "why": BUSY.format("struck")}
    try:
        out = _struck_out(folder, token, why)
        build(folder)
    finally:
        _unlocked(folder, held)
    taken = out.pop("ids")
    resting = [
        label["id"] for label in labels(folder) if any(anchor.split("+")[0] in taken for anchor in label["anchors"])
    ]  # left as they are, and named
    return {"struck": True, "token": token, **out, "resting": resting}


def kept_form(token: str) -> str:
    """A token to strike, in the form the home keeps what it names: a session by the first eight
    characters of its id, as the archive names it (the full id the harness gives is cut to
    them), and a label's key in capitals."""
    token = token.strip().strip("`")
    if token.lower().startswith("session:"):
        return "session:" + token[len("session:") :].strip()[:8]
    return token.upper() if KEY.fullmatch(token.upper()) else token


def matches(folder: Path, token: str) -> bool:
    """Whether anything the home keeps is named by this token: a message of the archive (by its
    id or its whole id), a session of it, or a label; or, for a session, a line of the small files
    that name sessions, a marker of its transcripts, or any hand-over words page, which may give a
    message of that session the archive does not hold yet (see `_cleared`)."""
    gone = {token}
    if any(_is_struck(row, gone) for row in _archived(folder)) or any(label["id"] == token for label in labels(folder)):
        return True
    if not token.startswith("session:"):
        return False
    if any(within(folder).glob("*.words.md")):
        return True
    session = token[len("session:") :]
    for name in BY_SESSION + (MARKERS,):
        try:
            lines = lines_of(within(folder, name).read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
        test = _marker_of if name == MARKERS else _of_session
        if any(test(line, session) for line in lines):
            return True
    return False


REACH = (
    "A strike cannot reach the harness's own transcript, an earlier second copy or a backup, or the history of a "
    "repository that holds this home."
)
# The small files of a home that name a session at the head of a line, by its id.
BY_SESSION = ("welcomed.txt", "told.txt", "there.txt")
# A line of a hand-over's words page that gives a message (see crossing/handover.py), and the one
# that names what a transcript did not hold.
WORDS = re.compile(r"^- `([0-9a-f]{8})`, the (?:person|session): ")
MISSING = "Named by a label and not in this transcript: "


def _rewritten(folder: Path, name: str, gone) -> bool:
    """A small plain file of the home with the lines `gone` names taken out, written whole beside
    itself and put in its place; nothing where it is not there. Gives whether a line went."""
    path = within(folder, name)
    if not path.is_file():
        return False
    lines = record.ended(path.read_text(encoding="utf-8", errors="surrogateescape"))
    kept = [line for line in lines if not gone(line)]
    if len(kept) == len(lines):
        return False
    fresh = within(folder, name + ".new")
    fresh.write_text("".join(kept), encoding="utf-8", errors="surrogateescape")
    os.replace(fresh, path)
    return True


def _of_session(line: str, session: str) -> bool:
    """Whether a line of welcomed, told or there names this session first: by its id, or by the
    archive's name for it, the id's first eight characters."""
    head = (line.split() or [""])[0]
    return head == session or head[:8] == session


def _marker_of(line: str, session: str) -> bool:
    """Whether a line of markers.jsonl is the marker of a transcript of this session, as the archive
    names a session by its transcript."""
    try:
        mark = json.loads(line)
    except ValueError:
        return False
    return (
        isinstance(mark, dict)
        and isinstance(mark.get("path"), str)
        and Path(mark["path"].split("#")[0]).stem[:8] == session
    )


def _unworded(folder: Path, ids: set[str]) -> tuple[list[str], list[str]]:
    """Take these messages out of every hand-over words page of the home (`*.words.md`): the
    pages mended line by line, and those that could not be and went whole.

    A page as crossing/handover.py writes it gives each message on a line of its own, and after
    them, at most, the line that names what was missing. A page with any other line after its
    first message (a message whose words ran over more than one line, or a page edited by hand)
    cannot be mended line by line, nor can one that still names a struck id once mended: that
    page goes whole, as the next hand-over makes it again from the record."""
    mended, dropped = [], []
    for page in sorted(within(folder).glob("*.words.md")):
        page = within(folder, page.name)
        lines = lines_of(page.read_text(encoding="utf-8", errors="surrogateescape"))
        if not any(each in line for line in lines for each in ids):
            continue
        first = next((n for n, line in enumerate(lines) if WORDS.match(line)), len(lines))
        sound = all(WORDS.match(line) or not line.strip() or line.startswith(MISSING) for line in lines[first:])
        out = []
        for line in lines:
            found = WORDS.match(line)
            if found and found.group(1) in ids:
                continue
            if line.startswith(MISSING):
                left = [each for each in re.findall(r"`([^`]+)`", line) if each not in ids]
                line = MISSING + ", ".join(f"`{each}`" for each in left) + "." if left else ""
            out.append(line)
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(out)).rstrip("\n") + "\n"
        if sound and not any(each in text for each in ids):
            _replaced(folder, page, text)
            mended.append(page.name)
        else:
            page.unlink()
            dropped.append(page.name)
    return mended, dropped


def _struck_out(folder: Path, token: str, why: str = "") -> dict:
    """Note a token among the struck and take what it names out of every plain file: how many
    lines left the archive and the label pages (`removed`), and the hand-over words pages mended
    (`mended`) and gone whole (`dropped`), or, for a whole session, every one of them gone whole
    (`cleared`). The database is not built here: whoever strikes builds
    it once, when the plain files stand as they are to stand.

    A line of the archive that is no message is left as it is, as a build passes over it: a
    strike that stopped there would have noted the token and left the words in the archive. A
    line that holds a byte that is no text is read for what it names all the same, and taken out
    where it is struck; one that is kept is written back as it was. Every file this rewrites is
    written whole beside itself and then put in its place (see `_replaced`): the caller holds the
    home's lock."""
    with open(within(folder, "struck.txt"), "a", encoding="utf-8") as handle:
        handle.write(token + (f"  # {why}" if why else "") + "\n")
    gone, removed, ids, wholes = struck(folder), 0, {token}, []

    def out(line: str) -> dict | None:
        """The message on this line of the archive, if it is struck; else nothing."""
        try:
            row = json.loads(line)
        except ValueError:
            return None
        return row if _said(row) and _is_struck(row, gone) else None

    for page in said_pages(folder):
        lines = lines_of(_text(page))
        taken = [out(line) for line in lines]
        if any(taken):
            removed += sum(1 for was in taken if was)
            ids |= {was["id"] for was in taken if was}
            wholes += [was["uuid"] for was in taken if was]
            _replaced(folder, page, "".join(line + "\n" for line, was in zip(lines, taken) if not was))
    if token.startswith("session:") and wholes:  # by each whole id: a transcript of another name brings none back
        with open(within(folder, "struck.txt"), "a", encoding="utf-8") as handle:
            handle.write("".join(f"{uuid}  # of {token}\n" for uuid in dict.fromkeys(wholes) if record.nameable(uuid)))
    for page in pages(folder):
        lines = record.ended(_text(page))
        kept = [line for line in lines if not ((m := ROW.match(line.rstrip("\n"))) and m.group(1) in gone)]
        if len(kept) != len(lines):
            removed += len(lines) - len(kept)
            _replaced(folder, page, "".join(kept))
    signs = within(folder, MODELS)
    if signs.exists():  # a struck label's model goes with it, and is not counted as a line of its own
        lines = record.ended(_text(signs))
        kept = [line for line in lines if not ((m := SIGNED.match(line.split("#")[0].strip())) and m.group(1) in gone)]
        if len(kept) != len(lines):
            _replaced(folder, signs, "".join(kept))
    log = within(folder, "reached.jsonl")
    if log.exists():  # what was pulled is a record too: a struck id leaves it
        kept = []
        for line in lines_of(_text(log)):
            pull = _pull(line) if _whole(line) else None
            if pull is None:  # a line that is no pull is left as it is, unless it names what was struck
                kept += [line + "\n"] if line.strip() and not any(i in line for i in ids) else []
                continue
            pull = {**pull, "ids": [i for i in pull["ids"] if i.split("+")[0] not in ids]}
            kept += [json.dumps(pull) + "\n"] if pull["ids"] else []
        _replaced(folder, log, "".join(kept))
    # The ids of the messages struck, as a page of words or a note names them: eight characters.
    said = {each[:8] for each in ids if re.match(r"[0-9a-f]{8}(?![0-9a-f])", each)}
    _rewritten(folder, FLAGGED, lambda line: line.strip() in said)
    exact = set(wholes) | ({token} if not token.startswith("session:") else set())
    _rewritten(folder, UNHELD, lambda line: line.strip() in exact or (len(token) == 8 and line.strip()[:8] == token))
    if token.startswith("session:"):  # a whole session: the lines that name it, and how far its transcripts were read
        session = token[len("session:") :]
        for name in BY_SESSION:
            _rewritten(folder, name, lambda line: _of_session(line, session))
        _rewritten(folder, MARKERS, lambda line: _marker_of(line, session))
    cleared = _cleared(folder) if token.startswith("session:") else []
    mended, dropped = _unworded(folder, said) if said and not cleared else ([], [])
    return {"removed": removed, "mended": mended, "dropped": dropped, "cleared": cleared, "ids": said}


def _cleared(folder: Path) -> list[str]:
    """Every hand-over words page of the home (`*.words.md`), taken away whole, for a session's
    strike: a page may give a message of that session the archive does not hold yet, which no id
    struck names. The next hand-over makes the page again from the record. Gives their names."""
    gone = []
    for page in sorted(within(folder).glob("*.words.md")):
        within(folder, page.name).unlink()
        gone.append(page.name)
    return gone


def _pull(line: str) -> dict | None:
    """A line of the log of what was pulled, where it is one: an object whose ids are strings."""
    try:
        pull = json.loads(line)
    except ValueError:
        return None
    ok = isinstance(pull, dict) and isinstance(pull.get("ids"), list) and all(isinstance(i, str) for i in pull["ids"])
    return pull if ok else None
