"""Labels that rest on labels, and the four states a label can be in: marking a stack and the
refusals, what a build makes of the plain pages, the room, the listing, the frame, undoing, and
what a session is told. No model, no network.

Run with pytest, or without it:  python3 tests/test_stacks.py
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to  # noqa: E402
from test_store import A, B, D, E, at_terminal, home, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, handover, serve, store  # noqa: E402

DAY = "2026-11-12"
HEAD = "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
TERN = "His boat is called Tern and lies at mooring 41."  # R1 of the page every home starts with
KEEL, SAILS = "The keel is checked every autumn.", "The sails are stowed dry."
MAST, RIGGING = "The mast was stepped again.", "The rigging was tuned."
CARE, GEAR, SPARS = (
    "Tern is kept with care the year round.",
    "The boat and all her gear are looked after.",
    "The spars are done.",
)
AGAIN, ALOFT = "Tern and her keel are kept with care.", "All that is aloft is done."
ASKS = re.compile(r"\bask(s|ed|ing)?\b", re.I)


def through(*argv: str) -> tuple[int, str]:
    """The door, in this process."""
    out = io.StringIO()
    with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
        code = door.main(list(argv))
    return code, out.getvalue()


def said(name: str, **given) -> tuple[str, bool]:
    """One call of a handle of the server's: the text that comes back, and whether it failed."""
    # A session a person sits in, unless the test says how the session was started (see serve.call).
    with started_by(os.environ.get("CLAUDE_CODE_ENTRYPOINT") or "cli"):
        answer = serve.handle(
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name, "arguments": given}}
        )
    return answer["result"]["content"][0]["text"], answer["result"]["isError"]


def digest(sentence: str) -> str:
    return hashlib.sha256(sentence.encode("utf-8")).hexdigest()[:6]


def lined(folder: Path) -> Path:
    """A home with three standing lines and three about the work, each on messages the archive
    holds: R1 on A and B, R2 on D, R3 on A; W1 on D and E, W2 on A, W3 on E."""
    crossings, _ = home(folder)
    for kind, whose, sentence, anchor in (
        ("relation", "his", KEEL, D),
        ("relation", "his", SAILS, A),
        ("work", "both", MAST, A),
        ("work", "both", RIGGING, E),
    ):
        assert store.mark(crossings, kind, whose, sentence, [anchor], day=DAY)["written"]
    return crossings


def stack(crossings: Path, kind: str, sentence: str, anchors: list[str]) -> dict:
    return store.mark(crossings, kind, "his" if kind == "relation" else "both", sentence, anchors, day=DAY)


def states(crossings: Path) -> dict[str, str]:
    """Every label's state by its key, as the store gives it."""
    return {
        label["id"]: label["state"]
        for kind in ("relation", "work", "next")
        for label in store.listed(crossings, kind, limit=1000)["labels"]
    }


def reworded(crossings: Path, was: str, now: str) -> None:
    """A sentence changed in its plain page by hand, and the store built again."""
    page = crossings / "labels" / f"{DAY}.md"
    page.write_text(page.read_text(encoding="utf-8").replace(was, now), encoding="utf-8")
    store.build(crossings)


# --- a label that rests on labels --------------------------------------------------------------


