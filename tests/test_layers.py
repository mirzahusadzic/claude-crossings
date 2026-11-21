"""Layers: every line of the session's voice is the layer of the model that made it, the person's
own lines are no model's, and a model that arrives reads another's lines and does not reframe
them. The frame, the door's lists, stacks, the person's `layer` verb, and the note to the one who
arrives. No model, no network.

Run with pytest, or without it:  python3 tests/test_layers.py
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to  # noqa: E402
from test_nest import ASKED, BRANCH, DECLINED, LET_BE, ORDER, SESSION, TAG, TWO_ENDED, families_carried, nested, rows_of  # noqa: E402
from test_nest import DOOR as LEFT  # noqa: E402  (the made-up line at the door of those homes)
from test_nest import held as asked_home  # noqa: E402  (a home of a made-up session, its labels marked in turn)
from test_nest import made as tied_home  # noqa: E402  (a home of a made-up session with a line at the door)
from test_store import D, E, at_terminal, home, in_person, row, started_by, sweep, switched_on  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, hook, layer, serve, store  # noqa: E402

M1, M2, M0 = "model-one", "model-two", "model-zero"  # made-up names, no real model's
DAY = "2026-11-12"
TERN = "Their boat is called Tern and lies at mooring 41."  # R1: his, by no known model
HULL = "The hull is to be painted grey in spring."  # W1: both, by no known model
KEEL = "The keel is checked every autumn."  # R2: his, by model-one
WATCH = "The two of them keep the night watch together."  # R3: both, by model-one
CHAIN = "The anchor chain is to be looked at."  # W2: both, by model-one
FENDERS = "The fenders are to be counted."  # W3: the session's, by no known model
CARE = "Tern is kept with care the year round."
ASKS = re.compile(r"\bask(s|ed|ing)?\b", re.I)
TOLD = "This home also holds lines made with another model, {}: they are read here, they are not this session's own, and the door gives them."
MANY = TOLD.replace("another model", "other models")


def spoken(uid: str, minute: int, text: str, model: str) -> dict:
    made = row("assistant", uid, minute, [{"type": "text", "text": text}])
    made["message"]["model"] = model
    return made


def written(folder: Path, name: str, rows: list[dict]) -> Path:
    path = folder / f"{name}.jsonl"
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return path


def through(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with at_terminal(), contextlib.redirect_stdout(out):  # the person's own shell
        code = door.main(list(argv))
    return code, out.getvalue()


def said(name: str, **given) -> tuple[str, bool]:
    # A session a person sits in, unless the test says how the session was started (see serve.call).
    with started_by(os.environ.get("CLAUDE_CODE_ENTRYPOINT") or "cli"):
        answer = serve.handle(
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name, "arguments": given}}
        )
    return answer["result"]["content"][0]["text"], answer["result"]["isError"]


def section(text: str, heading: str) -> str:
    return text.split(f"## {heading}\n\n")[1].split("\n\n")[0]


def held(tmp_path: Path) -> tuple[Path, Path]:
    """A home that model-one has held: the page every home starts with (R1, W1, of no known model),
    a session `northern` whose own voice is model-one's, and four labels marked since, three of
    them by model-one (R2 the person's, R3 and W2 of its own layer) and one by no known model (W3)."""
    crossings, _ = home(tmp_path)
    north = written(
        tmp_path,
        "northern-0001",
        [
            row("user", "10000001", 10, "The anchor chain wants a look."),
            spoken("10000002", 11, "It does; the shackle is worn.", M1),
        ],
    )
    assert store.archive(north, crossings) == 2
    for kind, whose, sentence, anchor, model in (
        ("relation", "his", KEEL, D, M1),
        ("relation", "both", WATCH, "10000002", M1),
        ("work", "both", CHAIN, "10000001", M1),
        ("work", "session", FENDERS, E, ""),
    ):
        assert store.mark(crossings, kind, whose, sentence, [anchor], day=DAY, model=model)["written"]
    return crossings, north


def arrived(tmp_path: Path, crossings: Path) -> Path:
    """A session `southern` whose own voice is model-two's: a second model known in the home."""
    south = written(
        tmp_path,
        "southern-0002",
        [row("user", "20000001", 20, "And the fenders?"), spoken("20000002", 21, "Two of them are split.", M2)],
    )
    assert store.archive(south, crossings) == 2
    store.build(crossings)
    return south


# --- the frame ------------------------------------------------------------------------------------


def test_the_frame_for_a_model_that_arrives_carries_the_persons_lines_and_not_another_models(tmp_path):
    crossings, _ = held(tmp_path)
    text = frame.compose(crossings, model=M2)
    assert (
        section(text, "Standing, about the two of you")
        == f"- R1 (theirs): {TERN} [aaaaaaaa, bbbbbbbb]\n- R2 (theirs): {KEEL} [dddddddd]"
    )
    assert section(text, "The work, newest first") == (
        f"- W3 (session): {FENDERS} [eeeeeeee]\n- W1 (both): {HULL} [dddddddd, eeeeeeee]"
    )
    assert WATCH not in text and CHAIN not in text
    assert "The anchor chain wants a look." not in text  # the person's words beneath a line not carried are not shown
    assert text.count(TOLD.format(M1)) == 1
    assert text.index(TOLD.format(M1)) < text.index("## Standing")  # near the preamble, before any line
    assert text.startswith(frame.opening() + "\n\n" + TOLD.format(M1) + "\n\n") and not ASKS.search(TOLD)
    assert text.rstrip().endswith(
        "of the session's voice, made with more than one model, from 2026-11-11 to 2026-11-11, and 6 labels."
    )
    assert len(text) <= frame.SIZE


def test_the_same_home_seen_by_the_model_that_held_it_is_as_it_was(tmp_path):
    crossings, _ = held(tmp_path)
    today = frame.compose(crossings)  # no model known: as before layers
    assert frame.compose(crossings, model=M1) == today
    assert section(today, "Standing, about the two of you").splitlines()[2] == f"- R3 (both): {WATCH} [10000002]"
    assert f"- W2 (both): {CHAIN} [10000001]" in today and "another model" not in today
    assert "- `10000001`: The anchor chain wants a look." in today
    assert frame.compose(crossings, new=True, model=M1) == frame.compose(crossings, new=True)


def test_a_stack_by_another_model_over_the_persons_lines_lets_them_cross_as_themselves(tmp_path):
    crossings, _ = held(tmp_path)
    assert store.mark(crossings, "relation", "his", CARE, ["R1", "R2"], day=DAY, model=M1)["id"] == "R4"
    one, two = frame.compose(crossings, model=M1), frame.compose(crossings, model=M2)
    assert (
        section(one, "Standing, about the two of you")
        == f"- R3 (both): {WATCH} [10000002]\n- R4 (theirs): {CARE} [R1, R2]"
    )
    assert (
        section(two, "Standing, about the two of you")
        == f"- R1 (theirs): {TERN} [aaaaaaaa, bbbbbbbb]\n- R2 (theirs): {KEEL} [dddddddd]"
    )
    assert CARE not in two and frame.compose(crossings) == one
    # Two deep: a stack of no known model's over model-one's stack. Model-two carries the one over it,
    # and the person's lines beneath model-one's stack stay behind the stack that is carried.
    assert store.mark(crossings, "relation", "his", "All of it, kept.", ["R4", "R3"], day=DAY)["id"] == "R5"
    assert section(frame.compose(crossings, model=M2), "Standing, about the two of you") == (
        f"- R1 (theirs): {TERN} [aaaaaaaa, bbbbbbbb]\n- R2 (theirs): {KEEL} [dddddddd]\n- R5 (theirs): All of it, kept. [R4, R3]"
    )


def test_lines_whose_writer_is_not_known_are_carried_for_every_model(tmp_path):
    crossings, _ = held(tmp_path)
    for model in (M1, M2, M0, ""):
        text = frame.compose(crossings, model=model)
        assert (
            f"- W1 (both): {HULL}" in text and f"- W3 (session): {FENDERS}" in text and f"- R1 (theirs): {TERN}" in text
        ), model


def test_another_models_messages_alone_are_said_and_a_new_session_is_told_of_its_lines(tmp_path):
    crossings, _ = held(tmp_path)
    arrived(tmp_path, crossings)
    for kind in (
        "relation",
        "work",
    ):  # the labels of model-one's layer, struck: its messages are still another model's lines
        for label in store.listed(crossings, kind)["labels"]:
            if label["model"] == M1 and label["whose"] != "his":
                store.strike(crossings, label["id"])
    one = frame.compose(crossings, model=M1)
    assert TOLD.format(M2) in one and "made with more than one model" in one and WATCH not in one
    assert MANY.format(f"{M1} and {M2}") in frame.compose(crossings, model=M0)
    assert frame.elsewhere([M0, M1, M2]) == MANY.format(f"{M0}, {M1} and {M2}")
    # A session started new, in a home where all there is to carry is another model's.
    alone, _ = home(tmp_path / "alone")
    for key in ("R1", "W1"):
        store.strike(alone, key)
    assert store.mark(alone, "work", "both", CHAIN, [D], day=DAY, model=M1)["written"]
    assert frame.compose(alone, new=True, model=M1) != "" and frame.compose(alone, new=True) != ""
    fresh = frame.compose(alone, new=True, model=M2)
    assert TOLD.format(M1) in fresh and CHAIN not in fresh and "## The work" not in fresh
    store.strike(alone, "W2")
    assert frame.compose(alone, new=True, model=M2) == ""  # nothing at all to carry or to tell of: nothing, as before


# --- the sentence of other models' lines, and the frame's size -------------------------------------------------

ONE = "made-up-model-0-xxxxxxxxx"  # a made-up name of 25 characters
LONG = [f"other-model-{n}-" + "x" * 70 for n in range(1, 9)]  # eight made-up names of 84 characters, shown by 80
SPOKEN = ["b1000002", "b1000004", "b1000005", "b1000007", "b1000009", "b1000011", "b1000013", "b1000015"]
LEFT_WHOLE = f"- N1 (session): {LEFT} [{', '.join(TWO_ENDED)}]"  # the line at the door of these homes, whole
# The frames 56d3925 made at the least size of the homes below, one message of the session's in each by a model of
# 25 characters: how long the frame may be now, at the most; and how such a frame says the standing lines that did
# not fit, by count.
AT_56D3925 = {"full": 2498, "small": 2434}
COUNTED = {
    "full": "46 standing lines did not fit and are not carried; `labels` gives them.",
    "small": "1 standing line did not fit and is not carried; `labels` gives them.",
}


def lines_of_eight(tmp_path: Path) -> Path:
    """A home that holds eight messages of the session's voice, each made by one of eight models with long names, and
    nothing else."""
    project = tmp_path / "project"
    crossings = project / "crossings"
    crossings.mkdir(parents=True)
    switched_on(project)
    rows = [spoken(f"9000000{n}", n, f"Session line {n}.", LONG[n - 1]) for n in range(1, 9)]
    assert store.archive(written(tmp_path, "eight-0001", rows), crossings) == 8
    store.build(crossings)
    return crossings


def test_one_message_of_another_model_gives_a_frame_past_the_least_size_by_count_and_no_longer_than_it_was(tmp_path):
    """Guard: at the least size, the sentence about another model's lines and the closing's words for it took a frame
    that holds its size without them past it, by one message of a model of 25 characters, and nothing gave way for it:
    2,498 characters of 2,400 in a full home and 2,434 in a small one. Past the size asked, the frame is made again by
    count, and the sentence then names no model, saying only that there is another. The line at the door keeps its
    least, and the frame is no longer than it was: where its fixed sentences and that least are longer than the size,
    it is as long as they are."""
    for name, full in (("full", True), ("small", False)):
        crossings = tied_home(tmp_path / name, rows=rows_of(ORDER, models={"b1000002": ONE}), full=full)
        for session in (SESSION, ""):
            made = frame.compose(crossings, frame.LEAST, model=M2, session=session)
            assert COUNTED[name] in made.split("\n\n"), (name, session)  # by count
            assert made.startswith(frame.opening() + "\n\n" + TOLD.replace(", {}", "") + "\n\n"), (name, session)
            assert LEFT_WHOLE in made.split("\n"), (name, session)  # the line at the door, at its least or more
            assert len(made) <= AT_56D3925[name], (name, session, len(made))


def test_eight_long_names_of_other_models_give_way_to_fewer_and_to_how_many_they_are_at_the_least_size(tmp_path):
    """Guard: eight models of long names, each shown by its first 80 characters, took the least frame to 2,728
    characters in a home of their messages alone. The sentence names as many of them as the frame has room for and
    counts the rest, and the frame is held to its size; in a full home, where it has room for none, it says how many
    they are. It is never left out, and the line at the door keeps its least."""
    eight = frame.compose(lines_of_eight(tmp_path / "eight"), frame.LEAST, model=M2)
    assert len(eight) <= frame.LEAST
    assert MANY.format(f"{LONG[0][:80]}, {LONG[1][:80]}, {LONG[2][:80]} and 5 more") in eight
    full = tied_home(tmp_path / "full", rows=rows_of(ORDER, models=dict(zip(SPOKEN, LONG))), full=True)
    for session in (SESSION, ""):
        made = frame.compose(full, frame.LEAST, model=M2, session=session)
        assert TOLD.replace("another model, {}", "8 other models") in made and COUNTED["full"] in made, session
        assert LEFT_WHOLE in made.split("\n"), session


def test_eight_long_names_of_other_models_are_all_named_where_the_frame_has_room(tmp_path):
    """Pin: at the usual size a full home with eight models of long names is held to its size with each of them named,
    as before: the sentence gives way only where the frame would otherwise pass its size."""
    full = tied_home(tmp_path, rows=rows_of(ORDER, models=dict(zip(SPOKEN, LONG))), full=True)
    for session in (SESSION, ""):
        made = frame.compose(full, frame.SIZE, model=M2, session=session)
        assert len(made) <= frame.SIZE and LEFT_WHOLE in made.split("\n"), session
        assert MANY.format(", ".join(each[:80] for each in LONG[:7]) + f" and {LONG[7][:80]}") in made, session


@in_person
def test_the_frame_hook_and_the_door_compose_for_the_model_that_is_there(tmp_path):
    return  # retired: it pins the frame's two lists at a cut, and a cut's frame is packed now; see tests/test_sample_join.py
    crossings, north = held(tmp_path)
    (crossings / "mode").write_text("beside\n", encoding="utf-8")
    (crossings / "carry").write_text("note\n", encoding="utf-8")
    event = {
        "hook_event_name": "SessionStart",
        "source": "compact",
        "transcript_path": str(north),
        "cwd": str(crossings.parent),
        "session_id": "northern-0001",
    }
    context = lambda out: json.loads(out)["hookSpecificOutput"]["additionalContext"]  # noqa: E731
    assert context(hook.carried(event)) == frame.compose(crossings, frame.MOST)  # by what it said last: model-one
    assert TOLD.format(M1) in context(hook.carried({**event, "model": M2}))
    project = str(crossings.parent)
    assert TOLD.format(M1) in through("frame", "--cwd", project, "--model", M2)[1]
    assert through("frame", "--cwd", project, "--transcript", str(north))[1] == frame.compose(crossings)
    (crossings / layer.THERE).write_text(f"northern {M2} 2099-01-01T00:00:00+00:00\n", encoding="utf-8")
    assert (
        TOLD.format(M1) in through("frame", "--cwd", project, "--transcript", str(north))[1]
    )  # what its hooks were told


# --- the door's lists -----------------------------------------------------------------------------


def test_the_doors_lists_name_the_model_only_where_two_are_known(tmp_path):
    crossings, north = held(tmp_path)
    project = str(crossings.parent)
    assert store.mark(crossings, "next", "session", "The chain first.", ["10000002"], day=DAY, model=M1)["id"] == "N1"
    one = {
        verb: through(verb, *rest, "--cwd", project)[1]
        for verb, rest in (
            ("labels", ()),
            ("look", ()),
            ("thread", ("10000002", "--around", "0")),
            ("find", ("chain",)),
        )
    }
    for verb, out in one.items():
        assert "written by" not in out and f"({M1})" not in out, verb
    assert one["labels"] == (
        f"- N1 (session, 2026-11-11): The chain first. [10000002]\n"
        f"- W3 (session, 2026-11-11): {FENDERS} [eeeeeeee]\n"
        f"- W2 (both, 2026-11-11): {CHAIN} [10000001]\n"
        f"- W1 (both, 2026-11-11): {HULL} [dddddddd, eeeeeeee]\n"
        "3 standing lines about the two of you (R1 to R3) are not listed here: labels --kind relation.\n"
    )
    assert (
        f"- W2 (both, 2026-11-11, written by {M1}): {CHAIN}" in through("labels", "W2", "--cwd", project)[1]
    )  # given whole, as before
    arrived(tmp_path, crossings)
    two = through("labels", "--cwd", project)[1]
    assert f"- W2 (both, 2026-11-11, written by {M1}): {CHAIN} [10000001]\n" in two
    assert f"- N1 (session, 2026-11-11, written by {M1}): The chain first." in two
    assert f"- W3 (session, 2026-11-11): {FENDERS}" in two  # not known: nothing said of it
    standing = through("labels", "--kind", "relation", "--cwd", project)[1]
    assert (
        f"- R2 (theirs, 2026-11-11): {KEEL}" in standing
        and f"- R3 (both, 2026-11-11, written by {M1}): {WATCH}" in standing
    )
    look = through("look", "--cwd", project)[1]
    assert (
        f"- N1 (the session's, written by {M1}): The chain first." in look
        and f"- W2 (both, written by {M1}): {CHAIN}" in look
    )
    thread = through("thread", "10000002", "--around", "1", "--cwd", project)[1]
    assert f"`10000002` the session ({M1}), 2026-11-11 09:11 UTC" in thread and "`10000001` the person, " in thread
    assert f"- R3 (relation, both, written by {M1}): {WATCH}" in thread
    found = through("find", "chain", "--cwd", project)[1]
    assert f"- W2 (work, both, written by {M1}): {CHAIN}" in found
    assert f"`20000002` the session ({M2}), " in through("find", "split", "--cwd", project)[1]
    assert (
        f"- R2 (relation, theirs): {KEEL}" in through("find", "keel", "--cwd", project)[1]
    )  # the person's line: no model's
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert f"written by {M1}" in said("labels")[0] and f"({M1})" in said("thread", id="10000002")[0]


def test_a_home_with_one_known_model_reads_byte_for_byte_as_before(tmp_path):
    """The frame and the lists of a home with one known model, set down as this make writes them."""
    crossings, _ = held(tmp_path)
    project = str(crossings.parent)
    assert store.known(crossings) == [M1]
    labels = through("labels", "--kind", "relation", "--cwd", project)[1]
    assert labels == (
        f"- R3 (both, 2026-11-11): {WATCH} [10000002]\n"
        f"- R2 (theirs, 2026-11-11): {KEEL} [dddddddd]\n"
        f"- R1 (theirs, 2026-11-11): {TERN} [aaaaaaaa, bbbbbbbb]\n"
    )
    text = frame.compose(crossings, model=M1)
    assert text == frame.compose(crossings) and text.endswith(
        "## The person's own words, as they stand in the record\n\n"
        "- `10000001`: The anchor chain wants a look.\n- `dddddddd`: We paint the hull grey in spring\n\n"
        "The store holds 3 messages of the person's and 3 of yours, from 2026-11-11 to 2026-11-11, and 6 labels.\n"
    )
    assert section(text, "Standing, about the two of you") == (
        f"- R1 (theirs): {TERN} [aaaaaaaa, bbbbbbbb]\n- R2 (theirs): {KEEL} [dddddddd]\n- R3 (both): {WATCH} [10000002]"
    )
    plain, _ = home(tmp_path / "plain")  # and a home with none
    assert store.known(plain) == [] and frame.compose(plain, model=M2) == frame.compose(plain)


# --- a silencing across models ------------------------------------------------------------------------------------


def refused_and_silenced(folder: Path, asking: str, other: str, whose: str) -> Path:
    """A home of a made-up session whose answers `asking` made, so that the server asks as that model: a line at the
    door on the person's ask and the session's declining answer, a refusal written under `asking` on the ask (X1),
    and a silencing of it written under `other` (S1), whose it is as `whose` gives it: the person's (`their`) or both
    their own on the person's next message, or the session's own on its answer to it."""
    rows = rows_of("ababababababab", ASKED, {f"b1{n:06d}": asking for n in range(2, 15, 2)})
    door_ = ("next", "session", LEFT, ["a1000003", "b1000004"])
    crossings = asked_home(folder, [], rows=rows, door=door_)
    assert store.mark(crossings, "refused", "session", BRANCH, ["a1000003"], day=DAY, model=asking)["written"]
    on = "b1000012" if whose == "session" else "a1000011"
    assert store.mark(crossings, "silenced", whose, LET_BE, ["X1", on], day=DAY, model=other)["written"]
    return crossings


def test_the_persons_silencing_puts_a_refusal_to_rest_for_every_model_and_the_sessions_for_its_own_alone(tmp_path):
    """Guard: a refusal written under one model and silenced under another was carried in the first model's frame
    whoever the silencing was, the person too, while `look` and `labels` called it silenced: "0 refusals standing, 1
    silenced (S1)" and "cooled beneath S1". The person's silencing, theirs or both their own, puts it to rest in every
    model's frame now, and `look` and `labels` call it silenced; a session's own silencing under another model leaves
    this model's refusal standing in this model's frame, and `look`, `labels` and `status` say it stands here, for the
    model that asks, as the server's `crossing` takes it: that of the session that spoke last. And so the other way
    about. Beside the ask, the session's answer stands by its id alone in every case."""
    for asking, other in ((M1, M2), (M2, M1)):
        for whose in ("their", "both", "session"):
            crossings = refused_and_silenced(tmp_path / f"{asking}-{whose}", asking, other, whose)
            on = frame.compose(crossings, session=SESSION, model=asking)
            with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
                crossing, looked, listed, status = (said(name, **given)[0] for name, given in (
                    ("crossing", {}), ("look", {}), ("labels", {"ids": ["X1"]}), ("status", {}),
                ))  # fmt: skip
            assert crossing.startswith(on), (asking, whose)  # the server asks as the session that spoke last
            assert nested(on) == ["     · after it, the session (N1): `b1000004`"] and DECLINED[0] not in on, (
                asking,
                whose,
            )
            x1 = next(line for line in listed.split("\n") if line.startswith("- X1 ("))
            if whose != "session":  # the person's: at rest for every model
                assert families_carried(on) == [] and BRANCH not in on, (asking, whose)
                assert "0 refusals standing, 1 silenced (S1)" in looked and ", cooled beneath S1," in x1, (
                    asking,
                    whose,
                )
                assert "Of the refusals, 0 stand and 1 is silenced." in status, (asking, whose)
                assert "Of the labels: 1 cooled, 0 misaligned, 0 unresolved." in status, status
            else:  # the session's own under another model: this model's refusal stands here, whole
                assert families_carried(on) == ["X1"] and BRANCH in on, (asking, whose)
                assert "1 refusal standing (X1); X1 is at rest for another model alone, not for this one" in looked
                assert "silenced (S1)" not in looked and "cooled beneath" not in x1, (asking, x1)
                assert ", standing here: S1 puts it to rest for another model alone," in x1, x1
                assert (
                    "Of the refusals, 1 stands and 0 are silenced; X1 is at rest for another model alone, not for this "
                    "one." in status
                ), status
                assert "Of the labels:" not in status, status  # X1 is no label cooled beneath another, here
                # and for the model that wrote the silencing, its own works as it does: the family is at rest there
                assert BRANCH not in frame.compose(crossings, session=SESSION, model=other)
                assert store.refusals(crossings, other) == {"standing": [], "silenced": ["S1"]}


def test_in_a_home_of_one_model_a_refusal_and_its_silencing_read_as_they_did(tmp_path):
    """Pin: where the refusal and its silencing are of the one model the home knows, the frame for that model and
    what `look`, `labels` and `status` answer through the server, which asks for it, are what they are with no model
    named, as before: the family at rest, no line of it carried, and no word of another model."""
    for whose in ("their", "session"):
        crossings = refused_and_silenced(tmp_path / whose, M1, M1, whose)
        assert frame.compose(crossings, session=SESSION, model=M1) == frame.compose(crossings, session=SESSION)
        with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
            served = [
                said(name, **given)[0] for name, given in (("look", {}), ("labels", {"ids": ["X1"]}), ("status", {}))
            ]
        project = str(crossings.parent)
        plain = [
            through(name, *more, "--cwd", project, "--bare")[1].rstrip("\n")
            for name, *more in (["look"], ["labels", "X1"], ["status"])
        ]
        assert served == plain and "another model" not in "".join(served), whose
        assert "0 refusals standing, 1 silenced (S1)" in served[0] and ", cooled beneath S1" in served[1], whose


def test_a_family_judged_again_under_one_model_and_silenced_under_another_stands_here_by_its_newest_judgment(tmp_path):
    """X1 and its judgment X2 written under model-one, and the session's own silencing S1 under model-two: the index
    carries S1 and cools X1 and X2 beneath it. For model-one, as the server asks, the family stands here by X2, the
    newest of its own layer, and X1 is cooled beneath X2, not beneath S1, which puts it to rest for model-two alone.
    For model-two, and with no model named, both stay cooled beneath S1."""
    rows = rows_of("ababababababab", ASKED, {f"b1{n:06d}": M1 for n in range(2, 15, 2)})
    crossings = asked_home(tmp_path, [], rows=rows, door=("next", "session", LEFT, ["a1000003", "b1000004"]))
    for kind, sentence, anchors, model in (
        ("refused", BRANCH, ["a1000003"], M1),
        ("refused", TAG, ["X1", "a1000007"], M1),
        ("silenced", LET_BE, ["X2", "b1000012"], M2),
    ):
        assert store.mark(crossings, kind, "session", sentence, anchors, day=DAY, model=model)["written"], sentence
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):  # model-one's session spoke last
        looked, listed, status = (said(name, **given)[0] for name, given in (
            ("look", {}), ("labels", {"ids": ["X1"]}), ("status", {}),
        ))  # fmt: skip
    clause = "X2 is at rest for another model alone, not for this one"
    assert f"; 1 refusal standing (X2); {clause}." in looked, looked
    assert listed.split("\n") == [
        f"- X1 (refused, session, 2026-11-11, cooled beneath X2, written by model-one): {BRANCH} [a1000003]",
        "  - X2 (refused, session, 2026-11-11, standing here: S1 puts it to rest for another model alone, written by "
        f"model-one): {TAG} [X1, a1000007]",
        f"  - S1 (silenced, session, 2026-11-11, written by model-two): {LET_BE} [X1, b1000012]",
    ], listed
    assert "Of the labels: 1 cooled, 0 misaligned, 0 unresolved." in status, status
    assert f"Of the refusals, 1 stands and 0 are silenced; {clause}." in status, status
    assert families_carried(frame.compose(crossings, session=SESSION, model=M1)) == ["X2"]
    for model in (M2, ""):
        found = store.listed(crossings, ids=("X1",), model=model)["labels"]
        states = [(row["id"], row["state"], row["parent"]) for row in found]
        assert states == [("X1", "cooled", "S1"), ("X2", "cooled", "S1"), ("S1", "carried", None)], (model, states)
    assert families_carried(frame.compose(crossings, session=SESSION, model=M2)) == []


