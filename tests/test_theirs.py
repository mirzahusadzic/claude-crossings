"""The person's side, as a session is offered it and shown it: `their` in the tool listing and in the usage, the role
`pair:them`, and `(theirs)` wherever a label's owner is printed, on a home whose files hold the token every make has
kept for the person (`his`). That token is still taken wherever it was, and means the same; and a home is written as
it was, byte for byte, whichever spelling it is given. On a made-up transcript, in temporary homes. No model, no
network.

Run with pytest, or without it:  python3 tests/test_theirs.py
"""

from __future__ import annotations

import contextlib
import datetime
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

from test_count import set_to  # noqa: E402
from test_edges import through  # noqa: E402
from test_store import A, B, D, E, home, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, hook, serve, store  # noqa: E402

OLD = re.compile(r"\b(his|him|His)\b")  # the person's side as the interface spelled it before, as a word
DAY = "2026-11-12"  # the day of the labels the store marks itself here
MOORING = "The mooring is the person's to choose."
HULL = "The hull is the person's to paint."
# The archive of the made-up transcript (tests/test_store.py), as every make has written it.
ARCHIVE = (
    '{"uuid": "aaaaaaaa-0000-4000-8000-000000000000", "id": "aaaaaaaa", "session": "session-", "voice": "his", '
    '"at": "2026-11-11T09:01:00.000Z", "text": "My boat is called Tern.\\nIts mooring is number 41, by the café."}\n'
    '{"uuid": "bbbbbbbb-0000-4000-8000-000000000000", "id": "bbbbbbbb", "session": "session-", "voice": "session", '
    '"at": "2026-11-11T09:02:00.000Z", "text": "Noted: Tern, at mooring 41.\\n\\n| a | table |\\n| --- | --- |"}\n'
    '{"uuid": "dddddddd-0000-4000-8000-000000000000", "id": "dddddddd", "session": "session-", "voice": "his", '
    '"at": "2026-11-11T09:04:00.000Z", "text": "We paint the hull grey in spring"}\n'
    '{"uuid": "eeeeeeee-0000-4000-8000-000000000000", "id": "eeeeeeee", "session": "session-", "voice": "session", '
    '"at": "2026-11-11T09:05:00.000Z", "text": "Grey it is. I will remind you in March."}\n'
)


def served(project: Path, name: str, **given) -> str:
    """One call of a handle through the door's server, for a session a person sits in: its text."""
    with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=str(project)):
        text, _ = serve.call(name, given)
    return text


def after(project: Path, given: dict, answer: str) -> str | None:
    """The line the person is shown under the turn after a call of the door's `mark`, as the hook gives it."""
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__plugin_crossings_door__mark",
        "transcript_path": str(project.parent / "s1.jsonl"),  # names no file
        "cwd": str(project),
        "session_id": "s1",
        "tool_input": given,
        "tool_response": [{"type": "text", "text": answer}],
    }
    with started_by("cli"):
        made = hook.run(event)
    return json.loads(made)["systemMessage"] if made else None


def kept(crossings: Path) -> dict:
    """What a home's files hold that a build reads: the archive's lines, each label page, and the columns of the
    index that hold the person's side."""
    db = sqlite3.connect(str(crossings / "store.db"))
    try:
        voices = [r[0] for r in db.execute("select voice from said order by seq")]
        owners = [tuple(r) for r in db.execute("select id, whose from label order by n")]
    finally:
        db.close()
    return {
        "said": {each.name: each.read_bytes() for each in sorted((crossings / "said").glob("*.jsonl"))},
        "pages": {each.name: each.read_bytes() for each in sorted((crossings / "labels").glob("*.md"))},
        "hand-over": (crossings / "hand-over.md").read_bytes(),
        "voices": voices,
        "owners": owners,
    }


def marked(crossings: Path, person: str) -> None:
    """The labels of the person's side, given in the spelling `person`: through the door's server (a standing line
    and a work label), from the person's own terminal, and by the store itself."""
    project = crossings.parent
    for kind, sentence, anchor in (("relation", MOORING, A), ("work", HULL, D)):
        answer = served(project, "mark", kind=kind, whose=person, sentence=sentence, anchors=[anchor])
        assert answer.startswith("marked "), answer
    code, out = through(
        "mark", "--whose", person, "--anchors", D, "The keel is the person's call.", "--cwd", str(project)
    )
    assert code == 0 and out.startswith("marked W3"), out
    assert store.mark(crossings, "work", person, "The tiller is the person's to varnish.", [A], day=DAY)["written"]


# --- what is offered and what is shown -----------------------------------------------------------------------------


