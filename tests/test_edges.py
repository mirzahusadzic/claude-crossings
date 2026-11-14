"""The small paths: the command lines, the refusals and the failures that the other two files
do not walk. No model, no network, and nothing of the person's: the Keychain is a stand-in.

Run with pytest, or without it:  python3 tests/test_edges.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_count import BEFORE, CUT, SUMMARY, set_to, written  # noqa: E402
from test_store import ROWS, A, B, E, after_a_cut, at_terminal, home, in_person, own_folder, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import count, door, frame, handover, hook, record, second, show, store, transcript  # noqa: E402

BOUNDARY = {"type": "system", "subtype": "compact_boundary"}
THE_SUMMARY = {"type": "user", "isCompactSummary": True, "message": {"content": [{"type": "text", "text": SUMMARY}]}}


def ran(script: str, *argv: str, stdin: str = "", cwd: Path | None = None, **env: str) -> subprocess.CompletedProcess:
    """One of the plugin's scripts as a process of its own, the way a session or a hook starts it."""
    return subprocess.run(
        [sys.executable, "-I", str(ROOT / "crossing" / script), *argv],
        input=stdin,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=60,
        env={**os.environ, **env},
    )


def as_the_module(*argv: str, **env: str) -> subprocess.CompletedProcess:
    """The door as a process of its own, as the hooks module starts it: with its flag, and the
    plugin's folder in CLAUDE_PLUGIN_ROOT (see door.personal)."""
    return ran("door.py", *argv, "--by-module", CLAUDE_PLUGIN_ROOT=str(ROOT), **env)


def words_script(*argv: str) -> subprocess.CompletedProcess:
    """The hand-over's words script as a process of its own, as the plugin's own module would start
    it: with its flag, and the plugin's folder in CLAUDE_PLUGIN_ROOT (see handover.main)."""
    return ran("handover.py", "--by-module", *argv, CLAUDE_PLUGIN_ROOT=str(ROOT))


def through(*argv: str) -> tuple[int, str]:
    """The door, in this process."""
    out = io.StringIO()
    with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
        code = door.main(list(argv))
    return code, out.getvalue()


# --- the reader ------------------------------------------------------------------------------


def test_a_message_is_read_back_from_the_command_line_and_nothing_else_is(tmp_path):
    _, path = home(tmp_path)
    assert ran("read.py").returncode == 2 and "Usage:" in ran("read.py").stderr
    assert ran("read.py", str(path)).returncode == 2  # nothing named
    assert ran("read.py", str(path), "not-an-id!").returncode == 2
    many = ran("read.py", str(path), *["1"] * 21)
    assert many.returncode == 2 and "at most 20 messages a call" in many.stderr
    by_id = ran("read.py", str(path), A, B)
    assert by_id.returncode == 0
    assert f"{A} (line 1), the person: My boat is called Tern. Its mooring is number 41, by the café." in by_id.stdout
    assert f"{B} (line 2), the session: Noted: Tern, at mooring 41." in by_id.stdout
    assert "private reasoning" not in by_id.stdout and "ls -la" not in by_id.stdout
    by_line = ran("read.py", str(path), "1", "3").stdout
    assert "the person: My boat is called Tern." in by_line and "(line 3): nothing was said here" in by_line
    assert ran("read.py", str(path), "0a0a0a0a").stdout.strip() == "no such message in this transcript"


# --- the hand-over's words -------------------------------------------------------------------


def test_the_anchored_words_are_written_from_the_command_line(tmp_path):
    crossings, path = home(tmp_path)
    wrong = words_script(str(path))
    assert wrong.returncode == 2 and "Usage:" in wrong.stderr
    made = words_script(str(path), str(crossings / "hand-over.md"))
    out = crossings / "hand-over.words.md"
    assert made.returncode == 0 and made.stdout.strip() == str(out)
    words = out.read_text(encoding="utf-8")
    assert f"- `{A}`, the person: My boat is called Tern." in words and f"- `{E}`, the session: Grey it is." in words
    assert "not in this transcript" not in words  # every id the page names was found


def test_an_id_that_names_no_words_is_said_to_be_missing(tmp_path):
    _, path = home(tmp_path)
    kept, missing = handover.words(path, [A, "ffffffff", "0a0a0a0a"])  # a tool's result, and an id nobody has
    assert [k[0] for k in kept] == [A] and missing == ["ffffffff", "0a0a0a0a"]
    (cut_short,), _ = handover.words(path, [A], most=10)
    assert cut_short[2] == "My boat is […]"


