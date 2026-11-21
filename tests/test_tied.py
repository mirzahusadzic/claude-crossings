"""A pair: `thread` asked with a role (store.tied, and the door's `thread --role`). `pair:them` is the pair headed by the
person's turn, `pair:me` the one headed by the session's, named from the session's side: a turn with the other voice's
next turn in the same session beneath it, in answer; named by a message of the heading voice, the pair its turn heads,
and by one of the other voice, the pair its turn answers. A turn is every message one voice said in a row in one
session, until the other spoke; a text the person pasted is the person's message's and breaks no turn. On made-up
transcripts of two sessions that speak at the same time, in a temporary home. No model, no network.

Run with pytest, or without it:  python3 tests/test_tied.py
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_handles import PASTED, WITH_PASTE  # noqa: E402
from test_off import asked, on_with_a_transcript, says, spans_file, switch  # noqa: E402
from test_serve import said  # noqa: E402
from test_store import DATA, home, in_person, row  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, sample, serve, store  # noqa: E402

THEM, ME = "pair:them", "pair:me"  # the roles, named from the session's side

# The first session ("talk-one"): a question answered twice; the person speaking twice in a row; and a message with a
# paste in it, answered last. Its turns: 1 | 2 3 | 4 5 | 6 | 7 | 8.
ONE = [
    row("user", "10000001", 1, "Shall we paint the hull before the launch?"),
    row("assistant", "10000002", 2, [{"type": "text", "text": "Yes: grey, as the yard has it."}]),
    row("assistant", "10000003", 3, [{"type": "text", "text": "Two coats, a day apart."}]),
    row("user", "10000004", 6, "And the mast?"),
    row("user", "10000005", 7, "Or is the tiller first?"),
    row("assistant", "10000006", 8, [{"type": "text", "text": "The tiller first, then the mast."}]),
    row("user", "10000007", 10, WITH_PASTE),
    row("assistant", "10000008", 11, [{"type": "text", "text": "The estimate is fair for two coats."}]),
]
# The second session ("talk-two"), whose messages stand among the first's in the order said.
TWO = [
    row("user", "20000001", 4, "A question asked in another session."),
    row("assistant", "20000002", 5, [{"type": "text", "text": "An answer given in another session."}]),
    row("assistant", "20000003", 9, [{"type": "text", "text": "A later word of the other session."}]),
]


def made(folder: Path, one: list = ONE, two: list = TWO) -> Path:
    """A home that holds both sessions, archived and built."""
    crossings, _ = home(folder, one, name="talk-one-0001")
    other = folder / "talk-two-0001.jsonl"
    other.write_text("".join(json.dumps(each) + "\n" for each in two), encoding="utf-8")
    store.archive(other, crossings)
    store.build(crossings)
    return crossings


def ids(rows: list[dict]) -> list[str]:
    return [each["id"] for each in rows]


ENTRY = re.compile(r"(\d+)\. `([^`]+)`")
FURTHER = re.compile(r"thread of `([^`]+)` with the role `([^`]+)` goes on from there\.")
AFTER = re.compile(r"[Tt]he pair after (?:this one begins|it) at `([^`]+)`; thread with the role `([^`]+)` gives")
BEFORE = re.compile(r"[Tt]he pair before this one begins at `([^`]+)`.*; thread with the role `([^`]+)` gives")


def paired(project: Path | str, at: str, role: str, *more: str) -> str:
    """The door's answer to `thread` asked with a role, from the person's own shell."""
    return through("thread", at, "--role", role, "--cwd", str(project), *more)[1]


def entries(shown: str) -> list[str]:
    return [line for line in shown.splitlines() if ENTRY.match(line)]


def listed(shown: str) -> list[str]:
    """The ids of the messages an answer shows, in its order."""
    return [ENTRY.match(line).group(2) for line in entries(shown)]


def quoted(shown: str) -> list[str]:
    return [line[len(door.QUOTED) :] for line in shown.splitlines() if line.startswith(door.QUOTED)]


def unmarked(shown: str) -> str:
    """A pair's answer without the id it was asked by and the marks on the one named: what every id of it gives."""
    first, rest = shown.split("\n", 1)
    return (
        re.sub(r"^thread of `[^`]+` with", "thread of … with", first)
        + "\n"
        + rest.replace(", the one you named:", ":").replace(", the one you named among them", "")
    )


def beneath(lines: list[str], entry: str) -> list[str]:
    """The two lines after the text of the message whose entry begins so."""
    at = next(n for n, line in enumerate(lines) if line.startswith(entry)) + 1
    while lines[at].startswith(door.QUOTED):
        at += 1
    return lines[at : at + 2]


def test_a_pair_headed_by_the_person_named_by_the_persons_is_their_turn_and_the_sessions_answer_in_order(tmp_path):
    crossings = made(tmp_path)
    out = store.tied(crossings, "10000001", store.HIS)
    assert out["found"] and out["paired"] and out["voice"] == "his" and out["named"] == "10000001"
    assert ids(out["head"]) == ["10000001"] and ids(out["answer"]) == ["10000002", "10000003"]  # the oldest first
    assert [each["text"] for each in out["answer"]] == ["Yes: grey, as the yard has it.", "Two coats, a day apart."]
    assert [each["voice"] for each in out["head"] + out["answer"]] == ["his", "session", "session"]
    assert [each["is_asked"] for each in out["head"] + out["answer"]] == [True, False, False]
    assert all(each["pastes"] == [] for each in out["head"] + out["answer"])


def test_a_pair_headed_by_the_session_named_by_the_sessions_is_its_turn_and_the_persons_answer(tmp_path):
    crossings = made(tmp_path)
    out = store.tied(crossings, "10000003", store.OWN)
    assert out["found"] and out["voice"] == "session" and out["named"] == "10000003"
    assert ids(out["head"]) == ["10000002", "10000003"] and ids(out["answer"]) == ["10000004", "10000005"]
    assert [each["voice"] for each in out["head"] + out["answer"]] == ["session", "session", "his", "his"]
    assert [each["is_asked"] for each in out["head"] + out["answer"]] == [False, True, False, False]
    shown = paired(crossings.parent, "10000003", ME)
    assert shown.splitlines()[0] == (
        "thread of `10000003` with the role `pair:me`: the session's turn, 2 messages, and the person's answer, "
        "2 messages, in the order they were said"
    )
    assert entries(shown) == [
        "1. `10000002` the session, 2026-11-11 09:02 UTC:",
        "2. `10000003` the session, 2026-11-11 09:03 UTC, the one you named:",
        "3. `10000004` the person, 2026-11-11 09:06 UTC:",
        "4. `10000005` the person, 2026-11-11 09:07 UTC:",
    ]
    assert door.QUOTED + "Or is the tiller first?" in shown.splitlines()
    assert "Shall we paint the hull" not in shown and "The tiller first" not in shown  # the turns before and after


def test_by_a_sessions_id_pair_him_gives_the_pair_it_answers_the_same_text_as_by_an_id_of_its_head(tmp_path):
    """Named by a message of the session's, the role of the person's gives the pair that message's turn answers,
    headed by the person's turn right before it: the same text as its head gives, but for the id asked and the one
    marked as named."""
    crossings = made(tmp_path)
    project = crossings.parent
    out = store.tied(crossings, "10000003", store.HIS)
    assert out["paired"] and out["voice"] == "his" and out["named"] == "10000003"
    assert ids(out["head"]) == ["10000001"] and ids(out["answer"]) == ["10000002", "10000003"]
    assert [each["is_asked"] for each in out["head"] + out["answer"]] == [False, False, True]
    assert out["before"] is None and out["after"] == "10000002"
    by_answer, by_head = paired(project, "10000003", THEM), paired(project, "10000001", THEM)
    assert by_answer.splitlines()[0] == (
        "thread of `10000003` with the role `pair:them`: the person's turn, 1 message, and the session's answer, "
        "2 messages, in the order they were said"
    )
    assert entries(by_answer)[-1] == "3. `10000003` the session, 2026-11-11 09:03 UTC, the one you named:"
    assert unmarked(by_answer) == unmarked(by_head) and by_answer != by_head
    text, failed = served(project, id="10000003", role=THEM)  # and so through the server
    assert not failed and text == paired(project, "10000003", THEM, "--bare").strip()


