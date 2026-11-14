"""What a strike reaches and what it cannot; ids that would name another file; a key typed by
the person, kept and named to them alone; the second copy's staging, outside the home; and one
archive at a time. No model, no network, and no real secret: every key here is a made-up one of
the right shape.

Run with pytest, or without it:  python3 tests/test_reach.py
"""

from __future__ import annotations

import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import as_the_module, ran, set_to, through  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import A, B, D, E, at_terminal, home, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, handover, record, second, store  # noqa: E402

KEY = "a passphrase for this test only"
# What the door and the files say, written out here, so that a test of the code before them fails on what it does.
UNNAMED = "An id given here cannot name a file (letters, digits, - and _ alone), so nothing was written."
FLAGGED = (
    "A kept message looks like it holds a key or a password ({0}), and door.py strike {0} removes it from the store."
)
COPY_KEY = (
    "The second copy's passphrase is taken from the environment (CROSSING_COPY_KEY), where every program the "
    "session starts can read it."
)
REACH = (
    "A strike cannot reach the harness's own transcript, an earlier second copy or a backup, or the history of a "
    "repository that holds this home."
)
NOTE, STAGE, LOCK = "copy-stage.txt", "crossing-copy-", "archive.lock"
COPYING = "copy.lock"
HELD = "another act was writing this home, so no copy was made this time"
BUSY = "another copy of this home was being made at that moment, so none was made this time"
UNUSABLE = "the home's copy lock is not a file this account can write"
UNREAD = "the note of a copy's stage in the home cannot be read"
CHANGED = "the home changed while the copy was made, so it was not put in place; the next copy takes it as it stands"


def staging() -> Path:
    return Path(tempfile.gettempdir()).resolve()


def noted(folder: Path) -> list[str]:
    """The ids `flagged.txt` notes, or none where there is no such file."""
    try:
        return [
            line
            for line in (folder / "flagged.txt").read_text(encoding="utf-8").splitlines()
            if not line.startswith("#")
        ]
    except FileNotFoundError:
        return []


def tree(folder: Path) -> dict[str, bytes]:
    """Every file under a folder, by its path from there, with what it holds."""
    return {
        str(p.relative_to(folder)): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file() and not p.is_symlink()
    }


def logged(data: Path) -> str:
    try:
        return (data / "errors.log").read_text(encoding="utf-8")
    except OSError:
        return ""


def transcript(folder: Path, name: str, rows: list[dict]) -> Path:
    path = folder / f"{name}.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


# --- what a strike reaches -----------------------------------------------------------------------


def words_page(crossings: Path, path: Path) -> Path:
    """The hand-over's words page, as crossing/handover.py writes it beside the page."""
    page = crossings / "hand-over.words.md"
    page.write_text(handover.page(path, crossings / "hand-over.md"), encoding="utf-8")
    return page


def test_a_struck_message_is_taken_out_of_the_hand_overs_words_page(tmp_path):
    crossings, path = home(tmp_path)
    page = words_page(crossings, path)
    assert f"- `{A}`, the person: My boat is called Tern." in page.read_text(encoding="utf-8")
    code, answer = through("strike", A, "--cwd", str(crossings.parent))
    assert code == 0 and "Its words were taken out of hand-over.words.md." in answer
    text = page.read_text(encoding="utf-8")
    assert A not in text and "My boat is called" not in text and "mooring is number 41" not in text
    for kept in (B, D, E):
        assert f"- `{kept}`, " in text, kept  # the others' words stand as they were
    assert text.startswith("## The anchored words, from the record\n") and text.endswith("\n") and "\n\n\n" not in text


def test_the_missing_ids_line_is_mended_and_goes_when_it_names_only_what_was_struck(tmp_path):
    crossings, path = home(tmp_path)
    page = words_page(crossings, path)
    page.write_text(
        page.read_text(encoding="utf-8") + f"\nNamed by a label and not in this transcript: `{D}`, `0a0a0a0a`.\n",
        encoding="utf-8",
    )
    store.strike(crossings, D)
    assert "Named by a label and not in this transcript: `0a0a0a0a`.\n" in page.read_text(encoding="utf-8")
    page.write_text(page.read_text(encoding="utf-8").replace("`0a0a0a0a`", f"`{E}`"), encoding="utf-8")
    store.strike(crossings, E)
    text = page.read_text(encoding="utf-8")
    assert "Named by" not in text and E not in text and text.endswith("|\n") and "\n\n\n" not in text


def test_a_words_page_that_cannot_be_mended_line_by_line_goes_whole_and_the_answer_says_so(tmp_path):
    crossings, path = home(tmp_path)
    page = words_page(crossings, path)
    text = page.read_text(encoding="utf-8").replace(
        f"- `{D}`, the person: We paint the hull grey in spring",
        f"- `{D}`, the person: We paint the hull\ngrey in spring, and then the deck",
    )
    page.write_text(text, encoding="utf-8")  # a message whose words run over two lines, as a hand would leave it
    other = crossings / "other.words.md"  # and one that names the id where no line of words gives it
    other.write_text(f"Words kept by hand: {D} said the deck comes next.\n", encoding="utf-8")
    untouched = crossings / "third.words.md"
    untouched.write_text(f"- `{A}`, the person: Not about this one.\n", encoding="utf-8")
    code, answer = through("strike", D, "--cwd", str(crossings.parent))
    assert code == 0 and not page.exists() and not other.exists()
    assert (
        "The hand-over words pages hand-over.words.md, other.words.md could not be mended line by line and were "
        "removed whole."
    ) in answer
    assert untouched.read_text(encoding="utf-8") == f"- `{A}`, the person: Not about this one.\n"
    single = crossings / "hand-over.words.md"
    single.write_text(f"- `{E}`, the session: Grey it is.\nI will remind you.\n", encoding="utf-8")
    answer = through("strike", E, "--cwd", str(crossings.parent))[1]
    assert (
        "The hand-over words page hand-over.words.md could not be mended line by line and was removed whole." in answer
    )


