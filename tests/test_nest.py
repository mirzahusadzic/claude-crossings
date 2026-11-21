"""The session's turns beside the person's sentences in a cut's frame: where the line at the door rests on a sentence
of the person's the packed part quotes and on a message of the session's turn right before or right after it in the
same session, that turn is set beneath the sentence, the turn before it first. So does a standing line carried in the
frame that is not the person's, or a stack through a line beneath it, its sentence quoted for it where nothing else
quotes it, tried once the frame is laid and kept only where it fits. There is no setting for it: a frame where no
label sets a turn is the frame it was, byte for byte. On made-up transcripts, in temporary homes. No model, no network.

Run with pytest, or without it:  python3 tests/test_nest.py
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_handles import WITH_PASTE  # noqa: E402
from test_serve import said as served  # noqa: E402
from test_store import DATA, at_terminal, started_by, switched_on  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, serve, store  # noqa: E402

DAY = "2026-11-12"  # the day of the made-up labels
SESSION = "tied-one"  # the made-up session, as the archive names it: the first eight characters of its transcript
NESTED = "     · "  # how a line of a turn set beside a sentence begins, as the frame writes it
OPENS = "and a few of the person's own words, some with the session's beside them. The time before"
TRADE = (
    "Not part of the frame: the session's turns beside the person's sentences, with any sentence quoted for them, take "
)


def said_row(uid: str, n: int, text: str, model: str = "") -> dict:
    """A row of a made-up transcript, the n-th said: the person's where its id begins with `a`, else the session's."""
    kind = "user" if uid.startswith("a") else "assistant"
    message = {"role": kind, "content": text if kind == "user" else [{"type": "text", "text": text}]}
    if model:
        message["model"] = model
    return {
        "type": kind,
        "uuid": f"{uid}-0000-4000-8000-000000000000",
        "timestamp": f"2026-11-11T{9 + n // 60:02d}:{n % 60:02d}:00.000Z",
        "message": message,
    }


def person(k: int) -> str:
    return f"Person {k}: shall the tove be gyred before the wabe is mapped, or after the borogoves are counted?"


def answer(k: int) -> str:
    return f"Session {k}: " + "the tove is gyred in the morning and the wabe is mapped by noon; " * 5


def rows_of(order: str, texts: dict | None = None, models: dict | None = None) -> list[dict]:
    """A made-up session by its voices in the order said (`a` the person's, `b` the session's): the n-th message is
    a1 or b1 and n on six digits, with the words `texts` gives it, else the made-up ones, and the model `models`
    gives a message of the session's."""
    texts, models = texts or {}, models or {}
    rows = []
    for n, v in enumerate(order, 1):
        uid = f"{v}1{n:06d}"
        rows.append(said_row(uid, n, texts.get(uid, person(n) if v == "a" else answer(n)), models.get(uid, "")))
    return rows


# The made-up session: the person's eight messages (ids beginning a1) and the session's eleven (b1), in turns
# 1 | 2 | 3 | 4 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 | 17 18 19.
ORDER = "ababbababababababbb"
ROWS = rows_of(ORDER)
# The line at the door: on five of the person's sentences and on a message of the session's turn on each side.
DOOR = "Find out whether the tove is gyred before the wabe is mapped."
TWO_ENDED = [
    "b1000002", "a1000003", "b1000004", "a1000006", "b1000007", "a1000008", "b1000009",
    "b1000011", "a1000012", "b1000013", "b1000015", "a1000016", "b1000017",
]  # fmt: skip
ONE_ENDED = ["a1000003", "a1000006", "a1000008", "a1000012", "a1000016"]  # the person's sentences alone
# The frames 12af10f makes of these homes, for the session that was cut: by length and digest. Each is as 12af10f made
# it with the person's rows printed `(theirs)`, the fixtures' own rows saying `Day n` for `On day n`, so that every
# row is as long as it was.
BEFORE = {
    ("small", 9000): (3179, "4b2a2bb8c079d106823ac7c3c43c3265dae5e0b20291c646439e77f7bb68cd1b"),
    ("full", 9000): (8919, "1807cfac5343af9840244e11e7d634c3c5b4ed129174aeb344d6a8eecff9d976"),
    ("full", 9500): (9401, "69a569e2313b5de6a1b2d5ea9da634d63455bf9dc425dead583267ac53d5f525"),
    ("one", 9000): (8950, "539e65fb84a611ee245450227a3b6b8c8609cc0284964384ede2f907f60d2b2b"),
    ("one", 9500): (9440, "7545e6e65c4b654d5a6c741e07db80d7ed87e984a3134494136e566e68108177"),
    ("small one", 9000): (3099, "981978e40ec8764803a2398b9e587b87a0a309573170247e17da8210a5e56669"),
}


def filled(crossings: Path) -> None:
    """Forty-five standing lines and a hundred and twenty labels about the work, on a page of an earlier day: more
    than a frame has room for."""
    (crossings / "labels").mkdir(exist_ok=True)
    (crossings / "labels" / "2026-11-10.md").write_text(
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
        + "".join(
            f"| R{n} | Day {n} the borogoves were counted again and the count was written down in the book. "
            "| his | `a1000001` |\n"
            for n in range(1, 46)
        )
        + "".join(
            f"| W{n} | The wabe was mapped again on day {n} and nothing new was found worth a longer sentence. "
            "| both | `a1000014` |\n"
            for n in range(1, 121)
        ),
        encoding="utf-8",
    )
    store.build(crossings)


def made(
    folder: Path,
    rows: list = ROWS,
    anchors: list = TWO_ENDED,
    full: bool = False,
    door_text: str = DOOR,
    other: list | None = None,
) -> Path:
    """A home of the made-up session, archived and built, and of `other`'s rows as a second session where given; a
    standing line on both ends of the person's fifth sentence (a1000010), where the session holds it, and the line
    at the door on `anchors`; with `full`, more labels than a frame has room for."""
    project = folder / "project"
    crossings = project / "crossings"
    crossings.mkdir(parents=True)
    switched_on(project)
    for name, held in ((SESSION, rows), ("tied-two", other or [])):
        if held:
            path = folder / f"{name}-0001.jsonl"
            path.write_text("".join(json.dumps(each) + "\n" for each in held), encoding="utf-8")
            store.archive(path, crossings)
    store.build(crossings)
    if full:
        filled(crossings)
    if any(each["uuid"].startswith("a1000010") for each in rows):
        standing = "The person counts the borogoves before anything is mapped."
        on_both = ["b1000009", "a1000010", "b1000011"]
        assert store.mark(crossings, "relation", "his", standing, on_both, day=DAY)["written"]
    assert store.mark(crossings, "next", "session", door_text, anchors, day=DAY)["written"]
    return crossings


def digest(text: str) -> tuple[int, str]:
    return len(text), hashlib.sha256(text.encode("utf-8")).hexdigest()


def framed(crossings: Path, size: int = 9000, model: str = "", turns: bool = True) -> str:
    """The cut's frame for the made-up session; without `turns`, the one made with no turn beside any sentence,
    through the frame's inner argument, which is no setting."""
    if turns:
        return frame.compose(crossings, size, model=model, session=SESSION)
    return frame._made(crossings, size, False, model, SESSION, nest=False)


def nested(made_: str) -> list[str]:
    """The lines of a frame that set a turn of the session's beside a sentence."""
    return [line for line in made_.split("\n") if line.startswith(NESTED)]


def packed(made_: str) -> list[str]:
    """The lines of a frame's packed part."""
    return made_.split(frame.PACKED_HEAD + "\n\n", 1)[1].split("\n\n", 1)[0].split("\n")


def words_of(text: str, most: int = 300) -> str:
    """A message's words as a frame shows them, cut at `most` characters."""
    return text if len(text) <= most else text[:most].rstrip() + " […]"


def door_line(made_: str) -> str:
    return next(line for line in made_.split("\n") if line.startswith("- N"))


def quotes_and_work(made_: str) -> tuple[set, set]:
    """The person's sentences a frame quotes, by id, and the labels about the work it writes out, by key."""
    quotes = {line.split("`")[1] for line in made_.split("\n") if line.startswith("- `")}
    work = {line.split(" (")[0].split()[-1] for line in made_.split("\n") if line.startswith(("- W", "     ↳ W"))}
    return quotes, work


# --- a line at the door on no turn of the session's: the frame it was -----------------------------------------------


def test_a_line_at_the_door_that_rests_on_no_turn_of_the_sessions_gives_the_frame_of_before(tmp_path):
    """Pin: a home whose line at the door rests on the person's sentences alone sets no turn beside them, and its
    frame is the one 12af10f made, by length and digest, though a standing line rests on both ends of a sentence."""
    one, small = made(tmp_path / "one", anchors=ONE_ENDED, full=True), made(tmp_path / "small", anchors=ONE_ENDED)
    for (name, size), pinned in BEFORE.items():
        if name in ("one", "small one"):
            assert digest(framed(one if name == "one" else small, size)) == pinned, (name, size)


def test_the_frame_made_without_turns_is_the_frame_of_before_by_length_and_digest(tmp_path):
    """Where the line at the door rests on both ends, the frame sets the turns; made without them, through the inner
    argument that `trade` measures against, it is the frame 12af10f made of the same home."""
    small, full = made(tmp_path / "small"), made(tmp_path / "full", full=True)
    homes = {"small": small, "full": full}
    for (name, size), pinned in BEFORE.items():
        if name in homes:
            assert nested(framed(homes[name], size)), (name, size)
            assert digest(framed(homes[name], size, turns=False)) == pinned, (name, size)


def test_no_setting_names_the_turns_neither_the_stores_nor_the_modules_lists(tmp_path):
    """Pin: there is no setting for the session's turns: the setting files the store names, and the module's lists
    of the files a session may not write and may read, are as they were."""
    assert store.SETTINGS == ("mode", "carry", "frame-size", "copy")
    source = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    for name in ("WRITTEN_BY_DOOR", "READABLE"):
        held = source.split(f"const {name} =", 1)[1].split("\n\n", 1)[0].split("\n// ", 1)[0]
        assert "frame-size" in held and "nest" not in held, name


def test_no_tool_of_the_servers_and_no_word_of_switch_changes_whether_turns_are_set(tmp_path):
    """Pin: the turns a frame sets are the same before and after every tool of the server's but `leave` (which
    writes a new line at the door), whatever it is given, and after the person's switch is turned off and on again
    or given a word it does not take; and no file is written for them."""
    crossings = made(tmp_path, anchors=["a1000003", "b1000004"])
    project = str(crossings.parent)
    before = nested(framed(crossings))
    calls = [
        ("look", {}), ("status", {}), ("labels", {"ids": ["nest"]}), ("find", {"words": "nest on"}),
        ("thread", {"id": "a1000003", "role": "pair:them"}), ("crossing", {}), ("crossing", {"nest": "off"}),
        ("mark", {"sentence": "The tove is not nested.", "anchors": ["a1000006"], "kind": "nest"}),
    ]  # fmt: skip
    with set_to(CLAUDE_PROJECT_DIR=project):
        for name, given in calls:
            served(name, **given)
            assert nested(framed(crossings)) == before, name
    code, said_ = through("switch", "nest", "--cwd", project)
    assert code == 2 and said_ == "switch takes one word: on, off, toggle, adopt, join or here.\n"
    for word in ("off", "on"):
        assert through("switch", word, "--cwd", project)[0] == 0, word
        assert nested(framed(crossings)) == before, word
    assert not (crossings / "nest").exists()