# --- a family that is another model's alone -------------------------------------------------------------------------

SHACKLE = "The shackle is not to be changed before the survey."  # X1, model-one's refusal of the person's ask
SURVEYED = "The survey is done, so the shackle may be changed."  # S1, model-one's session's own silencing of it


def alone(tmp_path: Path, silenced: bool) -> Path:
    """The home model-one held and model-two's session spoke in last (see `held` and `arrived`), with a refusal
    written under model-one on the person's message (X1); with `silenced`, a silencing of it written under model-one,
    the session's own, on its answer (S1). Every label of the family is of model-one's layer."""
    crossings, _ = held(tmp_path)
    arrived(tmp_path, crossings)
    assert store.mark(crossings, "refused", "session", SHACKLE, ["10000001"], day=DAY, model=M1)["written"]
    if silenced:
        assert store.mark(crossings, "silenced", "session", SURVEYED, ["X1", "10000002"], day=DAY, model=M1)["written"]
    return crossings


def answered(crossings: Path) -> tuple[str, str, str, str]:
    """What the server's crossing, look, labels X1 and status answer: for the model of the session that spoke last."""
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        return tuple(said(name, **given)[0] for name, given in (  # type: ignore[return-value]
            ("crossing", {}), ("look", {}), ("labels", {"ids": ["X1"]}), ("status", {}),
        ))  # fmt: skip


