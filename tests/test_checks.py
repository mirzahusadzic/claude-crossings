"""What a second review found, each with the test that holds it: places decided by the files
themselves and by the account's own folder, a home named outright believed by the record alone,
the person's verbs kept for the person, what was said while off kept off without its spans file,
the door kept for sessions a person sits in, a strike that says when it matched nothing, an ignore
file for a home inside a repository, a home's files trusted no further than they need be, a folder
that arrives in a project, an index that is no database, a subagent's label left unsigned, a mark
added to the index, and what is shown cleaned of what reorders or hides it. No model, no network.

Run with pytest, or without it:  python3 tests/test_checks.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import pwd
import select
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import as_the_module, ran, set_to, through  # noqa: E402
from test_guards import repository  # noqa: E402
from test_homes import public  # noqa: E402
from test_index import dump, same_as_whole, started  # noqa: E402
from test_off import says  # noqa: E402
from test_reading import reading_the_archive  # noqa: E402
from test_serve import said  # noqa: E402
from test_shipped import inside, logged  # noqa: E402
from test_store import ROWS, A, at_terminal, home, in_person, own_folder, row, started_by, sweep  # noqa: E402

from crossing import door, frame, hook, layer, off, record, second, store  # noqa: E402

ON = "Crossings is on for this project.\n"
NOT_ON = "Crossings is not switched on for this project.\n"
# What the door says, as the person reads it: written out here, so that the words are held too.
PERSONS = (
    "This is the person's to run, from their own terminal or with the plugin's command (/crossings), so nothing "
    "was done.\n"
)
LOST = (
    "The record of when Crossings was off in this project is missing, shorter than it was, or holds a line that "
    "cannot be read as a span, so nothing more is archived here until the person switches Crossings on again."
)
RESTORED = (
    "Crossings is on again for this project. Its record of when Crossings was off had been taken away, cut short or "
    "damaged, so everything said before this moment that was not kept already is kept off the record; what is said "
    "from now on is kept.\n"
)
UNATTENDED = "The door is for sessions a person sits in, and this one is not, so nothing was read."
PASSING = (
    "A crossings/ folder in this project was passed over: Crossings goes on keeping this project's home where you "
    "switched it on, outside the project."
)
IGNORE_SAID = (
    "This project's home lies inside a repository, and its ignore file there does not leave out said/, where "
    "the words are kept: they could be committed with the work."
)
INSIDE = "This home's copy file names a place inside the project, so no second copy was made.\n"


def shell(*argv: str) -> tuple[int, str]:
    """The door as a session's shell runs it: at no terminal, and not called by the plugin."""
    out = io.StringIO()
    with at_terminal(False), contextlib.redirect_stdout(out):
        code = door.main(list(argv))
    return code, out.getvalue()


def at_a_real_terminal(*argv: str, **env: str) -> tuple[int, str]:
    """The door as a process of its own whose input and output are a terminal (a pseudo-terminal
    made here), as the person's own shell runs it."""
    import pty

    master, slave = pty.openpty()
    try:
        started_ = subprocess.Popen(
            [sys.executable, "-I", str(ROOT / "crossing" / "door.py"), *argv],
            stdin=slave,
            stdout=slave,
            stderr=subprocess.PIPE,
            env={**os.environ, **env},
        )
    finally:
        os.close(slave)
    out = b""
    try:
        while select.select([master], [], [], 30)[0]:
            try:
                chunk = os.read(master, 4096)
            except OSError:  # the other end is closed: everything was read
                break
            if not chunk:
                break
            out += chunk
    finally:
        os.close(master)
    started_.wait(timeout=30)
    started_.stderr.close()
    return started_.returncode, out.decode("utf-8").replace("\r\n", "\n")


# --- S1: inside the project is decided by the files ----------------------------------------------------


def test_a_setting_inside_the_project_is_found_by_the_files_whatever_its_letters_or_its_path(tmp_path):
    project = tmp_path / "Tool"
    (project / ".git").mkdir(parents=True)
    shipped = project / "data"
    (shipped / "labels").mkdir(parents=True)
    (shipped / "labels" / "2026-01-01.md").write_text(
        f"| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R1 | A shipped line. | his | `{A}` |\n",
        encoding="utf-8",
    )
    other = tmp_path / "other"
    other.mkdir()
    # The same folder by another spelling, whose text still differs once it is resolved: through the
    # disk's own other path to it (/System/Volumes/Data on a Mac), or in letters of another case on a
    # disk that does not tell them apart. A link is no such spelling: resolving it gives the folder's
    # own text, which the text alone would catch, where the mend is that the files decide.
    candidates = ["/System/Volumes/Data" + str(shipped.resolve()), str(tmp_path) + "/tool/data"]
    spellings = [
        each
        for each in candidates
        if os.path.isdir(each)
        and os.path.samefile(each, shipped)
        and str(Path(each).resolve()) != str(shipped.resolve())  # the text differs, the folder does not
    ]
    # Where the system offers neither, as Linux on a disk that tells letters apart offers none, no
    # other spelling of the folder can be made without a mount: the loop has nothing to try there,
    # and what follows it is tested all the same.
    for spelled in spellings:
        with set_to(CROSSING_HOME=spelled):
            assert record.astray(project) == "CROSSING_HOME" and store.kept(project) is None, spelled
            assert through("labels", "R1", "--cwd", str(project)) == (1, door.ASTRAY.format("CROSSING_HOME") + "\n")
            assert record.astray(other) is None  # from another project, the same place is outside it
    assert record.lies_in(shipped / "not-there" / "yet", project) and not record.lies_in(other, project)