# --- the record, shown -----------------------------------------------------------------------


def test_the_cuts_on_record_are_shown_from_the_command_line(tmp_path):
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    store.consent(project)  # as the person's switching on keeps it
    whole = written(tmp_path, BEFORE + CUT)  # the harness gave sizes and how long the cut took
    record.write(count.count(whole), project / "crossings", "abcdef01-1111", whole, on="2026-11-11")
    sized = {**BOUNDARY, "compactMetadata": {"trigger": "auto", "preTokens": 5000, "postTokens": 400}}
    (tmp_path / "other").mkdir()
    bare = written(tmp_path / "other", BEFORE + [sized, THE_SUMMARY])  # sizes, and no time
    page = record.write(count.count(bare), project / "crossings", "fedcba98-2222", bare, on="2026-11-11")
    assert "5,000 tokens before, 400 after" in page.read_text(encoding="utf-8")
    assert "the cut took" not in page.read_text(encoding="utf-8")

    shown = ran("show.py", str(project)).stdout
    assert "2 cuts on record in this project" in shown
    assert "1,000 → 100 tokens · the cut took 2 s" in shown and "5,000 → 400 tokens\n" in shown
    assert "crossings/abcdef01-cut-1.md" in shown and str(project) not in shown  # beside the work, by a short path
    one = ran("show.py", "--session", "fedcba98", cwd=project).stdout  # no folder named: the one it stands in
    assert "1 cut on record in this project" in one and "abcdef01" not in one
    assert "no cut on record in this project" in ran("show.py", str(project), "--session", "00000000").stdout
    (tmp_path / "link").symlink_to(project, target_is_directory=True)  # by whichever path the project was named
    linked = show.block(tmp_path / "link")
    assert "    crossings/abcdef01-cut-1.md\n" in linked and str(tmp_path) not in linked
    with set_to(CROSSING_HOME=str(project / "crossings")):  # and from a home named outright, like every other piece,
        assert "no cut on record" in show.block(tmp_path / "other")  # once the person switched it on there (S3)
        store.consent(tmp_path / "other")
        assert "2 cuts on record in this project" in show.block(tmp_path / "other")


def test_a_project_without_the_folder_has_its_record_in_its_home_outside_it(tmp_path):
    plain = tmp_path / "plain"
    plain.mkdir()
    whole = written(tmp_path, BEFORE + CUT[:2])  # the cut written, and nothing said since: the hook is about it
    event = {
        "hook_event_name": "PostCompact",
        "transcript_path": str(whole),
        "cwd": str(plain),
        "session_id": "abcdef01-1111",
        "trigger": "manual",
        "compact_summary": SUMMARY,
    }
    hook.run(event)  # never switched on: no cut is counted, and looking for one makes no home
    assert "no cut on record in this project" in show.block(plain) and not record.home(plain).exists()
    assert through("switch", "on", "--cwd", str(plain))[0] == 0
    hook.run(event)
    page = record.home(plain) / "abcdef01-cut-1.md"
    assert page.exists() and page.parent.parent == record.homes() and list(plain.iterdir()) == []
    assert f"    {page}\n" in show.block(plain)  # by its whole path, since it is not beside the work


def test_a_record_makes_no_home(tmp_path):
    """A cut is counted into a home that is there. Were the record to make the folder it was
    handed, a project where Crossing was never switched on would get a home by being counted."""
    whole = written(tmp_path, BEFORE + CUT)
    try:
        record.write(count.count(whole), tmp_path / "no-home", "abcdef01-1111", whole)
    except FileNotFoundError:
        pass
    else:
        raise AssertionError("a record made a home")
    assert not (tmp_path / "no-home").exists() and record.read(tmp_path / "no-home", "abcdef01-1111", 1) is None


def test_looking_for_a_project_never_goes_above_the_persons_home(tmp_path):
    house = tmp_path / "house"
    inside = house / "a" / "b"
    inside.mkdir(parents=True)
    (tmp_path / "crossings").mkdir()  # a folder of that name above the home is nobody's project
    with own_folder(house):
        found = record.home(inside)
    assert found == record.outside(inside.resolve()) and found.parent == record.homes()


# --- the count -------------------------------------------------------------------------------