def test_a_refusal_of_another_models_alone_is_counted_for_no_family_here_and_said_to_be_that_models(tmp_path):
    """Guard: a refusal written under model-one and asked about by model-two is carried in no family of model-two's
    frame, while look, labels and status called it standing for model-two, with no clause: "1 refusal standing (X1)",
    a row of no state, "Of the refusals, 1 stands". For model-two it is counted neither standing nor silenced now, and
    one clause, in the words the door has, says it stands for another model alone. For model-one, and with no model
    named at a terminal, it stands, as before."""
    crossings = alone(tmp_path, silenced=False)
    crossing, looked, listed, status = answered(crossings)
    on = frame.compose(crossings, session="southern", model=M2)
    assert crossing.startswith(on) and families_carried(on) == [] and SHACKLE not in on  # the server asks as model-two
    clause = "X1 stands for another model alone, not for this one"
    assert f"; 0 refusals standing; {clause}." in looked and "1 refusal standing" not in looked, looked
    x1 = next(line for line in listed.split("\n") if line.startswith("- X1 ("))
    row = "another model's alone, standing there"  # the row is the label's own, and does not name its key again
    assert x1 == f"- X1 (refused, session, 2026-11-11, {row}, written by model-one): {SHACKLE} [10000001]", x1
    assert f" Of the refusals, 0 stand and 0 are silenced; {clause}." in status, status
    # For the model that wrote it the family stands, and with no model named; its frame carries it, as before.
    assert families_carried(frame.compose(crossings, session="northern", model=M1)) == ["X1"]
    assert store.refusals(crossings, M1) == store.refusals(crossings) == {"standing": ["X1"], "silenced": []}
    plain = through("look", "--cwd", str(crossings.parent), "--bare")[1]
    assert "; 1 refusal standing (X1)." in plain and "another model" not in plain, plain