def test_a_setting_that_names_no_absolute_path_is_not_followed(tmp_path):
    project = repository(tmp_path, "relative")
    for name in record.SETTINGS:
        with set_to(**{name: "homes"}):
            assert record.astray(project) == name and store.kept(project) is None
            assert through("look", "--cwd", str(project)) == (
                1,
                f"The setting {name} names no absolute path, so it was not followed.\n",
            )
            assert through("switch", "on", "--cwd", str(project))[0] == 1
    assert inside(project) == [".git"] and not (Path.cwd() / "homes").exists()
    assert "refused: the setting CROSSING_HOME names no absolute path: 'homes'" in logged(
        Path(os.environ["CLAUDE_PLUGIN_DATA"])
    )


# --- S2: the person's own folder is the account's --------------------------------------------------------


def test_the_persons_own_folder_is_the_accounts_and_not_what_home_says(tmp_path):
    account = Path(pwd.getpwuid(os.getuid()).pw_dir)
    fake = tmp_path / "project" / "fake-home"
    fake.mkdir(parents=True)
    with set_to(
        HOME=str(fake), CROSSING_HOMES=None, CROSSING_SWITCHED=None, CROSSING_OURS=None, CLAUDE_PLUGIN_DATA=None
    ):
        assert Path.home() == fake and record.own() == account  # paths alone: nothing is read or made there
        assert store.switched() == account / ".claude" / "crossing" / "switched"
        assert record.homes() == account / ".claude" / "crossing" / "homes"
        assert store.ours() == account / ".claude" / "crossing" / "ours"
        assert record._top(fake.resolve()) == fake.resolve()
        found = subprocess.run(
            [
                sys.executable,
                "-I",
                "-c",
                "import sys; sys.path.insert(0, sys.argv[1]); from crossing import hook; print(hook.LIVE)",
                str(ROOT),
            ],
            capture_output=True,
            text=True,
            env={**os.environ, "CROSSING_LIVE": ""},
            timeout=30,
        )
        assert found.stdout.strip() == str(account / ".claude" / "crossing" / "live")
    with set_to(CROSSING_SWITCHED=str(tmp_path / "named")):  # an explicit setting still names another place
        assert store.switched() == tmp_path / "named"


class Shell32:
    """The shell's known-folder call, as a test plays it: the folder it names, or a failure."""

    def __init__(self, code: int = 0):
        self.code, self.asked = code, []

    def SHGetKnownFolderPath(self, guid, flags, token, out):  # noqa: N802 (the system's own name)
        given = guid._obj
        self.asked.append((given.Data1, given.Data2, given.Data3, bytes(given.Data4)))
        if self.code == 0:
            out._obj.value = "C:\\Users\\someone"
        return self.code


class Ole32:
    def __init__(self):
        self.freed = 0

    def CoTaskMemFree(self, pointer):  # noqa: N802
        self.freed += 1


def test_on_windows_the_persons_folder_is_the_profiles_known_folder_and_no_variable(tmp_path):
    shell32, ole32 = Shell32(), Ole32()
    assert record._windows_profile((shell32, ole32)) == "C:\\Users\\someone" and ole32.freed == 1
    assert shell32.asked == [(0x5E6C858F, 0x0E22, 0x4760, bytes([0x9A, 0xFE, 0xEA, 0x33, 0x17, 0xB6, 0x71, 0x73]))]
    assert record._windows_profile((Shell32(code=1), Ole32())) == ""  # the call failed: nothing
    was = record.WINDOWS, record._windows_profile
    record.WINDOWS = True
    try:
        record._windows_profile = lambda: "C:\\Users\\someone"
        assert record.own() == Path("C:\\Users\\someone")
        record._windows_profile = was[1]  # here no Windows answers: the folder Python names, said once in the log
        before = logged(Path(os.environ["CLAUDE_PLUGIN_DATA"])).count("could not be read from the account")
        record._said_once.discard("own")
        assert record.own() == Path.home() == record.own()
        assert logged(Path(os.environ["CLAUDE_PLUGIN_DATA"])).count("could not be read from the account") == before + 1
    finally:
        record.WINDOWS, record._windows_profile = was
    account = record._account
    try:
        record._account = lambda: ""  # an account with no entry
        assert record.own() == Path.home()
    finally:
        record._account = account
    asked = pwd.getpwuid
    pwd.getpwuid = lambda uid: (_ for _ in ()).throw(KeyError(uid))
    try:
        assert record._account() == ""
    finally:
        pwd.getpwuid = asked


