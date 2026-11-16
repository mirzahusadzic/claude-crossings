"""Everything Crossings can tell a session, as one page, in the order a session meets it.

Each piece was written and reviewed on its own, and what they do together can be seen only when they
are read together, as the session reads them: what all of it leans a model toward, how it reads on its
words alone, without the intent that wrote it, and which of it is scaffolding that can retire and which
a guard that must stay. The second is asked of the words and not of a reader: a sentence that slips in
is written in good faith, by authors who read it through what they meant. The page is made from a
made-up store, by the tests' own means (tests/test_store.py makes the store in a temporary folder of
its own, and keeps the run from the person's own home); no model is called and nothing opens a
connection.

The page is kept as docs/told.md, and tests/test_told.py holds that it is the page this script makes
and that no sentence the plugin hands a session is missing from it: after changing any such sentence,
make the page again, never by hand. Between two releases, `git diff vX..vY -- docs/told.md` is what a
session is told now that it was not before.

    python3 scripts/told.py > docs/told.md
"""

from __future__ import annotations

import ast
import contextlib
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
from test_store import DATA, D, E, home, started_by  # noqa: E402  (and its data folder: nothing reaches the real home)

from crossing import door, frame, hook, serve, store  # noqa: E402

DAY = "2026-11-12"  # the day of the made-up labels, so that the page is the same on every run


def module_said(name: str) -> str:
    """One sentence of the hooks module's own, by the name of its constant: its string, as hooks/crossings.ts
    writes it on the lines after the name, its pieces joined."""
    source = (ROOT / "hooks" / "crossings.ts").read_text(encoding="utf-8")
    held = re.search(rf"^const {name} =\n((?:  .*\n)+)", source, flags=re.M)
    if held is None:
        raise SystemExit(f"hooks/crossings.ts holds no {name}: the page cannot say what the module tells a session")
    return "".join(a or b for a, b in re.findall(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"", held.group(1)))


def module_note() -> str:
    """The hooks module's own note for a hand-over page carried in a frame's place."""
    return module_said("NOTE")


# What the hooks module answers a session's call with as it refuses it: the archive's own files, the person's
# own verbs, and the files of a home that the door alone writes.
MODULE_REFUSES = ("REFUSED", "PERSONS", "WRITTEN")


def shared() -> str:
    """What the door answers `thread` for an id two messages share, as its source writes it, with an ellipsis
    where it names an id or a number."""
    tree = ast.parse((ROOT / "crossing" / "door.py").read_text(encoding="utf-8"))
    for each in ast.walk(tree):
        if isinstance(each, ast.JoinedStr):
            said = "".join(part.value if isinstance(part, ast.Constant) else "…" for part in each.values)
            if "messages are named" in said:
                return said.strip()
    raise SystemExit("crossing/door.py no longer says what thread answers for an id two messages share")


def tools() -> str:
    """Each of the server's tools, with its description and the description of each thing it takes."""
    lines = []
    for each in serve.TOOLS:
        lines.append(f"- **{each['name']}**: {each['description']}")
        for name, given in each.get("inputSchema", {}).get("properties", {}).items():
            if given.get("description"):
                lines.append(f"  - `{name}`: {given['description']}")
    return "\n".join(lines)


def answered(project: Path) -> str:
    """What the server answers to each tool, from the made-up store, as a session reads it."""
    calls = [
        ("look", {}),
        ("status", {}),
        ("labels", {}),
        ("find", {"words": "hull"}),
        ("find", {"words": "zeppelin"}),
        ("thread", {"id": D}),
        ("thread", {"id": "ffffffff"}),
        ("labels", {"ids": ["W99"]}),
        ("leave", {"sentence": "The paint is the next thing to settle.", "anchors": [D]}),
        # the first label about the work marked after a line at the door: the answer says the line may be overtaken
        ("mark", {"sentence": "The paint is to be bought before spring.", "anchors": [D]}),
        ("mark", {"sentence": "The brushes are bought.", "anchors": [D]}),  # and the next one does not
        ("mark", {"sentence": "", "anchors": []}),
        ("mark", {"sentence": "The keel is sound.", "anchors": ["ffffffff"]}),
    ]
    out = []
    with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=str(project)):
        for name, given in calls:
            text, _ = serve.call(name, given)
            out.append(f"### `{name}` {json.dumps(given, ensure_ascii=False)}\n\n{fenced(text)}")
    return "\n\n".join(out)


