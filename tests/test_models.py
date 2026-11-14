"""Which model spoke and which model wrote a label: kept in the archive and beside the label pages,
read as unknown where it was never kept, and shown where a reader looks. No model, no network.

Run with pytest, or without it:  python3 tests/test_models.py
"""

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

from test_edges import set_to  # noqa: E402
from test_store import D, at_terminal, home, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, hook, second, serve, store, transcript  # noqa: E402

NORTH, SOUTH = "made-up-model-north-1", "made-up-model-south-2"  # invented names, no real model's
DAY = "2026-11-12"


def spoken(uid: str, minute: int, text: str, model=None) -> dict:
    """A row of the session's own voice, naming the model that wrote it where `model` is given."""
    made = row("assistant", uid, minute, [{"type": "text", "text": text}])
    if model is not None:
        made["message"]["model"] = model
    return made


def kept(crossings: Path, session: str) -> list[dict]:
    return [
        json.loads(line) for line in (crossings / "said" / f"{session}.jsonl").read_text(encoding="utf-8").splitlines()
    ]


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


def two_sessions(tmp_path: Path) -> tuple[Path, Path, Path]:
    """A home whose archive holds two sessions besides the first: `northern`, on one model, and
    `southern`, on another, which spoke later. The first session's rows name no model."""
    crossings, _ = home(tmp_path)
    north = written(
        tmp_path,
        "northern-0001",
        [
            row("user", "10000001", 10, "The anchor chain wants a look."),
            spoken("10000002", 11, "It does; the shackle is worn.", NORTH),
        ],
    )
    south = written(
        tmp_path,
        "southern-0002",
        [row("user", "20000001", 20, "And the fenders?"), spoken("20000002", 21, "Two of them are split.", SOUTH)],
    )
    assert store.archive(north, crossings) == 2 and store.archive(south, crossings) == 2
    store.build(crossings)
    return crossings, north, south


# --- which model spoke ---------------------------------------------------------------------------


def test_a_message_of_the_sessions_keeps_the_model_that_said_it_and_the_persons_keep_none(tmp_path):
    crossings, _ = home(tmp_path)
    person = row("user", "30000001", 30, "Is the bilge pump running?")
    person["message"]["model"] = NORTH  # a row of the person's names no model, whatever it holds
    path = written(
        tmp_path,
        "harbour0-0003",
        [
            person,
            spoken("30000002", 31, "It is, quietly.", NORTH),
            spoken("30000003", 32, "No response requested.", "<synthetic>"),  # the harness's, in the session's place
            spoken("30000004", 33, "A row that names no model."),
        ],
    )
    assert store.archive(path, crossings) == 3  # the harness's row is nobody's words, and is not kept
    rows = kept(crossings, "harbour0")
    assert [(r["id"], r["voice"], r.get("model")) for r in rows] == [
        ("30000001", "his", None),
        ("30000002", "session", NORTH),
        ("30000004", "session", None),
    ]
    assert "model" not in rows[0] and "model" not in rows[2]  # a row that names none keeps none
    assert transcript.model(spoken("x", 1, "y", "  " + NORTH + " ")) == NORTH and transcript.model(person) == ""
    assert transcript.model(spoken("x", 1, "y", 7)) == ""
    store.build(crossings)
    db = sqlite3.connect(crossings / "store.db")
    assert db.execute("select model from said where id = '30000002'").fetchone()[0] == NORTH
    db.close()


def test_what_was_archived_before_is_read_as_unknown_and_never_written_twice(tmp_path):
    """An archive kept before models were: its lines name none, they stay as they are, and the
    same transcript archived again adds nothing."""
    crossings, _ = home(tmp_path)
    path = written(
        tmp_path,
        "harbour0-0003",
        [row("user", "30000001", 30, "Is the bilge pump running?"), spoken("30000002", 31, "It is, quietly.", NORTH)],
    )
    (crossings / "said").mkdir(exist_ok=True)
    old = [
        {
            "uuid": "30000001-0000-4000-8000-000000000000",
            "id": "30000001",
            "session": "harbour0",
            "voice": "his",
            "at": "2026-11-11T09:30:00.000Z",
            "text": "Is the bilge pump running?",
        },
        {
            "uuid": "30000002-0000-4000-8000-000000000000",
            "id": "30000002",
            "session": "harbour0",
            "voice": "session",
            "at": "2026-11-11T09:31:00.000Z",
            "text": "It is, quietly.",
        },
    ]
    page = crossings / "said" / "harbour0.jsonl"
    page.write_text("".join(json.dumps(r) + "\n" for r in old), encoding="utf-8")
    before = page.read_text(encoding="utf-8")
    assert store.archive(path, crossings) == 0 and page.read_text(encoding="utf-8") == before
    held = store.build(crossings)
    assert held["session"] == 3 and held["models"] == {"labels": 0, "session": 0}
    assert store.spoke(crossings, "harbour0") == ""  # its newest message names no model: not known


