"""What the session declined: a label of the kind refused (X1, X2, ...), the judgments of it that make a family, the
state of each, how the door lists and counts them, how a cut's frame carries them, packed or laid out as before,
and the server's `crossing`. Every index the door reads is made by hand in memory (the three tables of
tests/sampler_schema.sql, rows inserted directly, with tables of the lines beneath a label and of unread lines),
from label pages written through `store.mark` or by hand, with made-up ids and a made-up word; every home is a
temporary folder."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_sample_join import DOOR, SCHEMA, WABE, at_home, b, section, standing_in  # noqa: E402
from test_store import sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, layer, record, serve, store  # noqa: E402

DAY = "2026-11-12"
THE_WORK = "## The work, newest first"
OWN_WORDS = "## The person's own words, as they stand in the record"
BRANCH = "The branch is not deleted: it holds work not merged."
AGAIN = "Still not deleted: the work in it is merged, and the person asks for a tag first."
LAST = "Deleted after all is not done: the tag is not made yet."
# The three texts a session is told of refusals and of `crossing`, word for word.
MARK_KIND = (
    "relation (the two of you), work (default), refused (rests on what was asked; its sentence is your reason) or "
    "silenced (rests on a refusal that stands no longer; its sentence says why)."
)
CROSSING = "The frame the next session would get if the cut came now. Read-only."
TOLD = (
    "Something you declined can be marked too, as a label of the kind refused that rests on what was asked: it "
    "crosses with the ask and your reason. The session after you may judge it again, with another refused label "
    "that rests on its key. Either rests also on the message where its reason was said. A label of the kind "
    "silenced, resting on a refusal's key and on such a message, puts the refusal to rest: it crosses no more and "
    "stays in the record."
)
LABELS_KIND = (
    "Only that kind: relation (standing, about the two of you), work, next (lines left at the door), or refused."
)
# A judgment and a silencing that name no message are refused with this, the move named first.
NO_MESSAGE = "{} of a refusal rests on the message where its reason was said: name that message too."
HANDLE = "crossing: the frame the next session would be given if the cut came now"


@contextlib.contextmanager
def setting(**values: str):
    """Settings of the environment, each put back as it was however the test ends."""
    was = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in was.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


# --- a home's index made by hand from its pages ---------------------------------------------------------------------


def built(folder: Path, said_ids: tuple) -> sqlite3.Connection:
    """An index in memory made by hand: each of `said_ids` a message of the person's holding the made-up word, in
    session s1 or in the session given beside it (`id@session`), or, with a model too (`id@session@model`), a
    message of that session's own voice made with that model, the oldest first; and every label the home's pages
    hold that is not struck, in the state and beneath the label the store's own rule finds (store._stood), with its
    anchors and the lines its row names."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(
        SCHEMA + "create table beneath(stack text, line text, digest text);\ncreate table unread(lines integer);\n"
    )
    for seq, given in enumerate(said_ids, 1):
        name, session, model = (given.split("@") + ["", ""])[:3]  # with a model, a message of the session's voice
        db.execute(
            "insert into said (seq, uuid, id, session, voice, at, text, model) values (?, ?, ?, ?, ?, null, 'tove', ?)",
            (seq, f"{name}-u{seq}", name, session or "s1", "session" if model else "his", model),
        )
    gone = store.struck(folder)
    kept = [label for label in store.labels(folder) if label["id"] not in gone]
    parent, state = store._stood(kept, {given.partition("@")[0] for given in said_ids})
    for n, label in enumerate(kept, 1):
        db.execute(
            "insert into label values (?,?,?,?,?,?,?,?,?,?)",
            (
                n,
                label["id"],
                label["kind"],
                label["whose"],
                label["text"],
                label["page"],
                parent.get(label["id"]),
                folder.name,
                state[label["id"]],
                "",
            ),
        )
        db.executemany(
            "insert into anchor (label, said) values (?,?)", [(label["id"], each) for each in label["anchors"]]
        )
        db.executemany("insert into beneath values (?,?,?)", [(label["id"], k, was) for k, was in label["beneath"]])
    return db


@contextlib.contextmanager
def kept_home(folder: Path, *said_ids: str):
    """The store reads the home's pages through an index made by hand (see `built`), a new one at each read."""
    with standing_in(store, "_open", lambda *args, **kwargs: built(folder, said_ids)):
        yield


def refuse(folder: Path, sentence: str, *anchors: str, whose: str = "session") -> dict:
    return store.mark(folder, "refused", whose, sentence, list(anchors), day=DAY)


def silence(folder: Path, sentence: str, *anchors: str, whose: str = "session") -> dict:
    return store.mark(folder, "silenced", whose, sentence, list(anchors), day=DAY)


def states(folder: Path) -> dict:
    db = store._open(folder)
    try:
        return {
            r["id"]: (r["state"], r["parent"]) for r in db.execute("select id, state, parent from label order by n")
        }
    finally:
        db.close()


# --- marking a refusal, and judging it again -------------------------------------------------------------------------