def test_by_a_persons_id_pair_me_gives_the_pair_headed_by_the_sessions_turn_before_it(tmp_path):
    """Named by a message of the person's, the role of the session's gives the pair the person's turn answers, headed
    by the session's turn before it; and so by a text pasted into one."""
    crossings = made(tmp_path)
    project = crossings.parent
    for at in ("10000004", "10000005"):
        out = store.tied(crossings, at, store.OWN)
        assert out["paired"] and out["voice"] == "session", at
        assert ids(out["head"]) == ["10000002", "10000003"] and ids(out["answer"]) == ["10000004", "10000005"], at
        assert out["before"] == "10000001" and out["after"] == "10000004", at
    shown = paired(project, "10000005", ME)
    assert shown.splitlines()[0].startswith("thread of `10000005` with the role `pair:me`: the session's turn, 2 ")
    assert entries(shown)[-1] == "4. `10000005` the person, 2026-11-11 09:07 UTC, the one you named:"
    assert unmarked(shown) == unmarked(paired(project, "10000002", ME))
    by_paste = store.tied(crossings, "10000007+1", store.OWN)  # pasted into the person's message that answers 10000006
    assert ids(by_paste["head"]) == ["10000006"] and ids(by_paste["answer"]) == ["10000007"]
    assert [each["is_asked"] for each in by_paste["answer"][0]["pastes"]] == [True]
    assert (
        served(project, id="10000007+1", role=ME)[0]
        .splitlines()[0]
        .startswith(
            "thread of `10000007+1` with the role `pair:me`: the session's turn, 1 message, and the person's answer"
        )
    )


def test_every_id_of_a_head_and_of_its_answer_gives_the_same_pair_with_the_same_role_whole_where_it_fits(tmp_path):
    """Each pair of the first session, by each role: every id of its head and of its answer, a pasted text's among
    them, gives the same pair, whole, the same to the character but for the id asked and the one marked as named."""
    crossings = made(tmp_path)
    project = crossings.parent
    pairs = {
        THEM: [
            ["10000001", "10000002", "10000003"],
            ["10000004", "10000005", "10000006"],
            ["10000007", "10000007+1", "10000008"],
        ],
        ME: [["10000002", "10000003", "10000004", "10000005"], ["10000006", "10000007", "10000007+1"], ["10000008"]],
    }

    def unnamed(out: dict) -> dict:
        rows = [
            {
                **{key: value for key, value in each.items() if key not in ("is_asked", "pastes")},
                "pastes": [
                    {key: value for key, value in paste.items() if key != "is_asked"} for paste in each["pastes"]
                ],
            }
            for each in out["head"] + out["answer"]
        ]
        return {key: value for key, value in out.items() if key not in ("asked", "named", "head", "answer")} | {
            "rows": rows
        }

    for role, groups in pairs.items():
        for group in groups:
            whole = [each for each in group if "+" not in each]
            shown = [paired(project, at, role) for at in group]
            assert all(unmarked(each) == unmarked(shown[0]) for each in shown), (role, group)
            assert all(listed(each) == whole and "this page" not in each for each in shown), (role, group)
            outs = [store.tied(crossings, at, door.ROLES[role]) for at in group]
            assert all(unnamed(each) == unnamed(outs[0]) for each in outs), (role, group)
    # At the ceiling, by every id of a head of two and of an answer of three: whole, and the same.
    rest = store.PAIRED - len("Shall we sail at dawn?") - len("Or at noon?") - 8000
    fits = made(tmp_path / "fits", fitted(rest), [])
    shown = [served(fits.parent, id=f"4000000{n}", role=THEM)[0] for n in range(1, 6)]
    assert all(listed(each) == [f"4000000{n}" for n in range(1, 6)] for each in shown)
    assert all(unmarked(each) == unmarked(shown[0]) for each in shown)
    assert sum(map(len, quoted(shown[4]))) == store.PAIRED and "this page" not in shown[4]


OPENED = [  # a session whose first word is the session's
    row("assistant", "30000001", 1, [{"type": "text", "text": "The yard opens at eight."}]),
    row("assistant", "30000002", 2, [{"type": "text", "text": "The crane is booked for nine."}]),
    row("user", "30000003", 3, "Then we lift at nine."),
    row("assistant", "30000004", 4, [{"type": "text", "text": "Nine it is."}]),
]


def test_a_first_turn_answers_nothing_and_asked_for_the_pair_it_answers_one_sentence_names_the_role_that_gives_one(
    tmp_path,
):
    """The session's first turn asked with `pair:them`, and the person's first turn asked with `pair:me`: there is no
    such pair, and one sentence says so and names the role that gives the pair the message heads, which it does."""
    opened = made(tmp_path / "opened", OPENED, [])
    for at in ("30000001", "30000002"):
        assert store.tied(opened, at, store.HIS) == {
            "asked": at,
            "found": True,
            "paired": False,
            "named": at,
            "voice": "his",
        }
        sentence = (
            f"thread of `{at}` with the role `pair:them`: the session's turn it stands in is the first of its session "
            "and answers no turn of the person's, so there is no such pair; the role `pair:me` gives the pair it heads."
        )
        assert paired(opened.parent, at, THEM) == sentence + "\n"
        assert served(opened.parent, id=at, role=THEM) == (sentence, False)
        assert paired(opened.parent, at, ME).startswith(f"thread of `{at}` with the role `pair:me`: the session's turn")
    crossings = made(tmp_path / "one", [row("user", "80000001", 1, WITH_PASTE), *ONE[1:3]], [])
    for at in ("80000001", "80000001+1"):  # the person's first turn, and a text pasted into it
        out = store.tied(crossings, at, store.OWN)
        assert out == {"asked": at, "found": True, "paired": False, "named": at, "voice": "session"}, at
        sentence = (
            f"thread of `{at}` with the role `pair:me`: the person's turn it stands in is the first of its session and "
            "answers no turn of the session's, so there is no such pair; the role `pair:them` gives the pair it heads."
        )
        assert paired(crossings.parent, at, ME) == sentence + "\n" and "Estimate" not in sentence, at
        assert paired(crossings.parent, at, THEM).startswith(
            f"thread of `{at}` with the role `pair:them`: the person's"
        )


def test_the_last_turn_of_a_session_says_nothing_came_after_it(tmp_path):
    crossings = made(tmp_path)
    out = store.tied(crossings, "10000008", store.OWN)
    assert out["voice"] == "session" and ids(out["head"]) == ["10000008"] and out["answer"] == []
    assert out["after"] is None and out["before"] == "10000007"
    lines = paired(crossings.parent, "10000008", ME).splitlines()
    assert lines[0] == (
        "thread of `10000008` with the role `pair:me`: the session's turn, 1 message, and the person's answer, "
        "0 messages, in the order they were said"
    )
    assert lines[-3:] == [
        "The person said nothing after it in that session.",
        "",
        "The pair before this one begins at `10000007`; thread with the role `pair:them` gives it.",
    ]
    # A session of one word of the person's, never answered: nothing after it, and no pair before or after.
    alone = made(tmp_path / "alone", ONE[:1])
    out = store.tied(alone, "10000001", store.HIS)
    assert out["answer"] == [] and out["before"] is None and out["after"] is None
    shown = paired(alone.parent, "10000001", THEM)
    assert shown.rstrip().endswith("\n\nThe session said nothing after it in that session.") and "The pair" not in shown


def test_a_sessions_opening_turn_of_the_sessions_heads_a_pair(tmp_path):
    crossings = made(tmp_path, OPENED, [])
    for at in ("30000001", "30000002", "30000003"):  # its head, and its answer
        out = store.tied(crossings, at, store.OWN)
        assert out["voice"] == "session" and ids(out["head"]) == ["30000001", "30000002"]
        assert ids(out["answer"]) == ["30000003"] and out["before"] is None and out["after"] == "30000003"
    lines = paired(crossings.parent, "30000001", ME).splitlines()
    assert lines[0] == (
        "thread of `30000001` with the role `pair:me`: the session's turn, 2 messages, and the person's answer, "
        "1 message, in the order they were said"
    )
    assert lines[-1] == "The pair after this one begins at `30000003`; thread with the role `pair:them` gives it."
    out = store.tied(crossings, "30000003", store.HIS)  # and the person's answer heads the pair after it
    assert ids(out["head"]) == ["30000003"] and ids(out["answer"]) == ["30000004"] and out["before"] == "30000001"


def test_stepping_by_the_after_id_and_role_of_the_closing_line_passes_every_turn_once_as_a_head_and_ends(tmp_path):
    """From a session's first message, by the role of its own voice, on by the id the closing line gives the pair
    after at and the role it names: each pair is headed by the other voice's turn, so the role flips at each step, and
    every turn heads one pair, once, in order, the last of them with no answer; then the line names no pair after.
    Back by the pair before, the same pairs come in the other order."""
    crossings = made(tmp_path)
    project = crossings.parent
    first = paired(project, "10000004", THEM).splitlines()[-1]
    assert first == (
        "The pair before this one begins at `10000002`, and the pair after it at `10000006`; thread with the role "
        "`pair:me` gives each."
    )
    for data, start, role, turns in (
        (
            ONE,
            "10000001",
            THEM,
            [
                ["10000001"],
                ["10000002", "10000003"],
                ["10000004", "10000005"],
                ["10000006"],
                ["10000007"],
                ["10000008"],
            ],
        ),
        (OPENED, "30000001", ME, [["30000001", "30000002"], ["30000003"], ["30000004"]]),
    ):
        folder = made(tmp_path / start, data, [])
        heads, roles, at = [], [], start
        while at is not None and len(heads) <= len(data):
            out = store.tied(folder, at, door.ROLES[role])
            heads.append(ids(out["head"]))
            roles.append(role)
            further = AFTER.search(paired(folder.parent, at, role))
            assert (further.group(1) if further else None) == out["after"]
            at, role = (further.group(1), further.group(2)) if further else (None, role)
        assert heads == turns  # every turn of the session heads a pair, once, and the walk ends
        assert [each for head in heads for each in head] == [each["uuid"][:8] for each in data]
        assert all(one != two for one, two in zip(roles, roles[1:]))  # the role flips at every step
        back, at, role = [], heads[-1][0], roles[-1]
        while at is not None and len(back) <= len(data):  # and back, by the pair before
            back.append(ids(store.tied(folder, at, door.ROLES[role])["head"]))
            earlier = BEFORE.search(paired(folder.parent, at, role))
            at, role = (earlier.group(1), earlier.group(2)) if earlier else (None, role)
        assert back == heads[::-1]