# The functions of the store that refuse a mark or a line left at the door, each with a sentence of its own.
REFUSING = ("mark", "_unmarked", "_unstackable", "_scoped")


def refusals() -> list[str]:
    """Each sentence a mark, or a line left at the door, can be refused with, as the store's refusing functions
    write them (REFUSING): gathered from their source, in its order, with an ellipsis where a sentence names a
    key, an id or a model. A session meets them after `not marked: `. One made of fewer than three words, or a
    query of the index, is none of them."""
    tree = ast.parse((ROOT / "crossing" / "store.py").read_text(encoding="utf-8"))
    found: list[str] = []
    for node in tree.body:
        if not (isinstance(node, ast.FunctionDef) and node.name in REFUSING):
            continue
        docs = ast.get_docstring(node, clean=False)
        inside = {id(part) for each in ast.walk(node) if isinstance(each, ast.JoinedStr) for part in each.values}
        for each in ast.walk(node):
            if isinstance(each, ast.JoinedStr):
                said = "".join(part.value if isinstance(part, ast.Constant) else "…" for part in each.values)
            elif isinstance(each, ast.Constant) and isinstance(each.value, str) and id(each) not in inside:
                said = each.value
            else:
                continue
            if said != docs and len(said.split()) >= 3 and not said.lower().lstrip().startswith("select "):
                found.append(said.strip())
    return list(dict.fromkeys([*found, store.UNTEXT, store.BUSY.format("marked")]))


def fenced(text: str) -> str:
    return f"````text\n{text}\n````"


def below() -> str:
    """What a session is told as it starts in a folder below another home's folder (see store.waiting)."""
    top = Path(tempfile.mkdtemp(prefix="told-", dir=DATA)) / "tern"
    (top / ".git").mkdir(parents=True)
    (top / "crossings").mkdir()
    store.switch(top, "on")
    paper = top / "papers" / "paper"
    paper.mkdir(parents=True)
    with started_by("cli"):
        made = json.loads(hook.below(paper))
    return made["hookSpecificOutput"]["additionalContext"]