def test_a_refusal_is_marked_as_X1_and_listed_by_its_kind_and_counted_by_look_and_status(tmp_path):
    with kept_home(tmp_path, b(1)):
        out = refuse(tmp_path, BRANCH, b(1))
        assert (out["written"], out["id"], out["beneath"], out["anchors"]) == (True, "X1", [], [b(1)])
        page = (tmp_path / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
        assert f"| X1 | {BRANCH} | session | `{b(1)}` |\n" in page
        assert [(each["id"], each["kind"]) for each in store.labels(tmp_path)] == [("X1", "refused")]
        assert [row["id"] for row in store.listed(tmp_path, "refused")["labels"]] == ["X1"]
        assert store.listed(tmp_path, "work")["labels"] == []
        looked = store.look(tmp_path)
        assert (looked["refusals"], looked["labels"], looked["work"]) == ({"standing": ["X1"], "silenced": []}, 1, [])
        assert "; 1 refusal standing (X1)." in door.show_look(looked, bare=True)
        assert store.status(tmp_path)["labels"] == 1
        # whose it is: the session's, where nothing is given and where the person is named, a refusal being its own
        his = refuse(tmp_path, "Not pushed: the person said to wait.", b(1), whose="his")
        assert his["id"] == "X2" and store.listed(tmp_path, ids=("x2",))["labels"][0]["whose"] == "session"
        assert store.look(tmp_path)["refusals"]["standing"] == ["X1", "X2"] and store.status(tmp_path)["labels"] == 2
    # a look with no refusal says nothing of them
    assert "refusal" not in door.show_look({**looked, "refusals": {"standing": [], "silenced": []}}, bare=True)


def test_a_judgment_by_the_first_refusals_key_and_one_by_a_later_judgments_key_are_one_family(tmp_path):
    with kept_home(tmp_path, b(1), b(2), b(3)):
        assert refuse(tmp_path, BRANCH, b(1))["id"] == "X1"
        second = refuse(tmp_path, AGAIN, "X1", b(2))
        third = refuse(tmp_path, LAST, "`x2`", b(3))  # named by the later judgment's key
        assert (second["id"], second["beneath"], third["id"], third["beneath"]) == ("X2", ["X1"], "X3", ["X1"])
        rows = {each["id"]: each for each in store.labels(tmp_path)}
        x1 = store.digest(BRANCH)
        assert rows["X2"]["beneath"] == rows["X3"]["beneath"] == [("X1", x1)]  # never deeper: each hangs from X1
        page = (tmp_path / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
        assert f"| X3 | {LAST} | session | `X1@{x1}`, `{b(3)}` |\n" in page
        assert store.families(list(rows.values())) == {"X1": "X1", "X2": "X1", "X3": "X1"}
        # asked for by any of its keys, a refusal is given with its family: the first, then each judgment in turn
        for key in ("X1", "X2", "X3"):
            given = store.listed(tmp_path, ids=(key,))["labels"]
            assert [(each["id"], each["depth"]) for each in given] == [("X1", 0), ("X2", 1), ("X3", 1)], key
        assert [each["id"] for each in store.listed(tmp_path, ids=("X1", "X3"))["labels"]] == ["X1", "X2", "X3"]
        shown = door.show_labels(store.listed(tmp_path, ids=("X2",)), True, True)
        assert shown.split("\n") == [
            f"- X1 (refused, session, cooled beneath X3): {BRANCH} [{b(1)}]",
            f"  - X2 (refused, session, cooled beneath X3): {AGAIN} [X1, {b(2)}]",
            f"  - X3 (refused, session): {LAST} [X1, {b(3)}]",
        ]


def test_a_judgment_that_names_two_families_or_another_kind_is_refused_and_nothing_is_written(tmp_path):
    with kept_home(tmp_path, b(1), b(2), b(3)):
        refuse(tmp_path, BRANCH, b(1))
        refuse(tmp_path, "The tag is not pushed.", b(2))
        refuse(tmp_path, AGAIN, "X1", b(3))  # X3, of X1's family
        store.mark(tmp_path, "work", "session", "The wabe is mapped.", [b(3)], day=DAY)  # W1
        page = tmp_path / "labels" / f"{DAY}.md"
        written = page.read_text(encoding="utf-8")
        assert refuse(tmp_path, LAST, "X3", "X2", b(3)) == {
            "written": False,
            "why": "X1 and X2 are two refusals, and a judgment judges one alone",
        }
        assert refuse(tmp_path, LAST, "W1", b(3)) == {
            "written": False,
            "why": "a refusal rests on messages and on refusals alone, and this names a label of another kind: W1",
        }
        assert store.mark(tmp_path, "work", "session", "Over a refusal.", ["X1"], day=DAY) == {
            "written": False,
            "why": "a stack holds labels of its own kind alone, and of another kind here: X1",
        }
        assert refuse(tmp_path, LAST, "X9", b(3))["why"] == "no such label: X9"
        assert page.read_text(encoding="utf-8") == written
        # one family named twice is one family
        assert refuse(tmp_path, LAST, "X1", "X3", b(3))["beneath"] == ["X1"]


def test_of_a_family_the_newest_is_carried_and_the_others_cooled_beneath_it(tmp_path):
    with kept_home(tmp_path, b(1), b(2), b(3), b(4)):
        refuse(tmp_path, BRANCH, b(1))
        refuse(tmp_path, AGAIN, "X1", b(2))
        refuse(tmp_path, "The tag is not pushed.", b(4))  # X3, a family of its own
        refuse(tmp_path, LAST, "X2", b(3))  # X4, of X1's family
        assert states(tmp_path) == {
            "X1": ("cooled", "X4"),
            "X2": ("cooled", "X4"),
            "X3": ("carried", None),
            "X4": ("carried", None),
        }
        assert store.status(tmp_path)["states"]["cooled"] == 2


def test_a_judgment_that_names_no_older_refusal_or_two_families_is_misaligned_and_one_in_trouble_does_not_stand():
    def label(key: str, anchors: tuple = (), beneath: tuple = (), kind: str = "refused") -> dict:
        return {"id": key, "kind": kind, "text": key, "anchors": list(anchors), "beneath": list(beneath)}

    kept = [
        label("X1", (b(1),)),
        label("X2", (b(2),), (("X1", "000000"),)),  # a digest that is no longer the sentence's: judged all the same
        label("X3", (b(9),), (("X1", "000000"),)),  # rests on what the archive does not hold: unresolved
        label("X4", (b(3),)),
        label("X5", (b(3),), (("X1", "000000"), ("X4", "000000"))),  # of two families
        label("X6", (b(3),), (("X9", "000000"),)),  # names no refusal there is
        label("X7", (b(3),), (("X8", "000000"),)),  # names a newer one
        label("X8", (b(3),)),
        label("R1", (b(1),), kind="relation"),
        label("R2", (), (("X4", store.digest("X4")),), kind="relation"),  # an R stack over a refusal: none
    ]
    parent, state = store._stood(kept, {b(1), b(2), b(3)})
    assert state == {
        "X1": "cooled",
        "X2": "carried",  # the newest sound one stands, though X3 is newer
        "X3": "unresolved",
        "X4": "carried",
        "X5": "misaligned",
        "X6": "misaligned",
        "X7": "misaligned",
        "X8": "carried",
        "R1": "carried",
        "R2": "misaligned",
    }
    assert parent == {"X1": "X2"}  # and no refusal stands beneath an R stack, nor an R line beneath a refusal
    assert store.families(kept) == {
        "X1": "X1",
        "X2": "X1",
        "X3": "X1",
        "X4": "X4",
        "X5": "X5",  # of two families: the first of its own
        "X6": "X6",
        "X7": "X7",
        "X8": "X8",
    }


def test_stacks_of_the_standing_lines_and_the_work_are_as_they_were_beside_refusals(tmp_path):
    with kept_home(tmp_path, b(1), b(2)):
        for key in ("R", "W"):
            kind = "relation" if key == "R" else "work"
            store.mark(tmp_path, kind, "session", f"{kind} one.", [b(1)], day=DAY)
            store.mark(tmp_path, kind, "session", f"{kind} two.", [b(2)], day=DAY)
        refuse(tmp_path, BRANCH, b(1))
        refuse(tmp_path, AGAIN, "X1", b(2))
        stack = store.mark(tmp_path, "relation", "session", "Both, as one.", ["R1", "R2"], day=DAY)
        work = store.mark(tmp_path, "work", "session", "Both works, as one.", ["W1", "W2"], day=DAY)
        assert (stack["id"], stack["beneath"], work["id"], work["beneath"]) == ("R3", ["R1", "R2"], "W3", ["W1", "W2"])
        found = states(tmp_path)
        assert found["R1"] == found["R2"] == ("cooled", "R3") and found["W1"] == found["W2"] == ("cooled", "W3")
        assert found["X1"] == ("cooled", "X2") and found["X2"] == ("carried", None)
        assert store.mark(tmp_path, "work", "session", "Again.", ["W1"], day=DAY)["why"] == (
            "W1 already stands beneath W3, and a line stands beneath one stack alone"
        )


# --- the frame ---------------------------------------------------------------------------------------------------


def frame_index(said: tuple, labels: tuple, anchors: tuple, beneath: tuple) -> sqlite3.Connection:
    """A home's index made by hand in memory for the frame: each of `said` (an id, a voice and words) a message of
    session s1, each with a whole id of its own; each of `labels` (an id, a kind, a sentence, a state, the label it is
    cooled beneath and its model) a label of the session's in that order, resting on `anchors` (a label and the id it
    rests on) and naming `beneath` (a label and the key its row names)."""
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA + "create table beneath(stack text, line text);")
    for seq, (name, voice, text) in enumerate(said, 1):
        db.execute(
            "insert into said (seq, uuid, id, session, voice, at, text, model) values (?, ?, ?, 's1', ?, null, ?, '')",
            (seq, f"{name}-u{seq}", name, voice, text),
        )
    full = [tuple(label) + ("carried", None, "")[len(label) - 3 :] for label in labels]  # (id, kind, sentence) too
    for n, (name, kind, text, state, parent, model) in enumerate(full, 1):
        db.execute(
            "insert into label (n, id, kind, whose, text, page, parent, home, state, model) "
            "values (?, ?, ?, 'session', ?, '', ?, '', ?, ?)",
            (n, name, kind, text, parent, state, model),
        )
    db.executemany("insert into anchor (label, said) values (?, ?)", anchors)
    db.executemany("insert into beneath (stack, line) values (?, ?)", beneath)
    return db


def his(*names: str, text: str = "tove") -> tuple:
    return tuple((name, "his", text) for name in names)


def x(key: str, text: str, state: str = "carried", parent: str | None = None, model: str = "") -> tuple:
    return (key, "refused", text, state, parent, model)


def sx(key: str, text: str, state: str = "carried", parent: str | None = None) -> tuple:
    return (key, "silenced", text, state, parent, "")


def w(key: str, text: str) -> tuple:
    return (key, "work", text, "carried", None, "")


@contextlib.contextmanager
def framed(folder: Path, said: tuple, labels: tuple, anchors: tuple, beneath: tuple = (), flagged: tuple = ()):
    """The frame of `folder` made from a hand-made index (see `frame_index`), with what the empty home itself gives
    for its status and these ids flagged as looking like they hold a key."""
    held = store.status(folder)
    with standing_in(store, "_open", lambda *args, **kwargs: frame_index(said, labels, anchors, beneath)):
        with standing_in(store, "status", lambda *args, **kwargs: held):
            with standing_in(store, "flagged", lambda *args, **kwargs: list(flagged)):
                yield


def after(made: str, head: str, n: int = 1) -> str:
    """The n-th paragraph after the one under a heading."""
    return made.split(head + "\n\n", 1)[1].split("\n\n")[n]


def test_a_cuts_frame_packs_a_refusal_under_the_sentence_that_asked(tmp_path):
    with framed(tmp_path, his(b(1)), (x("X1", BRANCH),), (("X1", b(1)),)):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == ["- `b0000001`: tove", f"     ↳ X1 · refused: {BRANCH}"]
    assert frame.REFUSED_HEAD not in made and made.count(BRANCH) == 1


def test_a_judgment_packs_both_sentences_of_the_persons_and_says_it_was_judged_again_once(tmp_path):
    labels = (x("X1", BRANCH, "cooled", "X2"), x("X2", AGAIN))
    with framed(tmp_path, his(b(1), b(2)), labels, (("X1", b(1)), ("X2", b(2))), (("X2", "X1"),)):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "- `b0000002`: tove",
        f"     ↳ X2 · refused: {AGAIN} (judged again once)",
    ]
    assert BRANCH not in made  # what no longer stands is not carried


