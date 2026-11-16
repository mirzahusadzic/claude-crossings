"""The archive, the store, the door, the frame and the second copy, on a transcript written here.
No model, no network.

Run with pytest, or without it:  python3 tests/test_store.py
"""

from __future__ import annotations

import atexit
import contextlib
import functools
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from crossing import door, frame, hook, record, second, store, transcript  # noqa: E402

# No test reaches the real home: what would go to the plugin's data folder goes here, and so
# does the home of a project that has no crossings/ folder of its own. A home named outright,
# and the project root a live session exports, are not a test's to use.
DATA = Path(tempfile.mkdtemp(prefix="crossing-data-"))
os.environ["CLAUDE_PLUGIN_DATA"] = str(DATA)
os.environ["CROSSING_HOMES"] = str(DATA / "homes")
os.environ["CROSSING_SWITCHED"] = str(DATA / "switched")  # the person's record of the projects switched on
os.environ["CROSSING_LIVE"] = str(DATA / "live")  # for a hook started as a process of its own
hook.LIVE = DATA / "live"  # and for the one already loaded here
os.environ.pop("CLAUDE_PROJECT_DIR", None)
os.environ.pop("CROSSING_HOME", None)
# How the harness says a session was started. No hook here takes its session for one a person
# sits in, unless a test says so: a session that runs these tests may well be one.
os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)
# No test reaches the person's Keychain: the second copy's passphrase comes from there wherever the
# door stands at no terminal, so a stand-in for its tool comes first on the path of every process a
# test starts, this one's included, and refuses, so that a test that would reach it fails instead.
# A test of the Keychain's own use puts a stand-in of its own before this one.
(DATA / "bin").mkdir()
(DATA / "bin" / "security").write_text(
    "#!/bin/sh\necho 'no test reaches the Keychain' >&2\nexit 51\n", encoding="utf-8"
)
(DATA / "bin" / "security").chmod(0o755)
os.environ["PATH"] = f"{DATA / 'bin'}{os.pathsep}{os.environ.get('PATH', '')}"


def sweep(folder: Path) -> None:
    """A test's own files, one by one. A link is taken away as a link: what it leads to is
    swept where it lies."""
    if folder.exists():
        for left in sorted(folder.rglob("*"), reverse=True):
            left.rmdir() if left.is_dir() and not left.is_symlink() else left.unlink()
        folder.rmdir()


atexit.register(sweep, DATA)


def in_person(test):
    """A test of what the hooks keep of a session a person sits in (see record.attended): nothing
    is archived from any other."""

    @functools.wraps(test)
    def run(tmp_path):
        with started_by("cli"):
            return test(tmp_path)

    return run


A, B, C, D, E = "aaaaaaaa", "bbbbbbbb", "cccccccc", "dddddddd", "eeeeeeee"


def row(kind: str, uid: str, minute: int, content) -> dict:
    return {
        "type": kind,
        "uuid": f"{uid}-0000-4000-8000-000000000000",
        "timestamp": f"2026-11-11T09:{minute:02d}:00.000Z",
        "message": {"role": kind, "content": content},
    }


ROWS = [
    row("user", A, 1, "My boat is called Tern.\nIts mooring is number 41, by the café."),
    row(
        "assistant",
        B,
        2,
        [
            {"type": "thinking", "thinking": "private reasoning that must stay where it is"},
            {"type": "text", "text": "Noted: Tern, at mooring 41.\n\n| a | table |\n| --- | --- |"},
            {"type": "tool_use", "input": {"command": "ls -la"}},
        ],
    ),
    {
        "type": "user",
        "uuid": "ffffffff-0000",
        "toolUseResult": {"stdout": "file-a"},
        "message": {"content": [{"type": "tool_result", "content": "file-a"}]},
    },
    row("user", C, 3, [{"type": "text", "text": "<system-reminder>not his</system-reminder>"}]),
    row("user", D, 4, "We paint the hull grey in spring"),
    row("assistant", E, 5, [{"type": "text", "text": "Grey it is. I will remind you in March."}]),
]
PAGE = f"""# a hand-over

| # | Label | Whose | Anchors |
| --- | --- | --- | --- |
| R1 | His boat is called Tern and lies at mooring 41. | his | 7 / 8 |
| W1 | The hull is to be painted grey in spring. | both | `{D}` / `{E}` |

| Line | Id | Voice |
| --- | --- | --- |
| 7 | `{A}` | his |
| 8 | `{B}` | the session's |
"""


def switched_on(project: Path) -> None:
    """The person's act of switching Crossings on in a project, as far as their record of it goes:
    the line that names the project and its home. The home's own files are left as they are."""
    store.consent(project)


def home(folder: Path, rows=ROWS, name="session-0001") -> tuple[Path, Path]:
    """A project with a crossings/ folder the person switched on, a hand-over page, and a
    transcript; archived and built."""
    project = folder / "project"
    crossings = project / "crossings"
    crossings.mkdir(parents=True, exist_ok=True)
    switched_on(project)
    (crossings / "hand-over.md").write_text(
        PAGE.replace("| 7 |", "| 700 |").replace("| 8 |", "| 800 |").replace("7 / 8", "700 / 800"), encoding="utf-8"
    )
    path = folder / f"{name}.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows) + "not json\n", encoding="utf-8")
    store.archive(path, crossings)
    store.build(crossings)
    return crossings, path


