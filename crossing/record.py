"""Write the counted part of a cut's record: counts and pointers, and no text of either voice."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat
import sys
from datetime import date
from pathlib import Path

from .count import RUN, SHORT

try:
    import fcntl as _fcntl
except ImportError:  # Windows: `resolve` spells a path as the disk does already (see `spelled`)
    _fcntl = None

LEAST = 10  # how many of the least-held messages of a voice the page lists; the sidecar lists all
# The settings that name where the plugin keeps what it keeps. A project's own settings can set a
# session's environment, so none of them is followed where it names a place inside the project.
SETTINGS = ("CROSSING_HOME", "CROSSING_HOMES", "CROSSING_OURS", "CROSSING_SWITCHED")
WINDOWS = os.name == "nt"  # where a file's mode says nothing of who may read it


class Linked(Exception):
    """A file or a folder of a home that is a link, or a path that would lead out of the home.
    Nothing is read or written through it."""


class Unnamed(Linked):
    """An id that would become part of a file's name, or a line of a home's small files, and is
    not one that can: refused as a link is, and nothing is written for it."""


# What a session's id, a label page's day or any other id may be where it becomes part of a path:
# letters, digits, `-` and `_`, and no longer than a name needs to be.
NAME = re.compile(r"[A-Za-z0-9_-]{1,128}")


def ident(value: object) -> str:
    """The one check for an id that becomes part of a path (a page of the archive, a cut's
    record, a session's live file, a label page) or a line of a home's small files (welcomed,
    told, there): the id as it is, or `Unnamed`. A dot, a slash, a space, a line break or a
    length no id has would name another file, or another line."""
    if isinstance(value, str) and NAME.fullmatch(value):
        return value
    raise Unnamed(f"an id that cannot name a file: {str(value)[:80]!r}")


def lines_of(text: str) -> list[str]:
    """A plain file's lines, broken at line feeds alone. str.splitlines() also breaks at U+2028,
    U+2029 and the other separators a message, a reason or a path may hold, which the plugin
    writes as they are: a line of the archive, a row of a label page or a line of a home's small
    files would be cut in two, and each half read as a line of its own."""
    found = text.split("\n")
    if found[-1] == "":
        found.pop()
    return [line[:-1] if line.endswith("\r") else line for line in found]


_undecoded: set[str] = set()  # the files a line of which could not be read as text, logged once each a process


def decoded(data: bytes, name: object = "") -> list[str]:
    """A plain file's lines from its bytes, broken at line feeds alone (see `lines_of`), each read
    as UTF-8 on its own. A line that is no UTF-8 (a byte cut short, a file written by another hand)
    is read as an empty line, which every reader passes over, so that one damaged line costs that
    line alone and no reading stops at it; the error log says so once a process for each file
    (`name`). The file itself is left as it is."""
    found = data.split(b"\n")
    if found[-1] == b"":
        found.pop()
    lines = []
    for line in found:
        try:
            lines.append(line[:-1].decode("utf-8") if line.endswith(b"\r") else line.decode("utf-8"))
        except UnicodeDecodeError:
            lines.append("")
            passed(name)
    return lines


def passed(name: object) -> None:
    """One line in the error log, once a process for each file, that a line of it could not be
    read as text and was passed over."""
    if str(name) not in _undecoded:
        _undecoded.add(str(name))
        log(f"passed over: a line of {name} that cannot be read as text")


def lines_in(path: Path) -> list[str]:
    """The lines of a plain file of a home, each read on its own (see `decoded`): the one way the
    plugin reads a home's files as lines. A file that is not there, or cannot be opened, raises
    OSError as before."""
    return decoded(path.read_bytes(), path)


def add(path: Path, text: str, head: str = "") -> None:
    """Append whole lines (`text`, each ending in a line feed) to a plain file: the one way the
    plugin adds a line to a file of a home, a log or the person's record. Where the file's last line
    has no line feed (an editor, a checkout or a sync left it so), the line feed comes first, so that
    the last line and the first new one stay two lines; where the file is new or empty, `head` comes
    first. A file that cannot be opened raises OSError as before."""
    with open(path, "a", encoding="utf-8") as handle:
        if handle.tell():
            with open(path, "rb") as seen:
                seen.seek(-1, os.SEEK_END)
                if seen.read(1) != b"\n":
                    handle.write("\n")
        elif head:
            handle.write(head)
        handle.write(text)


def logged(path: Path, text: str) -> None:
    """Append to one of the plugin's own logs (see `add`), and narrow it to its owner alone where an
    earlier make left it readable by other accounts (0644): a file the process makes is its owner's
    already (see `private`), and one made before is narrowed the next time it is written. On Windows
    a mode says nothing, and nothing is done."""
    add(path, text)
    mode = stat.S_IMODE(path.stat().st_mode)
    if not WINDOWS and mode & 0o077:
        os.chmod(path, mode & 0o700)


def undecodable(path: Path) -> int:
    """How many lines of a file cannot be read as text; nought for a file that cannot be opened."""
    try:
        data = path.read_bytes()
    except OSError:
        return 0
    bad = 0
    for line in data.split(b"\n"):
        try:
            line.decode("utf-8")
        except UnicodeDecodeError:
            bad += 1
    return bad


def ended(text: str) -> list[str]:
    """A plain file's lines with their line feeds, broken at line feeds alone (see `lines_of`), so
    that a file put together again from them is the same file."""
    found = [line + "\n" for line in text.split("\n")]
    found[-1] = found[-1][:-1]
    return [line for line in found if line]


def nameable(value: object) -> bool:
    """Whether an id passes `ident`: an id that does not is left out of every line it would be."""
    try:
        ident(value)
    except Unnamed:
        return False
    return True


def within(folder: Path, *names: str) -> Path:
    """The path of a file of the home `folder`, by its names below it; refused (`Linked`) where
    any piece of it below the home is a link, or where it would lie outside the home. Every read
    and write the plugin makes inside a home goes through this, so that a link a repository
    ships in its folder, or one put there since, leads nowhere. The home folder itself may be a
    link: whether it is believed is the person's switch to say (see store.kept)."""
    path, step = folder.joinpath(*names), folder
    for name in Path(*names).parts:
        step = step / name
        if step.is_symlink():
            raise Linked(f"a file of the home is a link: {step}")
    root, found = folder.resolve(), path.resolve()
    if found != root and root not in found.parents:
        raise Linked(f"a path leads out of the home: {path}")
    return path


def sound(folder: Path) -> None:
    """Every file and folder of a home, through `within`: a home with a link anywhere below it is
    refused whole, before anything of it is read or written, so that an act refused at its last
    file has not written its first."""
    for path in sorted(folder.rglob("*")):
        within(folder, *path.relative_to(folder).parts)


def private() -> None:
    """From here on, every folder this process makes is its owner's alone (0700) and every file it
    writes too (0600): what was said is not for the other accounts of the computer. Each entry of
    the plugin calls this first. On Windows a mode says nothing, and nothing is done."""
    if not WINDOWS:
        os.umask(0o077)


def narrow(folder: Path) -> int:
    """A home made wider than its owner alone, as homes once were (0755, and 0644 for their
    files), narrowed file by file: what the group and the other accounts could read or enter is
    taken away, and nothing else changes. No link is followed: a home with one below it is
    refused whole (see `sound`), and a home folder that is a link is left as it is. Gives how
    many files and folders were narrowed; nothing on Windows."""
    if WINDOWS or folder.is_symlink() or not folder.is_dir():
        return 0
    sound(folder)
    narrowed = 0
    for path in [folder, *sorted(folder.rglob("*"))]:
        mode = stat.S_IMODE(path.lstat().st_mode)
        if mode & 0o077:
            os.chmod(path, mode & 0o700)
            narrowed += 1
    return narrowed


def own() -> Path:
    """The person's own folder, as the system's record of their account gives it, never as an
    environment variable says it: a project's settings can set a session's environment, HOME
    among it, and a folder of its own making would then hold a record of switches or a home
    that was never the person's. On Windows it is the user profile as the shell's known folder
    gives it (SHGetKnownFolderPath), which reads no variable. Only where neither can be had (an
    account with no entry, or a Windows that will not say) is it the folder Python's own rule
    gives, and the error log says so once a process. The plugin's explicit settings
    (CROSSING_HOMES, CROSSING_SWITCHED, CROSSING_OURS, CROSSING_LIVE) still name other places,
    under the rule of `astray`."""
    found = _windows_profile() if WINDOWS else _account()
    if found:
        return Path(found)
    if "own" not in _said_once:
        _said_once.add("own")
        log("the person's own folder could not be read from the account; the home Python names was used")
    return Path.home()


_said_once: set[str] = set()


def _account() -> str:
    """The account's own folder in the system's record of accounts, or nothing."""
    try:
        import pwd

        return pwd.getpwuid(os.getuid()).pw_dir
    except (ImportError, KeyError):
        return ""


def _windows_profile(libraries=None) -> str:
    """The user profile as Windows gives it by its known folder (FOLDERID_Profile,
    5E6C858F-0E22-4760-9AFE-EA3317B67173), or nothing. `libraries` is (shell32, ole32), for a
    test; else the system's own. ctypes is loaded here alone: no other entry needs it."""
    import ctypes

    class Guid(ctypes.Structure):
        _fields_ = [
            ("Data1", ctypes.c_uint32),
            ("Data2", ctypes.c_uint16),
            ("Data3", ctypes.c_uint16),
            ("Data4", ctypes.c_ubyte * 8),
        ]

    profile = Guid(0x5E6C858F, 0x0E22, 0x4760, (ctypes.c_ubyte * 8)(0x9A, 0xFE, 0xEA, 0x33, 0x17, 0xB6, 0x71, 0x73))
    try:
        shell32, ole32 = libraries or (ctypes.windll.shell32, ctypes.windll.ole32)  # type: ignore[attr-defined]
        found = ctypes.c_wchar_p()
        if shell32.SHGetKnownFolderPath(ctypes.byref(profile), 0, None, ctypes.byref(found)) != 0:
            return ""
        try:
            return found.value or ""
        finally:
            ole32.CoTaskMemFree(found)
    except (AttributeError, OSError):
        return ""


def terminal() -> bool:
    """Whether the door stands at a real terminal: its input and its output are both one. The
    person's own shell is; a session's shell, the hooks and the door's server are not."""
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


ROOT = Path(__file__).resolve().parent.parent  # the plugin's own folder


def from_plugin() -> bool:
    """Whether the process was started by the plugin's own hooks or module: the harness names the
    plugin's folder in CLAUDE_PLUGIN_ROOT for a hook, and the module and the hooks name it for
    the door they start. A session's shell is not given it. It is a check, not a wall: a shell
    that sets it itself passes, which is why the hooks module also refuses a shell command that
    calls the door so (hooks/crossings.ts)."""
    given = os.environ.get("CLAUDE_PLUGIN_ROOT")
    try:
        return bool(given) and os.path.samefile(given, ROOT)
    except OSError:
        return False


def attended() -> bool:
    """Whether the session is one a person sits in. The harness names how it was started in
    CLAUDE_CODE_ENTRYPOINT, which a hook's process inherits, and so does every process the hooks
    module starts: `cli` for a session in the terminal, `sdk-cli` for `claude -p`, `sdk-ts` or
    `sdk-py` for the SDK. A `cli` inherited from the session a headless one was started in is
    turned into `sdk-cli` by the harness itself. Any other name, or none, is not taken for a
    person: other tools start headless sessions in a project, and what such a session is given
    or says is not the person's."""
    return os.environ.get("CLAUDE_CODE_ENTRYPOINT") == "cli"


def data() -> Path:
    """The plugin's own data folder, which holds its logs and no home."""
    folder = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or own() / ".claude" / "crossing")
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def log(line: str) -> None:
    """One line in the plugin's error log. A log that cannot be written is no reason to stop."""
    try:
        logged(data() / "errors.log", line + "\n")
    except OSError:
        pass


