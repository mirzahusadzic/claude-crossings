"""What a call reads: a hook's log reads nothing of a transcript, an archive reads only what was
added to a transcript since it last read it, and a line of a home's plain files that is not what
it must be is passed over. No model, no network; every transcript is made up here.

Run with pytest, or without it:  python3 tests/test_reading.py
The scale test is left out where CROSSING_SCALE is 0.
"""

from __future__ import annotations

import builtins
import contextlib
import hashlib
import io
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_store import A, D, home, in_person, row, sweep, switched_on  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import hook, store  # noqa: E402


@contextlib.contextmanager
def parsing():
    """How many lines of a transcript are parsed while the block runs: every call of json.loads on
    a row that carries a `timestamp`, which a transcript's rows do and the archive's never do."""
    counted, loads = [0], json.loads

    def counting(text, *args, **kwargs):
        if (b'"timestamp"' if isinstance(text, (bytes, bytearray)) else '"timestamp"') in text:
            counted[0] += 1
        return loads(text, *args, **kwargs)

    json.loads = counting
    try:
        yield counted
    finally:
        json.loads = loads


def said(n: int, minute: int = 0) -> dict:
    """A made-up message of the person's, its id made from `n`."""
    return row("user", f"{n:08x}", minute % 60, f"Made-up message number {n} about the hull.")


def lines(rows: list[dict]) -> str:
    return "".join(json.dumps(r) + "\n" for r in rows)


def held(crossings: Path) -> list[str]:
    """The uuid of every message the archive holds, as many times as it holds it."""
    return [r["uuid"] for r in store._archived(crossings)]


def started(tmp_path: Path, count: int = 40) -> tuple[Path, Path]:
    """A home switched on and a transcript of `count` messages, archived once."""
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    switched_on(project)
    path = tmp_path / "abcdef01-0101.jsonl"
    path.write_text(lines([said(n, n) for n in range(count)]), encoding="utf-8")
    assert store.archive(path, project / "crossings") == count
    return project / "crossings", path


def marker(crossings: Path, path: Path) -> dict:
    return store.markers(crossings)[str(path.resolve())]


# --- the archive reads what was added (B2) ------------------------------------------------------------


def test_a_second_archive_parses_only_the_lines_added_since_the_first(tmp_path):
    crossings, path = started(tmp_path)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(lines([said(n, n) for n in range(100, 110)]))
    with parsing() as parsed:
        assert store.archive(path, crossings) == 10
    assert parsed[0] == 10, parsed[0]
    with parsing() as parsed:
        assert store.archive(path, crossings) == 0
    assert parsed[0] == 0  # nothing new, nothing parsed
    assert len(held(crossings)) == len(set(held(crossings))) == 50
    assert marker(crossings, path)["offset"] == path.stat().st_size


def test_nothing_new_reads_nothing_of_the_archive_either(tmp_path):
    crossings, path = started(tmp_path)
    reads, was = [], store._archived
    store._archived = lambda folder: reads.append(folder) or was(folder)
    try:
        assert store.archive(path, crossings) == 0
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "type": "user",
                        "uuid": "f0f0f0f0-1",
                        "toolUseResult": {"stdout": "x"},
                        "timestamp": "2026-11-11T10:00:00Z",
                        "message": {"content": [{"type": "tool_result", "content": "x"}]},
                    }
                )
                + "\n"
            )
        assert store.archive(path, crossings) == 0  # a tool's traffic is no message to keep
        assert reads == []
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(lines([said(200, 1)]))
        assert store.archive(path, crossings) == 1 and len(reads) == 1  # a message to keep: what is held is read
    finally:
        store._archived = was


def test_a_transcript_replaced_by_another_of_the_same_length_is_read_from_its_start(tmp_path):
    crossings, path = started(tmp_path)
    first = path.read_text(encoding="utf-8")
    other = first.replace('"uuid": "00', '"uuid": "ff')  # other ids, written to the same length
    assert len(other.encode()) == len(first.encode()) and other != first
    path.write_text(other, encoding="utf-8")
    with parsing() as parsed:
        assert store.archive(path, crossings) == 40
    assert parsed[0] == 40
    assert len(held(crossings)) == len(set(held(crossings))) == 80
    path.write_text(first, encoding="utf-8")  # and the first again: all of it is held already
    assert store.archive(path, crossings) == 0 and len(held(crossings)) == 80


