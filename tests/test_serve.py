"""The door as a server: the protocol spoken by hand, every handle, and no file's path in any answer.
No model, no network.

Run with pytest, or without it:  python3 tests/test_serve.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to  # noqa: E402
from test_store import ROWS, A, B, D, E, home, in_person, row, started_by, sweep  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import door, frame, hook, serve, store  # noqa: E402


def said(name: str, **given) -> tuple[str, bool]:
    """One call of a handle, as a client sends it: the text that comes back, and whether it failed."""
    # A session a person sits in, unless the test says how the session was started (see serve.call).
    with started_by(os.environ.get("CLAUDE_CODE_ENTRYPOINT") or "cli"):
        answer = serve.handle(
            {"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": {"name": name, "arguments": given}}
        )
    assert answer["id"] == 7 and [c["type"] for c in answer["result"]["content"]] == ["text"]
    return answer["result"]["content"][0]["text"], answer["result"]["isError"]


def test_the_protocol_is_spoken_by_hand_over_a_pipe(tmp_path):
    """As a harness starts it: one process, one JSON object a line in, one out."""
    crossings, _ = home(tmp_path)
    sent = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2025-03-26", "capabilities": {}},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "ping"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "status", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 5, "method": "resources/list"},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "strike", "arguments": {"id": A}}},
        {"jsonrpc": "2.0", "id": 8, "method": "initialize", "params": {"protocolVersion": "1999-01-01"}},
    ]
    lines = (
        "".join(json.dumps(s) + "\n" for s in sent[:3])
        + "\nnot json\n[1, 2]\n"
        + "".join(json.dumps(s) + "\n" for s in sent[3:])
    )
    env = {
        **os.environ,
        "CLAUDE_PROJECT_DIR": str(crossings.parent),
        "CLAUDE_CODE_ENTRYPOINT": "cli",
    }  # a person sits in it
    ran = subprocess.run(
        [sys.executable, "-I", str(ROOT / "crossing" / "serve.py")],
        input=lines,
        capture_output=True,
        text=True,
        timeout=60,
        env=env,
        cwd=tmp_path,
    )
    assert ran.returncode == 0 and ran.stderr == ""
    answers = {a["id"]: a for a in map(json.loads, ran.stdout.splitlines())}
    assert sorted(answers) == [1, 2, 3, 4, 5, 6, 8]  # a notice, a blank and a line that is no request get no answer
    first = answers[1]["result"]
    assert first["protocolVersion"] == "2025-03-26" and first["capabilities"] == {"tools": {"listChanged": False}}
    assert first["serverInfo"]["name"] == "door" and first["instructions"] == serve.instructions()
    assert (
        answers[8]["result"]["protocolVersion"] == "2025-06-18"
    )  # a version it does not know is answered in its newest
    assert answers[2]["result"] == {}
    assert [t["name"] for t in answers[3]["result"]["tools"]] == [
        "look",
        "labels",
        "find",
        "thread",
        "mark",
        "leave",
        "status",
    ]
    status = answers[4]["result"]
    assert status["isError"] is False and [c["type"] for c in status["content"]] == ["text"]
    assert status["content"][0]["text"].startswith(
        "The store holds 2 messages of the person's and 2 of the session's ("
    )
    assert status["content"][0]["text"].endswith("2026-11-11 to 2026-11-11), 2 labels, and 0 struck.")
    assert answers[5]["error"]["code"] == -32601
    assert answers[6]["error"] == {
        "code": -32602,
        "message": "The door has these handles: look, labels, find, thread, mark, leave, status.",
    }


def test_every_handle_is_a_small_tool_kept_in_front_of_a_session():
    """A harness shows a model only a server's tool names until it searches for one, unless the
    tool says to be loaded. Seven small handles are to be in front of a session."""
    for one in serve.TOOLS:
        assert one["_meta"] == {"anthropic/alwaysLoad": True} and one["inputSchema"]["type"] == "object"
        assert set(one["inputSchema"]["required"]) <= set(one["inputSchema"]["properties"])
        assert len(one["description"]) < (
            400 if one["name"] in ("mark", "leave") else 260
        )  # these two also say what a label is for
    assert len(json.dumps(serve.TOOLS)) < 5400
    wired = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]["door"]
    assert wired == {
        "command": "python3",
        "args": ["-I", "${CLAUDE_PLUGIN_ROOT}/crossing/serve.py"],
        "alwaysLoad": True,
    }


def test_what_a_session_is_told_names_the_handles_that_exist_and_no_file(tmp_path):
    """Nothing a session reads is to point a hand at the file system: no path, no script's name
    and no shell command, in the instructions, the tools, a frame, the waking note or any answer."""
    crossings, path = home(tmp_path)
    store.mark(crossings, "next", "session", "The mooring is next.", [A])
    told = [serve.instructions(), json.dumps(serve.TOOLS), frame.compose(crossings), hook.waking({"cut": 2})]
    with set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):
        told.append(serve.instructions())
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        told += [
            said("look")[0],
            said("status")[0],
            said("labels")[0],
            said("find", words="Tern")[0],
            said("thread", id=A)[0],
            said("mark", sentence="A label.", anchors=[D])[0],
            said("leave", sentence="A line.", anchors=[D])[0],
            said("find", words="zeppelin")[0],
            said("thread", id="0a0a0a0a")[0],
        ]
    for text in told:
        assert str(tmp_path) not in text and "/Users/" not in text and ".py" not in text and ".jsonl" not in text
        # What a label holds, "what the person tells and asks", is the one sentence where the word is the person's.
        assert "python" not in text.lower() and not re.search(r"\bask(s|ed|ing)?\b", text.replace(store.FOR, ""), re.I)
    # and nothing after the key but, for the first work label after the newest line left at the door, the one
    # sentence that asks for a fresh line, which names no file either
    assert f"marked W2. {door.OVERTAKEN}" in told and "marked N2" in told
    # Nor a shell's way of saying things, in the door's own sentences.
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        own = [
            serve.instructions(),
            json.dumps(serve.TOOLS),
            frame.opening(),
            hook.waking({"cut": 2}),
            said("look")[0],
            said("status")[0],
            said("labels")[0],
            said("labels", kind="relation")[0],
            said("find", words="zeppelin")[0],
        ]
    assert all(" --" not in text and "[id ...]" not in text for text in own)
    assert (
        "From here: labels (by kind, by day or by id), find, thread." in own[4]
        and "labels of the kind relation." in own[6]
    )
    named = re.findall(r"^- (\w+): ", frame.opening(), flags=re.M)
    assert named == ["look", "labels", "find", "thread", "mark", "leave"] and set(named) < set(serve.NAMES)
    assert all(f"`{name}`" in told[0] and f"`{name}`" in told[4] for name in named)
    assert (
        "cut 2 of this session" in told[3]
        and "find, then thread" in told[3]
        and "Do not open the transcript file" in told[3]
    )


def test_a_session_is_told_what_is_kept_by_itself_and_what_is_its_own_to_write(tmp_path):
    """A session has to be told what happens by itself and what does not. Otherwise it may try to
    save the conversation through the door, or wait for labels to appear."""
    crossings, _ = home(tmp_path)
    with set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):  # shipped by the plugin, whose hooks feed the store
        told = serve.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})["result"]["instructions"]
    assert "What is said is kept by itself, up to the moment you call: you never save it." in told
    assert "Labels are not made by themselves" in told and "a cut can come unannounced" in told
    os.environ.pop("CLAUDE_PLUGIN_ROOT", None)  # given to a harness that has no such hooks
    alone = serve.handle({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})["result"]["instructions"]
    assert "Nothing is archived here by itself" in alone and "kept by itself, up to the moment" not in alone
    assert len(told) < 1100 and len(alone) < 1100
    opening = frame.opening()
    assert (
        "What is said is kept by itself; labels and the line at the door are yours to write, as the work goes."
        in opening
    )
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert said("look")[0].startswith(
            "The store in outline: 1 day, 4 messages, 2 labels, 0 struck; kept up to 2026-11-11 09:05 UTC."
        )
        with set_to(CROSSING_OURS=str(tmp_path / "ours")):
            assert said("look", home="ours")[0].startswith(
                "The store in outline: 0 days, 0 messages, 0 labels, 0 struck."
            )


def test_the_plugin_is_named_crossings_and_its_door_tools_by_that_name_everywhere():
    """The plugin is Crossings by its own name. The harness names the door's tools by the plugin's name and
    its server's, so the hooks' matchers and the module's guard name them so too; and what the person is shown
    while a cut is counted or a frame is brought says Crossings. The package, the data folder and the settings
    keep the older singular name, crossing, which is where a person's record and homes lie."""
    plugin = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "crossings", plugin["name"]
    server = next(iter(json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]))
    prefix = f"mcp__plugin_{plugin['name']}_{server}__"
    hooks = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    matchers = [each["matcher"] for event in ("PreToolUse", "PostToolUse") for each in hooks[event]]
    assert matchers and all(matcher.startswith(prefix) for matcher in matchers), matchers
    module = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    assert f"startsWith('{prefix}')" in module and "mcp__plugin_crossing_" not in module
    shown = [
        one["statusMessage"]
        for event in hooks.values()
        for each in event
        for one in each["hooks"]
        if "statusMessage" in one
    ]
    assert shown and all(line.startswith("Crossings · ") for line in shown), shown


