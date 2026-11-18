"""Events from a hand-made index: the three tables of tests/sampler_schema.sql, rows inserted directly, made-up
ids, times and a few made-up words. Runs with or without pytest."""

from __future__ import annotations

import datetime
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing.sampler import core, from_store

SCHEMA = (Path(__file__).resolve().parent / "sampler_schema.sql").read_text(encoding="utf-8")
START = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
# The contract: every key an event holds, and no other.
CONTRACT = {"id", "in_stretch", "distance", "anchored", "labelled", "pulled", "guard"}  # `length` is the caller's


def at(seconds: int) -> str:
    """A made-up time, so many seconds after the start, as an ISO 8601 text with a closing `Z`."""
    return (START + datetime.timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def said(seq: int, name: str, voice: str = "his", session: str = "s1", when: object = None, text: str = "tove"):
    return (seq, name, voice, session, when, text)


def index(*rows, labels: tuple = (), anchors: tuple = ()) -> sqlite3.Connection:
    """An index in memory with the three tables, and these rows of `said`, `label` and `anchor` in them."""
    db = sqlite3.connect(":memory:")
    db.executescript(SCHEMA)
    for seq, name, voice, session, when, text in rows:
        db.execute(
            "insert into said (seq, uuid, id, session, voice, at, text, model) values (?, ?, ?, ?, ?, ?, ?, '')",
            (seq, f"u{seq}", name, session, voice, when, text),
        )
    for name, kind in labels:
        db.execute("insert into label (id, kind) values (?, ?)", (name, kind))
    for label, name in anchors:
        db.execute("insert into anchor (label, said) values (?, ?)", (label, name))
    return db


def events(db, session="s1", carried=(), pulled=None, cut_ids=(), flagged=(), window=400) -> list[dict]:
    return from_store.events(db, session, list(carried), pulled or {}, set(cut_ids), set(flagged), window)


def ids(found: list[dict]) -> list[str]:
    return [each["id"] for each in found]


def one(name: str, in_stretch=True, distance=0, anchored=0, pulled=0, guard="", labelled=0):
    """An event as the adapter makes it: with no length, which the caller sets."""
    return {
        "id": name,
        "in_stretch": in_stretch,
        "distance": distance,
        "anchored": anchored,
        "labelled": labelled,
        "pulled": pulled,
        "guard": guard,
    }


# --- the stretch ------------------------------------------------------------------------------------------------


def test_the_stretch_after_the_newest_id_a_cut_names():
    db = index(
        said(1, "p1", when=at(0)),
        said(2, "q1", "session", when=at(10)),
        said(3, "p2", when=at(20)),
        said(4, "q2", "session", when=at(30)),  # the newest a cut names
        said(5, "p3", when=at(2030), text="brillig wabe"),
        said(6, "q3", "session", when=at(2040)),
        said(7, "p4", when=at(2100), text="x" * 130),
    )
    found = events(db, cut_ids={"p1", "q2", "zz"}, pulled={"p4": 2, "p1": 5})
    assert found == [one("p3", distance=1), one("p4", distance=0, pulled=2)]
    after_p1 = events(db, cut_ids={"p1"})
    assert ids(after_p1) == ["p2", "p3", "p4"]
    assert [each["distance"] for each in after_p1] == [2, 1, 0]
    assert events(db, cut_ids={"p4"}) == []


def test_the_window_where_no_cut_names_one():
    db = index(
        said(1, "q0", "session"),
        said(2, "p1"),
        said(3, "q1", "session"),
        said(4, "p2"),
        said(5, "p3"),
    )
    assert events(db, window=2) == [one("p2", distance=1), one("p3")]
    assert ids(events(db, window=3)) == ["p1", "p2", "p3"]
    assert ids(events(db, window=400)) == ["p1", "p2", "p3"]  # from the person's first, not the session's
    assert ids(events(db, window=2, cut_ids={"gone"})) == ["p2", "p3"]  # a cut names none held
    assert events(db, window=0) == []
    assert events(index(said(1, "q0", "session"), said(2, "q1", "session"))) == []
    assert events(index()) == []


def test_two_sessions_held_apart():
    db = index(
        said(1, "a1", session="s1", when=at(0)),
        said(2, "b1", session="s2", when=at(5)),
        said(3, "a2", "session", session="s1", when=at(10)),  # the newest a cut of s1 names
        said(4, "b2", session="s2", when=at(15)),
        said(5, "a3", session="s1", when=at(100)),
        said(6, "b3", session="s2", when=at(130)),
    )
    # a3 alone is the stretch of s1: s2's messages are none of it
    assert events(db, "s1", cut_ids={"a2"}) == [one("a3")]
    # s2 holds no message a2, so its stretch is its window
    assert events(db, "s2", cut_ids={"a2"}) == [one("b1", distance=2), one("b2", distance=1), one("b3")]
    # with no session named, every session's messages are the stretch, and no cut is read
    every = events(db, "", cut_ids={"a2"})
    assert ids(every) == ["a1", "b1", "b2", "a3", "b3"]
    assert [each["distance"] for each in every] == [4, 3, 2, 1, 0]
    assert events(db, "s3") == []


def test_a_paste_is_passed_over():
    db = index(
        said(1, "x1", "pasted", when=at(0)),
        said(2, "p1", when=at(4000)),
        said(3, "x2", "pasted", when=at(4010)),
        said(4, "p2", when=at(4100)),
        said(5, "p2", "pasted"),  # a paste sharing an id makes no twin
    )
    assert events(db, cut_ids={"x2"}) == [one("p1", distance=1), one("p2")]


# --- what an event holds ------------------------------------------------------------------------------------------


def test_no_event_has_a_key_that_is_not_in_the_contract():
    db = index(
        said(1, "o1", when=at(0), text="mome rath"),
        said(2, "c1", "session", when=at(5)),
        said(3, "i1", when=at(10), text="outgrabe"),
        said(4, "i2", when="not a time"),
        said(5, "i2", session="s2"),
        labels=(("L1", "relation"),),
        anchors=(("L1", "i1"),),
    )
    found = events(db, carried=[{"id": "W1", "anchors": ["o1"]}], pulled={"i1": 1}, cut_ids={"c1"}, flagged={"i1"})
    assert ids(found) == ["o1", "i1", "i2"]
    for each in found:
        assert set(each) == CONTRACT, each["id"]
        assert "length" not in each
    assert [each["labelled"] for each in found] == [0, 1, 0]


def test_the_time_and_the_words_of_a_message_are_read_nowhere():
    def made(times: list, words: list) -> sqlite3.Connection:
        return index(
            said(1, "o1", when=times[0], text=words[0]),
            said(2, "c1", "session", when=times[1], text=words[1]),
            said(3, "i1", when=times[2], text=words[2]),
            said(4, "i2", when=times[3], text=words[3]),
        )

    # the same messages, once with times close and words short, once far apart, long or none
    near = made([at(0), at(1), at(2), at(3)], ["a", "b", "c", "d"])
    far = made([None, at(90000), "not a time", at(5)], ["brillig " * 40, "", "slithy", "x" * 5000])
    carried = [{"id": "W1", "anchors": ["o1", "i2"]}]
    want = [one("o1", in_stretch=False, anchored=1), one("i1", distance=1), one("i2", anchored=1)]
    assert events(near, carried=carried, cut_ids={"c1"}) == events(far, carried=carried, cut_ids={"c1"}) == want
    assert events(near, window=400) == events(far, window=400)


# --- the guards ---------------------------------------------------------------------------------------------------


def test_a_twin_a_flagged_and_a_standing_only_message_guarded():
    db = index(
        said(1, "g1"),
        said(2, "g1", session="s2"),  # g1's twin, in another session
        said(3, "g2"),
        said(4, "g3"),
        said(5, "g4"),
        said(6, "g5"),
        said(7, "g6"),
        said(8, "g7", "session"),
        said(9, "g7"),  # a twin of the session's voice
        labels=(("L1", "relation"), ("W9", "work")),
        anchors=(("L1", "g3"), ("L1", "g4"), ("W9", "g5")),
    )
    carried = [{"id": "W1", "anchors": ["g4"]}]
    found = {each["id"]: each["guard"] for each in events(db, carried=carried, flagged={"g2", "g1"})}
    assert found == {
        "g1": "twin",  # a twin is a twin before it is flagged
        "g2": "flagged",
        "g3": "standing",  # a standing line rests on it and no carried label does
        "g4": "",  # a carried label rests on it as well
        "g5": "",  # a work label that is not carried is no standing line
        "g6": "",
        "g7": "twin",
    }


# --- the messages a carried label rests on ----------------------------------------------------------------------------


def test_a_message_before_the_last_cut_with_a_carried_label_is_one_event():
    db = index(
        said(1, "o1", when=at(0), text="mome rath"),
        said(2, "o2", when=at(10)),
        said(3, "c1", "session", when=at(20)),  # the newest a cut names
        said(4, "i1", when=at(4000)),
        said(5, "i2", when=at(4060)),
    )
    carried = [{"id": "W1", "anchors": ["o1", "o1", "i1"]}, {"id": "W2", "anchors": ["o1"]}]
    found = events(db, carried=carried, pulled={"o1": 2, "i1": 1}, cut_ids={"c1"})
    assert found == [
        one("o1", in_stretch=False, anchored=2, pulled=2),
        one("i1", distance=1, anchored=1, pulled=1),
        one("i2"),
    ]
    for each in found:
        each["length"] = 10  # the caller's to set, as the plugin does from the entry it quotes
    picked = core.pick(found, core.SEEDS, 1000)
    o1 = next(each for each in picked["ranked"] if each["id"] == "o1")
    assert o1["features"] == {"anchored": 2, "pulled": 2, "tail": 0}
    assert picked["carried"] == ["i2", "i1", "o1"]


def test_a_message_in_the_stretch_with_a_carried_label_is_one_event():
    db = index(said(1, "c1", "session"), said(2, "i1"), said(3, "i2"))
    carried = [{"id": "W1", "anchors": ["i1"]}, {"id": "W2", "anchors": ["i1", "i2"]}]
    found = events(db, carried=carried, cut_ids={"c1"})
    assert found == [one("i1", distance=1, anchored=2), one("i2", anchored=1)]


def test_a_carried_label_on_a_message_out_of_the_session():
    db = index(
        said(1, "x1", session="s2", when=at(0)),
        said(2, "c1", "session", when=at(5)),
        said(3, "i1", when=at(10)),
        said(4, "x2", session="s2", when=at(20)),
        said(5, "y1", "session", session="s2"),
        said(6, "y2", "pasted"),
    )
    carried = [{"id": "W1", "anchors": ["x2", "x1", "y1", "y2", "gone"]}]
    found = events(db, carried=carried, cut_ids={"c1"})
    # x1 and x2 are the person's, in another session: outside the stretch, each where the index keeps it;
    # y1 is the session's own and y2 a paste, and "gone" is held nowhere: no event
    assert found == [
        one("x1", in_stretch=False, anchored=1),
        one("i1"),
        one("x2", in_stretch=False, anchored=1),
    ]


def test_a_twin_outside_the_stretch_is_two_messages_each_guarded():
    db = index(said(1, "t1"), said(2, "t1", session="s2"), said(3, "c1", "session"), said(4, "t1"))
    found = events(db, carried=[{"id": "W1", "anchors": ["t1"]}], cut_ids={"c1"})
    assert found == [
        one("t1", in_stretch=False, anchored=1, guard="twin"),
        one("t1", in_stretch=False, anchored=1, guard="twin"),
        one("t1", anchored=1, guard="twin"),
    ]
    for each in found:
        each["length"] = 10  # the caller's to set, as the plugin does from the entry it quotes
    assert core.pick(found, core.SEEDS, 1000)["carried"] == []
    assert core.pick(found, core.SEEDS, 1000, ["t1"])["carried"] == []  # nor by rule


# --- the labels of any kind ---------------------------------------------------------------------------------------


def test_labelled_counts_the_labels_of_any_kind_carried_or_not():
    rows = (said(1, "o1"), said(2, "c1", "session"), said(3, "i1"), said(4, "i2"), said(5, "i3"))
    db = index(
        *rows,
        labels=(("W1", "work"), ("L1", "relation"), ("N1", "next"), ("W2", "work")),
        anchors=(("W1", "i1"), ("L1", "i1"), ("N1", "i2"), ("W2", "i2"), ("L1", "i2"), ("W1", "o1"), ("L1", "o1")),
    )
    carried = [{"id": "W1", "anchors": ["i1", "o1"]}]
    found = events(db, carried=carried, cut_ids={"c1"})
    assert found == [
        # two labels rest on each, one of them a standing line and not carried: `anchored` counts the carried
        # one alone, and no guard is on it, since a carried label rests on it too
        one("o1", in_stretch=False, anchored=1, labelled=2),
        one("i1", distance=2, anchored=1, labelled=2),
        # three labels and none of them carried: `anchored` nought, and the standing line guards it as before
        one("i2", distance=1, labelled=3, guard="standing"),
        one("i3"),  # no label rests on it
    ]
    # `anchored` and the guards are as they were where the index holds no label at all
    bare = events(index(*rows), carried=carried, cut_ids={"c1"})
    assert [{**each, "labelled": 0} for each in found if each["id"] != "i2"] == [
        each for each in bare if each["id"] != "i2"
    ]


def test_a_label_naming_a_message_twice_counts_once():
    db = index(
        said(1, "c1", "session"),
        said(2, "i1"),
        said(3, "i2"),
        labels=(("W1", "work"), ("N1", "next")),
        anchors=(("W1", "i1"), ("W1", "i1"), ("N1", "i2"), ("W1", "i2"), ("N1", "i2")),
    )
    assert events(db, cut_ids={"c1"}) == [one("i1", distance=1, labelled=1), one("i2", labelled=2)]


def test_labelled_is_read_in_one_query_for_every_message():
    def statements(count: int) -> int:
        """How many statements the adapter runs over a stretch of `count` messages, a label on each."""
        rows = [said(1, "c1", "session")] + [said(n + 1, f"i{n}") for n in range(1, count + 1)]
        db = index(*rows, anchors=tuple((f"W{n}", f"i{n}") for n in range(1, count + 1)))
        run: list[str] = []
        db.set_trace_callback(run.append)
        found = events(db, cut_ids={"c1"})
        db.set_trace_callback(None)
        assert [each["labelled"] for each in found] == [1] * count
        return len(run)

    assert statements(1) == statements(2) == statements(40)


def test_a_connections_own_rows_are_left_alone():
    def made(rows_as):
        db = index(said(1, "c1", "session"), said(2, "p1", text="brillig"), said(3, "p2"))
        db.row_factory = rows_as
        return db

    def as_dict(cursor, row):
        return {column[0]: value for column, value in zip(cursor.description, row)}

    want = [one("p1", distance=1), one("p2")]
    for rows_as in (None, sqlite3.Row, as_dict):
        db = made(rows_as)
        assert events(db, carried=[{"id": "W1", "anchors": ["p1"]}], cut_ids={"c1"})[0]["anchored"] == 1
        assert events(db, cut_ids={"c1"}) == want
        assert db.row_factory is rows_as


def _run() -> None:
    tests = [test for name, test in list(globals().items()) if name.startswith("test_") and callable(test)]
    for test in tests:
        test()
    print(f"{Path(__file__).name}: {len(tests)} tests passed")


if __name__ == "__main__":
    _run()