def test_a_struck_session_leaves_every_small_file_that_names_it_and_its_markers(tmp_path):
    crossings, path = home(tmp_path)  # the archive names its session `session-`, from session-0001.jsonl
    other = transcript(tmp_path, "harbour0-0002", [row("user", "12345678", 20, "Another session's words.")])
    store.archive(other, crossings)
    store.unattended(path, crossings)  # a marker of its own for the same transcript
    (crossings / "welcomed.txt").write_text("session-0001\nharbour0-0002\n", encoding="utf-8")
    (crossings / "told.txt").write_text("session-0001 off\nharbour0-0002 off\nsession-0001 on\n", encoding="utf-8")
    (crossings / "there.txt").write_text(
        "# The model each session runs\nsession- claude-test-1 2026-11-11T09:00:00Z\n"
        "harbour0 claude-test-2 2026-11-11T09:00:00Z\n",
        encoding="utf-8",
    )
    (crossings / "flagged.txt").write_text(f"# ids\n{A}\n12345678\n", encoding="utf-8")
    (crossings / "markers.jsonl").write_text(
        (crossings / "markers.jsonl").read_text(encoding="utf-8") + "not a marker\n", encoding="utf-8"
    )
    assert (
        len(
            [
                line
                for line in (crossings / "markers.jsonl").read_text(encoding="utf-8").splitlines()
                if "session-0001" in line
            ]
        )
        == 2
    )
    code, answer = through("strike", "session:session-", "--cwd", str(crossings.parent))
    assert code == 0
    assert (crossings / "welcomed.txt").read_text(encoding="utf-8") == "harbour0-0002\n"
    assert (crossings / "told.txt").read_text(encoding="utf-8") == "harbour0-0002 off\n"
    assert (crossings / "there.txt").read_text(encoding="utf-8") == (
        "# The model each session runs\nharbour0 claude-test-2 2026-11-11T09:00:00Z\n"
    )
    assert (crossings / "flagged.txt").read_text(encoding="utf-8") == "# ids\n12345678\n"
    assert (crossings / "unattended.txt").read_text(encoding="utf-8").splitlines()[
        1:
    ] == []  # its ids, by the archive's
    marks = (crossings / "markers.jsonl").read_text(encoding="utf-8")
    assert "session-0001" not in marks and "harbour0-0002" in marks and "not a marker\n" in marks
    assert (
        store.status(crossings)["his"] == 1 and store.archive(path, crossings) == 0
    )  # read again whole, and nothing comes back
    for name in ("welcomed.txt", "told.txt", "there.txt", "markers.jsonl", "flagged.txt"):
        assert not (crossings / (name + ".new")).exists(), name
    assert answer.endswith(REACH + "\n")


def test_every_strike_ends_by_naming_what_it_cannot_reach(tmp_path):
    crossings, _ = home(tmp_path)
    (crossings / "welcomed.txt").write_text("harbour0-0002\n", encoding="utf-8")  # no line of the session struck below
    before = os.stat(crossings / "welcomed.txt").st_ino
    for token in ("W1", A, "session:session-"):
        code, answer = through("strike", token, "--cwd", str(crossings.parent))
        assert code == 0 and answer.endswith(
            " A strike cannot reach the harness's own transcript, an earlier second copy or "
            "a backup, or the history of a repository that holds this home.\n"
        ), token
    assert (
        "not struck: nothing named" in through("strike", "--cwd", str(crossings.parent))[1]
    )  # a refusal is said alone
    assert REACH not in through("strike", "--cwd", str(crossings.parent))[1] and store.REACH == REACH
    assert os.stat(crossings / "welcomed.txt").st_ino == before  # a file with nothing of it is not written again


# --- ids that would name another file ---------------------------------------------------------------

BAD = ("..", "../outside", "a\nb", "a b", "x" * 300, "a.b")


def test_a_session_id_that_cannot_name_a_file_writes_nothing_anywhere(tmp_path):
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    store.consent(project)  # on, and no label: a session a person sits in would be welcomed
    live, data = tmp_path / "live", tmp_path / "data"
    live.mkdir()
    data.mkdir()
    for bad in BAD:
        before = tree(tmp_path)
        event = {
            "hook_event_name": "SessionStart",
            "source": "startup",
            "session_id": bad,
            "cwd": str(project),
            "transcript_path": str(tmp_path / "harbour0-0001.jsonl"),
            "model": "claude-test-1",
        }
        done = ran(
            "hook.py",
            stdin=json.dumps(event),
            CLAUDE_CODE_ENTRYPOINT="cli",
            CROSSING_LIVE=str(live),
            CLAUDE_PLUGIN_DATA=str(data),
            CROSSING_DEBUG="0",
            CLAUDE_PROJECT_DIR=str(project),
        )
        assert (done.returncode, done.stdout, done.stderr) == (0, "", ""), repr(bad)
        after = tree(tmp_path)
        assert {k: v for k, v in after.items() if k != "data/errors.log"} == {
            k: v for k, v in before.items() if k != "data/errors.log"
        }, repr(bad)
        assert logged(data).splitlines()[-1].startswith("refused: an id that cannot name a file: "), repr(bad)
        assert "\n" not in logged(data).splitlines()[-1] and len(logged(data).splitlines()[-1]) < 140
    assert list(live.iterdir()) == [] and list((project / "crossings").iterdir()) == []