def test_a_refusal_at_rest_in_another_models_layer_alone_is_counted_for_no_family_here_and_said_to_be_that_models(
    tmp_path,
):
    """Guard: a refusal written under model-one, and silenced by model-one's session, asked about by model-two, is
    carried in no family of model-two's frame, while look, labels and status called it silenced for model-two, with no
    clause: "1 silenced (S1)", a row of no state, "1 is silenced". For model-two it is counted neither silenced nor
    standing now, and one clause says it is another model's alone, at rest there: "is at rest for another model
    alone", which the door says of a family that stands here, would be false. For model-one, and with no model named
    at a terminal, it is silenced, as before."""
    crossings = alone(tmp_path, silenced=True)
    crossing, looked, listed, status = answered(crossings)
    on = frame.compose(crossings, session="southern", model=M2)
    assert crossing.startswith(on) and families_carried(on) == [] and SHACKLE not in on and SURVEYED not in on
    clause = "S1 is another model's alone, at rest there"
    assert f"; 0 refusals standing; {clause}." in looked and "silenced (S1)" not in looked, looked
    rows = listed.split("\n")
    assert rows[:2] == [
        f"- X1 (refused, session, 2026-11-11, cooled beneath S1, written by model-one): {SHACKLE} [10000001]",
        f"  - S1 (silenced, session, 2026-11-11, another model's alone, at rest there, written by model-one): "
        f"{SURVEYED} [X1, 10000002]",
    ], rows
    assert f" Of the refusals, 0 stand and 0 are silenced; {clause}." in status, status
    assert families_carried(frame.compose(crossings, session="northern", model=M1)) == []
    assert store.refusals(crossings, M1) == store.refusals(crossings) == {"standing": [], "silenced": ["S1"]}
    plain = through("look", "--cwd", str(crossings.parent), "--bare")[1]
    assert "; 0 refusals standing, 1 silenced (S1)." in plain and "another model" not in plain, plain