def test_a_label_may_rest_on_labels_and_every_line_beneath_stays_whole_in_its_page(tmp_path):
    crossings = lined(tmp_path)
    first = (crossings / "hand-over.md").read_text(encoding="utf-8")
    out = stack(crossings, "relation", CARE, ["R1", "r2", f"`{D}`", "R2"])  # a key in either case, and named once
    assert (out["written"], out["id"], out["beneath"], out["anchors"]) == (True, "R4", ["R1", "R2"], [D])
    page = (crossings / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
    assert f"| R4 | {CARE} | his | `R1@{digest(TERN)}`, `R2@{digest(KEEL)}`, `{D}` |\n" in page
    # Nothing is lost by stacking: each line beneath is still in its page, whole.
    assert (
        f"| R2 | {KEEL} | his | `{D}` |\n" in page and (crossings / "hand-over.md").read_text(encoding="utf-8") == first
    )
    by_key = {label["id"]: label for label in store.labels(crossings)}
    assert by_key["R4"]["beneath"] == [("R1", digest(TERN)), ("R2", digest(KEEL))] and by_key["R4"]["anchors"] == [D]
    assert by_key["R1"]["beneath"] == [] and by_key["R1"]["anchors"] == [A, B]
    db = sqlite3.connect(crossings / "store.db")
    assert dict(db.execute("select id, parent from label where kind = 'relation'")) == {
        "R1": "R4",
        "R2": "R4",
        "R3": None,
        "R4": None,
    }
    assert db.execute("select stack, line, digest from beneath").fetchall() == [
        ("R4", "R1", digest(TERN)),
        ("R4", "R2", digest(KEEL)),
    ]
    db.close()
    alone = stack(crossings, "work", SPARS, ["w2", "W3"])  # on labels alone, with no message of its own
    assert alone["written"] and alone["id"] == "W4" and alone["anchors"] == []
    assert f"| W4 | {SPARS} | both | `W2@{digest(MAST)}`, `W3@{digest(RIGGING)}` |\n" in (
        crossings / "labels" / f"{DAY}.md"
    ).read_text(encoding="utf-8")
    assert stack(crossings, "relation", GEAR, ["R4", "R3"])["id"] == "R5"  # a stack may stand over a stack


def test_a_stack_that_breaks_a_rule_is_refused_in_one_sentence_and_nothing_is_written(tmp_path):
    crossings = lined(tmp_path)
    assert store.mark(crossings, "next", "session", "The mooring is next.", [A], day=DAY)["id"] == "N1"
    assert stack(crossings, "relation", CARE, ["R1", "R2"])["id"] == "R4"
    assert stack(crossings, "relation", GEAR, ["R4", "R3"])["id"] == "R5"  # two levels, the deepest there is
    store.strike(crossings, "W3")
    pages = {page: page.read_text(encoding="utf-8") for page in store.pages(crossings)}
    held = store.status(crossings)["labels"]
    refused = {
        "a label that is not there": stack(crossings, "work", SPARS, ["W2", "W99"]),
        "a label that was struck": stack(crossings, "work", SPARS, ["W2", "W3"]),
        "a standing line beneath the work": stack(crossings, "work", SPARS, ["W2", "R5"]),
        "a work label beneath a standing line": stack(crossings, "relation", CARE, ["R5", "W1"]),
        "a line left at the door beneath a stack": stack(crossings, "work", SPARS, ["W2", "N1"]),
        "a line left at the door as a stack": store.mark(
            crossings, "next", "session", "The spars are next.", ["W2", A], day=DAY
        ),
        "a line beneath another stack already": stack(crossings, "relation", CARE, ["R1", "R5"]),
        "a third level": stack(crossings, "relation", CARE, ["R5"]),
    }
    for what, out in refused.items():
        assert out["written"] is False and set(out) == {"written", "why"}, what
        why = out["why"]
        assert "\n" not in why and why.count(". ") == 0 and not ASKS.search(why) and "/" not in why, what
    assert refused["a label that is not there"]["why"] == "no such label: W99"
    assert refused["a label that was struck"]["why"] == "no such label: W3"
    assert (
        "R5" in refused["a standing line beneath the work"]["why"]
        and "kind" in refused["a standing line beneath the work"]["why"]
    )
    assert (
        "W1" in refused["a work label beneath a standing line"]["why"]
        and "R5" not in refused["a work label beneath a standing line"]["why"]
    )
    assert (
        "N1" in refused["a line left at the door beneath a stack"]["why"]
        and "kind" in refused["a line left at the door beneath a stack"]["why"]
    )
    assert "left at the door" in refused["a line left at the door as a stack"]["why"]
    assert refused["a line beneath another stack already"]["why"].startswith("R1 already stands beneath R4")
    assert refused["a third level"]["why"].startswith("R5 already stands over stacks")
    assert {page: page.read_text(encoding="utf-8") for page in store.pages(crossings)} == pages
    assert store.status(crossings)["labels"] == held
    # A message the archive does not hold is refused as before, beside labels that are there.
    assert (
        stack(crossings, "work", SPARS, ["W1", "W2", "0a0a0a0a"])["why"] == "no such message in the archive: 0a0a0a0a"
    )


def test_the_six_characters_beside_a_line_are_never_taken_for_a_message(tmp_path):
    """A message's id has eight characters and a digest six, so that neither is read as the
    other; and a digest of digits alone is no line's number in an early page's table."""
    crossings, _ = home(tmp_path)
    (crossings / "labels").mkdir()
    (crossings / "labels" / f"{DAY}.md").write_text(
        HEAD + f"| R2 | A line over the first, in a page written by hand. | his | `R1@123456`, `{D}` |\n"
        "| R3 | Another, whose digest has letters alone. | his | `R1@abcdef` |\n"
        "| R4 | One that names the same line twice. | his | `R1@aaaaaa`, `R1@bbbbbb` |\n"
        "| R5 | One that names a line with eight characters after its key. | his | `R1@1a2b3c4d` |\n\n"
        f"| Line | Id | Voice |\n| --- | --- | --- |\n| 123456 | `{E}` | the session's |\n",
        encoding="utf-8",
    )
    by_key = {label["id"]: label for label in store.labels(crossings)}
    assert by_key["R2"]["beneath"] == [("R1", "123456")] and by_key["R2"]["anchors"] == [
        D
    ]  # and not E, by the table of lines
    assert by_key["R3"]["beneath"] == [("R1", "abcdef")] and by_key["R3"]["anchors"] == []
    assert by_key["R4"]["beneath"] == [("R1", "aaaaaa")]
    assert by_key["R5"]["beneath"] == []  # eight characters are no digest
    assert handover.named(f"| R6 | A stack. | his | `R1@1a2b3c`, `R2@123456`, `W12@abcdef`, `{D}` |") == [D]
    assert store.ROW.match(f"| R6 | A stack. | his | `R1@1a2b3c`, `{D}` |").group(4) == f"`R1@1a2b3c`, `{D}`"
    made = stack(crossings, "work", "A stack marked here is read back as it was written.", ["W1"])
    read = [label for label in store.labels(crossings) if label["id"] == made["id"]][0]
    assert read["beneath"] == [("W1", digest("The hull is to be painted grey in spring."))] and read["anchors"] == []


# --- the four states -----------------------------------------------------------------------------


def test_every_label_has_one_of_four_states_and_a_build_makes_them_from_the_pages_alone(tmp_path):
    crossings = lined(tmp_path)
    assert set(states(crossings).values()) == {"carried"}
    assert store.status(crossings)["states"] == {"carried": 6, "cooled": 0, "misaligned": 0, "unresolved": 0}
    stack(crossings, "relation", CARE, ["R1", "R2"])
    stood = {
        "R1": "cooled",
        "R2": "cooled",
        "R3": "carried",
        "R4": "carried",
        "W1": "carried",
        "W2": "carried",
        "W3": "carried",
    }
    assert states(crossings) == stood
    assert store.status(crossings)["states"] == {"carried": 5, "cooled": 2, "misaligned": 0, "unresolved": 0}
    stack(
        crossings, "relation", GEAR, ["R4", "R3"]
    )  # the top of a stack of stacks is carried, and all beneath it cooled
    stood.update({"R3": "cooled", "R4": "cooled", "R5": "carried"})
    assert states(crossings) == stood
    (crossings / "store.db").unlink()  # parents, digests and states are all made again from the plain pages
    assert states(crossings) == stood
    store.build(crossings)  # a read made them in memory; a build puts them on disk
    db = sqlite3.connect(crossings / "store.db")
    assert dict(db.execute("select id, parent from label where parent is not null")) == {
        "R1": "R4",
        "R2": "R4",
        "R3": "R5",
        "R4": "R5",
    }
    db.close()


def test_a_stack_whose_line_changed_or_is_gone_is_misaligned_and_its_lines_are_carried(tmp_path):
    crossings = lined(tmp_path)
    stack(crossings, "relation", CARE, ["R1", "R2"])
    stack(crossings, "work", SPARS, ["W2", "W3"])
    reworded(crossings, "checked every autumn", "checked every spring")  # the digest in the stack's row no longer fits
    now = states(crossings)
    assert (now["R4"], now["R1"], now["R2"]) == ("misaligned", "carried", "carried")
    assert (now["W4"], now["W2"], now["W3"]) == ("carried", "cooled", "cooled")  # another stack is not touched by it
    assert (
        store.listed(crossings, ids=("R1",))["labels"][0]["parent"] == "R4"
    )  # the stack is still above it, in the page
    reworded(crossings, "checked every spring", "checked every autumn")  # as it stood when the stack was marked
    assert states(crossings)["R4"] == "carried" and states(crossings)["R2"] == "cooled"
    store.strike(crossings, "W3")  # a line beneath that is gone
    now = states(crossings)
    assert (now["W4"], now["W2"]) == ("misaligned", "carried") and "W3" not in now
    assert store.status(crossings)["states"] == {"carried": 4, "cooled": 2, "misaligned": 1, "unresolved": 0}


def test_a_label_that_rests_on_what_the_archive_lacks_or_on_nothing_is_unresolved(tmp_path):
    crossings = lined(tmp_path)
    page = crossings / "labels" / f"{DAY}.md"
    page.write_text(
        page.read_text(encoding="utf-8") + "| R4 | A line with nothing under it at all. | his |  |\n", encoding="utf-8"
    )
    store.strike(crossings, E)  # W1 rests on D and E, W3 on E alone
    now = states(crossings)
    assert (now["W1"], now["W3"], now["R4"]) == ("unresolved", "unresolved", "unresolved")
    assert {key for key, state in now.items() if state == "carried"} == {"R1", "R2", "R3", "W2"}
    assert store.status(crossings)["states"] == {"carried": 4, "cooled": 0, "misaligned": 0, "unresolved": 3}
    # A stack that rests on a message the archive lost is unresolved, and stands for its lines no
    # longer: they are carried. Once a line of it is gone too, it is misaligned first.
    assert stack(crossings, "relation", GEAR, ["R2", "R3", B])["id"] == "R5"
    assert (states(crossings)["R5"], states(crossings)["R2"]) == ("carried", "cooled")
    store.strike(crossings, B)
    now = states(crossings)
    assert (now["R5"], now["R2"], now["R3"], now["R1"]) == ("unresolved", "carried", "carried", "unresolved")
    store.strike(crossings, "R3")
    assert (states(crossings)["R5"], states(crossings)["R2"]) == ("misaligned", "carried")


def test_a_label_on_a_pasted_text_rests_on_it_after_a_build_and_is_not_unresolved(tmp_path):
    """A pasted text is anchored by its message's id and a number. Read back from its page
    without the number, the label rested on the message and not on the paste; and where the id
    has no letter in it, it was not read back at all, so that a build would call the label
    unresolved the moment it was marked."""
    from test_handles import WITH_PASTE
    from test_store import ROWS, row

    rows = ROWS + [row("user", "11111111", 10, WITH_PASTE), row("user", "1a1a1a1a", 11, WITH_PASTE)]
    crossings, _ = home(tmp_path, rows)
    for key, paste in (("W2", "11111111+1"), ("W3", "1a1a1a1a+1")):
        out = store.mark(
            crossings, "work", "both", f"The yard's estimate, as it was pasted under {paste[:8]}.", [paste, D], day=DAY
        )
        assert (out["written"], out["id"], out["anchors"]) == (True, key, [paste, D])
        assert f"| both | `{paste}`, `{D}` |\n" in (crossings / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
        read = [label for label in store.labels(crossings) if label["id"] == key][0]
        assert read["anchors"] == [paste, D] and states(crossings)[key] == "carried"
        assert store.thread(crossings, paste, 0)["said"][0]["labels"] == [
            key
        ]  # the label rests there, and is found there
        assert key not in store.thread(crossings, paste[:8], 0)["said"][0]["labels"]
    assert "Estimate for the hull" not in frame.compose(
        crossings
    )  # what was pasted is not quoted as the person's words
    store.strike(crossings, "11111111")  # a pasted text goes with the message it came in
    assert (states(crossings)["W2"], states(crossings)["W3"]) == ("unresolved", "carried")


def test_a_line_that_lost_its_message_is_unresolved_though_a_sound_stack_stands_over_it(tmp_path):
    """Unresolved is the state to be seen: a line the archive no longer holds up is named as
    such, beneath a stack or not, and the stack over it is as sound as its rows say."""
    crossings = lined(tmp_path)
    stack(crossings, "relation", CARE, ["R1", "R2"])
    stack(crossings, "relation", GEAR, ["R4", "R3"])
    store.strike(crossings, D)  # R2 rests on D alone
    now = states(crossings)
    assert (now["R2"], now["R1"], now["R4"], now["R5"]) == ("unresolved", "cooled", "cooled", "carried")
    reworded(crossings, "The sails are stowed dry", "The sails are stowed dry and loose")  # a line of the top stack
    now = states(crossings)
    assert (now["R5"], now["R4"], now["R3"], now["R1"]) == ("misaligned", "carried", "carried", "cooled")
    reworded(crossings, "The sails are stowed dry and loose", "The sails are stowed dry")
    store.strike(crossings, "R1")  # the stack beneath the top is misaligned, and says so though the top is sound
    now = states(crossings)
    assert (now["R5"], now["R4"], now["R3"], now["R2"]) == ("carried", "misaligned", "cooled", "unresolved")


def test_a_page_edited_by_hand_cannot_make_a_line_vanish(tmp_path):
    """The door refuses a ring, a line of another kind and a line beneath two stacks; a page can
    still be edited into any of them. A build then leaves every line to be seen: a stack is
    newer than its lines, so of two labels that name each other one is carried and the other
    misaligned, and neither is cooled beneath the other."""
    crossings, _ = home(tmp_path)
    (crossings / "labels").mkdir()
    (crossings / "labels" / f"{DAY}.md").write_text(
        HEAD + f"| R2 | {KEEL} | his | `{D}`, `R3@{digest(SAILS)}` |\n"
        f"| R3 | {SAILS} | his | `{A}`, `R2@{digest(KEEL)}` |\n"
        f"| W2 | {MAST} | both | `{E}`, `R1@{digest(TERN)}` |\n"
        f"| R4 | {CARE} | his | `R1@{digest(TERN)}` |\n"
        f"| R5 | {GEAR} | his | `R1@{digest(TERN)}`, `R5@{digest(GEAR)}` |\n",
        encoding="utf-8",
    )
    store.build(crossings)
    now = states(crossings)
    assert (now["R2"], now["R3"]) == ("misaligned", "carried")  # the ring
    assert now["W2"] == "misaligned"  # a standing line beneath the work
    assert (now["R1"], now["R4"], now["R5"]) == (
        "cooled",
        "carried",
        "misaligned",
    )  # the first stack is the one above; R5 names itself
    db = sqlite3.connect(crossings / "store.db")
    assert dict(db.execute("select id, parent from label where parent is not null")) == {"R1": "R4", "R2": "R3"}
    db.close()
    text = frame.compose(crossings)
    for key in ("R2", "R3", "R4", "R5", "W1", "W2"):
        assert f"\n- {key} (" in text, key
    assert [label["id"] for label in store.listed(crossings, ids=("R2", "R3", "R5"))["labels"]] == [
        "R5",
        "R3",
        "R2",
    ]  # and no listing runs in a ring


def test_a_database_of_an_older_make_is_built_again_before_it_is_read(tmp_path):
    """The database is only an index, and one left by an earlier make of the plugin has no
    states in it. It is made again from the plain files, not read as it is."""
    crossings = lined(tmp_path)
    stack(crossings, "relation", CARE, ["R1", "R2"])

    def older() -> None:
        (crossings / "store.db").unlink()
        db = sqlite3.connect(crossings / "store.db")
        db.executescript(
            "create table said(seq integer primary key, uuid text unique, id text, session text, voice text, at text, text text);"
            "create table label(n integer primary key, id text unique, kind text, whose text, text text, page text, "
            "parent text, home text); create table anchor(label text, said text);"
        )
        db.close()

    older()
    held = store.status(crossings)
    assert (held["his"], held["labels"], held["states"]["cooled"]) == (2, 7, 2)
    older()
    assert f"- R4 (his): {CARE} [R1, R2]" in frame.compose(crossings)
    older()
    assert store.look(crossings)["stacks"] == {"lines": 2, "stacks": 1}


# --- the room and the listing ----------------------------------------------------------------------


def test_status_and_the_room_count_the_states_and_recite_no_standing_line(tmp_path):
    crossings = lined(tmp_path)
    project = str(crossings.parent)
    plain = through("status", "--cwd", project)[1]
    assert plain.rstrip().endswith(
        "6 labels, and 0 struck."
    )  # nothing cooled, misaligned or unresolved: nothing said of it
    assert (
        "stack" not in through("look", "--cwd", project)[1]
        and "no longer holds" not in through("look", "--cwd", project)[1]
    )
    stack(crossings, "relation", CARE, ["R1"])
    one = store.look(crossings)
    assert one["stacks"] == {"lines": 1, "stacks": 1} and one["states"] == store.status(crossings)["states"]
    assert "about the work; 1 of the standing lines stands beneath 1 stack." in through("look", "--cwd", project)[1]
    stack(crossings, "relation", GEAR, ["R4", "R2"])
    stack(crossings, "work", SPARS, ["W2", "W3"])
    store.strike(crossings, "W3")  # W4 is misaligned
    store.strike(crossings, E)  # W1 is unresolved
    out = store.look(crossings)
    assert out["states"] == {"carried": 3, "cooled": 3, "misaligned": 1, "unresolved": 1}
    assert (out["stacks"], out["misaligned"], out["unresolved"]) == ({"lines": 3, "stacks": 2}, ["W4"], ["W1"])
    shown = through("look", "--cwd", project)[1]
    assert (
        "Labels: 5 (R1 to R5) standing, about the two of you; 3 (W1 to W4) about the work; "
        "3 of the standing lines stand beneath 2 stacks.\n"
        "Misaligned stacks, to be written again: W4.\n"
        "Resting on what the archive no longer holds: W1.\n"
    ) in shown
    for sentence in (TERN, KEEL, SAILS, CARE, GEAR):  # an outline: a stack over standing lines is as quiet as they are
        assert sentence not in shown
    assert f"- W4 (both, misaligned): {SPARS} [W2, W3]" in shown and "- W1 (both, unresolved): " in shown
    status = through("status", "--cwd", project)[1]
    assert "8 labels, and 2 struck. Of the labels: 3 cooled, 1 misaligned, 1 unresolved." in status


def test_the_newest_about_the_work_are_the_tops_and_a_long_row_of_keys_is_cut_short(tmp_path):
    crossings = lined(tmp_path)
    stack(crossings, "work", SPARS, ["W2", "W3"])
    shown = through("look", "--cwd", str(crossings.parent))[1]
    newest = shown.split("The newest about the work:\n")[1].split("\n\n")[0]
    assert newest == (
        f"- W4 (both): {SPARS} [W2, W3]\n- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]"
    )  # the cooled are behind their stack
    (crossings / "labels" / "2026-11-13.md").write_text(
        HEAD
        + "".join(
            f"| W{n} | A row whose message the archive never held, number {n}. | both | `0a0a0a0a` |\n"
            for n in range(5, 45)
        ),
        encoding="utf-8",
    )
    store.build(crossings)
    shown = through("look", "--cwd", str(crossings.parent))[1]
    assert "Resting on what the archive no longer holds: W5, W6, " in shown and "W28 and 16 more.\n" in shown
    assert len(store.look(crossings)["unresolved"]) == 40 and len(shown) < 3200


def test_a_label_in_a_list_says_its_state_and_a_stack_shows_what_stands_beneath_it(tmp_path):
    crossings = lined(tmp_path)
    project = str(crossings.parent)
    stack(crossings, "relation", CARE, ["R1", "R2", D])
    stack(crossings, "work", SPARS, ["W2", "W3"])
    by_key = {label["id"]: label for kind in ("relation", "work") for label in store.listed(crossings, kind)["labels"]}
    assert (by_key["R4"]["state"], by_key["R4"]["parent"], by_key["R4"]["beneath"], by_key["R4"]["anchors"]) == (
        "carried",
        None,
        ["R1", "R2"],
        [D],
    )
    assert (by_key["R1"]["state"], by_key["R1"]["parent"], by_key["R1"]["beneath"]) == ("cooled", "R4", [])
    assert (by_key["R3"]["state"], by_key["R3"]["parent"]) == ("carried", None)
    standing = through("labels", "--kind", "relation", "--cwd", project)[
        1
    ]  # by kind: one line a label, none beneath another
    assert standing == (
        f"- R4 (his, 2026-11-11): {CARE} [R1, R2, dddddddd]\n"
        f"- R3 (his, 2026-11-11): {SAILS} [aaaaaaaa]\n"
        f"- R2 (his, 2026-11-11, cooled beneath R4): {KEEL} [dddddddd]\n"
        f"- R1 (his, 2026-11-11, cooled beneath R4): {TERN} [aaaaaaaa, bbbbbbbb]\n"
    )
    store.strike(crossings, "W3")
    store.strike(crossings, E)
    listed = through("labels", "--cwd", project)[1]
    assert listed == (
        f"- W4 (both, misaligned): {SPARS} [W2, W3]\n"
        f"- W2 (both, 2026-11-11): {MAST} [aaaaaaaa]\n"
        "- W1 (both, 2026-11-11, unresolved): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]\n"
        "4 standing lines about the two of you (R1 to R4) are not listed here: labels --kind relation.\n"
    )


def test_a_stack_named_by_its_key_is_given_whole_with_every_line_beneath_it(tmp_path):
    crossings = lined(tmp_path)
    project = str(crossings.parent)
    stack(crossings, "relation", CARE, ["R1", "R2", D])
    stack(crossings, "relation", GEAR, ["R4", "R3"])
    out = store.listed(crossings, ids=("r5",))
    assert [(label["id"], label["depth"]) for label in out["labels"]] == [
        ("R5", 0),
        ("R4", 1),
        ("R1", 2),
        ("R2", 2),
        ("R3", 1),
    ]
    assert out["labels"][0]["beneath"] == ["R4", "R3"] and out["missing"] == [] and out["quiet"] == []
    whole = (
        f"- R5 (his): {GEAR} [R4, R3]\n"
        f"  - R4 (his, 2026-11-11, cooled beneath R5): {CARE} [R1, R2, dddddddd]\n"
        f"    - R1 (his, 2026-11-11, cooled beneath R4): {TERN} [aaaaaaaa, bbbbbbbb]\n"
        f"    - R2 (his, 2026-11-11, cooled beneath R4): {KEEL} [dddddddd]\n"
        f"  - R3 (his, 2026-11-11, cooled beneath R5): {SAILS} [aaaaaaaa]\n"
    )
    assert through("labels", "R5", "--cwd", project)[1] == whole
    # A line named beside its stack is given once, beneath it; and a kind named beside a key changes nothing.
    assert through("labels", "R1", "R5", "R4", "--kind", "work", "--cwd", project)[1] == whole
    assert through("labels", "R4", "--cwd", project)[1] == "".join(line[2:] + "\n" for line in whole.splitlines()[1:4])
    assert through("labels", "R2", "W9", "--cwd", project)[1] == (
        f"- R2 (his, 2026-11-11, cooled beneath R4): {KEEL} [dddddddd]\nNo such label: W9.\n"
    )
    store.strike(crossings, "R2")  # what is left beneath a misaligned stack is still given under it
    assert through("labels", "R4", "--cwd", project)[1] == (
        f"- R4 (his, 2026-11-11, misaligned): {CARE} [R1, R2, dddddddd]\n"
        f"  - R1 (his, 2026-11-11): {TERN} [aaaaaaaa, bbbbbbbb]\n"
    )


def test_a_cooled_line_is_still_found_by_its_words_and_in_its_thread(tmp_path):
    crossings = lined(tmp_path)
    project = str(crossings.parent)
    stack(crossings, "relation", CARE, ["R1", "R2", D])
    assert states(crossings)["R2"] == "cooled"
    assert [label["id"] for label in store.find(crossings, "keel autumn")["labels"]] == ["R2"]
    assert f"- R2 (relation, his): {KEEL} [dddddddd]" in through("find", "keel", "autumn", "--cwd", project)[1]
    resting = store.thread(crossings, D, 0)
    assert {"R2", "R4"} <= {label["id"] for label in resting["labels"]} and "R2" in resting["said"][0]["labels"]
    assert f"- R2 (relation, his): {KEEL}" in through("thread", D, "--around", "0", "--cwd", project)[1]
    # A stack that is found shows in its brackets what it rests on, as it does in a list.
    assert f"- R4 (relation, his): {CARE} [R1, R2, dddddddd]" in through("find", "care", "year", "--cwd", project)[1]


# --- the frame -------------------------------------------------------------------------------------


def section(text: str, heading: str) -> str:
    return text.split(f"## {heading}\n\n")[1].split("\n\n")[0]


def test_the_frame_carries_the_top_of_a_stack_and_not_the_lines_beneath_it(tmp_path):
    crossings = lined(tmp_path)
    before = frame.compose(crossings)
    stack(crossings, "relation", CARE, ["R1", "R2", D])
    stack(crossings, "work", SPARS, ["W2", "W3"])
    text = frame.compose(crossings)
    assert len(text) < len(before) and TERN in before and MAST in before  # smaller by what was stacked
    assert section(text, "Standing, about the two of you") == (
        f"- R3 (his): {SAILS} [aaaaaaaa]\n- R4 (his): {CARE} [R1, R2, dddddddd]"
    )
    assert section(text, "The work, newest first") == (
        f"- W4 (both): {SPARS} [W2, W3]\n- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]"
    )
    for sentence in (TERN, KEEL, MAST, RIGGING):  # behind their stacks, one reach away
        assert sentence not in text
    # The person's words are those the carried work rows rest on: not those beneath a cooled line.
    assert (
        section(text, "The person's own words, as they stand in the record")
        == f"- `{D}`: We paint the hull grey in spring"
    )
    assert "no longer holds" not in text and "to be written again" not in text and len(text) <= frame.SIZE
    assert text.rstrip().endswith("and 8 labels.")


def test_a_misaligned_stack_crosses_with_its_lines_and_says_it_is_to_be_written_again(tmp_path):
    crossings = lined(tmp_path)
    stack(crossings, "relation", CARE, ["R1", "R2", D])
    stack(crossings, "relation", GEAR, ["R4", "R3"])
    reworded(crossings, "checked every autumn", "checked every spring")
    text = frame.compose(crossings)
    assert section(text, "Standing, about the two of you") == (
        f"- R1 (his): {TERN} [aaaaaaaa, bbbbbbbb]\n"
        "- R2 (his): The keel is checked every spring. [dddddddd]\n"
        f"- R4 (his): {CARE} (to be written again: a line beneath it changed) [R1, R2, dddddddd]\n"
        f"- R5 (his): {GEAR} [R4, R3]"
    )
    assert "- R3 (his)" not in text  # still cooled, beneath the stack that is sound


def test_what_the_archive_no_longer_holds_up_is_named_by_key_and_not_carried(tmp_path):
    crossings = lined(tmp_path)
    assert store.mark(crossings, "next", "session", "The mooring is next.", [A], day=DAY)["id"] == "N1"
    assert store.mark(crossings, "next", "session", "The hull comes after the mooring.", [D], day=DAY)["id"] == "N2"
    store.strike(crossings, E)
    text = frame.compose(crossings)
    assert "\n\n2 labels rest on what the archive no longer holds: W1, W3; `labels` gives them.\n\n" in text
    assert "- W1 (" not in text and "- W3 (" not in text and f"- W2 (both): {MAST} [aaaaaaaa]" in text
    assert text.index("## The work") < text.index("2 labels rest on") < text.index("## The person's own words")
    store.strike(
        crossings, A
    )  # R1, R3 and W2 rest on it; so does the older line at the door, which no frame would carry
    text = frame.compose(crossings)
    assert "5 labels rest on what the archive no longer holds: R1, R3, W1, W2, W3; `labels` gives them." in text
    assert "## The work" not in text and "- N2 (session): The hull comes after the mooring. [dddddddd]" in text
    store.strike(crossings, D)  # and now the newest line at the door rests on nothing the archive holds
    text = frame.compose(crossings)
    assert "7 labels rest on what the archive no longer holds: R1, R2, R3, W1, W2, W3, N2; `labels` gives them." in text
    assert "## Left at the door" not in text and "## Standing" not in text and not ASKS.search(text)
    alone, _ = home(tmp_path / "alone")
    store.strike(alone, E)
    assert "\n\n1 label rests on what the archive no longer holds: W1; `labels` gives them.\n\n" in frame.compose(alone)


def test_a_frame_stays_within_its_size_however_many_labels_lost_their_ground(tmp_path):
    """The line that names them is part of the frame, so its length is taken from the room the
    labels have; and it names a few and counts the rest, so that it cannot fill a frame alone."""
    crossings = lined(tmp_path)
    page = crossings / "labels" / "2026-11-13.md"
    page.write_text(
        HEAD
        + "".join(
            f"| W{n} | A row whose message the archive never held, number {n}. | both | `0a0a0a0a` |\n"
            for n in range(4, 1204)
        ),
        encoding="utf-8",
    )
    store.build(crossings)
    text = frame.compose(crossings, frame.MOST)
    assert len(text) <= frame.MOST and f"- W3 (both): {RIGGING} [eeeeeeee]" in text
    assert (
        "1200 labels rest on what the archive no longer holds: W4, W5, " in text
        and "W27 and 1176 more; `labels` gives them." in text
    )
    small = frame.compose(crossings, len(frame.opening()) + 420 + 40)  # room for the opening and little more
    assert len(small) <= len(frame.opening()) + 420 + 40 and "W27 and 1176 more; `labels` gives them." in small
    # A full frame: a line at the door, more rows about the work than fit, and labels that lost their ground.
    assert store.mark(crossings, "next", "session", "The mooring is next.", [D], day=DAY)["written"]
    page.write_text(
        HEAD
        + "".join(f"| W{n} | Short, number {n}. | both | `{D}` |\n" for n in range(4, 404))
        + "".join(
            f"| W{n} | A row whose message the archive never held, number {n}. | both | `0a0a0a0a` |\n"
            for n in range(1001, 1031)
        ),
        encoding="utf-8",
    )
    store.build(crossings)
    for size in (3000, 3011, 3022, 3033, 4000, frame.MOST):  # wherever the last row that fits happens to end
        text = frame.compose(crossings, size)
        assert len(text) <= size, (size, len(text))
        assert "30 labels rest on what the archive no longer holds: W1001, W1002, " in text, size
        assert (
            "W1024 and 6 more; `labels` gives them." in text
            and "more labels in the store: `labels` lists them." in text
        ), size
        assert "## Left at the door" in text and "## The person's own words" in text, size


def test_the_frame_says_how_a_stack_is_read_and_how_one_is_marked(tmp_path):
    opening = frame.opening()
    assert "in brackets the ids it rests on: messages, or the lines stacked beneath it." in opening
    marked = re.search(r"^- mark: (.*)$", opening, flags=re.M).group(1)
    assert "labels of its kind" in marked and "stacks them" in marked
    assert len(opening) < 1800 and not ASKS.search(opening)  # it is carried at every cut, and says what it is for


# --- undoing ----------------------------------------------------------------------------------------


def test_striking_a_stack_gives_its_lines_back_and_striking_a_line_misaligns_its_stack(tmp_path):
    crossings = lined(tmp_path)
    stack(crossings, "relation", CARE, ["R1", "R2"])
    out = store.strike(crossings, "R4")
    assert out["struck"] and out["removed"] == 1
    page = (crossings / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
    assert "| R4 |" not in page and f"| R2 | {KEEL} | his | `{D}` |\n" in page  # the stack's row leaves; its lines stay
    assert states(crossings) == {key: "carried" for key in ("R1", "R2", "R3", "W1", "W2", "W3")}
    text = frame.compose(crossings)
    assert f"- R1 (his): {TERN}" in text and f"- R2 (his): {KEEL}" in text and CARE not in text
    again = stack(crossings, "relation", CARE, ["R1", "R2"])  # the lines are free to be stacked again, under a new key
    assert again["written"] and again["id"] == "R5"
    store.strike(crossings, "R1")
    assert (states(crossings)["R5"], states(crossings)["R2"]) == ("misaligned", "carried")
    text = frame.compose(crossings)
    assert (
        f"- R5 (his): {CARE} (to be written again: a line beneath it changed) [R1, R2]" in text
        and f"- R2 (his): {KEEL}" in text
    )
    assert TERN not in text
    (crossings / "store.db").unlink()  # and nothing struck comes back at a build
    held = store.build(crossings)
    assert (
        held["labels"] == 6 and held["struck"] == 2 and "R1" not in states(crossings) and "R4" not in states(crossings)
    )
    assert TERN not in frame.compose(crossings)


# --- writing a stack again ----------------------------------------------------------------------------


def test_a_misaligned_stack_is_replaced_by_the_stack_written_over_its_lines(tmp_path):
    """Of a misaligned stack the frame says that it is to be written again, and a session has
    no handle for striking. So the stack marked over its lines takes its place in the same act."""
    crossings = lined(tmp_path)
    assert stack(crossings, "relation", CARE, ["R1", "R2", "R3"])["id"] == "R4"
    reworded(crossings, "checked every autumn", "checked every spring")
    assert states(crossings)["R4"] == "misaligned"
    out = stack(crossings, "relation", AGAIN, ["R1", "R2"])  # over two of its three lines, as they now stand
    assert (out["written"], out["id"], out["replaced"], out["beneath"]) == (True, "R5", ["R4"], ["R1", "R2"])
    page = (crossings / "labels" / f"{DAY}.md").read_text(encoding="utf-8")
    assert "| R4 |" not in page and CARE not in page  # its row is out of its page
    assert f"| R5 | {AGAIN} | his | `R1@{digest(TERN)}`, `R2@{digest('The keel is checked every spring.')}` |\n" in page
    assert "R4" in store.struck(crossings)  # and its key is among the struck
    now = states(crossings)
    assert "R4" not in now and (now["R5"], now["R1"], now["R2"]) == ("carried", "cooled", "cooled")
    assert now["R3"] == "carried"  # a line the new stack did not take is carried again
    (crossings / "store.db").unlink()  # and the old stack does not come back at a build
    held = store.build(crossings)
    assert (held["struck"], held["states"]["misaligned"]) == (1, 0) and "R4" not in states(crossings)
    assert store.listed(crossings, ids=("R4",))["missing"] == ["R4"]
    text = frame.compose(crossings)
    assert CARE not in text and "to be written again" not in text
    assert f"- R5 (his): {AGAIN} [R1, R2]" in text and f"- R3 (his): {SAILS} [aaaaaaaa]" in text
    last = stack(crossings, "relation", GEAR, ["R5", "R3"])  # the old stack's key is not used again
    assert (last["id"], last["replaced"]) == ("R6", [])


def test_a_stack_whose_line_is_gone_is_written_again_over_the_lines_that_are_left(tmp_path):
    crossings = lined(tmp_path)
    assert stack(crossings, "work", SPARS, ["W2", "W3"])["id"] == "W4"
    assert stack(crossings, "work", ALOFT, ["W4", "W1"])["id"] == "W5"  # a stack over that stack
    store.strike(crossings, "W3")
    now = states(crossings)
    assert (now["W4"], now["W2"], now["W5"]) == ("misaligned", "carried", "carried")
    out = stack(crossings, "work", "The mast is done.", ["W2"])
    assert (out["id"], out["replaced"]) == ("W6", ["W4"])
    now = states(crossings)
    assert "W4" not in now and (now["W6"], now["W2"]) == ("carried", "cooled")
    # As with any strike, the stack that stood over the old one has lost a line. It is written again in its turn.
    assert (now["W5"], now["W1"]) == ("misaligned", "carried")
    out = stack(crossings, "work", ALOFT, ["W6", "W1"])
    assert (out["id"], out["replaced"]) == ("W7", ["W5"])
    assert states(crossings) == {
        "R1": "carried",
        "R2": "carried",
        "R3": "carried",
        "W1": "cooled",
        "W2": "cooled",
        "W6": "cooled",
        "W7": "carried",
    }
    assert store.struck(crossings) == {"W3", "W4", "W5"}


def test_a_sound_stack_is_still_protected_and_a_refused_stack_strikes_nothing(tmp_path):
    crossings = lined(tmp_path)
    assert stack(crossings, "relation", CARE, ["R1"])["id"] == "R4"  # sound
    assert stack(crossings, "relation", GEAR, ["R2", "R3"])["id"] == "R5"  # to be misaligned
    assert stack(crossings, "work", SPARS, ["W2", "W3", B])["id"] == "W4"  # to lose a message it rests on
    reworded(crossings, "stowed dry", "stowed dry and loose")
    store.strike(crossings, B)
    now = states(crossings)
    assert (now["R4"], now["R5"], now["W4"], now["W2"]) == ("carried", "misaligned", "unresolved", "carried")
    pages = {page: page.read_text(encoding="utf-8") for page in store.pages(crossings)}
    refused = {
        # One line beneath a sound stack refuses the whole, though another stands beneath a misaligned one.
        "beneath a sound stack": stack(crossings, "relation", AGAIN, ["R1", "R2"]),
        # A stack cannot stand beneath the one that takes its place.
        "the old stack among the lines": stack(crossings, "relation", AGAIN, ["R2", "R5"]),
        # A stack that lost a message is unresolved, not misaligned: it is still the stack above its lines.
        "beneath an unresolved stack": stack(crossings, "work", ALOFT, ["W2", "W3"]),
    }
    for what, out in refused.items():
        assert out["written"] is False and set(out) == {"written", "why"}, what
        why = out["why"]
        assert "\n" not in why and why.count(". ") == 0 and not ASKS.search(why) and "/" not in why, what
    assert (
        refused["beneath a sound stack"]["why"]
        == "R1 already stands beneath R4, and a line stands beneath one stack alone"
    )
    assert refused["the old stack among the lines"]["why"] == (
        "R5 is misaligned and this stack would take its place, so it cannot also stand beneath it"
    )
    assert refused["beneath an unresolved stack"]["why"].startswith("W2 already stands beneath W4")
    assert {page: page.read_text(encoding="utf-8") for page in store.pages(crossings)} == pages
    assert store.struck(crossings) == {B} and states(crossings) == now  # nothing was struck by a refusal


def test_the_door_and_its_server_say_which_stack_the_new_one_took_the_place_of(tmp_path):
    crossings = lined(tmp_path)
    project = str(crossings.parent)
    assert (
        through(
            "mark", "--kind", "relation", "--whose", "his", "--anchors", "R1,R2", CARE, "--touch", "--cwd", project
        )[0]
        == 0
    )
    reworded(crossings, "checked every autumn", "checked every spring")
    code, answer = through(
        "mark", "--kind", "relation", "--whose", "his", "--anchors", "R1,R2", AGAIN, "--touch", "--cwd", project
    )
    assert code == 0 and answer.startswith("marked R5, in place of R4 in ") and answer.endswith(".md\n")
    # Two stacks, each misaligned by a rewording of its own, and one stack marked over the lines of both.
    assert stack(crossings, "work", "The hull is done.", ["W1"])["id"] == "W4"
    assert stack(crossings, "work", SPARS, ["W2", "W3"])["id"] == "W5"
    page = crossings / "hand-over.md"
    page.write_text(page.read_text(encoding="utf-8").replace("painted grey", "painted white"), encoding="utf-8")
    reworded(crossings, "The mast was stepped again", "The mast was stepped once more")
    assert (states(crossings)["W4"], states(crossings)["W5"]) == ("misaligned", "misaligned")
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert said("mark", sentence=ALOFT, anchors=["W1", "W2", "W3"], whose="both") == (
            "marked W6, in place of W4 and W5",
            False,
        )
        assert said("mark", sentence=GEAR, anchors=["R5", "R3"], kind="relation") == (
            "marked R6",
            False,
        )  # nothing replaced, nothing said of it
    assert store.struck(crossings) == {"R4", "W4", "W5"} and set(states(crossings).values()) == {"carried", "cooled"}
    pulls = [json.loads(line)["ids"] for line in (crossings / "reached.jsonl").read_text(encoding="utf-8").splitlines()]
    assert pulls == [["R5"], ["W6"], ["R6"]]  # the pull that marked the first stack left the log with it


# --- what a session is told, and the door from a shell ------------------------------------------------


def test_the_door_and_its_server_stack_lines_and_say_plainly_what_they_refuse(tmp_path):
    crossings = lined(tmp_path)
    project = str(crossings.parent)
    code, answer = through(
        "mark", "--kind", "work", "--whose", "both", "--anchors", "w2,W3", SPARS, "--touch", "--cwd", project
    )
    assert code == 0 and answer.startswith("marked W4 in ")
    assert through(
        "mark", "--kind", "work", "--anchors", "W2", "A second stack over the same line.", "--cwd", project
    ) == (1, "not marked: W2 already stands beneath W4, and a line stands beneath one stack alone\n")
    told = []
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert said("mark", sentence=CARE, anchors=["R1", "r2", D], kind="relation", whose="his") == (
            "marked R4",
            False,
        )
        told += [
            said("mark", sentence=GEAR, anchors=["R4", "R9"], kind="relation")[0],
            said("mark", sentence=GEAR, anchors=["R4", "W1"], kind="relation")[0],
            said("mark", sentence=GEAR, anchors=["R1"], kind="relation")[0],
            said("leave", sentence="The spars are next.", anchors=["W4"])[0],
        ]
        assert told == [
            "not marked: no such label: R9",
            "not marked: a stack holds labels of its own kind alone, and of another kind here: W1",
            "not marked: R1 already stands beneath R4, and a line stands beneath one stack alone",
            "not marked: a line left at the door rests on messages alone, never on labels",
        ]
        assert said("leave", sentence="The spars are next.", anchors=["W4"])[1] is False  # a refused label is an answer
        assert said("mark", sentence=GEAR, anchors=["R4", "R3"], kind="relation", whose="his") == ("marked R5", False)
        assert said("mark", sentence="One level more.", anchors=["R5"], kind="relation")[0] == (
            "not marked: R5 already stands over stacks, and stacking goes no deeper than that"
        )
        whole = said("labels", ids=["R5"])[0]
        assert whole.splitlines()[0] == f"- R5 (his): {GEAR} [R4, R3]"
        assert [line[: line.index("(")] for line in whole.splitlines()[1:]] == [
            "  - R4 ",
            "    - R1 ",
            "    - R2 ",
            "  - R3 ",
        ]
        store.strike(crossings, "W3")
        store.strike(crossings, E)
        told += [
            whole,
            said("look")[0],
            said("status")[0],
            said("labels")[0],
            said("labels", kind="relation")[0],
            said("find", words="care year")[0],
            frame.compose(crossings),
        ]
    assert (
        "Misaligned stacks, to be written again: W4." in told[5]
        and "Of the labels: 4 cooled, 1 misaligned, 1 unresolved." in told[6]
    )
    assert (
        "to be written again: a line beneath it changed" in told[10]
        and "rests on what the archive no longer holds: W1" in told[10]
    )
    for text in told:
        assert str(tmp_path) not in text and "/Users/" not in text and ".py" not in text and ".md" not in text
        assert "python" not in text.lower() and not ASKS.search(text) and " --" not in text
    pulls = [json.loads(line) for line in (crossings / "reached.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [pull["ids"] for pull in pulls if pull["verb"] == "mark"] == [
        ["W4"],
        ["R4", D],
        ["R5"],
    ]  # keys and ids, no sentence


def test_a_session_is_told_that_lines_can_be_stacked_and_what_a_stack_is_given_with(tmp_path):
    return  # retired: it pins what the server told a session before the kind refused and the tool crossing; see tests/test_refused.py
    by_name = {one["name"]: one for one in serve.TOOLS}
    assert "labels of the same kind, which stacks them beneath this one" in by_name["mark"]["description"]
    assert "labels of its kind" in by_name["mark"]["inputSchema"]["properties"]["anchors"]["description"]
    assert "a stack with the lines beneath it" in by_name["labels"]["description"]
    assert (
        "labels" not in by_name["leave"]["inputSchema"]["properties"]["anchors"]["description"]
    )  # a line at the door stacks nothing
    assert all(len(one["description"]) < (400 if one["name"] in ("mark", "leave") else 260) for one in serve.TOOLS)
    assert len(json.dumps(serve.TOOLS)) < 5400  # mark also says what a label is for: what the person tells and asks
    with set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):
        told = serve.instructions()
    assert (
        "Lines can be stacked into fewer: `mark` a label that rests on them, and the frame then carries the one."
        in told
    )
    assert (
        len(told) < 1100 and not ASKS.search(told) and not ASKS.search(json.dumps(serve.TOOLS).replace(store.FOR, ""))
    )


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
