"""Two messages whose ids begin with the same eight characters: twins. A twin is printed by a name of its own, the
shortest beginning of its whole id that names it alone, and asked by any beginning of eight characters or more that
names one message; a beginning that names several is refused, each named by its own. A label marked on the eight
characters of one rests on the one the record proves it meant, or on neither, and never moves to the other; a strike
keeps the whole id of the message it took, so that a later twin is kept. On made-up transcripts of two sessions, in a
temporary home. No model, no network.

Run with pytest, or without it:  python3 tests/test_twins.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_serve import said as served  # noqa: E402
from test_store import DATA, switched_on  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import store  # noqa: E402

TAIL = "-0000-4000-8000-000000000000"
A = "30000001-0000-4000-8000-000000000000"  # named 30000001-0 once its twin is there
B = "30000001-1111-4000-8000-000000000000"  # its twin: 30000001-1, or 30000001-1111 beside C
C = "30000001-1112-4000-8000-000000000000"  # a third: 30000001-1112
PASTE = 'Here is what the yard sent.\n\n<pasted_content id="3d0c">\nTwo coats of grey.\n</pasted_content id="3d0c">'


def said(kind: str, whole: str, at: str, text: str) -> dict:
    """A row of a made-up transcript: `at` is the day and the time, as 2026-11-11T09:01."""
    return {
        "type": kind,
        "uuid": whole,
        "timestamp": f"{at}:00.000Z",
        "message": {"role": kind, "content": text if kind == "user" else [{"type": "text", "text": text}]},
    }


def his(whole: str, at: str, text: str) -> dict:
    return said("user", whole, at, text)


def own(whole: str, at: str, text: str) -> dict:
    return said("assistant", whole, at, text)


def made(folder: Path, *sessions: tuple[str, list]) -> Path:
    """A home switched on, with each session's transcript archived in turn, and built."""
    project = folder / "project"
    crossings = project / "crossings"
    crossings.mkdir(parents=True)
    switched_on(project)
    for name, rows in sessions:
        more(crossings, name, rows)
    return crossings


def more(crossings: Path, name: str, rows: list) -> None:
    """A transcript archived into the home, and the index built."""
    path = crossings.parent.parent / f"{name}.jsonl"
    path.write_text("".join(json.dumps(each) + "\n" for each in rows), encoding="utf-8")
    store.archive(path, crossings)
    store.build(crossings)


def door(crossings: Path, *argv: str) -> str:
    """What the door answers the person's shell, without its last line break."""
    return through(argv[0], *argv[1:], "--cwd", str(crossings.parent))[1].rstrip("\n")


def numbered(shown: str) -> list[str]:
    """The ids of a thread's or a pair's numbered entries, in order."""
    return [line.split("`")[1] for line in shown.splitlines() if line[:1].isdigit() and ". `" in line]


def twins(folder: Path) -> Path:
    """A and B, each the person's, each answered; B in another session, said later."""
    return made(
        folder,
        (
            "talk-one-0001",
            [
                his(A, "2026-11-11T09:01", "The hull is grey."),
                own(f"30000002{TAIL}", "2026-11-11T09:02", "Grey it is."),
            ],
        ),
        (
            "talk-two-0001",
            [
                his(B, "2026-11-11T09:05", "The hull is green."),
                own(f"30000003{TAIL}", "2026-11-11T09:06", "Green it is."),
            ],
        ),
    )


# --- names, as they are printed and asked -----------------------------------------------------------------------------