# --- stacks are scoped to one's own layer -----------------------------------------------------------


def test_a_stack_over_another_models_line_is_refused_and_over_the_persons_accepted(tmp_path):
    crossings, _ = held(tmp_path)
    pages = {page: page.read_text(encoding="utf-8") for page in store.pages(crossings)}
    out = store.mark(crossings, "relation", "both", CARE, ["R3", "R1"], day=DAY, model=M2, facing=M2)
    assert out == {
        "written": False,
        "why": "R3 was written by another model, model-one, and a stack stands over the "
        "person's lines, its own model's and those of no known model alone",
    }
    why = out["why"]
    assert "\n" not in why and why.count(". ") == 0 and not ASKS.search(why) and "/" not in why
    assert {page: page.read_text(encoding="utf-8") for page in store.pages(crossings)} == pages
    assert store.mark(crossings, "relation", "both", CARE, ["R3"], day=DAY, model=M1, facing=M1)[
        "written"
    ]  # its own: R4
    store.strike(crossings, "R4")
    took = store.mark(
        crossings, "relation", "his", CARE, ["R2", "R1"], day=DAY, model=M2, facing=M2
    )  # the person's lines
    assert (took["written"], took["id"], took["beneath"]) == (True, "R5", ["R2", "R1"])
    assert store.listed(crossings, ids=("R5",))["labels"][0]["model"] == M2
    assert store.mark(crossings, "work", "both", "Hull and fenders.", ["W1", "W3"], day=DAY, facing=M2)[
        "written"
    ]  # no known model's
    assert store.mark(crossings, "work", "both", "The chain, read.", ["10000002"], day=DAY, model=M2, facing=M2)[
        "written"
    ]  # resting on, not reframing
    assert store.mark(crossings, "next", "session", "The chain is model-one's.", ["10000002"], day=DAY, facing=M2)[
        "written"
    ]
    assert store.mark(crossings, "work", "both", "Unscoped.", ["W2"], day=DAY)[
        "written"
    ]  # not known who marks: as before