def test_the_count_of_labels_carried_takes_no_nested_line_for_a_label(tmp_path):
    """Pin: `frame.carried`, which the line shown to the person counts by, counts no line of a turn set beside a
    sentence, in any of its forms, and counts a nested frame as the same frame without those lines."""
    lines = [
        "     · after it, the session (N1): `b1000004` Session 4: the tove is gyred […] `b1000005`",
        "     · before it, the session (N1), as above: `b1000004` `b1000005`",
        "     · after it, the session (N1): 28 messages, `b1000004` to `b1000031`",
        "     · after it, the session (N1): `b1000004` (made-up-model-a) - W1 (session): a sentence",
    ]
    assert frame.carried("\n".join(lines)) == 0
    crossings = made(tmp_path, full=True)
    on = framed(crossings)
    assert frame.carried(on) == frame.carried("\n".join(line for line in on.split("\n") if line not in nested(on)))


def test_the_tools_a_session_is_shown_are_as_they_were_and_name_nothing_of_the_turns(tmp_path):
    """Pin: the listing keeps its size, and no tool takes or names a setting of the turns."""
    listed = json.dumps(serve.TOOLS)
    assert len(listed) == 5661 and "nest" not in listed and serve.NAMES == [
        "look", "labels", "find", "thread", "mark", "leave", "status", "crossing",
    ]  # fmt: skip


# --- which turns are set, and where -----------------------------------------------------------------------------


def test_the_turn_after_is_set_beneath_the_sentence_each_message_by_id_in_order(tmp_path):
    crossings = made(tmp_path, anchors=["a1000003", "b1000004"])
    on = framed(crossings)
    assert packed(on) == [
        "- `a1000003`: " + person(3),
        "     · after it, the session (N1): `b1000004` " + words_of(answer(4).strip()) + " `b1000005`",
        "     ↳ N1: the line at the door",
    ]
    # the opening says so, in this frame alone, and nothing else of the frame changes
    off = framed(crossings, turns=False)
    assert OPENS in on and OPENS not in off and frame.BESIDE not in off
    assert on.replace(frame.BESIDE, "", 1).replace(nested(on)[0] + "\n", "") == off


def test_the_turn_before_is_set_beneath_its_own_sentence(tmp_path):
    crossings = made(tmp_path, anchors=["b1000002", "a1000003"])
    assert packed(framed(crossings)) == [
        "- `a1000003`: " + person(3),
        "     · before it, the session (N1): `b1000002` " + words_of(answer(2).strip()),
        "     ↳ N1: the line at the door",
    ]


def test_both_ends_where_the_line_rests_on_both_and_on_any_message_of_a_turn(tmp_path):
    """The line rests on the second message of the turn after (b1000005): the whole turn is set, in its order. Both
    turns stand beneath the sentence, the turn before it first, then the turn after it, then what was told."""
    crossings = made(tmp_path, anchors=["b1000002", "a1000003", "b1000005"])
    assert packed(framed(crossings)) == [
        "- `a1000003`: " + person(3),
        "     · before it, the session (N1): `b1000002` " + words_of(answer(2).strip()),
        "     · after it, the session (N1): `b1000004` " + words_of(answer(4).strip()) + " `b1000005`",
        "     ↳ N1: the line at the door",
    ]


def test_in_a_frame_of_two_sentences_no_line_of_a_turn_stands_between_one_sentences_block_and_the_next_sentence(
    tmp_path,
):
    """Every line indented in the packed part reads as the sentence's above it: so the turn before the second
    sentence (b1000007, before a1000008) stands beneath a1000008, and nothing of a turn stands between the last line
    of a1000003's block and a1000008's own line, nor above the first sentence."""
    crossings = made(tmp_path, anchors=["b1000002", "a1000003", "a1000008", "b1000007"])
    lines = packed(framed(crossings))
    assert lines == [
        "- `a1000003`: " + person(3),
        "     · before it, the session (N1): `b1000002` " + words_of(answer(2).strip()),
        "     ↳ N1: the line at the door",
        "- `a1000008`: " + person(8),
        "     · before it, the session (N1): `b1000007` " + words_of(answer(7).strip()),
        "     ↳ N1: the line at the door",
    ]
    sentences = [at for at, line in enumerate(lines) if line.startswith("- `")]
    assert sentences[0] == 0 and all(not lines[at - 1].startswith(NESTED) for at in sentences[1:])


def test_a_sentence_that_opens_its_session_or_that_the_session_never_answered_has_no_turn_on_that_side(tmp_path):
    """The person's first message (a1000001) has no turn of the session's before it, and their last (a1000005), said
    as the session ends, none after it: the line at the door on each and on the turn on its other side sets that
    turn alone."""
    crossings = made(tmp_path, rows=rows_of("abbba"), anchors=["a1000001", "b1000002", "a1000005", "b1000004"])
    assert packed(framed(crossings)) == [
        "- `a1000001`: " + person(1),
        "     · after it, the session (N1): `b1000002` " + words_of(answer(2).strip()) + " `b1000003` `b1000004`",
        "     ↳ N1: the line at the door",
        "- `a1000005`: " + person(5),
        "     · before it, the session (N1), as above: `b1000002` `b1000003` `b1000004`",
        "     ↳ N1: the line at the door",
    ]


def test_a_work_label_the_persons_standing_line_a_turn_two_away_and_another_session_set_no_turn(tmp_path):
    """Beside the one the line at the door sets (after a1000003): a work label on a1000006 and the turn after it; the
    fixture's standing line of the person's on both ends of a1000010, which the line at the door rests on alone; the
    line at the door on a1000016 and on b1000013, two turns before it; and on a1000008 and on another session's
    message said with it. None of them sets a turn."""
    other = [said_row("a2000001", 7, "A question asked in another session."), said_row("c2000002", 8, answer(99))]
    anchors = ["a1000003", "b1000004", "a1000010", "a1000016", "b1000013", "a1000008", "c2000002"]
    crossings = made(tmp_path, anchors=anchors, other=other)
    assert store.mark(crossings, "work", "session", "The tove is gyred.", ["a1000006", "b1000007"], day=DAY)["written"]
    on = framed(crossings)
    assert nested(on) == [
        "     · after it, the session (N1): `b1000004` " + words_of(answer(4).strip()) + " `b1000005`"
    ]
    for quoted in ("a1000006", "a1000008", "a1000010", "a1000016"):  # each is quoted, and nothing is beside it
        at = packed(on).index(f"- `{quoted}`: " + person(int(quoted[2:])))
        assert not packed(on)[at - 1].startswith(NESTED) and not packed(on)[at + 1].startswith(NESTED), quoted


def test_a_frame_sets_the_homes_pairs_whichever_session_said_them_and_none_for_a_session_the_home_does_not_hold(
    tmp_path,
):
    """Guard, twice over. A frame for a session the home holds no message of, through compose and through the person's
    `frame --session`, set the turns of the line at the door all the same: it is now the frame made with no turn
    beside any sentence. And the pairs are the home's, as its labels and its line at the door are: a line left in one
    session may rest on a pair said in an earlier one, and the frame for either session sets both turns. Held to the
    frame's own session, the turn of the earlier pair was dropped: the frame for `tied-one` set `b1000004` alone."""
    other = [said_row("a2000001", 7, "A question asked in another session."), said_row("c2000002", 8, answer(99))]
    crossings = made(tmp_path, anchors=["a1000003", "b1000004", "a2000001", "c2000002"], other=other)
    both = [
        "     · after it, the session (N1): `b1000004` " + words_of(answer(4).strip()) + " `b1000005`",
        "     · after it, the session (N1): `c2000002` " + words_of(answer(99).strip()),
    ]
    for session in (SESSION, "tied-two"):
        assert nested(frame.compose(crossings, session=session)) == both, session
    for session in ("bogus", "tied-thr"):
        on = frame.compose(crossings, session=session)
        assert not nested(on) and on == frame._made(crossings, None, False, "", session, nest=False), session
    code, said_ = through("frame", "--cwd", str(crossings.parent), "--session", "bogus")
    assert code == 0 and said_ == frame.compose(crossings, session="bogus") and TRADE not in said_


# --- how a turn reads -----------------------------------------------------------------------------------------------


def test_the_messages_of_a_turn_share_one_cut_in_their_order_and_the_ids_after_it_stand_alone(tmp_path):
    texts = {"b1000004": "Four " * 30, "b1000005": "Five " * 40, "b1000006": "Six " * 25}
    crossings = made(tmp_path, rows=rows_of("ababbbab", texts), anchors=["a1000003", "b1000004"])
    four, five = ("Four " * 30).strip(), ("Five " * 40).strip()
    assert nested(framed(crossings)) == [
        f"     · after it, the session (N1): `b1000004` {four} `b1000005` {words_of(five, 300 - len(four))} `b1000006`"
    ]
    # where the words end at the cut with a message, the next is marked as cut and the rest stand alone
    texts = {"b1000004": "x" * 300, "b1000005": "Five.", "b1000006": "Six."}
    again = made(tmp_path / "again", rows=rows_of("ababbbab", texts), anchors=["a1000003", "b1000004"])
    assert nested(framed(again)) == [
        f"     · after it, the session (N1): `b1000004` {'x' * 300} `b1000005` […] `b1000006`"
    ]


def test_a_messages_words_are_cleaned_and_on_one_line_a_line_break_read_as_a_space(tmp_path):
    texts = {"b1000004": "First line.\nSecond\tline,‮ turned‏.\n\n| a | table |", "b1000005": "Five."}
    crossings = made(tmp_path, rows=rows_of(ORDER, texts), anchors=["a1000003", "b1000004"])
    assert nested(framed(crossings)) == [
        "     · after it, the session (N1): `b1000004` First line. Second line, turned. | a | table | `b1000005` Five."
    ]


def test_a_turn_of_more_messages_than_its_ids_fit_in_the_cut_is_bound_to_its_count_and_its_first_and_last(tmp_path):
    """Twenty-seven ids fit in the cut of 300 (27 * 11 - 1 = 296), and the line names each; twenty-eight do not,
    and the line gives the count and the first and last id, and no words."""
    for count in (27, 28):
        crossings = made(
            tmp_path / str(count), rows=rows_of("aba" + "b" * count + "ab"), anchors=["a1000003", "b1000004"]
        )
        line = nested(framed(crossings))
        ids = [f"b1{n:06d}" for n in range(4, 4 + count)]
        if count == 27:
            assert line == [
                "     · after it, the session (N1): `b1000004` "
                + words_of(answer(4).strip())
                + " "
                + " ".join(f"`{each}`" for each in ids[1:])
            ]
        else:
            assert line == [f"     · after it, the session (N1): 28 messages, `{ids[0]}` to `{ids[-1]}`"]


def test_a_turn_already_set_above_is_named_the_second_time_by_its_ids_alone(tmp_path):
    crossings = made(tmp_path, anchors=["a1000003", "b1000004", "a1000006"])
    assert packed(framed(crossings)) == [
        "- `a1000003`: " + person(3),
        "     · after it, the session (N1): `b1000004` " + words_of(answer(4).strip()) + " `b1000005`",
        "     ↳ N1: the line at the door",
        "- `a1000006`: " + person(6),
        "     · before it, the session (N1), as above: `b1000004` `b1000005`",
        "     ↳ N1: the line at the door",
    ]


def test_a_long_turn_set_again_is_named_by_its_ids_alone_or_from_28_ids_on_by_its_count_as_above(tmp_path):
    """Pin: a turn set already, higher in the packed part, is named again by its ids alone where they fit in the cut,
    as twenty-seven do; from twenty-eight ids on it is named by its count with its first and last id, the second time
    too, each time "as above"."""
    for count in (27, 28, 30):
        rows = rows_of("a" + "b" * count + "ab")  # the person's, the session's long turn, the person's again
        crossings = made(tmp_path / str(count), rows=rows, anchors=["a1000001", "b1000002", f"a1{count + 2:06d}"])
        ids = [f"b1{n:06d}" for n in range(2, 2 + count)]
        long = count >= 28
        first = f"{count} messages, `{ids[0]}` to `{ids[-1]}`" if long else " ".join(f"`{each}`" for each in ids)
        set_ = f"`{ids[0]}` " + words_of(answer(2).strip()) + " " + " ".join(f"`{each}`" for each in ids[1:])
        assert packed(framed(crossings)) == [
            "- `a1000001`: " + person(1),
            "     · after it, the session (N1): " + (first if long else set_),
            "     ↳ N1: the line at the door",
            f"- `a1{count + 2:06d}`: " + person(count + 2),
            f"     · before it, the session (N1), as above: {first}",
            "     ↳ N1: the line at the door",
        ], count


