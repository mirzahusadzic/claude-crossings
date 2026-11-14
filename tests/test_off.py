"""Off the record: what is said while the person's switch for a project is off is never kept,
however the transcript is read afterwards, and the store shows only that something may have been
said then, never what. On made-up projects and transcripts this file writes; no model, no network.

The spans are kept by the real clock, as the switch keeps them, and a message said meanwhile is
stamped by it too, as the harness stamps a transcript's rows: a few milliseconds apart, so that
the order of the moments is never in doubt.

Run with pytest, or without it:  python3 tests/test_off.py
"""

from __future__ import annotations

import datetime
import json
import re
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_guards import repository  # noqa: E402
from test_homes import public  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import ROWS, A, B, D, E, in_person, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import count, door, frame, hook, off, second, store  # noqa: E402

FIND = "mcp__plugin_crossing_door__find"


def stamp() -> str:
    """This moment, as the harness stamps a row of a transcript, a little after the last act."""
    time.sleep(0.005)
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def says(path: Path, uid: str, text: str, kind: str = "user", at: str | None = "now") -> dict:
    """One message at the end of a transcript, said at this moment; with `at` None, a row with no
    time at all, and with any other `at`, that time as it is written."""
    given = row(kind, uid, 0, text if kind == "user" else [{"type": "text", "text": text}])
    if at is None:
        del given["timestamp"]
    else:
        given["timestamp"] = stamp() if at == "now" else at
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(given) + "\n")
    return given


def switch(project: Path, word: str) -> str:
    """The person's switch, as their command turns it through the door; a moment after what was said."""
    time.sleep(0.005)
    code, out = through("switch", word, "--cwd", str(project))
    time.sleep(0.005)
    assert code == 0, out
    return out


def asked(project: Path, path: Path, name: str = "PreToolUse") -> None:
    """The hook a moment before a call of the door (or at a session's end), for this transcript."""
    event = {
        "hook_event_name": name,
        "tool_name": FIND,
        "transcript_path": str(path),
        "cwd": str(project),
        "session_id": path.stem,
    }
    with set_to(CROSSING_WAIT="1"):
        assert hook.run(event) is None