def refused(err: Exception) -> None:
    """One line in the plugin's error log for a link, an id or a setting that was refused."""
    log(f"refused: {err}")


_told: set[tuple[str, str]] = set()  # the settings refused in this process, logged once each


def astray(cwd: Path) -> str | None:
    """The first of the plugin's settings (SETTINGS) that names no absolute path, or whose place
    lies inside the project `cwd` stands in (its top: see `located`); or nothing. A repository can
    ship a settings file that sets a session's environment, and so a consent record or a home of
    its own making, named by one of these: such a setting is not followed, the project is one
    where Crossings was never switched on, and the error log says so once a process. A relative
    path is read from wherever a process happens to stand, so none is taken at all."""
    top = _top(cwd.resolve())
    for name in SETTINGS:
        value = os.environ.get(name)
        if not value:
            continue
        if not os.path.isabs(value):
            why = f"the setting {name} names no absolute path: {value[:120]!r}"
        elif lies_in(Path(value), top):
            why = f"the setting {name} names a place inside the project: {Path(value).resolve()}"
        else:
            continue
        if (name, why) not in _told:
            _told.add((name, why))
            refused(Exception(why))
        return name
    return None


def lies_in(path: Path, top: Path) -> bool:
    """Whether `path`, its links followed, lies at or below the folder `top`, decided by the files
    themselves: each folder of it that is there, from itself up, is compared with `top` by its
    device and its inode (os.path.samefile). Its text is not compared, so neither the case of
    its letters, on a disk that does not tell them apart, nor a link or a `..` can make a place
    inside the project read as one outside it."""
    for folder in (path.resolve(), *path.resolve().parents):
        try:
            if os.path.samefile(folder, top):
                return True
        except OSError:  # not there (yet): its parents decide
            continue
    return False


