"""The sampler joined to the home: the files it reads (the cut sidecars, the log of pulls), the events it gives,
and a cut's frame packed, which says no counts of the stretch. Every index is made by hand in memory (the three
tables of tests/sampler_schema.sql, rows inserted directly, and for the packed frame an empty table of the lines
beneath a stack), with made-up ids and a made-up word; every home is a temporary folder."""

from __future__ import annotations

import ast
import contextlib
import io
import json
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_store import sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, sample, store  # noqa: E402
from crossing.sampler import core, from_store  # noqa: E402

SCHEMA = (ROOT / "tests" / "sampler_schema.sql").read_text(encoding="utf-8")
# The contract: every key an event holds, and no other (as tests/test_sampler_from_store.py holds it).
CONTRACT = {"id", "in_stretch", "distance", "anchored", "labelled", "pulled", "guard"}


def said(seq: int, name: str, voice: str = "his", text: str = "tove", session: str = "s1") -> tuple:
    return (seq, name, voice, text, session)


def index(*rows: tuple, labels: tuple = (), anchors: tuple = ()) -> sqlite3.Connection:
    """An index in memory with the three tables, these rows of `said`, each with a whole id of its own, and these
    rows of `label` (an id and a kind) and of `anchor` (a label and the id it rests on)."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    for seq, name, voice, text, session in rows:
        db.execute(
            "insert into said (seq, uuid, id, session, voice, at, text, model) values (?, ?, ?, ?, ?, null, ?, '')",
            (seq, f"{name}-u{seq}", name, session, voice, text),
        )
    for name, kind in labels:
        db.execute("insert into label (id, kind) values (?, ?)", (name, kind))
    for label, name in anchors:
        db.execute("insert into anchor (label, said) values (?, ?)", (label, name))
    return db


def cut(folder: Path, session: str, n: int, *ids: str) -> None:
    """A cut sidecar of the session, whose person's pointers name these ids."""
    side = {"person": {"pointers": [{"id": each} for each in ids]}, "session": {"pointers": []}}
    store.within(folder, f"{session}-cut-{n}.json").write_text(json.dumps(side), encoding="utf-8")


def pulls(folder: Path, *ids: str) -> None:
    """The home's log of pulls: one pull a line, each naming one of these ids."""
    text = "".join(json.dumps({"ids": [each]}) + "\n" for each in ids)
    store.within(folder, "reached.jsonl").write_text(text, encoding="utf-8")


def b(k: int) -> str:
    """The id of the k-th message of the person's in a made-up stretch."""
    return f"b{k:07d}"


@contextlib.contextmanager
def standing_in(module, name: str, stand_in):
    """A function of a module stood in for, and the real one put back however the test ends."""
    real = getattr(module, name)
    setattr(module, name, stand_in)
    try:
        yield
    finally:
        setattr(module, name, real)


# --- the files the home's side reads ------------------------------------------------------------------------------


def test_a_cut_sidecar_that_cannot_be_read_is_passed_over(tmp_path):
    cut(tmp_path, "s1", 1, "aaaaaaa1")
    store.within(tmp_path, "s1-cut-2.json").write_text("{ cut short", encoding="utf-8")
    store.within(tmp_path, "s1-cut-3.json").write_bytes(b"\xff\xfe\x00")
    store.within(tmp_path, "s1-cut-4.json").mkdir()  # a folder of the name: no file to read
    store.within(tmp_path, "s1-cut-5.json").write_text("[1, 2]", encoding="utf-8")
    side = {"person": {"pointers": "aaaaaaa9"}, "session": {"pointers": [{"id": 7}, "x", {"id": "bbbbbbb1"}]}}
    store.within(tmp_path, "s1-cut-6.json").write_text(json.dumps(side), encoding="utf-8")
    cut(tmp_path, "s10", 1, "zzzzzzz9")  # another session's, though its name begins as this one's
    assert sample._cut_ids(tmp_path, "s1") == {"aaaaaaa1", "bbbbbbb1"}
    db = index(said(1, "aaaaaaa1", text="tove"), said(2, "aaaaaaa2", text="wabe"))
    assert [row["id"] for row in sample.stretch(tmp_path, db, "s1", 400)] == ["aaaaaaa2"]