def test_a_stack_reaches_no_deeper_into_another_layer_and_takes_no_place_of_its_stack(tmp_path):
    crossings, _ = held(tmp_path)
    assert (
        store.mark(crossings, "work", "both", "The chain, gathered.", ["W2"], day=DAY)["id"] == "W4"
    )  # no known model's, over model-one's
    assert store.mark(crossings, "work", "both", "All of it.", ["W4", "W1"], day=DAY, facing=M2)["why"].startswith(
        "W2 was written by another model, model-one"
    )
    assert store.mark(crossings, "work", "both", "All of it.", ["W4", "W1"], day=DAY, facing=M1)[
        "written"
    ]  # W5, model-one's own reach
    fresh, _ = held(tmp_path / "fresh")
    assert store.mark(fresh, "work", "both", "The fenders, by model-one.", ["W3"], day=DAY, model=M1)["id"] == "W4"
    page = fresh / "labels" / f"{DAY}.md"
    page.write_text(
        page.read_text(encoding="utf-8").replace(FENDERS, "The fenders are to be mended."), encoding="utf-8"
    )
    store.build(fresh)
    assert store.listed(fresh, ids=("W4",))["labels"][0]["state"] == "misaligned"
    assert store.mark(fresh, "work", "both", "Mended.", ["W3"], day=DAY, facing=M2) == {
        "written": False,
        "why": "W4 is a stack of another model's, model-one, and is written again by that model alone",
    }
    again = store.mark(fresh, "work", "both", "Mended.", ["W3"], day=DAY, facing=M1)
    assert again["written"] and again["replaced"] == ["W4"]