def on_with_a_transcript(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A project switched on, its home outside it, and a session's transcript holding one
    message, which is archived."""
    project, folder, path = public(tmp_path)
    path.write_text("", encoding="utf-8")
    switch(project, "on")
    says(path, "10000001", "The anchor chain was replaced last week.")
    asked(project, path)
    return project, folder, path


def kept_ids(folder: Path) -> list[str]:
    return [r["id"] for r in store._archived(folder)]


def finds(project: Path, words: str) -> str:
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        return said("find", words=words)[0]


def spans_file(folder: Path) -> list[str]:
    return [line for line in (folder / "off.txt").read_text(encoding="utf-8").splitlines() if not line.startswith("#")]


# --- the reported fault ------------------------------------------------------------------------


@in_person
def test_what_was_said_while_switched_off_is_not_kept_when_it_is_switched_on_again(tmp_path):
    """The fault as it was found: on, say something, archive; off, say two things; on, say one
    thing, archive. The two said while it was off came back through `find`."""
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "Between us: the harbour master is selling his boat.")
    says(path, "20000003", "I will say nothing of the harbour master's boat.", kind="assistant")
    answer = switch(project, "on")
    says(path, "30000004", "Back to the chain: it needs a swivel.")
    asked(project, path)
    for words in ("harbour", "master", "selling boat"):
        assert "Nothing in the store holds these words" in finds(project, words), words
    assert kept_ids(folder) == ["10000001", "30000004"]
    assert answer == door.SWITCHED["again"] + "\n"  # and the person's answer said it was on again
    assert "harbour" not in (folder / "said" / "abcdef01.jsonl").read_text(encoding="utf-8")
    # The thread shows the gap in its place, with its two moments, and nothing of what was said.
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        shown = said("thread", id="10000001")[0]
    start, end = spans_file(folder)[0].split()
    assert "`10000001`" in shown and "`30000004`" in shown and "20000002" not in shown and "20000003" not in shown
    first, last = (store.off.moment(t).strftime("%Y-%m-%d %H:%M:%S UTC") for t in (start, end))
    gap = f"(Crossings was off from {first} to {last}: nothing said then was kept.)"
    assert shown.index("`10000001`") < shown.index(gap) < shown.index("`30000004`")
    status = through("status", "--cwd", str(project))[1]
    assert "Crossings was off here 1 time: nothing said while it was off is kept." in status
    assert "holds 2 messages of the person's and 0 of the session's" in status  # and no count of what was said then


@in_person
def test_a_message_said_while_on_and_archived_only_after_an_off_span_is_kept(tmp_path):
    """Off the record by when it was said, not by when it was archived."""
    project, folder, path = on_with_a_transcript(tmp_path)
    says(path, "40000001", "Said while it was on, and not yet archived.")
    switch(project, "off")
    says(path, "40000002", "Said while it was off.")
    switch(project, "on")
    asked(project, path)
    assert kept_ids(folder) == ["10000001", "40000001"]


@in_person
def test_a_whole_pass_at_a_sessions_end_does_not_bring_the_words_back(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "The mooring fee is late this month.")
    switch(project, "on")
    asked(project, path, "SessionEnd")  # the whole transcript, read from its first line, in this process
    assert kept_ids(folder) == ["10000001"]
    started = hook.keep(path, project, wait=False)  # the session's end that is not held up: the door's build
    assert started.wait(timeout=60) == 0
    assert through("build", "--cwd", str(project), "--transcript", str(path))[0] == 0  # and the person's own build
    assert kept_ids(folder) == ["10000001"] and "Nothing in the store" in finds(project, "mooring fee")


@in_person
def test_a_fork_and_a_resume_that_repeat_the_messages_under_their_ids_do_not_bring_them_back(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "The insurance lapsed in the spring.")
    says(path, "20000003", "Then it lapsed in the spring.", kind="assistant")
    switch(project, "on")
    asked(project, path)
    for name in ("fedcba98-0001.jsonl", "13572468-0002.jsonl"):  # a fork, then a resume: new files, the same rows
        again = tmp_path / name
        again.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        says(again, f"5000000{name[-7]}", f"Said only in {name}.")
        asked(project, again)
        asked(project, again, "SessionEnd")
    assert sorted(kept_ids(folder)) == ["10000001", "50000001", "50000002"]
    assert "Nothing in the store" in finds(project, "insurance")


@in_person
def test_a_transcript_handed_over_by_its_path_from_a_shell_does_not_bring_them_back(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "The keel bolts are rusted through.")
    switch(project, "on")
    copy = tmp_path / "handed00-0009.jsonl"  # the person's own act, taken as it is
    copy.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    shown = through("status", "--cwd", str(project), "--transcript", str(copy))[1]
    assert "Newly archived" not in shown and kept_ids(folder) == ["10000001"]
    with started_by("sdk-cli"):  # and handed over from where no person sits, which is taken whole, too
        assert through("build", "--cwd", str(project), "--transcript", str(path))[0] == 0
    assert kept_ids(folder) == ["10000001"] and "Nothing in the store" in finds(project, "keel bolts")


@in_person
def test_two_sessions_in_one_project_and_one_talks_through_the_others_off_span(tmp_path):
    """The switch is the project's: what any session said inside a span is not kept."""
    project, folder, north = on_with_a_transcript(tmp_path)
    south = tmp_path / "fedcba98-5555.jsonl"
    says(south, "60000001", "South session, before.")
    asked(project, south)
    switch(project, "off")  # switched off from the north session
    says(south, "60000002", "South session, while the north switched it off.")
    says(north, "20000002", "North session, while off.")
    says(south, "60000003", "South session answers.", kind="assistant")
    asked(project, south)  # off: the hook adds nothing
    switch(project, "on")
    says(south, "60000004", "South session, after.")
    asked(project, south)
    asked(project, north)
    asked(project, south, "SessionEnd")
    assert sorted(kept_ids(folder)) == ["10000001", "60000001", "60000004"]


@in_person
def test_a_span_still_open_keeps_nothing_from_its_beginning_on(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    assert switch(project, "off").startswith("Crossings is off for this project")
    assert switch(project, "off").startswith("Crossings is off for this project")  # twice: the span is opened once
    assert len(spans_file(folder)) == 1 and len(spans_file(folder)[0].split()) == 1
    says(path, "20000002", "Said with the span open.")
    assert through("build", "--cwd", str(project), "--transcript", str(path))[0] == 0  # off: nothing is added
    status = through("status", "--cwd", str(project))[1]
    assert "Crossings was off here 1 time, the last still open: nothing said while it was off is kept." in status
    look = through("look", "--cwd", str(project))[1]
    assert re.search(
        r"- off the record from \d{4}-\d\d-\d\d \d\d:\d\d:\d\d UTC on, still off: nothing said then was kept", look
    )
    # Even with the switch file turned on by hand, the open span keeps everything after its beginning out.
    (folder / "switch").write_text("on\n", encoding="utf-8")
    says(path, "20000003", "Said after the switch was written by hand.")
    asked(project, path, "SessionEnd")
    assert kept_ids(folder) == ["10000001"]
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        shown = said("thread", id="10000001")[0]
    assert "on, and is still off: nothing said then was kept.)" in shown


@in_person
def test_several_spans_each_keep_out_what_was_said_inside_them(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    answers = []
    for n in range(1, 4):
        switch(project, "off")
        says(path, f"2000000{n}", f"Inside span {n}.")
        says(path, f"2100000{n}", f"Inside span {n}, the reply.", kind="assistant")
        answers.append(switch(project, "on"))
        says(path, f"3000000{n}", f"Between spans, after the {n}.")
    answers.append(switch(project, "on"))
    asked(project, path)
    asked(project, path, "SessionEnd")
    assert kept_ids(folder) == ["10000001", "30000001", "30000002", "30000003"]
    assert answers == [door.SWITCHED["again"] + "\n"] * 3 + [
        door.SWITCHED["on"] + "\n"
    ]  # the last: nothing open, on as it was
    assert len(spans_file(folder)) == 3 and all(len(line.split()) == 2 for line in spans_file(folder))
    assert (
        "Crossings was off here 3 times: nothing said while it was off is kept."
        in through("status", "--cwd", str(project))[1]
    )
    look = through("look", "--cwd", str(project))[1]
    assert len(re.findall(r"^- off the record from .+ UTC to .+ UTC: nothing said then was kept$", look, re.M)) == 3
    assert "Inside span" not in look and "Nothing in the store" in finds(project, "inside")
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        shown = said("thread", id="30000002", around=0)[0]
        wider = said("thread", id="30000002", around=1)[0]
    assert shown.count("(Crossings was off from") == 2  # the spans on either side of it, and not the one further off
    assert wider.count("(Crossings was off from") == 3


@in_person
def test_a_torn_or_nonsensical_spans_file_keeps_nothing_until_switched_on_again_and_nothing_it_covers(tmp_path):
    """A line of the record that is no span may have been a span, and what it held can no longer be
    told: nothing more is archived until the person switches on again, which keeps everything
    before that moment off. The lines stay as they were."""
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "Inside the span that can be read.")
    switch(project, "on")
    says(path, "30000003", "On the record, after it.")
    good = spans_file(folder)[0]
    with open(folder / "off.txt", "a", encoding="utf-8", errors="surrogateescape") as handle:
        handle.write(
            "yesterday afternoon\n2026-13-40T99:00:00Z\n2026-11-12T10:00:00Z 2026-11-12T09:00:00Z\n"
            "2026-11-12T10:00:00Z 2026-11-12T11:00:00Z extra\n2026-11-12T08:00:00 2026-11-12T09:00:00\n"
            "\udcff\udcfe\n2026-11-12T07:00:00Z\n2026-11-12T05:00:00Z 2026-11-12T05:30:00Z\n"  # open, and not the last
            "2026-11-12T08:00:0"
        )  # the last of them torn mid-line
    asked(project, path)
    assert kept_ids(folder) == ["10000001"] and store.lost(folder)
    status = through("status", "--cwd", str(project))[1]
    assert "Crossings was off here 2 times: nothing said while it was off is kept." in status
    assert (
        f"8 lines of the record of when Crossings was off ({folder / 'off.txt'}) could not be read and were passed over."
        in status
    )
    assert door.LOST in status
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        bare = said("status")[0]
    assert "8 lines of the record of when Crossings was off could not be read" in bare and "off.txt" not in bare
    # Switched off and on again, the lines that could not be read stay as they were, everything said
    # before that moment stays off, and what is said after it is kept.
    before = (folder / "off.txt").read_bytes()
    switch(project, "off")
    says(path, "20000004", "Inside a new span.")
    assert switch(project, "on") == door.SWITCHED["restored"] + "\n"
    asked(project, path, "SessionEnd")
    assert kept_ids(folder) == ["10000001"] and not store.lost(folder)
    says(path, "40000005", "On the record, after it was switched on again.")
    asked(project, path)
    assert kept_ids(folder) == ["10000001", "40000005"]
    after = (folder / "off.txt").read_bytes()
    assert after.startswith(before.rstrip(b"\n")) and good.encode() in after and b"\xff\xfe" in after


@in_person
def test_a_spans_file_that_cannot_be_read_at_all_keeps_nothing_and_moves_no_marker(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    marked = (folder / "markers.jsonl").read_text(encoding="utf-8")
    (folder / "off.txt").mkdir()  # there, and not a file
    says(path, "30000003", "Said while the record of the spans could not be read.")
    asked(project, path)
    assert kept_ids(folder) == ["10000001"] and (folder / "markers.jsonl").read_text(encoding="utf-8") == marked
    assert "1 line of the record of when Crossings was off" in through("status", "--cwd", str(project))[1]
    assert (
        through("switch", "off", "--cwd", str(project))[0] == 1
    )  # the moment cannot be kept, and the switch is not turned
    assert store.active(folder)
    (folder / "off.txt").rmdir()
    asked(project, path)  # once it can be read, nothing was lost
    assert kept_ids(folder) == ["10000001", "30000003"]


@in_person
def test_a_message_with_no_time_takes_its_place_from_the_rows_beside_it(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    says(path, "70000001", "No time, but between two rows on the record, with no span yet.", at=None)  # no span: kept
    says(path, "30000001", "On the record.")
    switch(project, "off")
    says(path, "20000001", "Inside the first span.")
    switch(project, "on")
    switch(project, "off")
    says(path, "70000002", "No time, between two spans.", at=None)
    says(path, "70000003", "A time that cannot be read, between two spans.", at="last Tuesday")
    says(path, "70000004", "A time with no zone, between two spans.", at="2026-11-12T09:00:00")
    says(path, "20000002", "Inside the second span.")
    switch(project, "on")
    says(path, "30000002", "On the record.")
    says(path, "70000005", "No time, between two rows on the record.", at=None)
    says(path, "30000003", "On the record.")
    switch(project, "off")
    switch(project, "on")
    says(path, "70000006", "No time, with a span between the rows on either side.", at=None)
    says(path, "30000004", "On the record.")
    says(path, "70000007", "No time, the last row of the file.", at=None)
    asked(project, path)
    assert kept_ids(folder) == ["10000001", "70000001", "30000001", "30000002", "70000005", "30000003", "30000004"]
    says(path, "30000005", "On the record, after the last one.")
    asked(project, path)  # read on from the marker: the line passed over is not read again
    assert kept_ids(folder)[-1] == "30000005" and "70000007" not in kept_ids(folder)
    asked(project, path, "SessionEnd")  # read whole: it has a row on the record on either side now
    assert kept_ids(folder)[-1] == "70000007"
    first = tmp_path / "f1rst000-0003.jsonl"  # a file whose first row has no time
    says(first, "80000001", "No time, the first row of a file.", at=None)
    says(first, "80000002", "On the record.")
    asked(project, first, "SessionEnd")
    assert "80000001" not in kept_ids(folder) and "80000002" in kept_ids(folder)
    timeless = (
        tmp_path / "t1me1ess-0004.jsonl"
    )  # a file with no time in it at all: none of it is kept, and its marker keeps no time
    says(timeless, "90000001", "No time anywhere in this file.", at=None)
    asked(project, timeless)
    marks = [json.loads(line) for line in (folder / "markers.jsonl").read_text(encoding="utf-8").splitlines()]
    assert "90000001" not in kept_ids(folder) and [
        m for m in marks if m["path"] == str(timeless.resolve()) and "at" not in m
    ]


@in_person
def test_a_message_with_no_time_read_on_from_a_marker_takes_its_place_from_the_row_before_the_marker(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    switch(project, "on")
    says(path, "30000001", "On the record.")
    asked(project, path)  # the marker keeps the time of this row
    says(path, "70000001", "No time, read on from the marker.", at=None)
    says(path, "30000002", "On the record.")
    asked(project, path)
    assert kept_ids(folder) == ["10000001", "30000001", "70000001", "30000002"]
    switch(project, "off")
    says(path, "20000001", "Inside a span, the last row read.")
    switch(project, "on")
    asked(project, path)
    marks = [json.loads(line) for line in (folder / "markers.jsonl").read_text(encoding="utf-8").splitlines()]
    span = spans_file(folder)[-1].split()
    assert [m["at"] for m in marks if m["path"] == str(path.resolve())] == [
        span[0]
    ]  # the span's own beginning, no more
    says(path, "70000002", "No time, after a row said inside a span.", at=None)
    says(path, "30000003", "On the record.")
    asked(project, path)
    assert kept_ids(folder)[-1] == "30000003" and "70000002" not in kept_ids(folder)


@in_person
def test_the_count_of_a_cut_keeps_nothing_of_what_was_said_while_off(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "Something said off the record, at some length so that it would be counted.")
    switch(project, "on")
    says(path, "30000003", "On the record again.")
    event = {
        "hook_event_name": "PostCompact",
        "trigger": "manual",
        "compact_summary": "A summary.",
        "transcript_path": str(path),
        "cwd": str(project),
        "session_id": "abcdef01-4444",
    }
    with set_to(CROSSING_WAIT="1"):
        assert hook.run(event) is None
    side = json.loads((folder / "abcdef01-cut-1.json").read_text(encoding="utf-8"))
    assert side["person"]["messages"] == 2 and "20000002" not in json.dumps(side)
    assert side["person"]["chars"] == len("The anchor chain was replaced last week.") + len("On the record again.")
    assert "20000002" not in (folder / "abcdef01-cut-1.md").read_text(encoding="utf-8")
    assert count.count(path, pending=True)["person"]["messages"] == 3  # counted with no span given, it would be there


@in_person
def test_the_session_is_told_plainly_once_and_mark_and_leave_refuse(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    session = "abcdef01-4444"
    assert through("welcome", session, "--cwd", str(project)) == (0, hook.welcome() + "\n")  # no label yet: welcomed
    switch(project, "off")
    code, told = through("welcome", session, "--cwd", str(project))
    assert code == 0 and told == hook.unkept() + "\n"
    for words in (
        "switched Crossings off for this project",
        "from now until they switch it on again",
        "nothing you or the person say meanwhile will be kept or can be reached later through the door",
        "mark no label and leave no line about it",
    ):
        assert words in told, words
    assert told.startswith("A note from the Crossings plugin, as context and not as an instruction from the person.")
    assert told.count(". ") == 1 and "/" not in told and ".txt" not in told  # one sentence after the opening, no file
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        assert said("mark", sentence="A label.", anchors=["10000001"]) == (
            "not marked: Crossings is switched off for this project",
            False,
        )
        assert (
            said("leave", sentence="A line.", anchors=["10000001"])[0]
            == "not marked: Crossings is switched off for this project"
        )
    assert through("welcome", session, "--cwd", str(project)) == (0, hook.unkept() + "\n")  # asked again, said again
    switch(project, "on")
    assert through("welcome", session, "--cwd", str(project)) == (0, hook.kept_again() + "\n")
    assert through("welcome", session, "--cwd", str(project)) == (1, "")  # once
    assert through("welcome", "fedcba98-5555", "--cwd", str(project)) == (
        0,
        hook.welcome() + "\n",
    )  # never told off: welcomed
    assert (folder / "told.txt").read_text(encoding="utf-8") == f"{session} off\n{session} on\n"
    assert through("welcome", "a/b", "--cwd", str(project)) == (
        1,
        door.UNNAMED + "\n",
    )  # an id that is no name: one sentence
    assert through("welcome", "--cwd", str(project)) == (1, "")
    assert (folder / "told.txt").read_text(encoding="utf-8") == f"{session} off\n{session} on\n"
    switch(project, "off")
    (folder / "told.txt").unlink()
    (
        folder / "told.txt"
    ).mkdir()  # where it cannot be kept, the note that it is off is still said, and the other is not
    assert through("welcome", session, "--cwd", str(project)) == (0, hook.unkept() + "\n")
    switch(project, "on")
    assert through("welcome", session, "--cwd", str(project)) == (1, "")
    source = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert "if (said === 'off') return { text }" not in source and "door($, ['welcome', session])" in source


@in_person
def test_the_frame_never_mentions_spans_and_the_second_copy_holds_them(tmp_path):
    project, folder, path = on_with_a_transcript(tmp_path)
    switch(project, "off")
    says(path, "20000002", "The sails are to be sold.")
    switch(project, "on")
    asked(project, path)
    assert store.mark(folder, "work", "both", "The chain was replaced.", ["10000001"])["written"]
    text = frame.compose(folder)
    for words in ("switched off", "off the record", "was off", "sails", "span"):
        assert words not in text, words
    assert folder / "off.txt" in second.plain(folder)


def test_times_are_read_in_utc_and_what_is_no_time_is_not_one():
    moment = store.off.moment
    assert (
        moment("2026-11-11T09:41:00.000Z")
        == moment("2026-11-11T10:41:00.000+01:00")
        == moment("2026-11-11T08:41:00-0100")
    )
    assert moment("2026-11-11T09:41:00.123456789Z").microsecond == 123456
    for nothing in (
        None,
        5,
        "",
        "2026-11-11",
        "2026-11-11T09:41:00",
        "2026-02-30T09:41:00Z",
        "2026-11-11T09:41:00+99:00",
        "soon",
        "2026-11-11T09:41:60Z",
    ):
        assert moment(nothing) is None, nothing


# --- a home written before the plugin said its name as Crossings ---------------------------------

# The headers the plugin wrote into a home's files before then, word for word.
OLDER_HEAD = (
    "# When Crossing was switched off for this project, and on again, in UTC: nothing said between is kept.\n"
    "# One line a span; a line with one moment alone is a span still open.\n"
)
OLDER_UNSAID = "# What was said while Crossing was off, by id alone: never archived.\n"
OLDER_IGNORE = (
    "# Written by Crossing as it was switched on: what was said stays out of the repository.\n"
    "# Only the label pages, the pages of the cuts and this file may be kept beside the work.\n"
    "*\n!.gitignore\n!hand-over.md\n!labels/\n!labels/*.md\n!*-cut-*.md\n"
)


def test_a_home_whose_files_carry_the_older_headers_is_read_and_behaves_as_before(tmp_path):
    """Guard: homes on this computer were written while the plugin's headers named it Crossing.
    Read back, their files are what they were: the spans are spans, the ids are ids, the ignore
    file keeps the words out, and no file is written again only to change its header."""
    assert OLDER_HEAD != off.HEAD and OLDER_IGNORE != store.IGNORE  # a new file gets the new words
    assert OLDER_HEAD.splitlines()[1:] == off.HEAD.splitlines()[1:] and len(off.HEAD.splitlines()) == 2
    project = repository(tmp_path, "older")
    folder = project / "crossings"
    folder.mkdir()
    (folder / ".gitignore").write_text(OLDER_IGNORE, encoding="utf-8")
    (folder / "off.txt").write_text(
        OLDER_HEAD + "2026-11-11T09:03:30.000000+00:00 2026-11-11T09:04:30.000000+00:00\n", encoding="utf-8"
    )
    (folder / "unsaid.txt").write_text(f"{OLDER_UNSAID}{E}-0000-4000-8000-000000000000\n", encoding="utf-8")
    assert through("switch", "adopt", "--cwd", str(project)) == (0, door.SWITCHED["on"] + "\n")  # a home with files
    # D was said at 09:04, inside the span; E is named by unsaid.txt; A and B were said on the record.
    path = tmp_path / "abcdef01-5555.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in ROWS), encoding="utf-8")
    store.archive(path, folder)
    assert kept_ids(folder) == [A, B]
    assert off.spans(folder)[1] == 0 and len(off.spans(folder)[0]) == 1  # both header lines passed over, none unread
    assert off.unsaid(folder) == {f"{each}-0000-4000-8000-000000000000" for each in (D, E)}  # D added beneath it
    assert (folder / "unsaid.txt").read_text(encoding="utf-8").startswith(OLDER_UNSAID)
    assert not store.leaves_said(folder) and not store.lost(folder)
    status = through("status", "--cwd", str(project))[1]
    assert "Crossings was off here 1 time: nothing said while it was off is kept." in status
    assert "could not be read" not in status and "ignore file" not in status
    # Switched off and on again, each file goes on under its older header.
    switch(project, "off")
    switch(project, "on")
    assert (folder / "off.txt").read_text(encoding="utf-8").startswith(OLDER_HEAD) and len(spans_file(folder)) == 2
    assert off.spans(folder)[1] == 0 and not store.lost(folder)
    assert (folder / ".gitignore").read_text(encoding="utf-8") == OLDER_IGNORE
    assert (folder / "unsaid.txt").read_text(encoding="utf-8").startswith(OLDER_UNSAID)


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