def test_a_twin_is_printed_by_a_name_of_its_own_and_a_message_no_other_shares_by_its_eight(tmp_path):
    """find, thread and a pair print a twin by the shortest beginning of its whole id that names it alone, and every
    other message by its first eight characters, as before."""
    crossings = twins(tmp_path)
    found = door(crossings, "find", "hull")
    assert "- `30000001-0` the person" in found and "- `30000001-1` the person" in found, found
    assert "`30000001` " not in found
    shown = door(crossings, "thread", "30000001-0", "--around", "3")
    assert numbered(shown) == ["30000001-0", "30000002", "30000001-1", "30000003"], shown
    assert "1. `30000001-0` the person, 2026-11-11 09:01 UTC, the one you named:" in shown
    paired = door(crossings, "thread", "30000001-1", "--role", "pair:them")
    assert numbered(paired) == ["30000001-1", "30000003"], paired
    assert "1. `30000001-1` the person, 2026-11-11 09:05 UTC, the one you named:" in paired
    db = store._open(crossings)
    assert [store.name(db, each) for each in (A, B, f"30000002{TAIL}")] == ["30000001-0", "30000001-1", "30000002"]
    db.close()
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        by_server = served("thread", id="30000001-1")[0]
    assert numbered(by_server) == ["30000001-0", "30000002", "30000001-1", "30000003"], by_server


def test_walking_a_long_pair_by_the_pointers_it_prints_passes_a_twin_and_shows_each_message_once(tmp_path):
    """A page's pointer to the next page, and the pair before and after, name a twin by its own name, so that the walk
    goes on through it: the next page is of the same pair, and every message is shown once."""
    long = ["A long account of the hull, plank by plank. " * 112 + f"Part {n}." for n in range(1, 6)]
    first = f"70000001{TAIL}"
    crossings = made(
        tmp_path,
        (
            "walk-one-0001",
            [
                his(first, "2026-11-11T09:01", "Tell me about the hull."),
                own(f"70000002{TAIL}", "2026-11-11T09:02", long[0]),
                own(f"70000003{TAIL}", "2026-11-11T09:03", long[1]),
                own(f"70000004{TAIL}", "2026-11-11T09:04", long[2]),  # where the second page begins
                own(f"70000005{TAIL}", "2026-11-11T09:05", long[3]),
                own(f"70000006{TAIL}", "2026-11-11T09:06", long[4]),
                his(f"70000007{TAIL}", "2026-11-11T09:07", "Thank you."),
            ],
        ),
        (
            "walk-two-0001",
            [
                his("70000001-3333-4000-8000-000000000000", "2026-11-11T09:10", "Another session."),
                own("70000004-1111-4000-8000-000000000000", "2026-11-11T09:11", "A twin of the second page's start."),
            ],
        ),
    )
    seen, at, pages = [], "70000001-0", 0
    while at:
        shown = door(crossings, "thread", at, "--role", "pair:them")
        assert "messages are named" not in shown and "no such message" not in shown, shown
        seen += [line.split(".")[0] for line in shown.splitlines() if line[:1].isdigit() and ". `" in line]
        further = [line for line in shown.splitlines() if "goes on from there" in line]
        at = further[0].split("thread of `")[1].split("`")[0] if further else ""
        pages += 1
        assert pages < 6
    assert seen == ["1", "2", "3", "4", "5", "6"] and pages == 3, (seen, pages)
    assert "thread of `70000004-0` with the role `pair:them` goes on from there." in door(
        crossings, "thread", "70000001-0", "--role", "pair:them"
    )
    answer = door(crossings, "thread", "70000002", "--role", "pair:me")
    assert "The pair before this one begins at `70000001-0`, and the pair after it at `70000007`" in answer, answer
    assert numbered(door(crossings, "thread", "70000001-3", "--role", "pair:them"))[0] == "70000001-3"


def test_a_beginning_that_names_several_messages_is_refused_naming_each_by_its_own_and_never_answered_with_the_first(
    tmp_path,
):
    crossings = twins(tmp_path)
    nine = door(crossings, "thread", "30000001-")
    assert nine == (
        "thread of `30000001-`: two messages are named `30000001-`, `30000001-0` and `30000001-1`; thread with one of "
        "them gives that one."
    ), nine
    assert door(crossings, "thread", "30000001-", "--role", "pair:me") == nine
    assert store.thread(crossings, "30000001")["twins"] == ["30000001-0", "30000001-1"]
    more(crossings, "talk-three-0001", [his(C, "2026-11-11T09:20", "The hull is blue.")])
    two = door(crossings, "thread", "30000001-1")
    assert two == (
        "thread of `30000001-1`: two messages are named `30000001-1`, `30000001-1111` and `30000001-1112`; thread with "
        "one of them gives that one."
    ), two
    three = door(crossings, "thread", "30000001")
    assert three.startswith(
        "thread of `30000001`: 3 messages are named `30000001`, `30000001-0`, `30000001-1111` and `30000001-1112`"
    ), three
    assert "the one you named" in door(crossings, "thread", "30000001-1112")