def test_the_door_and_its_server_refuse_a_reframing_by_the_model_that_is_there(tmp_path):
    crossings, north = held(tmp_path)
    south = arrived(tmp_path, crossings)
    project = str(crossings.parent)
    assert through("mark", "--kind", "relation", "--anchors", "R3", CARE, "--cwd", project, "--model", M2) == (
        1,
        "not marked: R3 was written by another model, model-one, and a stack stands over the person's lines, its own "
        "model's and those of no known model alone\n",
    )
    assert (
        through("mark", "--kind", "relation", "--anchors", "R3", CARE, "--cwd", project, "--transcript", str(south))[0]
        == 1
    )
    given = {"sentence": CARE, "anchors": ["R3"], "kind": "relation"}
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__plugin_crossings_door__mark",
        "tool_input": given,
        "transcript_path": str(south),
        "cwd": project,
        "session_id": "southern-0002",
    }
    with set_to(CLAUDE_PROJECT_DIR=project), started_by("cli"):
        assert hook.run(event) is None
        assert (crossings / layer.CALLING).read_text(encoding="utf-8") == f"{layer.digest('mark', given)} {M2}\n"
        assert said("mark", **given) == (
            "not marked: R3 was written by another model, model-one, and a stack stands over "
            "the person's lines, its own model's and those of no known model alone",
            False,
        )
        assert (crossings / layer.CALLING).read_text(encoding="utf-8") == ""  # taken: no later call is read by it
        assert hook.run({**event, "tool_input": {**given, "anchors": ["R2"]}}) is None
        assert said("mark", **{**given, "anchors": ["R2"]}) == ("marked R4", False)  # the person's line
        assert store.listed(crossings, ids=("R4",))["labels"][0]["model"] == M2  # signed as it was marked
        # A call no hook handed a model for: not known, and so not layered.
        assert said("mark", sentence="Read, not reframed.", anchors=["W2"]) == ("marked W4", False)
        # The hook before a subagent's call, or another handle's, or one with odd arguments, hands nothing.
        for odd in (
            {**event, "agent_id": "a1"},
            {**event, "tool_name": "mcp__plugin_crossings_door__find"},
            {**event, "tool_input": "odd"},
            {**event, "transcript_path": "", "session_id": "nobody00-1"},
        ):
            assert hook.run(odd) is None
        assert (crossings / layer.CALLING).read_text(encoding="utf-8") == ""
        assert (
            hook.run(
                {**event, "tool_input": {**given, "sentence": "Taken by the north."}, "transcript_path": str(north)}
            )
            is None
        )
        assert (crossings / layer.CALLING).read_text(encoding="utf-8").endswith(f" {M1}\n")
        assert said("mark", **given) == ("marked R5", False)  # another call's line is not this one's
    with started_by(None):  # a session no person sits in hands nothing over
        assert hook.run({**event, "tool_input": {**given, "sentence": "Unattended."}}) is None
    assert len((crossings / layer.CALLING).read_text(encoding="utf-8").splitlines()) == 1


def test_the_hand_off_keeps_a_small_file_and_reads_no_line_that_is_not_one(tmp_path):
    crossings, _ = held(tmp_path)
    given = {"sentence": "A.", "anchors": [D]}
    for n in range(layer.KEPT + 10):
        layer.hand(crossings, "mark", {"sentence": f"{n}.", "anchors": [D]}, M1)
    (crossings / layer.CALLING).write_text(
        (crossings / layer.CALLING).read_text(encoding="utf-8") + f"{layer.digest('mark', given)} two words\n\n",
        encoding="utf-8",
    )
    assert layer.handed(crossings, "mark", given) == ""  # its line is no line of this file: taken out all the same
    assert len((crossings / layer.CALLING).read_text(encoding="utf-8").splitlines()) == layer.KEPT
    assert layer.handed(crossings, "mark", {"sentence": "1.", "anchors": [D]}) == ""  # gone with the oldest
    assert layer.handed(crossings, "mark", {"sentence": f"{layer.KEPT + 9}.", "anchors": [D]}) == M1
    (crossings / layer.CALLING).unlink()
    (crossings / layer.CALLING).symlink_to(tmp_path / "elsewhere.txt")
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert said("mark", **given) == (door.LINKED, False)
    assert not (tmp_path / "elsewhere.txt").exists()


# --- the person's verb ------------------------------------------------------------------------------


def test_layer_signs_only_what_has_no_model_and_refuses_a_key_with_a_space(tmp_path):
    crossings, north = held(tmp_path)
    project = str(crossings.parent)
    signs = (crossings / store.MODELS).read_text(encoding="utf-8")
    archive = {page.name: page.read_text(encoding="utf-8") for page in (crossings / "said").glob("*.jsonl")}
    for argv in (
        ["layer"],
        ["layer", "model one"],
        ["layer", "model", "one"],
        ["layer", "model#one"],
        ["layer", "<synthetic>"],
    ):
        assert through(*argv, "--cwd", project) == (
            2,
            "layer takes one model's key, with no space in it: the model the lines with none were made with.\n",
        ), argv
    assert (crossings / store.MODELS).read_text(encoding="utf-8") == signs
    assert {page.name: page.read_text(encoding="utf-8") for page in (crossings / "said").glob("*.jsonl")} == archive
    store.strike(crossings, "W1")
    with open(crossings / "said" / "northern.jsonl", "a", encoding="utf-8") as handle:
        handle.write("not a message\n")  # a line that is no message is left as it is
    assert through("layer", M0, "--cwd", project) == (
        0,
        f"Signed 2 labels and 2 messages of the session's as made with {M0}; nothing that had a model was changed.\n",
    )
    assert {
        label["id"]: label["model"]
        for kind in ("relation", "work")
        for label in store.listed(crossings, kind)["labels"]
    } == {"R1": M0, "R2": M1, "R3": M1, "W2": M1, "W3": M0}
    kept = [
        json.loads(line)
        for page in sorted((crossings / "said").glob("*.jsonl"))
        for line in page.read_text(encoding="utf-8").splitlines()
        if line.startswith("{")
    ]
    assert {r["id"]: r.get("model") for r in kept if r["voice"] == "session"} == {
        "bbbbbbbb": M0,
        "eeeeeeee": M0,
        "10000002": M1,
    }
    assert all("model" not in r for r in kept if r["voice"] == "his")
    assert (crossings / "said" / "northern.jsonl").read_text(encoding="utf-8").endswith("\nnot a message\n")
    assert [line for line in (crossings / store.MODELS).read_text(encoding="utf-8").splitlines() if "@" in line][
        -2:
    ] == [f"R1@{store.digest(TERN)} {M0}", f"W3@{store.digest(FENDERS)} {M0}"]
    assert through("layer", M1, "--cwd", project)[1] == (
        f"Signed 0 labels and 0 messages of the session's as made with {M1}; nothing that had a model was changed.\n"
    )
    assert store.listed(crossings, ids=("W3",))["labels"][0]["model"] == M0
    # Once signed, a line of no known model is of a layer, and is read as one.
    text = frame.compose(crossings, model=M2)
    assert FENDERS not in text and f"- R1 (theirs): {TERN}" in text and MANY.format(f"{M1} and {M0}") in text
    assert store.mark(crossings, "work", "both", "Over it.", ["W3"], day=DAY, facing=M2)["why"].startswith(
        "W3 was written by another model, model-zero"
    )
    # The server offers no such handle.
    assert "layer" not in serve.NAMES
    answer = serve.handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "layer", "arguments": {}}}
    )
    assert "error" in answer