def test_no_log_of_pulls_gives_no_pulls(tmp_path):
    assert sample.pulled(tmp_path) == {}
    lines = [
        {"ids": ["aaaaaaa1-u1", "aaaaaaa2"]},
        {"ids": ["aaaaaaa1"]},
        {"ids": ["aaaaaaa3", "aaaaaaa3-u3"]},  # a pull counts once a message
        {"ids": ["aaaaaaa4+paste"]},  # a paste, none of the person's words
        {"ids": "aaaaaaa5"},  # no pull
    ]
    text = "\n".join(json.dumps(each) for each in lines) + "\nnot a pull\n"
    store.within(tmp_path, "reached.jsonl").write_text(text, encoding="utf-8")
    assert sample.pulled(tmp_path) == {"aaaaaaa1": 2, "aaaaaaa2": 1, "aaaaaaa3": 1}


# --- what is gone: the person's sampler, its files and its verb ------------------------------------------------------


def test_nothing_of_the_sampler_that_chose_is_left_in_the_home_side_the_door_or_the_store(tmp_path):
    gone = ("SWITCH", "OWN", "RELEASE", "switched", "turn", "live", "release_of", "frozen", "release", "scored", "pick")
    assert [name for name in gone if hasattr(sample, name)] == []
    assert [name for name in ("RELEASE", "_uncased", "_names") if hasattr(store, name)] == []
    assert [name for name in vars(door) if name.startswith("SAMPLE_")] == []
    assert [
        name for name in ("sampling", "live_settings", "released", "cases", "checked", "why") if hasattr(door, name)
    ] == []
    assert not hasattr(frame, "_weighed")
    assert "sample" not in door.PERSONAL


def test_the_door_has_no_verb_sample(tmp_path):
    said_to = io.StringIO()
    with contextlib.redirect_stderr(said_to), contextlib.redirect_stdout(io.StringIO()):
        try:
            door.main(["sample", "on", "--cwd", str(tmp_path)])
        except SystemExit as stopped:
            assert stopped.code == 2
        else:
            raise AssertionError("the door took the verb sample")
    assert "invalid choice: 'sample'" in said_to.getvalue()