def test_the_lookup_of_an_id_is_a_search_on_the_index_and_no_scan_of_its_messages(tmp_path):
    crossings = twins(tmp_path)
    db = store._open(crossings)
    asked: list[str] = []
    db.set_trace_callback(asked.append)
    for each in ("30000001", "30000001-1", A, "30000002", "30000001-1+1"):
        store._named_row(db, each)
    db.set_trace_callback(None)
    plans = [detail for sql in asked for *_, detail in db.execute("explain query plan " + sql)]
    assert asked and not [plan for plan in plans if plan.startswith("SCAN")], plans
    db.close()


def test_fewer_than_eight_characters_name_no_message(tmp_path):
    crossings = twins(tmp_path)
    for asked in ("3000000", "300", "30000002"[:7]):
        assert door(crossings, "thread", asked) == f"thread of `{asked}`: no such message in the store."
        assert (
            door(crossings, "thread", asked, "--role", "pair:them")
            == f"thread of `{asked}`: no such message in the store."
        )
    assert numbered(door(crossings, "thread", "30000002"))  # eight that one message holds names it, as ever


def test_a_text_pasted_into_a_twin_is_named_by_the_twins_name_and_its_number(tmp_path):
    crossings = made(
        tmp_path,
        ("talk-one-0001", [his(A, "2026-11-11T09:01", PASTE), own(f"30000002{TAIL}", "2026-11-11T09:02", "Noted.")]),
        ("talk-two-0001", [his(B, "2026-11-11T09:05", PASTE), own(f"30000003{TAIL}", "2026-11-11T09:06", "Noted.")]),
    )
    paired = door(crossings, "thread", "30000001-1", "--role", "pair:them")
    assert "into it, not shown here: `30000001-1+1` (" in paired, paired
    shared = door(crossings, "thread", "30000001+1")
    assert shared == (
        "thread of `30000001+1`: two messages are named `30000001+1`, `30000001-0+1` and `30000001-1+1`; thread with "
        "one of them gives that one."
    ), shared
    one = door(crossings, "thread", "30000001-1+1")
    assert [line.split("`")[1] for line in one.splitlines() if "the one you named" in line] == ["30000001-1+1"], one
    assert numbered(one) == ["30000002", "30000001-1", "30000001-1+1", "30000003"], one
    assert store.tied(crossings, "30000001-0+1", store.HIS)["head"][0]["pastes"][0]["is_asked"]
    assert door(crossings, "thread", "30000001-1+2") == "thread of `30000001-1+2`: no such message in the store."


def test_a_pasted_texts_number_is_digits_alone_and_any_other_names_no_text(tmp_path):
    """A text pasted into a message is named by the message's id and its number, which is ASCII digits alone: a
    letter, nothing, a digit of another script or a second number after the plus names no message."""
    crossings = made(
        tmp_path,
        ("talk-one-0001", [his(A, "2026-11-11T09:01", PASTE), own(f"30000002{TAIL}", "2026-11-11T09:02", "Noted.")]),
    )
    one = door(crossings, "thread", "30000001+1")
    assert [line.split("`")[1] for line in one.splitlines() if "the one you named" in line] == ["30000001+1"], one
    for asked in ("30000001+x", "30000001+", "30000001+\uff11", "30000001+1+1"):
        assert door(crossings, "thread", asked) == f"thread of `{asked}`: no such message in the store.", asked
        assert store.thread(crossings, asked) == {"asked": asked, "found": False, "said": [], "labels": []}, asked