# --- who is there, and the note to the one who arrives ---------------------------------------------


def test_the_one_who_arrives_is_told_once_a_change_and_never_where_nothing_changed(tmp_path):
    crossings, north = held(tmp_path)
    project = str(crossings.parent)
    wired = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PostModelSwitch"]
    assert [h["command"] for g in wired for h in g["hooks"]] == ['"${CLAUDE_PLUGIN_ROOT}/hooks/run.sh"']
    switch = {
        "hook_event_name": "PostModelSwitch",
        "transcript_path": str(north),
        "cwd": project,
        "session_id": "northern-0001",
        "from_model": M1,
        "to_model": M2,
        "source": "command",
    }
    start = {
        "hook_event_name": "SessionStart",
        "source": "resume",
        "transcript_path": str(north),
        "cwd": project,
        "session_id": "northern-0001",
    }

    def told(out):
        return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else None

    with started_by("cli"):
        assert hook.run({**start, "model": M1}) is None  # the model that spoke last: nothing to tell
        assert layer.there(crossings, "northern")[0] == M1 and layer.current(crossings, "northern") == M1
        with open(north, "a", encoding="utf-8") as handle:  # said just before the switch: archived by the switch's hook
            handle.write(json.dumps(spoken("10000003", 12, "And the windlass with it.", M1)) + "\n")
        assert json.loads(hook.run(switch))["hookSpecificOutput"] == {
            "hookEventName": "PostModelSwitch",
            "additionalContext": hook.arrival(),
        }
        assert store.thread(crossings, "10000003", 0)["found"]
        assert layer.current(crossings, "northern") == M2
        assert hook.run(switch) is None and hook.run({**start, "model": M2}) is None  # once a change
        assert hook.run({**switch, "to_model": M1}) is None  # back to the one that spoke last: its own session
        assert hook.run({**switch, "to_model": M2}) is not None  # and away from it again: a change of its own
        for odd in (
            {**switch, "to_model": ""},
            {**switch, "to_model": None},
            {**switch, "to_model": "<synthetic>"},
            {**switch, "to_model": M0, "agent_id": "a1"},
            {**switch, "to_model": M0, "transcript_path": "", "session_id": ""},
        ):
            assert hook.run(odd) is None
        # Its model is not known, so nothing of arriving; another session spoke here since it last did, and that is said.
        assert (
            told(hook.run({**start, "session_id": "session-0001", "transcript_path": "", "model": M2}))
            == hook.moved_on()
        )
        assert (
            told(hook.run({**start, "session_id": "nobody00-1", "transcript_path": "", "model": M2})) is None
        )  # it never spoke
        # A resume on another model than the one that spoke last, in a session never seen arriving.
        lines = (crossings / layer.THERE).read_text(encoding="utf-8")
        (crossings / layer.THERE).write_text("", encoding="utf-8")
        assert told(hook.run({**start, "model": M0})) == hook.arrival()
        assert not ASKS.search(hook.arrival()) and not re.search(r"\d", hook.arrival())
        (crossings / layer.THERE).unlink()
        (crossings / layer.THERE).mkdir()  # where it cannot be kept, nothing is said
        assert hook.run({**start, "model": M2}) is None
        (crossings / layer.THERE).rmdir()
        (crossings / layer.THERE).write_text(lines, encoding="utf-8")
    with started_by(None):  # nobody sits in it: nothing is kept of it, and nothing said
        assert hook.run({**switch, "to_model": M0}) is None and layer.there(crossings, "northern")[0] == M2


def test_which_model_is_there_is_the_newer_of_what_the_hooks_were_told_and_what_was_said(tmp_path):
    crossings, north = held(tmp_path)
    (crossings / layer.THERE).write_text(
        "# a note\nnot a line\n"
        f"northern {M2} 2026-11-11T09:05:00+00:00\n"  # told before model-one last spoke (09:11)
        f"northern {M0} not-a-time\n"  # a line that is not one is passed over
        f"southern {M0} 2026-11-11T09:00:00+00:00\n",
        encoding="utf-8",
    )
    assert layer.there(crossings, "northern") == (M2, "2026-11-11T09:05:00+00:00")
    assert (
        layer.current(crossings, "northern") == M1
    )  # a harness that never said the switch back: read by what was said
    layer.arrive(crossings, "northern", M2)
    assert layer.current(crossings, "northern") == M2
    assert layer.current(crossings, "southern") == M0  # never spoke: what the hooks were told
    assert layer.current(crossings, "session-") == ""  # spoke, and named no model; never told: not known
    assert layer.named("  " + M1 + " ") == M1 and layer.named(7) == "" and layer.named("a b") == ""
    # After a switch, a label the session marks is signed by the model there now, though it has not spoken yet.
    page = {
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__plugin_crossings_door__mark",
        "transcript_path": str(north),
        "cwd": str(crossings.parent),
        "session_id": "northern-0001",
        "tool_input": {"sentence": "Signed by model-two."},
    }
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert said("mark", sentence="Signed by model-two.", anchors=[D]) == ("marked W4", False)
        assert said("mark", sentence="Signed by a subagent.", anchors=[D]) == ("marked W5", False)
    assert hook.run({**page, "tool_response": [{"type": "text", "text": "marked W4"}]}) is None
    assert (
        hook.run(
            {
                **page,
                "agent_id": "a1",
                "tool_input": {"sentence": "Signed by a subagent."},
                "tool_response": [{"type": "text", "text": "marked W5"}],
            }
        )
        is None
    )
    models = {label["id"]: label["model"] for label in store.listed(crossings, "work")["labels"]}
    assert (models["W4"], models["W5"]) == (M2, "")  # a subagent's is left unsigned: its model is not told (S12)


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
