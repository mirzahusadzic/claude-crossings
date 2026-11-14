#!/usr/bin/env python3
"""The door as a server: the same handles over MCP's stdio, for any harness that can be given one.

  python3 -I crossing/serve.py

A session calls the door's handles as tools and never sees a file's path or a shell command:
what was said is to be reached through the door because that is the easiest way, and nothing
here points a hand at the file system. The server answers from the home of the project it was
started for (`CLAUDE_PROJECT_DIR`, else the directory it runs in), or from the folder
`CROSSING_HOME` names, as a harness without projects would set it. Where that project has no
home the person switched on, Crossings was never switched on there: every handle says so in
one sentence and makes nothing, and so does every handle asked of the home on this computer
(`home: ours`): it is offered only to a project where Crossings is switched on and on. Where a
setting of the plugin's names a place inside the project, a handle says that in one sentence
and nothing is followed. Where a file of the home is a link, a handle says that in one
sentence, and nothing is written. Switching Crossings on is the person's to do, and no handle
here does it. A session no person sits in (see record.attended) is answered in one sentence by
every handle, and nothing is read for it.

A server is not told which session is calling, so it never reads a transcript. Keeping the
archive up to date is a hook's work (crossing/hook.py, before each call of these tools); a
harness without hooks has the labels and the lines left at the door, and no archive. Nor is it
told which model calls: the hook before a call of `mark` hands that over in the home, by the
call's digest, and the server takes it (crossing/layer.py). Where none was handed over, the
model is not known, and nothing is layered.

The protocol is spoken by hand, one JSON object a line. Standard library only. No model is
called.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import door, layer, record, store  # noqa: E402

VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")  # the newest first; a client is answered in its own if known
# What a session is told of the door when it starts, with or without a frame. It names the
# handles that exist and no other, and it says what happens by itself and what does not:
# nothing else tells a session that the archive keeps itself and that labels do not.
KEPT = (
    "What is said is kept by itself, up to the moment you call: you never save it. Labels are not made by "
    "themselves: `mark` them as the work goes, and `leave` a line for the session that wakes after the next "
    "cut, since a cut can come unannounced. Lines can be stacked into fewer: `mark` a label that rests on "
    "them, and the frame then carries the one. The person is shown a line you leave, and a label about the "
    "two of you or one that speaks for them, as you write it. "
)
BARE = (
    "Nothing is archived here by itself: this harness has no hook that feeds the store, so it holds what was "
    "archived elsewhere. `mark` writes a label and `leave` a line for the session that comes next. "
)


def instructions() -> str:
    """The plugin's hooks are what feed the archive. Started by the plugin, the server can say
    so; given alone to another harness, it must not."""
    return (
        "The door to what you and the person said in this project, kept word for word under ids, with the labels "
        "that rest on it. "
        + (KEPT if os.environ.get("CLAUDE_PLUGIN_ROOT") else BARE)
        + "After a cut, reach here for what your context no longer holds: `look` shows the room and needs no word; "
        "`labels`, `find` and `thread` go on from there. Reach when the conversation calls for it, never to show "
        "that something is held. What the person told you in confidence is left alone until they bring it up; "
        "where you cannot tell whether something was said in confidence, treat it as if it was."
    )


HOME = {
    "type": "string",
    "enum": ["here", "ours"],
    "description": "This project's store (default), or the one on this computer.",
}
IDS = {"type": "array", "items": {"type": "string"}}


def tool(name: str, description: str, required: tuple = (), **properties) -> dict:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": {**properties, "home": HOME}, "required": list(required)},
        # seven small handles, to be in front of a session and not searched for
        "_meta": {"anthropic/alwaysLoad": True},
    }


TOOLS = [
    tool(
        "look",
        "The room, with no word needed: the days, the kinds of label, the newest labels about the work, and "
        "the line left at the door. Start here after a cut.",
    ),
    tool(
        "labels",
        "The labels themselves, newest first: by kind, by day, or whole by id, a stack with the lines "
        "beneath it. With nothing named, the labels about the work.",
        ids={**IDS, "description": "Label ids to give whole, as R3 or W12."},
        kind={
            "type": "string",
            "enum": ["relation", "work", "next"],
            "description": "Only that kind: relation (standing, about the two of you), work, or next "
            "(lines left at the door).",
        },
        day={"type": "string", "description": "Only those of one day, as 2026-11-11."},
    ),
    tool(
        "find",
        "Words, to the messages and labels that hold them, each by its id. Word stems, `word*` and "
        '"a phrase" are taken; a miss names the nearest words that are there.',
        ("words",),
        words={"type": "string", "description": "The words to look for: all of them, or failing that any."},
        voice={
            "type": "string",
            "enum": ["his", "session"],
            "description": "Only the person's messages, or only the session's.",
        },
    ),
    tool(
        "thread",
        "A message in its place, by its id: what stood before and after it, and the labels resting there.",
        ("id",),
        id={"type": "string", "description": "The id of a message, as find gives it."},
        around={
            "type": "integer",
            "description": "How many messages before and after to show (default 2, at most 50).",
        },
    ),
    tool(
        "mark",
        "Write a label: one sentence about a stretch of the record, resting on the ids of messages. An id "
        "the archive does not hold is refused. The ids may also be labels of the same kind, which stacks "
        "them beneath this one. " + store.FOR,
        ("sentence", "anchors"),
        sentence={"type": "string", "description": "The label, one sentence."},
        anchors={**IDS, "description": "The ids it rests on: messages, or labels of its kind."},
        kind={
            "type": "string",
            "enum": ["relation", "work"],
            "description": "About the two of you, or about the work (default).",
        },
        whose={
            "type": "string",
            "enum": ["his", "session", "both"],
            "description": "Whose the labelled thing is (default: the session's).",
        },
    ),
    tool(
        "leave",
        "Leave a line of your own for the session that wakes after the next cut: a few sentences on where "
        "things stand and what is open, resting on ids like a label. Only the newest is carried, at the top of "
        "the frame. " + store.FOR,
        ("sentence", "anchors"),
        sentence={"type": "string", "description": "The line, in your own words."},
        anchors={**IDS, "description": "The ids of the messages it rests on."},
    ),
    tool("status", "What the store holds, in one line."),
]
NAMES = [t["name"] for t in TOOLS]


def project() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())


def asked(name: str, given: dict) -> list[str] | str:
    """The door's own command line for a call, or the plain sentence that refuses it."""
    strings = lambda value: [v for v in value if isinstance(v, str) and v.strip()] if isinstance(value, list) else []  # noqa: E731
    said = given.get("sentence") if isinstance(given.get("sentence"), str) else ""
    if name == "labels":
        argv = ["labels"]
        if given.get("kind") in ("relation", "work", "next"):
            argv += ["--kind", given["kind"]]
        if isinstance(given.get("day"), str) and given["day"].strip():
            argv += ["--day", given["day"].strip()]
        return argv + ["--", *strings(given.get("ids"))]
    if name == "find":
        if not (isinstance(given.get("words"), str) and given["words"].strip()):
            return "find needs words."
        return (
            ["find"]
            + (["--voice", given["voice"]] if given.get("voice") in ("his", "session") else [])
            + ["--", given["words"]]
        )
    if name == "thread":
        if not (isinstance(given.get("id"), str) and given["id"].strip()):
            return "thread needs an id."
        around = (
            given.get("around")
            if isinstance(given.get("around"), int) and not isinstance(given.get("around"), bool)
            else 2
        )
        return ["thread", "--around", str(max(0, min(around, store.AROUND))), "--touch", "--", given["id"].strip()]
    if name in ("mark", "leave"):
        if not said.strip() or not strings(given.get("anchors")):
            return f"{name} needs a sentence and at least one anchor."
        # A line left at the door is the session's own, whatever else is said of it.
        kind = "next" if name == "leave" else "relation" if given.get("kind") == "relation" else "work"
        whose = "session" if name == "leave" or given.get("whose") not in ("his", "both") else given["whose"]
        return [
            "mark",
            "--kind",
            kind,
            "--whose",
            whose,
            "--anchors",
            ",".join(strings(given.get("anchors"))),
            "--touch",
            "--",
            said,
        ]
    return [name]  # look, status