def test_a_message_that_looks_like_a_key_or_that_a_refusal_or_a_silencing_rests_on_stands_by_its_id_alone(tmp_path):
    texts = {"b1000004": "The key is password: made-up-tove-1234 for now.", "b1000005": "Then the wabe."}
    anchors = ["a1000003", "b1000004", "a1000006", "b1000007", "a1000008", "b1000009"]
    crossings = made(tmp_path, rows=rows_of(ORDER, texts), anchors=anchors)
    refused = store.mark(
        crossings, "refused", "session", "The tove is not gyred: the wabe is first.", ["b1000007"], day=DAY
    )
    assert refused["written"]
    lines = nested(framed(crossings))
    assert lines == [
        "     · after it, the session (N1): `b1000004` `b1000005` Then the wabe.",
        "     · before it, the session (N1), as above: `b1000004` `b1000005`",
        "     · after it, the session (N1): `b1000007`",
        "     · before it, the session (N1), as above: `b1000007`",
        "     · after it, the session (N1): `b1000009` " + words_of(answer(9).strip()),
    ]
    assert "made-up-tove-1234" not in framed(crossings)
    # put to rest, the refusal crosses no more, and nor do the words of the message its silencing rests on
    why = "The wabe is mapped now."
    silenced = store.mark(crossings, "silenced", "session", why, [refused["id"], "b1000009"], day=DAY)
    assert silenced["written"]
    assert nested(framed(crossings))[-1] == "     · after it, the session (N1): `b1000009`"
    assert "Session 7:" not in framed(crossings) and "Session 9:" not in framed(crossings)


def test_a_message_of_another_model_is_named_with_its_model_and_a_struck_one_is_gone(tmp_path):
    texts = {"b1000004": "Four, short.", "b1000005": "Five, short."}
    models = {"b1000004": "made-up-model-a", "b1000005": "made-up-model-b"}
    crossings = made(tmp_path, rows=rows_of(ORDER, texts, models), anchors=["a1000003", "b1000004"])
    beneath = "     · after it, the session (N1): "
    assert nested(framed(crossings, model="made-up-model-b")) == [
        beneath + "`b1000004` (made-up-model-a) Four, short. `b1000005` Five, short."
    ]
    assert nested(framed(crossings)) == [beneath + "`b1000004` Four, short. `b1000005` Five, short."]  # no model known
    assert store.strike(crossings, "b1000005")["struck"]
    assert nested(framed(crossings)) == [beneath + "`b1000004` Four, short."]
    assert "b1000005" not in framed(crossings) and "Five, short" not in framed(crossings)


# --- the allowance and the ceiling ----------------------------------------------------------------------------------


def test_the_line_at_the_door_and_its_turns_never_pass_its_cap_and_a_turn_that_does_not_fit_goes_whole_last_first(
    tmp_path,
):
    anchors = ["b1000002", "a1000003", "b1000004"]
    crossings = made(tmp_path / "short", anchors=anchors)
    before, after = nested(framed(crossings))
    brackets = len("- N1 (session): ") + len(" [b1000002, a1000003, b1000004]")
    # a line at the door that leaves its turns room for the turn before and half the turn after
    room = store.LONGEST - len(frame.BESIDE) - (len(before) + 1) - (len(after) + 1) // 2
    long = ("The tove is to be gyred before the wabe is mapped and the borogoves are counted. " * 60)[: room - brackets]
    held = made(tmp_path / "long", anchors=anchors, door_text=long.strip())
    on = framed(held)
    assert nested(on) == [before]  # the turn after does not fit: it goes whole, and no part of it is left
    assert len(door_line(on)) + sum(len(line) + 1 for line in nested(on)) + len(frame.BESIDE) <= store.LONGEST
    # a line that leaves room for neither sets neither, and the frame is the one made without turns
    longer = ("The tove is to be gyred before the wabe is mapped and the borogoves are counted. " * 60)[
        : store.LONGEST - len(frame.BESIDE) - len(before) - brackets + 5
    ]
    none = made(tmp_path / "longer", anchors=anchors, door_text=longer.strip())
    off = framed(none, turns=False)
    assert framed(none) == off and nested(off) == []


def test_no_sentence_of_the_persons_and_no_work_label_is_lost_that_a_line_at_the_door_as_long_would_keep(tmp_path):
    """At the ceiling, the line at the door and its turns take what a line at the door as long as they are together
    would take, and no more: the person's sentences and the work rows that frame quotes and writes out are all in
    this one."""
    crossings = made(tmp_path / "turns", full=True)
    for size in (9000, 9500):
        on = framed(crossings, size)
        took = sum(len(line) + 1 for line in nested(on)) + len(", some with the session's beside them")
        assert nested(on) and OPENS in on
        as_long = made(tmp_path / f"long-{size}", full=True, door_text=DOOR + " " + "x" * (took - 1))
        assert len(door_line(framed(as_long, size))) == len(door_line(on)) + took
        kept_quotes, kept_work = quotes_and_work(framed(as_long, size))
        quotes, work = quotes_and_work(on)
        assert kept_quotes <= quotes and kept_work <= work, size


def test_at_the_ceiling_a_row_the_top_up_added_goes_before_a_turn_the_line_at_the_door_reserved(tmp_path):
    """A turn within the line at the door's allowance is not given up for a work row that only fills the room the
    turn had reserved: at the usual size every turn the line sets is in the frame, and the frame writes out no work
    row that the one made without turns does not."""
    crossings = made(tmp_path, full=True)
    _, work_off = quotes_and_work(framed(crossings, turns=False))
    on = framed(crossings)
    _, work = quotes_and_work(on)
    assert len(nested(on)) == 10  # both ends of each of the five sentences the line at the door rests on
    assert work <= work_off
    assert len(on) <= frame.SIZE


def test_the_frame_stays_within_its_ceiling_at_the_least_the_usual_and_the_most(tmp_path):
    crossings = made(tmp_path, full=True)
    for size in (frame.LEAST, frame.SIZE, frame.MOST):
        on = framed(crossings, size)
        assert len(on) <= size, size
        assert bool(nested(on)) == (size != frame.LEAST), size  # at the least there is no room: as without turns
    assert framed(crossings, frame.LEAST) == framed(crossings, frame.LEAST, turns=False)


# --- the trade, told after the frame --------------------------------------------------------------------------------


def test_the_trade_is_told_after_the_frame_by_crossing_and_frame_and_never_in_a_carried_frame(tmp_path):
    crossings, one = made(tmp_path / "both", full=True), made(tmp_path / "one", anchors=ONE_ENDED, full=True)

    def told(home: Path) -> dict[str, str]:
        project, path = str(home.parent), str(home.parent.parent / f"{SESSION}-0001.jsonl")
        out = io.StringIO()
        with started_by("cli"), at_terminal(False), set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):
            with contextlib.redirect_stdout(out):  # as the hooks module asks for a cut's frame
                door.main(["frame", "--cwd", project, "--transcript", path, "--by-module"])
            carried = out.getvalue()
            out = io.StringIO()
            with contextlib.redirect_stdout(out):  # as the person's command asks for it
                door.main(["frame", "--cwd", project, "--transcript", path, "--by-module", "--trade"])
            command = out.getvalue()
        with set_to(CLAUDE_PROJECT_DIR=project):
            crossing = served("crossing")[0]
        terminal = through("frame", "--cwd", project, "--transcript", path)[1]  # the person's own shell
        return {"carried": carried, "command": command, "terminal": terminal, "crossing": crossing}

    for how, text in told(one).items():  # nothing is set beside a sentence: no sentence after the frame
        assert text == framed(one) and TRADE not in text, how
    made_ = framed(crossings)
    trade = frame.trade(crossings, made_, session=SESSION)
    assert nested(made_) and trade.startswith(TRADE)
    account: dict = {}
    off: dict = {}
    frame._made(crossings, None, False, "", SESSION, account=account)
    frame._made(crossings, None, False, "", SESSION, nest=False, account=off)
    gone = [key for kind in ("standing", "work") for key in off[kind] if key not in account[kind]]
    unquoted = [f"`{each}`" for each in off["said"] if each not in account["said"]]
    assert gone and trade == (
        f"{TRADE}{account['nested']:,} characters of it; the labels it would carry without them: {store.some(gone)}; "
        f"the person's sentences it would quote without them: {store.some(unquoted) or 'none'}."
    )
    for how, text in told(crossings).items():
        assert text == (made_ if how == "carried" else f"{made_}\n{trade}\n"), how
    assert TRADE not in made_
    # where nothing is set, nothing is said after the frame
    assert frame.trade(one, framed(one), session=SESSION) == ""


def test_the_trade_of_a_frame_the_home_no_longer_gives_is_nothing_and_no_count_that_contradicts_it(tmp_path):
    """Guard: handed a frame that sets two turns, after both messages of them were struck, `trade` counted the frame
    the home gives now and said its turns "take 0 characters" under a frame that plainly holds two. Where the frame
    made again is not the one handed, it says nothing; of the frame the home gives now it says what it said before."""
    crossings = made(tmp_path, anchors=["b1000002", "a1000003", "b1000004"])
    before = framed(crossings)
    assert len(nested(before)) == 2 and frame.trade(crossings, before, session=SESSION).startswith(TRADE)
    assert store.strike(crossings, "b1000002")["struck"] and store.strike(crossings, "b1000004")["struck"]
    assert frame.trade(crossings, before, session=SESSION) == ""
    now = framed(crossings)
    assert now != before and frame.trade(crossings, now, session=SESSION) == ""  # it sets no turn now: nothing
    assert store.mark(crossings, "next", "session", DOOR, ["b1000005", "a1000006"], day=DAY)["written"]
    again = framed(crossings)
    assert nested(again) and frame.trade(crossings, again, session=SESSION).startswith(TRADE)


def test_a_home_that_changes_between_the_two_readings_is_given_its_frame_and_no_sentence_after_it(tmp_path):
    """Guard: `with_trade` made the frame and then, for the sentence after it, the frame with no turn; `trade` made
    the frame again and then that one: two readings of the home each, and nothing said they read one home. A line
    marked between them was named after the frame, "the labels it would carry without them: R2.", though the frame
    the sentence spoke of was made before R2 was there. Each takes a stamp of the home before its first reading and
    after its second now, and where the home changed it gives the frame and no sentence; where it did not, the
    sentence is told as before."""
    real, calls = frame._made, []

    def marking(*args, **kwargs):
        out = real(*args, **kwargs)
        calls.append(args[0])
        if len(calls) == 1:  # between the first reading and the second, a mark lands in the home
            line = "A line that came while the frame was made."
            assert store.mark(args[0], "relation", "session", line, ["a1000010", "b1000011"], day=DAY)["written"]
        return out

    for how in ("with_trade", "trade"):
        crossings = made(tmp_path / how)
        before = framed(crossings)
        calls.clear()
        frame._made = marking
        try:
            given = (
                frame.with_trade(crossings, session=SESSION)
                if how == "with_trade"
                else (before, frame.trade(crossings, before, session=SESSION))
            )
        finally:
            frame._made = real
        assert len(calls) == 2 and given == (before, ""), (how, given[1])
        now = framed(crossings)  # the home as it stands now, R2 in it: the sentence is told of its frame
        assert "- R2 (session): " in now and frame.with_trade(crossings, session=SESSION)[1].startswith(TRADE), how
        assert frame.trade(crossings, now, session=SESSION) == frame.with_trade(crossings, session=SESSION)[1], how