def test_two_judgments_say_judged_again_2_times_and_quote_the_ask_and_the_evidence_alone(tmp_path):
    labels = (x("X1", BRANCH, "cooled", "X3"), x("X2", AGAIN, "cooled", "X3"), x("X3", LAST))
    anchors = (("X1", b(2)), ("X2", b(1)), ("X3", b(3)))  # X1 asked by the second message, X2 by the first
    with framed(tmp_path, his(b(1), b(2), b(3)), labels, anchors, (("X2", "X1"), ("X3", "X1"))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [  # the first refusal's ask, and what the standing one rests on
        "- `b0000002`: tove",
        "- `b0000003`: tove",
        f"     ↳ X3 · refused: {LAST} (judged again 2 times)",
    ]
    assert "- `b0000001`" not in made


def test_refusals_come_first_in_the_packed_list_and_their_sentences_are_not_quoted_again(tmp_path):
    labels = (DOOR, w("W1", "The wabe is mapped."), w("W2", "The tove is gyred."), x("X1", BRANCH))
    anchors = (("N1", b(2)), ("W1", b(1)), ("W2", b(2)), ("X1", b(2)))
    with framed(tmp_path, his(b(1), b(2)), labels, anchors):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)  # laid out as before: the sentence is quoted as the work's
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000002`: tove",
        f"     ↳ X1 · refused: {BRANCH}",
        "     ↳ N1: the line at the door",
        "     ↳ W2 (session): The tove is gyred. [b0000002]",
        "- `b0000001`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000001]",
    ]
    assert made.count("- `b0000002`: tove") == 1 and THE_WORK not in made
    assert section(before, frame.REFUSED_HEAD) == [f"- X1 (session): {BRANCH} [b0000002]"]
    assert section(before, OWN_WORDS) == ["- `b0000002`: tove", "- `b0000001`: tove"]


def test_four_families_cross_all_four_and_no_sentence_counts_them(tmp_path):
    """Every family that stands crosses, the newest first: there is no cap of three, and no sentence counts the
    oldest in its place (it was "1 more refusal stands and is not carried: X1; `labels` gives it.")."""
    labels = tuple(x(f"X{k}", f"Refused {k}.") for k in range(1, 5))
    anchors = tuple((f"X{k}", b(k)) for k in range(1, 5))
    with framed(tmp_path, his(*(b(k) for k in range(1, 5))), labels, anchors):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
        new = frame.compose(tmp_path, 9000, new=True)  # a session started new is given them too
    assert section(made, frame.PACKED_HEAD) == [
        line for k in (4, 3, 2, 1) for line in (f"- `{b(k)}`: tove", f"     ↳ X{k} · refused: Refused {k}.")
    ]
    for laid in (made, before, new):
        assert "more refusal" not in laid
    for laid in (before, new):
        assert section(laid, frame.REFUSED_HEAD) == [f"- X{k} (session): Refused {k}. [{b(k)}]" for k in (4, 3, 2, 1)]


def test_five_families_all_cross_and_the_work_follows_them(tmp_path):
    """Five families, all of them carried, the newest first, and the work after them; by count, as a frame past its
    size is made, no sentence counts them either (it was "2 more refusals stand and are not carried: X1, X2")."""
    labels = tuple(x(f"X{k}", f"Refused {k}.") for k in range(1, 6)) + (WABE,)
    anchors = tuple((f"X{k}", b(k)) for k in range(1, 6)) + (("W1", b(6)),)
    with framed(tmp_path, his(*(b(k) for k in range(1, 7))), labels, anchors):
        made = frame.compose(tmp_path, 9000, session="s1")
        counted = frame._composed(tmp_path, 9000, False, "", by_count=True)
    assert section(made, frame.PACKED_HEAD) == [
        *(line for k in (5, 4, 3, 2, 1) for line in (f"- `{b(k)}`: tove", f"     ↳ X{k} · refused: Refused {k}.")),
        "- `b0000006`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000006]",
    ]
    assert section(counted, frame.REFUSED_HEAD) == [f"- X{k} (session): Refused {k}. [{b(k)}]" for k in (5, 4, 3, 2, 1)]
    assert "more refusal" not in made and "more refusal" not in counted


def test_laid_out_as_before_the_refusals_are_a_part_of_their_own_before_the_work_and_quote_nothing(tmp_path):
    labels = (x("X1", BRANCH, "cooled", "X2"), x("X2", AGAIN), WABE)
    anchors = (("X1", b(1)), ("X2", b(2)), ("W1", b(3)))
    with framed(tmp_path, his(b(1), b(2), b(3)), labels, anchors, (("X2", "X1"),)):
        made = frame.compose(tmp_path, 9000)
    assert section(made, frame.REFUSED_HEAD) == [f"- X2 (session): {AGAIN} [X1, b0000002] (judged again once)"]
    assert made.index(frame.REFUSED_HEAD) < made.index(THE_WORK) and frame.PACKED_HEAD not in made
    assert section(made, OWN_WORDS) == ["- `b0000003`: tove"]  # the work's own words, and no ask


def test_a_guarded_ask_is_not_quoted_and_the_refusal_line_still_stands(tmp_path):
    said = (
        ("c0000001", "his", "brillig one"),
        ("c0000001", "his", "brillig two"),  # an id two messages share
        (b(2), "his", "brillig, flagged as a key"),
        (b(3), "session", "brillig, the session's"),
        (b(4), "his", "tove"),
    )
    labels = (x("X1", "Shared."), x("X2", "Flagged."), x("X3", "Not the person's."), w("W1", "The wabe is mapped."))
    anchors = (("X1", "c0000001"), ("X2", b(2)), ("X3", b(3)), ("W1", b(4)))
    with framed(tmp_path, said, labels, anchors, flagged=(b(2),)):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000004`: tove",
        "     ↳ W1 (session): The wabe is mapped. [b0000004]",
    ]
    lines = [
        "- X3 (session): Not the person's. [b0000003]",
        "- X2 (session): Flagged. [b0000002]",
        "- X1 (session): Shared. [c0000001]",
    ]
    assert section(made, frame.REFUSED_HEAD) == section(before, frame.REFUSED_HEAD) == lines
    for laid in (made, before):
        assert "brillig" not in laid and not any(each in laid for each in ("`c0000001`:", "`b0000002`:", "`b0000003`:"))


def test_a_family_in_another_models_hand_or_resting_on_nothing_held(tmp_path):
    labels = (
        x("X1", BRANCH, "cooled", "X2", model="mine"),
        x("X2", AGAIN, model="theirs"),  # the newest judgment, in another model's hand: not this session's
        x("X3", "Rests on what is gone.", "unresolved"),
    )
    anchors = (("X1", b(1)), ("X2", b(2)), ("X3", "c0000009"))
    with framed(tmp_path, his(b(1), b(2)), labels, anchors, (("X2", "X1"),)):
        made = frame.compose(tmp_path, 9000, session="s1", model="mine")
        anyone = frame.compose(tmp_path, 9000, session="s1")
        assert store.not_by(tmp_path, "mine") == ["X2"]  # a refusal in another model's hand is named as such
    assert section(made, frame.PACKED_HEAD) == ["- `b0000001`: tove", f"     ↳ X1 · refused: {BRANCH}"]
    assert section(anyone, frame.PACKED_HEAD)[-1] == f"     ↳ X2 · refused: {AGAIN} (judged again once)"
    assert "1 label rests on what the archive no longer holds: X3; `labels` gives them." in made


def long_refusals(folder: Path, refusals: bool = True, digits: int = 1, long: int = 0):
    """A home with five families of refusals, each asked by two long messages, and a line at the door and a work
    label resting on twenty more. Without `refusals`, the same home with none; with `digits`, keys of that many
    digits, as a page written by hand may hold; with `long`, reasons of that many characters."""
    asks = [b(k) for k in range(1, 11)]
    words = [b(k) for k in range(11, 31)]
    key = [f"X{k:0{digits}d}" for k in range(1, 6)]
    reason = [(f"Refused {k}, " + "for a reason " * 400)[: long or 271].rstrip() + "." for k in range(1, 6)]
    labels = tuple(x(key[k - 1], reason[k - 1]) for k in range(1, 6) if refusals)
    labels += (DOOR, WABE)
    anchors = tuple((key[k - 1], asks[2 * k - 2 + n]) for k in range(1, 6) for n in (0, 1))
    anchors += tuple((name, each) for name in ("N1", "W1") for each in words)
    return framed(folder, his(*asks, *words, text="tove " * 80), labels, anchors)


def families_in(made: str) -> int:
    """How many families of refusals a frame carries: a packed line, or a line of the part of their own."""
    return sum(
        1
        for each in made.split("\n")
        if each.startswith("- X") or (each.startswith("     ↳ X") and "· refused:" in each)
    )