def test_a_truncated_transcript_is_read_from_its_start(tmp_path):
    crossings, path = started(tmp_path)
    whole = path.read_text(encoding="utf-8").splitlines(keepends=True)
    path.write_text("".join(whole[:10]), encoding="utf-8")  # shorter than the marker
    with parsing() as parsed:
        assert store.archive(path, crossings) == 0
    assert parsed[0] == 10 and marker(crossings, path)["offset"] == path.stat().st_size
    path.write_text(
        "".join(whole[:5]) + lines([said(n, n) for n in range(300, 340)]), encoding="utf-8"
    )  # cut and grown past it
    assert path.stat().st_size > len("".join(whole[:10]).encode())
    assert store.archive(path, crossings) == 40
    assert len(held(crossings)) == len(set(held(crossings))) == 80


def test_a_half_written_last_line_is_read_once_it_is_whole(tmp_path):
    crossings, path = started(tmp_path, 5)
    line = json.dumps(said(77, 7))
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line[:30])  # the harness is still writing it
    assert store.archive(path, crossings) == 0
    assert marker(crossings, path)["offset"] == path.stat().st_size - 30  # the marker stops before it
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line[30:] + "\n")
    with parsing() as parsed:
        assert store.archive(path, crossings) == 1
    assert parsed[0] == 1 and f"{77:08x}-0000-4000-8000-000000000000" in held(crossings)
    assert len(held(crossings)) == len(set(held(crossings))) == 6


def test_a_marker_file_that_is_torn_or_holds_nonsense_is_read_as_no_marker(tmp_path):
    crossings, path = started(tmp_path)
    key = str(path.resolve())
    good = marker(crossings, path)
    for nonsense in (
        json.dumps({"path": key, **good})[:25],  # torn in the middle of a line
        'nonsense\n[1, 2]\nnull\n"a string"\n',
        json.dumps({"path": key, "offset": str(good["offset"]), "check": good["check"]}),
        json.dumps({"path": key, "offset": -5, "check": good["check"]}),
        json.dumps({"path": key, "offset": True, "check": good["check"]}),
        json.dumps({"path": key, "offset": good["offset"]}),
        json.dumps({"path": [key], "offset": good["offset"], "check": good["check"]}),
        json.dumps({"path": key, "offset": good["offset"], "check": "0" * 64}),
    ):  # the bytes before it are not those read
        (crossings / store.MARKERS).write_text(nonsense, encoding="utf-8")
        with parsing() as parsed:
            assert store.archive(path, crossings) == 0, nonsense
        assert parsed[0] == 40, nonsense  # read from its start
        assert marker(crossings, path) == good  # and the marker is made right again
    (crossings / store.MARKERS).write_bytes(b"\xff\xfe not text at all \x00\n")
    assert store.markers(crossings) == {} and store.archive(path, crossings) == 0
    assert len(held(crossings)) == len(set(held(crossings))) == 40


def test_a_marker_for_a_transcript_at_another_path_is_not_this_ones(tmp_path):
    crossings, path = started(tmp_path)
    fork = tmp_path / "forked01-0101.jsonl"  # a fork repeats the messages under their ids, and adds its own
    fork.write_text(path.read_text(encoding="utf-8") + lines([said(n, n) for n in range(500, 503)]), encoding="utf-8")
    with parsing() as parsed:
        assert store.archive(fork, crossings) == 3
    assert parsed[0] == 43  # its own marker, none yet: read from its start
    assert set(store.markers(crossings)) == {str(path.resolve()), str(fork.resolve())}
    moved = tmp_path / "moved" / path.name  # the same file at another path
    moved.parent.mkdir()
    path.rename(moved)
    with open(moved, "a", encoding="utf-8") as handle:
        handle.write(lines([said(600, 1)]))
    with parsing() as parsed:
        assert store.archive(moved, crossings) == 1
    assert parsed[0] == 41
    assert len(held(crossings)) == len(set(held(crossings))) == 44


def test_what_is_struck_does_not_come_back_whatever_the_marker(tmp_path):
    crossings, path = started(tmp_path)
    struck = f"{3:08x}"
    assert store.strike(crossings, struck)["struck"]
    for whole in (False, True):
        assert store.archive(path, crossings, whole=whole) == 0
    (crossings / store.MARKERS).unlink()
    assert store.archive(path, crossings) == 0
    assert struck not in [r["id"] for r in store._archived(crossings)] and len(held(crossings)) == 39