# --- which model wrote a label ---------------------------------------------------------------------


def test_a_label_marked_from_the_door_keeps_the_model_of_the_session_that_marks_it(tmp_path):
    """The session that marks is named by its transcript: the model of its own newest message, though
    another session spoke later. The page's row is written as it always was."""
    crossings, north, _ = two_sessions(tmp_path)
    assert store.spoke(crossings, "northern") == NORTH and store.spoke(crossings, "southern") == SOUTH
    project = str(crossings.parent)
    code, out = through(
        "mark",
        "--cwd",
        project,
        "--transcript",
        str(north),
        "--anchors",
        "10000002",
        "--whose",
        "both",
        "The shackle on the anchor chain is to be replaced.",
    )
    assert code == 0 and out.startswith("marked W2")
    page = next((crossings / "labels").glob("*.md")).read_text(encoding="utf-8")
    assert page.endswith("| W2 | The shackle on the anchor chain is to be replaced. | both | `10000002` |\n")
    sign = (crossings / store.MODELS).read_text(encoding="utf-8").splitlines()
    assert sign[0].startswith("# ") and sign[1:] == [
        f"W2@{store.digest('The shackle on the anchor chain is to be replaced.')} {NORTH}"
    ]
    whole = through("labels", "W2", "--cwd", project)[1]
    assert whole.startswith(f"- W2 (both, 2026-11-11, written by {NORTH}): The shackle")
    # The home knows two models (the messages of `northern` and `southern`), so a list names the writer too.
    assert f"- W2 (both, 2026-11-11, written by {NORTH}): The shackle" in through("labels", "--cwd", project)[1]
    assert through("mark", "--cwd", project, "--anchors", "10000002", "Marked with no session named.")[1].startswith(
        "marked W3"
    )
    assert store.listed(crossings, ids=("W3",))["labels"][0]["model"] == ""  # not known, and so not kept
    assert len((crossings / store.MODELS).read_text(encoding="utf-8").splitlines()) == 2