def test_the_door_refuses_an_id_that_cannot_name_a_file_in_one_sentence(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    one = UNNAMED + "\n"
    assert one.count(". ") == 0 and one.endswith(".\n")
    with started_by("cli"):
        for bad in BAD:
            before = tree(tmp_path)
            assert through("welcome", bad, "--cwd", project) == (1, one), repr(bad)
            assert through("strike", f"session:{bad}", "--cwd", project) == (1, one), repr(bad)
            assert tree(tmp_path) == before, repr(bad)
    for bad in ("a b", "x\ny", ".."):
        handed = tmp_path / "handed" / f"{bad}.jsonl"
        handed.parent.mkdir(exist_ok=True)
        handed.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        before = tree(crossings)
        assert through("status", "--cwd", project, "--transcript", str(handed)) == (1, one), repr(bad)
        assert tree(crossings) == before and sorted(p.name for p in (crossings / "said").iterdir()) == [
            "session-.jsonl"
        ]
    for bad in BAD:  # a cut's record, and a label page's day
        try:
            record.where(crossings, bad, 1)
        except record.Unnamed:
            pass
        else:
            raise AssertionError(f"a cut's record was named by {bad!r}")
        try:
            store.mark(crossings, "work", "both", "A label on a day that is no name.", [D], day=bad)
        except record.Unnamed:
            pass
        else:
            raise AssertionError(f"a label page was named by {bad!r}")
    assert not (crossings / "labels").exists()  # no page was made under any of those names
    assert record.ident("abcdef01-2222_x") == "abcdef01-2222_x" and door.UNNAMED == UNNAMED


# --- a key typed by the person ----------------------------------------------------------------------

SECRETS = [  # made up, each of the right shape
    "-----BEGIN OPENSSH PRIVATE KEY-----\nb3BlbnNzaC1rZXktdjEAAAAAfakefakefake\n-----END OPENSSH PRIVATE KEY-----",
    "-----BEGIN PRIVATE KEY-----\nMIIEvfakefake\n-----END PRIVATE KEY-----",
    "The deploy uses AKIA" + "FAKE" + "0" * 12 + " for the bucket.",
    "token ghp_" + "Fake" + "0" * 32,
    "gho_" + "Fake" + "1" * 32 + " is the one",
    "ghs_" + "Fake" + "2" * 32,
    "github_pat_" + "11FAKE" + "0" * 16 + "_" + "x" * 59,
    "the key is sk-" + "fake" + "0" * 20,
    "curl -H 'Authorization: Bearer fake.token-for_tests'",
    "password=not-a-real-one",
    "passwd: fakefakefake",
    'api_key = "fake0000key"',
]
ORDINARY = [  # talk about passwords and keys, which is no key
    "I forgot my password again, can you help me reset it?",
    "The password must be at least 8 characters long.",
    "Put the api key in the settings, not in the code.",
    "Send a bearer token in the Authorization header.",
    "A key that begins sk- is a secret one, and ghp_ marks a token of GitHub's.",
    "password: none",
    "Use AKIA keys sparingly, and keep the -----BEGIN PUBLIC KEY----- block.",
    "The task-management-overview-of-the-week is long.",
]


def keyed(tmp_path: Path) -> tuple[Path, Path, list[str]]:
    """A home whose archive holds the person's messages with keys in them, talk about keys, a key
    the session wrote and one the person pasted. Gives the ids that look like they hold a key."""
    rows = [row("user", f"5ec{n:05x}", n, text) for n, text in enumerate(SECRETS)]
    rows += [row("user", f"00d{n:05x}", 20 + n, text) for n, text in enumerate(ORDINARY)]
    rows += [
        row("assistant", "a55a0001", 40, [{"type": "text", "text": "An example: password=example-value-123"}]),
        row(
            "user",
            "9a57ed01",
            41,
            'Look at this <pasted_content id="1">key AKIA' + "FAKE" + "1" * 12 + " in a log</pasted_content>",
        ),
    ]
    crossings, _ = home(tmp_path)
    path = transcript(tmp_path, "keyed000-0001", rows)
    store.archive(path, crossings)
    store.build(crossings)
    return crossings, path, [f"5ec{n:05x}" for n in range(len(SECRETS))] + ["9a57ed01"]


def test_a_message_that_looks_like_it_holds_a_key_is_kept_and_noted_by_its_id_alone(tmp_path):
    crossings, path, ids = keyed(tmp_path)
    assert noted(crossings) == ids  # each pattern; neither the talk about keys nor the session's own
    note = (crossings / "flagged.txt").read_text(encoding="utf-8")
    assert note.splitlines()[1:] == ids and note.startswith("# ")
    for text in SECRETS:
        for piece in text.split():
            assert len(piece) < 8 or piece not in note, piece  # nothing of what was said is copied
    assert "AKIAFAKE" not in note and "fake" not in note.lower()
    kept = {r["id"]: r["text"] for r in store._archived(crossings)}
    assert all(kept[i] for i in ids) and kept["5ec00009"] == "password=not-a-real-one"  # the plugin keeps what was said
    assert store.archive(path, crossings, whole=True) == 0 and noted(crossings) == ids  # noted once
    more = transcript(tmp_path, "keyed000-0002", [row("user", "5ec10001", 50, "and AKIA" + "FAKE" + "2" * 12)])
    store.archive(more, crossings)
    assert noted(crossings) == ids + ["5ec10001"] and note.splitlines()[0] in (crossings / "flagged.txt").read_text(
        encoding="utf-8"
    )


def test_status_and_look_from_a_shell_say_it_once_a_message_until_it_is_struck(tmp_path):
    crossings, _, ids = keyed(tmp_path)
    project = str(crossings.parent)
    sentence = FLAGGED.format
    status = through("status", "--cwd", project)[1]
    look = through("look", "--cwd", project)[1]
    for each in ids:
        assert status.count(sentence(each)) == 1 and look.count(sentence(each)) == 1, each
    assert sentence(ids[0]) == (
        f"A kept message looks like it holds a key or a password ({ids[0]}), and door.py strike "
        f"{ids[0]} removes it from the store."
    )
    for text in SECRETS:
        assert max(text.split(), key=len) not in status + look, text  # the id, and nothing of the message
    assert through("strike", ids[0], "--cwd", project)[0] == 0
    assert sentence(ids[0]) not in through("status", "--cwd", project)[1]
    assert (
        sentence(ids[0]) not in through("look", "--cwd", project)[1]
        and sentence(ids[1]) in through("look", "--cwd", project)[1]
    )
    assert ids[0] not in (crossings / "flagged.txt").read_text(encoding="utf-8")
    (crossings / "flagged.txt").write_text(
        (crossings / "flagged.txt").read_text(encoding="utf-8") + "0a0a0a0a\n", encoding="utf-8"
    )
    assert sentence("0a0a0a0a") not in through("status", "--cwd", project)[1]  # a note of what the store does not hold
    assert door.FLAGGED == FLAGGED


def test_the_session_is_never_told_which_message_it_was(tmp_path):
    crossings, path, ids = keyed(tmp_path)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent), CROSSING_COPY_KEY=KEY):
        for name in ("look", "status"):
            text = said(name)[0]
            assert "looks like it holds a key" not in text and "passphrase" not in text, name
    for text in (frame.compose(crossings), frame.compose(crossings, new=True)):
        assert "looks like it holds a key" not in text and "flagged" not in text
    assert "looks like it holds a key" not in through("look", "--bare", "--cwd", str(crossings.parent))[1]


# --- the second copy's staging --------------------------------------------------------------------