def homes() -> Path:
    """Where the homes of projects with no `crossings/` folder of their own lie: the folder
    CROSSING_HOMES names, else one under the person's own home."""
    return Path(os.environ.get("CROSSING_HOMES") or own() / ".claude" / "crossing" / "homes")


def names(folder: Path, project: Path) -> bool:
    """Whether the home at `folder` says, in its `project` file, that it is the home of the
    project at exactly this path."""
    try:
        return "\n".join(lines_in(within(folder, "project"))).rstrip("\n") == str(project)
    except Linked as err:
        refused(err)
        return False
    except OSError:
        return False


def outside(project: Path) -> Path:
    """The home of the project at this resolved path, where it has none of its own: a folder
    under `homes()`, named by the path and by eight characters of its digest, so that two paths
    that read alike (`a-b`, `a_b`, `a.b`) never come to one home. A home made before the digest
    was part of the name is still this project's where its `project` file names exactly this
    path; one that names another path is not."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(project)).strip("-") or "project"
    if names(homes() / slug, project):
        return homes() / slug
    return homes() / f"{slug}-{hashlib.sha256(str(project).encode('utf-8')).hexdigest()[:8]}"


def located(cwd: Path) -> tuple[Path, Path, bool]:
    """The home of the project `cwd` stands in; the top of that project, by its resolved path;
    and whether the home lies outside the project.

    The top is the top of the project's repository (a folder that holds `.git`, looked for no
    further up than the person's home), or `cwd` itself where it stands in no repository.

    A project that has a `crossings/` folder keeps its home there, where the person can read
    it beside the work. The folder is looked for upward from `cwd`, and never above the top: in
    a repository, a shell that stands in `crossings/` itself, or anywhere inside the project,
    means that project's home; in no repository, only `cwd`'s own `crossings/` is.

    Any other project has its home outside it, named by the path of its top: nothing that was
    said there, and nothing of how the plugin is set there, then lies inside the project. Links
    in `cwd` are followed first, so that every piece of the plugin comes to one home by
    whichever path it was told.

    Where the home is found says nothing of whether it is believed: that is the person's
    switch, kept outside every project (see store.kept). A `crossings` that is a link, to a
    folder or to nothing, is found as the project's home all the same, so that no home is made
    outside the project in its place: no home is believed or switched on through it (see
    store.kept and store.switch).

    The path is taken as the disk spells it (see `spelled`): on a disk that does not tell the
    case of letters apart, one folder is one project, with one home, by whichever spelling it
    was reached."""
    cwd = spelled(cwd.resolve())
    top = _top(cwd)
    chain = (cwd, *cwd.parents)
    for folder in chain[: chain.index(top) + 1]:
        if (folder / "crossings").is_dir() or (folder / "crossings").is_symlink():
            return folder / "crossings", top, False
    return outside(top), top, True


def spelled(path: Path) -> Path:
    """A path as the disk spells it. On a disk that does not tell the case of letters apart,
    `/a/Tern` and `/a/tern` name one folder, and this gives the one spelling of it whichever was
    given: the files decide, never the text. The deepest folder of the path that is there is
    opened and the system is asked for its own path (F_GETPATH, on macOS); what lies below it, not
    there yet, is kept as it was given. Where the system cannot say (another system, or a folder
    that cannot be opened), the path is as it was given: on Windows `resolve` spells it as the disk
    does already, and elsewhere a disk tells the case of letters apart."""
    path = Path(os.path.abspath(path))
    getpath = getattr(_fcntl, "F_GETPATH", None) if _fcntl is not None else None
    there, below = path, []
    while not there.exists() and there != there.parent:
        below.insert(0, there.name)
        there = there.parent
    if getpath is None:
        return path
    try:
        handle = os.open(there, os.O_RDONLY)
        try:
            found = _fcntl.fcntl(handle, getpath, bytes(1024)).split(b"\0", 1)[0]
        finally:
            os.close(handle)
    except OSError:
        return path
    named = Path(os.fsdecode(found))
    return named.joinpath(*below) if _same(named, there) else path


def _same(one: Path, other: Path) -> bool:
    """Whether two paths name one folder or file, by the files. A path that names none (gone, or
    holding a NUL, as a damaged line of the person's record may) is the same as nothing."""
    try:
        return os.path.samefile(one, other)
    except (OSError, ValueError):
        return False


def _top(cwd: Path) -> Path:
    """The top of the project the resolved folder `cwd` stands in: the nearest folder upward that
    holds `.git`, looked for no further up than the person's home; or `cwd` itself."""
    house = own().resolve()
    for folder in (cwd, *cwd.parents):
        if (folder / ".git").exists():
            return folder
        if folder == house:
            break
    return cwd


def place(cwd: Path) -> tuple[Path, Path | None]:
    """The home of the project `cwd` stands in; and, where that home lies outside the project,
    the project's own folder beside it. See `located`."""
    folder, top, out = located(cwd)
    return folder, top if out else None


def home(cwd: Path) -> Path:
    """Where the project `cwd` stands in keeps what was said: see `place`. This is the one rule;
    nothing else in the plugin puts a home's path together."""
    return place(cwd)[0]


def many(n: int, one: str, more: str = "", grouped: bool = False) -> str:
    """A count with its noun, as a sentence says it: one message, two messages, no messages as 0
    messages; `more` where the noun takes more than an s, and `grouped` for a count written with
    its thousands apart (1,000)."""
    count = f"{n:,}" if grouped else f"{n}"
    return f"{count} {one if n == 1 else more or one + 's'}"


def share(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "none stood"


def _voice_lines(name: str, v: dict) -> list[str]:
    least = sorted(v["pointers"], key=lambda p: (p["held"] / p["chars"] if p["chars"] else 1, -p["chars"]))
    none = sum(1 for p in v["pointers"] if not p["held"])
    lines = [
        f"| {name} | {v['messages']} | {v['whole']} | {share(v['covered'], v['chars'])} "
        f"| {v['sentences_found']} of {v['sentences']} | {none} |",
    ]
    return lines, [
        f"{p.get('id') or 'no id'} (line {p['line']}, {many(p['chars'], 'character')}, "
        f"{share(p['held'], p['chars'])} held)"
        for p in least[:LEAST]
    ]


def _figure(value) -> int | float | None:
    """A figure of a cut's count, where it is a number (and no truth value); else none: a figure of
    another shape leaves the page written without it."""
    return value if type(value) in (int, float) else None


def page(counted: dict, session_id: str, transcript: Path, on: str) -> str:
    from crossing.store import clean  # here: the store reads this file. What the harness gave is shown cleaned

    person, own = counted["person"], counted["session"]
    trigger, transcript = clean(counted["trigger"] or "trigger not given"), clean(transcript)
    (row_p,), least_p = _voice_lines("the person's", person)
    (row_s,), least_s = _voice_lines("the session's", own)
    before, after, took = (_figure(counted.get(name)) for name in ("tokens_before", "tokens_after", "cut_ms"))
    size = "not given by the harness"
    if before:
        size = f"{before:,} tokens before" + (f", {after:,} after" if after is not None else "")
        if took:
            seconds = f"{took / 1000:.0f}"
            size += f"; the cut took {seconds} second{'' if seconds == '1' else 's'}"
    voices = person["chars"] + own["chars"]
    record = voices + counted["tool_call_chars"] + counted["tool_result_chars"]
    unfinished = (
        ""
        if person["finished"] and own["finished"]
        else (
            "\n**Not all of it was counted:** the count ran out of its time and stopped; the numbers below "
            "cover only the messages reached.\n"
        )
    )
    return f"""# A cut, counted

Counted on {on} by the crossing plugin from the session's transcript, by script. No model was
called, and this page holds no text of either voice: counts and pointers only.
{unfinished}
| | |
| --- | --- |
| Kind | context compaction, {trigger} |
| Size | {size} |
| The summary | {summed(counted)} |
| Session | `{session_id}` |
| The record itself | `{transcript}`, cut {counted["cut"]} of the session, at line {counted["boundary_line"]} |
| What this cut covers | lines {counted["span_starts_after"] + 1} to {counted["boundary_line"] - 1}: \
only what stood since the previous cut, or since the start |

### What the summary holds word for word

| Voice | Messages before the cut | In the summary whole | Of its text, by characters | Sentences | \
Messages with nothing held |
| --- | --- | --- | --- | --- | --- |
{row_p}
{row_s}

The person's messages: {person["typed"]} typed at the prompt, {person["sent_mid_turn"]} sent while a turn ran.
Too short to judge (under {SHORT} characters) and counted as not held: {person["too_short"]} of the person's, \
{own["too_short"]} of the session's.

"Word for word" is the whole claim: a run of {RUN} characters or more that the summary also holds.
A summary can carry a message in other words and get no credit here, and matching words do
not show that anything still rests on them. These numbers say where to look.

### What the record before the cut was made of

The two voices were {share(voices, record)} of it by characters; tool calls and their results were the rest.

### Least held, by pointer

The person's: {"; ".join(least_p) or "none"}.

The session's: {"; ".join(least_s) or "none"}.

Every message's pointer is in the file beside this one.

A message is named by its id; its line is true for this transcript file only, since a fork or a
resume writes a new file with other lines and the same ids.
To read a message back: `python3 crossing/read.py <transcript> <id or line>` from the plugin's
folder. It shows only what was said. The transcript also holds reasoning blocks, tool traffic and
harness notes, so a session does not open that file itself.
"""


def summed(counted: dict) -> str:
    """The summary's length, and how much of it repeats the summary of the cut before, in words."""
    if not counted.get("traced"):
        return "none was handed over"
    chars = counted.get("summary_chars") or 0
    if counted.get("retold") is None:
        return (
            f"{many(chars, 'character', grouped=True)}; no summary of an earlier cut of this session was counted with "
            "its runs, so it is compared with none"
        )
    return (
        f"{many(chars, 'character', grouped=True)}, {share(counted['retold'], chars)} of them repeating the summary "
        f"of cut {counted['cut'] - 1} word for word, in runs of {RUN} characters or more"
    )


# The home's own key for the digests of a summary's runs (see count.runs). It lies beside the words
# themselves, in said/, which a session is not let read: whoever can read it can read what was said.
KEY = ("said", "runs.key")


def runs_key(folder: Path) -> bytes | None:
    """The home's key for the digests of a summary's runs, made the first time it is asked for:
    random, and kept in `said/runs.key`. Nothing where that file is there and holds no key: the
    runs are then not kept, and nothing is compared."""
    path = within(folder, *KEY)
    try:
        held = path.read_text(encoding="ascii").strip()
    except FileNotFoundError:
        path.parent.mkdir(exist_ok=True)
        made = secrets.token_hex(32)
        try:
            with open(path, "x", encoding="ascii") as handle:  # two cuts at once: the second reads the first's
                handle.write(made + "\n")
            return bytes.fromhex(made)
        except FileExistsError:
            return runs_key(folder)
    except (OSError, UnicodeDecodeError):
        return None
    return bytes.fromhex(held) if re.fullmatch(r"[0-9a-f]{64}", held) else None


def keyed(key: bytes) -> str:
    """Which key a sidecar's digests were made with, as the sidecar names it: a digest of the key's
    own, from which the key cannot be found."""
    return hashlib.blake2b(b"which key", key=key, digest_size=4).hexdigest()


def where(folder: Path, session_id: str, ordinal: int) -> Path:
    """The page for one cut, in the home `folder`. The name needs nothing that is known only
    after the count. A session's id that cannot name a file is refused (see `ident`)."""
    return folder / f"{ident(session_id)[:8]}-cut-{ordinal}.md"


HELD = "### What the summary holds word for word"
MADE = "### What the record before the cut was made of"


def honest(text: str, counted: dict) -> str:
    """Where the count has nothing to stand on, the page says so in the table's place."""
    person, own = counted["person"], counted["session"]
    if counted.get("untold"):
        said = (
            "### Not counted\n\nThe record of when Crossings was off in this project is missing, shorter "
            "than it was, or holds a line that cannot be read as a span, so what was said off the record "
            "cannot be told from the rest, and nothing said is listed here.\n\n"
        )
        return text[: text.index(HELD)] + said + text[text.index("Every message's pointer") :]
    if not person["messages"] and not own["messages"]:
        said = (
            "### Not counted\n\nAt the moment of the cut the transcript held no message of either voice in "
            "this stretch. A session that was just forked keeps its conversation in the file it was forked "
            "from, so nothing is counted here and nothing is guessed.\n\n"
        )
        return text[: text.index(HELD)] + said + text[text.index("Every message's pointer") :]
    if not counted.get("traced"):
        said = (
            "### Nothing to compare against\n\nNo summary was handed over for this cut: a plugin answered it "
            "in the harness's place, or the harness gave none. Before it stood "
            f"{many(person['messages'], 'message')} of the person's and {many(own['messages'], 'reply', 'replies')} of "
            "the session's. "
            "How much of them the new context holds was not counted.\n\n"
        )
        return text[: text.index(HELD)] + said + text[text.index(MADE) :]
    return text


def write(counted: dict, folder: Path, session_id: str, transcript: Path, on: str | None = None) -> Path:
    """The page and its sidecar, into the home `folder`. A record makes no home: the folder is
    there already, or nothing is written."""
    on = on or date.today().isoformat()
    path = where(folder, session_id, counted["cut"])
    side = within(folder, str(path.with_suffix(".json").relative_to(folder)))
    within(folder, str(path.relative_to(folder))).write_text(
        honest(page(counted, session_id, transcript, on), counted), encoding="utf-8"
    )
    side.write_text(
        json.dumps({"session_id": session_id, "transcript": str(transcript), "counted_on": on, **counted}, indent=1)
        + "\n",
        encoding="utf-8",
    )
    return path


def read(folder: Path, session_id: str, ordinal: int) -> dict | None:
    side = within(folder, str(where(folder, session_id, ordinal).with_suffix(".json").relative_to(folder)))
    return json.loads(side.read_text(encoding="utf-8")) if side.exists() else None