def test_each_handle_answers_as_the_door_does(tmp_path):
    rows = ROWS + [row("user", "77777777", 20, "-x marks nothing; a dash begins this message.")]
    crossings, _ = home(tmp_path, rows)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent), CROSSING_OURS=str(tmp_path / "ours")):
        assert said("look")[0].startswith(
            "The store in outline: 1 day, 5 messages, 2 labels, 0 struck; kept up to 2026-11-11 "
        )
        assert said("look", home="ours")[0].startswith("The store in outline: 0 days, 0 messages")
        assert "- W1 (both, 2026-11-11): The hull is to be painted grey in spring." in said("labels")[0]
        assert said("labels", kind="relation", day="2026-11-11", ids=[])[0].startswith(
            "- R1 (his, 2026-11-11): His boat"
        )
        assert said("labels", kind="gossip", day=" ", ids=["w1", 5, " "])[0].startswith("- W1 (both, 2026-11-11)")
        assert f"- `{D}` the person" in said("find", words="painted")[0]
        assert said("find", words="painted", voice="session")[0].count("`") == 0  # only a label holds it then
        assert "`77777777` the person" in said("find", words="-x marks")[0]  # words are words, whatever they begin with
        assert said("find") == ("find needs words.", True) and said("find", words="  ") == ("find needs words.", True)
        three = said("thread", id=D)[0]
        assert "the one you named" in three and f"`{B}`" in three and f"`{E}`" in three
        assert f"`{B}`" not in said("thread", id=D, around=0)[0] and f"`{B}`" in said("thread", id=D, around="many")[0]
        assert f"`{A}`" not in said("thread", id=D, around=-3)[0] and f"`{A}`" in said("thread", id=D, around=True)[0]
        assert said("thread") == ("thread needs an id.", True)
        assert said("thread", id="0a0a0a0a") == ("thread of `0a0a0a0a`: no such message in the store.", False)
        assert said(
            "mark", sentence="The keel is checked every autumn.", anchors=[D], kind="relation", whose="his"
        ) == ("marked R2", False)
        assert said("mark", sentence="The hull again.", anchors=[D, E], kind="gossip", whose="nobody") == (
            "marked W2",
            False,
        )
        assert said("mark", sentence="Both of us.", anchors=[D], whose="both") == ("marked W3", False)
        assert "- W2 (session, 2026-11-11): The hull again." in said("labels")[0] and "- W3 (both," in said("labels")[0]
        assert said("mark", sentence="Resting on nothing.", anchors=["0a0a0a0a"]) == (
            "not marked: no such message in the archive: 0a0a0a0a",
            False,
        )  # a refused label is an answer, not a failure
        assert said("mark", sentence="No anchor.") == ("mark needs a sentence and at least one anchor.", True)
        assert said("mark", sentence=7, anchors=[D]) == ("mark needs a sentence and at least one anchor.", True)
        assert said("leave", anchors=[D]) == ("leave needs a sentence and at least one anchor.", True)
        assert said("leave", sentence="The mooring is next.", anchors=[A], kind="relation", whose="his") == (
            "marked N1",
            False,
        )
        assert (
            "- N1 (session, 2026-11-11): The mooring is next." in said("labels", kind="next")[0]
        )  # a line at the door is the session's
    pulls = [json.loads(line) for line in (crossings / "reached.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [p["verb"] for p in pulls].count("thread") == 5 and ["N1", A] in [
        p["ids"] for p in pulls
    ]  # what was pulled is noted


def test_a_value_that_begins_with_a_dash_is_a_value_and_no_fault(tmp_path):
    """A day, the anchors of a label or the model behind a call go to the door as values whatever they begin
    with: the door answers them as it answers any other, and never with a fault of its command line."""
    crossings, _ = home(tmp_path)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert said("labels", day="--transcript=/x")[0].startswith("No label of that kind or day.")
        assert said("mark", sentence="A line on a dash.", anchors=["--session=abc"]) == (
            "not marked: no such message in the archive: --session=abc",
            False,
        )
        assert said("leave", sentence="A line on a dash.", anchors=["-x", D]) == (
            "not marked: no such message in the archive: -x",
            False,
        )
        assert serve.handed("mark", {}) == [] and serve.asked("labels", {"day": "-1"})[:2] == ["labels", "--day=-1"]


def test_a_fault_is_said_to_the_session_and_never_ends_the_server(tmp_path):
    crossings, _ = home(tmp_path)
    (crossings / "store.db").write_text("this is not a database", encoding="utf-8")
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        # A store.db that is no database is read as none: the index is made in memory, and the door answers (S11).
        assert said("status") == (
            "The store holds 2 messages of the person's and 2 of the session's (189 characters, "
            "2026-11-11 to 2026-11-11), 2 labels, and 0 struck.",
            False,
        )
        assert (crossings / "store.db").read_text(
            encoding="utf-8"
        ) == "this is not a database"  # and a read writes none
        was = serve.door.answer
        serve.door.answer = lambda *_: 1 / 0  # a fault inside the door
        try:
            assert said("status") == ("The door could not answer: ZeroDivisionError.", True)
        finally:
            serve.door.answer = was
        answer = serve.handle(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "look", "arguments": "none"}}
        )
        assert answer["result"]["isError"] is True
    assert (
        serve.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": "odd"})["result"]["tools"]
        == serve.TOOLS
    )
    assert serve.handle({"jsonrpc": "2.0", "id": 3})["error"]["code"] == -32601  # no method at all


