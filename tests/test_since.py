"""A line left at the door older than the work it speaks of (seen in a real store: the newest line still listed
as open two calls a later work label had closed, and a session reading only the line would have acted on it).
The room and the frame name, beside the line, the work labels marked after it, in the order they were written;
and the first work label marked after the newest line asks, once, for a fresh one. No model, no network.

Run with pytest, or without it:  python3 tests/test_since.py
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_store import A, D, E, at_terminal, home, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, store  # noqa: E402

DAY = "2026-11-12"


def run(project: str, *argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
        code = door.main([*argv, "--cwd", project])
    return code, out.getvalue()


def mark(project: str, kind: str, sentence: str, anchors: str = f"{D},{E}") -> str:
    code, said = run(project, "mark", "--kind", kind, "--whose", "session", "--anchors", anchors, *sentence.split())
    assert code == 0, said
    return said


def test_the_room_names_the_work_labels_marked_after_the_line_at_the_door(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    mark(project, "next", "Two calls are open: the quotes and the caps.", A)
    assert "since" in store.look(crossings)["left"] and store.look(crossings)["left"]["since"] == []
    assert "Marked since it" not in run(project, "look")[1]
    mark(project, "work", "Both calls are settled: the quotes fixed and the caps gone.")
    mark(project, "work", "Three more commits are made.")
    assert store.look(crossings)["left"]["since"] == ["W2", "W3"]
    assert "Marked since it: W2, W3." in run(project, "look")[1]
    mark(project, "next", "All is pushed.", A)  # a fresh line: nothing marked since it
    assert store.look(crossings)["left"]["since"] == []


def test_the_frame_names_them_beside_the_line_it_carries(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    mark(project, "next", "Two calls are open: the quotes and the caps.", A)
    assert "Marked after this line" not in frame.compose(crossings)
    mark(project, "work", "Both calls are settled.")
    composed = frame.compose(crossings)
    assert "Two calls are open: the quotes and the caps." in composed
    assert "Marked after this line: W2." in composed
    assert len(composed) <= frame.MOST


def test_a_long_line_is_kept_as_it_was_and_the_list_beside_it_gives_way(tmp_path):
    """A reading of the first make: the line is what a cold session reads first, and the note means something only beside
    it, so where the room runs out the list of labels is shortened, never the line cut further than before."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    long = " ".join(["The mooring is next and the line runs long."] * 90)
    mark(project, "next", long, A)
    for n in range(20):
        mark(project, "work", f"Work label number {n} after the long line.")
    whole = frame.compose(crossings, frame.MOST)
    assert long in whole, "in a frame of the usual size the long line crosses whole"
    assert "Marked after this line: W2, W3" in whole and "and 8 more." in whole
    assert len(whole) <= frame.MOST
    for size in (2000, 2300, 3000):  # the line cut anyway, which `labels` gives whole
        tight = frame.compose(crossings, size)
        assert len(tight) <= size, "the frame stays within its size"
        assert "`labels N1` gives it whole" in tight
    assert "Marked after this line: W2 and 19 more." in frame.compose(crossings, 3000)
    short = "The mooring is next."
    mark(project, "next", short, A)  # a line that crosses whole, with labels marked after it
    for n in range(20):
        mark(project, "work", f"Another work label, number {n}.")
    for size in (2000, frame.MOST):
        composed = frame.compose(crossings, size)
        assert f"- N2 (session): {short}" in composed and len(composed) <= size, "a whole line is never cut for it"


def test_the_frame_stays_within_its_size_whatever_the_lines_length(tmp_path):
    """The 420 characters a frame keeps for its headings take the note beside a line that crosses whole, and a
    line cut anyway keeps the note within its own room: so no length of line, at any size, makes the frame
    larger than it may be, or cuts a line that would have crossed whole."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    for n, length in enumerate(range(200, 4000, 270)):
        text = ("moor " * (length // 5))[:length].strip() + "."
        mark(project, "next", text, A)
        mark(project, "work", f"Work after the line {n}.")
        for size in (frame.LEAST, 3000, frame.MOST):
            composed = frame.compose(crossings, size)
            assert len(composed) <= size, (length, size)
            assert "Marked after this line:" in composed, (length, size)
            assert text in composed or "gives it whole." in composed, (length, size)


def test_the_first_work_label_after_the_newest_line_asks_once_for_a_fresh_one(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert door.OVERTAKEN not in mark(project, "work", "A label with no line left at all.")
    mark(project, "next", "Two calls are open.", A)
    assert door.OVERTAKEN in mark(project, "work", "Both calls are settled.")
    assert door.OVERTAKEN not in mark(project, "work", "Three more commits are made."), "once a line"
    assert door.OVERTAKEN not in mark(project, "relation", "He asks to be told before a push.", A)
    mark(project, "next", "All is pushed.", A)
    assert door.OVERTAKEN in mark(project, "work", "A new line, overtaken again.")


def test_a_struck_work_label_is_no_label_after_the_line(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    mark(project, "next", "Two calls are open.", A)
    mark(project, "work", "Both calls are settled.")
    with at_terminal():
        assert store.strike(crossings, "W2", "a test")["struck"]
    assert store.look(crossings)["left"]["since"] == []
    assert door.OVERTAKEN in mark(project, "work", "Both calls are settled, again."), "the struck one is none"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