def stand_in(seen: list) -> types.SimpleNamespace:
    """hdiutil's `create` as a stand-in: it notes the folder it was handed and what was in it, and
    writes a small file in the image's place. No image is made and no Keychain is asked."""

    def run(argv, **_):
        folder = Path(argv[argv.index("-srcfolder") + 1])
        seen.append(
            {
                "folder": folder,
                "files": sorted(str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()),
                "mode": stat.S_IMODE(folder.stat().st_mode),
            }
        )
        Path(argv[-1]).write_bytes(b"not an image")
        return subprocess.CompletedProcess(argv, 0, b"", b"")

    return types.SimpleNamespace(run=run)


def stood_in(test):
    """For the length of a test, the image is made by the stand-in and read back the same, as the
    person makes it from their own terminal, where the passphrase is taken from the environment."""

    def run(tmp_path):
        tool, checks, seen = second.subprocess, second.verify, []
        second.subprocess, second.verify = stand_in(seen), lambda *_: True
        try:
            with at_terminal():
                return test(tmp_path, seen)
        finally:
            second.subprocess, second.verify = tool, checks

    run.__name__ = test.__name__  # one argument, as pytest and the runner below ask
    return run


@stood_in
def test_the_copy_stages_nothing_inside_the_home(tmp_path, seen):
    crossings, _ = home(tmp_path)
    before = tree(crossings)
    with set_to(CROSSING_COPY_KEY=KEY):
        out = second.make(crossings, tmp_path / "cloud", "project")
    assert out["copied"] and len(seen) == 1, out
    stage = seen[0]["folder"]
    assert (
        crossings.resolve() not in stage.resolve().parents
        and (tmp_path / "cloud").resolve() not in stage.resolve().parents
    )
    assert stage.parent == staging() and stage.name.startswith("crossing-copy-")
    assert seen[0]["files"] == ["hand-over.md", "said/session-.jsonl"] and seen[0]["mode"] == 0o700
    # taken away, and nothing of it is left in the home but its lock, empty, as an archive's is
    assert not stage.exists() and tree(crossings) == {**before, COPYING: b""}
    assert not (crossings / ".copy-stage").exists() and not (crossings / NOTE).exists()


def staged(note: Path) -> Path:
    """The stage a copy's note names: its first field."""
    return Path(note.read_text(encoding="utf-8").strip().split("\t")[0])