def test_the_terminal_and_the_plugins_own_call_are_told_by_what_is_there(tmp_path):
    assert record.terminal() is False  # a test's own output is no terminal
    given = sys.stdin
    sys.stdin = None  # a process started with no input at all
    try:
        assert record.terminal() is False
    finally:
        sys.stdin = given
    for root, plugin in ((str(ROOT), True), (str(tmp_path), False), (str(tmp_path / "not-there"), False), ("", False)):
        with set_to(CLAUDE_PLUGIN_ROOT=root):
            assert record.from_plugin() is plugin, root


# --- S4: what is the person's is the person's ------------------------------------------------------------


def test_a_session_is_looked_for_by_its_id_exactly_and_never_as_a_pattern(tmp_path):
    crossings, path = home(tmp_path)
    house = tmp_path / "house"
    elsewhere = house / ".claude" / "projects" / "another-project"
    elsewhere.mkdir(parents=True)
    (elsewhere / "f0f0f0f0-1111.jsonl").write_text(
        json.dumps(row("user", "f0f0f0f0", 30, "Another project's words.")) + "\n", encoding="utf-8"
    )
    project = str(crossings.parent)
    with own_folder(house), started_by("cli"):
        for pattern in ("*", "f0f0f0f0-*", "?0f0f0f0-1111", "[f]0f0f0f0-1111"):
            assert through("status", "--session", pattern, "--cwd", project) == (1, door.UNNAMED + "\n"), pattern
        assert "Newly archived: 1." in through("status", "--session", "f0f0f0f0-1111", "--cwd", project)[1]  # by its id
    assert "f0f0f0f0" in [r["id"] for r in store._archived(crossings)]
    with own_folder(tmp_path / "no-projects"), started_by("cli"):  # an account whose harness kept no transcript yet
        assert (
            door.transcript_of("f0f0f0f0-1111") is None
            and through("status", "--session", "x1", "--cwd", project)[0] == 0
        )