def test_a_whole_id_names_its_own_message_also_where_it_begins_another(tmp_path):
    longer, shorter = "c3c3c3c3-0000-4000-8000-000000000000", "c3c3c3c3-0000"
    crossings = made(
        tmp_path,
        (
            "talk-one-0001",
            [
                his(longer, "2026-11-11T09:01", "The longer id, said first."),
                his(shorter, "2026-11-11T09:02", "The shorter."),
            ],
        ),
    )
    db = store._open(crossings)
    assert store.name(db, shorter) == shorter and store.name(db, longer) == "c3c3c3c3-0000-"
    db.close()
    assert store._named_row(store._open(crossings), shorter)[1]["text"] == "The shorter."
    by_short = door(crossings, "thread", shorter)
    named = [line for line in by_short.splitlines() if "the one you named" in line]
    assert named == ["2. `c3c3c3c3-0000` the person, 2026-11-11 09:02 UTC, the one you named:"], by_short
    assert "1. `c3c3c3c3-0000-` the person, 2026-11-11 09:01 UTC, the one you named:" in door(
        crossings, "thread", "c3c3c3c3-0000-"
    )


# --- a label never moves to the other twin ----------------------------------------------------------------------------


def labelled(folder: Path, b_at: str, reached: str | None) -> Path:
    """A, then W1 marked on its eight characters on a page of A's day, then B, said at `b_at`: a twin archived after
    the mark, from another session. `reached` is the mark's moment in the log of what was pulled, where there is one."""
    crossings = made(folder, ("talk-one-0001", [his(A, "2026-11-11T09:01", "The hull is grey.")]))
    assert store.mark(crossings, "work", "session", "The hull is to be grey.", ["30000001"], day="2026-11-11")[
        "written"
    ]
    if reached is not None:
        (crossings / "reached.jsonl").write_text(
            json.dumps({"at": reached, "verb": "mark", "ids": ["W1", "30000001"]}) + "\n", encoding="utf-8"
        )
    more(crossings, "talk-two-0001", [his(B, b_at, "The hull is green.")])
    return crossings


def resting_on(crossings: Path, asked: str) -> list[str]:
    """The labels a thread shows resting on the message asked."""
    line = next(line for line in door(crossings, "thread", asked).splitlines() if "the one you named" in line)
    return line.split("(labels: ")[1].rstrip("):").split(", ") if "(labels: " in line else []


def quoted(crossings: Path) -> list[str]:
    return [line for line in store_frame(crossings).splitlines() if line.startswith("- `")]


def store_frame(crossings: Path) -> str:
    from crossing import frame

    return frame.compose(crossings)


def state(crossings: Path, key: str) -> str:
    db = store._open(crossings)
    try:
        return db.execute("select state from label where id = ?", (key,)).fetchone()[0]
    finally:
        db.close()


def rested(crossings: Path) -> list[tuple]:
    """What each anchor rests on as the index holds it: the label, the anchor, the whole id it rests on ("" where the
    record cannot tell, None where no message held can be it), and 1 where a twin struck may be it."""
    db = store._open(crossings)
    try:
        return [tuple(r) for r in db.execute("select label, said, uuid, gone from anchor order by label, said")]
    finally:
        db.close()


def test_a_label_rests_on_the_twin_said_before_it_and_a_twin_said_after_its_day_never_takes_it(tmp_path):
    """B was said days after the page W1 was marked on: W1 can only be about A. It stays on A, and when A is struck it
    rests on what the archive no longer holds, and B is never quoted for it."""
    crossings = labelled(tmp_path, "2026-11-14T09:00", None)
    assert resting_on(crossings, "30000001-0") == ["W1"] and resting_on(crossings, "30000001-1") == []
    assert door(crossings, "labels", "W1").endswith("The hull is to be grey. [30000001 (30000001-0)]")
    assert state(crossings, "W1") == "carried"
    assert through("strike", A, "--cwd", str(crossings.parent))[0] == 0
    assert state(crossings, "W1") == "unresolved" and resting_on(crossings, "30000001") == []
    assert not [line for line in quoted(crossings) if "green" in line]