def killed_copy(tmp_path: Path, crossings: Path, **env: str) -> Path:
    """A copy killed once it staged, as the harness ends a hook that overran: the stage its note names."""
    bin_ = tmp_path / "bin"
    bin_.mkdir(exist_ok=True)
    (bin_ / "hdiutil").write_text("#!/bin/sh\nexec sleep 60\n", encoding="utf-8")  # an image tool that overruns
    (bin_ / "hdiutil").chmod(0o755)
    script = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); from crossing import record, second; "
        "record.terminal = lambda: True; second.make(Path(sys.argv[2]), Path(sys.argv[3]), 'project')"
    )  # the person's
    started = subprocess.Popen(
        [sys.executable, "-I", "-c", script, str(ROOT), str(crossings), str(tmp_path / "cloud")],
        env={**os.environ, "PATH": f"{bin_}{os.pathsep}{os.environ['PATH']}", "CROSSING_COPY_KEY": KEY, **env},
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    note = crossings / NOTE
    try:
        until = time.monotonic() + 20
        while not (note.exists() and (staged(note) / "said").exists()):
            assert time.monotonic() < until, "the copy was never staged"
            time.sleep(0.05)
    finally:
        os.killpg(started.pid, signal.SIGKILL)  # the run and its image tool
        started.wait(timeout=30)
    return staged(note)


@stood_in
def test_a_stage_a_killed_run_left_is_taken_away_by_the_next(tmp_path, seen):
    crossings, _ = home(tmp_path)
    left = killed_copy(tmp_path, crossings)
    assert not (crossings / ".copy-stage").exists()  # nothing staged inside the home
    assert (left / "said" / "session-.jsonl").exists()  # what the killed run left, where the note says
    with set_to(CROSSING_COPY_KEY=KEY):
        assert second.make(crossings, tmp_path / "cloud", "project")["copied"]
    assert not left.exists() and not (crossings / NOTE).exists() and not seen[0]["folder"].exists()


@stood_in
def test_a_stage_a_killed_copy_left_is_taken_away_by_the_next_whatever_its_temporary_folder(tmp_path, seen):
    # The next copy under another TMPDIR dropped the note of a killed copy's stage and left its plain files (pass 5, F2).
    crossings, _ = home(tmp_path)
    elsewhere = tmp_path / "tmp-old"
    elsewhere.mkdir()
    left = killed_copy(tmp_path, crossings, TMPDIR=str(elsewhere))
    assert left.parent == elsewhere.resolve() and (left / "said" / "session-.jsonl").exists()
    with set_to(CROSSING_COPY_KEY=KEY):
        assert second.make(crossings, tmp_path / "cloud", "project")["copied"]
    assert not left.exists() and not (crossings / NOTE).exists()
    assert list(elsewhere.iterdir()) == []  # whatever marked it went with it


@stood_in
def test_a_note_that_names_anything_but_a_stage_is_taken_away_alone(tmp_path, seen):
    crossings, _ = home(tmp_path)
    precious = tmp_path / "crossing-copy-precious"
    (precious / "said").mkdir(parents=True)
    (precious / "said" / "kept.jsonl").write_text("not the stage's\n", encoding="utf-8")
    data = tmp_path / "data"
    data.mkdir()
    for named in (str(precious), "crossing-copy-relative", str(staging() / "someone-elses")):
        (crossings / NOTE).write_text(named + "\n", encoding="utf-8")
        with set_to(CLAUDE_PLUGIN_DATA=str(data), CROSSING_COPY_KEY=KEY):
            assert second.make(crossings, tmp_path / "cloud", "project")["copied"], named
        assert not (crossings / NOTE).exists() and (precious / "said" / "kept.jsonl").exists(), named
        assert logged(data).splitlines()[-1].startswith("refused: the note of a copy's stage names no stage"), named
    gone = staging() / "crossing-copy-gone-already"
    (crossings / NOTE).write_text(f"{gone}\n", encoding="utf-8")
    with set_to(CLAUDE_PLUGIN_DATA=str(data)):
        second.cleared(crossings)  # a stage taken away already: the note goes, and nothing is said of it
    assert not (crossings / NOTE).exists() and len(logged(data).splitlines()) == 3
    second.cleared(crossings)  # and with no note, nothing is done


@stood_in
def test_a_note_whose_stage_bears_no_mark_of_its_token_is_taken_away_alone(tmp_path, seen):
    # A note names a stage and a token: a stage is taken away wherever it lies only where the file beside it holds that
    # token, so a note set by hand, or carried from elsewhere, empties no folder of the person's.
    crossings, _ = home(tmp_path)
    data = tmp_path / "data"
    data.mkdir()
    elsewhere = tmp_path / "elsewhere"
    precious = elsewhere / "crossing-copy-precious"
    (precious / "said").mkdir(parents=True)
    (precious / "said" / "kept.jsonl").write_text("not the stage's\n", encoding="utf-8")
    mark = elsewhere / "crossing-copy-precious.mark"
    other = elsewhere / "another-mark"
    other.write_bytes(b"0123\n")
    for how in ("none", "another token", "not text", "a link", "unreadable"):
        mark.unlink(missing_ok=True)
        if how == "another token":
            mark.write_text("not-this-token\n", encoding="utf-8")
        elif how == "not text":
            mark.write_bytes(b"\xff\xfe\n")
        elif how == "a link":
            mark.symlink_to(other)
        elif how == "unreadable":
            mark.write_text("0123\n", encoding="utf-8")
            mark.chmod(0)
        (crossings / NOTE).write_text(f"{precious}\t0123\n", encoding="utf-8")
        with set_to(CLAUDE_PLUGIN_DATA=str(data), CROSSING_COPY_KEY=KEY):
            assert second.make(crossings, tmp_path / "cloud", "project")["copied"], how
        assert not (crossings / NOTE).exists() and (precious / "said" / "kept.jsonl").exists(), how
        assert logged(data).splitlines()[-1].startswith("refused: the note of a copy's stage names no stage"), how
        if how == "unreadable":
            mark.chmod(0o600)
    assert other.read_bytes() == b"0123\n"


@stood_in
def test_a_left_stage_is_taken_away_file_by_file_following_no_link(tmp_path, seen):
    crossings, _ = home(tmp_path)
    outside = tmp_path / "outside"
    (outside / "inner").mkdir(parents=True)
    (outside / "inner" / "kept.txt").write_text("kept\n", encoding="utf-8")
    stage = Path(tempfile.mkdtemp(prefix=STAGE, dir=staging()))
    (stage / "said").mkdir()
    (stage / "said" / "session-.jsonl").write_text("{}\n", encoding="utf-8")
    (stage / "a-file").symlink_to(outside / "inner" / "kept.txt")
    (stage / "said" / "a-folder").symlink_to(outside / "inner", target_is_directory=True)
    (crossings / NOTE).write_text(f"{stage}\n", encoding="utf-8")
    with set_to(CROSSING_COPY_KEY=KEY):
        assert second.make(crossings, tmp_path / "cloud", "project")["copied"]
    assert not stage.exists() and not (crossings / NOTE).exists()
    assert (outside / "inner" / "kept.txt").read_text(encoding="utf-8") == "kept\n"  # what a link led to is untouched
    assert sorted(p.name for p in (outside / "inner").iterdir()) == ["kept.txt"]
    assert (second.STAGED, second.STAGE, second.staging()) == (NOTE, STAGE, staging())


@stood_in
def test_no_copy_is_staged_where_the_temporary_folder_lies_inside_the_home(tmp_path, seen):
    crossings, _ = home(tmp_path)
    (crossings / "tmp").mkdir()
    was = tempfile.tempdir
    tempfile.tempdir = str(crossings / "tmp")
    try:
        with set_to(CROSSING_COPY_KEY=KEY):
            out = second.make(crossings, tmp_path / "cloud", "project")
            (tmp_path / "cloud").mkdir(exist_ok=True)
            tempfile.tempdir = str(tmp_path / "cloud")
            inside = second.make(crossings, tmp_path / "cloud", "project")
    finally:
        tempfile.tempdir = was
    assert (
        out
        == inside
        == {"copied": False, "why": "the system's temporary folder lies inside the home or the copy's folder"}
    )
    assert seen == [] and list((crossings / "tmp").iterdir()) == [] and list((tmp_path / "cloud").iterdir()) == []
    assert not (crossings / NOTE).exists()


@stood_in
def test_a_copy_stages_its_files_under_the_homes_lock_and_makes_its_image_after_it(tmp_path, seen):
    # A copy staged while a strike rewrote the archive could keep the struck text in the newest image (a review).
    crossings, _ = home(tmp_path)
    name, held_then, copy = store._lock_name(crossings), [], second.shutil.copyfile

    def copying(source, target):  # each staged file: whether the home's lock is held as it is copied
        held_then.append(name in store._locks_here())
        return copy(source, target)

    making = second.subprocess.run

    def made(argv, **given):  # the image: whether the lock is held still as it is made
        held_then.append(("image", name in store._locks_here()))
        return making(argv, **given)

    second.shutil = types.SimpleNamespace(copyfile=copying)
    second.subprocess.run = made
    try:
        with set_to(CROSSING_COPY_KEY=KEY):
            assert second.make(crossings, tmp_path / "cloud", "project")["copied"]
    finally:
        second.shutil, second.subprocess.run = shutil, making
    assert held_then == [True, True, ("image", False)]  # the files under it, the image after it is let go
    assert name not in store._locks_here()

    stages = {p for p in staging().iterdir() if p.name.startswith(STAGE)}
    wait, store.WAIT = store.WAIT, 0.2
    held = store._locked(crossings)  # another act holds the home: an archive, a mark, a strike
    try:
        with set_to(CROSSING_COPY_KEY=KEY):
            out = second.make(crossings, tmp_path / "cloud", "project")
    finally:
        store._unlocked(crossings, held)
        store.WAIT = wait
    assert out == {"copied": False, "why": HELD} and len(seen) == 1  # nothing staged, and no image made
    assert not (crossings / NOTE).exists() and {p for p in staging().iterdir() if p.name.startswith(STAGE)} == stages
    assert [p.name for p in (tmp_path / "cloud").iterdir()] == ["project.dmg"]
    with set_to(CROSSING_COPY_KEY=KEY):
        assert second.make(crossings, tmp_path / "cloud", "project")["copied"]  # once it is let go, a copy is made


@stood_in
def test_one_copy_of_a_home_at_a_time_and_the_next_leaves_a_live_stage_alone(tmp_path, seen):
    # Two copies at once shared the note of a stage, and the second took away the first's while it was made (a review).
    crossings, _ = home(tmp_path)
    live = Path(tempfile.mkdtemp(prefix=STAGE, dir=staging()))  # the stage of a copy being made at this moment
    (live / "said").mkdir()
    (live / "said" / "session-.jsonl").write_text("staged\n", encoding="utf-8")
    (crossings / NOTE).write_text(f"{live}\n", encoding="utf-8")
    wait, store.WAIT = store.WAIT, 0.2
    other = store._held_at(crossings / COPYING)  # that copy holds the home's copy lock
    try:
        with set_to(CROSSING_COPY_KEY=KEY):
            out = second.make(crossings, tmp_path / "cloud", "project")
    finally:
        store._let_go(crossings / COPYING, other)
        store.WAIT = wait
    assert out == {"copied": False, "why": BUSY} and seen == []
    assert (live / "said" / "session-.jsonl").read_text(encoding="utf-8") == "staged\n"  # its stage is left as it was
    assert (crossings / NOTE).read_text(encoding="utf-8") == f"{live}\n"
    with set_to(CROSSING_COPY_KEY=KEY):  # once that copy is done or gone, the next takes a stage it left away
        assert second.make(crossings, tmp_path / "cloud", "project")["copied"]
    assert not live.exists() and not (crossings / NOTE).exists() and second.COPYING == COPYING


def making(during):
    """For the length of a test, an image is made by a stand-in that holds the staged files' bytes, so
    a test can tell which image stands; `during()` runs as it is made, after the home's lock is let go."""

    def run(test):
        def made(argv, **_):
            folder = Path(argv[argv.index("-srcfolder") + 1])
            during[0]()
            files = sorted(p for p in folder.rglob("*") if p.is_file())
            Path(argv[-1]).write_bytes(b"".join(p.read_bytes() for p in files))
            return subprocess.CompletedProcess(argv, 0, b"", b"")

        def ran(tmp_path):
            tool, checks = second.subprocess, second.verify
            second.subprocess, second.verify = types.SimpleNamespace(run=made), lambda *_: True
            try:
                with at_terminal(), set_to(CROSSING_COPY_KEY=KEY):
                    return test(tmp_path)
            finally:
                second.subprocess, second.verify = tool, checks

        ran.__name__ = test.__name__
        return ran

    return run


DURING = [lambda: None]  # what happens in the home while an image is made, for the test that sets it


@making(DURING)
def test_an_image_made_while_a_strike_took_words_is_not_put_in_place_and_one_made_while_words_came_is(tmp_path):
    # A copy staged before a strike and put in place after it kept the struck text in the newest image (pass 5, F1).
    crossings, path = home(tmp_path)
    STRUCK = "by the café".encode()  # the message a strike takes, and no label holds
    cloud = tmp_path / "cloud"
    image = cloud / "project.dmg"
    try:
        assert second.make(crossings, cloud, "project")["copied"] and STRUCK in image.read_bytes()
        later = transcript(tmp_path, "session-0002", [row("user", "77777777", 30, "A later word about the jib.")])
        DURING[0] = lambda: store.archive(later, crossings)  # words came while it was made: appended, it stands
        assert second.make(crossings, cloud, "project")["copied"], "an image of a home that only grew stands"
        assert STRUCK in image.read_bytes() and b"jib" not in image.read_bytes()
        DURING[0] = lambda: store.strike(crossings, A)  # a strike took words while it was made
        out = second.make(crossings, cloud, "project")
        assert out == {"copied": False, "why": CHANGED}, out
        assert STRUCK in image.read_bytes()  # the earlier image stands, as a strike says of an earlier copy
        assert sorted(p.name for p in cloud.iterdir()) == ["project.dmg"]  # and the one made meanwhile went
        DURING[0] = lambda: None
        assert second.make(crossings, cloud, "project")["copied"]  # the next takes the home as it stands
        assert STRUCK not in image.read_bytes() and b"jib" in image.read_bytes()
    finally:
        DURING[0] = lambda: None


IMAGE_TOOL = r'''"""hdiutil as a stand-in, for the tests alone and on every system: `create` keeps a folder's files
in one zip with a digest of the passphrase it is handed, `attach` lays them out in a fresh folder
under IMAGE_MOUNTS and names it on its last line as hdiutil does, and `detach` leaves it be. It
encrypts nothing. With IMAGE_TAMPERS set, what it lays out is not what went in; IMAGE_PAUSE
makes `create` take that many seconds."""
import hashlib, os, sys, tempfile, time, zipfile
from pathlib import Path

argv = sys.argv[1:]
key = hashlib.sha256(sys.stdin.buffer.read() if "-stdinpass" in argv else b"").hexdigest()
if argv[0] == "create":
    time.sleep(float(os.environ.get("IMAGE_PAUSE") or 0))  # an image that takes its time
    source = Path(argv[argv.index("-srcfolder") + 1])
    with zipfile.ZipFile(argv[-1], "w") as image:
        image.writestr(".key", key)
        for path in sorted(source.rglob("*")):
            if path.is_file():
                image.write(path, path.relative_to(source).as_posix())
elif argv[0] == "attach":
    try:
        image = zipfile.ZipFile(argv[-1])
    except (OSError, zipfile.BadZipFile):
        sys.exit("hdiutil: attach failed - image not recognized")
    with image:
        if image.read(".key").decode() != key:
            sys.exit("hdiutil: attach failed - Authentication error")
        mount = Path(tempfile.mkdtemp(dir=os.environ["IMAGE_MOUNTS"]))
        for name in image.namelist():
            if name != ".key":
                (mount / name).parent.mkdir(parents=True, exist_ok=True)
                (mount / name).write_bytes(image.read(name) + (b"otherwise" if os.environ.get("IMAGE_TAMPERS") else b""))
    print(f"/dev/disk9\tGUID_partition_scheme\t\n/dev/disk9s1\tApple_HFS\t{mount}")
'''


def test_the_image_is_opened_again_and_one_that_reads_back_otherwise_replaces_nothing_on_any_system(tmp_path):
    # The check by opening the image again ran only where macOS's hdiutil is: on Linux no line of it did.
    crossings, _ = home(tmp_path)
    tool, mounts, cloud = tmp_path / "image-tool", tmp_path / "mounts", tmp_path / "cloud"
    tool.mkdir()
    mounts.mkdir()
    (tool / "hdiutil.py").write_text(IMAGE_TOOL, encoding="utf-8")
    (tool / "hdiutil").write_text(
        f'#!/bin/sh\nexec "{sys.executable}" -I "{tool / "hdiutil.py"}" "$@"\n', encoding="utf-8"
    )
    (tool / "hdiutil").chmod(0o755)
    stray = tmp_path / "not-an-image.dmg"
    stray.write_bytes(b"not an image")
    with set_to(PATH=f"{tool}{os.pathsep}{os.environ['PATH']}", IMAGE_MOUNTS=str(mounts), CROSSING_COPY_KEY=KEY):
        with at_terminal():
            first = second.make(crossings, cloud, "project")
            image = (cloud / "project.dmg").read_bytes()
            with set_to(IMAGE_TAMPERS="1"):
                otherwise = second.make(crossings, cloud, "project")
        unread = second.verify(stray, {}, b"any key\0")
    assert first["copied"] and first["files"] == 2, first
    page = (crossings / "hand-over.md").read_bytes()
    opened = [(p / "hand-over.md").read_bytes() for p in mounts.iterdir()]
    assert sorted(opened) == sorted([page, page + b"otherwise"])  # each image opened again: as it went in, and not
    assert otherwise == {"copied": False, "why": "the image did not read back the same"}
    assert (cloud / "project.dmg").read_bytes() == image  # the earlier good copy stands
    assert sorted(p.name for p in cloud.iterdir()) == ["project.dmg"]  # and the new one went
    assert unread is False  # a file that is no image does not pass for one


def image_tools(tmp_path: Path) -> Path:
    """A folder for the front of the path: the image stand-in, and a Keychain that holds a passphrase."""
    tool = tmp_path / "image-tool"
    tool.mkdir()
    (tool / "hdiutil.py").write_text(IMAGE_TOOL, encoding="utf-8")
    (tool / "hdiutil").write_text(
        f'#!/bin/sh\nexec "{sys.executable}" -I "{tool / "hdiutil.py"}" "$@"\n', encoding="utf-8"
    )
    (tool / "security").write_text("#!/bin/sh\necho made-up-passphrase-for-a-test\n", encoding="utf-8")
    for name in ("hdiutil", "security"):
        (tool / name).chmod(0o755)
    (tmp_path / "mounts").mkdir()
    return tool


def a_cut(path: Path, project: Path, name: str = "PostCompact") -> dict:
    event = {"hook_event_name": name, "transcript_path": str(path), "cwd": str(project), "session_id": path.stem}
    return {**event, "trigger": "auto", "compact_summary": "A summary."} if name == "PostCompact" else event


def test_a_copy_a_cut_could_not_make_leaves_a_line_in_the_log(tmp_path):
    # A cut whose copy was given up for another copy, or a home held, left nothing anywhere (pass 5, F3).
    crossings, path = home(tmp_path)
    (crossings / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    log = Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "errors.log"
    before = log.read_text(encoding="utf-8") if log.exists() else ""
    other = store._held_at(crossings / COPYING)  # another copy of this home is being made
    try:
        done = ran("hook.py", stdin=json.dumps(a_cut(path, crossings.parent)), CLAUDE_CODE_ENTRYPOINT="cli")
    finally:
        store._let_go(crossings / COPYING, other)
    assert (done.returncode, done.stderr) == (0, ""), done
    added = (log.read_text(encoding="utf-8") if log.exists() else "")[len(before) :]
    assert f"not copied: {BUSY}" in added, added


def test_a_sessions_end_makes_its_copy_in_a_process_of_its_own(tmp_path):
    # Two lock waits and the image itself do not fit in the five seconds a session's end has (pass 5, F3).
    crossings, path = home(tmp_path)
    cloud = tmp_path / "cloud"
    (crossings / "copy").write_text(str(cloud) + "\n", encoding="utf-8")
    tool = image_tools(tmp_path)
    env = {
        "PATH": f"{tool}{os.pathsep}{os.environ['PATH']}",
        "IMAGE_MOUNTS": str(tmp_path / "mounts"),
        "IMAGE_PAUSE": "3",
        "CROSSING_WAIT": "1",
        "CLAUDE_CODE_ENTRYPOINT": "cli",
    }
    began = time.monotonic()
    done = ran("hook.py", stdin=json.dumps(a_cut(path, crossings.parent, "SessionEnd")), **env)
    took = time.monotonic() - began
    assert (done.returncode, done.stdout, done.stderr) == (0, "", ""), done
    assert took < 2.5, took  # the image takes three seconds: the hook did not wait for it
    image = cloud / f"{second.named(crossings.parent.resolve())}.dmg"
    until = time.monotonic() + 30
    while not image.exists():
        assert time.monotonic() < until, "the copy was never made"
        time.sleep(0.1)
    assert b"by the caf" in image.read_bytes()


def test_a_copy_lock_or_note_this_account_cannot_use_is_said_in_one_sentence(tmp_path):
    # A copy lock that was a folder, or could not be written, gave the person a traceback (pass 5, F4).
    crossings, _ = home(tmp_path)
    (crossings / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    lock, note = crossings / COPYING, crossings / NOTE
    for how in ("a folder", "not writable"):
        lock.mkdir() if how == "a folder" else (lock.write_text("", encoding="utf-8"), lock.chmod(0o400))
        done = as_the_module("copy", "--cwd", str(crossings.parent))
        assert (done.returncode, done.stdout, done.stderr) == (1, f"not copied: {UNUSABLE}\n", ""), (how, done)
        lock.rmdir() if how == "a folder" else (lock.chmod(0o600), lock.unlink())
    note.mkdir()  # the note of a stage that is no file
    done = as_the_module("copy", "--cwd", str(crossings.parent))
    assert (done.returncode, done.stdout, done.stderr) == (1, f"not copied: {UNREAD}\n", ""), done


def test_status_from_a_shell_says_once_that_the_passphrase_is_in_the_environment(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    with set_to(CROSSING_COPY_KEY=KEY):
        text = through("status", "--cwd", project)[1]
        assert text.count(COPY_KEY) == 1 and text.endswith(COPY_KEY + "\n") and KEY not in text
        assert COPY_KEY not in through("status", "--bare", "--cwd", project)[1]
    with set_to(CROSSING_COPY_KEY=None):
        assert COPY_KEY not in through("status", "--cwd", project)[1]
    assert door.COPY_KEY == COPY_KEY


# --- one archive at a time -------------------------------------------------------------------------

MANY = 3000


def test_two_archives_of_one_transcript_at_once_keep_each_message_once(tmp_path):
    """Real processes, let go at the same moment, each reading the transcript whole."""
    crossings, _ = home(tmp_path)
    rows = [
        row(
            "user" if n % 2 else "assistant",
            f"{0x30000000 + n:08x}",
            n % 60,
            f"Message {n} about the rigging, long enough to take a moment to read."
            if n % 2
            else [{"type": "text", "text": f"Reply {n}, as long as the message it answers, give or take."}],
        )
        for n in range(MANY)
    ]
    path = transcript(tmp_path, "rigging0-0001", rows)
    go = tmp_path / "go"
    script = (
        "import sys, time; from pathlib import Path; sys.path.insert(0, sys.argv[1]); from crossing import store\n"
        "while not Path(sys.argv[4]).exists(): time.sleep(0.002)\n"
        "print(store.archive(Path(sys.argv[2]), Path(sys.argv[3]), whole=True))"
    )
    started = [
        subprocess.Popen(
            [sys.executable, "-I", "-c", script, str(ROOT), str(path), str(crossings), str(go)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=os.environ.copy(),
        )
        for _ in range(3)
    ]
    time.sleep(1.0)  # each is started and waiting
    go.write_text("", encoding="utf-8")
    done = [each.communicate(timeout=120) for each in started]
    lines = (crossings / "said" / "rigging0.jsonl").read_text(encoding="utf-8").splitlines()
    ids = [json.loads(line)["uuid"] for line in lines]
    assert len(ids) == len(set(ids)) == MANY, (len(ids), len(set(ids)))
    assert [err for _, err in done] == ["", "", ""] and sorted(int(out) for out, _ in done) == [0, 0, MANY], done
    assert store.build(crossings)["his"] == 2 + MANY // 2


def test_a_message_an_older_make_kept_twice_is_built_and_counted_once(tmp_path):
    crossings, _ = home(tmp_path)
    page = crossings / "said" / "session-.jsonl"
    lines = page.read_text(encoding="utf-8").splitlines()
    page.write_text("\n".join(lines + lines[:1] + lines[2:3]) + "\n", encoding="utf-8")  # two messages, each kept twice
    held = store.build(crossings)
    assert (held["his"], held["session"]) == (2, 2)
    assert [s["id"] for s in store.thread(crossings, A, around=5)["said"]] == [A, B, D, E]
    assert "2 messages of the person's and 2 of the session's" in through("status", "--cwd", str(crossings.parent))[1]
    store.strike(crossings, A)  # both of its rows go
    assert A not in page.read_text(encoding="utf-8") and store.build(crossings)["his"] == 1
    (crossings / "struck.txt").write_text(
        (crossings / "struck.txt").read_text(encoding="utf-8") + f"{B}  # by hand\n", encoding="utf-8"
    )
    assert (
        B in page.read_text(encoding="utf-8") and store.build(crossings)["session"] == 1
    )  # struck by hand: both rows passed over


def test_an_archive_that_cannot_have_the_lock_in_time_does_nothing_and_says_so_once(tmp_path):
    crossings, path = home(tmp_path)
    later = transcript(
        tmp_path, "session-0002", [row("user", "77777777", 30, "Said while another archive held the home.")]
    )
    data = tmp_path / "data"
    data.mkdir()
    import fcntl

    holder = open(crossings / LOCK, "a")
    fcntl.flock(holder.fileno(), fcntl.LOCK_EX)
    was, store.WAIT = getattr(store, "WAIT", 5.0), 0.1
    try:
        with set_to(CLAUDE_PLUGIN_DATA=str(data)):
            marks = (crossings / store.MARKERS).read_text(encoding="utf-8")
            assert store.archive(later, crossings) == 0
        assert (crossings / store.MARKERS).read_text(encoding="utf-8") == marks  # no marker moved
        assert logged(data).count("busy: another archive held") == 1 and logged(data).endswith(
            "so session-0002.jsonl was not read this time\n"
        )
    finally:
        store.WAIT = was
        fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
        holder.close()
    assert store.archive(later, crossings) == 1  # the next reads it
    assert store.LOCK == LOCK


def test_where_there_is_no_flock_the_lock_is_a_file_made_only_where_none_is(tmp_path):
    crossings, path = home(tmp_path)
    lock = crossings / LOCK
    if lock.exists():  # flock's, which stays
        lock.unlink()
    was = getattr(store, "fcntl", None), getattr(store, "WAIT", 5.0)
    store.fcntl, store.WAIT = None, 0.1
    try:
        first = transcript(tmp_path, "session-0002", [row("user", "77777777", 30, "One.")])
        assert store.archive(first, crossings) == 1 and not lock.exists()  # made, and taken away after
        lock.write_text("", encoding="utf-8")  # held by another
        second_ = transcript(tmp_path, "session-0003", [row("user", "66666666", 31, "Two.")])
        assert store.archive(second_, crossings) == 0 and lock.exists()
        old = time.time() - store.STALE - 10
        os.utime(lock, (old, old))  # left by a process that ended before it could take it away
        assert store.archive(second_, crossings) == 1 and not lock.exists()
        assert store._left(lock) is True  # one gone already is no longer held
    finally:
        store.fcntl, store.WAIT = was
    # And as the module loads where there is no flock at all, as on Windows: a process of its own.
    script = (
        "import sys; from pathlib import Path; sys.path.insert(0, sys.argv[1]); sys.modules['fcntl'] = None\n"
        "from crossing import store\n"
        "print(store.fcntl is None, store.archive(Path(sys.argv[2]), Path(sys.argv[3])), Path(sys.argv[3], 'archive.lock').exists())"
    )
    third = transcript(tmp_path, "session-0004", [row("user", "55555555", 32, "Three.")])
    done = subprocess.run(
        [sys.executable, "-I", "-c", script, str(ROOT), str(third), str(crossings)],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert (done.returncode, done.stdout, done.stderr) == (0, "True 1 False\n", "")


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder)
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