def test_a_home_may_be_named_outright_for_a_harness_with_no_project(tmp_path):
    crossings, _ = home(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    before = os.getcwd()
    os.chdir(elsewhere)
    try:
        with set_to(CROSSING_HOME=str(crossings)):
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
            assert said("status") == (
                "Crossings is not switched on for this project.",
                True,
            )  # named, and not switched on (S3)
            store.consent(elsewhere)  # as `switch on` keeps it, while the setting stands
            assert "2 messages of the person's" in said("status")[0]
            assert said("mark", sentence="Marked from nowhere in particular.", anchors=[D]) == ("marked W2", False)
    finally:
        os.chdir(before)
    assert "| W2 | Marked from nowhere in particular." in (crossings / "labels").glob("*.md").__next__().read_text(
        encoding="utf-8"
    )
    assert not (elsewhere / "crossings").exists()


@in_person
def test_the_archive_is_brought_up_to_the_moment_before_the_door_is_used(tmp_path):
    """A server is not told which session is calling, so it cannot read a transcript. In Claude
    Code a hook wired to the door's tools alone does it, a moment before the door answers."""
    crossings, path = home(tmp_path)
    wired = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]["PreToolUse"]
    assert [g["matcher"] for g in wired] == ["mcp__plugin_crossings_door__.*"]
    later = row("user", "99999999", 30, "Said a moment before the door was used.")
    path.write_text(path.read_text(encoding="utf-8") + json.dumps(later) + "\n", encoding="utf-8")
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__plugin_crossings_door__find",
        "transcript_path": str(path),
        "cwd": str(tmp_path),
        "session_id": "session-0001",
    }
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        assert "`99999999`" not in said("find", words="moment")[0]  # the server alone does not know of it
        assert hook.run(event) is None
        assert "`99999999` the person" in said("find", words="moment")[0]
        built = (crossings / "store.db").stat().st_mtime_ns
        assert (
            hook.run(event) is None and (crossings / "store.db").stat().st_mtime_ns == built
        )  # nothing new: nothing rebuilt
        assert hook.run({**event, "transcript_path": str(tmp_path / "gone.jsonl")}) is None
        (crossings / "switch").write_text("off\n", encoding="utf-8")
        more = row("user", "88888888", 31, "Said while Crossings was switched off.")
        path.write_text(path.read_text(encoding="utf-8") + json.dumps(more) + "\n", encoding="utf-8")
        hook.run(event)
        assert "88888888" not in said("find", words="switched")[0]


def test_a_line_left_at_the_door_is_to_say_what_the_work_is_for(tmp_path):
    """Guard: a line at the door that says where things stand and what is open, and no more, hands the session
    that wakes a next step and no reason for it; across several cuts that makes a session that carries work on
    with no word of what it is for. The tool says to leave that too, and to rest the line on the message where
    the person said it, since a frame carries the person's words that its line at the door rests on. The tool
    stays as small as it was held to be."""
    leave = next(each for each in serve.TOOLS if each["name"] == "leave")["description"]
    assert "where things stand, what is open and what the work is for" in leave
    assert "among them the message where the person said what for" in leave and len(leave) < 400
    crossings, _ = home(tmp_path)
    store.mark(crossings, "next", "session", "The hull is painted grey because the old paint peels.", [D])
    carried = frame.compose(crossings)
    assert f"- `{D}`: We paint the hull grey in spring" in carried  # their words, beside the line that rests on them


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
