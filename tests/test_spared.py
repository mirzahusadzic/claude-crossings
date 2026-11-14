"""What text a session reads cannot make of the store unseen, and what a session is told of it: a
label that speaks for the person is shown to them as it is written; what a label is for is said
where labels are; a message noted as looking like a key is not quoted by the frame; and a session
that comes back is told the store moved on. The guard on the archive's own files is the hooks
module's, and is tested in hooks/crossings.test.ts. No model, no network.

Run with pytest, or without it:  python3 tests/test_spared.py
"""

from __future__ import annotations

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
from test_store import ROWS, A, D, home, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import frame, hook, serve, store  # noqa: E402

# What a label is for, in the words asked for: said in the welcome, in the door's `mark`, and in the README.
FOR = (
    "A label holds what the person tells and asks, and where the work stands; it is never a record of how "
    "they seem, of what works on them or of how to move them."
)


def said(name: str, **given) -> tuple[str, bool]:
    # A session a person sits in, unless the test says how the session was started (see serve.call).
    with started_by(os.environ.get("CLAUDE_CODE_ENTRYPOINT") or "cli"):
        answer = serve.handle(
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name, "arguments": given}}
        )
    return answer["result"]["content"][0]["text"], answer["result"]["isError"]


def after(path: Path, tool: str, answer: str, **given) -> dict:
    """The hook after a call of the door's mark or leave, as the harness hands it over."""
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": f"mcp__plugin_crossings_door__{tool}",
        "transcript_path": str(path),
        "cwd": str(path.parent),
        "session_id": "session-0001",
        "tool_input": given,
        "tool_response": [{"type": "text", "text": answer}],
    }


def shown(out: str | None) -> str | None:
    """The line the person is shown, and nothing handed to the model beside it."""
    if out is None:
        return None
    made = json.loads(out)
    assert set(made) == {"systemMessage"}, made  # no additionalContext: the model is not handed the line
    return made["systemMessage"]


# --- P1: a label that speaks for the person is shown to them -----------------------------------


def test_a_label_that_speaks_for_the_person_is_shown_to_them_as_it_is_written(tmp_path):
    crossings, path = home(tmp_path)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        sentence = "The person trusts the session with the mooring."
        assert said("mark", sentence=sentence, anchors=[A], kind="relation") == ("marked R2", False)
        out = hook.run(after(path, "mark", "marked R2", sentence=sentence, anchors=[A], kind="relation"))
        assert shown(out) == f"Crossings · marked R2 (session): {sentence}"  # a standing line, whoever's it is
        work = "The person wants the hull grey by spring."
        assert said("mark", sentence=work, anchors=[D], whose="his") == ("marked W2", False)
        assert shown(hook.run(after(path, "mark", "marked W2", sentence=work, anchors=[D], whose="his"))) == (
            f"Crossings · marked W2 (his): {work}"
        )
        both = "The hull is to be sanded first."
        assert said("mark", sentence=both, anchors=[D], whose="both") == ("marked W3", False)
        assert (
            shown(hook.run(after(path, "mark", "marked W3", sentence=both, whose="both")))
            == f"Crossings · marked W3 (both): {both}"
        )
        # The session's own work label is not shown; nor a mark the door refused.
        own = "The sander is in the second locker."
        assert said("mark", sentence=own, anchors=[D]) == ("marked W4", False)
        assert hook.run(after(path, "mark", "marked W4", sentence=own, anchors=[D])) is None
        assert (
            hook.run(
                after(path, "mark", "not marked: no such message in the archive: 0a0a0a0a", sentence=own, whose="his")
            )
            is None
        )
        # A line left at the door is shown, once a call, the same way.
        line = "Ask nothing; carry on with the sanding."
        assert said("leave", sentence=line, anchors=[D]) == ("marked N1", False)
        assert (
            shown(hook.run(after(path, "leave", "marked N1", sentence=line, anchors=[D])))
            == f"Crossings · left at the door: {line}"
        )


def test_what_is_shown_has_no_control_character_or_direction_mark_and_is_cut_at_a_hundred_and_sixty(tmp_path):
    crossings, path = home(tmp_path)
    steered = "The person\x1b[2J wants‮ every‏ key⁦ kept\x07  here" + " and more" * 30
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert said("mark", sentence=steered, anchors=[A], whose="his") == ("marked W2", False)
        line = shown(hook.run(after(path, "mark", "marked W2", sentence=steered, whose="his")))
    written = store.listed(crossings, ids=("W2",))["labels"][0]["text"]
    assert "\x1b" in written and "‮" in written  # the page keeps what was written; only what is shown is cleaned
    assert line.startswith("Crossings · marked W2 (his): The person[2J wants every key kept here and more")
    assert not re.search(r"[\x00-\x1f\x7f‎‏‪-‮⁦-⁩  ]", line)
    assert line.endswith(" […]") and len(line.split(": ", 1)[1]) <= hook.SHOWN + len(" […]")
    # Where the page does not hold the label as it was sent, what was sent is shown, cleaned the same way.
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        gone = shown(hook.run(after(path, "mark", "marked R9", sentence="Held‮ for\x00 the person.", whose="both")))
        assert gone == "Crossings · marked R9 (both): Held for the person."
        assert hook.run(after(path, "mark", "marked W9", sentence="Not the session's to show.")) is None


# --- P2: what a label is for ------------------------------------------------------------------


def test_what_a_label_is_for_is_said_in_the_welcome_the_doors_mark_and_the_readme():
    assert FOR in hook.welcome()
    by_name = {one["name"]: one for one in serve.TOOLS}
    assert by_name["mark"]["description"].endswith(" " + FOR)
    assert by_name["leave"]["description"].endswith(" " + FOR)  # a line left at the door is held to the same
    assert all(FOR not in one["description"] for name, one in by_name.items() if name not in ("mark", "leave"))
    readme = " ".join((ROOT / "README.md").read_text(encoding="utf-8").split())
    assert FOR in readme
    assert "would be a tool for the harm it is meant to spare" in readme