def test_compose_and_composed_take_no_rule_and_no_weighed_and_nothing_of_the_counted_part_is_left(tmp_path):
    tree = ast.parse((ROOT / "crossing" / "frame.py").read_text(encoding="utf-8"))
    defs = {node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
    for name in ("compose", "_composed"):
        args = defs[name].args
        named = {each.arg for each in args.posonlyargs + args.args + args.kwonlyargs}
        named |= {each.arg for each in (args.vararg, args.kwarg) if each is not None}
        assert not named & {"rule", "weighed"}, name
        assert "session" in named, name
    assert "_weighed" not in defs
    # the part that said the stretch a cut ended by count is gone, with what it was made from
    assert not {"_shaped", "shape_part", "_run"} & set(defs)
    assert [name for name in vars(frame) if name.startswith("SHAPE_")] == [] and not hasattr(frame, "sample")
    assert not hasattr(sample, "shaped")


def test_a_cuts_frame_says_no_counts_of_the_stretch_however_long_a_run_with_no_label_is(tmp_path):
    cut(tmp_path, "s1", 1, "a0000001")  # thirteen of the person's after the cut, and one label, on the last
    ids = ("a0000001",) + tuple(b(k) for k in range(1, 14))
    with at_home(tmp_path, ids, (WABE,), (("W1", b(13)),)):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert "by count" not in made and "Counted by rule" not in made and "longest runs" not in made
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000013`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000013]",
    ]
    # the store's line follows the packed part, and nothing between but the sentence of the weighed and unmarked, which
    # names five of the twelve with no label on them by their ids, and counts nothing
    assert made.split("\n\n")[-4] == frame.PACKED_HEAD
    assert made.split("\n\n")[-2] == (
        "The record weighs these, and no label rests on them: `b0000012`, `b0000011`, `b0000010`, `b0000009`, "
        "`b0000008`; `thread` gives each in its place."
    )
    assert made.split("\n\n")[-1].startswith("The store holds ")


# --- the events of a stretch ---------------------------------------------------------------------------------------


def test_events_hold_the_contracts_keys_and_labelled_counts_a_standing_line_that_is_not_carried(tmp_path):
    cut(tmp_path, "s1", 1, "a0000001")
    db = index(
        said(1, "a0000001"),  # before the cut: a carried label rests on it
        said(2, "b0000001"),  # a standing line rests on it, and no carried label
        said(3, "b0000002"),  # a carried work label rests on it, and the standing line too
        said(4, "b0000003"),  # no label: reached for, twice
        said(5, "b0000004", session="s2"),  # another session's
        labels=(("R1", "relation"), ("W1", "work"), ("W2", "work")),
        anchors=(("R1", "b0000001"), ("R1", "b0000002"), ("W1", "b0000002"), ("W2", "a0000001")),
    )
    pulls(tmp_path, "b0000003-u4", "b0000003")
    carried = [{"id": "W1", "anchors": ["b0000002"]}, {"id": "W2", "anchors": ["a0000001"]}]
    found = sample.events(tmp_path, db, "s1", carried, set())
    assert all(set(each) == CONTRACT for each in found)
    by = {each["id"]: each for each in found}
    assert list(by) == ["a0000001", "b0000001", "b0000002", "b0000003"]
    assert (by["a0000001"]["in_stretch"], by["a0000001"]["anchored"], by["a0000001"]["labelled"]) == (False, 1, 1)
    assert (by["b0000001"]["anchored"], by["b0000001"]["labelled"], by["b0000001"]["guard"]) == (0, 1, "standing")
    assert (by["b0000002"]["anchored"], by["b0000002"]["labelled"], by["b0000002"]["guard"]) == (1, 2, "")
    assert (by["b0000003"]["labelled"], by["b0000003"]["pulled"]) == (0, 2)
    # the sampler's events, handed what the home holds: the cut records, the pulls, and the sampler's own window
    assert found == from_store.events(db, "s1", carried, sample.pulled(tmp_path), {"a0000001"}, set(), 400)
    assert sample.events(tmp_path, db, "s1", carried, {"b0000003"})[-1]["guard"] == "flagged"
    # where no cut of the session is recorded, from the newest of the person's that the window fixed in the sampler
    # holds on
    many = index(*[said(k, f"d{k:07d}", session="s9") for k in range(1, core.SEEDS["window"] + 2)])
    assert [each["id"] for each in sample.events(tmp_path, many, "s9", [], set())][:1] == ["d0000002"]
    assert len(sample.events(tmp_path, many, "s9", [], set())) == core.SEEDS["window"] == 400
    # the settings are fixed in the sampler: a file of them in the home, as the sampler once read one, is not read
    store.within(tmp_path, "sample-settings").write_text("window 1\n", encoding="utf-8")
    assert sample.events(tmp_path, db, "s1", carried, set()) == found
    assert len(sample.events(tmp_path, many, "s9", [], set())) == 400


# --- a cut's frame, packed: each of the person's sentences, and what the session told of it ---------------------

OWN_WORDS = "## The person's own words, as they stand in the record"
THE_WORK = "## The work, newest first"
ROOM = 420  # what `frame._composed` keeps of a frame's size for its headings and its closing lines


def home_index(said_ids: tuple, labels: tuple, anchors: tuple) -> sqlite3.Connection:
    """A home's index made by hand in memory: the three tables of tests/sampler_schema.sql and an empty one of the
    lines beneath a stack; each of `said_ids` a message of the person's in session s1 holding the made-up word, each
    of `labels` (an id, a kind and a sentence) a carried label of the session's in that order, resting on `anchors`
    (a label and the id it rests on)."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA + "create table beneath(stack text, line text);")
    for seq, name in enumerate(said_ids, 1):
        db.execute(
            "insert into said (seq, uuid, id, session, voice, at, text, model) "
            "values (?, ?, ?, 's1', 'his', null, 'tove', '')",
            (seq, f"{name}-u{seq}", name),
        )
    for n, (name, kind, text) in enumerate(labels, 1):
        db.execute(
            "insert into label (n, id, kind, whose, text, page, parent, home, state, model) "
            "values (?, ?, ?, 'session', ?, '', '', '', 'carried', '')",
            (n, name, kind, text),
        )
    for label, name in anchors:
        db.execute("insert into anchor (label, said) values (?, ?)", (label, name))
    return db


@contextlib.contextmanager
def at_home(folder: Path, said_ids: tuple, labels: tuple, anchors: tuple):
    """The frame of `folder` made from a hand-made index. Two functions of the store are stood in for: `_open`
    gives the index (a new one at each call, as the frame closes the one it reads), and `status` gives what the
    empty home itself gives, taken before (the store's own reads tables the hand-made index does not hold)."""
    held = store.status(folder)
    with standing_in(store, "_open", lambda *args, **kwargs: home_index(said_ids, labels, anchors)):
        with standing_in(store, "status", lambda *args, **kwargs: held):
            yield


def section(made: str, head: str) -> list[str]:
    """The lines of a frame's part under this heading, up to the next part."""
    return made.split(head + "\n\n", 1)[1].split("\n\n", 1)[0].split("\n")


DOOR = ("N1", "next", "Find out whether the tove is gyred.")
WABE = ("W1", "work", "The wabe is mapped.")


def test_a_quoted_sentence_is_followed_by_the_line_at_the_door_and_then_the_work_label_resting_on_it(tmp_path):
    with at_home(tmp_path, (b(1),), (DOOR, WABE), (("N1", b(1)), ("W1", b(1)))):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)  # the same frame laid out as before
    own = section(before, THE_WORK)
    assert own == ["- W1 (session): The wabe is mapped. [b0000001]"]  # the work label's own line
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "     ↳ N1: the line at the door",
        "     ↳ " + own[0][len("- ") :],
    ]
    assert THE_WORK not in made  # the one work label is packed, and no other is left to list


def bare_keys(made: str) -> list[str]:
    """The lines of a frame that name a label by its key alone, beneath a sentence."""
    return re.findall(r"^\s*↳ \w+$", made, flags=re.M)


def test_a_work_label_resting_on_two_quoted_sentences_side_by_side_is_written_once_under_the_second(tmp_path):
    with at_home(tmp_path, (b(1), b(2)), (WABE,), (("W1", b(1)), ("W1", b(2)))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "- `b0000002`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000001, b0000002]",
    ]
    assert made.count("The wabe is mapped.") == 1 and bare_keys(made) == []


def test_a_work_label_resting_on_two_quoted_sentences_with_another_between_is_written_once_under_the_later(tmp_path):
    # W2, the newer, is chosen by first: its sentences are listed first, and W1's second sentence after them
    waits = ("W2", "work", "The borogove waits.")
    anchors = (("W1", b(1)), ("W1", b(3)), ("W2", b(1)), ("W2", b(2)))
    with at_home(tmp_path, (b(1), b(2), b(3)), (WABE, waits), anchors):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",  # both rest on it, and neither is written beneath it
        "- `b0000002`: tove",
        "     ↳ W2 (session): The borogove waits. [b0000001, b0000002]",
        "- `b0000003`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000001, b0000003]",
    ]
    assert made.count("The wabe is mapped.") == made.count("The borogove waits.") == 1 and bare_keys(made) == []
    assert THE_WORK not in made


def test_the_line_at_the_door_stays_beneath_every_sentence_it_rests_on_where_the_work_row_is_written_later(tmp_path):
    with at_home(tmp_path, (b(1), b(2)), (DOOR, WABE), (("N1", b(1)), ("W1", b(1)), ("W1", b(2)))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "     ↳ N1: the line at the door",
        "- `b0000002`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000001, b0000002]",
    ]
    anchors = (("N1", b(1)), ("N1", b(2)), ("W1", b(1)), ("W1", b(2)))
    with at_home(tmp_path, (b(1), b(2)), (DOOR, WABE), anchors):
        both = frame.compose(tmp_path, 9000, session="s1")
    assert section(both, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "     ↳ N1: the line at the door",
        "- `b0000002`: tove",
        "     ↳ N1: the line at the door",
        "     ↳ W1 (session): The wabe is mapped. [b0000001, b0000002]",
    ]
    assert bare_keys(made) == bare_keys(both) == []


def test_where_a_work_rows_last_sentence_does_not_fit_it_stands_beneath_the_last_that_does_or_with_the_work(tmp_path):
    # the line at the door rests on the first 28 sentences; W1 on the second and the last two, W2 on the last two
    ids = tuple(b(n) for n in range(1, 31))
    waits = ("W2", "work", "The borogove waits.")
    anchors = tuple(("N1", each) for each in ids[:28])
    anchors += (("W1", b(2)), ("W1", b(29)), ("W1", b(30)), ("W2", b(29)), ("W2", b(30)))
    w1 = "     ↳ W1 (session): The wabe is mapped. [b0000002, b0000029, b0000030]"
    w2 = "     ↳ W2 (session): The borogove waits. [b0000029, b0000030]"
    with at_home(tmp_path, ids, (DOOR, WABE, waits), anchors):
        packed = frame.compose(tmp_path, 9000, session="s1")
        assert frame.LEAST + 100 < len(packed) < frame.MOST
        less = frame.compose(tmp_path, len(packed) - 1, session="s1")
        least = frame.compose(tmp_path, len(less) - 1, session="s1")
    lines = section(packed, frame.PACKED_HEAD)
    assert lines[-3:] == ["- `b0000030`: tove", w2, w1] and lines[-4] == "- `b0000029`: tove"
    # the last sentence goes, and both rows stand beneath the last of theirs that is left
    assert len(less) <= len(packed) - 1 and less == packed.replace("\n- `b0000030`: tove", "")
    assert section(less, frame.PACKED_HEAD)[-3:] == ["- `b0000029`: tove", w2, w1]
    # the one before it goes too: W1 stands beneath the second sentence, the last of its own left, and W2, with none
    # of its own left, is listed with the work again; each is written once, and no bare key is left anywhere
    assert len(least) <= len(less) - 1 and frame.PACKED_HEAD in least
    kept = section(least, frame.PACKED_HEAD)
    assert "- `b0000029`: tove" not in kept and "- `b0000030`: tove" not in kept and "- `b0000027`: tove" in kept
    at = kept.index("- `b0000002`: tove")
    assert kept[at + 1 : at + 4] == ["     ↳ N1: the line at the door", w1, "- `b0000003`: tove"]
    assert section(least, THE_WORK) == ["- " + w2[len("     ↳ ") :]]
    for made in (packed, less, least):
        assert made.count("The wabe is mapped.") == made.count("The borogove waits.") == 1 and bare_keys(made) == []


def test_a_work_label_no_quoted_sentence_stands_beside_stays_under_the_work_and_a_packed_one_is_not_there_again(
    tmp_path,
):
    # W2 rests on an id the hand-made index holds no message under: no sentence of the person's is quoted for it
    waits = ("W2", "work", "The borogove waits.")
    with at_home(tmp_path, (b(1),), (WABE, waits), (("W1", b(1)), ("W2", "c0000009"))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000001]",
    ]
    assert section(made, THE_WORK) == ["- W2 (session): The borogove waits. [c0000009]"]
    assert made.index(frame.PACKED_HEAD) < made.index(THE_WORK)
    assert made.count("The wabe is mapped.") == 1 and made.count("The borogove waits.") == 1


def test_a_packed_frame_has_no_part_of_the_persons_own_words(tmp_path):
    with at_home(tmp_path, (b(1),), (DOOR, WABE), (("N1", b(1)), ("W1", b(1)))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert frame.PACKED_HEAD in made
    assert OWN_WORDS not in made
    assert made.count("- `b0000001`: tove") == 1  # the sentence is quoted once, packed


def test_with_no_session_named_or_for_a_session_started_new_the_frame_is_laid_out_as_before(tmp_path):
    with at_home(tmp_path, (b(1),), (DOOR, WABE), (("N1", b(1)), ("W1", b(1)))):
        packed = frame.compose(tmp_path, 9000, session="s1")
        unnamed = frame.compose(tmp_path, 9000)
        started = frame.compose(tmp_path, 9000, new=True, session="s1")
    assert frame.PACKED_HEAD in packed  # the same home packs, for the session that was cut
    for made in (unnamed, started):
        assert frame.PACKED_HEAD not in made and "↳" not in made
        assert section(made, THE_WORK) == ["- W1 (session): The wabe is mapped. [b0000001]"]
        assert section(made, OWN_WORDS) == ["- `b0000001`: tove"]
    assert unnamed != started  # the one is a cut's frame, the other a new session's


def test_the_labels_a_packed_frame_carries_are_counted_as_those_of_the_frame_laid_out_as_before(tmp_path):
    # a standing line, the line at the door and a work label on the sentence, and a work label no quoted sentence
    # stands beside: packed, W1 is written beneath the sentence and W2 with the work
    standing = ("R1", "relation", "The tove is the person's own.")
    waits = ("W2", "work", "The borogove waits.")
    anchors = (("R1", b(1)), ("N1", b(1)), ("W1", b(1)), ("W2", "c0000009"))
    with at_home(tmp_path, (b(1),), (standing, DOOR, WABE, waits), anchors):
        packed = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    assert "     ↳ W1 (session): The wabe is mapped. [b0000001]" in section(packed, frame.PACKED_HEAD)
    assert section(before, THE_WORK) == [
        "- W2 (session): The borogove waits. [c0000009]",
        "- W1 (session): The wabe is mapped. [b0000001]",
    ]
    assert frame.carried(packed) == frame.carried(before) == 3  # R1, W1 and W2, each once
    # a frame with none: no label at all, or the line at the door alone, beneath its sentence or laid out as before
    with at_home(tmp_path, (b(1),), (), ()):
        empty = frame.compose(tmp_path, 9000, session="s1")
    with at_home(tmp_path, (b(1),), (DOOR,), (("N1", b(1)),)):
        door_only = [frame.compose(tmp_path, 9000, session="s1"), frame.compose(tmp_path, 9000)]
    assert section(door_only[0], frame.PACKED_HEAD) == ["- `b0000001`: tove", "     ↳ N1: the line at the door"]
    assert "\n- N1 (session): " in door_only[1]
    assert [frame.carried(each) for each in (empty, *door_only)] == [0, 0, 0]


def many_at_home(folder: Path, k: int = 30):
    """A home whose line at the door and one work label both rest on k quoted sentences: packed, each sentence has
    the line at the door beneath it, and the last the work label too, so the packed frame is longer than the one laid
    out as before by far more than ROOM."""
    ids = tuple(b(n) for n in range(1, k + 1))
    return at_home(folder, ids, (DOOR, WABE), tuple((name, each) for name in ("N1", "W1") for each in ids))


def test_where_the_packed_frame_would_pass_its_size_the_last_sentences_go_until_it_fits_and_it_stays_packed(tmp_path):
    with many_at_home(tmp_path):
        packed = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
        # The size of the frame laid out as before, and what is left of it after ROOM: the same labels and words are
        # chosen at it, and the packed frame is longer than it by far more than ROOM.
        size = len(before) + ROOM
        assert frame.LEAST <= size <= frame.MOST and len(packed) > size
        assert frame.compose(tmp_path, size) == before
        at_size = frame.compose(tmp_path, size, session="s1")
        # held to its size as the frame laid out as before is: at its own length it is given whole, and one character
        # less, the last sentence goes with the lines beneath it
        assert frame.compose(tmp_path, len(packed), session="s1") == packed
        less = frame.compose(tmp_path, len(packed) - 1, session="s1")
    every = [f"- `{b(n)}`: tove" for n in range(1, 31)]
    assert quotes_in(packed) == every and frame.PACKED_HEAD in at_size and len(at_size) <= size
    # the work label, written once beneath the last of its sentences, stands beneath the last that is left
    assert section(packed, frame.PACKED_HEAD)[-1].startswith("     ↳ W1 (session): The wabe is mapped. [")
    assert less == packed.replace(f"\n- `{b(30)}`: tove\n     ↳ N1: the line at the door", "")
    kept = quotes_in(at_size)  # as many go as must, the last first, and every line of what is left is as it was
    assert 0 < len(kept) < 30 and kept == every[: len(kept)]
    gone = "".join(f"\n- `{b(n)}`: tove\n     ↳ N1: the line at the door" for n in range(len(kept) + 1, 31))
    assert at_size == packed.replace(gone, "")


def test_a_packed_frame_is_never_longer_than_its_size(tmp_path):
    laid = set()
    with many_at_home(tmp_path):
        for size in range(frame.LEAST, frame.MOST + 1, 50):
            made = frame.compose(tmp_path, size, session="s1")
            assert len(made) <= size, size
            assert (frame.PACKED_HEAD in made) == bool(quotes_in(made)), size
            laid.add(frame.PACKED_HEAD in made)
    assert laid == {True, False}  # packed wherever a sentence fits, laid out as before where none does


def full_at_home(folder: Path):
    """A home whose contents fill a frame's room, as a home long worked in does: eight standing lines of about 600
    characters, more than their share holds; eight work rows of about 900, each resting on one of eight quoted
    sentences; and, written last, a line at the door of about 2,700 characters resting on all eight. Laid out as
    before at the home's size, the frame comes within ROOM of it, and an older work row tops up the room."""
    ids = tuple(b(n) for n in range(1, 9))
    labels = tuple((f"R{n}", "relation", ("The tove is the person's own. " * 20).strip()) for n in range(1, 9))
    labels += tuple((f"W{n}", "work", ("The wabe is mapped. " * 45).strip()) for n in range(1, 9))
    labels += (("N1", "next", ("Find out whether the tove is gyred. " * 75).strip()),)
    anchors = tuple((f"R{n}", b(1)) for n in range(1, 9)) + tuple((f"W{n}", ids[n - 1]) for n in range(1, 9))
    return at_home(folder, ids, labels, anchors + tuple(("N1", each) for each in ids))


def quotes_in(made: str) -> list[str]:
    """The sentences of the person's a frame quotes, packed or laid out as before, by their lines."""
    return re.findall(r"^- `b\d{7}`: .*$", made, flags=re.M)


def work_in(made: str) -> set[str]:
    """The keys of the work rows a frame writes out, packed or laid out as before."""
    return set(re.findall(r"(W\d+) \(session\): ", made))


def test_in_a_home_that_fills_the_room_a_cuts_frame_is_packed_within_its_size_and_the_top_up_goes_first(tmp_path):
    with full_at_home(tmp_path):
        made = frame.compose(tmp_path, frame.SIZE, session="s1")
        before = frame.compose(tmp_path, frame.SIZE)
    assert frame.SIZE - ROOM < len(before) <= frame.SIZE  # laid out as before, within ROOM of its size
    assert frame.PACKED_HEAD in made and OWN_WORDS not in made and len(made) <= frame.SIZE
    lines = section(made, frame.PACKED_HEAD)
    assert [each for each in lines if each.startswith("- `")] == quotes_in(made) == section(before, OWN_WORDS)
    for at, each in enumerate(lines):  # each sentence, and beneath it the line at the door and the work resting on it
        if each.startswith("- `"):
            assert lines[at + 1] == "     ↳ N1: the line at the door", each
            assert at + 2 == len(lines) or lines[at + 2].startswith(("     ↳ W", "- `")), each
    # to make the room, the older work row the top-up added goes, and every sentence stays
    carried = sorted(work_in(before), key=lambda key: int(key[1:]))
    assert len(carried) >= 2 and work_in(made) == set(carried[1:])


def test_over_every_size_a_cuts_frame_of_a_full_home_is_within_it_and_packed_wherever_a_sentence_is_quoted(tmp_path):
    seen = set()
    with full_at_home(tmp_path):
        for size in range(frame.LEAST, frame.MOST + 1, 25):
            made = frame.compose(tmp_path, size, session="s1")
            assert len(made) <= frame.bounded(size), size
            assert (frame.PACKED_HEAD in made) == bool(quotes_in(made)), size
            if not quotes_in(made):  # the true fall-back: no sentence fits, and the frame is laid out as before
                assert made == frame.compose(tmp_path, size) and OWN_WORDS not in made, size
            seen.add(bool(quotes_in(made)))
    assert seen == {True, False}  # packed wherever a sentence fits; at the least sizes none does


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