def ahead(crossings: Path, path: Path) -> None:
    """Set the transcript's marker at its end, as if the last lines had been read."""
    with open(path, "rb") as handle:
        data = handle.read()
    mark = {
        "path": str(path.resolve()),
        "offset": len(data),
        "check": hashlib.sha256(data[-store.CHECKED :]).hexdigest(),
    }
    (crossings / store.MARKERS).write_text(json.dumps(mark) + "\n", encoding="utf-8")


@in_person
def test_the_whole_pass_at_a_sessions_end_picks_up_what_a_marker_stepped_over(tmp_path):
    crossings, path = started(tmp_path)
    project = crossings.parent
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(lines([said(900, 9)]))
    ahead(crossings, path)
    assert store.archive(path, crossings) == 0  # the marker steps over it
    missing = f"{900:08x}-0000-4000-8000-000000000000"
    assert missing not in held(crossings)
    event = {
        "hook_event_name": "SessionEnd",
        "transcript_path": str(path),
        "cwd": str(project),
        "session_id": "abcdef01-0101",
    }
    with set_to(CROSSING_WAIT="1"):
        assert hook.run(event) is None
    assert missing in held(crossings) and len(held(crossings)) == len(set(held(crossings))) == 41
    # The session's end that is not waited for asks the door to build, which reads the transcript whole too.
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(lines([said(901, 9)]))
    ahead(crossings, path)
    assert through("status", "--transcript", str(path), "--cwd", str(project))[1].count("Newly archived") == 0
    assert hook.keep(path, project, wait=False).wait(timeout=60) == 0
    assert f"{901:08x}-0000-4000-8000-000000000000" in held(crossings) and len(held(crossings)) == 42


class Tallied:
    """An open file of the archive's pages, which counts what is read of it."""

    def __init__(self, handle, tally: list[int]):
        self.handle, self.tally = handle, tally

    def read(self, *args):
        data = self.handle.read(*args)
        self.tally[0] += len(data)
        return data

    def __iter__(self):
        for line in self.handle:
            self.tally[0] += len(line)
            yield line

    def __enter__(self):
        self.handle.__enter__()
        return self

    def __exit__(self, *args):
        return self.handle.__exit__(*args)

    def __getattr__(self, name):
        return getattr(self.handle, name)


@contextlib.contextmanager
def reading_the_archive(crossings: Path):
    """How much of the archive's pages is read while the block runs, in bytes or characters, and
    how many of their lines are parsed: every call of json.loads on a line that names a voice,
    which the archive's lines do and a transcript's rows never do."""
    tally, parsed, real_open, real_io_open, loads = [0], [0], builtins.open, io.open, json.loads
    pages = str((crossings / "said").resolve())

    def watching(file, *args, **kwargs):
        handle = real_open(file, *args, **kwargs)
        return Tallied(handle, tally) if str(Path(file).resolve()).startswith(pages) else handle

    def counting(text, *args, **kwargs):
        if (b'"voice"' if isinstance(text, (bytes, bytearray)) else '"voice"') in text:
            parsed[0] += 1
        return loads(text, *args, **kwargs)

    builtins.open = io.open = watching
    json.loads = counting
    try:
        yield tally, parsed
    finally:
        builtins.open, io.open, json.loads = real_open, real_io_open, loads


@in_person
def test_ten_new_messages_in_a_store_of_thousands_read_no_page_of_the_archive_whole(tmp_path):
    """The hook before a door call archives what was just said and brings the index up to it: by
    adding to the index, the archive's pages are read only where they grew."""
    crossings, path = started(tmp_path, 3000)
    store.build(crossings)
    page = crossings / "said" / "abcdef01.jsonl"
    with open(path, "a", encoding="utf-8") as handle:  # said after all that is held
        handle.write(lines([{**said(n), "timestamp": f"2026-11-11T10:00:0{n % 10}.000Z"} for n in range(5000, 5010)]))
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__plugin_crossing_door__find",
        "transcript_path": str(path),
        "cwd": str(crossings.parent),
        "session_id": "abcdef01-0101",
    }
    with reading_the_archive(crossings) as (read, parsed):
        assert hook.run(event) is None
    added = sum(len(line.encode()) for line in page.read_text(encoding="utf-8").splitlines(keepends=True)[-10:])
    assert parsed[0] == 10, parsed[0]  # the ten lines added, and none of the thousands before them
    # Its check before the marker, the lines added, and its last byte, which says whether its last line was ended.
    assert read[0] <= store.CHECKED + added + 1 < page.stat().st_size // 10, (read[0], added, page.stat().st_size)
    assert store.status(crossings)["his"] == 3010 and store.find(crossings, "5009")["said"][0]["id"] == f"{5009:08x}"


