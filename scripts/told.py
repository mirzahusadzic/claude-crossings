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
from test_store import DATA, ROWS, A, B, D, E, home, row, started_by  # noqa: E402  (and its data folder: nothing reaches the real home)  # noqa: E402  (the made-up store's messages, and one made of a row)

from crossing import door, frame, hook, layer, off, serve, store  # noqa: E402

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


# What the hooks module hands the harness's summarizer as its instructions at a cut, and the line the page says it with.
LEDGER_HEAD = "## As a cut is made: what the harness's summary is asked for"
LEDGER_TOLD = (
    "Told to the harness's summarizer, not to the session: as its instructions, wherever the harness makes a summary "
    "in a project whose cuts Crossings answers (the mode `beside` or `own`), at the cut and ahead of it alike. Not for "
    "a subagent's own cut, not in a session no person sits in, and not where a message was to carry the frame and "
    "the door gave none. What the person typed after `/compact` follows it after an empty line, unchanged."
)


def ledger() -> str:
    """The section of the page that says what the summary of a cut is asked for (`LEDGER` in hooks/crossings.ts)."""
    return f"{LEDGER_HEAD}\n\n{LEDGER_TOLD}\n\n" + fenced(module_said("LEDGER"))


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
        ("find", {"words": "moring"}),  # a miss beside a word that is there: the nearest words are named
        ("find", {"words": ""}),
        ("thread", {"id": ""}),
        ("thread", {"id": D}),
        ("thread", {"id": "ffffffff"}),
        ("thread", {"id": D, "role": "pair:them"}),  # by the person's id: the pair the person's turn heads
        ("thread", {"id": E, "role": "pair:me"}),  # by the session's id: the pair its turn heads, the session's last
        ("thread", {"id": A, "role": "pair:me"}),  # the person's first turn answers no turn of the session's: no pair
        ("thread", {"id": D, "role": "pair"}),  # a role that is neither of the two is refused
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


# A long message of the person's, of the made-up store's kind, that `find` shows in part.
LONG = (
    "First the old paint comes off the hull, plank by plank, and the seams are looked at as it goes. " * 4
    + "Then the keel is checked for the varnish. "
    + "After that the hull is washed, left to dry for a week, and painted grey in two coats. " * 4
)


def excerpted() -> str:
    """What `find` answers through the server where it shows a message in part: a long one, found by a word in its
    middle."""
    rows = [*ROWS, row("user", "f0f0f0f0", 9, LONG)]
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)), rows=rows)
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)), started_by("cli"):
        return serve.call("find", {"words": "varnish"})[0]


# What the section of long lines and labels says before its calls.
LONG_TOLD = (
    "Through the server the plugin started, whose hook after the call shows the person, under the turn, a standing "
    "line, a label that speaks for them and every line left at the door, each cut at 160 characters."
)


def long_marked() -> str:
    """What the server answers where a line left at the door, and then a label about the work, come in long: each is
    written whole, and the answer says how long it is, before the sentence it adds otherwise; and where a standing
    line and a label of the person's do, which the person is shown, from 160 characters (store.SHOWN). In a home of
    its own, the made-up store, with a line of over 900 characters, a label of the session's of over 240 (door.TENTH,
    door.SHORT), a standing line of between 160 and 240, and a label of the person's of over 240."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    line = (
        "The hull is scraped plank by plank, the seams are looked at as it goes, and the paint waits for a dry week. "
    )
    label = "The grey paint is chosen for the hull, two coats of it, once the old paint is off. "
    standing = "The person keeps the boat's papers in the chart table and wants them left where they are. "
    theirs = "The person wants the mast stepped only once the paint is dry, whatever the forecast says. "
    calls = (
        ("leave", "a line", line * 10, {}),
        ("mark", "a label", label * 4, {}),
        ("mark", "a standing line", standing * 2, {"kind": "relation"}),
        ("mark", "a label of the person's", theirs * 3, {"whose": "their"}),
    )
    out = [LONG_TOLD]
    with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=str(crossings.parent), CLAUDE_PLUGIN_ROOT=str(ROOT)):
        for name, what, sentence, more in calls:
            text, _ = serve.call(name, {"sentence": sentence.strip(), "anchors": [D], **more})
            out.append(f"### `{name}`, with {what} of {len(sentence.strip()):,} characters\n\n{fenced(text)}")
    return "\n\n".join(out)


def at_rest_elsewhere() -> str:
    """What `look`, `labels` and `status` say through the server of a refusal that a session's own silencing, written
    under another model, puts to rest for that model alone: it stands for the model that asks, and they say so."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    here, other = "a-made-up-model", "another-made-up-model"
    store.mark(crossings, "refused", "session", "The mast is not stepped before the paint.", [D], day=DAY, model=here)
    put_to_rest = "The paint is on, so the mast can go up."
    store.mark(crossings, "silenced", "session", put_to_rest, ["X1", E], day=DAY, model=other)
    layer.arrive(crossings, "session-", here)  # the session that spoke last, which the server asks for, runs `here`
    with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)), started_by("cli"):
        looked, listed, status = (serve.call(name, given)[0] for name, given in (
            ("look", {}), ("labels", {"ids": ["X1"]}), ("status", {}),
        ))  # fmt: skip
    counted = next(line for line in looked.split("\n") if line.startswith("Labels: "))
    return "\n\n".join(fenced(each) for each in (counted, listed, status))