def test_pastes_are_named_under_a_persons_message_in_an_answer_as_in_a_head(tmp_path):
    crossings = made(tmp_path)
    project = str(crossings.parent)
    paste = {"id": "10000007+1", "name": "10000007+1", "length": len(PASTED), "is_asked": False, "labels": []}
    answered = store.tied(crossings, "10000006", store.OWN)  # the session's turn, answered by the message pasted into
    assert answered["voice"] == "session" and ids(answered["answer"]) == ["10000007"]
    assert answered["answer"][0]["pastes"] == [paste] and answered["head"][0]["pastes"] == []
    headed = store.tied(crossings, "10000007", store.HIS)
    assert ids(headed["head"]) == ["10000007"] and headed["head"][0]["pastes"] == [paste]
    by_paste = store.tied(crossings, "10000007+1", store.HIS)  # a paste's id names the pair of the message it came in
    assert by_paste["named"] == "10000007+1" and ids(by_paste["head"]) == ["10000007"]
    assert ids(by_paste["answer"]) == ["10000008"] and by_paste["head"][0]["pastes"] == [{**paste, "is_asked": True}]
    assert not any(each["is_asked"] for each in by_paste["head"] + by_paste["answer"])
    assert all(PASTED not in json.dumps(out) for out in (answered, headed, by_paste))  # never a word of it
    line = (
        "The person pasted 1 text into it, not shown here: `10000007+1` (84 characters); thread gives it in its place."
    )
    for at, role, entry in (
        ("10000006", ME, "2. `10000007` the person"),
        ("10000007", THEM, "1. `10000007` the person"),
    ):
        shown = paired(project, at, role)
        assert beneath(shown.splitlines(), entry) == ["", line] and "Estimate for the hull" not in shown
    shown = paired(project, "10000007+1", THEM)
    assert beneath(shown.splitlines(), "1. `10000007` the person") == [
        "",
        "The person pasted 1 text into it, not shown here, the one you named among them: `10000007+1` "
        "(84 characters); thread gives it in its place.",
    ]
    assert "Estimate for the hull" not in shown and "the one you named:" not in shown


ANOTHER = "A second estimate: three coats, and a week more."


def two_pasted() -> list[dict]:
    """The session asks for two estimates; the person's message has both pasted into it (60000002+1 and +2); the
    session answers."""
    person = (
        f'Two estimates came.\n\n<pasted_content id="aa01">\n{PASTED}\n</pasted_content id="aa01">\n\nAnd this one.'
        f'\n\n<pasted_content id="aa02">\n{ANOTHER}\n</pasted_content id="aa02">'
    )
    return [
        row("assistant", "60000001", 1, [{"type": "text", "text": "Send me both estimates."}]),
        row("user", "60000002", 2, person),
        row("assistant", "60000003", 3, [{"type": "text", "text": "The second is dearer."}]),
    ]


def test_the_pastes_are_named_by_id_and_length_and_no_text_of_them(tmp_path):
    other = ANOTHER
    crossings = made(tmp_path, two_pasted(), [])
    project = crossings.parent
    pastes = [
        {"id": "60000002+1", "name": "60000002+1", "length": len(PASTED), "is_asked": False, "labels": []},
        {"id": "60000002+2", "name": "60000002+2", "length": len(other), "is_asked": False, "labels": []},
    ]
    assert store.tied(crossings, "60000001", store.OWN)["answer"][0]["pastes"] == pastes  # in an answer
    assert store.tied(crossings, "60000002", store.HIS)["head"][0]["pastes"] == pastes  # and in a head
    sentence = (
        f"The person pasted 2 texts into it, not shown here: `60000002+1` ({len(PASTED)} characters) and "
        f"`60000002+2` ({len(other)} characters); thread gives each in its place."
    )
    for at, role in (("60000001", ME), ("60000002", THEM)):
        shown = served(project, id=at, role=role)[0]
        assert sentence in shown.splitlines() and "Estimate for the hull" not in shown and "three coats" not in shown
    # What the sentence says of `thread` holds: a paste's id gives it in its place, as pasted by the person.
    threaded = served_thread(project, "60000002+2")
    assert "`60000002+2` pasted by the person, 2026-11-11 09:02 UTC, the one you named:" in threaded
    assert "three coats" in threaded and threaded.index("2. `60000002+1`") < threaded.index("3. `60000002+2`")
    # A pair with no paste names none, and says nothing of pastes.
    bare = made(tmp_path / "none", ONE[:2], [])
    out = store.tied(bare, "10000001", store.HIS)
    assert [each["pastes"] for each in out["head"] + out["answer"]] == [[], []]
    assert "pasted" not in served(bare.parent, id="10000001", role=THEM)[0]


def served_thread(project: Path, said_id: str) -> str:
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        return said("thread", id=said_id)[0]


def test_a_struck_message_is_not_shown(tmp_path):
    crossings = made(tmp_path)
    project = str(crossings.parent)
    store.strike(crossings, "10000002")  # of the session's, in a turn of two
    assert ids(store.tied(crossings, "10000001", store.HIS)["answer"]) == ["10000003"]
    assert ids(store.tied(crossings, "10000003", store.OWN)["head"]) == ["10000003"]
    for at, role in (("10000001", THEM), ("10000003", ME), ("10000003", THEM)):
        assert "Yes: grey" not in paired(project, at, role)
    # The session's whole turn between two of the person's: what the index keeps out stands as no turn.
    store.strike(crossings, "10000006")
    out = store.tied(crossings, "10000005", store.HIS)
    assert ids(out["head"]) == ["10000004", "10000005", "10000007"] and ids(out["answer"]) == ["10000008"]
    assert "The tiller first" not in paired(project, "10000005", THEM)
    store.strike(crossings, "10000001")  # and the person's own, the session's first
    assert store.tied(crossings, "10000001", store.HIS) == {"asked": "10000001", "found": False}
    assert paired(project, "10000001", THEM) == "thread of `10000001`: no such message in the store.\n"
    out = store.tied(crossings, "10000003", store.OWN)  # the session's turn now opens its session
    assert out["before"] is None and ids(out["head"]) == ["10000003"]
    assert ids(out["answer"]) == ["10000004", "10000005", "10000007"]
    shown = paired(project, "10000003", ME)
    assert "Shall we paint the hull" not in shown and "Yes: grey" not in shown and "The tiller first" not in shown
    assert not store.tied(crossings, "10000003", store.HIS)["paired"]  # and answers no turn of the person's


def test_no_pair_crosses_into_another_session(tmp_path):
    crossings = made(tmp_path)
    project = str(crossings.parent)
    # What talk-two said between, in time, is neither in an answer nor a turn of talk-one's.
    out = store.tied(crossings, "10000003", store.OWN)
    assert ids(out["answer"]) == ["10000004", "10000005"] and out["before"] == "10000001"
    assert "20000002" not in ids(store.tied(crossings, "10000001", store.HIS)["answer"])
    # Talk-two's last turn ends with its session, though talk-one speaks on after it.
    out = store.tied(crossings, "20000003", store.OWN)
    assert out["voice"] == "session" and ids(out["head"]) == ["20000002", "20000003"]
    assert out["answer"] == [] and out["after"] is None and out["before"] == "20000001"
    shown = paired(project, "20000003", ME)
    assert "1000000" not in shown and "The person said nothing after it in that session." in shown.splitlines()
    for at in ("20000001", "20000003"):  # by the head, and by the answer: the pair of talk-two's own
        out = store.tied(crossings, at, store.HIS)
        assert out["before"] is None and ids(out["head"]) == ["20000001"], at
        assert ids(out["answer"]) == ["20000002", "20000003"] and out["after"] == "20000002", at