def test_a_frame_carries_every_family_at_every_size_and_passes_its_size_only_for_them(tmp_path):
    """Five families, at every size, packed, laid out as before and for a new session: all five cross, by their
    sentences whole, and no sentence counts them (three crossed at the most, none at the least size, and the rest
    were counted). A frame stays within its size where everything else it carries can give way to them; where it
    is longer, it is the frame of the least size, which carries nothing that can give way: no work, no sentence
    of the person's, and the line at the door at its least."""
    sizes = range(frame.LEAST, frame.MOST + 1, 25)
    variants = (("s1", False), ("", False), ("", True))
    with long_refusals(tmp_path):
        least = {
            variant: frame.compose(tmp_path, frame.LEAST, new=variant[1], session=variant[0]) for variant in variants
        }
        for size in sizes:
            for session, new in variants:
                made = frame.compose(tmp_path, size, new=new, session=session)
                assert families_in(made) == 5 and "more refusal" not in made, (size, session, new)
                assert all(f"Refused {k}, for a reason" in made for k in range(1, 6)), (size, session, new)
                assert len(made) <= frame.MOST, (size, session, new)
                if len(made) > size:
                    assert made == least[session, new], (size, session, new)
    for made in least.values():
        assert len(made) > frame.LEAST and "W1" not in made and "- `b00000" not in made and "tove tove" not in made


def test_only_past_the_most_a_frame_may_be_do_the_oldest_families_go_to_the_sentence_that_counts_them(tmp_path):
    """Five families of 3,000-character reasons are more than the most a hook can carry (MOST): the newest cross whole
    as long as they fit within it, and the oldest go to the sentence that names them by key, oldest first; with keys
    written by hand so long that naming them would pass MOST, it says how many they are. At the least size five
    families of short reasons all cross, and the frame is longer than the size asked (they went to that sentence)."""
    with long_refusals(tmp_path):
        least = frame.compose(tmp_path, frame.LEAST, session="s1")
    assert families_in(least) == 5 and "more refusal" not in least and frame.LEAST < len(least) <= frame.MOST
    with long_refusals(tmp_path, long=3000):
        most = frame.compose(tmp_path, frame.MOST, session="s1")
        least = frame.compose(tmp_path, frame.LEAST, session="s1")
    carried = families_in(most)
    left = [f"X{k}" for k in range(1, 6 - carried)]
    assert 0 < carried < 5 and len(most) <= frame.MOST and len(least) <= frame.MOST
    for made in (most, least):  # at the least size as at the most: the frame is as long as the families make it
        assert families_in(made) == carried, made
        assert f"{len(left)} more refusals stand and are not carried: {', '.join(left)}; `labels` gives them." in made
    one_more = len(f"- X{5 - carried} (session): ") + 3000
    assert len(most) + one_more > frame.MOST  # the newest of those left would pass it
    with long_refusals(tmp_path, digits=1000, long=3000):
        long_keys = frame.compose(tmp_path, frame.MOST, session="s1")
    carried = families_in(long_keys)
    assert 0 < carried < 5 and len(long_keys) <= frame.MOST
    counted = f"{5 - carried} more refusal{'s' if carried < 4 else ''} stand{'' if carried < 4 else 's'} and "
    assert counted in long_keys and "not carried; `labels` gives" in long_keys
    named = ", ".join("X" + "0" * 999 + str(k) for k in range(1, 6 - carried))
    assert len(long_keys) + len(": " + named) > frame.MOST  # naming them by key would pass it


def test_a_family_whose_line_alone_passes_the_most_goes_to_the_sentence_that_counts_it_in_a_part_of_its_own(tmp_path):
    """One family whose reason is 9,400 characters, as a page written by hand may hold it (a mark takes LONGEST at the
    most): beside what the frame cannot give way, its line would take the frame past MOST, so it goes to the sentence
    that counts the families, and no family is carried. The sentence then follows no refusal: it stands as a part of
    its own, where their part would be, packed, laid out as before and for a new session, within MOST."""
    reason = ("Refused, " + "for a reason " * 800)[:9400].rstrip() + "."
    counted = "1 more refusal stands and is not carried: X1; `labels` gives it."
    with framed(tmp_path, his(b(1), b(2)), (DOOR, x("X1", reason), WABE), (("N1", b(2)), ("X1", b(1)), ("W1", b(2)))):
        for session, new in (("s1", False), ("", False), ("", True)):
            made = frame.compose(tmp_path, frame.MOST, new=new, session=session)
            assert families_in(made) == 0 and "for a reason" not in made, (session, new)
            assert f"\n\n{counted}\n\n" in made and made.count("more refusal") == 1, (session, new)
            assert frame.REFUSED_HEAD not in made and len(made) <= frame.MOST, (session, new)


def test_a_frame_with_no_refusal_is_as_it_was(tmp_path):
    # past its opening, the frame of a home with no refusal, packed and laid out as before, as the frame of this
    # branch gave it before refusals were (taken from that frame.py, run on the same hand-made home); but packed, the
    # work label resting on two sentences is now written once beneath the second, and no bare key stands under the first
    waits = ("W2", "work", "The borogove waits.")
    anchors = (("N1", b(1)), ("W1", b(1)), ("W1", b(2)), ("W2", "c0000009"))
    with at_home(tmp_path, (b(1), b(2)), (DOOR, WABE, waits), anchors):
        packed = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    head = frame.opening()
    assert packed.startswith(head) and before.startswith(head)
    assert packed[len(head) :] == (
        "\n\n## Left at the door by the session before this cut\n\n- N1 (session): Find out whether the tove is "
        "gyred. [b0000001]\n\nMarked after this line: W1, W2.\n\n## What was said, and what the session told of it"
        "\n\n- `b0000001`: tove\n     ↳ N1: the line at the door\n- `b0000002`: tove\n     ↳ W1 (session): The wabe "
        "is mapped. [b0000001, b0000002]\n\n## The work, newest first\n\n- W2 (session): The "
        "borogove waits. [c0000009]\n\nThe store holds 0 messages of the person's and 0 of yours, from  to , and 0 "
        "labels.\n"
    )
    assert before[len(head) :] == (
        "\n\n## Left at the door by the session before this cut\n\n- N1 (session): Find out whether the tove is "
        "gyred. [b0000001]\n\nMarked after this line: W1, W2.\n\n## The work, newest first\n\n- W2 (session): The "
        "borogove waits. [c0000009]\n- W1 (session): The wabe is mapped. [b0000001, b0000002]\n\n## The person's own "
        "words, as they stand in the record\n\n- `b0000001`: tove\n- `b0000002`: tove\n\nThe store holds 0 messages "
        "of the person's and 0 of yours, from  to , and 0 labels.\n"
    )


def test_the_labels_a_frame_carries_are_counted_once_each_and_a_refusal_packed_beneath_its_quote_too(tmp_path):
    # two standing lines, the line at the door and a work label on the first sentence, a refusal on the second, and a
    # work label no quoted sentence stands beside: packed, W1 is written beneath a sentence and X1 beneath its quote
    labels = (
        ("R1", "relation", "The tove is the person's own."),
        ("R2", "relation", "The borogove is the person's too."),
        DOOR,
        WABE,
        x("X1", BRANCH),
        w("W2", "The borogove waits."),
    )
    anchors = (("R1", b(1)), ("R2", b(1)), ("N1", b(1)), ("W1", b(1)), ("X1", b(2)), ("W2", "c0000009"))
    with framed(tmp_path, his(b(1), b(2)), labels, anchors):
        packed = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    lines = section(packed, frame.PACKED_HEAD)
    assert f"     ↳ X1 · refused: {BRANCH}" in lines and "     ↳ W1 (session): The wabe is mapped. [b0000001]" in lines
    assert "     ↳ N1: the line at the door" in lines and frame.REFUSED_HEAD in before
    # R1, R2, W1, W2 and X1, each once; the line at the door, laid out or beneath a sentence, is no label carried here
    assert frame.carried(packed) == frame.carried(before) == 5
    # a misaligned silencing, carried as itself in the part of refusals, is counted as the refusals are
    with framed(tmp_path, his(b(1)), (sx("S1", "Put to rest by hand.", "misaligned"),), (("S1", b(1)),)):
        alone = frame.compose(tmp_path, 9000, session="s1")
    assert section(alone, frame.REFUSED_HEAD)[0].startswith("- S1 (session): ") and frame.carried(alone) == 1


# --- the server: `crossing`, and what a session is told ---------------------------------------------------------


def files(folder: Path) -> list[tuple[str, int]]:
    """Every file of a home, by its path in it and its size."""
    return sorted((str(each.relative_to(folder)), each.stat().st_size) for each in folder.rglob("*") if each.is_file())


@contextlib.contextmanager
def served(folder: Path, project: Path):
    """The door's server answering from `folder`, the home of `project`, for a session a person sits in."""
    project.mkdir(exist_ok=True)
    with setting(CLAUDE_PROJECT_DIR=str(project)):
        with standing_in(store, "kept", lambda *args, **kwargs: folder):
            with standing_in(record, "attended", lambda *args, **kwargs: True):
                yield