def test_a_count_that_runs_out_of_time_says_it_is_unfinished_and_guesses_nothing(tmp_path):
    c = count.count(written(tmp_path, BEFORE + CUT), seconds=-1.0)
    assert c["person"]["finished"] is False and c["person"]["pointers"] == [] and c["person"]["covered"] == 0
    assert c["person"]["messages"] == 3  # what stood is still known


# --- the hook --------------------------------------------------------------------------------


@in_person
def test_the_waking_note_is_about_this_cut_whichever_hook_the_harness_called_first(tmp_path):
    """The harness asks for the note first as a rule. Where it hands the summary over first, the
    record is already there, and the note is still about that cut and names no file."""
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    store.consent(project)  # as the person's switching on keeps it
    path = written(tmp_path, BEFORE)  # the boundary is not in the file yet at either call
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "abcdef01-1111"}
    hook.run({**event, "hook_event_name": "PostCompact", "trigger": "manual", "compact_summary": SUMMARY})
    said = json.loads(hook.run({**event, "hook_event_name": "SessionStart", "source": "compact"}))
    note = said["hookSpecificOutput"]["additionalContext"]
    assert "cut 1 of this session" in note and str(tmp_path) not in note


@in_person
def test_the_frame_still_crosses_where_its_small_conveniences_fail(tmp_path):
    crossings, _, event = after_a_cut(tmp_path / "a")
    (crossings / "last-carry.json").mkdir()  # the trace cannot be written
    gone = {**event, "transcript_path": str(tmp_path / "no-such-file.jsonl")}  # nor the archive brought up to date
    text = json.loads(hook.carried(gone))["hookSpecificOutput"]["additionalContext"]
    assert text.startswith(transcript.CARRIED) and "- R1 (his): His boat is called Tern" in text
    crossings, _, event = after_a_cut(tmp_path / "b")
    (crossings / "mode").unlink()  # a project that never said how it cuts
    assert hook.carried(event) is None