def alone_elsewhere() -> str:
    """What `look`, `labels` and `status` say through the server of a refusal that is another model's alone, first
    where it stands there, then where that model's session put it to rest: the frame for the model that asks
    carries nothing of it, and they count it neither standing nor silenced."""
    here, other = "a-made-up-model", "another-made-up-model"
    shown = []
    for at_rest in (False, True):
        crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
        refused = "The mast is not stepped before the paint."
        store.mark(crossings, "refused", "session", refused, [D], day=DAY, model=other)
        if at_rest:
            put_to_rest = "The paint is on, so the mast can go up."
            store.mark(crossings, "silenced", "session", put_to_rest, ["X1", E], day=DAY, model=other)
        layer.arrive(crossings, "session-", here)  # the session that spoke last, which the server asks for
        with set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)), started_by("cli"):
            looked, listed, status = (serve.call(name, given)[0] for name, given in (
                ("look", {}), ("labels", {"ids": ["X1"]}), ("status", {}),
            ))  # fmt: skip
        shown += [next(line for line in looked.split("\n") if line.startswith("Labels: ")), listed, status]
    return "\n\n".join(fenced(each) for each in shown)


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


def said_by_server(words: str) -> str:
    """One sentence the door's server builds as it answers, found in its source by words it holds, with an
    ellipsis where it names what it was given."""
    tree = ast.parse((ROOT / "crossing" / "serve.py").read_text(encoding="utf-8"))
    for each in ast.walk(tree):
        if isinstance(each, ast.JoinedStr):
            said = "".join(part.value if isinstance(part, ast.Constant) else "…" for part in each.values)
            if words in said:
                return said.strip()
    raise SystemExit(f"crossing/serve.py no longer says: {words}")


# The two sentences the server answers with where it could not run a call, or was asked for a tool it has not.
SERVER_REFUSES = ("The door could not answer", "The door has these handles")


def off_and_on() -> tuple[str, str]:
    """What a session's mark is answered while the person has Crossings switched off, and how the room looks
    once it is on again: the span off the record has a line of its own. In a home of its own, with a clock that
    reads the made-up store's morning, so that the page is the same on every run."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    project = crossings.parent
    reads = iter(("2026-11-11T09:10:00.000000+00:00", "2026-11-11T09:30:00.000000+00:00"))
    was = off.now
    off.now = lambda: next(reads)
    try:
        with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=str(project)):
            store.switch(project, "off")
            refused, _ = serve.call("mark", {"sentence": "The paint is bought.", "anchors": [D]})
            store.switch(project, "on")
            room, _ = serve.call("look", {})
    finally:
        off.now = was
    return refused, room


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
    """The frame a session is given where the keys of a page written by hand would take it past its size: made
    again with the sentences that name labels outside their own lines saying how many they are (see
    frame.compose). Shown at the least size, with a long line at the door, so that each of those sentences is in
    it; made with the frame's own composition, as compose makes it in that case."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    line = "The paint is to be bought before the yard closes, and the hull scraped first. " * 20
    store.mark(crossings, "next", "session", line.strip(), [D], day=DAY)
    store.mark(crossings, "work", "session", "The scraper is borrowed.", [E], day=DAY)
    unheld = "| W9 | A row whose message the archive never held. | both | `0a0a0a0a` |\n"
    with open(crossings / "labels" / f"{DAY}.md", "a", encoding="utf-8") as handle:
        handle.write(unheld)
    store.build(crossings)
    return frame._composed(crossings, frame.LEAST, False, "", by_count=True)