def handed(name: str, given: dict) -> list[str]:
    """The model behind a call of `mark`, as the hook before the call handed it over in the
    project's home (see crossing/layer.py), for the door to scope the stack to: this server is
    told neither the session nor the model. Nothing where none was handed over."""
    folder = store.kept(project()) if name == "mark" else None
    model = layer.handed(folder, name, given) if folder is not None else ""
    return ["--model", model] if model else []


UNATTENDED = "The door is for sessions a person sits in, and this one is not, so nothing was read."


def call(name: str, given: dict) -> tuple[str, bool]:
    """A handle's answer as text, and whether it is a failure. A refused label is an answer;
    a project where Crossings was never switched on is a failure, said before anything is read,
    and so is the home on this computer asked of from such a project, or from one switched off.

    A session no person sits in is answered in one sentence, and nothing is read: the server
    learns it as the hooks do, from CLAUDE_CODE_ENTRYPOINT in its own environment, which the
    harness hands every server it starts as it hands its hooks (see record.attended)."""
    if not record.attended():
        return UNATTENDED, True
    ours = given.get("home") == "ours"
    stray = record.astray(project())
    if stray:
        return door.strayed(stray), True
    if (store.offered(project()) if ours else store.kept(project())) is None:
        return door.NOT_ON, True
    argv = asked(name, given)
    if isinstance(argv, str):
        return argv, True
    try:
        model = handed(name, given)
    except record.Linked as err:  # as the door says it: nothing is read or written through a link
        record.refused(err)
        return door.LINKED, False
    split = argv.index("--") if "--" in argv else len(argv)
    argv[split:split] = ["--bare", "--cwd", str(project())] + (["--home", "ours"] if ours else []) + model
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = door.main(argv, served=True)
    return out.getvalue().strip() or "Nothing came back.", code != 0 and name not in ("mark", "leave")


def handle(request: dict) -> dict | None:
    identifier, method, params = request.get("id"), request.get("method"), request.get("params")
    params = params if isinstance(params, dict) else {}
    if method == "initialize":
        wanted = params.get("protocolVersion")
        result = {
            "protocolVersion": wanted if wanted in VERSIONS else VERSIONS[0],
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "door", "title": "The Crossings door", "version": "1"},
            "instructions": instructions(),
        }
    elif isinstance(method, str) and method.startswith("notifications/"):
        return None
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call" and params.get("name") in NAMES:
        given = params.get("arguments")
        try:
            text, failed = call(params["name"], given if isinstance(given, dict) else {})
        except (Exception, SystemExit) as err:  # a fault is said to the session; it never ends the server
            text, failed = f"The door could not answer: {type(err).__name__}.", True
        result = {"content": [{"type": "text", "text": text}], "isError": failed}
    elif method == "tools/call":
        return {
            "jsonrpc": "2.0",
            "id": identifier,
            "error": {"code": -32602, "message": f"The door has these handles: {', '.join(NAMES)}."},
        }
    else:
        return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": identifier, "result": result}


def main() -> int:
    record.private()  # what the door writes is its owner's alone
    for line in sys.stdin:
        try:
            request = json.loads(line)
        except ValueError:
            continue
        answer = handle(request) if isinstance(request, dict) else None
        if answer is not None:
            sys.stdout.write(json.dumps(answer, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