def test_a_cut_renews_the_second_copy_where_the_home_names_a_folder(tmp_path):
    if shutil.which("hdiutil") is None:  # the image is macOS's own: elsewhere there is no copy to renew
        return
    crossings, path = home(tmp_path)
    (crossings / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    event = {"transcript_path": str(path), "cwd": str(crossings.parent), "session_id": "session-0001"}
    keychain = tmp_path / "bin" / "security"  # a hook stands at no terminal: the Keychain is asked, here a stand-in
    keychain.parent.mkdir()
    keychain.write_text(KEYCHAIN, encoding="utf-8")
    keychain.chmod(0o755)
    path_was = os.environ["PATH"]
    with (
        set_to(
            CROSSING_COPY_KEY="a passphrase for this test only",
            PATH=f"{keychain.parent}{os.pathsep}{path_was}",
            CROSSING_TEST_KEYCHAIN=str(tmp_path / "keychain"),
        ),
        started_by("cli"),
    ):  # a person sits in it
        hook.run({**event, "hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": "A summary."})
    # named by the project's folder and eight characters of its whole path's digest (second.named)
    image = (tmp_path / "cloud" / f"{second.named(crossings.parent.resolve())}.dmg").read_bytes()
    assert len(image) > 1000 and b"Tern" not in image
    assert (tmp_path / "keychain").read_text(encoding="utf-8").strip() != "a passphrase for this test only"


def test_a_hook_with_nothing_to_say_says_nothing_and_a_failure_never_reaches_the_session(tmp_path):
    quiet = ran(
        "hook.py",
        stdin=json.dumps(
            {"hook_event_name": "SessionStart", "source": "startup", "session_id": "", "cwd": str(tmp_path)}
        ),
    )
    assert quiet.returncode == 0 and quiet.stdout == ""
    data = tmp_path / "data"
    (data / "errors.log").mkdir(parents=True)  # even the plugin's own log cannot be written
    failed = ran("hook.py", stdin='"not an event"', CLAUDE_PLUGIN_DATA=str(data))
    assert failed.returncode == 0 and failed.stdout == "" and failed.stderr == ""


def test_no_test_marks_a_session_in_the_real_home(tmp_path):
    """A session Crossing is on in is marked by an empty file in the person's home. A test's
    made-up session must never be marked there, whether the hook runs here or as its own process."""
    event = {
        "hook_event_name": "SessionStart",
        "source": "startup",
        "session_id": "made-up-for-a-test",
        "cwd": str(tmp_path),
    }
    assert ran("hook.py", stdin=json.dumps(event)).returncode == 0
    hook.run({**event, "session_id": "made-up-here-too"})
    real = Path.home() / ".claude" / "crossing"
    assert not (real / "live" / "made-up-for-a-test").exists() and not (real / "live" / "made-up-here-too").exists()
    assert (Path(os.environ["CROSSING_LIVE"]) / "made-up-for-a-test").exists() and (
        hook.LIVE / "made-up-here-too"
    ).exists()
    assert (
        real not in hook.LIVE.parents and real not in record.homes().parents
    )  # nor is a made-up project's home kept there


# --- the door --------------------------------------------------------------------------------


def test_the_door_finds_a_sessions_transcript_by_its_id(tmp_path):
    crossings, path = home(tmp_path)
    house = tmp_path / "house"
    kept = house / ".claude" / "projects" / "some-project"
    kept.mkdir(parents=True)
    later = row("user", "99999999", 30, "Said after the store was last built.")
    (kept / "session-0001.jsonl").write_text(
        path.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8"
    )
    project = str(crossings.parent)
    with own_folder(house), started_by("cli"):  # by its id, the transcript of a session a person sits in
        assert "Newly archived: 1." in through("status", "--cwd", project, "--session", "session-0001")[1]
        unknown = through("status", "--cwd", project, "--session", "no-such-session")[1]
    assert "3 messages of the person's" in unknown and "Newly archived" not in unknown


def test_the_door_says_plainly_what_it_did_not_find(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    label_only = through("find", "lies", "--cwd", project)[1]  # a word of the label's, in no message
    assert "- R1 (relation, his)" in label_only and "Said:" not in label_only
    assert "That is a miss, not a no" in through("find", "?!", "--cwd", project)[1]  # no word at all
    assert store.find(crossings, "?!") == {
        "asked": "?!",
        "all_words": True,
        "labels_all": True,
        "labels": [],
        "said": [],
        "nearest": [],
    }
    later = row("user", "99999999", 30, "Nothing rests on this one.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8")
    alone = through("thread", "99999999", "--around", "0", "--cwd", project, "--transcript", str(path))[1]
    assert "the one you named" in alone and "Labels resting here" not in alone


def test_a_label_that_holds_the_words_does_not_hide_the_messages_that_hold_some(tmp_path):
    """Labels and messages are each looked for on their own: where labels hold every word, a
    message that holds only some of them, in other forms, is still shown."""
    crossings, _ = home(tmp_path)
    out = store.find(crossings, "lies mooring")  # the label says where the boat lies; no message has that word
    assert [label["id"] for label in out["labels"]] == ["R1"] and out["labels_all"] is True
    assert sorted(s["id"] for s in out["said"]) == sorted([A, B]) and out["all_words"] is False
    code, said = through("find", "lies mooring", "--cwd", str(crossings.parent))
    assert "(no message holds all of these words; any of them)" in said and f"- `{A}` the person" in said
    assert "\nLabels:\n- R1 " in said
    some = through("find", "Tern zeppelin", "--cwd", str(crossings.parent))[1]  # no label holds both either
    assert "Labels (holding any of these words):\n- R1 " in some and f"- `{A}` the person" in some
    only = store.find(crossings, "lies")  # a word of a label's alone: nothing to qualify
    assert only["all_words"] is True and only["said"] == [] and [label["id"] for label in only["labels"]] == ["R1"]


def test_a_thread_cuts_a_long_neighbour_short_and_keeps_the_asked_one_whole(tmp_path):
    long = "A long message about the rigging. " * 40
    rows = ROWS + [row("user", "77777777", 20, long), row("assistant", "88888888", 21, long)]
    crossings, _ = home(tmp_path, rows)
    out = store.thread(crossings, "77777777", 1)
    asked, after = [s for s in out["said"] if s["is_asked"]][0], out["said"][-1]
    assert asked["text"] == long.strip() and after["id"] == "88888888"
    assert after["text"].endswith(" […]") and len(after["text"]) <= store.NEAR + 4


def test_striking_and_copying_through_the_door(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert "not struck: nothing named" in through("strike", "--cwd", project)[1]
    struck = through("strike", A, "--why", "asked to", "--cwd", project)[1]
    assert struck.startswith(f"struck {A}: ") and "will not come back at a build" in struck
    assert store.status(crossings)["his"] == 1
    code, said = through("copy", "--cwd", project)
    assert code == 1 and "No second copy is set for this home" in said
    if shutil.which("hdiutil") is None:  # the image is macOS's own: elsewhere no copy is made
        return
    (crossings / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    ours = tmp_path / "ours"
    ours.mkdir()
    (ours / "copy").write_text(str(tmp_path / "cloud") + "\n", encoding="utf-8")
    with set_to(
        CROSSING_COPY_KEY="a passphrase for this test only", CROSSING_OURS=str(ours)
    ):  # at the person's terminal
        code, said = through("copy", "--cwd", project)
        assert code == 0 and "plain files, encrypted, to " in said and "read back the same" in said
        code, said = through("copy", "--cwd", project, "--home", "ours")  # a home with nothing in it yet
        assert code == 1 and said.strip() == "not copied: nothing to copy yet"


def test_a_label_without_a_sentence_or_without_an_anchor_is_refused(tmp_path):
    crossings, _ = home(tmp_path)
    for text, anchors in (("", [A]), ("   ", [A]), ("A sentence with nothing under it.", []), ("A sentence.", [" "])):
        out = store.mark(crossings, "work", "both", text, anchors)
        assert out == {"written": False, "why": "a label needs a sentence and at least one anchor"}
    assert not (crossings / "labels").exists()


# --- the store -------------------------------------------------------------------------------


def test_a_damaged_line_or_a_build_that_was_cut_off_does_not_stop_the_next_build(tmp_path):
    crossings, _ = home(tmp_path)
    page = crossings / "said" / "session-.jsonl"
    page.write_text(page.read_text(encoding="utf-8") + "half a line that is not js\n", encoding="utf-8")
    (crossings / "store.db.new").write_text("left by a build that never finished", encoding="utf-8")
    held = store.build(crossings)
    assert (held["his"], held["session"], held["labels"]) == (2, 2, 2)
    assert not (crossings / "store.db.new").exists()


def test_a_damaged_line_in_the_archive_does_not_stop_a_strike(tmp_path):
    """A build passes over a line that is no message. A strike that stopped at one had already
    noted the id among the struck, and left the words themselves in the archive."""
    crossings, _ = home(tmp_path)
    page = crossings / "said" / "session-.jsonl"
    page.write_text(page.read_text(encoding="utf-8") + "half a line that is not js\n", encoding="utf-8")
    out = store.strike(crossings, A)
    assert out["struck"] and out["removed"] == 1
    kept = page.read_text(encoding="utf-8")
    assert "Tern.\\nIts" not in kept and kept.endswith("half a line that is not js\n")  # which is left as it is
    assert store.status(crossings)["his"] == 1 and store.find(crossings, "mooring", voice="his")["said"] == []


# --- the frame -------------------------------------------------------------------------------


def test_a_frame_is_made_where_no_store_was_built_yet(tmp_path):
    crossings, _ = home(tmp_path)
    (crossings / "store.db").unlink()
    assert "- R1 (his): His boat is called Tern" in frame.compose(crossings)
    assert not (crossings / "store.db").exists()  # made in memory: a read makes no database


def test_a_frame_too_small_for_anything_else_still_names_the_door(tmp_path):
    crossings, _ = home(tmp_path)
    text = frame.compose(crossings, frame.LEAST)  # the least a frame may be: room for the opening and little more
    assert "1 standing line did not fit and is not carried: R1; `labels` gives them." in text
    assert frame.TOOL in text and "- W1 (both): The hull is to be painted grey in spring." in text
    assert "## Standing" not in text and "## The person's own words" not in text
    # A size asked below the least, or above the most, is held between them (S9): a home's file can set it.
    assert frame.compose(crossings, len(frame.opening()) + 460) == text == frame.compose(crossings, 10)
    (crossings / "frame-size").write_text("100000\n", encoding="utf-8")
    assert frame.size_of(crossings) == frame.MOST
    (crossings / "frame-size").write_text("-5\n", encoding="utf-8")
    assert frame.size_of(crossings) == frame.LEAST and frame.bounded(10**9) == frame.MOST
    assert through("frame", "--size", "5", "--cwd", str(crossings.parent)) == (0, text)


# --- the second copy -------------------------------------------------------------------------

KEYCHAIN = """#!/bin/sh
# A stand-in for macOS's `security`, for a test: one item, kept in a file.
case "$1" in
  find-generic-password) [ -s "$CROSSING_TEST_KEYCHAIN" ] && cat "$CROSSING_TEST_KEYCHAIN" || exit 44 ;;
  add-generic-password)
    while [ $# -gt 1 ]; do
      [ "$1" = "-w" ] && printf '%s\\n' "$2" > "$CROSSING_TEST_KEYCHAIN"
      shift
    done ;;
esac
"""


def test_the_passphrase_is_made_once_and_kept_in_the_keychain(tmp_path):
    """Against a stand-in: no test reads or writes the person's Keychain."""
    stand_in = tmp_path / "bin" / "security"
    stand_in.parent.mkdir()
    stand_in.write_text(KEYCHAIN, encoding="utf-8")
    stand_in.chmod(0o755)
    kept = tmp_path / "keychain"
    with set_to(PATH=f"{stand_in.parent}{os.pathsep}{os.environ['PATH']}", CROSSING_TEST_KEYCHAIN=str(kept)):
        os.environ.pop("CROSSING_COPY_KEY", None)
        first = second.passphrase()
        assert len(first) >= 40 and kept.read_text(encoding="utf-8").strip() == first  # made, and put away
        assert second.passphrase() == first  # found there the next time, not made again
        log = Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "errors.log"

        def lines():
            return log.read_text(encoding="utf-8").count("ignored: CROSSING_COPY_KEY is set") if log.exists() else 0

        before, _ = lines(), second._ignored.clear()
        with set_to(CROSSING_COPY_KEY="given for a test"):
            with at_terminal():  # the person's own terminal: taken from there
                assert second.passphrase() == "given for a test"
            assert second.passphrase() == first  # anywhere else it is passed over, for the Keychain's (S9)
            assert second.passphrase() == first
        assert lines() == before + 1  # with one line in the log, once a process


def test_an_image_that_does_not_read_back_the_same_replaces_nothing(tmp_path):
    if shutil.which("hdiutil") is None:  # the image is macOS's own
        return
    crossings, _ = home(tmp_path)
    cloud = tmp_path / "cloud"
    stray = crossings / ".copy-stage" / "not-this-copy" / "kept.txt"
    stray.parent.mkdir(parents=True)
    stray.write_text("someone else's file", encoding="utf-8")
    with set_to(CROSSING_COPY_KEY="a passphrase for this test only"), at_terminal():
        assert second.make(crossings, cloud, "project")["copied"] is True
        before = (cloud / "project.dmg").read_bytes()
        checks, second.verify = second.verify, lambda *_: False
        try:
            out = second.make(crossings, cloud, "project")
        finally:
            second.verify = checks
    assert out == {"copied": False, "why": "the image did not read back the same"}
    assert (cloud / "project.dmg").read_bytes() == before  # the earlier good copy stands
    assert sorted(p.name for p in cloud.iterdir()) == ["project.dmg"]
    assert stray.read_text(encoding="utf-8") == "someone else's file"  # only its own staged files are removed
    assert not (crossings / ".copy-stage" / "project").exists()
    assert second.verify(stray, {}, b"any key\0") is False  # a file that is no image does not pass for one


# --- the transcript's reader -----------------------------------------------------------------


def test_the_reader_takes_only_what_a_voice_said(tmp_path):
    path = tmp_path / "odd.jsonl"
    path.write_text(
        '[1, 2]\n"a string"\n' + json.dumps(row("user", A, 1, "The one row here.")) + "\n", encoding="utf-8"
    )
    assert [line for line, _ in transcript.rows(path)] == [3]  # a line that is no row is passed over
    queued = {"type": "attachment", "attachment": {"type": "queued_command", "prompt": "sent by a hook, not by him"}}
    assert transcript.person(queued) == []
    mixed = row(
        "user", B, 2, [{"type": "image", "source": {}}, {"type": "text", "text": "A picture, and these words."}]
    )
    assert transcript.person(mixed) == ["A picture, and these words."]
    result = {
        "type": "user",
        "message": {
            "content": [
                {"type": "tool_result", "content": [{"type": "text", "text": "abc"}, {"n": 12, "none": None}, "de"]}
            ]
        },
    }
    assert transcript.tool_traffic(result) == (0, len("abc text 12  de"))
    try:
        transcript.last_written(path)
    except LookupError as err:
        assert "holds no cut" in str(err)
    else:
        raise AssertionError("a transcript without a cut was given one")


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