def few_named() -> str:
    """The frame a session is given at the least size where more models made lines than the frame has room to name:
    the sentence about their lines says only how many they are (see frame._made). In a home of its own, the made-up
    store with a line at the door and eight labels each marked by a made-up model of a long name."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    store.mark(crossings, "next", "session", "Find out whether the grey paint has been bought.", [D], day=DAY)
    for n in range(1, 9):
        name = f"made-up-model-{n}-of-a-long-name-" + "x" * 40
        store.mark(crossings, "work", "session", f"The paint for coat {n} is mixed.", [E], day=DAY, model=name)
    return frame.compose(crossings, frame.LEAST, model="a-made-up-model")


def cut_session(crossings: Path) -> str:
    """The made-up home's one session, as the archive names it: a cut's frame is asked for by session, and it is
    that frame that is laid out with each sentence of the person's packed with what was told of it."""
    db = store._open(crossings)
    try:
        return db.execute("select session from said where session != '' order by seq limit 1").fetchone()[0]
    finally:
        db.close()


def nesting() -> str:
    """What `crossing` gives where the line at the door rests on both ends of a sentence of the person's: the cut's
    frame, with the session's turns set beside that sentence, and after it, apart, the sentence of what those turns
    take. In a home of its own, the made-up store with a line at the door on the person's message (D) and on the
    session's message on each side of it (B, E); no other file is written."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    store.mark(crossings, "next", "session", "Find out whether the grey paint has been bought.", [B, D, E], day=DAY)
    with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        text, _ = serve.call("crossing", {})
    return text


def standing() -> str:
    """What `crossing` gives where a standing line carried in the frame, not the person's, rests on both ends of a
    sentence of the person's, and where a stack does through a line beneath it: the cut's frame, with those turns set
    beside the sentences, keyed by the line and by the stack, and after it, apart, the sentence of what they take. In
    a home of its own, the made-up store with a line at the door on the person's message (D) alone; a standing line on
    D and the session's answer to it (E); and a line on the person's first message (A) and the session's answer (B),
    beneath a stack. The store's own standing line of the person's on A and B sets nothing; no other file is
    written."""
    crossings, _ = home(Path(tempfile.mkdtemp(prefix="told-", dir=DATA)))
    store.mark(crossings, "next", "session", "Find out whether the grey paint has been bought.", [D], day=DAY)
    store.mark(crossings, "relation", "both", "The person plans the boat's work by the seasons.", [D, E], day=DAY)
    name = "The boat's name and mooring are kept to hand."
    kept = store.mark(crossings, "relation", "session", name, [A, B], day=DAY)
    store.mark(crossings, "relation", "session", "What the session holds of the boat.", [kept["id"]], day=DAY)
    with started_by("cli"), set_to(CLAUDE_PROJECT_DIR=str(crossings.parent)):
        text, _ = serve.call("crossing", {})
    return text


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
        "### Its instructions, where the server runs without the plugin\n\n"
        "The server can be added to another client by itself. No hook feeds the archive there, and the instructions "
        "say so.\n\n" + fenced(alone),
        "### Its tools\n\n" + tools(),
        "## As a session starts in a home that holds no label yet, or as the person switches Crossings on during it\n\n"
        + fenced(hook.welcome()),
        "## A session started new, in a home that holds labels: its frame\n\n"
        + fenced(frame.compose(crossings, new=True)),
        ledger(),
        "## After a cut: the waking note\n\n" + fenced(hook.waking({"cut": 2})),
        "## After a cut: the frame\n\n" + fenced(frame.compose(crossings)),
        "## After a cut, for the session that was cut: the person's sentences, each with what was told of it\n\n"
        + fenced(frame.compose(crossings, session=cut_session(crossings))),
        "## After a cut, where the line at the door rests on both ends of a sentence: the session's turns beside it, "
        "as `crossing` gives the frame, with the sentence it says after the frame and apart from it\n\n"
        + fenced(nesting()),
        "## After a cut, where a standing line rests on both ends of a sentence, or a stack through a line beneath it: "
        "the session's turns beside it, as `crossing` gives the frame, with the sentence it says after the frame and "
        "apart from it\n\n" + fenced(standing()),
        "## After a cut, the frame at the least size a home may set\n\n"
        + fenced(frame.compose(crossings, frame.LEAST)),
        "## After a cut, where a page written by hand holds keys that would take the frame past its size: the frame "
        "names labels by count\n\n" + fenced(by_count()),
        "## After a cut where no frame can be made: the hooks module's note before the hand-over page\n\n"
        + fenced(module_note()),
        "## After a cut, in a home where other models made lines\n\n"
        + fenced(frame.compose(crossings, model="a-made-up-model")),
        "## After a cut, at the least size, where more models made lines than the frame has room to name: the "
        "sentence says how many they are\n\n" + fenced(few_named()),
        "## As the person switches Crossings off during a session, and on again\n\n"
        + fenced(hook.unkept())
        + "\n\n"
        + fenced(hook.kept_again()),
        "## As another model comes into the session\n\n" + fenced(hook.arrival()),
        "## A session resumed where another worked since it last spoke\n\n" + fenced(hook.moved_on()),
        "## A session that starts in a folder below another home's folder\n\n" + fenced(below()),
        "## What the door's tools answer, from the made-up store\n\n" + answered(project),
        "## What `find` answers where it shows a message in part\n\n" + fenced(excerpted()),
        "## What `leave` and `mark` answer where a line or a label comes in long\n\n" + long_marked(),
        "## What `look`, `labels` and `status` say of a refusal put to rest for another model alone: it stands for the "
        "model that asks, the one of the session that spoke last\n\n" + at_rest_elsewhere(),
        "## What they say of a refusal that is another model's alone, standing there and then at rest there: it is "
        "counted for no family of the model that asks\n\n" + alone_elsewhere(),
        "## What a mark, or a line left at the door, can be refused with\n\n"
        "Each follows `not marked: `; an ellipsis stands where the sentence names a key, an id or a model.\n\n"
        + fenced("\n".join(refusals())),
        "## What the hooks module says as it refuses a session's call\n\n"
        + "\n\n".join(fenced(module_said(name)) for name in MODULE_REFUSES),
        "## What `thread` answers for an id two messages share\n\n" + fenced(shared()),
        "## While the person has Crossings switched off, and once it is on again\n\n"
        + "### `mark`, while it is off\n\n"
        + fenced(off_and_on()[0])
        + "\n\n### `look`, once it is on again\n\n"
        + fenced(off_and_on()[1]),
        "## What the door's server says where it could not answer\n\n"
        + "\n\n".join(fenced(said_by_server(words)) for words in SERVER_REFUSES)
        + "\n\n"
        + fenced("Nothing came back."),  # what it says where the door gave no words
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
    # Then what the session declined, marked once every other part is made, so that each of those is as it was: a
    # refusal judged again once, packed for the session that was cut; then three more, laid out as before, where
    # every family that stands is carried; and the sentence that names the oldest families where they would take a
    # frame past the most a hook can carry.
    hull = store.mark(
        crossings, "refused", "session", "The hull is not painted: the old paint comes off first.", [E], day=DAY
    )
    again = "Still not painted: the old paint is off, and the hull is wet."
    store.mark(crossings, "refused", "session", again, [hull["id"], D], day=DAY)
    packed = frame.compose(crossings, session=cut_session(crossings))
    for sentence, at in (
        ("The mast is not stepped before the paint.", D),
        ("No varnish is bought for the tiller.", E),
        ("The old ropes are not thrown away.", D),
    ):
        store.mark(crossings, "refused", "session", sentence, [at], day=DAY)
    at = next(n for n, part in enumerate(parts) if part.startswith("## After a cut, for the session that was cut")) + 1
    parts[at:at] = [
        "## After a cut, for the session that was cut, where it declined something: each refusal first, under the "
        "sentences of the person's that asked\n\n" + fenced(packed),
        "## After a cut, where four refusals stand, laid out as before\n\n" + fenced(frame.compose(crossings)),
        "## Where the refusals that stand would take a frame past the most a hook can carry: the oldest, in a "
        "sentence in their place\n\n"
        + fenced(frame._beyond([{"standing": {"id": "X2", "n": 2}}, {"standing": {"id": "X3", "n": 3}}], False))
        + "\n\n"
        + fenced(frame._beyond([{"standing": {"id": "X2", "n": 2}}], True)),
    ]
    return "\n\n".join(parts) + "\n"


if __name__ == "__main__":
    os.environ.pop("CLAUDE_PLUGIN_ROOT", None)  # the page says which instructions hold with it, and which without
    with contextlib.redirect_stderr(sys.stderr):
        sys.stdout.write(page())
