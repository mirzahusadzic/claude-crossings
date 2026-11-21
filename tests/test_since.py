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

from test_edges import set_to  # noqa: E402
from test_store import A, D, E, at_terminal, home, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, serve, store  # noqa: E402

DAY = "2026-11-12"
# What a mark is answered with after its key, word for word: where a label or a line comes in long, by its length as
# its row keeps it; and once a line, where the line at the door is older than the label.
LONG_LABEL = "This label is {} characters long: a list shows 240 of one, and a frame may have no room for it."
LONG_LINE = (
    "This line is {} characters long: it takes room from the standing lines, the work and the person's own words. "
    "A shorter one can be left in its place."
)
OVERTAKEN = "The line at the door was left before this label: where it no longer holds, a new one can be left."


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
    assert "Marked after this line" not in run(project, "look")[1]
    mark(project, "work", "Both calls are settled: the quotes fixed and the caps gone.")
    mark(project, "work", "Three more commits are made.")
    assert store.look(crossings)["left"]["since"] == ["W2", "W3"]
    assert "Marked after this line: W2, W3." in run(project, "look")[1]
    assert "Marked since" not in run(project, "look")[1], "one wording for one fact, the frame's"
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
        assert len(tight) <= frame.bounded(size), "the frame stays within its size, or the least a frame may be"
        assert "`labels N1` gives it whole" in tight
    assert "Marked after this line: W2 and 19 more." in frame.compose(crossings, 3000)
    short = "The mooring is next."
    mark(project, "next", short, A)  # a line that crosses whole, with labels marked after it
    for n in range(20):
        mark(project, "work", f"Another work label, number {n}.")
    for size in (2000, frame.MOST):
        composed = frame.compose(crossings, size)
        assert f"- N2 (session): {short}" in composed and len(composed) <= frame.bounded(size), (
            "a whole line is never cut for it"
        )


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


def of(length: int) -> str:
    """A sentence of so many characters, as a label's row keeps it (store.plain): words, and dots to the length."""
    words = ("The keel is checked plank by plank before the paint " * 90)[: length - 1].rstrip()
    return words + "." * (length - len(words))


def served(project: str, name: str, **given) -> str:
    """What the door's server answers a call with, for a session a person sits in."""
    with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=project):
        return serve.call(name, given)[0]


def first(answer: str) -> str:
    """An answer of `leave` up to what the record weighs, which may follow it apart (see tests/test_unmarked.py)."""
    return answer.split("\n\n")[0]


def test_a_label_longer_than_a_list_shows_is_marked_whole_and_its_answer_says_how_long_it_is(tmp_path):
    """Guard: sessions wrote labels of 1,000 to 2,500 characters, a list shows 240 of one and a frame holds about
    9,000 in all, and the answer was "marked W2" at every length up to the 4,000 a mark takes. A label about the work
    or about the two of you that is longer than 240 characters is written whole, as before, and its answer adds one
    sentence of its length, counted as its row keeps it and with a thousands comma; one of 240 adds nothing."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert served(project, "mark", sentence=of(240), anchors=[D]) == "marked W2"
    assert served(project, "mark", sentence=of(241), anchors=[D]) == "marked W3. " + LONG_LABEL.format("241")
    assert served(project, "mark", sentence=of(240), anchors=[A], kind="relation") == "marked R2"
    relation = served(project, "mark", sentence=of(241), anchors=[A], kind="relation")
    assert relation == "marked R3. " + LONG_LABEL.format("241")
    given = of(240).replace(" ", "   ", 1)  # 242 characters given, 240 kept: a row holds one space for a run of them
    assert len(given) == 242 and served(project, "mark", sentence=given, anchors=[D]) == "marked W4"
    assert served(project, "mark", sentence=of(2500), anchors=[D]) == "marked W5. " + LONG_LABEL.format("2,500")
    rows = store.listed(crossings, ids=("W3", "R3", "W4", "W5"))["labels"]
    assert {row["id"]: row["text"] for row in rows} == {"W3": of(241), "R3": of(241), "W4": of(240), "W5": of(2500)}
    assert door.SHORT == 240  # what a list shows of one, and the point the sentence is said from


def test_a_long_stack_is_answered_as_a_long_label(tmp_path):
    """Guard: a stack is a label of its kind over the lines beneath it, and the frame carries it in their place: one
    longer than a list shows is answered with its length as any label is, about the work or about the two of you."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    served(project, "mark", sentence="The hull is scraped.", anchors=[D])  # W2
    served(project, "mark", sentence="The hull is painted.", anchors=[E])  # W3
    assert served(project, "mark", sentence=of(612), anchors=["W2", "W3"]) == "marked W4. " + LONG_LABEL.format("612")
    assert served(project, "mark", sentence=of(240), anchors=["W4"]) == "marked W5"  # a stack over it, not long
    served(project, "mark", sentence="The boat is called Tern.", anchors=[A], kind="relation")  # R2
    served(project, "mark", sentence="Its mooring is 41.", anchors=[A], kind="relation")  # R3
    stack = served(project, "mark", sentence=of(300), anchors=["R2", "R3"], kind="relation")
    assert stack == "marked R4. " + LONG_LABEL.format("300")
    assert store.listed(crossings, ids=("W4",))["labels"][0]["beneath"]  # a stack, with its lines beneath it