def test_what_a_session_is_offered_says_their_and_pair_them_and_never_the_old_spelling():
    listed = json.dumps(serve.TOOLS)
    tools = {each["name"]: each["inputSchema"]["properties"] for each in serve.TOOLS}
    assert tools["find"]["voice"]["enum"] == ["their", "session"]
    assert tools["mark"]["whose"]["enum"] == ["their", "session", "both"]
    assert tools["thread"]["role"]["enum"] == ["pair:me", "pair:them"]
    assert tools["thread"]["role"]["description"].startswith("`pair:them`: the pair headed by the person's turn;")
    assert not OLD.search(listed), OLD.search(listed)
    for root in (None, str(ROOT)):  # the server's instructions, with the plugin's hooks or alone
        with set_to(CLAUDE_PLUGIN_ROOT=root):
            assert not OLD.search(serve.instructions())
    # the door's usage, as its source gives it and as its parser prints it
    assert "--voice their|session" in door.__doc__ and "--whose their|session|both" in door.__doc__
    assert "pair:me|pair:them" in door.__doc__ and not OLD.search(door.__doc__)
    helped = io.StringIO()
    with contextlib.redirect_stdout(helped), contextlib.suppress(SystemExit):
        door.main(["--help"])
    assert "{their,session}" in helped.getvalue() and "{their,session,both}" in helped.getvalue()
    assert not OLD.search(helped.getvalue())
    assert door.UNROLED == "thread takes one of two roles: pair:me or pair:them."


def test_every_answer_shows_the_persons_side_as_theirs_on_a_home_whose_files_hold_the_old_token(tmp_path):
    crossings, _ = home(tmp_path)
    project = crossings.parent
    marked(crossings, "his")
    store.mark(crossings, "next", "session", "Find out whether the mooring is chosen.", [A, D], day=DAY)
    # The files hold the token every make kept: the archive's voice, the pages' whose cells, the index's columns.
    files = kept(crossings)
    assert all(b'"voice": "his"' in each for each in files["said"].values())
    assert b"| his |" in files["hand-over"] and all(b"| his |" in each for each in files["pages"].values())
    assert "his" in files["voices"] and ("R2", "his") in files["owners"]
    answers = {
        "look": served(project, "look"),
        "labels": served(project, "labels"),
        "labels R1 R2 W2": served(project, "labels", ids=["R1", "R2", "W2"]),
        "labels relation": served(project, "labels", kind="relation"),
        "find mooring": served(project, "find", words="mooring"),
        "find hull": served(project, "find", words="hull"),
        "thread": served(project, "thread", id=A),
        "pair": served(project, "thread", id=D, role="pair:them"),
        "crossing": served(project, "crossing"),
        "status": served(project, "status"),
        "door look": through("look", "--cwd", str(project))[1],
        "door labels": through("labels", "R1", "R2", "R3", "W2", "W3", "--cwd", str(project))[1],
        "door find": through("find", "person", "--cwd", str(project))[1],
        "door thread": through("thread", D, "--cwd", str(project))[1],
        "frame": frame.compose(crossings),
        "frame, new": frame.compose(crossings, new=True),
        "frame, packed": frame.compose(crossings, session="session-"),
        "hand-over page": door.handed_over(crossings),
    }
    for name, text in answers.items():
        assert not OLD.search(text), (name, OLD.search(text), text)
    # Each place a label's owner is printed prints the person's as theirs.
    for name, theirs in (
        ("look", "- W4 (theirs): The tiller is the person's to varnish. [aaaaaaaa]"),
        ("labels R1 R2 W2", "- R1 (theirs, 2026-11-11): Their boat is called Tern"),
        ("labels R1 R2 W2", f"- R2 (theirs, 2026-11-11): {MOORING}"),
        ("labels relation", "- R1 (theirs, 2026-11-11): Their boat is called Tern"),
        ("find mooring", f"- R2 (relation, theirs): {MOORING}"),
        ("find hull", f"- W2 (work, theirs): {HULL}"),
        ("thread", f"- R2 (relation, theirs): {MOORING}"),
        ("crossing", "- R1 (theirs): Their boat is called Tern and lies at mooring 41."),
        ("crossing", f"- R2 (theirs): {MOORING}"),
        ("door look", "- W4 (theirs): The tiller is the person's to varnish. [aaaaaaaa]"),
        ("door labels", "- W3 (theirs, 2026-11-11): The keel is the person's call. [dddddddd]"),
        ("door find", f"- W2 (work, theirs): {HULL}"),
        ("door thread", f"- W2 (work, theirs): {HULL}"),
        ("frame", "- W1 (both): The hull is to be painted grey in spring."),
        ("frame", f"- W2 (theirs): {HULL}"),
        ("frame, new", "- R1 (theirs): Their boat is called Tern"),
        ("frame, packed", "- R1 (theirs): Their boat is called Tern"),
        ("hand-over page", "- R1 (theirs): Their boat is called Tern and lies at mooring 41. [aaaaaaaa, bbbbbbbb]"),
    ):
        assert theirs in answers[name], (name, theirs, answers[name])
    assert "with the role `pair:them`: the person's turn" in answers["pair"]
    # And the line the person is shown as such a label is marked through the door, also where its page has it not.
    given = {"whose": "their", "sentence": "The sails are the person's to choose.", "anchors": [D]}
    answer = served(project, "mark", **given)
    assert after(project, given, answer) == f"Crossings · marked {answer.split()[1]} (theirs): {given['sentence']}"
    unwritten = {"kind": "relation", "whose": "his", "sentence": "Not in any page.", "anchors": [D]}
    assert after(project, unwritten, "marked R9") == "Crossings · marked R9 (theirs): Not in any page."