def test_the_doors_answer_gives_each_message_under_its_id_and_the_labels_by_key_alone(tmp_path):
    long = "The hull is long. " * 400  # past what a thread gives of the message it is asked of
    one = [ONE[0], row("assistant", "10000002", 2, [{"type": "text", "text": long}]), *ONE[2:]]
    crossings = made(tmp_path, one)
    sentence = "The hull is painted grey in two coats."
    first = store.mark(crossings, "work", "session", sentence, ["10000003"])["id"]
    second = store.mark(crossings, "work", "both", "The launch waits for the paint.", ["10000001", "20000002"])["id"]
    project = str(crossings.parent)
    code, shown = through("thread", "10000001", "--role", THEM, "--bare", "--cwd", project)
    assert code == 0
    lines = shown.splitlines()
    assert lines[:4] == [
        "thread of `10000001` with the role `pair:them`: the person's turn, 1 message, and the session's answer, "
        "2 messages, in the order they were said",
        "",
        "1. `10000001` the person, 2026-11-11 09:01 UTC, the one you named:",
        door.QUOTED + "Shall we paint the hull before the launch?",
    ]
    assert "2. `10000002` the session, 2026-11-11 09:02 UTC:" in lines
    cut = next(line for line in lines if line.startswith(door.QUOTED + "The hull is long."))
    assert cut.endswith(" […]") and len(cut) < len(door.QUOTED) + store.WHOLE + 5
    assert lines[-1] == f"Labels resting here: {first}, {second}."  # by key alone, on any message shown
    assert sentence not in shown and "The launch waits" not in shown
    assert str(tmp_path) not in shown and "crossings" not in shown and ".jsonl" not in shown  # no file, no folder
    assert "Labels resting here" not in paired(project, "10000005", THEM)
    twins = [row("user", "30000001", 1, "The first of two."), row("user", "30000001", 2, "The second of two.")]
    twins[1]["uuid"] = "30000001-1111-4000-8000-000000000000"
    shared = made(tmp_path / "shared", twins, [])
    by_whole = store.tied(shared, "30000001-1111", store.HIS)["head"]  # both are the person's, said in a row: one turn
    assert [(each["text"], each["is_asked"]) for each in by_whole] == [
        ("The first of two.", False),
        ("The second of two.", True),
    ]


def test_a_role_that_is_neither_is_refused_and_an_id_with_a_role_is_answered_as_a_thread_answers_it(tmp_path):
    """A role that is neither of the two is refused in one sentence that names both, by the door and by the server,
    and nothing is read or noted; an id that names no message, one two messages share, and none at all are answered
    with a role as `thread` answers them without one."""
    crossings = made(tmp_path)
    project = crossings.parent
    for role in ("pair", "pair:his", "pair:session", "PAIR:ME", " pair:me", ""):
        assert through("thread", "10000001", "--role", role, "--touch", "--cwd", str(project)) == (
            2,
            "thread takes one of two roles: pair:me or pair:them.\n",
        ), role
        assert served(project, id="10000001", role=role) == (door.UNROLED, True), role
    for role in (7, True, ["pair:me"], {"pair": "me"}):  # what no schema lets through, as a client may send it
        assert served(project, id="10000001", role=role) == (door.UNROLED, True), role
    assert not (crossings / "reached.jsonl").exists()  # nothing was read, nothing noted
    assert served(project, id="10000001", role=None)[0] == served_thread(project, "10000001")  # null is no role
    for role in (THEM, ME):
        assert paired(project, "0a0a0a0a", role) == through("thread", "0a0a0a0a", "--cwd", str(project))[1]
        assert paired(project, "0a0a0a0a", role) == "thread of `0a0a0a0a`: no such message in the store.\n"
        assert served(project, id="0a0a0a0a", role=role) == (
            "thread of `0a0a0a0a`: no such message in the store.",
            False,
        )
        for given in ({}, {"id": ""}, {"id": "   "}, {"id": 7}, {"id": ["10000001"]}, {"id": " ", "role": "bogus"}):
            assert served(project, **{"role": role, **given}) == ("thread needs an id.", True), given
        assert store.tied(crossings, "0a0a0a0a", door.ROLES[role]) == {"asked": "0a0a0a0a", "found": False}
    twins = [row("user", "30000001", 1, "The first of two."), row("user", "30000001", 2, "The second of two.")]
    twins[1]["uuid"] = "30000001-1111-4000-8000-000000000000"
    shared = made(tmp_path / "shared", twins, [])
    older, newer = "30000001-0", "30000001-1"  # each by its name: the shortest beginning of its whole id it alone has
    threaded = (
        f"thread of `30000001`: two messages are named `30000001`, `{older}` and `{newer}`; thread with one of them "
        "gives that one."
    )
    assert through("thread", "30000001", "--cwd", str(shared.parent))[1] == threaded + "\n"
    for role in (THEM, ME):
        assert store.tied(shared, "30000001", door.ROLES[role]) == {
            "asked": "30000001",
            "found": False,
            "twins": [older, newer],
        }
        assert paired(shared.parent, "30000001", role) == threaded + "\n"
        assert served(shared.parent, id="30000001", role=role) == (threaded, False)
    assert not (shared / "reached.jsonl").exists()  # nothing found, nothing noted


def test_an_id_that_is_empty_once_cleaned_names_no_message_with_a_role_or_without_one(tmp_path):
    """Guard: `thread` from the person's shell with no id, with an empty one, or with backticks alone, which the door
    takes off, read the empty id as the beginning of every whole id and gave the first message said, marked as the one
    named, with a role or without one; through the server, which refuses no id and a blank one, backticks alone did
    the same and noted it as reached. Each is answered now as an id that names no message, and nothing is noted."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    nothing = "thread of ``: no such message in the store."
    for given in ([], [""], ["``"]):
        for role in ([], ["--role", THEM], ["--role", ME]):
            assert through("thread", *given, *role, "--cwd", project, "--touch") == (0, nothing + "\n"), (given, role)
    for role in ({}, {"role": THEM}, {"role": ME}):
        assert served(crossings.parent, id="``", **role) == (nothing, False), role
    assert not (crossings / "reached.jsonl").exists()  # nothing found, nothing noted
    for each in ("", "  ", "``", "​"):
        assert store.thread(crossings, each) == {"asked": each, "found": False, "said": [], "labels": []}, each
        assert store.tied(crossings, each, store.HIS) == {"asked": each, "found": False}, each


def test_thread_without_a_role_reads_as_it_did_before_the_roles(tmp_path):
    """A pin: `thread` asked with no role, through the door and through the server, gives what it gave before roles
    were added, to the character; `--around` is taken as before, and the server asks the door as before."""
    crossings = made(tmp_path)
    project = crossings.parent
    key = store.mark(crossings, "work", "session", "The mast waits for the tiller.", ["10000005"])["id"]
    assert through("thread", "10000004", "--cwd", str(project)) == (
        0,
        "thread of `10000004`: 5 messages, in the order they were said\n\n"
        "1. `20000001` the person, 2026-11-11 09:04 UTC:\n    > A question asked in another session.\n\n"
        "2. `20000002` the session, 2026-11-11 09:05 UTC:\n    > An answer given in another session.\n\n"
        "3. `10000004` the person, 2026-11-11 09:06 UTC, the one you named:\n    > And the mast?\n\n"
        f"4. `10000005` the person, 2026-11-11 09:07 UTC (labels: {key}):\n    > Or is the tiller first?\n\n"
        "5. `10000006` the session, 2026-11-11 09:08 UTC:\n    > The tiller first, then the mast.\n\n"
        f"Labels resting here:\n- {key} (work, session): The mast waits for the tiller.\n",
    )
    assert through("thread", "10000004", "--around", "0", "--cwd", str(project)) == (
        0,
        "thread of `10000004`: 1 message, in the order they were said\n\n"
        "1. `10000004` the person, 2026-11-11 09:06 UTC, the one you named:\n    > And the mast?\n",
    )
    assert served_thread(project, "10000007+1") == (
        "thread of `10000007+1`: 4 messages, in the order they were said\n\n"
        "1. `20000003` the session, 2026-11-11 09:09 UTC:\n    > A later word of the other session.\n\n"
        "2. `10000007` the person, 2026-11-11 09:10 UTC:\n    > Here is what the yard sent back.\n    > \n"
        "    > [pasted: 84 characters]\n\n"
        "3. `10000007+1` pasted by the person, 2026-11-11 09:10 UTC, the one you named:\n"
        "    > Estimate for the hull: two coats of grey.\n    > \n    > | a | table |\n    > \n"
        "    > Ready by the end of March.\n\n"
        "4. `10000008` the session, 2026-11-11 09:11 UTC:\n    > The estimate is fair for two coats."
    )
    assert serve.asked("thread", {"id": " -x ", "around": 9}) == ["thread", "--around", "9", "--touch", "--", "-x"]
    assert serve.asked("thread", {"id": "x", "around": 99}) == ["thread", "--around", "50", "--touch", "--", "x"]
    assert serve.asked("thread", {"id": ""}) == "thread needs an id."


# --- the labels line: lines left at the door are counted, not listed -------------------------------------------


def left_at_the_door(crossings: Path, anchors: list[str], times: int) -> list[str]:
    """Lines left at the door one after another, each resting on the same messages, as a session leaves them: their
    keys, in the order written."""
    return [
        store.mark(crossings, "next", "session", f"Where the painting stands, line {n}.", anchors)["id"]
        for n in range(1, times + 1)
    ]


def named_in(shown: str, key: str) -> bool:
    return re.search(rf"\b{re.escape(key)}\b", shown) is not None


def test_two_lines_or_more_left_at_the_door_under_a_pair_are_counted_and_the_newest_named_by_its_key(tmp_path):
    """A work label is listed by key, as a label of any kind but `next` is. Three lines left at the door, which rest on
    many of the same messages one after another, are not listed: one sentence gives their count and the newest by its
    key, the last the store wrote, and neither older one is named. So whichever voice heads the pair."""
    crossings = made(tmp_path)
    project = crossings.parent
    older = left_at_the_door(crossings, ["10000001", "10000002"], 2)
    work = store.mark(crossings, "work", "session", "The hull is painted grey.", ["10000003"])["id"]
    newest = left_at_the_door(crossings, ["10000001", "10000003"], 1)[0]
    line = f"Labels resting here: {work}. 3 lines left at the door rest here too, the newest of them {newest}."
    for at, role in (("10000001", THEM), ("10000003", ME)):  # the person's turn heads the one, the session's the other
        shown = served(project, id=at, role=role)[0]
        assert shown == paired(project, at, role, "--bare").strip(), at
        assert shown.splitlines()[-1] == line, at
        assert not any(named_in(shown, key) for key in older), at
    for at, voice in (("10000001", "his"), ("10000003", "session")):
        out = store.tied(crossings, at, voice)
        assert out["voice"] == voice and out["labels"] == [*older, work, newest] and out["left"] == [*older, newest]


def test_a_pair_on_which_only_lines_left_at_the_door_rest_gives_their_count_and_the_newest_alone(tmp_path):
    """With no label of another kind, the count and the newest stand alone where the labels line stands. The newest
    is the last written, in the store's own order, though its key sorts before older ones' as text."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    keys = left_at_the_door(crossings, ["10000003", "10000004"], 11)
    assert sorted(keys)[-1] != keys[-1]  # as text, an older key would pass for the newest
    for at, role in (
        ("10000003", ME),
        ("10000001", THEM),
    ):  # the session's turn, and the person's, answered by 10000003
        shown = paired(project, at, role)
        assert shown.splitlines()[-1] == f"11 lines left at the door rest here, the newest of them {keys[-1]}.", at
        assert "Labels resting here" not in shown and not any(named_in(shown, key) for key in keys[:-1]), at
    out = store.tied(crossings, "10000003", store.OWN)
    assert out["labels"] == keys and out["left"] == keys