def test_a_line_at_the_door_longer_than_a_tenth_of_a_frame_is_left_whole_and_its_answer_says_what_it_takes(tmp_path):
    """Guard: a line left at the door is fitted first and takes the room of what the frame fits after it (see
    frame._composed), and a line of 2,500 characters was answered "marked N1" as one of twenty was. A line longer than
    900 characters, a tenth of a frame of the usual size, is left whole, as before, and its answer adds what it takes
    and that a shorter one can be left in its place; one of 900 adds nothing."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert first(served(project, "leave", sentence=of(900), anchors=[D])) == "marked N1"
    assert first(served(project, "leave", sentence=of(901), anchors=[D])) == "marked N2. " + LONG_LINE.format("901")
    assert first(served(project, "leave", sentence=of(2140), anchors=[D])) == "marked N3. " + LONG_LINE.format("2,140")
    longest = served(project, "leave", sentence=of(store.LONGEST), anchors=[D])
    assert first(longest) == "marked N4. " + LONG_LINE.format("4,000")
    rows = store.listed(crossings, ids=("N2", "N4"))["labels"]
    assert {row["id"]: row["text"] for row in rows} == {"N2": of(901), "N4": of(4000)}  # left whole, nothing cut
    assert door.TENTH == frame.SIZE // 10 == 900


def test_a_refusal_and_a_silencing_of_any_length_are_answered_with_their_key_alone(tmp_path):
    """Guard: a refusal's sentence is its reason and crosses whole by rule, and a silencing's says why a refusal
    stands no longer: neither is said to be long, at any length a mark takes, where a label about the work as long
    is."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert served(project, "mark", sentence=of(901), anchors=[D]) == "marked W2. " + LONG_LABEL.format("901")
    for n, length in enumerate((241, 901, store.LONGEST), 1):
        assert served(project, "mark", sentence=of(length), anchors=[D], kind="refused") == f"marked X{n}", length
    for n, length in enumerate((241, 901, store.LONGEST), 1):
        silenced = served(project, "mark", sentence=of(length), anchors=[f"X{n}", E], kind="silenced")
        assert silenced == f"marked S{n}", length
    code, said = run(project, "mark", "--kind", "refused", "--anchors", D, "--bare", *of(store.LONGEST).split())
    assert code == 0 and said == "marked X4\n"  # nor from the person's own terminal


def test_the_length_is_said_before_the_line_at_the_door_and_that_sentence_is_as_it_was(tmp_path):
    """Guard: the answer of the first work label marked after the newest line left at the door said, after its key,
    that the line is older than it. A long one says its length first, and then that sentence, byte for byte; a short
    one says that sentence alone, as before."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    served(project, "leave", sentence="Two calls are open.", anchors=[A])
    long = served(project, "mark", sentence=of(612), anchors=[D])
    assert long == f"marked W2. {LONG_LABEL.format('612')} {OVERTAKEN}" and OVERTAKEN == door.OVERTAKEN
    assert served(project, "mark", sentence=of(612), anchors=[D]) == "marked W3. " + LONG_LABEL.format("612")
    served(project, "leave", sentence="All is pushed.", anchors=[A])
    assert served(project, "mark", sentence="Both calls are settled.", anchors=[D]) == f"marked W4. {OVERTAKEN}"


def test_the_persons_own_verb_and_a_sessions_shell_are_answered_as_the_server_is(tmp_path):
    """Guard: the sentence is the door's, so the person's own `door.py mark` at their terminal and a session's shell
    are told it as the server is, after the key and where the answer names the page."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    label, line = of(612), of(2140)
    assert served(project, "mark", sentence=label, anchors=[D]) == "marked W2. " + LONG_LABEL.format("612")
    code, said = run(project, "mark", "--kind", "work", "--anchors", D, *label.split())  # names the page
    assert code == 0 and said.startswith("marked W3 in ") and said.endswith(f".md. {LONG_LABEL.format('612')}\n")
    code, said = run(project, "mark", "--kind", "next", "--anchors", D, "--bare", *line.split())
    assert code == 0 and said == f"marked N1. {LONG_LINE.format('2,140')}\n"
    out = io.StringIO()
    with at_terminal(False), contextlib.redirect_stdout(out):  # a session's shell: the door stands at no terminal
        code = door.main(["mark", "--kind", "relation", "--anchors", A, "--bare", "--cwd", project, *label.split()])
    assert code == 0 and out.getvalue() == f"marked R2. {LONG_LABEL.format('612')}\n"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