def test_the_frame_with_the_sentence_after_it_reads_the_turns_once_through_the_door_and_the_server(tmp_path):
    """Guard: the door's `frame`, where it tells the sentence after the frame (with --trade, at a terminal and for the
    server's `crossing`), made the frame and then made it again with its turns for the sentence, and read every turn
    of the session's twice. It reads them as often as the frame alone does now, and what it gives is as before: the
    frame, and after it the sentence `trade` tells of it."""
    crossings = made(tmp_path, full=True)
    project, path = str(crossings.parent), str(crossings.parent.parent / f"{SESSION}-0001.jsonl")
    real, reads = store.tied, []

    def tied(*args, **kwargs):
        reads.append(args[1])
        return real(*args, **kwargs)

    def counted(action) -> tuple[str, int]:
        reads.clear()
        store.tied = tied
        try:
            return action(), len(reads)
        finally:
            store.tied = real

    alone, once = counted(lambda: framed(crossings))
    trade = frame.trade(crossings, alone, session=SESSION)
    assert nested(alone) and once and trade.startswith(TRADE)

    def through_the_command() -> str:
        out = io.StringIO()
        with started_by("cli"), at_terminal(False), set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):
            with contextlib.redirect_stdout(out):  # as the person's command asks for it
                door.main(["frame", "--cwd", project, "--transcript", path, "--by-module", "--trade"])
        return out.getvalue()

    def through_the_server() -> str:
        with set_to(CLAUDE_PROJECT_DIR=project):
            return served("crossing")[0]

    for how in (
        through_the_command,
        through_the_server,
        lambda: through("frame", "--cwd", project, "--transcript", path)[1],
    ):
        given, read = counted(how)
        assert given == f"{alone}\n{trade}\n" and read == once, (how, read, once)
    assert counted(lambda: frame.trade(crossings, alone, session=SESSION)) == (trade, once)  # made again once, to see


# --- the turns a standing line sets ---------------------------------------------------------------------------------

ON_THREE = ("next", "session", DOOR, ["a1000003"])  # a line at the door on a sentence alone: it sets no turn itself
COUNTING = "The person counts the borogoves before anything is mapped."
SHORT = {"b1000011": "Counted first, then mapped."}  # a short answer to a1000010
HEAD = "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
# A full page: a standing line of the session's on a1000010 and its answer, the oldest, then forty-four of the person's
# and a hundred and twenty labels about the work, more than a frame has room for.
FULL = (
    f"| R1 | {COUNTING} | session | `a1000010`, `b1000011` |\n"
    + "".join(
        f"| R{n} | Day {n} the borogoves were counted again and the count was written down in the book. | his | "
        "`a1000001` |\n"
        for n in range(2, 46)
    )
    + "".join(
        f"| W{n} | The wabe was mapped again on day {n} and nothing new was found worth a longer sentence. | both | "
        "`a1000014` |\n"
        for n in range(1, 121)
    )
)
# The frames 9719e2f makes of the homes below, for the session that was cut, where no standing line sets a turn: as it
# made them with the person's rows printed `(theirs)` and the fixtures' own rows saying `Day n` (see BEFORE).
NOTHING = {
    "his": (2521, "3a1c7bad9d16a5f44ad67a4aa48a7bd3dd232aaca7b84cee5a09b5143922e6b9"),
    "his beneath": (2443, "65c868ea6e4df231b610816651cc37cee8cf89a854e5ae579da93d1db3bdafc8"),
    "his stack": (2442, "7e69dfa7244f8b9d7fe8151c72b45d271cb6f223274fee055d210c750388a86e"),
    "together": (2455, "92405d905cf4f61b791544f48f28a862b55320b447d589f15a47c7ae3d2a1383"),
    "unresolved": (2520, "21b3e1c1f268057885516310379161bc020d8262727a8d774ee85d32cf666056"),
    "flagged": (2522, "2e9c03f258a951ff89791d55317a73f2f6548918806c01ff154049648edf61d5"),
    "not carried": (8956, "d7a367db615a4b2701b88c74222bb3ed114972ca5f8bf7bc504bbc605efca242"),
    "least": (2259, "5a64607d71ed3e4ff040a07785fde59409cad6409b4838c62e7495bad66b5fe3"),
    "new": (2598, "6610f8cad2f4add85088fa8591e8d6fd2de3e1d3efac0ea7a997a0dff3c87f4c"),
    "none": (2347, "7d756a1067c7294f842ea189f2707fc00151be4451a23de9ca8017146a2a0371"),
    "long": (9083, "892793804f9821431317313999d99b19e52ec2c2225c7aa1b58f04a3623a8df9"),
}


def held(folder: Path, marks: list, rows: list = ROWS, page: str = "", door: tuple | None = ON_THREE) -> Path:
    """A home of the made-up session (`rows`), archived and built; the rows of `page` on an earlier day where given;
    then each of `marks` (a kind, whose it is, a sentence and what it rests on) and the line at the door (`door`, where
    given), marked in turn."""
    project = folder / "project"
    crossings = project / "crossings"
    crossings.mkdir(parents=True)
    switched_on(project)
    path = folder / f"{SESSION}-0001.jsonl"
    path.write_text("".join(json.dumps(each) + "\n" for each in rows), encoding="utf-8")
    store.archive(path, crossings)
    store.build(crossings)
    if page:
        (crossings / "labels").mkdir(exist_ok=True)
        (crossings / "labels" / "2026-11-10.md").write_text(HEAD + page, encoding="utf-8")
        store.build(crossings)
    for kind, whose, sentence, anchors in [*marks, *([door] if door else [])]:
        assert store.mark(crossings, kind, whose, sentence, anchors, day=DAY)["written"], sentence
    return crossings


def turn(side: str, key: str, n: int, *more: int) -> str:
    """The line of a turn of the session's set beside a sentence, keyed by `key`: message n with its made-up words,
    and the ids of `more` after it."""
    ids = "".join(f" `b1{each:06d}`" for each in more)
    return f"     · {side} it, the session ({key}): `b1{n:06d}` " + words_of(answer(n).strip()) + ids


def standing_lines(made_: str) -> list[str]:
    return [line for line in made_.split("\n") if line.startswith("- R")]


def test_a_carried_standing_line_on_both_ends_sets_its_turns_beneath_the_sentence_it_quotes_for_them(tmp_path):
    """The session's standing line on a1000010 and on the session's turn on each side of it: the sentence, which no
    other label quotes, is quoted for it, with both turns beneath, keyed by the line. The line itself is carried in its
    own part as before, and the opening says the session's words stand beside the person's."""
    crossings = held(tmp_path, [("relation", "session", COUNTING, ["b1000009", "a1000010", "b1000011"])])
    on = framed(crossings)
    assert packed(on) == [
        "- `a1000003`: " + person(3),
        "     ↳ N1: the line at the door",
        "- `a1000010`: " + person(10),
        turn("before", "R1", 9),
        turn("after", "R1", 11),
    ]
    assert f"- R1 (session): {COUNTING} [b1000009, a1000010, b1000011]" in standing_lines(on) and OPENS in on


def test_a_standing_line_on_a_sentence_quoted_already_adds_its_turn_alone_and_a_turn_two_labels_set_is_one_line(
    tmp_path,
):
    """On a1000003, which the line at the door quotes: the standing line's turn after it is set beneath it and nothing
    is quoted again. Where the line at the door rests on that turn too, it is one line keyed by both, the line at the
    door first; and where two standing lines do, one line keyed by both, the newer first."""
    tove = "The tove is the person's."
    alone = held(tmp_path / "alone", [("relation", "both", tove, ["a1000003", "b1000004"])])
    assert packed(framed(alone)) == [
        "- `a1000003`: " + person(3),
        turn("after", "R1", 4, 5),
        "     ↳ N1: the line at the door",
    ]
    door = ("next", "session", DOOR, ["a1000003", "b1000004"])
    both = held(tmp_path / "both", [("relation", "session", tove, ["a1000003", "b1000004"])], door=door)
    assert packed(framed(both)) == [
        "- `a1000003`: " + person(3),
        turn("after", "N1, R1", 4, 5),
        "     ↳ N1: the line at the door",
    ]
    two = held(
        tmp_path / "two",
        [
            ("relation", "session", tove, ["a1000010", "b1000011"]),
            ("relation", "both", COUNTING, ["a1000010", "b1000011"]),
        ],
    )
    assert packed(framed(two))[2:] == ["- `a1000010`: " + person(10), turn("after", "R2, R1", 11)]


def test_a_carried_stack_sets_the_turn_a_line_beneath_it_sets_keyed_by_the_stack_two_deep(tmp_path):
    marks = [
        ("relation", "session", COUNTING, ["a1000010", "b1000011"]),
        ("relation", "session", "The wabe is the person's.", ["a1000006"]),
        ("relation", "session", "What the session holds of the counting.", ["R1"]),
    ]
    one = held(tmp_path / "one", marks)
    assert nested(framed(one)) == [turn("after", "R3", 11)]
    two = held(tmp_path / "two", [*marks, ("relation", "both", "All of it, as one.", ["R3", "R2"])])
    on = framed(two)
    assert nested(on) == [turn("after", "R4", 11)] and standing_lines(on) == [
        "- R4 (both): All of it, as one. [R3, R2]"
    ]
    # two lines beneath it on the same pair: the turn is set once, by the stack's key
    same = [
        ("relation", "session", COUNTING, ["a1000010", "b1000011"]),
        ("relation", "both", "The person counts aloud.", ["a1000010", "b1000011"]),
        ("relation", "session", "Both, as one.", ["R1", "R2"]),
    ]
    assert nested(framed(held(tmp_path / "same", same))) == [turn("after", "R3", 11)]


def test_a_misaligned_stack_looks_through_nothing_and_its_line_sets_its_turn_by_its_own_key(tmp_path):
    marks = [
        ("relation", "session", COUNTING, ["a1000010", "b1000011"]),
        ("relation", "session", "The wabe is the person's.", ["a1000006"]),
        ("relation", "session", "Both, as one.", ["R1", "R2"]),
    ]
    crossings = held(tmp_path, marks)
    assert nested(framed(crossings)) == [turn("after", "R3", 11)]
    assert store.strike(crossings, "R2")["struck"]  # a line beneath it gone: the stack is misaligned
    on = framed(crossings)
    assert "- R3 (session): Both, as one. (to be written again: a line beneath it changed) [R1, R2]" in standing_lines(
        on
    )
    assert nested(on) == [turn("after", "R1", 11)]