def test_the_marks_moment_tells_a_twin_said_the_same_day_after_it_and_without_it_the_label_rests_on_neither(tmp_path):
    proven = labelled(tmp_path / "proven", "2026-11-11T11:00", "2026-11-11T10:00:00+00:00")
    assert resting_on(proven, "30000001-0") == ["W1"] and resting_on(proven, "30000001-1") == []
    told = labelled(tmp_path / "told", "2026-11-11T11:00", None)  # the page's day alone cannot tell
    assert resting_on(told, "30000001-0") == [] and resting_on(told, "30000001-1") == []
    assert door(told, "labels", "W1").endswith("The hull is to be grey. [30000001 (30000001-0 or 30000001-1)]")
    assert state(told, "W1") == "carried" and quoted(told) == []


def test_a_label_the_record_cannot_tell_rests_on_neither_twin_and_a_strike_of_one_never_moves_it_to_the_other(tmp_path):
    """B was said before W1 was marked, and archived after it, from a session read later: either could be what W1
    meant. It rests on neither, is carried by its sentence, and stays so when one of them is struck."""
    crossings = labelled(tmp_path, "2026-11-11T09:30", "2026-11-11T10:00:00+00:00")
    assert resting_on(crossings, "30000001-0") == [] and resting_on(crossings, "30000001-1") == []
    assert state(crossings, "W1") == "carried" and quoted(crossings) == []
    assert through("strike", A, "--cwd", str(crossings.parent))[0] == 0
    assert resting_on(crossings, "30000001") == [] and state(crossings, "W1") == "carried"
    assert not [line for line in quoted(crossings) if "green" in line], quoted(crossings)
    assert door(crossings, "labels", "W1").endswith("[30000001 (30000001 or one struck)]")


def test_a_label_marked_on_the_eight_characters_of_a_struck_twin_rests_where_a_whole_build_finds_it(tmp_path):
    """B is struck by its whole id, and W1 is marked on the eight characters it shared with A. The mark adds no row
    of its own to the index, which would rest W1 on A: the index is made whole, and W1 rests where a whole build finds
    it, on neither, since the record cannot tell A from a twin struck, whose time it no longer holds."""
    crossings = made(
        tmp_path,
        ("talk-one-0001", [his(A, "2026-11-11T09:01", "The hull is grey.")]),
        ("talk-two-0001", [his(B, "2026-11-11T09:05", "The hull is green.")]),
    )
    assert through("strike", B, "--cwd", str(crossings.parent))[0] == 0
    assert store.mark(crossings, "work", "session", "The hull is to be grey.", ["30000001"], day="2026-11-11")[
        "written"
    ]
    marked = rested(crossings)
    assert marked == [("W1", "30000001", "", 1)], marked
    assert state(crossings, "W1") == "carried" and resting_on(crossings, "30000001") == []
    assert door(crossings, "labels", "W1").endswith("The hull is to be grey. [30000001 (30000001 or one struck)]")
    store.build(crossings)
    assert rested(crossings) == marked


# --- a strike writes the whole id ------------------------------------------------------------------------------------


def test_a_strike_writes_the_whole_id_and_a_later_message_that_shares_eight_characters_is_kept(tmp_path):
    first, later = f"40000001{TAIL}", "40000001-2222-4000-8000-000000000000"
    crossings = made(tmp_path, ("talk-one-0001", [his(first, "2026-11-11T09:01", "A message to be struck.")]))
    code, out = through("strike", "40000001", "--cwd", str(crossings.parent))
    assert code == 0 and out.startswith("struck 40000001:"), out
    assert (crossings / "struck.txt").read_text(encoding="utf-8").splitlines() == [f"{first}  # of 40000001"]
    more(crossings, "talk-two-0001", [his(later, "2026-11-11T09:05", "A later message, sharing the eight.")])
    assert [row["uuid"] for row in store._archived(crossings)] == [later]
    assert "A later message" in door(crossings, "thread", "40000001")