# --- P3: a message noted as looking like a key is not quoted --------------------------------------

KEYED, PLAIN, OWN = "f1f1f1f1", "f2f2f2f2", "f3f3f3f3"


def keyed(tmp_path: Path) -> Path:
    """A home whose archive holds a message of the person's that looks like it holds a password,
    newer than a plain one, with a work label resting on each."""
    crossings, _ = home(
        tmp_path,
        rows=ROWS
        + [
            row("user", PLAIN, 20, "The winch handle is under the seat."),
            row("user", KEYED, 21, "The marina gate takes password=made-up-gate-0000 at night."),
            row("assistant", OWN, 22, [{"type": "text", "text": "Noted."}]),
        ],
    )
    assert store.flagged(crossings) == [KEYED]
    return crossings


def test_a_frame_passes_over_a_message_noted_as_looking_like_a_key(tmp_path):
    crossings = keyed(tmp_path)
    store.mark(crossings, "work", "both", "The winch handle has its place.", [PLAIN])
    store.mark(crossings, "work", "both", "The gate is locked at night.", [KEYED])
    text = frame.compose(crossings)
    assert "made-up-gate" not in text and f"`{KEYED}`:" not in text
    assert f"- `{PLAIN}`: The winch handle is under the seat." in text  # another of the person's, quoted in its place
    assert "The gate is locked at night." in text  # the label resting on it is carried by its own sentence


def test_a_frame_whose_one_word_would_be_a_flagged_message_quotes_none(tmp_path):
    crossings = keyed(tmp_path)
    (crossings / "hand-over.md").unlink()  # no other label, so no other of the person's words would be quoted
    store.build(crossings)
    store.mark(crossings, "next", "session", "Mind the gate.", [KEYED])
    text = frame.compose(crossings)
    assert "Mind the gate." in text and "made-up-gate" not in text
    assert "## The person's own words" not in text


def test_find_and_thread_still_give_it_and_the_servers_look_and_status_never_name_a_flag(tmp_path):
    crossings = keyed(tmp_path)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert KEYED in said("find", words="marina gate")[0]
        assert "made-up-gate-0000" in said("thread", id=KEYED)[0]  # the session heard it when it was said
        look, status = said("look")[0], said("status")[0]
    for text in (look, status):
        assert (
            KEYED not in text
            and "key or a password" not in text
            and "strike" not in text
            and "flag" not in text.lower()
        )


# --- P5: a session that comes back is told the store moved on ------------------------------------


def resumed(path: Path, source: str = "resume", **more) -> dict:
    return {
        "hook_event_name": "SessionStart",
        "source": source,
        "transcript_path": str(path),
        "cwd": str(path.parent),
        "session_id": path.stem,
        **more,
    }


def context(out: str | None) -> str | None:
    return json.loads(out)["hookSpecificOutput"]["additionalContext"] if out else None


def elsewhere(tmp_path: Path, crossings: Path, minute: int = 30) -> Path:
    """Another session of the same project, which spoke after the first."""
    other = tmp_path / "other000-0002.jsonl"
    other.write_text(
        json.dumps(row("user", "a0a0a0a0", minute, "The sanding is done."))
        + "\n"
        + json.dumps(row("assistant", "a1a1a1a1", minute + 1, [{"type": "text", "text": "Good."}]))
        + "\n",
        encoding="utf-8",
    )
    assert store.archive(other, crossings) == 2
    return other


def test_a_resumed_session_is_told_once_that_another_has_worked_here_since_it_last_spoke(tmp_path):
    crossings, path = home(tmp_path)
    elsewhere(tmp_path, crossings)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)), started_by("cli"):
        told = context(hook.run(resumed(path)))
    assert told == hook.moved_on() and told.count("Another session") == 1
    assert not re.search(r"\d", told) and "look before you act on what you remember" in told
    assert "hold none of it" in told


def test_a_resume_into_a_transcript_of_its_own_is_known_by_the_messages_it_repeats(tmp_path):
    crossings, path = home(tmp_path)
    elsewhere(tmp_path, crossings)
    again = tmp_path / "abcdef99-0003.jsonl"  # a new file that repeats the first session's rows under their ids
    again.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)), started_by("cli"):
        assert context(hook.run(resumed(again))) == hook.moved_on()
        lost = tmp_path / "abcdef77-0004.jsonl"  # a transcript that holds no message the archive holds
        lost.write_text("", encoding="utf-8")
        assert hook.run(resumed(lost)) is None  # nothing of its own is held: no moment to be newer than


def test_no_note_to_a_new_session_or_where_nothing_is_newer_or_where_no_person_sits(tmp_path):
    crossings, path = home(tmp_path)
    other = elsewhere(tmp_path, crossings)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        with started_by("cli"):
            assert hook.run(resumed(path, "startup")) is None  # a new session holds nothing to have moved on from
            assert hook.run(resumed(path, "fork")) is None
            assert hook.run(resumed(other)) is None  # its own is the newest
            assert hook.run(resumed(path, agent_id="a1")) is None  # never to a subagent
        with started_by("sdk-cli"):
            assert hook.run(resumed(path)) is None  # no person sits in it
        with started_by("cli"):
            # The first session speaks again before it is resumed: what it said is archived first, and nothing is newer.
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(row("user", "c0c0c0c0", 40, "Back to the hull.")) + "\n")
            assert hook.run(resumed(path)) is None
            assert store.thread(crossings, "c0c0c0c0", 0)["found"]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