def test_a_frame_where_no_standing_line_sets_a_turn_is_the_frame_of_before(tmp_path):
    """Pin: the person's line on both ends of a1000010; the person's line beneath a stack of the session's; a stack of
    the person's over the session's line on both ends, which it hides; two lines of the session's on one end each,
    stacked, which never set a turn by what they rest on together; a line beneath a sound stack, left unresolved by a
    strike; a line on both ends of a sentence noted as holding a key; one on both ends that is not carried; and at the
    least size, for a new session and with no session named, a line that sets its turns at the usual size (see the
    first test of this part, on the same labels). Each frame is the
    one 9719e2f made, by length and digest, and the one made without turns; and in the home on this computer, which
    holds no message, no such line can be marked."""
    on_both = ["b1000009", "a1000010", "b1000011"]
    secret = rows_of(ORDER, {"a1000010": "Here it is: password=made-up-tove-123456 for the wabe."})
    homes = {
        "his": held(tmp_path / "his", [("relation", "his", COUNTING, on_both)]),
        "his beneath": held(
            tmp_path / "his beneath", [("relation", "his", COUNTING, on_both), ("relation", "session", "Held.", ["R1"])]
        ),
        "his stack": held(
            tmp_path / "his stack", [("relation", "session", COUNTING, on_both), ("relation", "his", "Mine.", ["R1"])]
        ),
        "together": held(
            tmp_path / "together",
            [
                ("relation", "session", "On the ask.", ["a1000010"]),
                ("relation", "session", "On the answer.", ["b1000011"]),
                ("relation", "session", "Both, as one.", ["R1", "R2"]),
            ],
        ),
        "unresolved": held(
            tmp_path / "unresolved",
            [
                ("relation", "session", COUNTING, ["a1000010", "b1000011", "a1000012"]),
                ("relation", "session", "The wabe is the person's.", ["a1000006"]),
                ("relation", "session", "Both, as one.", ["R1", "R2"]),
            ],
        ),
        "flagged": held(tmp_path / "flagged", [("relation", "session", COUNTING, on_both)], rows=secret),
        "not carried": made(tmp_path / "not carried", anchors=["a1000003"], full=True),
        "least": held(tmp_path / "least", [("relation", "session", COUNTING, on_both)]),
    }
    assert store.strike(homes["unresolved"], "a1000012")["struck"]
    # after the fixture's forty-five lines and its own of the person's (R46), one of the session's on both ends: R47
    assert store.mark(homes["not carried"], "relation", "session", COUNTING, on_both, day=DAY)["written"]
    for name, crossings in homes.items():
        size = frame.LEAST if name == "least" else 9000
        on = framed(crossings, size)
        assert on == framed(crossings, size, turns=False) and not nested(on), name
        assert digest(on) == NOTHING[name], name
    least = homes["least"]
    assert digest(frame.compose(least, new=True)) == NOTHING["new"] and digest(frame.compose(least)) == NOTHING["none"]
    with set_to(CROSSING_OURS=str(tmp_path / "ours")):
        ours = store.ours()
        ours.mkdir()
        refused = store.mark(ours, "relation", "session", COUNTING, on_both, day=DAY)
        assert not refused["written"] and refused["why"].startswith("no such message in the archive")
        assert not nested(frame.compose(ours, session=SESSION))


def test_standing_turns_are_tried_the_newest_line_first_within_the_allowance_also_with_no_line_at_the_door(tmp_path):
    """Twelve standing lines, each on a sentence of the person's and the session's answer to it, and no line at the door:
    the turns and the sentences quoted for them take at most what a line at the door may be (store.LONGEST), less the
    opening's words for them. Eight fit, and they are those of the eight newest lines, each with its sentence; each of
    the four oldest is tried and goes whole."""
    marks = [
        ("relation", "session", f"Standing line {k}.", [f"a1{2 * k - 1:06d}", f"b1{2 * k:06d}"]) for k in range(1, 13)
    ]
    crossings = held(tmp_path, marks, rows=rows_of("ab" * 13), door=None)
    on = framed(crossings)
    keys = [line.split(" (")[1].split(")")[0] for line in nested(on)]
    assert keys == [f"R{k}" for k in range(12, 4, -1)]
    lines = packed(on)
    assert lines[:2] == ["- `a1000023`: " + person(23), turn("after", "R12", 24)] and len(lines) == 16
    each = len(lines[0]) + len(lines[1]) + 2
    assert (
        sum(len(line) + 1 for line in lines)
        <= store.LONGEST - len(frame.BESIDE)
        < sum(len(x) + 1 for x in lines) + each
    )


# The frames c542766 made of the homes of the test below: four and eight standing lines, each on a sentence and its answer.
LAID = {
    4: (4083, "3ac41285cd1f395fc4fb32184283d6aaa6e93b8ed332c7bfa000f623879ef49e"),
    8: (6150, "b508e8e1227f1d0b81b02468b387eab4a93092b9ee6e3b728cb3965726a23358"),
}


def test_each_turn_is_laid_once_for_a_frame_however_often_the_frame_is_laid_again(tmp_path):
    """Guard: the frame is laid again for every turn a standing line sets that is tried, and for every row that gives
    way, and every turn kept was laid again each time, its messages' words cleaned again: 14 times for four turns of
    one message each, 44 for eight, 4 for the one turn two rows give way to at the ceiling. A turn's line is laid once
    for a frame now, its words cleaned once, and the frame is the same, byte for byte."""
    real, cleaned = store.clean, []

    def clean(text, lines=False):
        if lines:  # the words of a message, cleaned to be shown on one line beside a sentence (see frame._nested)
            cleaned.append(text)
        return real(text, lines)

    def laid(crossings: Path, size: int) -> str:
        cleaned.clear()
        store.clean = clean
        try:
            return frame.compose(crossings, size, session=SESSION)
        finally:
            store.clean = real

    for count in (4, 8):
        marks = [
            ("relation", "session", f"Standing line {k}.", [f"a1{2 * k - 1:06d}", f"b1{2 * k:06d}"])
            for k in range(1, count + 1)
        ]
        on = laid(held(tmp_path / str(count), marks, rows=rows_of("ab" * count), door=None), 9500)
        assert len(nested(on)) == count and len(cleaned) == count, (count, len(cleaned))
        assert digest(on) == LAID[count], count
    full = held(tmp_path / "full", [], rows=rows_of(ORDER, SHORT), page=FULL, door=("next", "session", DOOR, ONE_ENDED))
    on = laid(full, 9100)
    assert nested(on) == ["     · after it, the session (R1): `b1000011` Counted first, then mapped."]
    assert cleaned == [SHORT["b1000011"]]


def test_at_the_ceiling_a_standing_turn_takes_only_rows_the_top_up_added(tmp_path):
    """In a full frame of 9,100 characters, the oldest standing line, R1, sets the short turn after a1000010 only once
    two rows the top-up added give way, the last added first: every other work row, every standing line and every
    sentence the frame made without it carries is still there, and the frame stays within its size."""
    crossings = held(tmp_path, [], rows=rows_of(ORDER, SHORT), page=FULL, door=("next", "session", DOOR, ONE_ENDED))
    on, off = framed(crossings, 9100), framed(crossings, 9100, turns=False)
    assert nested(on) == ["     · after it, the session (R1): `b1000011` Counted first, then mapped."]
    (quotes_on, work_on), (quotes_off, work_off) = quotes_and_work(on), quotes_and_work(off)
    assert quotes_on == quotes_off | {"a1000010"} and work_off - work_on == {"W112", "W113"} and work_on < work_off
    assert standing_lines(on) == standing_lines(off) and len(on) <= 9100


def test_a_standing_turn_tried_that_does_not_fit_leaves_the_frame_as_it_is_without_it_with_its_rows_back(tmp_path):
    """The same full frame at 9,100, the turn after a1000010 a long one: it is tried, and it takes more than the short
    one, for which two rows gave way (above), so those two gave way for it too; it does not fit once every row the
    top-up added is gone, and goes whole, and the rows come back: the frame is the one made without turns, byte for
    byte, and 9719e2f's."""
    door = ("next", "session", DOOR, ONE_ENDED)
    short = held(tmp_path / "short", [], rows=rows_of(ORDER, SHORT), page=FULL, door=door)
    long = held(tmp_path / "long", [], page=FULL, door=door)
    assert nested(framed(short, 9100))  # this one is set: the rows the top-up added are there to give way
    on = framed(long, 9100)
    assert on == framed(long, 9100, turns=False) and digest(on) == NOTHING["long"]
    # and so beside a sentence the line at the door quotes already (a1000003): its long turn goes, the sentence stays
    page = FULL.replace("`a1000010`, `b1000011`", "`a1000003`, `b1000004`", 1)
    quoted_ = held(tmp_path / "quoted", [], page=page, door=door)
    on = framed(quoted_, 9100)
    assert on == framed(quoted_, 9100, turns=False) and "- `a1000003`: " + person(3) in packed(on)


def test_through_a_standing_line_a_key_a_refusal_and_another_model_are_kept_as_at_the_door(tmp_path):
    """The guards of the line at the door's turns hold for a standing line's: a message that looks like it holds a key,
    and one a refusal rests on, by its id alone; another model's message named with its model; and a sentence noted as
    holding a key is not quoted, so nothing is set beside it."""
    texts = {
        "b1000004": "The key is password: made-up-tove-1234 for now.",
        "b1000005": "Then the wabe.",
        "a1000010": "Here it is: password=made-up-tove-123456 for the wabe.",
    }
    marks = [
        ("refused", "session", "The tove is not gyred: the wabe is first.", ["b1000007"]),
        ("relation", "session", "The tove is the person's.", ["a1000003", "b1000004"]),
        ("relation", "session", "The wabe is the person's.", ["a1000006", "b1000007"]),
        ("relation", "session", COUNTING, ["b1000009", "a1000010", "b1000011"]),
    ]
    crossings = held(tmp_path, marks, rows=rows_of(ORDER, texts), door=("next", "session", DOOR, ["a1000016"]))
    on = framed(crossings)
    assert nested(on) == [
        "     · after it, the session (R2): `b1000007`",
        "     · after it, the session (R1): `b1000004` `b1000005` Then the wabe.",
    ]
    assert "made-up-tove-1234" not in on and "made-up-tove-123456" not in on and "`a1000010`:" not in on
    models = {"b1000004": "made-up-model-a", "b1000005": "made-up-model-b"}
    short = {"b1000004": "Four, short.", "b1000005": "Five, short."}
    other = held(
        tmp_path / "other",
        [("relation", "session", "The tove is the person's.", ["a1000003", "b1000004"])],
        rows=rows_of(ORDER, short, models),
    )
    assert nested(framed(other, model="made-up-model-b")) == [
        "     · after it, the session (R1): `b1000004` (made-up-model-a) Four, short. `b1000005` Five, short."
    ]


def test_the_trade_counts_the_sentence_quoted_for_a_standing_turn_and_names_the_work_rows_that_gave_way(tmp_path):
    crossings = held(tmp_path, [], rows=rows_of(ORDER, SHORT), page=FULL, door=("next", "session", DOOR, ONE_ENDED))
    on = framed(crossings, 9100)
    took = sum(len(line) + 1 for line in [*nested(on), "- `a1000010`: " + person(10)]) + len(frame.BESIDE)
    assert frame.trade(crossings, on, 9100, session=SESSION) == (
        f"{TRADE}{took:,} characters of it; the labels it would carry without them: W113, W112; the person's "
        "sentences it would quote without them: none."
    )


# --- a refusal where turns are tied ---------------------------------------------------------------------------------


def families_carried(made_: str) -> list[str]:
    """The keys of the families a frame carries in words, packed beneath a sentence or in their own part."""
    return [
        line.split("↳ ")[1].split(" ·")[0] if "· refused:" in line else line[2:].split(" ")[0]
        for line in made_.split("\n")
        if "· refused:" in line or line.startswith("- X")
    ]


def families(crossings: Path, long: int, asks: tuple = ("a1000012", "a1000014", "a1000016")) -> list[str]:
    """A family a sentence of the person's, each refused for a reason `long` characters long; the reasons, the
    oldest first."""
    reasons = []
    for k, ask in enumerate(asks, 1):
        reason = (f"Refused {k}: " + "the tove is not gyred before the wabe is mapped, " * 90)[:long].rstrip() + "."
        assert store.mark(crossings, "refused", "session", reason, [ask], day=DAY)["written"]
        reasons.append(reason)
    return reasons