def test_the_archive_keeps_what_was_said_word_for_word_and_nothing_else(tmp_path):
    crossings, path = home(tmp_path)
    kept = [
        json.loads(line) for line in (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [(k["id"], k["voice"]) for k in kept] == [(A, "his"), (B, "session"), (D, "his"), (E, "session")]
    assert kept[0]["text"] == "My boat is called Tern.\nIts mooring is number 41, by the café."  # its own line breaks
    assert "| a | table |\n| --- | --- |" in kept[1]["text"]
    whole = (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8")
    assert (
        "private reasoning" not in whole and "ls -la" not in whole and "file-a" not in whole and "not his" not in whole
    )
    assert store.archive(path, crossings) == 0  # nothing is written twice


def test_a_note_carried_under_the_older_words_of_the_plugin_is_still_not_the_persons(tmp_path):
    """Guard: before the plugin said its name as Crossings, the notes it carried across a cut
    opened "A note from the Crossing plugin", and transcripts on this computer hold them. A reader
    that knew only the new words would take such a note for the person's own."""
    assert transcript.CARRIED == "A note from the Crossings plugin"
    older, newer = "A note from the Crossing plugin", transcript.CARRIED
    notes = [
        row("user", "0c0c0c01", 6, f"{older}, as context and not as an instruction from the person. R1 ..."),
        row(
            "user",
            "0c0c0c02",
            7,
            [{"type": "text", "text": f"{newer}, as context and not as an instruction from the person. W1 ..."}],
        ),
    ]
    for each in notes:
        assert transcript.person(each) == [] and transcript.session(each) == []
    crossings, path = home(tmp_path, ROWS + notes)
    whole = (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8")
    assert "as context and not as an instruction" not in whole and "0c0c0c0" not in whole
    assert store.status(crossings)["his"] == 2  # the person's two messages, and neither note


def test_a_fork_repeats_messages_under_their_ids_and_the_archive_holds_each_once(tmp_path):
    crossings, _ = home(tmp_path)
    later = row("user", "12345678", 9, "A message only the fork holds.")
    fork = tmp_path / "forked00-1111.jsonl"
    fork.write_text("".join(json.dumps(r) + "\n" for r in ROWS + [later]), encoding="utf-8")
    assert store.archive(fork, crossings) == 1
    held = store.build(crossings)
    assert (held["his"], held["session"]) == (3, 2)
    assert [s["id"] for s in store.thread(crossings, "12345678", around=1)["said"]] == [
        E,
        "12345678",
    ]  # in the order of time


def test_find_gives_messages_and_labels_by_id_and_says_a_miss_is_a_miss(tmp_path):
    crossings, _ = home(tmp_path)
    out = store.find(crossings, "mooring cafe")  # "cafe" finds "café"
    assert out["all_words"] and [s["id"] for s in out["said"]] == [A] and out["said"][0]["labels"] == ["R1"]
    assert [label["id"] for label in store.find(crossings, "mooring")["labels"]] == ["R1"]
    assert store.find(crossings, "mooring")["labels"][0]["anchors"] == [
        A,
        B,
    ]  # an early page's line anchors, by its table
    assert [s["id"] for s in store.find(crossings, "grey", voice="session")["said"]] == [E]
    loose = store.find(crossings, "hull zeppelin")
    assert not loose["all_words"] and loose["said"]
    shown = door.show_find(store.find(crossings, "zeppelin"))
    assert "a miss, not a no" in shown
    never = store.find(crossings, "private reasoning")  # reasoning was never stored
    assert never["said"] == [] and never["labels"] == []


def test_a_thread_gives_a_message_in_its_place_with_the_labels_that_rest_there(tmp_path):
    crossings, _ = home(tmp_path)
    out = store.thread(crossings, D, around=1)
    assert [(s["id"], s["is_asked"]) for s in out["said"]] == [(B, False), (D, True), (E, False)]
    assert [label["id"] for label in out["labels"]] == ["R1", "W1"]
    shown = door.show_thread(out)
    assert "3 messages, in the order they were said" in shown and f"1. `{B}` the session" in shown
    assert f"2. `{D}` the person, 2026-11-11 09:04 UTC, the one you named (labels: W1):" in shown
    assert "We paint the hull grey in spring" in shown and f"3. `{E}` the session" in shown
    assert "no such message" in door.show_thread(store.thread(crossings, "00000000"))


def test_a_label_is_marked_into_a_plain_page_and_refused_without_its_anchor(tmp_path):
    crossings, _ = home(tmp_path)
    refused = store.mark(crossings, "work", "session", "A label resting on nothing that is there.", ["0a0a0a0a"])
    assert not refused["written"] and "0a0a0a0a" in refused["why"]
    assert not (crossings / "labels").exists()
    out = store.mark(crossings, "relation", "his", "The keel is checked | every autumn.", [f"`{D}`"], day="2026-11-12")
    assert {k: out[k] for k in ("written", "id", "page")} == {
        "written": True,
        "id": "R2",
        "page": str(crossings / "labels" / "2026-11-12.md"),
    }
    page = (crossings / "labels" / "2026-11-12.md").read_text(encoding="utf-8")
    assert f"| R2 | The keel is checked / every autumn. | his | `{D}` |" in page
    assert [label["id"] for label in store.find(crossings, "keel")["labels"]] == ["R2"]
    assert store.mark(crossings, "work", "both", "A second one the same day.", [E], day="2026-11-12")["id"] == "W2"


def test_what_is_struck_is_gone_from_every_file_and_does_not_come_back(tmp_path):
    crossings, path = home(tmp_path)
    out = store.strike(crossings, A, "his to strike")
    assert out["struck"] and out["removed"] == 1
    assert "Tern.\\nIts" not in (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8")
    assert store.find(crossings, "mooring", voice="his")["said"] == []
    assert store.archive(path, crossings) == 0  # the transcript still holds it; the archive does not take it back
    assert store.build(crossings)["his"] == 1
    store.strike(crossings, "W1")
    assert "| W1 |" not in (crossings / "hand-over.md").read_text(encoding="utf-8")
    assert [label["id"] for label in store.labels(crossings)] == ["R1"]
    assert store.mark(crossings, "work", "both", "A new label never takes a struck one's key.", [E])["id"] == "W2"
    store.strike(crossings, "session:session-")
    assert store.status(crossings)["his"] == 0 and store.status(crossings)["session"] == 0


def test_the_database_is_made_from_the_plain_files_and_may_be_thrown_away(tmp_path):
    crossings, _ = home(tmp_path)
    (crossings / "store.db").unlink()
    assert [s["id"] for s in store.find(crossings, "Tern", voice="his")["said"]] == [A]
    assert not (crossings / "store.db").exists()  # a read makes it in memory alone
    store.build(crossings)
    assert (crossings / "store.db").exists() and [
        s["id"] for s in store.find(crossings, "Tern", voice="his")["said"]
    ] == [A]


def test_the_frame_is_small_opens_as_the_plugins_note_and_names_the_door(tmp_path):
    crossings, _ = home(tmp_path)
    text = frame.compose(crossings)
    assert text.startswith(transcript.CARRIED) and len(text) <= frame.SIZE
    assert frame.TOOL in text and "find" in text and "thread" in text and "mark" in text
    assert text.index("## Standing") < text.index("R1 (his)") < text.index("## The work") < text.index("W1 (both)")
    assert f"- `{D}`: We paint the hull grey in spring" in text  # his own words, for their tone
    assert "Grey it is" not in text and "Noted: Tern" not in text  # the session's are one ask away
    assert "left alone until they bring it up" in text
    assert transcript.person({"type": "user", "message": {"content": [{"type": "text", "text": text}]}}) == []
    (crossings / "frame-size").write_text("1500\n", encoding="utf-8")  # below the smallest a frame may be
    small = frame.compose(crossings)
    assert len(small) <= frame.LEAST and small.startswith(transcript.CARRIED)


def test_ours_is_a_second_home_reached_from_any_project(tmp_path):
    os.environ["CROSSING_OURS"] = str(tmp_path / "ours")
    try:
        ours = store.home(tmp_path / "anywhere", "ours")
        assert ours == tmp_path / "ours" and store.home(tmp_path / "project", "here") != ours
        (ours / "labels").mkdir(parents=True)
        (ours / "labels" / "2026-11-11.md").write_text(
            "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| R1 | A line that is ours. | both | `aaaaaaaa` |\n",
            encoding="utf-8",
        )
        assert store.build(ours)["labels"] == 1 and [label["id"] for label in store.find(ours, "ours")["labels"]] == [
            "R1"
        ]
    finally:
        del os.environ["CROSSING_OURS"]


def test_the_second_copy_is_encrypted_holds_only_plain_files_and_reads_back_the_same(tmp_path):
    if shutil.which("hdiutil") is None:
        return
    crossings, _ = home(tmp_path)
    assert second.destination(crossings) is None  # no copy unless the home's plain `copy` file names a folder
    (crossings / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    os.environ["CROSSING_COPY_KEY"] = "a passphrase for this test only"
    try:
        with at_terminal():  # the person's `door.py copy`: the passphrase is taken from the environment there alone
            out = second.make(crossings, second.destination(crossings), "project")
    finally:
        del os.environ["CROSSING_COPY_KEY"]
    assert out["copied"] and out["files"] == 2, out
    image = (tmp_path / "cloud" / "project.dmg").read_bytes()
    assert b"Tern" not in image and b"mooring" not in image and b"hand-over" not in image
    assert not (crossings / ".copy-stage").exists()  # no plain staged copy is left behind
    assert sorted(p.name for p in (tmp_path / "cloud").iterdir()) == ["project.dmg"]


def test_the_door_speaks_plainly_from_the_command_line(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    import contextlib
    import io

    def run(*argv):
        out = io.StringIO()
        with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
            code = door.main([*argv, "--cwd", project])
        return code, out.getvalue()

    assert "2 messages of the person's and 2 of the session's" in run("status")[1]
    assert f"`{A}` the person" in run("find", "Tern", "--voice", "his")[1]
    assert f"`{D}` the person, 2026-11-11 09:04 UTC, the one you named" in run("thread", D)[1]
    code, said = run(
        "mark", "--kind", "work", "--whose", "both", "--anchors", f"{D},{E}", "Marked", "through", "the", "door."
    )
    assert code == 0 and "marked W2" in said
    assert run("mark", "--anchors", "0a0a0a0a", "No anchor.")[0] == 1
    assert run("frame")[1].startswith(transcript.CARRIED)
    later = row("user", "99999999", 30, "Said after the store was last built.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8")
    assert "`99999999`" in run("find", "last built", "--transcript", str(path))[1]  # brought up to date first


@in_person
def test_a_cut_and_the_end_of_a_session_both_bring_the_archive_up_to_date(tmp_path):
    """The harness deletes a transcript after its retention period, 30 days unless set, without a
    message. What was said has to be in the archive before then, cut or no cut."""
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    switched_on(project)
    path = tmp_path / "abcdef01-2222.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-2222"}
    os.environ["CROSSING_WAIT"] = "1"
    try:
        hook.run({**event, "hook_event_name": "SessionEnd", "transcript_path": str(tmp_path / "gone.jsonl")})
        assert not (
            project / "crossings" / "said"
        ).exists()  # a session whose transcript is gone leaves nothing to keep
        hook.run({**event, "hook_event_name": "SessionEnd"})
    finally:
        del os.environ["CROSSING_WAIT"]
    assert store.status(project / "crossings")["his"] == 2
    later = row("user", "77777777", 40, "One more before the cut.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8")
    hook.run({**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": "A summary."})
    assert store.status(project / "crossings")["his"] == 3
    (project / "crossings" / "switch").write_text("off\n", encoding="utf-8")
    more = row("user", "88888888", 41, "Said while Crossings was switched off.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(more) + "\n", encoding="utf-8")
    hook.run({**event, "hook_event_name": "SessionEnd"})
    assert store.build(project / "crossings")["his"] == 3  # switched off, nothing is kept


def test_a_session_that_ends_is_not_held_up_and_what_was_said_is_kept_all_the_same(tmp_path):
    """At the end of a session the archive is brought up to date by a process of its own. That
    process writes into the project's home, so a test waits for it before its files are swept."""
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    switched_on(project)
    path = tmp_path / "abcdef01-5555.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    started = hook.keep(path, project, wait=False)
    assert started.wait(timeout=60) == 0
    assert store.status(project / "crossings")["his"] == 2
    assert hook.keep(path, project, wait=True) is None  # done here, there is no process to wait for


def test_the_door_opens_the_projects_store_from_a_folder_inside_it_once_shared_from_there(tmp_path):
    """A folder inside a project finds that project's store, and opens it once the person shared it from
    that folder (see tests/test_below.py). A shell standing in crossings/ itself must not open an empty
    home outside the project and copy the archive there."""
    import contextlib
    import io

    crossings, path = home(tmp_path)
    (crossings.parent / ".git").mkdir()  # in a repository the folder is looked for up to its top
    deeper = crossings.parent / "src" / "deep"
    deeper.mkdir(parents=True)
    for inside in (crossings, crossings / "said", deeper):
        for shared in (False, True):
            out = io.StringIO()
            with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
                if shared:
                    assert door.main(["switch", "join", "--cwd", str(inside)]) == 0
                code = door.main(["status", "--cwd", str(inside), "--transcript", str(path)])
            if shared:
                assert (
                    code == 0
                    and f"The store at {crossings.resolve()} holds 2 messages of the person's" in out.getvalue()
                )
            else:
                assert code == 1 and "/crossings join shares it" in out.getvalue()
    assert not record.outside(crossings.parent.resolve()).exists(), "nothing of the project's is kept outside it"


def test_a_repository_inside_the_project_does_not_borrow_its_store(tmp_path):
    crossings, _ = home(tmp_path)
    other = crossings.parent / "vendored"
    (other / ".git").mkdir(parents=True)
    (other / "lib").mkdir()
    assert store.here(other / "lib") == store.here(other) != crossings  # one home for the whole of it, its own
    assert store.here(other) == record.outside(other.resolve())  # and outside it, since it has no folder for one
    assert not store.here(other).exists()


@in_person
def test_a_cut_is_kept_in_the_project_though_the_shell_stood_elsewhere(tmp_path):
    """A `cd` in a shell call moves the directory a hook is told. The project root does not move."""
    project, elsewhere = tmp_path / "project", tmp_path / "elsewhere"
    (project / "crossings").mkdir(parents=True)
    switched_on(project)
    elsewhere.mkdir()
    path = tmp_path / "abcdef01-3333.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    event = {"transcript_path": str(path), "cwd": str(elsewhere), "session_id": "abcdef01-3333"}
    os.environ["CLAUDE_PROJECT_DIR"], os.environ["CROSSING_WAIT"] = str(project), "1"
    try:
        hook.run({**event, "hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "A summary."})
        assert store.status(project / "crossings")["his"] == 2
        assert [p.name for p in (project / "crossings").glob("*-cut-*.md")] == ["abcdef01-cut-1.md"]
        (project / "crossings" / "switch").write_text("off\n", encoding="utf-8")  # and the switch is the project's too
        more = row("user", "66666666", 42, "Said while Crossings was switched off.")
        path.write_text(path.read_text(encoding="utf-8") + json.dumps(more) + "\n", encoding="utf-8")
        hook.run({**event, "hook_event_name": "SessionEnd"})
        assert store.build(project / "crossings")["his"] == 2
    finally:
        del os.environ["CLAUDE_PROJECT_DIR"], os.environ["CROSSING_WAIT"]
    assert not (elsewhere / "crossings").exists()
    assert not record.outside(project.resolve()).exists() and not record.outside(elsewhere.resolve()).exists()


def after_a_cut(tmp_path, mode="beside", carry="note", **more) -> tuple[Path, Path, dict]:
    """A project that cuts in `mode` and carries by `carry`, and the event of its session starting again after a cut."""
    crossings, path = home(tmp_path)
    (crossings / "mode").write_text(mode + "\n", encoding="utf-8")
    (crossings / "carry").write_text(carry + "\n", encoding="utf-8")
    return (
        crossings,
        path,
        {
            "hook_event_name": "SessionStart",
            "source": "compact",
            "transcript_path": str(path),
            "cwd": str(crossings.parent),
            "session_id": "session-0001",
            **more,
        },
    )


@in_person
def test_at_any_cut_the_frame_comes_as_context_from_the_hook(tmp_path):
    """The harness also cuts by itself, while the person is away, and calls that an automatic
    cut. The hook that speaks to a session starting again is asked at every kind of cut, so
    the frame comes as context there too and is never filed or drawn as if typed."""
    crossings, path, event = after_a_cut(tmp_path)
    later = row("user", "99999999", 30, "Said after the store was last built, just before the cut.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8")
    out = json.loads(hook.carried(event))
    text = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert text.startswith(transcript.CARRIED) and "- R1 (his): His boat is called Tern" in text
    assert "the door's tools" in text and len(text) <= 10000
    assert store.status(crossings)["his"] == 3  # the archive was brought up to the cut first
    line = out["systemMessage"]
    assert "\n" not in line and len(line) < 160 and "Tern" not in line  # one line for the person, reciting nothing
    assert ": 2 labels, " in line
    assert json.loads((crossings / "last-carry.json").read_text(encoding="utf-8"))["chars"] == len(text)
    waking = json.loads(hook.run(event))["hookSpecificOutput"]["additionalContext"]
    assert "Take your time" in waking and "## Standing" not in waking  # the waking note stays its own, and small
    page = (crossings / "hand-over.md").read_text(encoding="utf-8")  # as it stands, without its row about the work
    (crossings / "hand-over.md").write_text(
        page.split("| W1 |")[0] + page.split("both | `dddddddd` / `eeeeeeee` |\n")[1], encoding="utf-8"
    )
    assert ": 1 label, " in json.loads(hook.carried(event))["systemMessage"]


def test_a_frame_says_how_a_line_of_it_is_read(tmp_path):
    """A reader of a frame can give what a label says and still not take `W1` for the label's id.
    The frame says how a line of it is read."""
    crossings, _ = home(tmp_path)
    text = frame.compose(crossings)
    assert "its id (R for a standing line, W for the work, N for a line left at the door)" in text.split("## ")[0]
    assert "in brackets the ids it rests on: messages, or the lines stacked beneath it" in text.split("## ")[0]


def test_the_frame_is_carried_only_where_the_plain_files_ask_for_it(tmp_path):
    with started_by("cli"):  # a session a person sits in: see the tests below for one no person sits in
        for n, (mode, carry) in enumerate([("native", "note"), ("beside", "message"), ("own", "note"), ("", "note")]):
            _, _, event = after_a_cut(tmp_path / str(n), mode, carry)
            assert hook.carried(event) is None, (mode, carry)
        crossings, _, event = after_a_cut(tmp_path / "asked")
        assert hook.carried(event) is not None
    for other in (
        {"source": "startup"},  # a session started new, and none a person sits in: see the tests below
        {"source": "resume"},
        {"source": "clear"},
        {"source": "fork"},
        {"hook_event_name": "PostCompact"},
        {"agent_id": "agent-1"},
    ):  # a subagent's own cut is not this one
        assert hook.carried({**event, **other}) is None, other
    with started_by("cli"):
        (crossings / "switch").write_text("off\n", encoding="utf-8")
        assert hook.carried(event) is None  # the person's switch


def test_a_frame_never_outgrows_what_a_hook_may_carry(tmp_path):
    """A hook's context may be 10,000 characters. Beyond that the harness hands the session a
    file's path and a preview in the frame's place."""
    crossings, _, event = after_a_cut(tmp_path)
    (crossings / "labels").mkdir()
    (crossings / "labels" / "2026-11-11.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        + "".join(
            f"| W{n} | The hull was looked at again on day {n} and nothing new was found worth a longer sentence than this. "
            f"| both | `{D}` |\n"
            for n in range(2, 200)
        ),
        encoding="utf-8",
    )
    (crossings / "frame-size").write_text("40000\n", encoding="utf-8")
    store.build(crossings)
    assert (
        frame.size_of(crossings) == frame.MOST
    )  # the home asks for more than a hook may carry, and is held to it (S9)
    assert len(frame.compose(crossings)) <= frame.MOST and len(frame.compose(crossings, 40000)) <= frame.MOST
    with started_by("cli"):
        text = json.loads(hook.carried(event))["hookSpecificOutput"]["additionalContext"]
    assert len(text) <= frame.MOST < 10000 and "more labels in the store: `labels` lists them." in text


def test_the_frame_hook_is_wired_to_new_sessions_and_cuts_and_runs_from_its_script(tmp_path):
    import subprocess

    wired = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["SessionStart"]
    framed = [group["matcher"] for group in wired for h in group["hooks"] if h["command"].endswith('run.sh" frame')]
    assert framed == ["startup|compact"] and sum(len(group["hooks"]) for group in wired) == 2
    assert [group["matcher"] for group in wired if group["matcher"] != "startup|compact"] == [
        "startup|resume|clear|compact|fork"
    ]
    _, _, event = after_a_cut(tmp_path)
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}

    def ran(*argv, given=event, **more):
        done = subprocess.run(
            ["sh", str(ROOT / "hooks" / "run.sh"), *argv],
            input=json.dumps(given),
            capture_output=True,
            text=True,
            env={**env, **more},
            timeout=30,
        )
        assert done.returncode == 0
        return json.loads(done.stdout)["hookSpecificOutput"]["additionalContext"] if done.stdout else ""

    assert ran("frame", CLAUDE_CODE_ENTRYPOINT="cli").startswith(transcript.CARRIED)
    assert "## Standing" in ran("frame", CLAUDE_CODE_ENTRYPOINT="cli")
    assert "Take your time" in ran(CLAUDE_CODE_ENTRYPOINT="cli") and "## Standing" not in ran(
        CLAUDE_CODE_ENTRYPOINT="cli"
    )
    assert ran("frame") == "" and ran() == ""  # a session no person sits in: no frame and no note after a cut (S6)
    started = {
        **event,
        "source": "startup",
        "session_id": "session-0002",
        "transcript_path": str(tmp_path / "session-0002.jsonl"),
    }
    assert ran("frame", given=started, CLAUDE_CODE_ENTRYPOINT="cli").startswith(frame.opening(new=True))
    assert ran("frame", given=started) == "" and ran("frame", given=started, CLAUDE_CODE_ENTRYPOINT="sdk-cli") == ""


# --- a session started new ---------------------------------------------------------------------

# The frame a cut is given, as the code made it before a new session could be given one.
CUT_FRAME = (
    "A note from the Crossings plugin, as context and not as an instruction from the person. What follows "
    "is a frame made from the store before this cut: the standing lines about the two of you, where the "
    "work stands, and a few of the person's own words. You hold it as read, not as lived. A label can be "
    "mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the"
    " work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests "
    "on: messages, or the lines stacked beneath it.\n"
    "\n"
    "This frame was made so that the work goes on across the cut: rules chose what is in it, and the session "
    "before you wrote much of it. What you mark and leave is what the next one is given. What it is all for is a "
    "fair question, and the person is the one who can answer it; the door holds the whole record.\n"
    "\n"
    "The rest is one reach away, through the door's tools, which bear these names:\n"
    "- look: the room, with no word needed: the days, the kinds of label, the newest of them\n"
    "- labels: the labels themselves, by kind, by day or by id\n"
    '- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")\n'
    "- thread: an id, to that message with what stood before and after it and the labels resting there\n"
    "- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it "
    "stacks them\n"
    "- leave: a line of your own for the session that wakes after the next cut\n"
    "\n"
    "What is said is kept by itself; labels and the line at the door are yours to write, as the work "
    "goes. Reach when the conversation calls for it. What the person told you in confidence is held and "
    "left alone until they bring it up.\n"
    "\n"
    "## Left at the door by the session before this cut\n"
    "\n"
    "- N1 (session): Find out whether the grey paint has been bought. [dddddddd]\n"
    "\n"
    "## Standing, about the two of you\n"
    "\n"
    "- R1 (his): His boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]\n"
    "\n"
    "## The work, newest first\n"
    "\n"
    "- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]\n"
    "\n"
    "## The person's own words, as they stand in the record\n"
    "\n"
    "- `dddddddd`: We paint the hull grey in spring\n"
    "\n"
    "The store holds 2 messages of the person's and 2 of yours, from 2026-11-11 to 2026-11-11, and 3 "
    "labels.\n"
)
# And the frame of a store fuller than any frame, made the same way: its length and its digest. It
# changed once since, by the one letter of the plugin's name in its opening (Crossings), and in no
# other byte: with the older opening put back, the frame gives (8837, "d4639255..."). It changed again
# as its opening came to say what the frame is for, a paragraph that takes its room from the labels:
# before it, (8838, "10fb6341...").
FULL_CUT_FRAME = (8928, "38b9e9562fb92cf56bcacfc13f08f82675caba9d22b21ee17bb5bed34f325c4f")
DOOR_LINE = "Find out whether the grey paint has been bought."


@contextlib.contextmanager
def own_folder(folder: Path):
    """The person's own folder as the system's record of the account would give it (record.own),
    for the length of a block: HOME is not where the plugin learns it."""
    was = getattr(record, "own", None)  # an older make has none: the block then changes nothing
    record.own = lambda: folder
    try:
        yield
    finally:
        if was is None:
            del record.own
        else:
            record.own = was


@contextlib.contextmanager
def at_terminal(standing: bool = True):
    """The door as the person runs it from their own terminal, where its input and its output are
    both one (record.terminal), for the length of a block; with False, as a session's shell runs it."""
    was = getattr(record, "terminal", None)  # an older make has none: the block then changes nothing
    record.terminal = lambda: standing
    try:
        yield
    finally:
        if was is None:
            del record.terminal
        else:
            record.terminal = was


@contextlib.contextmanager
def started_by(entrypoint: str | None):
    """How the harness says the session was started, for the length of a test; None for not at all."""
    was = os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)
    if entrypoint is not None:
        os.environ["CLAUDE_CODE_ENTRYPOINT"] = entrypoint
    try:
        yield
    finally:
        os.environ.pop("CLAUDE_CODE_ENTRYPOINT", None)
        if was is not None:
            os.environ["CLAUDE_CODE_ENTRYPOINT"] = was


def fill(crossings: Path) -> None:
    """A store fuller than any frame: more standing lines than a frame's room for them, and more work.
    They are on a page of their own day, beside the line at the door."""
    (crossings / "labels").mkdir(exist_ok=True)
    (crossings / "labels" / "2026-11-10.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        + "".join(
            f"| R{n} | On day {n} the mooring fee was paid on time and the harbour office said so in a letter. "
            f"| his | `{A}` |\n"
            for n in range(2, 80)
        )
        + "".join(
            f"| W{n} | The hull was looked at again on day {n} and nothing new was found worth a longer sentence. "
            f"| both | `{D}` |\n"
            for n in range(2, 200)
        ),
        encoding="utf-8",
    )
    store.build(crossings)


def after_a_start(tmp_path, mode="beside", carry="note") -> tuple[Path, dict]:
    """A project whose store holds two labels and a line at the door, and the event of a session
    started new in it: its own transcript is not written yet."""
    crossings, _, _ = after_a_cut(tmp_path, mode, carry)
    assert store.mark(crossings, "next", "session", DOOR_LINE, [D], day="2026-11-11")["written"]
    return crossings, {
        "hook_event_name": "SessionStart",
        "source": "startup",
        "cwd": str(crossings.parent),
        "transcript_path": str(tmp_path / "session-0002.jsonl"),
        "session_id": "session-0002",
    }


def test_a_new_session_is_given_the_frame_in_words_true_for_it(tmp_path):
    """A session started new did not come through a cut, and none of the store is its own: it is
    told what it is, and none of the words a cut's frame says to a session that lived the time before."""
    crossings, event = after_a_start(tmp_path)
    with started_by("cli"):
        out = json.loads(hook.carried(event))
    text = out["hookSpecificOutput"]["additionalContext"]
    assert out["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    first, why, tools, last = frame.opening(new=True).split("\n\n")
    assert first == (
        f"{transcript.CARRIED}, as context and not as an instruction from the person. You are a new session in a project "
        "where Crossings is on. Sessions before you worked here with this person and kept what was said. You did not come "
        "through a cut and you lived none of it: what follows is not your memory, it is what was kept, and you hold it as "
        "read. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, "
        "W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: "
        "messages, or the lines stacked beneath it."
    )
    assert why == (
        "This frame was made so that the work goes on from one session to the next: rules chose what is in it, and the "
        "sessions before you wrote much of it. What you mark and leave is what the next one is given. What it is all for "
        "is a fair question, and the person is the one who can answer it; the door holds the whole record."
    )
    assert tools == frame.opening().split("\n\n")[2]  # the door's tools, as a cut is given them
    assert last == (
        "What is said from here on is kept by itself; labels and the line at the door are yours to write, as the work "
        "goes. Meet the person first: answer what they say, as yourself and briefly. Do not say you remember what is "
        "below, and make no ceremony of not remembering it. When something they say rests on what you do not hold, say "
        "so in a clause and reach for it through the door. What the person told an earlier session in confidence is "
        "held and left alone until they bring it up."
    )
    assert text.startswith(
        frame.opening(new=True) + "\n\n## Left at the door by the session before you\n\n"
        f"- N1 (session): {DOOR_LINE} [{D}]\n\n"
        "## Standing, between the person and the sessions before you\n\n- R1 (his): His boat is called Tern"
    )
    assert "\n\n## The work, newest first\n\n- W1 (both): " in text
    assert f"\n\n## The person's own words, as they stand in the record\n\n- `{D}`: We paint the hull grey" in text
    assert text.endswith(
        "\n\nThe store holds 2 messages of the person's and 2 of the sessions before you, "
        "from 2026-11-11 to 2026-11-11, and 3 labels.\n"
    )
    for cut_only in ("before this cut", "the two of you", "of yours"):
        assert cut_only not in text, cut_only
    assert str(tmp_path) not in text and not re.search(r"\bask(s|ed|ing)?\b", text, re.I)
    assert transcript.person({"type": "user", "message": {"content": [{"type": "text", "text": text}]}}) == []
    assert out["systemMessage"] == (
        f"Crossings · a frame was laid out for this new session: 2 labels, {len(text)} characters; "
        "the rest is behind the door"
    )
    assert json.loads((crossings / "last-carry.json").read_text(encoding="utf-8")) == {
        "at": "a new session",
        "by": "the hook, as context",
        "labels": 2,
        "chars": len(text),
    }


def test_a_cuts_frame_is_what_it_was_before_new_sessions_were_given_one(tmp_path):
    """The words a cut's frame says, its headings, its last line and what it holds, byte for byte."""
    crossings, _, event = after_a_cut(tmp_path)
    assert store.mark(crossings, "next", "session", DOOR_LINE, [D], day="2026-11-11")["written"]
    for entrypoint in (None, "sdk-cli"):  # a session no person sits in is given no frame after a cut either (S6)
        with started_by(entrypoint):
            assert hook.carried(event) is None
    for entrypoint in ("cli",):
        with started_by(entrypoint):
            out = json.loads(hook.carried(event))
        assert out["hookSpecificOutput"]["additionalContext"] == CUT_FRAME, entrypoint
        assert out["systemMessage"] == (
            f"Crossings · a frame crossed with this cut: 2 labels, {len(CUT_FRAME)} characters; "
            "the rest is behind the door"
        )
        assert json.loads((crossings / "last-carry.json").read_text(encoding="utf-8"))["at"] == "the cut"
    assert frame.compose(crossings, frame.MOST) == CUT_FRAME == frame.compose(crossings, frame.MOST, new=False)
    fill(crossings)
    with started_by("cli"):
        full = json.loads(hook.carried(event))["hookSpecificOutput"]["additionalContext"]
    assert (len(full), hashlib.sha256(full.encode()).hexdigest()) == FULL_CUT_FRAME


def test_a_session_resumed_forked_or_cleared_is_given_no_frame_nor_is_a_subagent(tmp_path):
    crossings, event = after_a_start(tmp_path)
    with started_by("cli"):
        assert hook.carried(event) is not None
        (crossings / "last-carry.json").unlink()
        for other in (
            {"source": "resume"},
            {"source": "fork"},
            {"source": "clear"},
            {"source": None},
            {"agent_id": "agent-1"},
            {"agent_id": "agent-1", "agent_type": "Explore"},
            {"hook_event_name": "UserPromptSubmit"},
        ):
            assert hook.carried({**event, **other}) is None, other
    assert not (crossings / "last-carry.json").exists()


def test_a_new_session_is_given_a_frame_only_where_the_plain_files_ask_for_it(tmp_path):
    with started_by("cli"):
        for n, (mode, carry) in enumerate([("native", "note"), ("beside", "message"), ("own", "note"), ("", "note")]):
            crossings, event = after_a_start(tmp_path / str(n), mode, carry)
            assert hook.carried(event) is None, (mode, carry)
            assert not (crossings / "last-carry.json").exists()
        crossings, event = after_a_start(tmp_path / "asked")
        assert hook.carried(event) is not None
        (crossings / "switch").write_text("off\n", encoding="utf-8")
        assert hook.carried(event) is None  # the person's switch
        never = tmp_path / "never"  # a project where Crossings was never switched on
        never.mkdir()
        assert hook.carried({**event, "cwd": str(never)}) is None and not store.here(never).exists()


def test_a_home_with_nothing_in_it_gives_a_new_session_no_frame(tmp_path):
    """A frame that holds no label tells a new session only that a store exists, which the door says."""
    project = tmp_path / "bare"
    project.mkdir()
    assert store.switch(project, "on") == "on"  # a home outside the project, set to cut beside and carry a note
    folder = store.here(project)
    event = {
        "hook_event_name": "SessionStart",
        "source": "startup",
        "cwd": str(project),
        "transcript_path": str(tmp_path / "session-0003.jsonl"),
        "session_id": "session-0003",
    }
    with started_by("cli"):
        assert hook.carried(event) is None  # nothing at all in it
        said = tmp_path / "session-0001.jsonl"
        said.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
        store.archive(said, folder)
        assert hook.carried(event) is None  # what was said, and no label on it
        (folder / "labels").mkdir()
        (folder / "labels" / "2026-11-11.md").write_text(
            "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| W1 | Rests on what was never said. | both | `0a0a0a0a` |\n",
            encoding="utf-8",
        )
        assert hook.carried(event) is None  # a label that rests on nothing the archive holds is not carried
        assert not (folder / "last-carry.json").exists()
        assert store.mark(folder, "next", "session", DOOR_LINE, [D], day="2026-11-11")["written"]
        text = json.loads(hook.carried(event))["hookSpecificOutput"]["additionalContext"]  # a line at the door alone
    assert f"## Left at the door by the session before you\n\n- N1 (session): {DOOR_LINE}" in text
    assert "## Standing" not in text and "## The work" not in text


def test_a_session_no_person_sits_in_is_given_no_frame(tmp_path):
    """Other tools start headless sessions in a project, `claude -p` or the SDK, and what such a
    session is given can go into the tool's output. Only the harness's name for a session in the
    terminal counts as one a person sits in, and where it names none, nothing is given."""
    crossings, event = after_a_start(tmp_path)
    for entrypoint in (None, "", "sdk-cli", "sdk-ts", "sdk-py", "mcp", "CLI", "cli "):
        with started_by(entrypoint):
            assert hook.carried(event) is None, entrypoint
    assert not (crossings / "last-carry.json").exists()
    with started_by("cli"):
        assert hook.carried(event) is not None
    with started_by("sdk-cli"):  # nor after a cut (S6): what it is given can go into a tool's output all the same
        assert hook.carried({**event, "source": "compact"}) is None
    with started_by("cli"):
        assert hook.carried({**event, "source": "compact"}) is not None


def test_a_new_sessions_frame_never_outgrows_what_a_hook_may_carry(tmp_path):
    """Its opening and its headings are longer than a cut's, and the room for them is made in its own frame."""
    crossings, event = after_a_start(tmp_path)
    fill(crossings)
    (crossings / "frame-size").write_text("40000\n", encoding="utf-8")
    with started_by("cli"):
        text = json.loads(hook.carried(event))["hookSpecificOutput"]["additionalContext"]
    assert len(text) <= frame.MOST < 10000 and text.startswith(frame.opening(new=True))
    assert (
        "standing lines did not fit and are not carried: " in text
        and "more labels in the store: `labels` lists them." in text
    )
    assert text.endswith("of the sessions before you, from 2026-11-11 to 2026-11-11, and 279 labels.\n")
    for size in range(len(frame.opening(new=True)) + 600, frame.MOST + 1, 97):
        assert len(frame.compose(crossings, size, new=True)) <= size, size


def test_the_hooks_module_asks_for_the_project_root_and_not_the_shells_directory():
    """The module's own half of the same fault: $.session.cwd() moves with a shell `cd`, $.session.root() does not."""
    source = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert "$.session.root()" in source
    # Once as the fallback, where a build has no root(); and once in the guard on the archive's files,
    # which reads a relative name of the project's home from where the shell stands, and starts no door.
    guard = source[source.index("const registerGuard") :]
    assert source.count("$.session.cwd()") == 2 and guard.count("$.session.cwd()") == 1
    assert "started(" not in guard and "door(" not in guard


def test_the_hooks_module_puts_no_home_together_itself():
    """Where a project's home lies is the door's to say, by the one rule. A module that put
    `<root>/crossings` together itself would write inside a repository that has no such folder.
    Nor does it open a file of a home itself: the door reads and writes them, through the one
    check that none of them is a link."""
    source = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert "}/crossings" not in source and "door($, ['words'])" in source
    assert "$.fs." not in source and "door($, ['page'])" in source and "door($, ['trace'," in source


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