def test_an_old_strike_of_eight_characters_still_hides_a_later_message_that_shares_them(tmp_path):
    """Guard: a line of eight characters written before stands for a message whose whole id was not kept, and cannot
    be told from a later one: it keeps hiding every message that begins so."""
    crossings = made(tmp_path, ("talk-one-0001", [his(f"40000009{TAIL}", "2026-11-11T09:01", "Another, kept.")]))
    (crossings / "struck.txt").write_text("40000001  # struck before\n", encoding="utf-8")
    more(crossings, "talk-two-0001", [his("40000001-2222-4000-8000-000000000000", "2026-11-11T09:05", "Hidden.")])
    assert [row["uuid"] for row in store._archived(crossings)] == [f"40000009{TAIL}"]


def test_a_strike_of_one_twin_leaves_the_other_its_flag_and_its_pulls(tmp_path):
    keyed, plain = f"50000001{TAIL}", "50000001-3333-4000-8000-000000000000"
    crossings = made(tmp_path, ("talk-one-0001", [his(keyed, "2026-11-11T09:01", "password=hunter22hunter22 is it")]))
    assert store.flagged(crossings) == ["50000001"]
    store.reached(crossings, "thread", ["50000001"])  # the keyed one, pulled while it was the only one so named
    more(crossings, "talk-two-0001", [his(plain, "2026-11-11T09:05", "An ordinary message.")])
    store.reached(crossings, "thread", ["50000001-3"])  # the plain one, by its own name
    assert through("strike", plain, "--cwd", str(crossings.parent))[0] == 0
    assert store.flagged(crossings) == ["50000001"]
    pulls = [json.loads(line)["ids"] for line in (crossings / "reached.jsonl").read_text().splitlines()]
    assert pulls == [["50000001"]], pulls
    assert (crossings / "struck.txt").read_text(encoding="utf-8").splitlines() == [f"{plain}  # of {plain}"]
    assert through("strike", keyed, "--cwd", str(crossings.parent))[0] == 0
    assert store.flagged(crossings) == [] and not (crossings / "reached.jsonl").read_text().strip()


def test_a_strike_names_the_labels_resting_on_what_it_took_and_not_those_proven_to_rest_on_the_other_twin(tmp_path):
    crossings = labelled(tmp_path, "2026-11-14T09:00", None)
    code, out = through("strike", B, "--cwd", str(crossings.parent))
    assert code == 0 and "W1" not in out, out
    assert "W1" in through("strike", A, "--cwd", str(crossings.parent))[1]


def test_a_strike_names_a_row_written_by_hand_since_the_index_was_made_by_its_eight_characters_alone(tmp_path):
    """Two rows written on W1's page by hand after the last build, which the index does not hold: a strike of A names
    W1, which the index found resting on A, and the row whose anchor is A's eight characters, and not the row on
    eight characters of no message it took."""
    crossings = labelled(tmp_path, "2026-11-14T09:00", None)
    page = crossings / "labels" / "2026-11-11.md"
    page.write_text(
        page.read_text(encoding="utf-8")
        + "| W2 | Written by hand on another. | session | `30000009` |\n"
        + "| W3 | Written by hand on its eight. | session | `30000001` |\n",
        encoding="utf-8",
    )
    code, out = through("strike", A, "--cwd", str(crossings.parent))
    assert code == 0 and "The labels that rest on what was struck stay as they are: W1, W3." in out, out


# --- the work of it grows with what there is, not with its square -----------------------------------------------------


def laid_by_hand(folder: Path, said: list[dict], page: str, struck: str = "") -> Path:
    """A home whose archive, label page and struck ids are written by hand, as an import or an old make may leave
    them; not built."""
    project = folder / "project"
    crossings = project / "crossings"
    (crossings / "said").mkdir(parents=True)
    (crossings / "labels").mkdir()
    switched_on(project)
    (crossings / "said" / "talk-one.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in said), encoding="utf-8"
    )
    (crossings / "labels" / "2026-11-11.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n" + page
    )
    if struck:
        (crossings / "struck.txt").write_text(struck, encoding="utf-8")
    return crossings