def test_one_line_left_at_the_door_under_a_pair_is_listed_by_key_as_today_and_a_second_makes_it_a_count(tmp_path):
    """One line left at the door is a key among the others, in the order written, or the only one; a second makes the
    two a count."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    work = store.mark(crossings, "work", "session", "The hull is painted grey.", ["10000002"])["id"]
    line = left_at_the_door(crossings, ["10000001"], 1)[0]
    assert paired(project, "10000001", THEM).splitlines()[-1] == f"Labels resting here: {work}, {line}."
    alone = made(tmp_path / "alone")
    only = left_at_the_door(alone, ["10000002"], 1)[0]
    assert paired(alone.parent, "10000003", ME).splitlines()[-1] == f"Labels resting here: {only}."
    newer = left_at_the_door(crossings, ["10000002"], 1)[0]
    assert paired(project, "10000001", THEM).splitlines()[-1] == (
        f"Labels resting here: {work}. 2 lines left at the door rest here too, the newest of them {newer}."
    )
    out = store.tied(crossings, "10000001", store.HIS)
    assert out["labels"] == [work, line, newer] and out["left"] == [line, newer]
    assert store.tied(alone, "10000003", store.OWN)["left"] == [only]


# --- what was pasted into a pair: the labels resting on it, on a line of its own ---------------------------------

PASTE = "10000007+1"  # pasted into 10000007, the person's message, which heads its pair and answers 10000006's
ON_PASTES = "Resting on what was pasted into this pair: "


def on_the_pastes(shown: str) -> list[str]:
    """The lines of a pair's answer that speak of the labels resting on what was pasted into it."""
    return [line for line in shown.splitlines() if "pasted into this pair" in line]


def test_a_label_on_a_paste_alone_is_named_on_a_line_of_its_own_with_the_pastes_id_and_not_among_the_pairs(tmp_path):
    """A label that rests on a text the person pasted, and on nothing else, is named by its key on a line of its own,
    with the paste's id, by the id of the message it was pasted into and by the paste's own id alike. It is not among
    the labels resting on the pair's messages, and no word of the paste or of the label is shown."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    sentence = "The yard's estimate is for grey."
    key = store.mark(crossings, "work", "session", sentence, [PASTE])["id"]
    line = f"{ON_PASTES}{key} on `{PASTE}`."
    for at in ("10000007", PASTE):
        shown = paired(project, at, THEM)
        assert shown.splitlines()[-3:] == [
            "The pair before this one begins at `10000006`, and the pair after it at `10000008`; thread with the role "
            "`pair:me` gives each.",
            "",
            line,
        ], at
        assert on_the_pastes(shown) == [line] and "Labels resting here" not in shown, at
        assert sentence not in shown and "Estimate for the hull" not in shown, at
    for at in ("10000007", PASTE):
        out = store.tied(crossings, at, store.HIS)
        assert out["labels"] == [] and out["left"] == [] and out["pasted_left"] == [], at
        assert [each["labels"] for each in out["head"] + out["answer"]] == [[], []], at
        assert [each["labels"] for each in out["head"][0]["pastes"]] == [[key]], at


def test_a_label_on_a_paste_and_on_a_message_of_the_pair_stands_in_both_lines(tmp_path):
    """Both are true: it rests on a message of the pair, and on what was pasted into it. A label on a message alone
    stands in the labels line alone."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    both = store.mark(crossings, "work", "session", "The estimate came with the message.", ["10000007", PASTE])["id"]
    own = store.mark(crossings, "work", "session", "The answer finds it fair.", ["10000008"])["id"]
    for at in ("10000007", PASTE, "10000008"):
        assert paired(project, at, THEM).splitlines()[-2:] == [
            f"Labels resting here: {both}, {own}.",
            f"{ON_PASTES}{both} on `{PASTE}`.",
        ], at
    out = store.tied(crossings, "10000007", store.HIS)
    assert out["labels"] == [both, own] and out["head"][0]["labels"] == [both] and out["answer"][0]["labels"] == [own]
    assert out["head"][0]["pastes"][0]["labels"] == [both]


def test_a_pair_headed_by_the_session_whose_answer_holds_the_message_pasted_into_says_the_same_line(tmp_path):
    """The session's turn, answered by the person's message the text was pasted into: the line speaks of the whole
    pair, whichever voice heads it, in the same words."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    key = store.mark(crossings, "work", "session", "The estimate is in.", [PASTE])["id"]
    line = f"{ON_PASTES}{key} on `{PASTE}`."
    for at in ("10000006", "10000007", PASTE):
        shown = paired(project, at, ME)
        assert shown.splitlines()[-3:] == [
            "The pair before this one begins at `10000004`, and the pair after it at `10000007`; thread with the role "
            "`pair:them` gives each.",
            "",
            line,
        ], at
        assert on_the_pastes(shown) == [line] and "Labels resting here" not in shown, at
    out = store.tied(crossings, "10000006", store.OWN)
    assert out["voice"] == "session" and ids(out["answer"]) == ["10000007"] and out["labels"] == []
    assert out["answer"][0]["pastes"][0]["labels"] == [key]


def test_a_served_pair_names_the_labels_on_what_was_pasted_into_it_as_the_door_does(tmp_path):
    crossings = made(tmp_path)
    project = crossings.parent
    key = store.mark(crossings, "work", "session", "The estimate is in.", [PASTE])["id"]
    # by the paste's id, in the person's turn and in the session's answered by it; and the session's own turn
    for at, role in ((PASTE, THEM), (PASTE, ME), ("10000007", THEM), ("10000006", ME)):
        text, failed = served(project, id=at, role=role)
        assert not failed and text == paired(project, at, role, "--bare").strip(), at
        assert text.splitlines()[-1] == f"{ON_PASTES}{key} on `{PASTE}`.", at
        for place in (str(tmp_path), "crossings", ".jsonl"):
            assert place not in text, (at, place)


def test_two_lines_or_more_left_at_the_door_on_what_was_pasted_are_counted_there_as_under_the_pair(tmp_path):
    """The rule of the labels line holds on the line of the pastes: one line left at the door is a key among the
    others; two or more are counted, with the newest by its key, the last the store wrote; where only they rest there,
    the count stands alone. The labels line counts those on the pair's own messages alone, and a pair whose messages
    hold none of them has no labels line."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    first = left_at_the_door(crossings, [PASTE], 1)[0]
    work = store.mark(crossings, "work", "session", "The estimate is for grey.", [PASTE])["id"]
    assert paired(project, "10000007", THEM).splitlines()[-1] == f"{ON_PASTES}{first}, {work} on `{PASTE}`."
    newer = left_at_the_door(crossings, [PASTE, "10000008"], 2)
    line = f"{ON_PASTES}{work} on `{PASTE}`. 3 lines left at the door rest there too, the newest of them {newer[-1]}."
    assert paired(project, "10000007", THEM).splitlines()[-2:] == [
        f"2 lines left at the door rest here, the newest of them {newer[-1]}.",
        line,
    ]
    shown = paired(project, "10000006", ME)  # no line rests on 10000006 or 10000007 themselves
    assert shown.splitlines()[-1] == line and "rest here" not in shown and not named_in(shown, first)
    alone = made(tmp_path / "alone")
    keys = left_at_the_door(alone, [PASTE], 11)
    assert sorted(keys)[-1] != keys[-1]  # as text, an older key would pass for the newest
    for at, role in (("10000007", THEM), (PASTE, THEM), ("10000006", ME), (PASTE, ME)):
        shown = paired(alone.parent, at, role)
        assert shown.splitlines()[-1] == (
            f"11 lines left at the door rest on what was pasted into this pair, the newest of them {keys[-1]}."
        ), at
        assert "Resting on what" not in shown and not any(named_in(shown, key) for key in keys[:-1]), at
    out = store.tied(crossings, "10000007", store.HIS)
    assert out["labels"] == newer and out["left"] == newer and out["pasted_left"] == [first, *newer]
    assert out["head"][0]["pastes"][0]["labels"] == [first, work, *newer]
    by_paste = store.tied(alone, PASTE, store.HIS)
    assert by_paste["pasted_left"] == keys and by_paste["left"] == []