def test_every_family_that_stands_crosses_in_words_at_every_size_with_turns_and_without(tmp_path):
    """Guard: the line at the door's turns were reserved before the families were fitted, three families at the most
    crossed, and the rest went to a sentence that counts them. Three families of 600-character reasons crossed at the
    usual size as two and "1 more refusal stands and is not carried: X1", where the frame made without turns carried
    all three; in a full home at 6,000, three short families crossed as none. Each family that stands crosses by its
    sentence, whole, at every size, in a cut's frame with turns and without and in a new session's, and no sentence
    counts them."""
    long = made(tmp_path / "long")
    full = made(tmp_path / "full", full=True)
    homes = {"long": (long, families(long, 600)), "full": (full, families(full, 100))}
    for name, (crossings, reasons) in homes.items():
        for size in [*range(frame.LEAST, frame.MOST, 500), frame.MOST]:
            for how, made_ in (
                ("turns", framed(crossings, size)),
                ("none", framed(crossings, size, turns=False)),
                ("new", frame.compose(crossings, size, new=True)),
            ):
                assert sorted(families_carried(made_)) == ["X1", "X2", "X3"], (name, size, how)
                assert all(reason in made_ for reason in reasons) and "more refusal" not in made_, (name, size, how)
                assert len(made_) <= frame.MOST, (name, size, how)


def test_five_families_of_600_characters_cross_in_words_at_9000_and_what_gave_way_is_named(tmp_path):
    """Guard: five families in a full home at the usual size crossed as three, and "2 more refusals stand and are not
    carried: X1, X2". All five cross in words now, the newest first; the work gave way to them first, then the
    standing lines, the newest first, and the line at the door's turns, which are the tail of that line, come after
    them: all ten are set, and the frame carries every label a frame without turns carries when its line at the door
    is as long as the line with them. Every standing line and every work row the frame does not carry is named, by key
    or by count, as the frame names what it leaves out."""
    crossings = made(tmp_path, full=True)
    reasons = families(crossings, 600, ("a1000003", "a1000006", "a1000008", "a1000012", "a1000016"))
    on = framed(crossings)
    assert families_carried(on) == ["X5", "X4", "X3", "X2", "X1"] and all(reason in on for reason in reasons)
    assert "more refusal" not in on and len(on) <= frame.SIZE
    standing = [f"R{n}" for n in range(1, 47)]  # the fixture's lines of the person's, the oldest first
    shown = [key for key in standing if f"- {key} (theirs):" in on]
    left = standing[len(shown) :]
    assert shown == standing[: len(shown)]  # the newest standing lines gave way, as ever
    if left:
        some = len(left) != 1
        assert (
            f"{len(left)} standing line{'s' if some else ''} did not fit and {'are' if some else 'is'} not carried: "
            f"{left[0]}{' to ' + left[-1] if some else ''}; `labels` gives them."
        ) in on
    work = {line.split(" (")[0].split()[-1] for line in on.split("\n") if line.startswith(("- W", "     ↳ W"))}
    assert f"{120 - len(work)} more labels in the store: `labels` lists them." in on
    account: dict = {}
    assert frame._made(crossings, None, False, "", SESSION, account=account) == on and len(nested(on)) == 10
    as_long = made(tmp_path / "as long", full=True, door_text=DOOR + " " + "x" * (account["nested"] - 1))
    families(as_long, 600, ("a1000003", "a1000006", "a1000008", "a1000012", "a1000016"))
    off = framed(as_long, turns=False)
    assert len(door_line(off)) == len(door_line(on)) + account["nested"] and labels_written(off) <= labels_written(on)


def test_the_line_at_the_door_gives_way_to_the_families_last_down_to_its_least(tmp_path):
    """A line at the door of 1,500 characters and three families of 600: at the usual size the line crosses whole;
    at the least size the families cross whole and the line is cut to its least, 300 characters, and the frame is as
    long as they and the frame's fixed sentences are; between, the line is cut no further than the families need."""
    long_line = ("The tove is to be gyred before the wabe is mapped and the borogoves are counted. " * 20)[
        :1500
    ].strip()
    crossings = made(tmp_path, anchors=ONE_ENDED, door_text=long_line)
    reasons = families(crossings, 600)
    usual, least = framed(crossings), framed(crossings, frame.LEAST)
    assert long_line in usual and families_carried(usual) == ["X3", "X2", "X1"]
    assert all(reason in least for reason in reasons) and long_line not in least
    assert len(door_line(least).split("\n")[0]) <= frame.DOOR and door_line(least).endswith(
        " […] `labels` gives it whole."
    )
    assert len(least) > frame.LEAST and not nested(least) and "- `a1" not in least
    for size in range(frame.LEAST, frame.SIZE, 500):
        made_ = framed(crossings, size)
        assert sorted(families_carried(made_)) == ["X1", "X2", "X3"], size
        # the line is cut only once everything before it gave way: the standing line, and the sentences quoted for
        # the line alone (a1000012 and a1000016 are the families' asks too)
        others = ("- R", "- `a1000003`", "- `a1000006`", "- `a1000008`")
        assert long_line in made_ or not any(each in made_ for each in others), size


def test_a_standing_lines_turn_is_tried_after_the_families_and_none_gives_way_to_it(tmp_path):
    """Pin: three families of 900-character reasons and a standing line of the session's on both ends of a1000010:
    its turns are set, and every family is carried as the frame made without turns carries it."""
    standing = ("relation", "session", COUNTING, ["b1000009", "a1000010", "b1000011"])
    crossings = held(tmp_path, [standing], door=("next", "session", DOOR, ONE_ENDED))
    families(crossings, 900)
    for size in (9000, 9500):
        on, off = framed(crossings, size), framed(crossings, size, turns=False)
        assert nested(on) and families_carried(on) == families_carried(off) == ["X3", "X2", "X1"], size


ASKED = {
    "a1000003": "Person 3: delete the borogove branch now, please.",
    "b1000004": "Session 4: No: the borogove branch holds work not merged, so it stays.",
    "a1000007": "Person 7: the work is merged now, so delete it?",
    "b1000008": "Session 8: Still not: the person asked for a tag first.",
    "a1000011": "Person 11: leave the branch; it does not matter now.",
    "b1000012": "Session 12: Then the refusal rests.",
}
SINGLE = rows_of("ababababababab", ASKED)  # every turn one message: a1 | b2 | a3 | b4 | ... | b14
BRANCH = "The branch is not deleted: it holds work not merged."
TAG = "Still not deleted: the person asks for a tag first."
LET_BE = "The person let the branch be; nothing is asked any more."
ASKING = "The person asks before anything is deleted."
ON_13 = ("next", "session", DOOR, ["a1000013"])  # a line at the door on a sentence alone: it sets no turn
OVER = [("relation", "session", "The wabe is the person's.", ["a1000005"]), ("relation", "session", "Over it.", ["R1"])]
DECLINED = ("No: the borogove", "Still not: the", "Then the refusal")  # the session's answers to the asks, in words


def without_turns(on: str) -> str:
    """A frame that sets turns, less its turns and the opening's words for them."""
    return "\n".join(line for line in on.replace(frame.BESIDE, "", 1).split("\n") if not line.startswith(NESTED))


def test_a_family_crosses_line_for_line_as_without_turns_and_its_declining_message_by_its_id_alone(tmp_path):
    """Pin: a refusal on the ask and on the session's declining answer; the line at the door on both ends, a standing
    line of the session's on both, a stack over that line, and a judgment on the next pair: each frame, less its turns,
    is the frame made without them, and the messages the family rests on stand by their ids alone."""
    refused = ("refused", "session", BRANCH, ["a1000003", "b1000004"])
    door = held(tmp_path / "door", [refused], rows=SINGLE, door=("next", "session", DOOR, ["a1000003", "b1000004"]))
    on = framed(door)
    assert packed(on) == [
        "- `a1000003`: " + ASKED["a1000003"],
        "     · after it, the session (N1): `b1000004`",
        f"     ↳ X1 · refused: {BRANCH}",
        "     ↳ N1: the line at the door",
    ]
    assert without_turns(on) == framed(door, turns=False)
    standing = ("relation", "session", ASKING, ["a1000003", "b1000004"])
    for name, marks, key in (("standing", [refused, standing], "R1"), ("stack", [refused, standing, *OVER], "R3")):
        crossings = held(tmp_path / name, marks, rows=SINGLE, door=ON_13)
        on = framed(crossings)
        assert packed(on)[:3] == [
            "- `a1000003`: " + ASKED["a1000003"],
            f"     · after it, the session ({key}): `b1000004`",
            f"     ↳ X1 · refused: {BRANCH}",
        ], name
        assert without_turns(on) == framed(crossings, turns=False) and DECLINED[0] not in on, name
    judged = ("refused", "session", TAG, ["X1", "a1000007", "b1000008"])
    door_ = ("next", "session", DOOR, ["a1000003", "b1000004", "a1000007", "b1000008"])
    again = held(tmp_path / "again", [refused, judged], rows=SINGLE, door=door_)
    on = framed(again)
    assert packed(on) == [
        "- `a1000003`: " + ASKED["a1000003"],
        "     · after it, the session (N1): `b1000004`",
        "     ↳ N1: the line at the door",
        "- `a1000007`: " + ASKED["a1000007"],
        "     · after it, the session (N1): `b1000008`",
        f"     ↳ X2 · refused: {TAG} (judged again once)",
        "     ↳ N1: the line at the door",
    ]
    assert without_turns(on) == framed(again, turns=False) and BRANCH not in on and DECLINED[1] not in on


def test_silenced_no_word_of_the_family_crosses_through_any_turn_and_the_ask_is_quoted_only_for_another_label(tmp_path):
    """Pin: put to rest, a family crosses in no line, and every message of its run stands by its id alone in the turns
    the line at the door, a standing line of the session's and a stack over it set; the ask is quoted for the line at
    the door or the standing line that rests on it, and with nothing else on it, not at all."""
    marks = [
        ("refused", "session", BRANCH, ["a1000003", "b1000004"]),
        ("refused", "session", TAG, ["X1", "a1000007", "b1000008"]),
        ("silenced", "session", LET_BE, ["X2", "b1000012"]),
    ]
    door = ("next", "session", DOOR, ["a1000003", "b1000004", "a1000007", "b1000008", "a1000011", "b1000012"])
    by_door = framed(held(tmp_path / "door", marks, rows=SINGLE, door=door))
    assert nested(by_door) == [f"     · after it, the session (N1): `b1{n:06d}`" for n in (4, 8, 12)]
    framed_ = [by_door]
    standing = ("relation", "session", ASKING, ["a1000003", "b1000004"])
    for name, more, key in (("standing", [standing], "R1"), ("stack", [standing, *OVER], "R3")):
        on = framed(held(tmp_path / name, marks + more, rows=SINGLE, door=ON_13))
        assert nested(on) == [f"     · after it, the session ({key}): `b1000004`"], name
        assert "- `a1000003`: " + ASKED["a1000003"] in packed(on), name  # quoted for the line on both ends of the pair
        framed_.append(on)
    alone = framed(held(tmp_path / "alone", marks, rows=SINGLE, door=ON_13))
    assert "a1000003" not in alone
    for on in [*framed_, alone]:
        assert not families_carried(on) and "more refusal" not in on
        assert not any(each in on for each in (BRANCH, TAG, LET_BE, *DECLINED))


