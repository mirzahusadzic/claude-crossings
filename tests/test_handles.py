"""The handles a session reaches for: whose words a paste is, a forgiving find, the room, a line
left at the door, and what was pulled. No model, no network.

Run with pytest, or without it:  python3 tests/test_handles.py
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_store import ROWS, A, B, D, E, at_terminal, home, row, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import count, door, frame, store, transcript  # noqa: E402

PASTED = "Estimate for the hull: two coats of grey.\n\n| a | table |\n\nReady by the end of March."
WITH_PASTE = f'Here is what the yard sent back.\n\n<pasted_content id="3d0c">\n{PASTED}\n</pasted_content id="3d0c">'
ONLY_PASTE = f'<pasted_content id="77aa">{PASTED}</pasted_content id="77aa">'


def through(*argv: str) -> tuple[int, str]:
    """The door, in this process."""
    out = io.StringIO()
    with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
        code = door.main(list(argv))
    return code, out.getvalue()


# --- whose words a paste is ------------------------------------------------------------------


def test_what_the_person_pasted_is_not_what_the_person_said(tmp_path):
    """A paste under a line of the person's own is someone else's words that the person handed
    over. Held as the person's, all of it would be counted and quoted as theirs."""
    typed, pastes = transcript.unpasted(WITH_PASTE)
    assert typed.split() == "Here is what the yard sent back. [pasted: 84 characters]".split() and pastes == [PASTED]
    assert transcript.person(row("user", "11111111", 10, WITH_PASTE)) == ["Here is what the yard sent back."]
    assert transcript.person(row("user", "22222222", 11, ONLY_PASTE)) == []  # nothing of his to count
    assert transcript.person(row("user", "22222222", 11, ONLY_PASTE), whole=True) == [ONLY_PASTE]  # and still kept
    assert (
        transcript.person(row("user", "33333333", 12, "<system-reminder>not his</system-reminder>"), whole=True) == []
    )

    rows = ROWS + [row("user", "11111111", 10, WITH_PASTE), row("user", "22222222", 11, ONLY_PASTE)]
    crossings, path = home(tmp_path, rows)
    held = store.status(crossings)
    assert (held["his"], held["session"], held["pasted"]) == (4, 2, 2)
    kept = (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8")
    assert "Estimate for the hull" in kept  # the archive keeps the message as it was sent

    out = store.thread(crossings, "11111111", 1)
    said = {s["id"]: s for s in out["said"]}
    assert said["11111111"]["voice"] == "his"
    assert said["11111111"]["text"] == "Here is what the yard sent back.\n\n[pasted: 84 characters]"
    assert said["11111111+1"]["voice"] == "pasted" and said["11111111+1"]["text"] == PASTED
    found = store.find(crossings, "estimate coats")
    assert {s["voice"] for s in found["said"]} == {"pasted"} and store.find(crossings, "estimate", voice="his")[
        "said"
    ] == []
    shown = through("thread", "11111111+1", "--around", "0", "--cwd", str(crossings.parent))[1]
    assert "`11111111+1` pasted by the person" in shown and "the one you named" in shown
    assert "2 pasted texts, kept apart" in through("status", "--cwd", str(crossings.parent))[1]

    # What the person's voice is counted as, at a cut, is the typed words alone.
    c = count.count(path, "A summary that holds: Here is what the yard sent back.")
    assert c["person"]["chars"] == sum(len(t) for r in rows for t in transcript.person(r))
    assert "Estimate for the hull" not in frame.compose(crossings)

    assert store.strike(crossings, "11111111+1") == {
        "struck": False,
        "why": "a pasted text is struck with the message it came in: strike 11111111",
    }
    assert store.strike(crossings, "11111111")["struck"] is True
    assert (
        "Estimate for the hull: two coats"
        not in (crossings / "said" / "session-.jsonl").read_text(encoding="utf-8").split("22222222")[0]
    )
    assert store.status(crossings)["pasted"] == 1


# --- a forgiving grip -------------------------------------------------------------------------


def said_ids(crossings: Path, words: str, **more) -> list[str]:
    return [s["id"] for s in store.find(crossings, words, **more)["said"]]


def test_find_takes_a_stem_a_star_and_a_phrase(tmp_path):
    """A word is found by its stem, a `*` takes every word that begins so, and quotes hold a phrase."""
    crossings, _ = home(tmp_path)
    assert said_ids(crossings, "painted") == [D]  # the message says "paint"
    assert said_ids(crossings, "reminded") == [E]  # the session said "remind"
    assert sorted(said_ids(crossings, "moor*")) == sorted([A, B]) and said_ids(crossings, "moor") == [A, B][
        :0
    ] + said_ids(crossings, "moor")
    assert (
        said_ids(crossings, '"hull grey"') == [D] and said_ids(crossings, '"grey hull"') == []
    )  # a phrase keeps its order
    assert (
        store.find(crossings, '"?!" ""')["said"] == [] and store.find(crossings, '""')["nearest"] == []
    )  # quotes with no word in them
    assert said_ids(crossings, "boat", limit=1) == [A]  # and never more than was asked for


def test_the_door_never_finds_less_than_a_search_of_the_files_would(tmp_path):
    """A word inside a longer one, as in bilgePump, is no word to an index. A plain search of the
    files finds it, so the door must too."""
    import sqlite3

    rows = ROWS + [
        row("user", "55555555", 20, "Reset the bilgePump timer, please."),
        row("assistant", "66666666", 21, "It pumped all night; a pump log helps."),
    ]
    crossings, _ = home(tmp_path, rows)
    texts = dict(sqlite3.connect(crossings / "store.db").execute("select id, text from said"))
    for word in sorted({w for text in texts.values() for w in re.findall(r"[a-z]{3,}", text.lower())}):
        by_search = {i for i, text in texts.items() if word in text.lower()}
        assert by_search <= set(said_ids(crossings, word, limit=1000)), word
    hit = [s for s in store.find(crossings, "pump")["said"] if s["id"] == "55555555"][0]
    assert "bilge[Pump] timer" in hit["part"] and hit["labels"] == []
    inside = store.find(crossings, "pring")  # the end of "spring": in a message and in a label, a word in neither
    assert [s["id"] for s in inside["said"]] == [D] and [label["id"] for label in inside["labels"]] == ["W1"]
    assert inside["labels"][0]["anchors"] == [D, E] and inside["labels"][0]["text"].startswith("The hull")
    assert store.find(crossings, "pring", voice="session")["said"] == []
    long = "word " * 40 + "needle" + " word" * 40
    assert store._part(long, ["needle"]).startswith("… ") and store._part(long, ["needle"]).endswith(" …")


def test_a_miss_names_the_nearest_words_that_are_there(tmp_path):
    crossings, _ = home(tmp_path)
    assert store.find(crossings, "moring")["nearest"] == [("mooring", 2)]
    said = through("find", "moring", "zeppelin", "--cwd", str(crossings.parent))[1]
    assert "That is a miss, not a no" in said and said.rstrip().endswith("Nearest words that are there: mooring (2).")
    assert "Nearest" not in through("find", "zeppelin", "--cwd", str(crossings.parent))[1]


def test_a_standing_line_that_only_shares_a_word_is_named_and_not_recited(tmp_path):
    """Where a label holds every word looked for, it is given. Where it merely shares one of them,
    a standing line about the person is named by its id and left alone: a search for something
    else is not to recite what was confided."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    some = through("find", "Tern zeppelin", "--cwd", project)[1]
    labels_part = some.split("Said:")[0]
    assert (
        "- R1 (relation, his): a standing line about the two of you, not recited here; `labels R1` gives it."
        in labels_part
    )
    assert "lies at mooring" not in labels_part
    every = through("find", "Tern lies", "--cwd", project)[1]  # every word asked for is in it
    assert "- R1 (relation, his): His boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]" in every
    work = through("find", "hull zeppelin", "--cwd", project)[1]  # a label about the work is given either way
    assert "- W1 (work, both): The hull is to be painted grey in spring." in work


def test_labels_that_only_share_a_word_are_few_and_short(tmp_path):
    """A few words can find the one message meant and, beside it, many long labels that each
    share one small word. A door that talks too much is one a session stops reaching for."""
    crossings, _ = home(tmp_path)
    (crossings / "labels").mkdir()
    (crossings / "labels" / "2026-11-11.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        + "".join(
            f"| W{n} | The hull was looked at again on day {n}, "
            + "and looked at once more, " * 12
            + f"to no end. | both | `{D}` |\n"
            for n in range(2, 12)
        ),
        encoding="utf-8",
    )
    store.build(crossings)
    project = str(crossings.parent)
    some = through("find", "hull zeppelin", "--cwd", project)[1].split("Said:")[0]
    assert some.count("\n- W") == 3 and " […] [dddddddd]" in some and "5 more labels hold one of these words" in some
    every = through("find", "hull looked", "--cwd", project)[1].split("Said:")[0]
    assert every.count("\n- W") == 8 and "to no end. [dddddddd]" in every  # every word asked for: given whole


# --- the room -----------------------------------------------------------------------------------


def test_the_room_is_shown_without_a_word_and_keeps_quiet_what_was_confided(tmp_path):
    rows = ROWS + [row("user", "11111111", 10, WITH_PASTE)]
    crossings, _ = home(tmp_path, rows)
    project = str(crossings.parent)
    out = store.look(crossings)
    assert out["days"] == [{"day": "2026-11-11", "his": 3, "session": 2, "pasted": 1}]
    assert (out["standing"], out["work"], out["left"], out["struck"]) == (["R1"], ["W1"], None, 0)
    shown = through("look", "--cwd", project)[1]
    assert shown.startswith("The store in outline: 1 day, 5 messages, 2 labels, 0 struck; kept up to 2026-11-11 ")
    assert "- 2026-11-11: 3 of the person's, 2 of the session's, 1 pasted" in shown
    assert "Labels: 1 (R1 to R1) standing, about the two of you; 1 (W1 to W1) about the work." in shown
    assert "- W1 (both): The hull is to be painted grey in spring. [dddddddd, eeeeeeee]" in shown
    assert "Tern" not in shown and "Left at the door" not in shown  # the standing line is named, not recited


def test_the_room_stays_small_however_much_the_store_holds(tmp_path):
    crossings, _ = home(tmp_path)
    (crossings / "labels").mkdir()
    (crossings / "labels" / "2026-11-11.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        + "".join(
            f"| W{n} | The hull was looked at again on day {n}, "
            + "and looked at once more, " * 12
            + f"to no end. | both | `{D}` |\n"
            for n in range(2, 47)
        ),
        encoding="utf-8",
    )
    store.build(crossings)
    project = str(crossings.parent)
    shown = through("look", "--cwd", project)[1]
    assert len(shown) < 3200 and "46 (W1 to W46) about the work" in shown and shown.count("\n- W") == 8
    assert "- W46 (both): The hull was looked at again on day 46," in shown and " […] [dddddddd]" in shown

    listed = through("labels", "--cwd", project)[1]
    assert listed.count("\n- W") + 1 == 40 and "6 more, older: name a kind or a day." in listed
    assert "1 standing line about the two of you (R1 to R1) is not listed here: labels --kind relation." in listed
    assert "Tern" not in listed and " […] [dddddddd]" in listed  # cut short in a list
    one = through("labels", "w46", "R1", "W99", "--cwd", project)[1]  # by id: whole, and of any kind
    assert "to no end. [dddddddd]" in one and "- R1 (his, 2026-11-11): His boat is called Tern" in one
    assert "No such label: W99." in one and "not listed here" not in one
    assert (
        through("labels", "--kind", "relation", "--cwd", project)[1].strip()
        == "- R1 (his, 2026-11-11): His boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]"
    )
    assert through("labels", "--day", "2026-01-01", "--cwd", project)[1].startswith("No label of that kind or day.")
    assert "- W46 (both, 2026-11-11)" in through("labels", "--kind", "work", "--day", "2026-11-11", "--cwd", project)[1]


def test_an_empty_home_is_an_empty_room_and_not_an_error(tmp_path):
    import os

    crossings, _ = home(tmp_path)  # the home on this computer is offered to a project switched on
    os.environ["CROSSING_OURS"] = str(tmp_path / "ours")
    try:
        shown = through("look", "--home", "ours", "--cwd", str(crossings.parent))[1]
        listed = through("labels", "--home", "ours", "--cwd", str(crossings.parent))[1]
    finally:
        del os.environ["CROSSING_OURS"]
    assert not (tmp_path / "ours").exists()  # and looking made nothing
    assert shown.startswith("The store in outline: 0 days, 0 messages, 0 labels, 0 struck.")
    assert "Labels: none standing, about the two of you; none about the work." in shown and "The newest" not in shown
    assert listed.strip() == "No label of that kind or day."


# --- a line left at the door ----------------------------------------------------------------------


def test_a_line_left_at_the_door_opens_the_frame_and_only_the_newest_is_carried(tmp_path):
    """A session leaves a line for the one that wakes after the next cut, as the work goes, since
    a cut may come unannounced. It rests on what was said, like any label."""
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    assert store.mark(crossings, "next", "session", "I was painting the hull; reach for W1 first.", [D])["id"] == "N1"
    assert store.mark(crossings, "next", "session", "The hull is done; the mooring is next.", [A])["id"] == "N2"
    assert store.mark(crossings, "next", "session", "Resting on nothing.", ["0a0a0a0a"])["written"] is False
    text = frame.compose(crossings)
    after_opening = text.split("\n\n## ", 1)[1]
    assert after_opening.startswith(
        "Left at the door by the session before this cut\n\n"
        "- N2 (session): The hull is done; the mooring is next. [aaaaaaaa]\n\n## Standing"
    )
    assert "N1 (" not in text
    assert store.look(crossings)["left"] == {
        "id": "N2",
        "text": "The hull is done; the mooring is next.",
        "anchors": [A],
        "since": [],  # no work label marked after it
    }
    assert (
        "Left at the door:\n- N2 (the session's): The hull is done; the mooring is next. [aaaaaaaa]"
        in through("look", "--cwd", project)[1]
    )
    assert "- N2 (session, 2026-11-11): The hull is done" in through("labels", "--cwd", project)[1]
    assert "- N1 (session, 2026-11-11)" in through("labels", "--kind", "next", "--cwd", project)[1]
    store.strike(crossings, "N2")
    text = frame.compose(crossings)
    assert "- N1 (session): I was painting the hull; reach for W1 first. [dddddddd]" in text and "N2 (" not in text
    assert store.mark(crossings, "next", "session", "Again.", [A])["id"] == "N3"  # a struck key is not used again
    code, said = through(
        "mark", "--kind", "next", "--whose", "session", "--anchors", A, "Left", "from", "a", "shell.", "--cwd", project
    )
    assert code == 0 and "marked N4" in said


def test_a_frame_names_only_handles_that_exist(tmp_path):
    """A session that wakes takes every word of a frame for something it can do. So nothing the
    plugin itself says in a frame or in the waking note uses a word that reads as a handle the
    door does not have."""
    from crossing import hook

    crossings, _ = home(tmp_path)
    store.mark(crossings, "next", "session", "The mooring is next.", [A])
    small = frame.compose(crossings, len(frame.opening()) + 580)  # the labels do not all fit: the lines that say so
    assert "1 more label in the store: `labels` lists them." in small
    waking = hook.waking({"cut": 1})
    for text in (small, frame.compose(crossings), waking):
        assert not re.search(r"\bask(s|ed|ing)?\b", text, re.I)
    from crossing import serve

    named = re.findall(r"^- (\w+): ", frame.opening(), flags=re.M)
    assert named == ["look", "labels", "find", "thread", "mark", "leave"]
    assert set(named) < set(serve.NAMES)  # every handle the frame names is one the door's server offers


def test_the_words_a_frame_quotes_are_those_its_own_work_rows_rest_on(tmp_path):
    """The person's words a frame quotes are the ones its own work rows rest on. Not those under
    a label the frame does not carry, which would bring in what it left out; and not those
    under a standing row, which is held without what was said beneath it being put on show."""
    rows = ROWS + [row("user", "55555555", 20, "The newest thing said about the rigging.")]
    crossings, _ = home(tmp_path, rows)  # R1 rests on A and B, W1 on D and E
    (crossings / "labels").mkdir()
    (crossings / "labels" / "2026-11-11.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        + "".join(
            f"| W{n} | The hull was looked at again on day {n}, "
            + "and looked at once more, " * 10
            + f"to no end. | both | `{E}` |\n"
            for n in range(2, 47)
        )
        + "| W47 | The rigging is the newest work. | his | `55555555` |\n",
        encoding="utf-8",
    )
    store.build(crossings)
    text = frame.compose(crossings)
    quoted = text.split("## The person's own words, as they stand in the record\n\n")[1]
    assert "- `55555555`: The newest thing said about the rigging." in quoted
    assert f"`{A}`" not in quoted  # what the standing row rests on
    assert "- W1 (" not in text and f"`{D}`" not in quoted  # nor what a label the frame does not carry rests on
    assert frame.SIZE - len(text) < 700  # and the room that leaves goes to older work rows


def test_an_id_made_of_digits_alone_is_still_an_id(tmp_path):
    """About one id in forty has no letter in it. Such an id was taken for a line number and
    dropped from a label's anchors, so the label rested on less than it said."""
    from crossing import handover

    rows = ROWS + [row("user", "55555555", 20, "A message whose id has no letter in it.")]
    crossings, _ = home(tmp_path, rows)
    assert store.mark(crossings, "work", "his", "The rigging is next.", ["55555555", D])["written"] is True
    listed = store.listed(crossings, ids=("W2",))["labels"][0]
    assert listed["anchors"] == ["55555555", D]
    assert handover.named(
        "| W2 | The rigging is next. | his | `55555555`, `dddddddd` | and line 1234567 or 123456789"
    ) == ["55555555", D]
    assert store.thread(crossings, "55555555", 0)["labels"][0]["id"] == "W2"


def test_the_standing_lines_cross_whole_before_the_work_takes_room(tmp_path):
    """The standing lines are what a session that wakes is most likely to break if it does not
    hold them, and the newest of them are the ones it has never seen cross. While they fit in
    the frame at all they are carried whole, and the work rows take what is left; when they
    no longer fit, the frame says which are missing."""
    crossings, _ = home(tmp_path)
    (crossings / "labels").mkdir()
    rows = "".join(
        f"| R{n} | A standing line, number {n}, said once and meant to be kept for as long as the two of them work. "
        f"| his | `{A}` |\n"
        for n in range(2, 71)
    )
    work = "".join(f"| W{n} | A row about the work, number {n}. | both | `{D}` |\n" for n in range(2, 12))
    (crossings / "labels" / "2026-11-11.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n" + rows + work, encoding="utf-8"
    )
    store.build(crossings)
    text = frame.compose(crossings)
    standing = text.split("## Standing, about the two of you\n\n")[1].split("\n\n")[0]
    carried = standing.count("\n") + 1
    assert "- R1 (his)" in standing
    assert "## The work, newest first\n\n- W11 (both)" in text  # and the newest work still crosses
    assert 45 < carried < 70  # far more than half the frame's room, where it stopped before
    assert (
        f"{70 - carried} standing lines did not fit and are not carried: R{carried + 1} to R70; `labels` gives them."
        in text
    )
    few = frame.compose(home(tmp_path / "few")[0])
    assert "did not fit" not in few


# --- what was pulled ------------------------------------------------------------------------------


def test_what_is_pulled_through_the_door_is_noted_and_a_strike_takes_it_out(tmp_path):
    from crossing import second

    rows = ROWS + [row("user", "11111111", 10, WITH_PASTE)]
    crossings, _ = home(tmp_path, rows)
    project, log = str(crossings.parent), crossings / "reached.jsonl"
    through("thread", D, "--cwd", project)  # a look from a shell is not a pull
    assert not log.exists()
    through("thread", D, "--touch", "--cwd", project)
    through("thread", "11111111+1", "--touch", "--cwd", project)
    through("thread", "0a0a0a0a", "--touch", "--cwd", project)  # nothing found, nothing noted
    assert through("mark", "--touch", "--whose", "both", "--anchors", f"{D},{E}", "Marked.", "--cwd", project)[0] == 0
    assert through("mark", "--touch", "--anchors", "0a0a0a0a", "Refused.", "--cwd", project)[0] == 1
    pulls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [(p["verb"], p["ids"]) for p in pulls] == [
        ("thread", [D]),
        ("thread", ["11111111+1"]),
        ("mark", ["W2", D, E]),
    ]
    assert all(re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\+00:00", p["at"]) for p in pulls)
    assert "paint" not in log.read_text(encoding="utf-8")  # ids and times, and nothing of what was said
    assert log not in second.plain(crossings)  # the second copy was agreed for the archive, not for this

    store.strike(crossings, D)
    store.strike(crossings, "11111111")  # and its paste goes with it
    left = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [(p["verb"], p["ids"]) for p in left] == [("mark", ["W2", E])]
    store.strike(crossings, "session:session-")  # every message of the session; the label marked there still stands
    assert [json.loads(line)["ids"] for line in log.read_text(encoding="utf-8").splitlines()] == [["W2"]]
    store.strike(crossings, "W2")
    assert log.read_text(encoding="utf-8") == ""


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