def test_labels_on_two_texts_pasted_into_one_message_are_named_by_each_paste_and_counted_across_both(tmp_path):
    """Each paste with the keys resting on it, in the order pasted and each in the order written; a label on both
    stands under both. Lines left at the door are counted across the pastes, the newest the last written whichever
    paste it rests on, and a paste on which only counted lines rest is not named."""
    crossings = made(tmp_path, two_pasted(), [])
    project = str(crossings.parent)
    one = store.mark(crossings, "work", "session", "The first estimate is for grey.", ["60000002+1"])["id"]
    two = store.mark(crossings, "work", "session", "The second is for three coats.", ["60000002+2"])["id"]
    both = store.mark(crossings, "work", "session", "Both came from the yard.", ["60000002+2", "60000002+1"])["id"]
    listed_ = f"{ON_PASTES}{one}, {both} on `60000002+1`; {two}, {both} on `60000002+2`."
    # the session's turn it answers, its own, and by a paste's id in each
    for at, role in (("60000001", ME), ("60000002", THEM), ("60000002+2", THEM), ("60000002+2", ME)):
        assert paired(project, at, role).splitlines()[-1] == listed_, at
    older = left_at_the_door(crossings, ["60000002+2"], 1)[0]
    newest = left_at_the_door(crossings, ["60000002+1"], 1)[0]  # on the paste before, written after
    assert paired(project, "60000002", THEM).splitlines()[-1] == (
        f"{listed_} 2 lines left at the door rest there too, the newest of them {newest}."
    )
    out = store.tied(crossings, "60000002", store.HIS)
    assert [each["labels"] for each in out["head"][0]["pastes"]] == [[one, both, newest], [two, both, older]]
    assert out["pasted_left"] == [older, newest] and out["labels"] == [] and out["left"] == []
    only = made(tmp_path / "only", two_pasted(), [])  # the second paste holds counted lines alone
    work = store.mark(only, "work", "session", "The first estimate is for grey.", ["60000002+1"])["id"]
    lines = left_at_the_door(only, ["60000002+2"], 2)
    assert paired(only.parent, "60000002", THEM).splitlines()[-1] == (
        f"{ON_PASTES}{work} on `60000002+1`. 2 lines left at the door rest there too, the newest of them {lines[-1]}."
    )


def test_the_line_of_the_pastes_speaks_of_the_whole_pair_also_on_a_page_that_does_not_show_where_it_was_pasted(
    tmp_path,
):
    """Like the labels line: a pair too long to show whole is a page, and the line is said under it all the same."""
    rows = [
        *(
            row("assistant", f"7000000{n}", n, [{"type": "text", "text": sized(4000, word)}])
            for n, word in ((1, "Alpha"), (2, "Bravo"), (3, "Charlie"))
        ),
        row("user", "70000004", 4, WITH_PASTE),
    ]
    crossings = made(tmp_path, rows, [])
    project = crossings.parent
    key = store.mark(crossings, "work", "session", "The estimate came last.", ["70000004+1"])["id"]
    line = f"{ON_PASTES}{key} on `70000004+1`."
    shown = served(project, id="70000001", role=ME)[0]
    assert listed(shown) == ["70000001", "70000002", "70000003"]  # the message pasted into is not on this page
    assert (
        "1 message of this pair comes after this page; thread of `70000004` with the role `pair:me` goes on from there."
    ) in shown
    assert shown.splitlines()[-1] == line and "The person pasted" not in shown
    assert served(project, id="70000004+1", role=THEM)[0].splitlines()[-1] == line  # and the pair the message heads
    pasted = served(project, id="70000004+1", role=ME)[0]  # and this pair, by the paste's id: a page from its message
    assert listed(pasted) == ["70000004"] and pasted.splitlines()[-1] == line