def test_a_build_finds_the_struck_twins_of_an_anchor_in_one_step_however_many_ids_were_struck(tmp_path):
    """Guard: a build compared every anchor of every label with every whole id struck: with a hundred labels on one
    message and a hundred and one ids struck it made 10,100 comparisons, and 40,200 with two hundred and two hundred
    and one, four times as many for twice as much. It finds the ids struck under an anchor's eight characters in one
    step now: one comparison an anchor, for the one twin struck under it, at either size. What each anchor rests on is
    as before: on neither, the record cannot tell it from the twin struck."""
    message = "71000001-0000-4000-8000-000000000000"
    row = {"uuid": message, "id": message[:8], "session": "talk-one", "voice": "his", "at": "2026-11-11T09:01:00.000Z"}
    counted: list[int] = []

    class Struck(str):
        def startswith(self, *args):  # a whole id struck, compared with an anchor
            counted.append(1)
            return super().startswith(*args)

    real = store.struck
    for n in (100, 200):
        page = "".join(f"| W{k} | Work {k}. | session | `71000001` |\n" for k in range(1, n + 1))
        struck = "71000001-1111-4000-8000-000000000000  # a twin of the message, struck\n" + "".join(
            f"{0x80000000 + k:08x}-0000-4000-8000-000000000000  # struck\n" for k in range(n)
        )
        crossings = laid_by_hand(tmp_path / str(n), [{**row, "text": "One message."}], page, struck)
        counted.clear()
        store.struck = lambda folder: {Struck(token) for token in real(folder)}
        try:
            store.build(crossings)
        finally:
            store.struck = real
        assert len(counted) == n, (n, len(counted))
        db = store._open(crossings)
        try:
            rested = [tuple(r) for r in db.execute("select distinct said, uuid, gone from anchor")]
            assert rested == [("71000001", "", 1)], rested
        finally:
            db.close()


def test_the_messages_under_one_beginning_are_named_in_one_pass(tmp_path):
    """Guard: each name of a twin was made by comparing it with every other message under its eight characters, and
    an id that names them all asked for every name: a hundred twins took 9,900 comparisons in `thread` and as many
    in `labels` for a label on their eight characters, and two hundred 39,800, four times as many for twice as many.
    The names of all messages under one beginning are made in one pass now, one comparison for each two that stand
    side by side in the order of their whole ids, and they are the names they were."""
    real, counted = os.path.commonprefix, []

    def common(parts):
        counted.append(1)
        return real(parts)

    for n in (100, 200):
        said = [
            {"uuid": f"81000000-{k:04d}-4000-8000-{k:012d}", "id": "81000000", "session": "talk-one", "voice": "his",
             "at": f"2026-11-11T09:{k % 60:02d}:00.000Z", "text": f"Twin {k}."}
            for k in range(n)
        ]  # fmt: skip
        crossings = laid_by_hand(tmp_path / str(n), said, "| W1 | On all of them. | session | `81000000` |\n")
        store.build(crossings)
        names = [f"81000000-{k:04d}" for k in range(n)]
        os.path.commonprefix = common
        try:
            counted.clear()
            assert store.thread(crossings, "81000000")["twins"] == names
            assert len(counted) == n - 1, (n, "thread", len(counted))
            counted.clear()
            shown = store.listed(crossings, ids=("W1",))["labels"][0]["shown"]["81000000"]
            assert len(counted) == n - 1, (n, "labels", len(counted))
        finally:
            os.path.commonprefix = real
        assert shown == f"81000000 ({', '.join(names[:-1])} or {names[-1]})"


# --- a page, a log and struck ids written by hand ----------------------------------------------------------------------

LATER = {
    "uuid": f"71000001{TAIL}",
    "id": "71000001",
    "session": "talk-one",
    "voice": "his",
    "at": "2026-11-14T09:01:00.000Z",
    "text": "Said days after the page.",
}  # the one message the archive holds under W1's eight characters
ON_IT = "| W1 | Work. | session | `71000001` |\n"
STRUCK = "".join(f"71000001-{k * 4}-4000-8000-000000000000  # a twin, struck\n" for k in "12")