# --- the log reads nothing of a transcript (B1) ---------------------------------------------------------


def test_a_hook_call_with_the_log_on_does_not_open_the_transcript(tmp_path):
    path = tmp_path / "abcdef01-0202.jsonl"
    path.write_text(lines([said(n, n) for n in range(30)]), encoding="utf-8")
    never = tmp_path / "never"  # a project where Crossing was never switched on
    never.mkdir()
    opened, real_open, real_io_open = [], builtins.open, io.open

    def watching(file, *args, **kwargs):
        if str(file) == str(path):
            opened.append(str(file))
        return real_open(file, *args, **kwargs)

    log = Path(os.environ["CLAUDE_PLUGIN_DATA"]) / "calls.log"
    before = log.read_text(encoding="utf-8") if log.exists() else ""
    for name in ("PreToolUse", "SessionStart", "SessionEnd"):
        event = {
            "hook_event_name": name,
            "source": "startup",
            "tool_name": "mcp__plugin_crossing_door__find",
            "transcript_path": str(path),
            "cwd": str(never),
            "session_id": "abcdef01-0202",
        }
        builtins.open = io.open = watching
        stdin = sys.stdin
        sys.stdin = io.StringIO(json.dumps(event))
        try:
            with set_to(CROSSING_DEBUG=None):  # the log is on unless it is set to 0
                assert hook.main() == 0
        finally:
            builtins.open, io.open, sys.stdin = real_open, real_io_open, stdin
    assert opened == [], opened
    written = [json.loads(line) for line in log.read_text(encoding="utf-8")[len(before) :].splitlines()]
    assert [(w["event"], w["phase"]) for w in written] == [
        (name, phase) for name in ("PreToolUse", "SessionStart", "SessionEnd") for phase in ("start", "end")
    ]
    assert all(
        w["transcript_bytes"] == path.stat().st_size and isinstance(w["transcript_changed"], float) for w in written
    )
    assert all("lines" not in w and "cuts_in_transcript" not in w for w in written)
    with set_to(CROSSING_DEBUG=None):
        for given in (
            "",
            5,
            None,
            str(tmp_path / "gone.jsonl"),
        ):  # no transcript, or no path at all: nothing to measure
            hook.note({"hook_event_name": "PreToolUse", "transcript_path": given})
    gone = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()[-4:]]
    assert [(w["transcript_bytes"], w["transcript_changed"]) for w in gone] == [(None, None)] * 4


# --- a line that is not what it must be is passed over (B4) ---------------------------------------------

NOT_ROWS = [
    "[1, 2]",
    '"a string"',
    "null",
    "17",
    '{"id": "abababab", "voice": "his", "text": "no uuid"}',
    json.dumps({"uuid": 5, "id": "cdcdcdcd", "session": "s", "voice": "his", "text": "t"}),
    json.dumps({"uuid": "efefefef-1", "id": "efefefef", "session": "s", "voice": "nobody", "text": "t"}),
    json.dumps({"uuid": "a0a0a0a0-1", "id": "a0a0a0a0", "session": "s", "voice": "his", "text": "t", "at": 5}),
    json.dumps(
        {"uuid": "b0b0b0b0-1", "id": "b0b0b0b0", "session": "s", "voice": "session", "text": "t", "model": {"a": 1}}
    ),
    "not json at all",
]