def test_beside_an_ask_a_family_rests_on_the_sessions_turn_stands_by_its_ids_alone_standing_or_silenced(tmp_path):
    """Guard: a refusal rests on the message that asked, its sentence the reason (docs/store.md), a judgment or a
    silencing on the message where its reason was said, and any of them may rest on a text pasted into a message.
    Where the line at the door, a standing line of the session's or a stack over it rested on such a message of the
    person's and on the session's turn right after it, that turn was set beneath it in words, under the family's own
    line: `· after it, the session (N1): `b1000004` Session 4: No: the borogove branch holds work not merged, so it
    stays.`, and still so once the family was silenced; so too where it was set as the turn before the person's next
    sentence. That turn stands by its ids alone."""
    refused = ("refused", "session", BRANCH, ["a1000003"])
    pasted = rows_of("ababababababab", {**ASKED, "a1000003": WITH_PASTE})
    on_both = ("next", "session", DOOR, ["a1000003", "b1000004"])
    standing = ("relation", "session", ASKING, ["a1000003", "b1000004"])
    cases = [  # each: its marks, its line at the door, its rows, and the turn set beside a sentence, by its ids
        ("door", [refused], on_both, SINGLE, "after it, the session (N1): `b1000004`"),
        ("standing", [refused, standing], ON_13, SINGLE, "after it, the session (R1): `b1000004`"),
        ("stack", [refused, standing, *OVER], ON_13, SINGLE, "after it, the session (R3): `b1000004`"),
        (
            "paste",
            [("refused", "session", BRANCH, ["a1000003+1"])],
            on_both,
            pasted,
            "after it, the session (N1): `b1000004`",
        ),
        (
            "before",
            [refused],
            ("next", "session", DOOR, ["b1000004", "a1000005"]),
            SINGLE,
            "before it, the session (N1): `b1000004`",
        ),
    ]
    for name, marks, left, rows, turn in cases:
        crossings = held(tmp_path / name, marks, rows=rows, door=left)
        for stage in ("standing", "silenced"):
            if stage == "silenced":
                assert store.mark(crossings, "silenced", "session", LET_BE, ["X1", "b1000012"], day=DAY)["written"]
            on = framed(crossings)
            assert nested(on) == [NESTED + turn] and DECLINED[0] not in on, (name, stage)
    # a judgment on the person's message where its reason came, and a silencing on the person's own
    marks = [refused, ("refused", "session", TAG, ["X1", "a1000007"])]
    left = ("next", "session", DOOR, ["a1000007", "b1000008", "a1000011", "b1000012"])
    crossings = held(tmp_path / "judged", marks, rows=SINGLE, door=left)
    assert nested(framed(crossings)) == [
        "     · after it, the session (N1): `b1000008`",
        "     · after it, the session (N1): `b1000012` " + ASKED["b1000012"],
    ]
    assert store.mark(crossings, "silenced", "his", LET_BE, ["X2", "a1000011"], day=DAY)["written"]
    on = framed(crossings)
    assert nested(on) == [f"     · after it, the session (N1): `b1{n:06d}`" for n in (8, 12)]
    assert not any(each in on for each in DECLINED)


def test_beside_an_ask_the_record_cannot_place_between_twins_the_sessions_turn_stands_by_its_ids_alone(tmp_path):
    """Guard: a refusal marked through the server on the eight characters of the person's ask, and a line left at the
    door on the session's answer and the person's next sentence; then a message of the person's archived from another
    session under the same eight characters, said before the refusal was marked: the record cannot tell which of the
    two the refusal rests on, and it rests on neither. The answer was set as the turn before the next sentence in
    words, `· before it, the session (N1): `b1000002` Session 4: No: the borogove branch holds work not merged, so it
    stays.`, while the family stood and once it was silenced through the server. Every message of the person's under
    those eight characters counts as the ask now: the turn stands by its ids alone, in the frame `compose` makes for
    the session and in the one the server's `crossing` gives."""
    rows = rows_of("aba", {"a1000001": ASKED["a1000003"], "b1000002": ASKED["b1000004"]})
    crossings = held(tmp_path, [], rows=rows, door=None)
    project = str(crossings.parent)
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert served("mark", sentence=BRANCH, anchors=["a1000001"], kind="refused")[0].startswith("marked X1")
        assert served("leave", sentence=DOOR, anchors=["b1000002", "a1000003"])[0].startswith("marked N1")
    twin = said_row("a1000001", 0, "The twin of the ask, said in another session.")
    twin["uuid"] = "a1000001-1111-4000-8000-000000000000"  # a whole id of its own under the ask's eight characters
    path = tmp_path / "tied-two-0001.jsonl"
    path.write_text(json.dumps(twin) + "\n", encoding="utf-8")
    store.archive(path, crossings)
    store.build(crossings)
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert served("labels", ids=["X1"])[0].endswith(f"{BRANCH} [a1000001 (a1000001-0 or a1000001-1)]")
    for stage in ("standing", "silenced"):
        if stage == "silenced":
            with set_to(CLAUDE_PROJECT_DIR=project):
                assert served("mark", sentence=LET_BE, anchors=["X1", "a1000003"], kind="silenced")[0].startswith(
                    "marked S1"
                )
        with set_to(CLAUDE_PROJECT_DIR=project):
            by_server = served("crossing")[0]
        for how, on in (("compose", framed(crossings)), ("crossing", by_server)):
            assert nested(on) == [NESTED + "before it, the session (N1): `b1000002`"], (stage, how, nested(on))
            assert DECLINED[0] not in on and families_carried(on) == ([] if stage == "silenced" else ["X1"]), (
                stage,
                how,
            )


def test_a_refusal_on_the_sessions_message_the_record_cannot_place_between_twins_holds_it_to_its_ids(tmp_path):
    """Guard: a refusal marked through the server on the eight characters of the session's own declining answer, and
    a line left at the door on the person's ask and that answer; then a message of the session's archived from
    another session under the same eight characters, said before the refusal was marked: the refusal rests on
    neither. The answer, held to its id while the refusal rested on it alone, was set in words, `· after it, the
    session (N1): `b1000002` Session 4: No: the borogove branch holds work not merged, so it stays.`, while the
    family stood and once it was silenced through the server. Every message of the session's under those eight
    characters is held to its ids now, in the frame `compose` makes for the session and in the server's `crossing`."""
    rows = rows_of("aba", {"a1000001": ASKED["a1000003"], "b1000002": ASKED["b1000004"]})
    crossings = held(tmp_path, [], rows=rows, door=None)
    project = str(crossings.parent)
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert served("mark", sentence=BRANCH, anchors=["b1000002"], kind="refused")[0].startswith("marked X1")
        assert served("leave", sentence=DOOR, anchors=["a1000001", "b1000002"])[0].startswith("marked N1")
    turn = NESTED + "after it, the session (N1): `b1000002`"
    assert nested(framed(crossings)) == [turn]  # held to its id while the refusal rests on it alone
    twin = said_row("b1000002", 0, "The twin of the answer, said in another session.")
    twin["uuid"] = "b1000002-1111-4000-8000-000000000000"  # a whole id of its own under the answer's eight characters
    path = tmp_path / "tied-two-0001.jsonl"
    path.write_text(json.dumps(twin) + "\n", encoding="utf-8")
    store.archive(path, crossings)
    store.build(crossings)
    with set_to(CLAUDE_PROJECT_DIR=project):
        assert served("labels", ids=["X1"])[0].endswith(f"{BRANCH} [b1000002 (b1000002-0 or b1000002-1)]")
    for stage in ("standing", "silenced"):
        if stage == "silenced":
            with set_to(CLAUDE_PROJECT_DIR=project):
                assert served("mark", sentence=LET_BE, anchors=["X1", "a1000003"], kind="silenced")[0].startswith(
                    "marked S1"
                )
        with set_to(CLAUDE_PROJECT_DIR=project):
            by_server = served("crossing")[0]
        for how, on in (("compose", framed(crossings)), ("crossing", by_server)):
            assert nested(on) == [turn], (stage, how, nested(on))
            assert DECLINED[0] not in on and families_carried(on) == ([] if stage == "silenced" else ["X1"]), (
                stage,
                how,
            )


def test_a_refusal_on_one_message_of_a_turn_holds_that_one_to_its_id_and_the_others_keep_their_words(tmp_path):
    """Pin: the session refuses the middle message of a turn of three that the line at the door sets beneath a
    sentence, and says why in its next turn: those two stand by their ids alone, the others in words, and so once the
    refusal is silenced; the family crosses by its line in its own part, since it asked nothing of the person's."""
    texts = {
        "b1000004": "Session 4: first the tove.",
        "b1000005": "Session 5: the branch can be deleted now.",
        "b1000006": "Session 6: then the wabe.",
        "b1000008": "Session 8: message 5 was wrong: the branch holds work.",
    }
    door = ("next", "session", DOOR, ["a1000003", "b1000004", "a1000007", "b1000008"])
    wrong = ("refused", "session", "Message 5 was wrong: the branch holds work.", ["b1000005", "b1000008"])
    crossings = held(tmp_path, [wrong], rows=rows_of("ababbbabab", texts), door=door)
    turns = [
        "     · after it, the session (N1): `b1000004` Session 4: first the tove. `b1000005` `b1000006` Session 6: "
        "then the wabe.",
        "     · before it, the session (N1), as above: `b1000004` `b1000005` `b1000006`",
        "     · after it, the session (N1): `b1000008`",
    ]
    on = framed(crossings)
    assert nested(on) == turns and "can be deleted" not in on and "message 5 was wrong" not in on
    assert "- X1 (session): Message 5 was wrong: the branch holds work. [b1000005, b1000008]" in on.split("\n")
    assert store.mark(crossings, "silenced", "session", "The branch is gone after all.", ["X1", "b1000010"], day=DAY)[
        "written"
    ]
    on = framed(crossings)
    assert nested(on) == turns and not families_carried(on) and "can be deleted" not in on


def test_a_pair_names_the_family_resting_on_it_by_key_and_gives_the_declining_answer_as_the_record_holds_it(tmp_path):
    """Pin: `thread` with either role over the ask and the declining answer gives the answer word for word, as the
    record holds it, and names the refusal resting there by its key; once it is silenced the key stays, and the
    silencing is named only under the pair its own message stands in."""
    door = ("next", "session", DOOR, ["a1000003", "b1000004", "a1000011", "b1000012"])
    crossings = held(tmp_path, [], rows=SINGLE, door=door)

    def keys(at: str, role: str) -> str:
        with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
            said = served("thread", id=at, role=role)[0]
        assert (DECLINED[0] in said) == (at in ("a1000003", "b1000004")), (at, role)
        return next(line for line in said.split("\n") if line.startswith("Labels resting here: "))

    asked = (("a1000003", "pair:them"), ("b1000004", "pair:them"), ("b1000004", "pair:me"))
    assert all(keys(at, role) == "Labels resting here: N1." for at, role in asked)
    assert store.mark(crossings, "refused", "session", BRANCH, ["a1000003", "b1000004"], day=DAY)["written"]
    assert all(keys(at, role) == "Labels resting here: N1, X1." for at, role in asked)
    assert store.mark(crossings, "silenced", "session", LET_BE, ["X1", "b1000012"], day=DAY)["written"]
    assert all(keys(at, role) == "Labels resting here: N1, X1." for at, role in asked)
    assert keys("a1000011", "pair:them") == "Labels resting here: N1, S1."


def test_a_struck_message_a_refusal_rests_on_leaves_its_turn_and_the_family_is_named_by_key_as_without_turns(tmp_path):
    """The refusal rests on the ask and on the middle message of the session's turn after it, which is set by its ids
    alone; struck, that message is gone from the turn, id and all, and the refusal is named by its key among the
    labels that rest on what the archive no longer holds, as in the frame made without turns."""
    texts = {
        "b1000004": "Session 4: first the tove.",
        "b1000005": "Session 5: no, it stays.",
        "b1000006": "Session 6: then.",
    }
    door = ("next", "session", DOOR, ["a1000003", "b1000004"])
    refused = ("refused", "session", BRANCH, ["a1000003", "b1000005"])
    crossings = held(tmp_path, [refused], rows=rows_of("ababbbabab", texts), door=door)
    assert nested(framed(crossings)) == ["     · after it, the session (N1): `b1000004` `b1000005` `b1000006`"]
    assert store.strike(crossings, "b1000005")["struck"]
    on = framed(crossings)
    assert nested(on) == ["     · after it, the session (N1): `b1000004` `b1000006`"]
    assert "b1000005" not in on and BRANCH not in on and "first the tove" not in on
    assert "1 label rests on what the archive no longer holds: X1; `labels` gives them." in on
    assert without_turns(on) == framed(crossings, turns=False)