# --- the old spelling, still taken ----------------------------------------------------------------------------------


def test_the_old_spelling_is_still_taken_wherever_it_was_and_answers_the_same(tmp_path):
    crossings, _ = home(tmp_path)
    project = crossings.parent
    # The server: `voice` of find, `role` of thread; the answer names the role in the new spelling.
    assert served(project, "find", words="mooring", voice="his") == served(
        project, "find", words="mooring", voice="their"
    )
    said = served(project, "find", words="mooring", voice="their")
    assert f"`{A}` the person" in said and f"`{B}`" not in said
    for asked in (A, D, E):
        assert served(project, "thread", id=asked, role="pair:him") == served(
            project, "thread", id=asked, role="pair:them"
        )
    assert served(project, "thread", id=D, role="pair:him").startswith(
        f"thread of `{D}` with the role `pair:them`: the person's turn"
    )
    # The door from the person's own terminal: --voice, --role and --whose.
    assert through("find", "mooring", "--voice", "his", "--cwd", str(project)) == through(
        "find", "mooring", "--voice", "their", "--cwd", str(project)
    )
    for asked in (A, D):
        assert through("thread", asked, "--role", "pair:him", "--cwd", str(project)) == through(
            "thread", asked, "--role", "pair:them", "--cwd", str(project)
        )
    # The store itself: a voice to find by, and whose a label is.
    assert store.find(crossings, "mooring", voice="his") == store.find(crossings, "mooring", voice="their")
    assert store.settled("relation", "their") == store.settled("relation", "his") == "his"
    assert store.settled("refused", "their") == "session"
    # A mark of either spelling, by the server, the door and the store, is the person's: shown as such, and written
    # as every make wrote it.
    for person in ("his", "their"):
        given = {"kind": "relation", "whose": person, "sentence": f"The berth is chosen ({person}).", "anchors": [A]}
        answer = served(project, "mark", **given)
        assert after(project, given, answer) == f"Crossings · marked {answer.split()[1]} (theirs): {given['sentence']}"
    rows = [label for label in store.labels(crossings) if label["text"].startswith("The berth")]
    assert [label["whose"] for label in rows] == ["his", "his"] and all(store.persons(label) for label in rows)
    # A home given the new spelling is written byte for byte as one given the old.
    written = {}
    for person in ("his", "their"):
        made, _ = home(tmp_path / person)
        marked(made, person)
        written[person] = kept(made)
    assert written["their"] == written["his"]


# --- the files of a home, as they were ------------------------------------------------------------------------------


def test_pin_a_home_is_written_byte_for_byte_as_the_make_before_wrote_it(tmp_path):
    """Pin: what the make before this one writes of a home where labels of the person's side are marked through the
    server, from the person's terminal and by the store, each given `his`: its archive, its label pages and the index's
    columns of the person's side. The archive's voice and the pages' whose cell are the words v0.4.0 compares with
    (`his`, `session`, `both`), so it reads such a home as before; nothing here is of this make's own."""
    crossings, _ = home(tmp_path)
    marked(crossings, "his")
    files = kept(crossings)
    assert files["said"] == {"session-.jsonl": ARCHIVE.encode("utf-8")}
    today = datetime.date.today().isoformat()
    head = (
        "Each row is one sentence about a stretch of the record and the ids it rests on: messages, or other labels, "
        "each with a mark of its sentence as it stood. Strike any row; the store follows at its next build.\n\n"
        "| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n"
    )
    assert files["pages"] == {
        f"{today}.md": (
            f"# Labels marked on {today}\n\n{head}"
            f"| R2 | {MOORING} | his | `{A}` |\n"
            f"| W2 | {HULL} | his | `{D}` |\n"
            f"| W3 | The keel is the person's call. | his | `{D}` |\n"
        ).encode("utf-8"),
        f"{DAY}.md": (
            f"# Labels marked on {DAY}\n\n{head}| W4 | The tiller is the person's to varnish. | his | `{A}` |\n"
        ).encode("utf-8"),
    }
    assert files["voices"] == ["his", "session", "his", "session"]
    # the hand-over page first, then the pages by their names: the day the store marked on, before today
    assert files["owners"] == [
        ("R1", "his"),
        ("W1", "both"),
        ("W4", "his"),
        ("R2", "his"),
        ("W2", "his"),
        ("W3", "his"),
    ]
    assert b"| R1 | Their boat is called Tern and lies at mooring 41. | his | 700 / 800 |" in files["hand-over"]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