def by_count() -> str:
    """The frame a session is given where the keys of a page written by hand would take it past what a hook may
    carry (frame.MOST): made again with the sentences that name labels outside their own lines saying how many
    they are (see frame.compose). Shown at the least size, with a long line at the door, so that each of those
    sentences is in it; made with the frame's own composition, as compose makes it in that case."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    line = "The paint is to be bought before the yard closes, and the hull scraped first. " * 20
    store.mark(crossings, "next", "session", line.strip(), [D], day=DAY)
    store.mark(crossings, "work", "session", "The scraper is borrowed.", [E], day=DAY)
    unheld = "| W9 | A row whose message the archive never held. | both | `0a0a0a0a` |\n"
    with open(crossings / "labels" / f"{DAY}.md", "a", encoding="utf-8") as handle:
        handle.write(unheld)
    store.build(crossings)
    return frame._composed(crossings, frame.LEAST, False, "", by_count=True)


def page() -> str:
    """The page: every sentence Crossings can tell a session, in the order a session meets them."""
    # A project switched on, with a hand-over page and a made-up transcript archived; then a line left at the
    # door, work marked after it, a stack whose line was written again by hand since (misaligned), a row resting
    # on what the archive never held (unresolved), and a label of another model's: each a sentence of the frame.
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    project = crossings.parent
    store.mark(crossings, "next", "session", "Find out whether the grey paint has been bought.", [D], day=DAY)
    paint = store.mark(crossings, "work", "session", "The grey paint is chosen; the hull waits.", [E], day=DAY)
    mast = store.mark(crossings, "work", "session", "The mast is stepped after the paint.", [D], day=DAY)
    store.mark(crossings, "work", "session", "The spring work, in its order.", [paint["id"], mast["id"]], day=DAY)
    page_ = crossings / "labels" / f"{DAY}.md"
    written = page_.read_text(encoding="utf-8").replace("The mast is stepped after the paint.", "The mast waits.")
    unheld = "| W9 | A row whose message the archive never held. | both | `0a0a0a0a` |\n"
    page_.write_text(written + unheld, encoding="utf-8")
    store.build(crossings)
    store.mark(crossings, "work", "session", "The tiller is to be varnished.", [D], day=DAY, model="another-model")
    with set_to(CLAUDE_PLUGIN_ROOT=str(ROOT)):
        started = serve.instructions()
    alone = serve.instructions()
    parts = [
        "# What a session is told",
        "Everything Crossings can tell a session, in the order a session meets it: made by `scripts/told.py` from a "
        "made-up store, never by hand. Read it whole, as a session receives it, and ask of all of it together: what "
        "does it lean the model toward; how does it read on its words alone, without the intent that wrote it; which "
        "of it is scaffolding that can retire, and which a guard that must stay. Between two releases, `git diff` of "
        "this page is what a session is told now that it was not before.",
        "## As a session starts: the door's server",
        "### Its instructions, started by the plugin\n\n" + fenced(started),
        "### Its instructions, given alone to another harness\n\n" + fenced(alone),
        "### Its tools\n\n" + tools(),
        "## As a session starts in a home that holds no label yet, or as the person switches Crossings on during it\n\n"
        + fenced(hook.welcome()),
        "## A session started new, in a home that holds labels: its frame\n\n"
        + fenced(frame.compose(crossings, new=True)),
        "## After a cut: the waking note\n\n" + fenced(hook.waking({"cut": 2})),
        "## After a cut: the frame\n\n" + fenced(frame.compose(crossings)),
        "## After a cut, the frame at the least size a home may set\n\n"
        + fenced(frame.compose(crossings, frame.LEAST)),
        "## After a cut, where a page written by hand holds keys that would take the frame past what a hook may "
        "carry: the frame names labels by count\n\n" + fenced(by_count()),
        "## After a cut where no frame can be made: the hooks module's note before the hand-over page\n\n"
        + fenced(module_note()),
        "## After a cut, in a home where other models made lines\n\n"
        + fenced(frame.compose(crossings, model="a-made-up-model")),
        "## As the person switches Crossings off during a session, and on again\n\n"
        + fenced(hook.unkept())
        + "\n\n"
        + fenced(hook.kept_again()),
        "## As another model comes into the session\n\n" + fenced(hook.arrival()),
        "## A session resumed where another worked since it last spoke\n\n" + fenced(hook.moved_on()),
        "## A session that starts in a folder below another home's folder\n\n" + fenced(below()),
        "## What the door's tools answer, from the made-up store\n\n" + answered(project),
        "## What a mark, or a line left at the door, can be refused with\n\n"
        "Each follows `not marked: `; an ellipsis stands where the sentence names a key, an id or a model.\n\n"
        + fenced("\n".join(refusals())),
        "## What the hooks module says as it refuses a session's call\n\n"
        + "\n\n".join(fenced(module_said(name)) for name in MODULE_REFUSES),
        "## What `thread` answers for an id two messages share\n\n" + fenced(shared()),
        "## What the door says in place of an answer\n\n"
        + "\n\n".join(
            fenced(text)
            for text in (
                serve.UNATTENDED,
                door.NOT_ON,
                door.BELOW_BARE,
                door.PERSONS,
                door.UNSEATED,
            )
        ),
    ]
    return "\n\n".join(parts) + "\n"


if __name__ == "__main__":
    os.environ.pop("CLAUDE_PLUGIN_ROOT", None)  # the page says which instructions hold with it, and which without
    with contextlib.redirect_stderr(sys.stderr):
        sys.stdout.write(page())