def test_the_persons_verbs_and_options_are_refused_to_a_sessions_shell(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    before = inside(tmp_path)
    for argv in (
        ["switch", "off"],
        ["switch", "on"],
        ["switch", "adopt"],
        ["switch", "toggle"],
        ["strike", A],
        ["strike", "session:session-"],
        ["layer", "some-model"],
        ["copy"],
        ["look", "--transcript", str(path)],
        ["status", "--session", "session-0001"],
        ["build", "--transcript", str(path), "--by-hook"],
        ["switch", "off", "--by-module"],
    ):
        assert shell(*argv, "--cwd", project) == (1, PERSONS), argv
    assert inside(tmp_path) == before and store.active(crossings)
    # The plugin's own module: its flag, with the plugin's folder in CLAUDE_PLUGIN_ROOT, and not either alone.
    alone = ran("door.py", "switch", "off", "--by-module", "--cwd", project, CLAUDE_PLUGIN_ROOT="")
    assert (alone.returncode, alone.stdout) == (1, PERSONS)
    wrong = ran("door.py", "switch", "off", "--by-module", "--cwd", project, CLAUDE_PLUGIN_ROOT=str(tmp_path))
    assert (wrong.returncode, wrong.stdout) == (1, PERSONS)
    rooted = ran("door.py", "switch", "off", "--cwd", project, CLAUDE_PLUGIN_ROOT=str(ROOT))
    assert (rooted.returncode, rooted.stdout) == (1, PERSONS)
    assert as_the_module("switch", "off", "--cwd", project).stdout == door.SWITCHED["off"] + "\n"
    # And the person at a real terminal.
    assert at_a_real_terminal("switch", "on", "--cwd", project) == (0, door.SWITCHED["again"] + "\n")
    assert shell("look", "--cwd", project)[0] == 0  # what any session may read stays open


def test_a_label_marked_from_a_shell_for_the_person_is_said_by_the_persons_next_status(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    code, out = shell("mark", "--whose", "his", "--anchors", A, "He wants the mooring sold.", "--cwd", project)
    assert code == 0 and out.startswith("marked W2 in ")
    assert (
        shell("mark", "--kind", "relation", "--anchors", A, "A standing line from a shell.", "--cwd", project)[0] == 0
    )
    assert shell("mark", "--anchors", A, "The session's own work label.", "--cwd", project)[0] == 0  # not the person's
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert (
            said("mark", sentence="Through the door.", anchors=[A], whose="his")[0] == "marked W4"
        )  # the hook shows it
        assert "marked from a shell" not in said("status")[0]  # the session's own status is not the person's
    assert store.shelled(crossings) == ["W2", "R2"]
    sentence = "2 labels were marked from a shell, not through the door, and shown to no one as marked: W2, R2."
    assert "marked from a shell" not in shell("status", "--cwd", project)[1] and store.shelled(crossings) == [
        "W2",
        "R2",
    ]  # a session's shell is not told the person's keys, and clears nothing
    assert sentence in through("status", "--cwd", project)[1]  # the person's own status says it, once
    assert "marked from a shell" not in through("status", "--cwd", project)[1]
    assert not (crossings / store.SHELLED).exists()


# --- S5: off the record without the spans file -------------------------------------------------------------


def off_and_on(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A project switched on, a message kept, then switched off from inside the session, two said
    while off, and switched on again through the person's command, which names the session."""
    project, folder, path = public(tmp_path)
    path.write_text("", encoding="utf-8")
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    says(
        path, "10000001", "Kept: the chain was replaced."
    )  # archived at none of the hooks before the switch: see below
    time.sleep(0.005)
    assert through("switch", "off", "--cwd", str(project))[0] == 0
    says(path, "20000002", "Off the record: the harbour master is selling.")
    says(path, "20000003", "Nothing of the harbour master's sale.", kind="assistant")
    time.sleep(0.005)
    house = tmp_path / "house"
    (house / ".claude" / "projects" / "tern").mkdir(parents=True)
    os.link(path, house / ".claude" / "projects" / "tern" / path.name)
    with own_folder(house), started_by("cli"):  # as the person's command turns it, naming the session
        assert through("switch", "on", "--session", path.stem, "--cwd", str(project)) == (
            0,
            door.SWITCHED["again"] + "\n",
        )
    return project, folder, path


def test_what_was_said_while_off_is_noted_by_id_as_the_span_closes_and_never_kept_without_the_spans_file(tmp_path):
    project, folder, path = off_and_on(tmp_path)
    noted = off.unsaid(folder)
    assert noted == {"20000002-0000-4000-8000-000000000000", "20000003-0000-4000-8000-000000000000"}  # by id alone
    assert [r["id"] for r in store._archived(folder)] == [
        "10000001"
    ]  # what was said before the span, kept as it closed
    with own_folder(tmp_path / "house"), started_by("cli"):  # off and on again with nothing said: nothing more to note
        assert through("switch", "off", "--cwd", str(project))[0] == 0
        assert through("switch", "on", "--session", path.stem, "--cwd", str(project)) == (
            0,
            door.SWITCHED["again"] + "\n",
        )
    assert off.unsaid(folder) == noted
    assert "harbour" not in (folder / off.UNSAID).read_text(encoding="utf-8")
    (folder / off.FILE).unlink()  # a session, a checkout or a clean takes the record of the spans away
    status = through("status", "--cwd", str(project))[1]
    assert LOST in status and LOST in through("look", "--cwd", str(project))[1]
    with started_by("cli"):
        assert "Newly archived" not in through("build", "--transcript", str(path), "--cwd", str(project))[1]
    assert [r["id"] for r in store._archived(folder)] == ["10000001"]  # nothing archived while the record is lost
    # The record's mark taken away too, as an older make knew none: the ids noted still keep the words out.
    switched = Path(os.environ["CROSSING_SWITCHED"])
    switched.write_text(
        "".join(line + "\n" for line in switched.read_text(encoding="utf-8").splitlines() if '"spans"' not in line),
        encoding="utf-8",
    )
    assert not store.lost(folder)
    with started_by("cli"):
        through("build", "--transcript", str(path), "--cwd", str(project))
    assert [r["id"] for r in store._archived(folder)] == ["10000001"]


def test_a_spans_file_cut_short_stops_archiving_until_the_person_switches_on_and_everything_before_is_off(tmp_path):
    project, folder, path = off_and_on(tmp_path)
    (folder / off.UNSAID).unlink()  # neither record of what was said while off is left, but the person's own
    lines = (folder / off.FILE).read_text(encoding="utf-8").splitlines()
    (folder / off.FILE).write_text(lines[0] + "\n", encoding="utf-8")  # shorter than the switch left it
    assert store.lost(folder) and store.archive(path, folder, whole=True) == 0
    says(path, "30000004", "Said while the record was lost.")
    assert through("switch", "on", "--cwd", str(project)) == (0, RESTORED)
    assert not store.lost(folder) and LOST not in through("status", "--cwd", str(project))[1]
    says(path, "40000005", "Said once it was restored.")
    with started_by("cli"):
        through("build", "--transcript", str(path), "--cwd", str(project))
    assert [r["id"] for r in store._archived(folder)] == ["10000001", "40000005"]
    assert "1970-01-01" in (folder / off.FILE).read_text(encoding="utf-8")  # everything before that moment is off


# --- S6: the door is for sessions a person sits in --------------------------------------------------------


def test_the_server_answers_a_session_no_person_sits_in_with_one_sentence_and_reads_nothing(tmp_path):
    crossings, _ = home(tmp_path)
    read, believed, opened = store._open, store.kept, []
    store._open = lambda folder: opened.append(folder) or read(folder)
    store.kept = lambda cwd: opened.append(cwd) or believed(cwd)
    try:
        with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
            for entrypoint in ("sdk-cli", "sdk-py", "mcp"):
                with started_by(entrypoint):
                    for name, given in (
                        ("look", {}),
                        ("status", {}),
                        ("labels", {}),
                        ("find", {"words": "Tern"}),
                        ("thread", {"id": A}),
                        ("mark", {"sentence": "A line.", "anchors": [A]}),
                        ("leave", {"sentence": "A line.", "anchors": [A]}),
                    ):
                        assert said(name, **given) == (UNATTENDED, True), (entrypoint, name)
            assert opened == []
            with started_by("cli"):
                assert said("look")[1] is False and opened
    finally:
        store._open, store.kept = read, believed
    assert not (crossings / "reached.jsonl").exists()


# --- S7: a strike by a session's whole id -----------------------------------------------------------------


def test_a_session_struck_by_its_whole_id_is_struck_and_a_strike_that_matched_nothing_says_so(tmp_path):
    crossings, path = home(tmp_path, name="abcdef01-2222-3333")
    project = str(crossings.parent)
    assert store.status(crossings)["his"] == 2
    code, said_ = through("strike", "session:abcdef01-2222-3333", "--cwd", project)
    assert code == 0 and said_.startswith("struck session:abcdef01: 4 lines removed")
    assert store.status(crossings)["his"] == 0 and "session:abcdef01" in store.struck(crossings)
    assert through("strike", "session:abcdef01-2222-3333", "--cwd", project) == (
        1,
        "not struck: nothing in this home is named session:abcdef01, so nothing was struck\n",
    )
    assert through("strike", "0a0a0a0a", "--cwd", project) == (
        1,
        "not struck: nothing in this home is named 0a0a0a0a, so nothing was struck\n",
    )
    assert through("strike", "r1", "--cwd", project)[1].startswith("struck R1: ")  # a key in the form the pages keep it
    assert "0a0a0a0a" not in store.struck(crossings)
    (crossings / "told.txt").write_text("c0ffee00-1234 off\n", encoding="utf-8")  # named by a small file alone
    assert through("strike", "session:c0ffee00-1234", "--cwd", project)[1].startswith("struck session:c0ffee00: ")
    assert not (crossings / "told.txt").read_text(encoding="utf-8")


# --- S8: an ignore file for a home inside a repository ------------------------------------------------------


def test_a_home_inside_a_repository_is_given_an_ignore_file_that_keeps_the_words_out(tmp_path):
    project = repository(tmp_path, "kept")
    (project / "crossings").mkdir()
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    ignore = project / "crossings" / ".gitignore"
    assert ignore.read_text(encoding="utf-8") == store.IGNORE
    if shutil.which("git"):  # read as git reads it, in a repository of the test's own
        subprocess.run(["git", "init", "-q", str(project / "real")], check=True, timeout=30)
        (project / "real" / "crossings").mkdir()
        shutil.copyfile(ignore, project / "real" / "crossings" / ".gitignore")
        names = [
            "said/abcdef01.jsonl",
            "store.db",
            "off.txt",
            "unsaid.txt",
            "models.txt",
            "markers.jsonl",
            "flagged.txt",
            "hand-over.words.md",
            "abcdef01-cut-1.json",
            "said/runs.key",
            "labels/2026-01-01.md",
            "hand-over.md",
            "abcdef01-cut-1.md",
            ".gitignore",
        ]
        checked = subprocess.run(
            ["git", "-C", str(project / "real"), "check-ignore", "--no-index", "--stdin"],
            input="".join(f"crossings/{name}\n" for name in names),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert sorted(checked.stdout.split()) == sorted(f"crossings/{name}" for name in names[:10]), checked.stdout
    # An ignore file that is there is left alone; where it lets said/ in, status says so once.
    other = repository(tmp_path, "own-ignore")
    (other / "crossings").mkdir()
    (other / "crossings" / ".gitignore").write_text("store.db\n", encoding="utf-8")
    assert through("switch", "on", "--cwd", str(other)) == (0, ON)
    assert (other / "crossings" / ".gitignore").read_text(encoding="utf-8") == "store.db\n"
    assert IGNORE_SAID in through("status", "--cwd", str(other))[1]
    assert IGNORE_SAID not in through("status", "--cwd", str(other))[1]
    (other / "crossings" / ".gitignore").write_text("said/\n", encoding="utf-8")
    assert not store.leaves_said(other / "crossings")
    # A home outside the project, in no repository, is given none.
    loose, outside, _ = public(tmp_path / "loose")
    assert through("switch", "on", "--cwd", str(loose)) == (0, ON) and not (outside / ".gitignore").exists()
    (tmp_path / ".git").mkdir()  # a repository above the person's own folder is not looked for
    with own_folder(tmp_path / "house"), set_to(CROSSING_HOMES=str(tmp_path / "house" / "homes")):
        aside, _, _ = public(tmp_path / "house" / "aside")
        assert through("switch", "on", "--cwd", str(aside)) == (0, ON)
        assert not (record.outside(aside.resolve()) / ".gitignore").exists()


# --- S9: a believed home's files, trusted no further than they need be -----------------------------------------


def test_a_copy_file_or_a_staging_folder_inside_the_project_makes_no_copy(tmp_path):
    crossings, path = home(tmp_path)
    project = crossings.parent
    (crossings / "copy").write_text(str(project / "synced") + "\n", encoding="utf-8")
    assert through("copy", "--cwd", str(project)) == (1, INSIDE)
    with started_by("cli"), set_to(CROSSING_WAIT="1"):
        hook.keep(path, project, wait=True)
    assert not (project / "synced").exists()
    assert "refused: the home's copy file names a place inside the project" in logged(
        Path(os.environ["CLAUDE_PLUGIN_DATA"])
    )
    staged = project / "tmp"
    staged.mkdir()
    with set_to(TMPDIR=str(staged)):
        tempfile.tempdir = None  # the temporary folder is asked again, as a process of its own would
        try:
            out = second.make(crossings, tmp_path / "cloud", "project", project)
        finally:
            tempfile.tempdir = None
    assert out == {"copied": False, "why": "the system's temporary folder lies inside the project"}
    assert list(staged.iterdir()) == [] and not (tmp_path / "cloud").exists()


# --- S10: a crossings/ folder that arrives does not hide the home the person switched on -------------------------


def test_a_crossings_folder_that_arrives_is_passed_over_for_the_home_outside_and_said_once(tmp_path):
    project, outside, path = public(tmp_path)
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    store.archive(path, outside)
    store.build(outside)
    arrived = project / "crossings"
    (arrived / "labels").mkdir(parents=True)  # a checkout brings one, with a line of someone else's
    (arrived / "labels" / "2026-01-01.md").write_text(
        f"| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R1 | Not the person's. | his | `{A}` |\n",
        encoding="utf-8",
    )
    assert store.kept(project) == outside and store.passed_over(project) == arrived.resolve()
    status = through("status", "--cwd", str(project))[1]
    assert status.startswith(f"The store at {outside} holds 2 messages") and PASSING in status
    assert PASSING not in through("status", "--cwd", str(project))[1]  # once
    event = {
        "hook_event_name": "SessionStart",
        "source": "startup",
        "cwd": str(project),
        "session_id": "abcdef01-4444",
        "transcript_path": str(path),
    }
    with started_by("cli"):
        told = json.loads(hook.run(event))
        assert told["systemMessage"] == f"Crossings · {PASSING}"
        again = hook.run({**event, "session_id": "abcdef01-5555"})
        assert again is None or "systemMessage" not in json.loads(again)  # once
    assert (
        through("look", "--cwd", str(project))[0] == 0
        and "Not the person's" not in through("labels", "--cwd", str(project))[1]
    )
    assert inside(arrived) == ["labels", "labels/2026-01-01.md"]  # and nothing is written into it
    # Where the note of who was told cannot be read or written, nothing is said: said every time would be worse.
    (outside / store.PASSED).unlink()
    (outside / store.PASSED).mkdir()
    assert store.passed_note(project, outside, "status") is None
    (outside / store.PASSED).rmdir()
    (outside / store.PASSED).write_text("hook elsewhere\n", encoding="utf-8")
    os.chmod(outside / store.PASSED, 0o400)
    try:
        assert store.passed_note(project, outside, "status") is None
    finally:
        os.chmod(outside / store.PASSED, 0o600)


# --- S11: an index that is no database ------------------------------------------------------------------------


def test_a_store_db_that_is_no_database_is_read_as_none_and_made_again(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    (crossings / "store.db").write_text("this is not a database", encoding="utf-8")
    for argv in (["look"], ["status"], ["find", "Tern"], ["thread", A], ["labels", "R1"], ["frame"]):
        code, out = through(*argv, "--cwd", project)
        assert code == 0 and "Traceback" not in out, argv
    assert "Tern" in through("find", "Tern", "--cwd", project)[1]
    assert (crossings / "store.db").read_text(encoding="utf-8") == "this is not a database"  # a read writes none
    more = row("user", "99999999", 40, "Said after the index was written over.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(more) + "\n", encoding="utf-8")
    with started_by("cli"):
        hook.run(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "mcp__plugin_crossing_door__find",
                "cwd": project,
                "transcript_path": str(path),
                "session_id": "session-0001",
            }
        )
    assert store.status(crossings)["his"] == 3 and (crossings / "store.db").read_bytes().startswith(b"SQLite format 3")
    (crossings / "store.db").write_text("written over again", encoding="utf-8")  # and a mark over such an index
    assert through("mark", "--anchors", A, "Marked over a broken index.", "--cwd", project)[0] == 0
    assert (crossings / "store.db").read_bytes().startswith(b"SQLite format 3") and store.status(crossings)[
        "labels"
    ] == 3


# --- an sqlite3 with no full-text search -----------------------------------------------------------------------


class _NoFts5(sqlite3.Connection):
    """A connection as an sqlite3 built without FTS5 gives one: making a table with it fails as
    SQLite fails it there (or, given another `fault`, with that)."""

    fault = "no such module: fts5"

    def execute(self, sql, *given):
        if "fts5" in sql.lower():
            raise sqlite3.OperationalError(self.fault)
        return super().execute(sql, *given)

    def executescript(self, script):
        if "fts5" in script.lower():
            raise sqlite3.OperationalError(self.fault)
        return super().executescript(script)


class _Faulty(_NoFts5):
    fault = "disk I/O error"


@contextlib.contextmanager
def without_fts5(factory=_NoFts5):
    """Every connection made meanwhile is one with no FTS5."""
    real = sqlite3.connect
    sqlite3.connect = lambda *given, **more: real(*given, factory=factory, **more)
    try:
        yield
    finally:
        sqlite3.connect = real


def test_where_sqlite3_has_no_full_text_search_it_is_said_in_a_sentence_and_what_is_said_is_kept(tmp_path):
    """Guard: without FTS5 the index cannot be made, and the door answered only "The door could
    not answer: OperationalError." The person and the session are told why, and the archive in
    said/, which needs no index, is written all the same."""
    project = tmp_path / "project"
    crossings = project / "crossings"
    crossings.mkdir(parents=True)
    path = tmp_path / "session-0001.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    with without_fts5():
        assert not store.searchable()
        assert through("switch", "on", "--cwd", str(project)) == (0, f"{door.SWITCHED['on']} {store.NO_SEARCH}\n")
        with started_by("cli"):  # the hook a moment before a door tool: it archives, and raises nothing
            assert (
                hook.run(
                    {
                        "hook_event_name": "PreToolUse",
                        "tool_name": "mcp__plugin_crossing_door__find",
                        "cwd": str(project),
                        "transcript_path": str(path),
                        "session_id": "session-0001",
                    }
                )
                is None
            )
        words = (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8")
        assert "My boat is called Tern" in words and "Grey it is" in words  # kept in plain files, with no index
        for argv in (["status"], ["look"], ["find", "Tern"], ["thread", A], ["labels"]):
            assert through(*argv, "--cwd", str(project)) == (1, store.NO_SEARCH + "\n"), argv
        with set_to(CLAUDE_PROJECT_DIR=str(project)):
            for name, given in (
                ("status", {}),
                ("look", {}),
                ("find", {"words": "Tern"}),
                ("thread", {"id": A}),
                ("labels", {}),
            ):
                assert said(name, **given) == (store.NO_SEARCH, True), name
    # Where FTS5 is there again, the index is made from the same plain files.
    assert store.searchable()
    assert "holds 2 messages of the person's and 2 of the session's" in through("status", "--cwd", str(project))[1]
    assert "Tern" in through("find", "Tern", "--cwd", str(project))[1]
    # Any other fault of SQLite's is not taken for a missing FTS5: it is raised as before.
    assert not (crossings / "store.db").exists()  # no index on disk was made meanwhile, and a read makes none
    with without_fts5(_Faulty):
        assert store.searchable()
        for act in (lambda: through("status", "--cwd", str(project)), lambda: store.refresh(crossings)):
            try:
                act()
                raise AssertionError("not raised")
            except sqlite3.OperationalError as err:
                assert str(err) == "disk I/O error" and not store.unsearchable(err)


# --- S13: a mark is added to the index -------------------------------------------------------------------------


def test_a_mark_is_added_to_the_index_and_gives_the_database_a_whole_build_gives(tmp_path):
    project, crossings, path = started(tmp_path)
    builds, real = [], store.build
    store.build = lambda folder: builds.append(folder) or real(folder)
    try:
        for n, (kind, whose, model) in enumerate(
            (
                ("work", "both", "made-up-model"),
                ("relation", "his", ""),
                ("next", "session", "made-up-model"),
                ("work", "session", ""),
            )
        ):
            out = store.mark(
                crossings,
                kind,
                whose,
                f"Label {n} about the hull.",
                [f"{n + 1:08x}", f"{n + 3:08x}+1" if (n + 3) % 5 == 3 else f"{n + 3:08x}"],
                day="2026-03-01",
                model=model,
            )
            assert out["written"], out
        assert store.sign(crossings, "W2", "Label 3 about the hull.", "made-up-model")
        assert builds == []  # each was added, as an archive adds messages
        stacked = store.mark(crossings, "work", "both", "Over both.", ["W1", "W2"], day="2026-03-01")
        assert stacked["written"] and builds == [crossings]  # a stack changes the states of its lines: made whole
    finally:
        store.build = real
    same_as_whole(project, crossings, ["00000001", "00000004"])
    reached = dump(crossings / "store.db")
    store.build(crossings)
    assert dump(crossings / "store.db") == reached


def test_a_mark_after_a_page_was_changed_by_hand_makes_the_index_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    assert store.mark(crossings, "work", "both", "First.", ["00000001"], day="2026-03-01")["written"]
    page = crossings / "labels" / "2026-03-01.md"
    with open(page, "a", encoding="utf-8") as handle:
        handle.write("| W9 | Written by hand. | both | `00000002` |\n")
    assert store.mark(crossings, "work", "both", "Second.", ["00000002"], day="2026-03-01")["written"]
    same_as_whole(project, crossings, ["00000002"])
    with open(page, "a", encoding="utf-8") as handle:
        handle.write(
            "| W11 | Written by hand again. | both | `00000002` |\n"
        )  # past W10, which the pages gave "Second."
    assert store.sign(
        crossings, "W11", "Written by hand again.", "made-up-model"
    )  # the index no longer stood for the pages
    assert store.mark(crossings, "work", "both", "After it.", ["00000002"], day="2026-03-01")["written"]
    same_as_whole(project, crossings, ["00000002"])
    failing, store._restood = store._restood, lambda *_: (_ for _ in ()).throw(store.sqlite3.OperationalError("locked"))
    try:
        assert store.mark(crossings, "work", "both", "An addition that fails.", ["00000002"], day="2026-03-01")[
            "written"
        ]
    finally:
        store._restood = failing
    same_as_whole(project, crossings, ["00000002"])  # made whole instead
    later = crossings / "labels" / "2026-04-01.md"  # a page after the one marked into: a build numbers it last
    later.write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| W20 | Later. | both | `00000003` |\n",
        encoding="utf-8",
    )
    store.build(crossings)
    assert store.mark(crossings, "work", "both", "Third.", ["00000003"], day="2026-03-01")["written"]
    same_as_whole(project, crossings, ["00000003"])


@in_person
def test_the_hook_before_a_mark_learns_the_model_without_reading_the_archive_whole(tmp_path):
    from test_reading import lines
    from test_reading import said as message
    from test_reading import started as large

    crossings, path = large(tmp_path, 3000)
    store.build(crossings)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(
            lines([{**message(n), "timestamp": f"2026-11-11T10:00:0{n % 10}.000Z"} for n in range(5000, 5010)])
        )
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__plugin_crossing_door__mark",
        "transcript_path": str(path),
        "cwd": str(crossings.parent),
        "session_id": "abcdef01-0101",
        "tool_input": {"sentence": "A label.", "anchors": [f"{5009:08x}"]},
    }
    layer.arrive(crossings, "abcdef01", "made-up-model")
    with reading_the_archive(crossings) as (read, parsed):
        assert hook.run(event) is None
    assert parsed[0] == 10, parsed[0]  # the ten lines added, and none of the thousands before them
    assert (crossings / layer.CALLING).read_text(encoding="utf-8").split()[1] == "made-up-model"


# --- S14: what is shown is cleaned ----------------------------------------------------------------------------

MARKS = "\u202e\u2066\u2069\u200e\u200f\u061c\u2028\u2029\x1b\x07\ufeff\u200b"  # each one a character no text shows


def test_a_labels_sentence_and_a_messages_words_are_shown_with_nothing_that_reorders_or_hides(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    steered = f"The hull{MARKS}[31m is grey."
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row("user", "77777777", 40, f"Paint{MARKS}[31m it grey\nin spring.")) + "\n")
    store.archive(path, crossings)
    page = crossings / "labels" / "2026-11-11.md"
    page.parent.mkdir(exist_ok=True)
    page.write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        f"| W5 | {steered} | his{MARKS} | `77777777` |\n| N1 | Left{MARKS} here. | session | `77777777` |\n",
        encoding="utf-8",
    )
    store.build(crossings)
    shown = [
        through(*argv, "--cwd", project)[1]
        for argv in (["look"], ["labels"], ["labels", "W5"], ["find", "grey"], ["thread", "77777777"], ["find", "hull"])
    ]
    shown.append(frame.compose(crossings))
    for text in shown:
        assert not any(mark in text for mark in MARKS), [mark for mark in MARKS if mark in text]
    assert "The hull[31m is grey." in shown[2] and "Paint[31m it grey" in shown[4]  # the words themselves stay
    # A message holding a line or paragraph separator is kept whole, on its line of the archive, and read as one.
    assert store.status(crossings)["unread"] == 0 and store.status(crossings)["his"] == 3
    assert "    in spring." in shown[4]  # a message's own lines stay lines
    assert steered in page.read_text(encoding="utf-8")  # the page is left as it was
    assert store.clean("a\tb\nc", lines=True) == "a\tb\nc" and store.clean("a\tb\nc") == "abc"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:
                sweep(folder)
            print("ok", name)