def test_a_label_marked_through_the_server_is_signed_by_the_hook_after_the_call(tmp_path):
    """The server is not told which session calls it. The hook after the call is, and signs the
    label the door's answer names, with the sentence that was sent, once."""
    crossings, north, south = two_sessions(tmp_path)
    wired = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PostToolUse"]
    assert [g["matcher"] for g in wired] == ["mcp__plugin_crossing_door__(mark|leave)"]
    sentence = "The fenders  are to be  replaced."
    event = {
        "hook_event_name": "PostToolUse",
        "tool_name": "mcp__plugin_crossing_door__mark",
        "transcript_path": str(south),
        "cwd": str(tmp_path),
        "session_id": "southern-0002",
        "tool_input": {"sentence": sentence, "anchors": ["20000002"]},
    }
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent), CROSSING_OURS=str(tmp_path / "ours")):
        answer = said("mark", sentence=sentence, anchors=["20000002"])
        assert answer == ("marked W2", False)
        assert store.listed(crossings, ids=("W2",))["labels"][0]["model"] == ""
        refused = {
            **event,
            "tool_response": [{"type": "text", "text": "not marked: no such message in the archive: 0a0a0a0a"}],
        }
        assert hook.run(refused) is None and not (crossings / store.MODELS).exists()
        other = {
            **event,
            "tool_input": {"sentence": "Another sentence altogether."},
            "tool_response": [{"type": "text", "text": "marked W2"}],
        }
        assert hook.run(other) is None and not (crossings / store.MODELS).exists()  # not the label that was sent
        assert hook.run({**event, "tool_input": {}, "tool_response": "marked W2"}) is None
        assert hook.run({**event, "tool_input": "odd", "tool_response": "marked W2"}) is None
        assert not (crossings / store.MODELS).exists()
        done = {**event, "tool_response": [{"type": "text", "text": "marked W2"}]}
        assert hook.run(done) is None
        assert (
            f"(session, 2026-11-11, written by {SOUTH}): The fenders are to be replaced."
            in said("labels", ids=["W2"])[0]
        )
        lines = (crossings / store.MODELS).read_text(encoding="utf-8").splitlines()
        assert hook.run({**done, "transcript_path": str(north)}) is None  # signed once: the first stands
        assert (crossings / store.MODELS).read_text(encoding="utf-8").splitlines() == lines
        (crossings / "store.db").unlink()  # and the index is made again from the plain files alike
        assert store.listed(crossings, ids=("W2",))["labels"][0]["model"] == SOUTH
        # A line left at the door is signed the same way, and so is a label in the home that is ours.
        assert said("leave", sentence="Look at the fenders first.", anchors=["20000002"]) == ("marked N1", False)
        assert hook.run(
            {
                **done,
                "tool_name": "mcp__plugin_crossing_door__leave",
                "tool_input": {"sentence": "Look at the fenders first."},
                "tool_response": [{"type": "text", "text": "marked N1"}],
            }
        ) == json.dumps(
            {"systemMessage": "Crossings · left at the door: Look at the fenders first."}, ensure_ascii=False
        )  # and shown to the person
        assert store.listed(crossings, ids=("N1",))["labels"][0]["model"] == SOUTH
        store.archive(
            south, tmp_path / "ours"
        )  # the home that is ours holds no archive of its own unless one is put there
        assert said("mark", sentence="A line that is ours.", anchors=["20000002"], home="ours") == ("marked W1", False)
        assert (
            hook.run(
                {
                    **done,
                    "tool_input": {"sentence": "A line that is ours.", "home": "ours"},
                    "tool_response": [{"type": "text", "text": "marked W1"}],
                }
            )
            is None
        )
        assert store.listed(tmp_path / "ours", ids=("W1",))["labels"][0]["model"] == SOUTH
        assert store.listed(crossings, ids=("W1",))["labels"][0]["model"] == ""  # this home's W1 is another label
        # A session whose newest message names no model signs nothing: its model is not known.
        assert said("mark", sentence="Marked by the first session.", anchors=[D]) == ("marked W3", False)
        first = {
            **done,
            "transcript_path": "",
            "session_id": "session-0001",
            "tool_input": {"sentence": "Marked by the first session."},
            "tool_response": [{"type": "text", "text": "marked W3"}],
        }
        assert hook.run(first) is None and store.listed(crossings, ids=("W3",))["labels"][0]["model"] == ""
        (crossings / "switch").write_text("off\n", encoding="utf-8")  # switched off, nothing is added
        assert store.sign(crossings, "W3", "Marked by the first session.", "") is False
        assert (
            hook.run({**first, "transcript_path": str(south)}) is None
            and store.listed(crossings, ids=("W3",))["labels"][0]["model"] == ""
        )


def test_old_pages_read_exactly_as_before_and_a_reworded_label_is_of_a_model_not_known(tmp_path):
    crossings, north, _ = two_sessions(tmp_path)
    before = store.labels(crossings)
    assert (
        store.mark(crossings, "work", "both", "The chain is to be galvanised.", ["10000002"], day=DAY, model=NORTH)[
            "model"
        ]
        == NORTH
    )
    assert store.labels(crossings)[:2] == before  # the page every home starts with, as it was read
    assert [label["model"] for label in store.listed(crossings, kind="work")["labels"]] == [NORTH, ""]
    assert [label["model"] for label in store.listed(crossings, kind="relation")["labels"]] == [""]
    assert "written by" not in through("labels", "R1", "W1", "--cwd", str(crossings.parent))[1]
    page = crossings / "labels" / f"{DAY}.md"
    page.write_text(page.read_text(encoding="utf-8").replace("galvanised", "painted"), encoding="utf-8")
    store.build(crossings)
    assert (
        store.listed(crossings, ids=("W2",))["labels"][0]["model"] == ""
    )  # its sentence is no longer the one it wrote
    assert (
        store.sign(crossings, "W2", "The chain is to be painted.", SOUTH) is True
    )  # and it may be signed as it stands now
    assert store.listed(crossings, ids=("W2",))["labels"][0]["model"] == SOUTH
    assert store.sign(crossings, "W9", "No such label.", SOUTH) is False


def test_a_hand_edited_line_and_a_key_signed_twice(tmp_path):
    crossings, _ = home(tmp_path)
    (crossings / store.MODELS).write_text(
        "# a note\n"
        f"W1@{store.digest('The hull is to be painted grey in spring.')} {NORTH}  # first\n"
        "not a line of this file\n"
        f"W1@{store.digest('The hull is to be painted grey in spring.')} {SOUTH}\n",
        encoding="utf-8",
    )
    assert store.build(crossings)["models"]["labels"] == 1
    assert store.listed(crossings, ids=("W1",))["labels"][0]["model"] == SOUTH  # the later line stands


