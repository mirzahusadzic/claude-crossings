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


def test_a_long_line_and_the_labels_after_it_stay_within_the_frame(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    mark(project, "next", " ".join(["The mooring is next and the line runs long."] * 90), A)
    for n in range(20):
        mark(project, "work", f"Work label number {n} after the long line.")
    for size in (2000, frame.MOST):
        composed = frame.compose(crossings, size)
        assert "Marked after this line: W2, W3" in composed and "and 8 more." in composed
        assert len(composed) <= size


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