def test_a_line_of_the_archive_that_is_no_message_is_passed_over_everywhere(tmp_path):
    crossings, path = home(tmp_path)
    project = crossings.parent
    page = crossings / "said" / "session-.jsonl"
    page.write_text(page.read_text(encoding="utf-8") + "\n".join(NOT_ROWS) + "\n\n", encoding="utf-8")
    assert store.build(crossings)["unread"] == len(NOT_ROWS)  # the empty line is not counted
    assert len(store._archived(crossings)) == 4
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row("user", "12121212", 50, "Said after the bad lines.")) + "\n")
    assert store.archive(path, crossings) == 1 and store.archive(path, crossings, whole=True) == 0
    code, shown = through("status", "--cwd", str(project))
    assert code == 0 and f" {len(NOT_ROWS)} lines of the archive could not be read and were passed over." in shown
    for argv in (
        ["look"],
        ["labels"],
        ["find", "hull"],
        ["thread", D],
        ["frame"],
        ["build", "--transcript", str(path)],
    ):
        assert through(*argv, "--cwd", str(project))[0] == 0, argv
    event = {"transcript_path": str(path), "cwd": str(project), "session_id": "session-0001"}
    with set_to(CROSSING_WAIT="1"):
        for name, more in (
            ("PreToolUse", {}),
            ("SessionEnd", {}),
            ("PostToolUse", {"tool_input": {"sentence": "x"}, "tool_response": "marked W1"}),
        ):
            assert hook.run({**event, "hook_event_name": name, **more}) is None, name
    assert store.mark(crossings, "work", "both", "Marked over bad lines.", [D], model="made-up-model")["written"]
    out = store.strike(crossings, A)
    assert out["struck"] and out["removed"] == 1
    assert page.read_text(encoding="utf-8").count("\n") >= len(NOT_ROWS)  # what was no message is left as it was
    page.write_text("\n".join(NOT_ROWS[:1]) + "\n", encoding="utf-8")
    assert through("build", "--cwd", str(project))[1].endswith(
        " 1 line of the archive could not be read and was passed over.\n"
    )
    page.write_text("", encoding="utf-8")
    assert "could not be read" not in through("build", "--cwd", str(project))[1]  # said only when it is so


def test_a_line_of_the_log_of_pulls_or_of_the_models_that_is_no_line_is_passed_over(tmp_path):
    crossings, _ = home(tmp_path)
    assert store.mark(crossings, "work", "both", "A label of a known model.", [D], model="made-up-model")["written"]
    with open(crossings / store.MODELS, "a", encoding="utf-8") as handle:
        handle.write("nonsense\nW9@zzzzzz\n\n[1]\n")
    assert store.models(crossings) == {("W2", store.digest("A label of a known model.")): "made-up-model"}
    store.reached(crossings, "thread", [A])
    store.reached(crossings, "thread", [D])
    with open(crossings / "reached.jsonl", "a", encoding="utf-8") as handle:
        handle.write('not json\n[1, 2]\n{"ids": "x"}\n{"ids": [1]}\n\nhalf a line naming ' + A + "\n")
    assert store.strike(crossings, A)["struck"]
    kept = (crossings / "reached.jsonl").read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["ids"] for line in kept[:1]] == [[D]]  # the pull of the struck id is gone
    assert kept[1:] == [
        "not json",
        "[1, 2]",
        '{"ids": "x"}',
        '{"ids": [1]}',
    ]  # what is no pull stays, unless it names it
    assert all(A not in line for line in kept)


# --- at scale ------------------------------------------------------------------------------------------------


def test_at_scale_an_archive_reads_only_what_was_added(tmp_path):
    """A few hundred thousand short made-up lines, a tenth of them messages. Left out where
    CROSSING_SCALE is 0; the bounds are generous, for a computer that is busy with other work."""
    if os.environ.get("CROSSING_SCALE") == "0":
        return
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    switched_on(project)
    crossings, path = project / "crossings", tmp_path / "abcdef01-0303.jsonl"
    with open(path, "w", encoding="utf-8") as handle:
        for n in range(300000):
            handle.write(
                json.dumps(
                    said(n, n)
                    if n % 10 == 0
                    else {
                        "type": "user",
                        "uuid": f"{n:08x}-9",
                        "timestamp": "2026-11-11T10:00:00Z",
                        "toolUseResult": {"stdout": "x"},
                        "message": {"content": [{"type": "tool_result", "content": "ok"}]},
                    }
                )
                + "\n"
            )
    start = time.perf_counter()
    assert store.archive(path, crossings) == 30000
    first = time.perf_counter() - start
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(lines([said(n, n) for n in range(400000, 400010)]))
    start = time.perf_counter()
    with parsing() as parsed:
        assert store.archive(path, crossings) == 10
    added = time.perf_counter() - start
    start = time.perf_counter()
    assert store.archive(path, crossings) == 0
    nothing = time.perf_counter() - start
    assert parsed[0] == 10
    assert first < 60 and added < 5 and nothing < 1, (first, added, nothing)


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            took = time.perf_counter()
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name, f"({time.perf_counter() - took:.1f} s)" if "scale" in name else "")