def test_stacks_states_and_striking_behave_as_before_and_a_struck_label_takes_its_model_with_it(tmp_path):
    crossings, north, _ = two_sessions(tmp_path)
    for sentence in ("The chain.", "The shackle."):
        assert store.mark(crossings, "work", "both", sentence, ["10000002"], day=DAY, model=NORTH)["written"]
    top = store.mark(crossings, "work", "both", "The ground tackle.", ["W2", "W3"], day=DAY, model=SOUTH)
    assert top["written"] and top["beneath"] == ["W2", "W3"]
    states = {label["id"]: (label["state"], label["model"]) for label in store.listed(crossings, kind="work")["labels"]}
    assert states == {"W1": ("carried", ""), "W2": ("cooled", NORTH), "W3": ("cooled", NORTH), "W4": ("carried", SOUTH)}
    row = [
        line
        for line in (crossings / "labels" / f"{DAY}.md").read_text(encoding="utf-8").splitlines()
        if line.startswith("| W4 ")
    ]
    assert row == [
        f"| W4 | The ground tackle. | both | `W2@{store.digest('The chain.')}`, `W3@{store.digest('The shackle.')}` |"
    ]
    assert store.not_by(crossings, NORTH) == ["W4"] and store.not_by(crossings, SOUTH) == ["W2", "W3"]
    assert store.not_by(crossings, "made-up-model-east-3") == [
        "W2",
        "W3",
        "W4",
    ]  # a label of a model not known is never among them
    signs = (crossings / store.MODELS).read_text(encoding="utf-8")
    assert store.strike(crossings, "W1")["removed"] == 1  # a label never signed: the file of models is as it was
    assert (crossings / store.MODELS).read_text(encoding="utf-8") == signs
    assert store.strike(crossings, "W4")["removed"] == 1  # the line of the page; its model goes with it, uncounted
    assert "W4@" not in (crossings / store.MODELS).read_text(encoding="utf-8")
    assert {label["id"]: label["state"] for label in store.listed(crossings, kind="work")["labels"]} == {
        "W2": "carried",
        "W3": "carried",
    }
    store.strike(crossings, "10000001")  # a message struck leaves the file of models alone
    assert store.not_by(crossings, SOUTH) == ["W2", "W3"]
    copied = [p.name for p in second.plain(crossings)]
    assert store.MODELS in copied and "struck.txt" in copied  # the second copy holds it, as a plain file


def test_status_counts_what_is_known_and_the_frame_carries_no_model(tmp_path):
    plain, _ = home(tmp_path / "plain")
    assert through("status", "--cwd", str(plain.parent))[1].endswith(
        "2 labels, and 0 struck.\n"
    )  # nothing known: as before
    crossings, north, south = two_sessions(tmp_path)
    project = str(crossings.parent)
    assert through("status", "--cwd", project)[1].endswith(
        "and 0 struck. Which model wrote it is known for 0 of the labels and 2 of the session's messages.\n"
    )
    framed = frame.compose(crossings)
    assert store.mark(crossings, "work", "both", "The fenders are split.", ["20000002"], day="2026-11-11")["written"]
    unsigned = frame.compose(crossings)
    store.sign(crossings, "W2", "The fenders are split.", SOUTH)
    assert (
        frame.compose(crossings) == unsigned != framed
        and NORTH not in unsigned
        and SOUTH not in frame.compose(crossings)
    )
    shown = through("status", "--cwd", project)[1]
    assert "Which model wrote it is known for 1 of the labels and 2 of the session's messages." in shown
    assert store.status(crossings)["models"] == {"labels": 1, "session": 2}


def test_a_database_of_the_make_before_models_is_built_again(tmp_path):
    crossings, _, _ = two_sessions(tmp_path)
    db = sqlite3.connect(crossings / "store.db")
    db.execute("pragma user_version = 2")
    db.commit()
    db.close()
    assert store.status(crossings)["models"] == {"labels": 0, "session": 2}  # read from one made in memory
    db = sqlite3.connect(crossings / "store.db")
    assert db.execute("pragma user_version").fetchone()[0] == 2  # a read writes no database
    db.close()
    store.build(crossings)
    db = sqlite3.connect(crossings / "store.db")
    assert (
        db.execute("pragma user_version").fetchone()[0] == store.MADE == 4
    )  # 4: it counts the lines of the archive that are no message
    db.close()


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