def test_a_pair_with_a_paste_and_no_label_on_it_reads_to_the_character(tmp_path):
    """A pin of a whole answer: where no label rests on what was pasted, a pair reads so, with no label at all and with
    labels on its messages, by a message's id and by the paste's."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    pasted = [
        "2. `10000007` the person, 2026-11-11 09:10 UTC:",
        door.QUOTED + "Here is what the yard sent back.",
        door.QUOTED,
        door.QUOTED + "[pasted: 84 characters]",
        "",
        "The person pasted 1 text into it, not shown here: `10000007+1` (84 characters); thread gives it in its place.",
        "",
    ]
    assert paired(project, "10000006", ME) == "\n".join(
        [
            "thread of `10000006` with the role `pair:me`: the session's turn, 1 message, and the person's answer, "
            "1 message, in the order they were said",
            "",
            "1. `10000006` the session, 2026-11-11 09:08 UTC, the one you named:",
            door.QUOTED + "The tiller first, then the mast.",
            "",
            *pasted,
            "The pair before this one begins at `10000004`, and the pair after it at `10000007`; thread with the role "
            "`pair:them` gives each.",
            "",
        ]
    )
    work = store.mark(crossings, "work", "session", "The yard sent an estimate.", ["10000007"])["id"]
    line = left_at_the_door(crossings, ["10000008"], 1)[0]
    for at, entry, among in (
        ("10000007", "1. `10000007` the person, 2026-11-11 09:10 UTC, the one you named:", ""),
        (PASTE, "1. `10000007` the person, 2026-11-11 09:10 UTC:", ", the one you named among them"),
    ):
        assert paired(project, at, THEM) == "\n".join(
            [
                f"thread of `{at}` with the role `pair:them`: the person's turn, 1 message, and the session's answer, "
                "1 message, in the order they were said",
                "",
                entry,
                *pasted[1:4],
                "",
                f"The person pasted 1 text into it, not shown here{among}: `10000007+1` (84 characters); thread gives "
                "it in its place.",
                "",
                "2. `10000008` the session, 2026-11-11 09:11 UTC:",
                door.QUOTED + "The estimate is fair for two coats.",
                "",
                "The pair before this one begins at `10000006`, and the pair after it at `10000008`; thread with the "
                "role `pair:me` gives each.",
                "",
                f"Labels resting here: {work}, {line}.",
                "",
            ]
        ), at


def test_a_pair_pulled_through_the_door_is_logged_as_a_thread_is_and_counted_once(tmp_path):
    """The id named, and nothing more, under the verb asked; a pair that is not there, or an id that names nothing,
    notes nothing."""
    crossings = made(tmp_path)
    project = str(crossings.parent)
    log = crossings / "reached.jsonl"
    paired(project, "10000003", ME)  # asked without --touch: no pull is noted
    assert not log.exists()
    paired(project, "10000003", THEM, "--touch")
    paired(project, "0a0a0a0a", ME, "--touch")  # nothing found, nothing noted
    paired(project, "10000001", ME, "--touch")  # no such pair, nothing shown: nothing noted
    paired(project, "10000007+1", ME, "--touch")
    pulls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    assert [(each["verb"], each["ids"]) for each in pulls] == [("thread", ["10000003"]), ("thread", ["10000007+1"])]
    # The released readers of the log read a pull by its ids, whatever its verb; a paste's is not the person's words.
    assert sample.pulled(crossings) == {"10000003": 1}


# --- the door's server ------------------------------------------------------------------------------------------


def served(project: Path, **given) -> tuple[str, bool]:
    """A call of the server's `thread`, as a session a person sits in makes it, for this project: with a `role`, a
    pair."""
    with set_to(CLAUDE_PROJECT_DIR=str(project)):
        return said("thread", **given)


DESCRIBED = (
    "A message in its place, by its id: what stood before and after it, and the labels resting there. With a role, its "
    "place is a pair: a turn with the other voice's answer beneath it."
)
ROLE = (
    "`pair:them`: the pair headed by the person's turn; `pair:me`: by the session's. The one the message heads, or the "
    "one it answers."
)


def unknown_tool(name: str) -> dict:
    return serve.handle(
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": name, "arguments": {"id": "10000001"}}}
    )


def test_the_server_lists_eight_tools_none_named_pair_and_a_call_of_pair_is_answered_as_any_unknown_tool(tmp_path):
    listed_ = serve.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})["result"]["tools"]
    names = [each["name"] for each in listed_]
    assert names == ["look", "labels", "find", "thread", "mark", "leave", "status", "crossing"] == serve.NAMES
    assert len(names) == 8 and "pair" not in names
    crossings = made(tmp_path)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        refused, strike = unknown_tool("pair"), unknown_tool("strike")
    assert (
        refused
        == strike
        == {
            "jsonrpc": "2.0",
            "id": 3,
            "error": {
                "code": -32602,
                "message": "The door has these handles: look, labels, find, thread, mark, leave, status, crossing.",
            },
        }
    )
    assert not (crossings / "reached.jsonl").exists()
    thread = next(each for each in listed_ if each["name"] == "thread")
    assert thread["description"] == DESCRIBED and thread["inputSchema"]["required"] == ["id"]
    assert list(thread["inputSchema"]["properties"]) == ["id", "around", "role", "home"]
    assert thread["inputSchema"]["properties"]["role"] == {"type": "string", "enum": [ME, THEM], "description": ROLE}
    assert thread["_meta"] == {"anthropic/alwaysLoad": True}
    for root in (None, str(ROOT)):  # what a session is told as the server connects, with the plugin's hooks or alone
        with set_to(CLAUDE_PLUGIN_ROOT=root):
            told = serve.instructions()
        assert "`labels`, `find` and `thread` go on from there;" in told and "pair" not in told


def test_the_listing_is_pinned_at_its_size_with_the_role_on_thread(tmp_path):
    """The tools a session is shown, measured with `thread`'s role and without `pair`: smaller than with `pair`
    (5,846), and under the cap the tests hold. The person's side spelled `their` and `pair:them` took six characters
    more than `his` and `pair:him` (5,655)."""
    assert len(json.dumps(serve.TOOLS)) == 5661 < 5846 < 5900


def test_a_served_pair_answers_with_the_pair_and_names_no_file_or_folder(tmp_path):
    crossings = made(tmp_path)
    project = crossings.parent
    text, failed = served(project, id="10000003", role=ME, around=9)  # with a role, `around` does nothing
    assert not failed and text == paired(project, "10000003", ME, "--bare").strip()
    assert text == served(project, id="10000003", role=ME)[0]
    assert text.startswith(
        "thread of `10000003` with the role `pair:me`: the session's turn, 2 messages, and the person's answer, 2 "
        "messages"
    )
    assert "1. `10000002` the session, 2026-11-11 09:02 UTC:" in text
    assert "2. `10000003` the session, 2026-11-11 09:03 UTC, the one you named:" in text
    for place in (str(tmp_path), str(tmp_path.resolve()), "/Users/", "/private/", "crossings", ".py", ".jsonl"):
        assert place not in text, place
    assert served(project, id=" 10000007+1 ", role=THEM)[0].startswith("thread of `10000007+1` with the role")
    # Asked of the door as a thread is: the id after the `--`, whatever it begins with, and the pull noted.
    assert serve.asked("thread", {"id": " -x ", "around": 9, "role": ME}) == [
        "thread",
        "--role=pair:me",
        "--touch",
        "--",
        "-x",
    ]


def test_a_pair_pulled_through_the_server_is_noted_once_under_its_verb(tmp_path):
    crossings = made(tmp_path)
    project = crossings.parent
    served(project, id="10000003", role=ME)
    served(project, id="0a0a0a0a", role=ME)  # nothing found, nothing noted
    served(project, id="30000001", role=THEM)  # nothing found either
    served(project, id="10000001", role=ME)  # no such pair: nothing noted
    served(project, role=ME)  # refused, nothing read
    served(project, id="10000004", role="pair")  # refused, nothing read
    pulls = [json.loads(line) for line in (crossings / "reached.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [(each["verb"], each["ids"]) for each in pulls] == [("thread", ["10000003"])]
    assert sample.pulled(crossings) == {"10000003": 1}


# --- a span off the record ------------------------------------------------------------------------------------


@in_person
def test_a_span_off_the_record_inside_a_pair_is_said_where_it_stands(tmp_path):
    """What the person said while Crossings was off is not kept, so the session's messages on either side of it are
    one turn, and a pair runs on across it: the span is said in its place, in the words a thread says it in, and
    nothing of what was said."""
    project, folder, path = on_with_a_transcript(tmp_path)  # 10000001, the person's
    says(path, "10000002", "The chain is galvanised.", kind="assistant")
    switch(project, "off")
    says(path, "20000001", "Said while it was off.")
    says(path, "20000002", "Answered while it was off.", kind="assistant")
    switch(project, "on")
    says(path, "30000001", "And it wants a swivel.", kind="assistant")
    asked(project, path)
    out = store.tied(folder, "10000001", store.HIS)
    assert ids(out["answer"]) == ["10000002", "30000001"]
    assert [each["before"] for each in out["gaps"]] == [out["answer"][1]["seq"]]
    assert ids(store.tied(folder, "30000001", store.OWN)["head"]) == [
        "10000002",
        "30000001",
    ]  # one turn of the session's
    start, end = spans_file(folder)[0].split()
    first, last = (store.off.moment(t).strftime("%Y-%m-%d %H:%M:%S UTC") for t in (start, end))
    gap = f"(Crossings was off from {first} to {last}: nothing said then was kept.)"
    assert gap == door.gap(out["gaps"][0]).strip()
    for asked_id, role, number in (
        ("10000001", THEM, 2),
        ("10000002", THEM, 2),
        ("10000002", ME, 1),
        ("30000001", ME, 1),
    ):
        shown = served(project, id=asked_id, role=role)[0]
        assert shown.count(gap) == 1 and "while it was off" not in shown
        assert shown.index(f"{number}. `10000002`") < shown.index(gap) < shown.index(f"{number + 1}. `30000001`")
    # A pair with no span among its messages says none.
    says(path, "40000001", "And the shackle?")
    says(path, "40000002", "A new one.", kind="assistant")
    asked(project, path)
    assert store.tied(folder, "40000001", store.HIS)["gaps"] == []
    assert "Crossings was off" not in served(project, id="40000001", role=THEM)[0]


# --- the ceiling, and a pair too long to show whole --------------------------------------------------------------


def sized(n: int, word: str) -> str:
    """A text of exactly `n` characters, of one word said again and again, ending in a full stop."""
    return (f"{word} " * n)[: n - 1] + "."


def fitted(middle: int) -> list[dict]:
    """The person's turn of two messages (40000001, 40000002) and the session's answer of three (40000003 of 5,000
    characters, 40000004 of `middle`, 40000005 of 3,000), each of a word of its own; then the person's next message."""
    return [
        row("user", "40000001", 1, "Shall we sail at dawn?"),
        row("user", "40000002", 2, "Or at noon?"),
        *(
            row("assistant", f"4000000{n}", n, [{"type": "text", "text": sized(size, word)}])
            for n, size, word in ((3, 5000, "Alpha"), (4, middle, "Bravo"), (5, 3000, "Charlie"))
        ),
        row("user", "40000009", 30, "Then we sail."),
    ]


def test_a_pair_that_fits_is_whole_whichever_id_named_it(tmp_path):
    """Every message of it, in order, each under its id, as with no ceiling at all, by either id of its head; and one
    character more is no longer whole: named by its first, a page from the beginning."""
    rest = store.PAIRED - len("Shall we sail at dawn?") - len("Or at noon?") - 8000
    crossings = made(tmp_path, fitted(rest), [])
    project = crossings.parent
    seen = []
    for asked_id in ("40000001", "40000002"):
        shown = served(project, id=asked_id, role=THEM)[0]
        was = store.PAIRED
        store.PAIRED = 10**9
        try:
            unbound = served(project, id=asked_id, role=THEM)[0]
        finally:
            store.PAIRED = was
        assert shown == unbound, asked_id
        assert listed(shown) == ["40000001", "40000002", "40000003", "40000004", "40000005"]
        assert sum(map(len, quoted(shown))) == store.PAIRED  # at the ceiling, to the character
        assert all(word in shown for word in ("Alpha", "Bravo", "Charlie"))
        assert "this page" not in shown and "before the one you named" not in shown
        seen.append(unmarked(shown))
    assert seen[0] == seen[1]
    over = made(tmp_path / "over", fitted(rest + 1), [])
    past = served(over.parent, id="40000001", role=THEM)[0]
    assert listed(past) == ["40000001", "40000002", "40000003", "40000004"] and "Charlie" not in past
    assert "before the one you named" not in past  # named by its first, the page starts at the beginning
    assert (
        "1 message of this pair comes after this page; thread of `40000005` with the role `pair:them` goes on from there."
    ) in past.splitlines()