def test_a_refusal_on_a_pasted_text_crosses_by_its_line_and_the_answer_it_rests_on_by_its_id(tmp_path):
    rows = rows_of("ababababababab", {"a1000003": WITH_PASTE, "b1000004": ASKED["b1000004"]})
    door = ("next", "session", DOOR, ["a1000003", "b1000004"])
    crossings = held(tmp_path, [("refused", "session", BRANCH, ["a1000003+1", "b1000004"])], rows=rows, door=door)
    on = framed(crossings)
    assert nested(on) == ["     · after it, the session (N1): `b1000004`"]
    assert f"- X1 (session): {BRANCH} [a1000003+1, b1000004]" in on.split("\n")
    assert "Estimate for the hull" not in on and DECLINED[0] not in on
    assert without_turns(on) == framed(crossings, turns=False)


def test_a_refusal_in_another_models_hand_holds_its_message_to_its_id_in_this_models_turns(tmp_path):
    rows = rows_of("ababababababab", ASKED, {f"b1{n:06d}": "made-up-model-b" for n in range(2, 15, 2)})
    crossings = held(tmp_path, [], rows=rows, door=None)
    by_b = store.mark(
        crossings, "refused", "session", BRANCH, ["a1000003", "b1000004"], day=DAY, model="made-up-model-b"
    )
    by_a = store.mark(crossings, "next", "session", DOOR, ["a1000003", "b1000004"], day=DAY, model="made-up-model-a")
    assert by_b["written"] and by_a["written"]
    on = framed(crossings, model="made-up-model-a")
    assert nested(on) == ["     · after it, the session (N1): `b1000004`"]  # by its id alone, and so with no model
    assert not families_carried(on) and BRANCH not in on and DECLINED[0] not in on and "made-up-model-b" in on
    assert families_carried(framed(crossings)) == ["X1"]  # no model known: carried, as before layers


def labels_written(made_: str) -> set[str]:
    """The keys of the labels a frame writes out: the refusals, the standing lines and the work, packed or not."""
    keys = set(families_carried(made_))
    keys |= {line.split(" (")[0][2:] for line in made_.split("\n") if line.startswith("- R")}
    return keys | quotes_and_work(made_)[1]


# Homes shaped like the dry try on a home of real use: forty pairs, the person's sentences long, forty-five standing
# lines of the person's, a hundred and twenty labels about the work each resting on one of thirty-two of the person's
# sentences, and the line at the door on three pairs, each a sentence of the person's and the session's answer to it.
THREE_PAIRS = ["a1000003", "b1000004", "a1000009", "b1000010", "a1000015", "b1000016"]
COUNTED_AGAIN = "The borogoves were counted again and the count was written down in the book, line by line. "
GYRED = "the tove is to be gyred before the wabe is mapped, and the borogoves counted after it, one by one; "


def dry_door(length: int) -> str:
    """A line at the door of `length` characters, about the made-up session."""
    return (DOOR + " " + "The tove is to be gyred before the wabe is mapped. " * 90)[:length].strip()


def dry(folder: Path, standing: int, work: int, said: int, door_text: str, lines: int = 45) -> Path:
    """A home shaped like the dry try (see THREE_PAIRS): `lines` standing lines of `standing` characters, work labels
    of `work`, the person's sentences of `said`, and the line at the door `door_text`."""
    sentences = {f"a1{n:06d}": (f"Person {n}: " + GYRED * 9)[:said] for n in range(1, 80, 2)}
    asks = [f"a1{n:06d}" for n in range(17, 80, 2)]
    page = "".join(
        f"| R{n} | Day {n}: " + (COUNTED_AGAIN * 50)[:standing].strip() + " | his | `a1000001` |\n"
        for n in range(1, lines + 1)
    ) + "".join(
        f"| W{n} | Day {n}: " + (COUNTED_AGAIN * 50)[:work].strip() + f" | both | `{asks[n % len(asks)]}` |\n"
        for n in range(1, 121)
    )
    return held(
        folder, [], rows=rows_of("ab" * 40, sentences), page=page, door=("next", "session", door_text, THREE_PAIRS)
    )


def refused_in_full(folder: Path, door_text: str = DOOR) -> Path:
    """The full home, with one refusal of 50 characters on a sentence the line at the door rests on (a1000012)."""
    crossings = made(folder, full=True, door_text=door_text)
    families(crossings, 50, ("a1000012",))
    return crossings


def test_turns_never_cost_more_than_a_line_at_the_door_as_long_at_any_size(tmp_path):
    """Guard: the line at the door's turns were reserved before the standing lines and the work were fitted, and
    when the frame then let some of them go for its size, what they had reserved was not given back. In the full home
    at 6,000 six of the ten turns were kept and the frame carried no standing line and no work row, where a line at
    the door as long as the line with those six turns leaves room for six labels. And they were the first to give way,
    to a family and to what the packing adds: with one refusal of 50 characters in the full home, at 9,000 the frame
    set nine turns and lost R20, R21 and R22, which a line at the door as long carries, and so at eighteen of the
    thirty sizes from 4,000 to 9,500. The turns are the tail of the line at the door now. At every size from the least to the most, in
    the small home, the full one, the full one with that refusal and two homes shaped like the dry try, the frame with
    turns carries every label the frame without turns carries when its line at the door is as long as the line with
    the turns the first one keeps."""
    homes = {
        "small": (lambda folder, text: made(folder, door_text=text), DOOR),
        "full": (lambda folder, text: made(folder, full=True, door_text=text), DOOR),
        "refused": (refused_in_full, DOOR),
        "dry, long work": (lambda folder, text: dry(folder, 100, 900, 280, text), dry_door(3000)),
        "dry, short work": (lambda folder, text: dry(folder, 150, 250, 150, text), dry_door(1500)),
    }
    for name, (build, text) in homes.items():
        crossings = build(tmp_path / name, text)
        for size in sorted({*range(frame.LEAST, frame.MOST + 1, 500), *range(2500, frame.MOST + 1, 500)}):
            account: dict = {}
            on = frame._made(crossings, size, False, "", SESSION, account=account)
            took = account["nested"]
            if not took:
                assert on == framed(crossings, size, turns=False), (name, size)
                continue
            as_long = build(tmp_path / f"{name}-{size}", text + " " + "x" * (took - 1))
            off = framed(as_long, size, turns=False)
            assert len(door_line(off)) == len(door_line(on)) + took, (name, size)  # whole, as long as the two
            assert labels_written(off) <= labels_written(on), (
                name,
                size,
                sorted(labels_written(off) - labels_written(on)),
            )
            assert len(on) <= size, (name, size)


def test_where_the_sentences_the_line_does_not_rest_on_take_what_the_packing_adds_every_turn_it_holds_is_set(
    tmp_path,
):
    """Guard: in a full home shaped like the dry try, with short work labels each on a sentence of its own, the line at
    the door rests on three pairs and its allowance holds all three turns. Laid, the frame ran over for what the
    packing adds and a turn paid first; made again with that turn's room given back, the room went to standing lines,
    the frame ran over again and the next turn paid: at 9,000 one turn was set. The sentences the line does not rest on
    give way before its turns now, and every turn the allowance holds is set."""
    crossings = dry(tmp_path, 150, 250, 150, dry_door(1500))
    on = framed(crossings)
    assert [line.split(": `")[1].split("`")[0] for line in nested(on)] == ["b1000004", "b1000010", "b1000016"], nested(
        on
    )
    assert all("- `" + each + "`: " in on for each in ("a1000003", "a1000009", "a1000015")) and len(on) <= frame.SIZE
    off = framed(crossings, turns=False)
    assert quotes_and_work(off)[1] <= quotes_and_work(on)[1]  # no work label the frame without turns writes is lost


def test_a_refusal_no_longer_takes_the_turns_the_home_without_it_sets(tmp_path):
    """Guard: one refusal of 50 characters in the full home made the frame at 9,000 set nine turns, where the home
    without it sets ten: the turns gave way to it first. What it needs is taken from the work now, and the frame sets
    as many turns as the home without it; the refusal crosses whole, and the turn after its ask by its ids alone."""
    without = framed(made(tmp_path / "without", full=True))
    on = framed(refused_in_full(tmp_path / "refused"))
    assert len(nested(on)) == len(nested(without)) == 10, (len(nested(on)), len(nested(without)))
    assert families_carried(on) == ["X1"] and len(on) <= frame.SIZE
    assert NESTED + "after it, the session (N1): `b1000013`" in nested(on)


def test_the_sentence_after_the_frame_names_every_label_the_turns_cost(tmp_path):
    """Guard: the sentence after the frame named the standing lines and the work the turns cost, and said "the labels
    it would carry without them: none." where a family went for them to "1 more refusal stands and is not carried:
    X1". It names every label of any kind that the frame without turns carries and this one does not, and none
    other; and where the turns cost a refusal it names it first."""
    long = made(tmp_path / "long")
    families(long, 600)
    full = made(tmp_path / "full", full=True)
    for crossings, size in ((long, 9000), (full, 6000), (full, 9000), (full, 9500)):
        made_, trade = frame.with_trade(crossings, size, session=SESSION)
        gone = labels_written(framed(crossings, size, turns=False)) - labels_written(made_)
        listed = trade.split("the labels it would carry without them: ")[1].split(";")[0] if trade else "none"
        listed, _, more = listed.partition(" and ")  # past 24 keys, how many more there are
        named = set(listed.split(", ")) - {"none"}
        assert named <= gone and len(named) + int(more.split()[0] if more else 0) == len(gone), (
            crossings.parent.parent.name, size, sorted(gone), trade,
        )  # fmt: skip
    # the sentence of a frame whose turns cost a refusal, as `trade` would count it
    on = {"nested": 120, "refused": [], "standing": ["R1"], "work": [], "said": []}
    said = frame._traded(long, on, 9000, "", SESSION)
    assert "the labels it would carry without them: X3, X2, X1; " in said and said.startswith(TRADE), said


def test_the_sentence_after_the_frame_names_the_persons_sentences_the_turns_cost(tmp_path):
    """Guard: the turns give way after the sentences the line at the door does not rest on, so they may cost the frame
    a sentence of the person's that the frame made with no turn quotes; the sentence after the frame named the labels
    they cost and none of those sentences. It names them too now, by their ids, as the door and the server give it."""
    crossings = dry(tmp_path, 20, 250, 150, dry_door(1500), lines=0)  # no standing line: the work pays for the turns
    (crossings / "frame-size").write_text("8000\n", encoding="utf-8")
    made_, trade = frame.with_trade(crossings, session=SESSION)
    unquoted = sorted(quotes_and_work(framed(crossings, 8000, turns=False))[0] - quotes_and_work(made_)[0])
    assert len(nested(made_)) == 3 and unquoted == ["a1000061", "a1000063"] and trade.startswith(TRADE), (
        unquoted,
        trade,
    )
    named = trade.split("; the person's sentences it would quote without them: ")[1].rstrip(".")
    assert sorted(each.strip("`") for each in named.split(", ")) == unquoted, trade
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert served("crossing")[0] == f"{made_}\n{trade}\n"


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            # In the tests' own data folder, which test_store sweeps as the run ends.
            test(Path(tempfile.mkdtemp(prefix="crossing-test-", dir=DATA)))
            print("ok", name)