def test_a_label_whose_every_twin_that_may_be_it_is_struck_rests_on_what_the_archive_no_longer_holds(tmp_path):
    """The one message the archive holds under W1's eight characters was said days after W1's page, and is not what
    W1 rests on; two twins struck by their whole ids may be. Whichever it was, the archive no longer holds it: W1
    rests on what it no longer holds, as it does with one twin struck, or with no message held under them."""
    for name, said, gone in (
        ("two", [LATER], STRUCK),
        ("one", [LATER], STRUCK.splitlines(True)[0]),
        ("none", [], STRUCK),
    ):
        crossings = laid_by_hand(tmp_path / name, said, ON_IT, gone)
        store.build(crossings)
        assert rested(crossings) == [("W1", "71000001", None, 1)], name
        assert state(crossings, "W1") == "unresolved", name
        assert door(crossings, "labels", "W1") == "- W1 (session, unresolved): Work. [71000001]", name


def test_a_label_on_a_page_whose_name_is_no_date_is_bound_by_no_day_and_rests_on_neither_twin(tmp_path):
    """On the page of a day, the message held under W1's eight characters, said days later, cannot be what W1 rests
    on, and a twin struck is: W1 rests on what the archive no longer holds. On a page whose name has the shape of a
    day and is no date (a thirteenth month), no day ends it: the record cannot tell the two apart, and W1 rests on
    neither, carried by its sentence."""
    gone = STRUCK.splitlines(True)[0]
    dated = laid_by_hand(tmp_path / "dated", [LATER], ON_IT, gone)
    store.build(dated)
    assert rested(dated) == [("W1", "71000001", None, 1)] and state(dated, "W1") == "unresolved"
    undated = laid_by_hand(tmp_path / "undated", [LATER], "", gone)
    (undated / "labels" / "2026-13-45.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n" + ON_IT, encoding="utf-8"
    )
    store.build(undated)
    assert rested(undated) == [("W1", "71000001", "", 1)] and state(undated, "W1") == "carried"
    assert door(undated, "labels", "W1") == "- W1 (session): Work. [71000001 (71000001 or one struck)]"


def test_the_marks_moment_is_read_from_the_marks_own_line_and_one_that_cannot_be_read_gives_none(tmp_path):
    """Before the mark's own line, the log of what was pulled holds a line of another verb naming W1 first at a later
    moment, a mark naming no id and a line that is no pull: each is passed over, and the mark's own moment proves W1
    on A, said before it, and not on B, said after it. A mark whose moment cannot be read gives none: W1 is told by
    its page's day alone, which holds both, and rests on neither."""
    log = [
        json.dumps({"at": "2026-11-11T12:00:00+00:00", "verb": "thread", "ids": ["W1", "30000001"]}),
        json.dumps({"at": "2026-11-11T12:00:00+00:00", "verb": "mark", "ids": []}),
        "not a pull",
        json.dumps({"at": "2026-11-11T10:00:00+00:00", "verb": "mark", "ids": ["W1", "30000001"]}),
    ]
    proven = labelled(tmp_path / "proven", "2026-11-11T11:00", None)
    (proven / "reached.jsonl").write_text("".join(line + "\n" for line in log), encoding="utf-8")
    store.build(proven)
    assert resting_on(proven, "30000001-0") == ["W1"] and resting_on(proven, "30000001-1") == []
    unread = labelled(tmp_path / "unread", "2026-11-11T11:00", None)
    (unread / "reached.jsonl").write_text(
        json.dumps({"at": "not a moment", "verb": "mark", "ids": ["W1", "30000001"]}) + "\n", encoding="utf-8"
    )
    store.build(unread)
    assert resting_on(unread, "30000001-0") == [] and resting_on(unread, "30000001-1") == []
    assert door(unread, "labels", "W1").endswith("The hull is to be grey. [30000001 (30000001-0 or 30000001-1)]")


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            # In the tests' own data folder, which test_store sweeps as the run ends.
            test(Path(tempfile.mkdtemp(prefix="crossing-test-", dir=DATA)))
            print("ok", name)