def in_turns(*turns: list[int]) -> list[dict]:
    """A session of turns, the person's first and then each voice in its turn: one message of each size, numbered on
    from 50000001, each of a word of its own that carries its number (Word01, Word02, ...)."""
    rows, n = [], 1
    for at, sizes in enumerate(turns):
        kind = "user" if at % 2 == 0 else "assistant"
        for size in sizes:
            text = sized(size, f"Word{n:02d}")
            rows.append(row(kind, f"500000{n:02d}", n, text if kind == "user" else [{"type": "text", "text": text}]))
            n += 1
    return rows


def test_a_pair_that_does_not_fit_starts_at_the_message_named_and_says_what_stands_before_and_after(tmp_path):
    """The named message and those after it while their texts fit; one sentence for those of the pair before it, with
    the pair's first; one for those after the page, with the id and the role the next page starts at and the pair's
    last. Each keeps its number in the whole pair, and the closing line and the labels line are as for any pair."""
    crossings = made(tmp_path, in_turns([22], [4000] * 6, [13]), [])  # the session's turn: 50000002 to 50000007
    key = store.mark(crossings, "work", "session", "The second answer is the one to keep.", ["50000002"])["id"]
    project = crossings.parent
    shown, failed = served(project, id="50000004", role=ME)
    assert not failed and shown == paired(project, "50000004", ME, "--bare").strip()
    lines = shown.splitlines()
    assert lines[:5] == [
        "thread of `50000004` with the role `pair:me`: the session's turn, 6 messages, and the person's answer, "
        "1 message, in the order they were said",
        "",
        "2 messages of this pair stand before the one you named and are not shown here; the pair begins at `50000002`.",
        "",
        "3. `50000004` the session, 2026-11-11 09:04 UTC, the one you named:",
    ]
    assert entries(shown) == [
        "3. `50000004` the session, 2026-11-11 09:04 UTC, the one you named:",
        "4. `50000005` the session, 2026-11-11 09:05 UTC:",
        "5. `50000006` the session, 2026-11-11 09:06 UTC:",
    ]
    for word in ("Word01", "Word02", "Word03", "Word07", "Word08"):
        assert word not in shown, word
    assert sum(map(len, quoted(shown))) <= store.PAIRED < sum(map(len, quoted(shown))) + 4000  # the next did not fit
    assert lines[-5:] == [
        "2 messages of this pair come after this page, the last of them `50000008`; thread of `50000007` with the "
        "role `pair:me` goes on from there.",
        "",
        "The pair before this one begins at `50000001`, and the pair after it at `50000008`; thread with the role "
        "`pair:them` gives each.",
        "",
        f"Labels resting here: {key}.",
    ]
    # Named by its first, the page starts at the beginning; and a page that reaches the end says nothing of more.
    begun = served(project, id="50000002", role=ME)[0]
    assert listed(begun) == ["50000002", "50000003", "50000004"] and "before the one you named" not in begun
    ended = served(project, id="50000006", role=ME)[0]
    assert listed(ended) == ["50000006", "50000007", "50000008"] and "this page" not in ended
    assert "4 messages of this pair stand before the one you named" in ended
    answered = served(project, id="50000008", role=ME)[0]  # by the answer's id, a page of the same pair from there
    assert listed(answered) == ["50000008"] and "6 messages of this pair stand before the one you named" in answered
    # One before alone, and one after alone, are said so.
    one = made(tmp_path / "one", in_turns([22], [4000] * 4, [13]), [])
    lone = served(one.parent, id="50000003", role=ME)[0].splitlines()
    assert (
        "1 message of this pair stands before the one you named and is not shown here; the pair begins at `50000002`."
    ) in lone
    assert (
        "1 message of this pair comes after this page; thread of `50000006` with the role `pair:me` goes on from there."
    ) in lone


def walked(crossings: Path, at: str, role: str) -> tuple[list[str], int]:
    """A pair walked page by page through the server, from the id and the role given, on by the id and the role each
    page says the next starts at: the ids of the messages shown, in order, and how many pages. Each page starts at the
    one named, and numbers each message by its place in the pair."""
    pair = store.tied(crossings, at, door.ROLES[role])
    whole = ids(pair["head"] + pair["answer"])
    shown_ids, pages = [], 0
    while at is not None and pages <= len(whole):
        shown, failed = served(crossings.parent, id=at, role=role)
        assert not failed and shown.startswith(f"thread of `{at}` with the role `{role}`: ")
        pages += 1
        page = [ENTRY.match(line).groups() for line in entries(shown)]
        assert page[0][1] == at  # it starts at the one named
        assert all(int(number) == whole.index(said_id) + 1 for number, said_id in page)  # its number in the pair
        assert sum(map(len, quoted(shown))) <= store.PAIRED
        shown_ids += [said_id for _, said_id in page]
        further = FURTHER.search(shown)
        assert further is None or further.group(2) == role  # the same role, so the same pair
        at = further.group(1) if further else None
    return shown_ids, pages


def test_walking_a_pair_too_long_by_the_ids_and_the_role_it_gives_shows_each_message_exactly_once(tmp_path):
    """From the pair's first, on by the id and the role each page says the next starts at: every message of the pair
    once, in order, and the walk ends. A page that stops inside the answer gives an id of the answer, and with the same
    role it is a page of the same pair. So on the case where an id of the answer would head the next pair, which fits:
    walked by the role, its messages are not shown again."""
    for n, (turns, start, role, whole, pages) in enumerate(
        (
            # the case of step 1d: the second page stopped inside the answer, whose own pair fits
            (([22], [4000] * 4, [4000, 4000, 1000], [13]), "50000002", ME, range(2, 9), 3),
            (([22], [7000, 4000, 4000, 4000], [4000] * 4, [13]), "50000002", ME, range(2, 10), 3),
            (([4000] * 3, [4000, 4000, 1000], [13]), "50000001", THEM, range(1, 7), 2),  # a pair headed by the person
        )
    ):
        crossings = made(tmp_path / f"walk-{n}", in_turns(*turns), [])
        shown, counted = walked(crossings, start, role)
        assert shown == [f"500000{n:02d}" for n in whole] and counted == pages, (turns, shown)  # each once, in order
    first = served(crossings.parent, id="50000001", role=THEM)[0]
    assert "after this page" in first and "before the one you named" not in first


@in_person
def test_a_span_off_the_record_is_said_on_a_page_where_it_stands_and_not_otherwise(tmp_path):
    """A span is said before a message the page shows, and after the last of the pair where the page reaches the
    end; a page that shows neither says none."""
    project, folder, path = on_with_a_transcript(tmp_path)  # 10000001, the person's
    for uid, word in (("10000002", "Alpha"), ("10000003", "Bravo"), ("10000004", "Charlie")):
        says(path, uid, sized(5000, word), kind="assistant")
    switch(project, "off")
    says(path, "20000001", "Said while it was off.")
    switch(project, "on")
    says(path, "30000001", sized(4000, "Delta"), kind="assistant")
    says(path, "30000002", sized(4000, "Keel"), kind="assistant")
    switch(project, "off")  # and once more after the last of the pair, with nothing said since
    switch(project, "on")
    asked(project, path)
    out = store.tied(folder, "10000004", store.OWN)  # the session's turn, across the first span
    assert out["voice"] == "session" and out["answer"] == []
    assert ids(out["head"]) == ["10000002", "10000003", "10000004", "30000001", "30000002"]
    seqs = {each["id"]: each["seq"] for each in out["head"]}
    assert [each["before"] for each in out["gaps"]] == [seqs["30000001"], None]
    spans = [door.gap(each).strip() for each in out["gaps"]]

    def said_off(shown: str) -> list[str]:
        return [line for line in shown.splitlines() if line.startswith("(Crossings was off")]

    begun = served(project, id="10000002", role=ME)[0]  # 1 and 2: no span stands among them, and the end is not reached
    assert listed(begun) == ["10000002", "10000003"] and said_off(begun) == [] and "while it was off" not in begun
    middle = served(project, id="10000004", role=ME)[0]  # 3 and 4, with the first span between them
    lines = middle.splitlines()
    assert listed(middle) == ["10000004", "30000001"] and said_off(middle) == spans[:1]
    assert lines.index(entries(middle)[0]) < lines.index(spans[0]) < lines.index(entries(middle)[1])
    ended = served(project, id="30000002", role=ME)[0]  # 5, to the end: the span after the last of the pair
    lines = ended.splitlines()
    assert listed(ended) == ["30000002"] and said_off(ended) == spans[1:] and "while it was off" not in ended
    assert lines.index(entries(ended)[0]) < lines.index(spans[1])


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            # In the tests' own data folder, which test_store sweeps as the run ends.
            test(Path(tempfile.mkdtemp(prefix="crossing-test-", dir=DATA)))
            print("ok", name)