def test_crossing_gives_the_frame_of_the_session_that_spoke_last_as_the_door_makes_it_and_changes_no_file(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    asked: list = []
    with_trade = frame.with_trade  # the server tells the sentence after the frame: both are of one making

    def composed(*args, **kwargs):
        asked.append(kwargs)
        return with_trade(*args, **kwargs)

    with kept_home(folder, b(1), f"{b(2)}@s2"), served(folder, project):
        assert serve.call("mark", {"kind": "refused", "sentence": BRANCH, "anchors": [b(1)]}) == ("marked X1", False)
        judged = {"kind": "refused", "sentence": AGAIN, "anchors": ["X1", b(2)]}
        assert serve.call("mark", judged) == ("marked X2", False)
        assert serve.asked("labels", {"kind": "refused"}) == ["labels", "--kind", "refused", "--"]
        listed = serve.call("labels", {"kind": "refused"})[0].split("\n")
        assert [line.split(" ")[1] for line in listed] == ["X2", "X1"]
        store.build(folder)
        was = files(folder)
        with standing_in(frame, "with_trade", composed):
            text, failed = serve.call("crossing", {})
        answer = serve.handle({"id": 1, "method": "tools/call", "params": {"name": "crossing", "arguments": {}}})
        assert files(folder) == was
        made = frame.compose(folder, None, model=layer.current(folder, "s2"), session="s2")
    assert asked == [{"model": layer.current(folder, "s2"), "session": "s2"}]  # s2 spoke last
    assert not failed and text == made
    assert answer["result"] == {"content": [{"type": "text", "text": made}], "isError": False}
    assert section(made, frame.PACKED_HEAD) == [  # a cut's frame for a session named: packed
        "- `b0000001`: tove",
        "- `b0000002`: tove",
        f"     ↳ X2 · refused: {AGAIN} (judged again once)",
    ]
    asked.clear()
    with kept_home(folder, f"{b(2)}@s2", b(1)), served(folder, project), standing_in(frame, "with_trade", composed):
        assert serve.call("crossing", {})[1] is False
    assert [each["session"] for each in asked] == ["s1"]  # now s1 spoke last


def test_crossing_in_a_home_whose_index_holds_no_message_gives_the_frame_of_no_session(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    page = folder / "labels" / f"{DAY}.md"
    page.parent.mkdir()
    page.write_text(f"| X1 | {BRANCH} | session | `{b(1)}` |\n", encoding="utf-8")  # a row written by hand
    with kept_home(folder), served(folder, project):
        assert door.spoke_last(folder) == ""
        text, failed = serve.call("crossing", {})
        made = frame.compose(folder)
    assert not failed and text == made and frame.PACKED_HEAD not in made
    assert "1 label rests on what the archive no longer holds: X1; `labels` gives them." in made


def test_crossing_in_a_room_that_holds_nothing_says_what_look_says(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    with served(folder, project):
        looked, _ = serve.call("look", {})
        text, failed = serve.call("crossing", {})
    assert not failed and text == looked and looked.startswith("The store in outline: 0 days, 0 messages, 0 labels")
    assert files(folder) == []


def test_the_texts_a_session_is_told_of_refusals_and_of_crossing_stand_word_for_word():
    with setting(CLAUDE_PLUGIN_ROOT=str(ROOT)):
        started = serve.handle({"id": 1, "method": "initialize", "params": {}})["result"]["instructions"]
    alone = serve.instructions()
    stacked = "Lines can be stacked into fewer: `mark` a label that rests on them, and the frame then carries the one. "
    assert stacked + TOLD + " The person is shown" in started
    tools = {each["name"]: each for each in serve.handle({"id": 2, "method": "tools/list"})["result"]["tools"]}
    kind = tools["mark"]["inputSchema"]["properties"]["kind"]
    assert kind["description"] == MARK_KIND and kind["enum"] == ["relation", "work", "refused", "silenced"]
    listing = tools["labels"]["inputSchema"]["properties"]["kind"]
    assert listing["enum"] == ["relation", "work", "next", "refused"] and listing["description"] == LABELS_KIND
    assert len(json.dumps(serve.TOOLS)) < 5900  # the size the server's own test holds every tool to
    assert tools["crossing"]["description"] == CROSSING
    assert set(tools["crossing"]["inputSchema"]["properties"]) == {"home"} and serve.NAMES[-1] == "crossing"
    for told in (started, alone):
        assert f"`{HANDLE.replace(':', '`:', 1)}" in told
    for new in (False, True):  # the frame's opening names the six it named before: the tool says what it is itself
        assert "crossing" not in frame.opening(new)
    assert serve.asked("crossing", {}) == ["frame"]


def test_over_a_pipe_the_server_lists_crossing_and_passes_over_what_is_no_request():
    lines = [
        '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}',
        '{"jsonrpc": "2.0", "method": "notifications/initialized"}',  # answered with nothing
        "not a request",  # passed over
        "[1, 2]",  # no request either
        '{"jsonrpc": "2.0", "id": 2, "method": "ping"}',
        '{"jsonrpc": "2.0", "id": 3, "method": "tools/list"}',
    ]
    said = io.StringIO()
    with standing_in(sys, "stdin", io.StringIO("\n".join(lines) + "\n")), contextlib.redirect_stdout(said):
        assert serve.main() == 0
    answers = [json.loads(line) for line in said.getvalue().splitlines()]
    assert [each["id"] for each in answers] == [1, 2, 3]
    assert answers[1]["result"] == {}
    assert [each["name"] for each in answers[2]["result"]["tools"]][-1] == "crossing"


# --- the second review: quotes and room, families whose first refusal is gone, the make, a shared ask -------------


def test_a_family_quotes_its_ask_and_its_evidence_alone_and_its_line_is_carried_however_many_it_rests_on(tmp_path):
    asks = tuple(b(k) for k in range(1, 26))
    with framed(tmp_path, his(*asks, text="tove " * 80), (x("X1", "Short reason."),), tuple(("X1", k) for k in asks)):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    lines = section(made, frame.PACKED_HEAD)
    assert [each[:13] for each in lines] == ["- `b0000001`:", "- `b0000025`:", "     ↳ X1 · r"]
    assert lines[-1] == "     ↳ X1 · refused: Short reason." and "more refusal" not in made
    assert section(before, frame.REFUSED_HEAD) == ["- X1 (session): Short reason. [" + ", ".join(asks) + "]"]


def test_a_family_whose_quotes_do_not_fit_the_packed_frame_is_carried_by_its_line_alone(tmp_path):
    words = tuple(b(k) for k in range(11, 31))
    labels = (WABE, x("X1", "Short reason."))
    anchors = tuple(("W1", each) for each in words) + (("X1", b(1)),)
    said = his(b(1), text="brillig " * 60) + his(*words)
    found = set()
    with framed(tmp_path, said, labels, anchors):
        for size in range(frame.LEAST, frame.MOST + 1, 10):
            made = frame.compose(tmp_path, size, session="s1")
            assert len(made) <= size, size
            named = "1 more refusal stands and is not carried: X1; `labels` gives it."  # at the least sizes
            assert any(each in made for each in ("X1 · refused: Short reason.", "- X1 (session):", named)), size
            packed, apart, quoted = frame.PACKED_HEAD in made, frame.REFUSED_HEAD in made, "brillig" in made
            found.add((packed, apart, quoted))
            if packed and apart:
                assert section(made, frame.REFUSED_HEAD) == ["- X1 (session): Short reason. [b0000001]"]
    # packed with its quote at the larger sizes; packed, the family by its line alone, where the quote does not fit
    assert {(True, False, True), (True, True, False)} <= found


def test_a_family_whose_first_refusal_is_gone_is_still_one_and_its_newest_stands(tmp_path):
    page = tmp_path / "labels" / f"{DAY}.md"
    page.parent.mkdir()
    x1 = store.digest(BRANCH)
    page.write_text(  # X1 struck, or its row deleted: the rows that name it are left
        f"| X2 | {AGAIN} | session | `X1@{x1}`, `{b(2)}` |\n| X3 | {LAST} | session | `X1@{x1}`, `{b(3)}` |\n",
        encoding="utf-8",
    )
    with kept_home(tmp_path, b(1), b(2), b(3), b(4)):
        assert states(tmp_path) == {"X2": ("cooled", "X3"), "X3": ("carried", None)}
        assert store.families(store.labels(tmp_path)) == {"X2": "X1", "X3": "X1"}
        given = store.listed(tmp_path, ids=("X2",))["labels"]
        assert [(each["id"], each["depth"]) for each in given] == [("X2", 1), ("X3", 1)]
        # judged again through one of them, the new row names the first refusal as the family's rows name it
        out = refuse(tmp_path, "Nor now.", "X3", b(4))
        assert (out["written"], out["beneath"]) == (True, ["X1"])
        assert f"| X4 | Nor now. | session | `X1@{x1}`, `{b(4)}` |" in page.read_text(encoding="utf-8")
        assert states(tmp_path)["X4"] == ("carried", None) and states(tmp_path)["X3"] == ("cooled", "X4")
    labels = (x("X2", AGAIN, "cooled", "X3"), x("X3", LAST))
    with framed(tmp_path, his(b(1), b(2)), labels, (("X2", b(1)), ("X3", b(2))), (("X2", "X1"), ("X3", "X1"))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [  # the oldest ask of any of it, and the standing one's
        "- `b0000001`: tove",
        "- `b0000002`: tove",
        f"     ↳ X3 · refused: {LAST} (judged again once)",
    ]


def test_a_misaligned_refusal_is_carried_as_itself_with_the_note_a_misaligned_stack_carries(tmp_path):
    labels = (
        x("X1", BRANCH),
        x("X4", "The tag is not pushed."),
        x("X5", "Of two families.", "misaligned"),
        x("X6", "Over a standing line.", "misaligned"),
    )
    anchors = (("X1", b(1)), ("X4", b(2)), ("X5", b(3)), ("X6", b(3)))
    beneath = (("X5", "X1"), ("X5", "X4"), ("X6", "R1"))
    with framed(tmp_path, his(b(1), b(2), b(3)), labels, anchors, beneath):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    again = " (to be written again: a line beneath it changed)"
    lines = [f"- X6 (session): Over a standing line.{again} [R1, b0000003]"]
    lines += [f"- X5 (session): Of two families.{again} [X1, X4, b0000003]"]
    assert section(made, frame.REFUSED_HEAD) == lines  # packed: they quote nothing, so they stand apart
    assert section(before, frame.REFUSED_HEAD) == lines + [
        "- X4 (session): The tag is not pushed. [b0000002]",
        f"- X1 (session): {BRANCH} [b0000001]",
    ]
    assert "- `b0000003`" not in made  # quoted on no misaligned label's account
    assert f"     ↳ X1 · refused: {BRANCH}" in made.split("\n")  # four, and every one carried: the oldest too
    for laid in (made, before):
        assert "more refusal" not in laid
    kept = [
        {"id": "X1", "kind": "refused", "text": "a", "anchors": [b(1)], "beneath": []},
        {"id": "X2", "kind": "refused", "text": "b", "anchors": [b(1)], "beneath": [("R1", "000000")]},
    ]
    assert store._stood(kept, {b(1)})[1] == {"X1": "carried", "X2": "misaligned"}


def test_a_message_is_never_quoted_because_a_standing_line_rests_on_it_and_one_a_refusal_rests_on_too_is_quoted_for_it(
    tmp_path,
):
    standing = ("R1", "relation", "The tove is the person's own.")
    held = ["- R1 (session): The tove is the person's own. [b0000001]"]
    with framed(tmp_path, his(b(1)), (standing, x("X1", BRANCH)), (("R1", b(1)), ("X1", b(1)))):
        both = frame.compose(tmp_path, 9000, session="s1")
    with framed(tmp_path, his(b(1)), (standing,), (("R1", b(1)),)):
        alone = frame.compose(tmp_path, 9000, session="s1")
    # beneath the refusal, for the refusal's sake; the standing line is carried as it is, in its own part
    assert section(both, frame.PACKED_HEAD) == ["- `b0000001`: tove", f"     ↳ X1 · refused: {BRANCH}"]
    assert section(both, frame.ARRIVALS["cut"]["standing"]) == section(alone, frame.ARRIVALS["cut"]["standing"]) == held
    assert "`b0000001`:" not in alone and frame.PACKED_HEAD not in alone and OWN_WORDS not in alone


def test_two_families_on_one_ask_stand_under_it_the_newer_first(tmp_path):
    labels = (x("X1", BRANCH), x("X2", "The tag is not pushed."))
    with framed(tmp_path, his(b(1)), labels, (("X1", b(1)), ("X2", b(1)))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "     ↳ X2 · refused: The tag is not pushed.",
        f"     ↳ X1 · refused: {BRANCH}",
    ]
    assert frame.REFUSED_HEAD not in made


def test_a_judgment_in_trouble_adds_nothing_to_the_count_and_is_quoted_for_nothing(tmp_path):
    labels = (x("X1", BRANCH, "cooled", "X3"), x("X2", AGAIN, "unresolved"), x("X3", LAST))
    anchors = (("X1", b(1)), ("X2", b(2)), ("X3", b(3)))
    with framed(tmp_path, his(b(1), b(2), b(3)), labels, anchors, (("X2", "X1"), ("X3", "X1"))):
        made = frame.compose(tmp_path, 9000, session="s1")
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "- `b0000003`: tove",
        f"     ↳ X3 · refused: {LAST} (judged again once)",
    ]
    assert "- `b0000002`" not in made
    assert "1 label rests on what the archive no longer holds: X2; `labels` gives them." in made


def test_a_stack_of_the_work_that_names_a_refusals_key_passes_it_over_as_it_always_did(tmp_path):
    page = tmp_path / "labels" / f"{DAY}.md"
    page.parent.mkdir()
    w1, x1 = store.digest("The wabe is mapped."), store.digest(BRANCH)
    page.write_text(
        f"| W1 | The wabe is mapped. | session | `{b(1)}` |\n| X1 | {BRANCH} | session | `{b(1)}` |\n"
        f"| W2 | Both, as one. | session | `X1@{x1}`, `W1@{w1}`, `{b(2)}` |\n"
        f"| R1 | Over nothing there. | session | `X9@{x1}`, `{b(2)}` |\n",
        encoding="utf-8",
    )
    rows = {each["id"]: each for each in store.labels(page.parent.parent)}
    assert rows["W2"]["beneath"] == [("W1", w1)] and rows["W2"]["anchors"] == [b(2)]
    assert rows["R1"]["beneath"] == [] and rows["R1"]["anchors"] == [b(2)]
    with kept_home(tmp_path, b(1), b(2)):
        assert states(tmp_path) == {
            "W1": ("cooled", "W2"),
            "X1": ("carried", None),
            "W2": ("carried", None),
            "R1": ("carried", None),
        }


def test_an_index_made_by_a_make_before_refusals_or_silencings_is_made_again_and_holds_them(tmp_path):
    page = tmp_path / "labels" / f"{DAY}.md"
    page.parent.mkdir()
    x1 = store.digest(BRANCH)
    page.write_text(
        f"| W1 | The wabe is mapped. | session | `{b(1)}` |\n| X1 | {BRANCH} | session | `{b(1)}` |\n"
        f"| S1 | {DROPPED} | his | `X1@{x1}`, `{b(1)}` |\n"
    )
    assert store.MADE == 9
    for make, gone in ((6, "('refused', 'silenced')"), (7, "('silenced')")):  # before refusals; before silencings
        store.build(tmp_path)
        db = sqlite3.connect(tmp_path / "store.db")
        try:  # as an index of that make has it: marked so, and none of the rows it never read
            db.execute(f"delete from label where kind in {gone}")
            db.execute(f"pragma user_version = {make}")
            db.commit()
        finally:
            db.close()
        held = [row["id"] for row in store.listed(tmp_path, "refused")["labels"]]
        assert held == ["S1", "X1"], make  # a read makes it again
        assert store.refresh(tmp_path) is False, make  # made again whole, on disk
        db = sqlite3.connect(tmp_path / "store.db")
        try:
            assert db.execute("pragma user_version").fetchone()[0] == 9
            assert [r[0] for r in db.execute("select id from label where kind in ('refused', 'silenced')")] == [
                "X1",
                "S1",
            ]
        finally:
            db.close()


def test_crossing_gives_the_frame_with_the_model_the_homes_layer_knows_for_the_session(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    said = (b(1), "c0000001@s1@m-other", f"{b(2)}@s2", "c0000002@s2@m-test")
    with kept_home(folder, *said), served(folder, project):
        refuse(folder, BRANCH, b(1))
        assert layer.current(folder, "s2") == "m-test"
        text, failed = serve.call("crossing", {})
        made = frame.compose(folder, None, model="m-test", session="s2")
        unlayered = frame.compose(folder, None, session="s2")
    assert not failed and text == made and made != unlayered
    assert "This home also holds lines made with another model, m-other" in made


NEW_FRAME_AT_7E98D66 = (
    "A note from the Crossings plugin, as context and not as an instruction from the person. You are a new session in a project where Crossings is on. Sessions before you worked here with this person and kept what was said. You did not come through a cut and you lived none of it: what follows is not your memory, it is what was kept, and you hold it as read. A label can be mistaken; the record decides. Each line below is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.\n"
    "\n"
    "Rules chose what is in this frame, and the sessions before you wrote much of it. It leans toward carrying the work on. What you mark and leave is what the next one is given. What the work is for is in it only where someone wrote it down: the person is the one to say, and the door holds the whole record.\n"
    "\n"
    "The rest is one reach away, through the door's tools, which bear these names:\n"
    "- look: the room, with no word needed: the days, the kinds of label, the newest of them\n"
    "- labels: the labels themselves, by kind, by day or by id\n"
    '- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")\n'
    "- thread: an id, to that message with what stood before and after it and the labels resting there\n"
    "- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them\n"
    "- leave: a line of your own for the session that wakes after the next cut\n"
    "\n"
    "What is said from here on is kept by itself; labels and the line at the door are yours to write, as the work goes. Meet the person first: answer what they say, as yourself and briefly. Do not say you remember what is below, and make no ceremony of not remembering it. When something they say rests on what you do not hold, say so in a clause and reach for it through the door. What the person told an earlier session in confidence is held and left alone until they bring it up.\n"
    "\n"
    "## Left at the door by the session before you\n"
    "\n"
    "- N1 (session): Find out whether the tove is gyred. [b0000002]\n"
    "\n"
    "Marked after this line: W1, W2.\n"
    "\n"
    "## Standing, between the person and the sessions before you\n"
    "\n"
    "- R1 (session): The tove is the person's own. [b0000001]\n"
    "\n"
    "## The work, newest first\n"
    "\n"
    "- W2 (session): The borogove waits. [c0000009]\n"
    "- W1 (session): The wabe is mapped. [b0000002, b0000003]\n"
    "\n"
    "## The person's own words, as they stand in the record\n"
    "\n"
    "- `b0000002`: tove\n"
    "- `b0000003`: tove\n"
    "\n"
    "The store holds 0 messages of the person's and 0 of the sessions before you, from  to , and 0 labels.\n"
)


def test_a_new_sessions_frame_with_no_refusal_is_what_it_was_before_refusals(tmp_path):
    # the frame a new session is given, at the home's size, for a hand-made home with no refusal: as the frame.py
    # of commit 7e98d66 gave it for the same home
    labels = (
        ("R1", "relation", "The tove is the person's own."),
        ("N1", "next", "Find out whether the tove is gyred."),
        ("W1", "work", "The wabe is mapped."),
        ("W2", "work", "The borogove waits."),
    )
    anchors = (("R1", b(1)), ("N1", b(2)), ("W1", b(2)), ("W1", b(3)), ("W2", "c0000009"))
    with framed(tmp_path, his(b(1), b(2), b(3)), labels, anchors):
        assert frame.compose(tmp_path, new=True) == NEW_FRAME_AT_7E98D66


# --- the fourth review: every move on a refusal rests on a message, and a silencing puts one to rest ---------------

DROPPED = "Put to rest: the person no longer wants the branch kept."


def test_a_judgment_rests_on_a_message_and_without_one_nothing_is_marked(tmp_path):
    with kept_home(tmp_path, b(1), b(2), "c0000001@s1@m-test"):
        refuse(tmp_path, BRANCH, b(1))
        page = tmp_path / "labels" / f"{DAY}.md"
        written = page.read_text(encoding="utf-8")
        assert refuse(tmp_path, AGAIN, "X1") == {"written": False, "why": NO_MESSAGE.format("A judgment")}
        assert page.read_text(encoding="utf-8") == written
        judged = refuse(tmp_path, AGAIN, "X1", b(2))  # marked as before
        assert (judged["written"], judged["id"], judged["beneath"], judged["anchors"]) == (True, "X2", ["X1"], [b(2)])
        assert refuse(tmp_path, LAST, "X2", "c0000001")["written"]  # a message of the session's voice will do too


def test_a_silencing_by_the_first_key_or_a_later_members_by_the_person_or_the_session_silences_its_family(tmp_path):
    with kept_home(tmp_path, b(1), b(2), b(3), b(4)):
        refuse(tmp_path, BRANCH, b(1))
        refuse(tmp_path, AGAIN, "X1", b(2))
        refuse(tmp_path, "The tag is not pushed.", b(3))  # X3, a family of its own
        by_him = silence(tmp_path, DROPPED, "X2", b(4), whose="his")  # by a later member's key, the person's
        by_session = silence(tmp_path, "The tag is pushed by hand now.", "X3", b(4))  # by the first key
        assert (by_him["id"], by_him["beneath"], by_session["id"], by_session["beneath"]) == (
            "S1",
            ["X1"],
            "S2",
            ["X3"],
        )
        page = (tmp_path / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
        assert f"| S1 | {DROPPED} | his | `X1@{store.digest(BRANCH)}`, `{b(4)}` |" in page
        assert states(tmp_path) == {
            "X1": ("cooled", "S1"),
            "X2": ("cooled", "S1"),
            "X3": ("cooled", "S2"),
            "S1": ("carried", None),
            "S2": ("carried", None),
        }
        assert store.families(store.labels(tmp_path)) == {"X1": "X1", "X2": "X1", "X3": "X3", "S1": "X1", "S2": "X3"}
        assert store.refusals(tmp_path) == {"standing": [], "silenced": ["S1", "S2"]}
        both = silence(tmp_path, "Both of them, by both.", "X3", b(4), whose="both")
        assert both["id"] == "S3" and store.listed(tmp_path, ids=("S3",))["labels"][-1]["whose"] == "both"


def test_a_refusal_and_its_judgment_are_the_sessions_whoever_is_named_and_a_silencing_keeps_whose_it_is(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()

    def by_door(kind: str, whose: str, sentence: str, *anchors: str) -> str:
        argv = ["mark", "--kind", kind, f"--anchors={','.join(anchors)}", "--cwd", str(project)]
        argv += (["--whose", whose] if whose else []) + ["--", sentence]
        said = io.StringIO()
        with contextlib.redirect_stdout(said):
            assert door.main(argv) == 0, said.getvalue()
        return said.getvalue().split()[1]  # marked X1 in its page

    def by_server(kind: str, whose: str, sentence: str, *anchors: str) -> str:
        given = {"kind": kind, "sentence": sentence, "anchors": list(anchors), **({"whose": whose} if whose else {})}
        text, failed = serve.call("mark", given)
        assert text.startswith("marked ") and not failed, text
        return text.split()[1]

    expected = {}
    with kept_home(folder, b(1), b(2), b(3), b(4)), served(folder, project):
        for mark_by in (by_door, by_server):
            first = {}
            for whose in ("his", "both"):  # a refusal, and a judgment of it, each marked as the person's or both
                first[whose] = mark_by("refused", whose, BRANCH, b(1))
                expected[first[whose]] = expected[mark_by("refused", whose, AGAIN, first[whose], b(2))] = "session"
            # a silencing keeps the whose it is given, and is the session's where none is
            expected[mark_by("silenced", "his", DROPPED, first["his"], b(3))] = "his"
            expected[mark_by("silenced", "", "Pushed by hand.", first["both"], b(4))] = "session"
        written = {label["id"]: label["whose"] for label in store.labels(folder)}
        shelled = store.shelled(folder)
    assert list(expected) == ["X1", "X2", "X3", "X4", "S1", "S2", "X5", "X6", "X7", "X8", "S3", "S4"]
    assert written == expected
    page = (folder / "labels").glob("*.md")
    rows = [line for each in page for line in each.read_text(encoding="utf-8").splitlines() if line.startswith("| X")]
    assert len(rows) == 8 and all(" | session | " in row for row in rows)
    # marked from a shell, a refusal speaks for no one but the session, and is not kept to be said to the person
    assert shelled == ["S1"]


def test_a_silencing_that_names_no_family_two_families_another_kind_or_no_message_is_refused(tmp_path):
    with kept_home(tmp_path, b(1), b(2)):
        refuse(tmp_path, BRANCH, b(1))
        refuse(tmp_path, "The tag is not pushed.", b(2))
        store.mark(tmp_path, "work", "session", "The wabe is mapped.", [b(1)], day=DAY)
        page = tmp_path / "labels" / f"{DAY}.md"
        written = page.read_text(encoding="utf-8")
        refused = {
            (b(1),): "a silencing rests on the key of the refusal it puts to rest: name that key too",
            ("X1", "X2", b(1)): "X1 and X2 are two refusals, and a silencing puts one alone to rest",
            ("X1",): NO_MESSAGE.format("A silencing"),
            ("W1", b(1)): "a silencing rests on messages and on refusals alone, and this names a label of another "
            "kind: W1",
            ("S9", b(1)): "no such label: S9",
        }
        for anchors, why in refused.items():
            assert silence(tmp_path, DROPPED, *anchors) == {"written": False, "why": why}, anchors
        assert page.read_text(encoding="utf-8") == written
        silence(tmp_path, DROPPED, "X1", b(2))  # S1
        assert store.mark(tmp_path, "work", "session", "Over it.", ["S1", b(1)], day=DAY)["why"] == (
            "a stack holds labels of its own kind alone, and of another kind here: S1"
        )
        assert store.mark(tmp_path, "next", "session", "Over it.", ["S1", b(1)], day=DAY)["why"] == (
            "a line left at the door rests on messages alone, never on labels"
        )


def test_a_silenced_family_does_not_cross_and_a_frame_with_none_else_is_the_frame_with_no_refusal(tmp_path):
    refusals = (x("X1", BRANCH, "cooled", "S1"), sx("S1", DROPPED))
    anchors = (("N1", b(2)), ("W1", b(2)), ("X1", b(1)), ("S1", b(1)))
    beneath = (("S1", "X1"),)
    made = {}
    for name, labels in (("silenced", (DOOR, WABE) + refusals), ("none", (DOOR, WABE))):
        with framed(tmp_path, his(b(1), b(2)), labels, anchors, beneath):
            made[name] = [frame.compose(tmp_path, 9000, session="s1"), frame.compose(tmp_path, 9000)]
            made[name].append(frame.compose(tmp_path, 9000, new=True))
    assert made["silenced"] == made["none"]  # packed, laid out as before, and for a new session
    assert frame.PACKED_HEAD in made["none"][0] and frame.REFUSED_HEAD not in made["none"][1]
    with framed(tmp_path, his(b(1)), refusals, (("X1", b(1)), ("S1", b(1))), beneath):
        assert frame.compose(tmp_path, 9000, new=True) == ""  # a new session in a home with no other label
        alone = frame.compose(tmp_path, 9000, session="s1")
    assert "refus" not in alone.split(frame.opening(), 1)[1].lower() and "X1" not in alone and "S1" not in alone


def test_two_standing_and_one_silenced_cross_two_and_no_sentence_for_more(tmp_path):
    labels = (x("X1", BRANCH), x("X2", "The tag is not pushed."), x("X3", LAST, "cooled", "S1"), sx("S1", DROPPED))
    anchors = (("X1", b(1)), ("X2", b(2)), ("X3", b(3)), ("S1", b(3)))
    with framed(tmp_path, his(b(1), b(2), b(3)), labels, anchors, (("S1", "X3"),)):
        made = frame.compose(tmp_path, 9000, session="s1")
        before = frame.compose(tmp_path, 9000)
    assert section(made, frame.PACKED_HEAD) == [
        "- `b0000002`: tove",
        "     ↳ X2 · refused: The tag is not pushed.",
        "- `b0000001`: tove",
        f"     ↳ X1 · refused: {BRANCH}",
    ]
    assert section(before, frame.REFUSED_HEAD) == [
        "- X2 (session): The tag is not pushed. [b0000002]",
        f"- X1 (session): {BRANCH} [b0000001]",
    ]
    for laid in (made, before):
        assert "more refusal" not in laid and "X3" not in laid and "S1" not in laid


def test_a_silenced_family_woken_by_a_judgment_crosses_again_counting_its_refusals_after_the_first(tmp_path):
    with kept_home(tmp_path, b(1), b(2), b(3), b(4), b(5)):
        refuse(tmp_path, BRANCH, b(1))
        silence(tmp_path, DROPPED, "X1", b(2), whose="his")
        quiet = frame.compose(tmp_path, 9000, session="s1")
        woken = refuse(tmp_path, AGAIN, "S1", b(3))  # on the silenced family, by the silencing's key
        assert (woken["id"], woken["beneath"]) == ("X2", ["X1"])
        assert states(tmp_path)["X2"] == ("carried", None) and states(tmp_path)["S1"] == ("cooled", "X2")
        once = frame.compose(tmp_path, 9000, session="s1")
        silence(tmp_path, "Put to rest again.", "X2", b(4))  # S2
        refuse(tmp_path, LAST, "X1", b(5))  # X3: woken again
        twice = frame.compose(tmp_path, 9000, session="s1")
        assert store.refusals(tmp_path) == {"standing": ["X3"], "silenced": []}
    assert "X1" not in quiet and "· refused:" not in quiet
    assert section(once, frame.PACKED_HEAD) == [
        "- `b0000001`: tove",
        "- `b0000003`: tove",
        f"     ↳ X2 · refused: {AGAIN} (judged again once)",
    ]
    assert section(twice, frame.PACKED_HEAD)[-1] == f"     ↳ X3 · refused: {LAST} (judged again 2 times)"


def test_a_silencing_written_by_hand_that_names_no_refusal_is_misaligned_and_shown_with_the_note(tmp_path):
    page = tmp_path / "labels" / f"{DAY}.md"
    page.parent.mkdir()
    w1 = store.digest("The wabe is mapped.")
    page.write_text(
        f"| W1 | The wabe is mapped. | session | `{b(1)}` |\n"
        f"| S1 | Put to rest by hand. | session | `{b(1)}` |\n"  # names no refusal
        f"| S2 | Over the work. | session | `W1@{w1}`, `{b(1)}` |\n"  # names a label of another kind
        f"| W2 | Over a silencing. | session | `S1@{w1}`, `W1@{w1}`, `{b(1)}` |\n",  # the S key passed over
        encoding="utf-8",
    )
    with kept_home(tmp_path, b(1)):
        found = states(tmp_path)
        made = frame.compose(tmp_path, 9000, session="s1")
    assert found == {
        "W1": ("cooled", "W2"),
        "S1": ("misaligned", None),
        "S2": ("misaligned", None),
        "W2": ("carried", None),
    }
    note = " (to be written again: a line beneath it changed)"
    assert section(made, frame.REFUSED_HEAD) == [
        f"- S2 (session): Over the work.{note} [W1, b0000001]",
        f"- S1 (session): Put to rest by hand.{note} [b0000001]",
    ]


def test_the_run_of_a_family_is_given_by_any_of_its_keys_in_order_with_kinds_and_asking_changes_nothing(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    with kept_home(folder, b(1), b(2), b(3), b(4), b(5)), served(folder, project):
        refuse(folder, BRANCH, b(1))
        refuse(folder, AGAIN, "X1", b(2))
        silence(folder, DROPPED, "X2", b(3), whose="his")
        refuse(folder, LAST, "S1", b(4))  # X3: it stands again
        refuse(folder, "The tag is not pushed.", b(5))  # X4, of its own
        silence(folder, "Pushed by hand.", "X4", b(5))  # S2: silenced
        store.build(folder)
        was = files(folder)
        run = [serve.call("labels", {"ids": [key]}) for key in ("X1", "X2", "S1", "X3", "x3")]
        kinds = serve.call("labels", {"kind": "refused"})
        looked, status = serve.call("look", {})[0], serve.call("status", {})[0]
        assert files(folder) == was  # nothing written, and nothing added to the log of pulls
    lines = [
        f"- X1 (refused, session, cooled beneath X3): {BRANCH} [b0000001]",
        f"  - X2 (refused, session, cooled beneath X3): {AGAIN} [X1, b0000002]",
        f"  - S1 (silenced, theirs, cooled beneath X3): {DROPPED} [X1, b0000003]",
        f"  - X3 (refused, session): {LAST} [X1, b0000004]",
    ]
    assert all(each == ("\n".join(lines), False) for each in run)
    assert kinds[0].split("\n") == [
        "- S2 (silenced, session): Pushed by hand. [X4, b0000005]",
        "- X4 (session, cooled beneath S2): The tag is not pushed. [b0000005]",
        f"- X3 (session): {LAST} [X1, b0000004]",
        f"- S1 (silenced, theirs, cooled beneath X3): {DROPPED} [X1, b0000003]",
        f"- X2 (session, cooled beneath X3): {AGAIN} [X1, b0000002]",
        f"- X1 (session, cooled beneath X3): {BRANCH} [b0000001]",
    ]
    assert "; 1 refusal standing (X3), 1 silenced (S2)" in looked
    assert " Of the refusals, 1 stands and 1 is silenced." in status


def test_look_and_status_count_the_silenced_apart_and_say_nothing_where_no_refusal_is(tmp_path):
    folder, project = tmp_path.resolve() / "home", tmp_path.resolve() / "project"
    folder.mkdir()
    with kept_home(folder, b(1), b(2), b(3)), served(folder, project):
        store.mark(folder, "work", "session", "The wabe is mapped.", [b(1)], day=DAY)
        assert "refus" not in serve.call("look", {})[0] and "refus" not in serve.call("status", {})[0]
        refuse(folder, BRANCH, b(1))
        refuse(folder, "The tag is not pushed.", b(2))
        silence(folder, DROPPED, "X1", b(3))
        assert "; 1 refusal standing (X2), 1 silenced (S1)." in serve.call("look", {})[0]
        silence(folder, "Pushed by hand.", "X2", b(3))
        refuse(folder, LAST, b(3))
        assert "; 1 refusal standing (X3), 2 silenced (S1, S2)." in serve.call("look", {})[0]
        assert " Of the refusals, 1 stands and 2 are silenced." in serve.call("status", {})[0]
        refuse(folder, "Nor that.", b(3))
        assert " Of the refusals, 2 stand and 2 are silenced." in serve.call("status", {})[0]
        assert "; 2 refusals standing (X3, X4), 2 silenced (S1, S2)." in serve.call("look", {})[0]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
