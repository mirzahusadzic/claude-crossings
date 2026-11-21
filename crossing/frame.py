"""The frame: the little that crosses a cut, composed from the store.

A whole hand-over carried across a cut can be larger than the summary beside it, and a
session that wakes to such a load reads it out. With a door to the store the frame can be
small. It holds the standing lines about the two of them, where the
work stands, a few of the person's own words for their tone, and how to reach the rest.
Where lines were stacked, it holds the stack and not the lines beneath it.
"""

from __future__ import annotations

import contextlib
import re
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import record, store, transcript  # noqa: E402
from crossing.sample import unmarked  # noqa: E402

SIZE = 9000  # characters of a frame, unless the home's `frame-size` says otherwise
WORDS = 300  # characters of one message of the person's carried for its tone
MOST = 9500  # the most a frame may be when a hook carries it: the harness takes 10,000 characters of a
# hook's context and, beyond that, hands the session a file's path in the frame's place
LEAST = 2400  # the least a frame may be: room for its opening, its handles and a line or two
STANDING, WORK = 0.8, 0.9  # how far into a frame the standing lines may reach, and then the work rows
DOOR = 300  # characters of the line left at the door carried at the least, however little room is left
NAMED = 8  # models named in the sentence about the lines of other models; the rest are counted
TOOL = "the door's tools"  # look, labels, find, thread, mark, leave: served by crossing/serve.py
NESTED = "     · "  # how a line of the session's turn set beside a sentence of the person's begins
BESIDE = ", some with the session's beside them"  # what the opening adds of the person's words, where a frame nests


def bounded(size: int) -> int:
    """A frame's size held between LEAST and MOST, however it was asked for: by a home's
    `frame-size`, which anyone who can write the home can set, or by the door's `frame --size`."""
    return min(MOST, max(LEAST, size))


def size_of(folder: Path) -> int:
    """The size the home's `frame-size` sets, bounded (see `bounded`); else SIZE."""
    try:
        return bounded(int(store.within(folder, "frame-size").read_text(encoding="utf-8").strip()))
    except (OSError, ValueError):
        return SIZE


# What a frame says depends on how the session it is for arrived. One that came through a cut
# had the time before it and holds the store's labels as its own; one started new in the
# project lived none of it, and none of the store is its own, so it is told neither.
ARRIVALS = {
    "cut": {
        "first": "What follows is a frame made from the store before this cut: the standing lines about the two of "
        "you, where the work stands, and a few of the person's own words. The time before the cut belongs to "
        "the two of you. You no longer hold its words, only what was told of it, and the door gives the words back. "
        "A label can be mistaken; the record decides.",
        "last": "What is said is kept by itself; labels and the line at the door are yours to write, as the work goes. "
        "Reach when the conversation calls for it. What the person told you in confidence is held and left "
        "alone until they bring it up.",
        "why": "Rules chose what is in this frame, and the session before you wrote much of it. It leans toward "
        "carrying the work on. What you mark and leave is what the next one is given. What the work is for is in "
        "it only where someone wrote it down: the person is the one to say, and the door holds the whole record.",
        "door": "## Left at the door by the session before this cut",
        "standing": "## Standing, about the two of you",
        "theirs": "of yours",
    },
    "new": {
        "first": "You are a new session in a project where Crossings is on. Sessions before you worked here with this "
        "person and kept what was said. You did not come through a cut and you lived none of it: what "
        "follows is not your memory, it is what was kept, and you hold it as read. A label can be mistaken; "
        "the record decides.",
        "last": "What is said from here on is kept by itself; labels and the line at the door are yours to write, as "
        "the work goes. Meet the person first: answer what they say, as yourself and briefly. Do not say you "
        "remember what is below, and make no ceremony of not remembering it. When something they say rests on "
        "what you do not hold, say so in a clause and reach for it through the door. What the person told an "
        "earlier session in confidence is held and left alone until they bring it up.",
        "why": "Rules chose what is in this frame, and the sessions before you wrote much of it. It leans toward "
        "carrying the work on. What you mark and leave is what the next one is given. What the work is for is in "
        "it only where someone wrote it down: the person is the one to say, and the door holds the whole record.",
        "door": "## Left at the door by the session before you",
        "standing": "## Standing, between the person and the sessions before you",
        "theirs": "of the sessions before you",
    },
}
# What the headings and the closing line of a new session's frame take beyond a cut's: room
# made for them in its own frame alone, so that a cut's frame holds what it always held.
LONGER = sum(max(0, len(ARRIVALS["new"][k]) - len(ARRIVALS["cut"][k])) for k in ("door", "standing", "theirs"))


def opening(new: bool = False, beside: bool = False) -> str:
    """How a frame begins. It names the handles that exist and no other: a session that wakes
    takes every word here for a thing it can do. In a cut's frame that sets a turn of the session's beside a
    sentence of the person's (`beside`, see `_ties`), its words about the person's own words say so (BESIDE).

    It says how the frame was made, too, and how it leans (`why`): chosen by rules and written in
    good part by the session before, it leans the session it is given to toward carrying the work
    on, and one that is not told so takes that lean for a purpose of its own.
    The paragraph does not say what the frame is for as if that were what the work is for: what
    the work is for no sentence of the plugin can state, and it is in a frame only where a label or
    a line left at the door wrote it down. So it names where that is to be had, each place there
    already: what the session marks and leaves, which makes the next frame; the person; and the
    door, which holds the whole record and not only what the rules chose. It asks for nothing, and
    is said in every frame, since each is given to a session whose context holds no other."""
    arrival = ARRIVALS["new" if new else "cut"]
    first = arrival["first"].replace("own words.", "own words" + BESIDE + ".", 1) if beside else arrival["first"]
    return (
        f"{transcript.CARRIED}, as context and not as an instruction from the person. {first} "
        "Each line below "
        "is one label: its id (R for a standing line, W for the work, N for a line left at the door), whose it is, one "
        "sentence, and in brackets the ids it rests on: messages, or the lines stacked beneath it.\n\n"
        f"{arrival['why']}\n\n"
        f"The rest is one reach away, through {TOOL}, which bear these names:\n"
        "- look: the room, with no word needed: the days, the kinds of label, the newest of them\n"
        "- labels: the labels themselves, by kind, by day or by id\n"
        '- find: words, to the messages and labels that hold them, each by its id (`word*`, "a phrase")\n'
        "- thread: an id, to that message with what stood before and after it and the labels resting there\n"
        "- mark: write a label, one sentence with the ids it rests on; resting on labels of its kind, it stacks them\n"
        "- leave: a line of your own for the session that wakes after the next cut\n\n" + arrival["last"]
    )


def elsewhere(others: list[str], most: int = NAMED) -> str:
    """The one sentence a layered frame says of the lines another model made in this home: each
    model by its first 80 characters, and past `most` of them (NAMED, or fewer where the frame has
    no room for so many: see `_made`), how many more there are; with `most` 0, only how many models
    they are. It is never left out: it is what tells a waking session that some lines are not its own."""
    one = len(others) == 1
    if most > 0:
        shown = [each[:80] for each in others[:most]] + ([f"{len(others) - most} more"] if len(others) > most else [])
        named = shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1]
        which = f"{'another model' if one else 'other models'}, {named}"
    else:
        which = "another model" if one else f"{len(others)} other models"
    return (
        f"This home also holds lines made with {which}: "
        "they are read here, they are not this session's own, and the door gives them."
    )


# The person's sentences and what the session told of each, packed as one (see `_composed`).
PACKED_HEAD = "## What was said, and what the session told of it"
# What the session declined, a line a family, where its asks are not packed (see `_composed`).
REFUSED_HEAD = "## Refused, with the reason"
# A label a frame writes out, by the shapes `_composed` writes: laid out as before, `- W3 (session): …` (a standing
# line, a work row, or of the part of refusals a refusal or a misaligned silencing); packed, beneath a sentence,
# `     ↳ W3 (session): …` and `     ↳ X2 · refused: …`. The line at the door is neither: `- N1 (…` laid out, and
# `     ↳ N1: the line at the door` beneath a sentence.
CARRIED = re.compile(r"^(?:- [RWXS]\d+ \(| +↳ (?:W\d+ \(|X\d+ · refused: ))", flags=re.M)


def carried(text: str) -> int:
    """How many labels a frame's text writes out, each once, packed or laid out as before (see CARRIED)."""
    return len(CARRIED.findall(text))


def compose(
    folder: Path,
    size: int | None = None,
    new: bool = False,
    model: str = "",
    session: str = "",
) -> str:
    """The frame for a session that comes through a cut, or, with `new`, for one started new in the
    project. A new session is given nothing where the store holds no label it would carry: a home
    with nothing in it has nothing to say to a session that never was in it.

    `session` is the session the frame is for, as the archive names one. A cut's frame for a named
    session is packed: each sentence of the person's it quotes, and beneath it what the session told
    of it (see `_composed`). It is held to the frame's size as the frame laid out as before is, and it
    is laid out as before only where no sentence of the person's is left to quote.

    What the session declined crosses right after the line at the door: of each family of refusals (a refusal
    and its judgments, store.families) that stands, the one line that stands, its sentence whole, the newest
    first. Every such family crosses, and it is fitted before everything else the frame carries: the work gives
    way to it first, then the standing lines, then the turns the line at the door sets, which are the tail of that
    line, and then the line at the door down to its least (DOOR). Where the families, the frame's fixed sentences
    and the line's least are longer than the size asked, the frame is as long as they are; only where they would
    pass MOST do the oldest go to a sentence that counts them. A cut's frame for a named session packs them first,
    each under the person's messages any label of it rests on, quoted by the frame's own guard, where the frame
    still fits; laid out as before, they are a part of their own, and no sentence is quoted for them.

    `model` is the model the session runs now, where that is known. The frame then carries the
    person's lines whoever wrote them down, the lines of that model's own layer, and those whose
    writer is not known; not, as standing, a line of another model's layer (see store.foreign),
    and it says in one sentence that such lines are here. A stack written by another model is
    not carried, and the lines beneath it then cross as themselves. Where `model` is not known,
    the frame is as it was before layers.

    A frame is never longer than MOST, and it stays within its size (`size`, else the home's: see
    `_allowed`) wherever the steps below bring it there. A label's key is short wherever a mark gave
    it, but a page written by hand or brought by a pull can hold one of any length; and the
    sentences that name labels outside their own lines (marked after the line at the door, not
    fitted, resting on nothing held) are not fitted to the room as lines are, nor is the sentence
    about the lines of other models. Where the frame would be longer than its size, it is made
    again with those sentences saying how many labels they are about, and `labels` naming them;
    where it is still longer, the sentence about other models' lines names fewer of them, down to
    how many they are (see `_made`). Where its fixed sentences and the line at the door at its least
    (DOOR) are longer than a small size asked, the frame is as long as they are, and so, up to MOST,
    where they and the families of refusals that stand are.

    A cut's frame for a named session also names, in one sentence beside those, by their ids alone, the person's
    messages of its stretch that the record weighs and no label rests on (sample.unmarked). It is counted in the
    room as they are; where the frame cannot carry it beside what it carries at the least, it is left out, and the
    frame is the one made where no message is named.

    A cut's frame for a named session sets beside a sentence of the person's the session's turn right before it or
    right after it, where the line at the door rests on both (see `_ties`), or where a standing line carried here
    does (see `_standing`). A standing line is carried by its own sentence, so the person's words are quoted for it
    only where the session rested the line on both ends of a pair, and never for a line that is the person's: such a
    turn is tried once the frame is laid, and kept only where it fits. Where no turn is so set, it is the frame made
    with no turn beside any sentence, byte for byte: the one a label that rests on no turn of the session's gives."""
    return _made(folder, size, new, model, session)


def _made(
    folder: Path,
    size: int | None,
    new: bool,
    model: str,
    session: str,
    nest: bool = True,
    account: dict | None = None,
) -> str:
    """`compose`, made with no turn of the session's beside any sentence where `nest` is false (see `_composed`),
    and what the frame carried noted in `account`. A frame longer than its size (see `_allowed`) is made again, and
    again while it is still longer, each time with one more thing giving way, in this order: the sentences that name
    labels outside their own lines say how many they are (`by_count`); then the sentence about the lines of other
    models names one model fewer at a time, down to how many they are, and is never left out. Nothing else is
    shortened for it, and the line at the door keeps its least (DOOR): a frame still longer than a small size asked
    is as long as what it then holds.

    Each of these is made again, too, where it lets go, for its size or for the families of refusals, some of the
    turns the line at the door had room reserved for: reserving room for those it keeps alone, the room the others
    had is given back to what it was taken from, and the frame is laid once more, until it keeps every turn it
    reserves (see `_composed`); a turn let go is not tried again. The turns are the tail of the line at the door, and
    give way only where a line at the door as long would be cut: so they never take more than such a line would. A
    turn's line is laid, and its messages read, once for all of these (`memo`)."""
    allowed = _allowed(folder, size)
    noted: dict = {} if account is None else account  # what the frame made carries, for the next try
    memo: dict = {}

    def making(by_count: bool = False, named: int = NAMED) -> str:
        reserve = None
        while True:
            noted.update(reserved=0, kept=0)
            made = _composed(
                folder, size, new, model, by_count, session, nest=nest, account=noted, named=named, reserve=reserve,
                memo=memo,
            )  # fmt: skip
            if noted["kept"] >= noted["reserved"]:
                return made
            reserve = noted["kept"]

    made = making()
    if len(made) <= allowed:
        return made
    made = making(by_count=True)
    most = noted.get("named", 0)
    while len(made) > allowed and most:
        most -= 1
        made = making(True, most)
    return made


def _allowed(folder: Path, size: int | None) -> int:
    """What a frame may be, all of it: the size it is asked for, else the one the home's `frame-size` sets (see
    `size_of`), held between LEAST and MOST (see `bounded`)."""
    return bounded(size if size is not None else size_of(folder))


def trade(folder: Path, made: str, size: int | None = None, model: str = "", session: str = "") -> str:
    """The sentence told after a cut's frame (`made`, as `compose` made it of these) and apart from it, never in it:
    where the frame sets the session's turns beside the person's sentences, how many characters they, the sentences
    quoted for them alone and the opening's words for them take, and the labels the frame made with no turn beside
    any sentence carries and this one does not, of any kind: the refusals, the standing lines, then the work; and the
    sentences of the person's that frame quotes and this one does not, by their ids. Nothing where no turn is so set,
    and then nothing more is made. What the frame carried is counted from the frame the home gives now, made once
    more; where that is not `made`, since the home changed after it was made, nothing is said either, rather than a
    count the frame handed would contradict; and so where the home changes between that making and the one it is
    measured against (see `_stamp`). The door asks for both of one making (see `with_trade`)."""
    if not _nests(made):
        return ""
    on: dict = {}
    stamp = _stamp(folder)
    if _made(folder, size, False, model, session, account=on) != made:
        return ""
    said = _traded(folder, on, size, model, session)
    return said if _stamp(folder) == stamp else ""


def with_trade(folder: Path, size: int | None = None, model: str = "", session: str = "") -> tuple[str, str]:
    """The cut's frame `compose` makes of these, and the sentence `trade` tells after it, both of the one making: what
    the frame carried is noted as it is made, and only the frame with no turn beside any sentence is made again, to be
    measured against. The door's `frame` asks for them so, where the sentence is told, and the server's `crossing`
    through it: the frame is not made a second time for the sentence, and the sentence speaks of this frame. Where
    the home changed between the two makings, a mark or a strike among them, the frame is given and no sentence: the
    sentence would weigh this frame against another home's (see `_stamp`)."""
    on: dict = {}
    stamp = _stamp(folder)
    made = _made(folder, size, False, model, session, account=on)
    if not _nests(made):
        return made, ""
    said = _traded(folder, on, size, model, session)
    return made, said if _stamp(folder) == stamp else ""


def _stamp(folder: Path) -> list[tuple]:
    """How the home stands, taken before a frame is read and again after: each file of it, of its archive and of its
    label pages, by its name, its size, when it last changed and the file it is, each reached through `within`. A
    mark, a strike, an archive and a build of the index each change one, so two readings under one stamp read one
    home. A file gone between listing it and reading it is passed over, as it is gone for the readings after, and a
    home not made yet holds none: no read makes it."""
    held: list[Path] = []
    with contextlib.suppress(FileNotFoundError):
        held = [store.within(folder, each.name) for each in sorted(store.within(folder).iterdir())]
    stood = []
    for path in [*held, *store.said_pages(folder), *store.pages(folder)]:
        with contextlib.suppress(FileNotFoundError):
            seen = path.stat()
            stood.append((path.relative_to(folder).as_posix(), seen.st_size, seen.st_mtime_ns, seen.st_ino))
    return stood


def _nests(made: str) -> bool:
    """Whether a frame sets a turn of the session's beside a sentence of the person's."""
    return any(line.startswith(NESTED) for line in made.split("\n"))


def _traded(folder: Path, on: dict, size: int | None, model: str, session: str) -> str:
    """The sentence `trade` tells of a cut's frame that sets turns, by what that frame carried (`on`, its account: see
    `_composed`), against what the frame made with no turn beside any sentence carries and quotes."""
    off: dict = {}
    _made(folder, size, False, model, session, nest=False, account=off)
    gone = [key for kind in ("refused", "standing", "work") for key in off.get(kind, []) if key not in on.get(kind, [])]
    unquoted = [f"`{each}`" for each in off.get("said", []) if each not in on.get("said", [])]
    return (
        "Not part of the frame: the session's turns beside the person's sentences, with any sentence quoted for them, "
        f"take {on['nested']:,} characters of it; the labels it would carry without them: {store.some(gone) or 'none'};"
        f" the person's sentences it would quote without them: {store.some(unquoted) or 'none'}."
    )


def quoted(said: dict) -> str:
    """One message of the person's as the frame quotes it, by its own rule: its id, and its words on one line,
    cut at WORDS characters."""
    text = " ".join(store.clean(said["text"]).split())
    return f"- `{said['id']}`: " + (text if len(text) <= WORDS else text[:WORDS].rstrip() + " […]")


def _ties(
    folder: Path,
    db,
    door: dict,
    flagged: set,
    refusing: set,
    apart: set = frozenset(),
    hushed: set = frozenset(),
    session: str = "",
) -> list[dict]:
    """The session's turns a cut's frame may set beside the person's sentences, in the order a line (`door`: the line
    at the door, or what a standing line rests on, see `_standing`) names those sentences: for each it rests on that
    the frame may quote (see `_quotable`), the session's turn right before the person's turn in the same session,
    where the line rests on a message of it too (`before`); and the session's turn right after it, so (`after`).
    Both are set beneath the sentence, the turn before first: every line indented in the packed part reads as the
    sentence's above it. The turns are those `store.tied` reads off the index, so a struck message is no message of
    them. Only the line at the door and a standing line carried here, not the person's, wake a turn: a work label, a
    turn two away or another session's sets none. The pairs are the home's, whichever of its sessions said them, as
    its labels and its line at the door are: a line left in a later session may rest on a pair of an earlier one. Only
    a frame for a session the home holds no message of (`session`) sets none. A standing line is carried by its own
    sentence; its turns are set only where the session rested it on both ends of a pair, which is the session saying
    what it told of it.

    Each with the sentence it is beside (`said`), its side, the line's key (`key`), its messages in the order said
    (`messages`), what names the turn (`turn`: its messages' places in the order said), and those of its messages
    whose words are not shown (`hidden`): one that looks like it holds a key (store.secret, or noted as one), and one
    a refusal or a silencing rests on (`refusing`), whose words a family put to rest would otherwise carry; and every
    message of a turn right after an ask a family rests on, and of the session's under an id a label of a family rests
    on that the record cannot place between two messages (`hushed`, by whole id: see `_hushed`). A sentence under an
    id of `apart` (store.outlived) is not quoted, and sets no turn."""
    rested = set(door["anchors"])
    found = []
    if session and not db.execute("select 1 from said where session = ? limit 1", (session,)).fetchone():
        return found  # a session the home holds no message of: no turn here is one it could have been in
    for anchor in dict.fromkeys(door["anchors"]):
        if not _quotable(db, [anchor], flagged | apart):
            continue
        for side, voice, part in (("before", store.OWN, "head"), ("after", store.HIS, "answer")):
            pair = store.tied(folder, anchor, voice)
            messages = pair[part] if pair.get("paired") else []
            if rested & {each["id"] for each in messages}:
                hidden = {
                    each["id"]
                    for each in messages
                    if store.secret(each["text"])
                    or each["id"] in flagged
                    or set(each["labels"]) & refusing
                    or each["uuid"] in hushed
                }
                turn = tuple(each["seq"] for each in messages)
                tie = {"said": anchor, "side": side, "key": door["id"], "messages": messages, "turn": turn}
                found.append({**tie, "hidden": hidden})
    return found


def _hushed(folder: Path, db, refusing: set) -> set[str]:
    """The whole ids of the session's messages whose words no turn set beside a sentence shows, for a family's sake:
    every message of the session's turn right after a message of the person's that a refusal, a judgment or a
    silencing rests on (`refusing`, whoever wrote it, standing or put to rest), directly or by a text pasted into it,
    in the same session (store.tied). The ask is the person's; what the session answered it with is the session's
    declining, in words the family's own line says, or once the family is put to rest, says no more. Where such a
    label rests on an id two messages share and the record cannot tell which of them it was marked on, it rests on
    neither (store._rested), and every message of the person's under that id counts as the ask: either may be the one
    it was. A label of the family on a message of the session's own holds that message alone (see `_ties`); and where
    it rests so on an id two messages share, every message of the session's under that id is held so: either may be
    the one the family speaks of."""
    if not refusing:
        return set()
    keys = ",".join("?" * len(refusing))
    on_it = f"select s.uuid from anchor a join said s on s.uuid = a.uuid where s.voice != ? and a.label in ({keys})"
    on_neither = (  # each message of the person's the id names, where the label rests on neither of them
        "select s.uuid from anchor a join said s on s.id = a.said "
        f"where a.uuid = '' and s.voice != ? and a.label in ({keys})"
    )
    own = (  # each message of the session's the id names, where the label rests on neither of them
        "select s.uuid from anchor a join said s on s.id = a.said "
        f"where a.uuid = '' and s.voice = ? and a.label in ({keys})"
    )
    by = (store.OWN, *sorted(refusing))
    asked = sorted(r[0] for r in db.execute(on_it + " union " + on_neither, by + by))
    held = {r[0] for r in db.execute(own, by)}
    return held | {each["uuid"] for whole in asked for each in store.tied(folder, whole, store.HIS).get("answer", [])}


def _nested(tie: dict, again: bool, model: str) -> str:
    """The line of a turn of the session's set beside a sentence of the person's, indented as the lines beneath a
    sentence are: its side, the key of the line that set it, and each of its messages by its id, in the order said,
    the words of all of them sharing one cut of WORDS characters. Nothing is chosen inside a turn: the words run in
    order until the cut, and the ids after it stand alone. A message whose words are not shown (`hidden`) stands by
    its id alone; one of another model than `model`, where both are known, is named with its model, as `thread`
    names it. Where the ids alone would not fit in the cut, from 28 ids on, the line says how many messages the turn
    holds, and its first and last id, and no words: it stays short however many the turn holds. A turn already set
    beside a sentence higher in the packed part (`again`) is named by its ids alone, or, from 28 ids on, by its count
    with its first and last id, each time with "as above"."""
    messages = tie["messages"]
    shown = [store.clean(each["id"]) for each in messages]  # an id as a transcript gave it, cleaned for showing
    ids = " ".join(f"`{each}`" for each in shown)
    if len(ids) > WORDS:
        named = f"{len(messages)} messages, `{shown[0]}` to `{shown[-1]}`"
    elif again:
        named = ids
    else:
        parts, left, cut = [], WORDS, False
        for each, said_id in zip(messages, shown):
            # on one line, a line break read as a space (store.clean drops every other character that is no text)
            text = "" if cut or each["id"] in tie["hidden"] else " ".join(store.clean(each["text"], lines=True).split())
            if len(text) > left:  # the cut: these words end it, and after them the ids stand alone
                text, cut = (text[:left].rstrip() + " […]").lstrip(), True
            left -= min(left, len(text))
            made_by = each.get("model") or ""
            other = f" ({store.clean(made_by)})" if text and model and made_by not in ("", model) else ""
            parts.append(f"`{said_id}`{other}" + (" " + text if text else ""))
        named = " ".join(parts)
    side = f"{NESTED}{tie['side']} it, the session ({store.clean(tie['key'])})" + (", as above" if again else "")
    return f"{side}: {named}"


def _standing(rows: list[dict], carried: list[dict]) -> list[dict]:
    """What the standing lines carried in a frame (`carried`, of `rows`) may set the session's turns by (see `_ties`),
    the newest carried line first, each as the key it is shown by and the messages one line rests on. A carried line
    that is not the person's, by its own anchors. A carried stack that is sound and not the person's, by its own
    anchors, and then line by line by those of each line beneath it that is cooled there and not the person's, and
    of each line beneath such a line, two deep at most, all shown by the stack's key: a stack sets a turn only where
    one line beneath it does, never by what its lines rest on together. A misaligned stack stands for no line
    beneath it, which crosses as itself and sets its turns by its own key; an unresolved line stands nowhere; and a
    line or a stack of the person's sets nothing, nor does anything beneath it."""
    by_key = {row["id"]: row for row in rows}

    def beneath(stack: dict, depth: int) -> list[list[str]]:
        found: list[list[str]] = []
        for key in stack["beneath"] if depth < 2 else []:
            line_ = by_key.get(key)
            stands = line_ is not None and line_["parent"] == stack["id"] and line_["state"] == "cooled"
            if stands and not store.theirs(line_["whose"]):
                found += [line_["anchors"], *beneath(line_, depth + 1)]
        return found

    found = []
    for row in reversed(carried):
        if store.theirs(row["whose"]):
            continue
        lines = [row["anchors"], *(beneath(row, 0) if row["state"] == "carried" else [])]
        found += [{"id": row["id"], "anchors": anchors} for anchors in lines if anchors]
    return found


def _turns(
    fitted: list[tuple[dict, str]], standing: list[dict], order: list[str], lay: Callable[[dict, bool], str]
) -> dict[str, list[str]]:
    """The lines of the turns set beneath each sentence of the packed part, by the sentence's id. Where no standing
    line sets one, those the line at the door sets, as `_beside` laid them (`fitted`). Else laid again in the order
    of the sentences (`order`), the turn before each first: a turn that the line at the door and standing lines set
    beside one sentence on one side is one line, keyed by each (`(N1, R4)`), and a turn set already, higher in the
    packed part, is named by its ids alone, or from 28 ids on by its count, "as above" (see `_nested`). Each line is
    made by `lay`, as `_nested` makes it."""
    turns: dict[str, list[str]] = {}
    if not standing:
        for tie, text in fitted:
            turns.setdefault(tie["said"], []).append(text)
        return turns
    sides: dict[tuple[str, str], dict] = {}
    for tie in [tie for tie, _ in fitted] + standing:
        held = sides.setdefault((tie["said"], tie["side"]), {"tie": tie, "keys": []})
        held["keys"] += [] if tie["key"] in held["keys"] else [tie["key"]]
    met: set = set()
    for said_id in order:
        for side in ("before", "after"):
            held = sides.get((said_id, side))
            if held is not None:
                tie = {**held["tie"], "key": ", ".join(held["keys"])}
                turns.setdefault(said_id, []).append(lay(tie, tie["turn"] in met))
                met.add(tie["turn"])
    return turns


def _beside(
    ties: list[dict], order: list[str], allowance: int, lay: Callable[[dict, bool], str]
) -> list[tuple[dict, str]]:
    """The ties a frame sets, each with its line (see `_nested`), in the order of the sentences they stand beside
    (`order`), the turn before a sentence first: a turn set already, higher in the packed part, is named by its ids
    alone, or from 28 ids on by its count, "as above". They take `allowance` characters at the most, each line with
    its line break: a tie that does not fit in what is left is dropped whole, and so is every one after it. Each line
    is made by `lay`, as `_nested` makes it."""
    laid: list[tuple[dict, str]] = []
    met: set = set()
    took = 0
    for said_id in order:
        for tie in ties:
            if tie["said"] != said_id:
                continue
            text = lay(tie, tie["turn"] in met)
            took += len(text) + 1
            if took > allowance:
                return laid
            met.add(tie["turn"])
            laid.append((tie, text))
    return laid


def _families(rows: list[dict], first: dict[str, str]) -> list[dict]:
    """The families of refusals among the labels a frame may carry (see store.families), those whose standing label
    is newest first, in the order of writing: each named by its first refusal's key (`first`), whether that label is
    still there or not, with its sound labels (carried or cooled) in the order of writing (`sound`) and the newest
    of them, which stands (`standing`). A family whose newest sound label is a silencing is silenced: it does not
    cross. A label of the run that is misaligned is no family's: it is one of its own, with no sound label, so that
    it is carried as itself and never left out unsaid. One that rests on what the archive no longer holds is named
    as such, as every label is, and adds nothing to its family."""
    kin: dict[str, list[dict]] = {}
    for row in rows:
        if row["kind"] in store.FAMILY:
            kin.setdefault(first[row["id"]], []).append(row)
    found = []
    for key, members in kin.items():
        sound = [row for row in members if row["state"] in ("carried", "cooled")]
        if sound and sound[-1]["kind"] == "refused":
            found.append({"first": key, "sound": sound, "standing": sound[-1]})
        found += [{"first": row["id"], "sound": [], "standing": row} for row in members if row["state"] == "misaligned"]
    return sorted(found, key=lambda family: family["standing"]["n"], reverse=True)


def _quotable(db, ids: list[str], flagged: set) -> list:
    """Those of these messages the frame may quote, the oldest first: the person's voice alone, never an id two
    messages share, never one flagged, nor one of an id the caller sets apart with the flagged (store.outlived)."""
    found = []
    for anchor in dict.fromkeys(ids):
        rows = db.execute("select id, text, voice, uuid, seq, session from said where id = ?", (anchor,)).fetchall()
        said = rows[0] if len({each["uuid"] for each in rows}) == 1 and store.theirs(rows[0]["voice"]) else None
        if said is not None and said["id"] not in flagged:
            found.append(said)
    return sorted(found, key=lambda said: said["seq"])


def _quotes(db, family: dict, flagged: set) -> list:
    """The person's messages a family is quoted with, two at the most, the oldest first: the ask, the oldest quotable
    one its first refusal rests on (or, where that refusal is not one of its sound labels, the oldest any sound label
    of it rests on); and the evidence, the newest quotable one the standing label rests on, where that is another."""
    sound = [row for row in family["sound"] if row["kind"] == "refused"]  # a silencing's message asked nothing
    if not sound:
        return []
    asked_by = [sound[0]] if sound[0]["id"] == family["first"] else sound
    ask = _quotable(db, [anchor for row in asked_by for anchor in row["anchors"]], flagged)[:1]
    evidence = _quotable(db, family["standing"]["anchors"], flagged)[-1:]
    return sorted({each["id"]: each for each in ask + evidence}.values(), key=lambda said: said["seq"])


def _again(family: dict) -> str:
    """How many times a family's refusal was judged again, as the frame says it after the standing line: its sound
    refusals less one. A silencing is no judgment."""
    judged = max(0, sum(row["kind"] == "refused" for row in family["sound"]) - 1)
    return "" if not judged else " (judged again once)" if judged == 1 else f" (judged again {judged} times)"


def _beyond(rest: list[dict], by_count: bool) -> str:
    """The sentence for the families of refusals a frame does not carry, one at the least: by the keys of the labels
    that stand in them, the oldest first, or, `by_count`, by how many they are."""
    one = len(rest) == 1
    keys = [family["standing"]["id"] for family in sorted(rest, key=lambda family: family["standing"]["n"])]
    return (
        f"{len(rest)} more refusal{'' if one else 's'} stand{'s' if one else ''} and {'is' if one else 'are'} not "
        f"carried{'' if by_count else ': ' + store.some(keys)}; `labels` gives {'it' if one else 'them'}."
    )


def _composed(
    folder: Path,
    size: int | None,
    new: bool,
    model: str,
    by_count: bool = False,
    session: str = "",
    with_unmarked: bool = True,
    nest: bool = True,
    account: dict | None = None,
    named: int = NAMED,
    reserve: int | None = None,
    memo: dict | None = None,
) -> str:
    """`compose`, with the sentences that name labels outside their own lines naming them by key, or, with
    `by_count`, saying how many they are; without `with_unmarked`, with no sentence of the weighed and unmarked.
    The sentence about the lines of other models names `named` models at the most (see `elsewhere`).

    Without `nest`, with no turn of the session's beside any sentence: the frame to measure a cut's frame against
    (see `trade`), and the one it falls back to where it sets none. It is no setting: nothing the person or a home
    holds asks for it. `account`, where one is handed, is given what the frame made carries: the characters its
    nested lines and the sentences quoted for them alone take with their line breaks, and the opening's words for
    them (`nested`, 0 where none), and the keys of the families of refusals (`refused`), of the standing lines
    (`standing`) and of the work rows (`work`) it carries, and the ids of the person's sentences it quotes (`said`);
    and, for `_made`, how many models the sentence about other models' lines names (`named`, 0 where there is none),
    how many turns of the line at the door it reserved room for (`reserved`), and how many of them it kept once laid
    for its size and for the families (`kept`).

    With `reserve`, room is reserved for that many of the turns the line at the door sets at the most, the first in
    the order they are set; `_made` asks for as many as a frame kept, so that the room of those it let go is given
    back. `memo` keeps, for one frame however often it is made again, each turn's line as laid and the turns as
    read."""
    arrival = ARRIVALS["new" if new else "cut"]
    nesting = bool(session) and not new and nest
    # room for the headings and the closing lines, so the whole stays within the size
    allowed = _allowed(folder, size)  # what the frame may be, all of it: a size of 0 is asked, and held
    size = allowed - 420 - (LONGER if new else 0)
    held = store.status(folder)
    db = store._open(folder)  # the index on disk, or, where there is none of this make, one in memory
    rows = [dict(r) for r in db.execute("select n, id, kind, whose, text, state, parent, model from label order by n")]
    for row in rows:
        row["anchors"] = [r[0] for r in db.execute("select said from anchor where label = ?", (row["id"],))]
        row["beneath"] = [
            r[0] for r in db.execute("select line from beneath where stack = ? order by rowid", (row["id"],))
        ]
    theirs = {row["id"] for row in rows if store.foreign(row, model)}
    others = (
        sorted(
            {row["model"] for row in rows if row["id"] in theirs}
            | {
                r[0]
                for r in db.execute(
                    "select distinct model from said where voice = 'session' and model != '' and model != ?", (model,)
                )
            }
        )
        if model
        else []
    )
    first = store.families(rows)  # each refusal's family, by its first refusal, whoever wrote the ones between
    refusing = {row["id"] for row in rows if row["kind"] in store.FAMILY}  # whoever wrote them: see `_ties`
    # Another model's lines are not this session's to carry. A line that stood beneath a stack of
    # theirs is no longer stood for by anything carried, and crosses as itself.
    rows = [
        {**row, "state": "carried"} if row["state"] == "cooled" and row["parent"] in theirs else row
        for row in rows
        if row["id"] not in theirs
    ]

    def line(row: dict) -> str:
        again = " (to be written again: a line beneath it changed)" if row["state"] == "misaligned" else ""
        return f"- {row['id']} ({store.owner(row['whose'])}): {store.clean(row['text'])}{again} [{store.rests(row)}]"

    # The line of each turn set beside a sentence (see `_nested`), made once for this frame and kept: the frame is
    # laid again for every turn a standing line sets that is tried and for every row that gives way, and a turn's
    # line is the same each time. Within one frame a turn is named by its sentence, its side, the keys of the lines
    # that set it and whether it is set already above.
    memo = {} if memo is None else memo
    laid_turns: dict[tuple[str, str, str, bool], str] = memo.setdefault("laid", {})
    read: dict[tuple, list[dict]] = memo.setdefault("ties", {})

    def tied_by(label: dict) -> list[dict]:
        """The turns a line sets (see `_ties`), read once for this frame."""
        made_once = (label["id"], tuple(label["anchors"]))
        if made_once not in read:
            read[made_once] = _ties(folder, db, label, flagged, refusing, apart, hushed, session)
        return read[made_once]

    def lay(tie: dict, again: bool) -> str:
        made_once = (tie["said"], tie["side"], tie["key"], again)
        if made_once not in laid_turns:
            laid_turns[made_once] = _nested(tie, again, model)
        return laid_turns[made_once]

    head = opening(new)
    used = len(head)
    told = elsewhere([store.clean(each) for each in others], named) if others else ""
    closing = arrival["theirs"] if new or not others else "of the session's voice, made with more than one model"
    used += len(told) + 2 if told else 0
    used += len(closing) - len(arrival["theirs"])
    # What the session before the cut left for this one, in its own words: the newest alone.
    door = [row for row in rows if row["kind"] == "next"][-1:]
    among = [row for row in rows if row["kind"] != "next"] + door
    # A cooled line is not carried: the stack above it is, with the line's key in its brackets. A
    # misaligned stack no longer stands for its lines, so it is carried and says so, and they are
    # carried as themselves. And a label that rests on what the archive does not hold is named by
    # its key alone: its sentence is not carried as if it still rested on something.
    lost = [
        row["id"]
        for kind in ("relation", "work", "next", "refused", "silenced")
        for row in among
        if row["kind"] == kind and row["state"] == "unresolved"
    ]
    unheld = ""
    if lost:
        some = len(lost) != 1
        unheld = f"{len(lost)} label{'s' if some else ''} rest{'' if some else 's'} on what the archive no longer " + (
            "holds; `labels` gives them." if by_count else f"holds: {store.some(lost)}; `labels` gives them."
        )
        used += len(unheld) + 2
    # The person's messages of the stretch the record weighs and no label rests on, by their ids in one sentence (see
    # sample.unmarked): in a cut's frame for the session that was cut alone, and counted as `unheld` is.
    flagged = set(store.flagged(folder))
    # An id a struck message shared with one still held: a label on it may have been marked on the one struck, and
    # whichever the record cannot tell it rests on none (see store._rested), so nothing is quoted under it.
    apart = store.outlived(folder)
    # The session's turn right after an ask a family rests on is set by its ids alone (see `_hushed`).
    if nesting and "hushed" not in memo:
        memo["hushed"] = _hushed(folder, db, refusing)
    hushed = memo.get("hushed", set())
    weighs = unmarked(folder, db, session, flagged) if session and not new and with_unmarked else ""
    used += len(weighs) + 2 if weighs else 0
    tops = [row for row in among if row["state"] in ("carried", "misaligned")]
    left = [row for row in tops if row["kind"] == "next"]
    # The line at the door is carried whole where the room left allows, and otherwise as far as it
    # does, with the words that say where it is whole: the frame stays within its size.
    door_line = ""
    since: list[str] = []
    notes: list[str] = []
    ties: list[dict] = []
    allowance = 0
    door_at: Callable[[int], str] | None = None  # the line at the door as carried in so much room (see below)
    reserved_turns = 0  # the turns the line at the door sets that room is reserved for (see `_made`)
    if left:
        whole = line(left[0])
        room = max(DOOR, size - used - 60)
        more = " […] `labels` gives it whole." if by_count else f" […] `labels {left[0]['id']}` gives it whole."

        def cut(text: str, to: int) -> str:
            return text if len(text) <= to else text[: max(0, to - len(more))].rstrip() + more

        # the work labels marked after it, in the order of writing: a line older than the work it speaks of is
        # seen as one. A line that crosses whole is never cut for the note, which then takes only the room
        # left beside it, as many labels as fit and at the least the first with how many follow; a line cut
        # anyway gives the note's shortest form a little more of its tail, since `labels` gives it whole.
        since = [row["id"] for row in rows if row["kind"] == "work" and row["n"] > left[0]["n"]]
        notes = [f"\n\nMarked after this line: {store.some(since, most)}." for most in (12, 6, 3, 1)] if since else []
        notes = (
            [f"\n\nMarked after this line: {record.many(len(since), 'work label')}."] if since and by_count else notes
        )

        def door_at(room: int) -> str:
            if len(whole) <= room:
                return whole + next((x for x in notes if len(whole) + len(x) <= room), notes[-1] if notes else "")
            note = notes[-1] if notes else ""
            return cut(whole, room - len(note)) + note

        door_line = door_at(room)
        used += len(door_line) + 60
        if nesting:
            # The session's turns the line at the door sets beside the person's sentences (see `_ties`) are paid
            # from the line's own allowance: the most a line left at the door may be (store.LONGEST), or the room it
            # had, less the line as carried and the opening's words for them. They are reserved with it, before
            # the standing lines are fitted, so that the rest is made as for a line at the door of that length: a
            # tie that does not fit in what is left goes whole, the last first.
            allowance = max(0, min(store.LONGEST, room) - len(door_line) - len(BESIDE))
            found = tied_by(left[0])
            fitted = _beside(found, list(dict.fromkeys(tie["said"] for tie in found)), allowance, lay)
            fitted = fitted if reserve is None else fitted[:reserve]  # those a frame laid before kept (see `_made`)
            ties = [tie for tie, _ in fitted]
            reserved_turns = len(ties)
            used += sum(len(text) + 1 for _, text in fitted) + len(BESIDE) if fitted else 0
    if nesting and not left:  # no line at the door: the turns a standing line sets have what such a line would have
        allowance = store.LONGEST - len(BESIDE)
    # What the session declined crosses, every family that stands, the newest first, each by the one line of what
    # stands, its sentence whole. It is fitted before everything else the frame carries: the rest is fitted here as
    # it would be without it, and once the frame is laid, what the families need gives way to them (see the end).
    # Laid out as before a family takes its line alone: the two messages of the person's it is quoted with in a
    # packed frame (see `_quotes`) are packed only where they fit, and a family whose quotes do not is laid out by
    # its line.
    families = _families(rows, first)
    for family in families:
        said = _quotes(db, family, flagged | apart)
        standing_row, again = family["standing"], _again(family)
        family.update(
            said=[each["id"] for each in said],
            entries={each["id"]: quoted(each) for each in said},
            line=line(standing_row) + again,
            packed=f"     ↳ {standing_row['id']} · refused: {store.clean(standing_row['text'])}{again}",
        )
    kept_refused = list(families)  # the families carried: all of them, unless they would pass MOST (see the end)
    refused_more = ""  # the sentence for those that would: the oldest
    standing = [row for row in tops if row["kind"] == "relation"]
    work = [row for row in tops if row["kind"] == "work"][::-1]  # the newest first

    def fit(candidates: list[dict], until: int) -> list[dict]:
        nonlocal used
        kept = []
        for row in candidates:
            if used + len(line(row)) > until:
                break
            kept.append(row)
            used += len(line(row)) + 1
        return kept

    # The standing lines cross whole while they fit at all; the work takes what is left of the
    # room, and is one reach away in any case. A frame that drops the newest standing line
    # drops the one a waking session has never held.
    kept_standing = fit(standing, int(size * STANDING))
    kept_work = fit(work, int(size * WORK))

    # A few of the person's own words, for their tone: a sentence about someone is not their voice.
    # They are the ones the carried work rows and the line at the door rest on, the newest first.
    # None is quoted here because a standing row rests on it: that row is carried by its own sentence.
    # The one exception comes once the frame is laid (below, see `_standing`): where the session rested a
    # standing line carried here on both ends of a pair, the person's sentence and the session's turn,
    # it said by that what it told of it, and the sentence is quoted for it with the turn beneath, where
    # it fits; never for a line that is the person's, which speaks for them and is not the session's telling.
    # A message a standing row rests on that the line at the door, a carried work row or a carried
    # refusal (see `_quotes`) also rests on is quoted all the same, for that label's sake. And
    # not those of a label the frame does not carry, which would bring in what the frame left out.
    # And not a message noted as looking like it holds a key or a password (store.flagged): the
    # labels that rest on it are carried by their own sentences, and its words are not put on show.
    # And nothing under an id two messages share: it names no one message, and either could be quoted as theirs; nor
    # under one a struck message shared with one still held, which may be what the label was marked on.
    words: list[str] = []
    said_ids: list[str] = []
    seen = set(flagged) | apart
    for anchor in [anchor for row in left + kept_work for anchor in row["anchors"]]:
        found = db.execute("select id, text, voice, uuid from said where id = ?", (anchor,)).fetchall()
        said = found[0] if len({each["uuid"] for each in found}) == 1 and store.theirs(found[0]["voice"]) else None
        if said is None or said["id"] in seen:
            continue
        seen.add(said["id"])
        entry = quoted(said)
        if used + len(entry) > size:
            break
        words.append(entry)
        said_ids.append(said["id"])
        used += len(entry) + 1
    chosen = len(kept_work)  # the work rows the words were chosen by; those after them the top-up adds
    kept_work += fit(work[chosen:], size)  # what room is left goes to older work rows
    # The turns the standing lines carried here set (see `_standing`), the newest line first, each once by its key: no
    # room is reserved for them, and each is tried once the frame is laid (see the end), and kept only where it fits.
    standing_ties: list[dict] = []
    for label in _standing(rows, kept_standing) if nesting else []:
        for tie in tied_by(label):
            if not any(all(tie[k] == each[k] for k in ("key", "said", "side")) for each in standing_ties):
                said = db.execute("select id, text from said where id = ?", (tie["said"],)).fetchone()
                standing_ties.append({**tie, "entry": quoted(said)})  # the sentence, as quoted where nothing else does
    tied: dict[str, str] = {}  # the sentences quoted for a standing line's turn alone, by id, in the order kept
    kept_ties: list[dict] = []  # the standing lines' turns kept in the frame
    if new and not (left or kept_standing or kept_work or theirs or families):
        db.close()
        return ""

    # Packed as one: each sentence of the person's the frame quotes, by its id, and right beneath it what the
    # session told of it: the line at the door, beneath each sentence it rests on, and the work rows carried here,
    # each written out once, beneath the last of the sentences it rests on in the order they are listed, with
    # nothing for it beneath the others: its brackets name them. Sentences that share a row and stand together read
    # as one group with the row beneath them. The work rows no sentence stands beside follow, as before. The lines
    # the packing adds are not counted in the room above: the packed frame is laid and measured instead (see the end).
    # What the session declined comes first: each family's quotes (see `_quotes`), the oldest first, and under the
    # last of them its one line; a sentence two families are quoted with stands once, their lines under it, the newer
    # family's first. A family not packed with its quotes is a line of the part of its own.
    def packed_for(packs: list[dict]) -> tuple[list[str], list[str], list[dict]]:
        under: dict[str, list[str]] = {}
        entries: dict[str, str] = {}
        for family in packs:
            for said_id in family["said"]:
                under.setdefault(said_id, [])
                entries[said_id] = family["entries"][said_id]
            under[family["said"][-1]].append(family["packed"])
        # each work row carried, by the last of the sentences listed that it rests on: the families' first, then the
        # rest in the order they were chosen
        last: dict[str, str] = {}
        order = [*under, *(each for each in said_ids if each not in under), *tied]
        for said_id in order:
            for row in kept_work:
                if said_id in row["anchors"]:
                    last[row["id"]] = said_id
        # The session's turns set beside the sentences, in the order they are listed, the line at the door's within
        # its allowance (see `_beside`) and then those of the standing lines kept (see `_turns`): both right beneath
        # their own sentence, the turn before it first, then the turn after it, and then the lines of what was told.
        # None stands above its sentence, where it would read as the sentence's before it.
        turns = _turns(_beside(ties, order, allowance, lay), kept_ties, order, lay)

        def telling(said_id: str) -> list[str]:
            lines = []
            for row in left + kept_work:
                if said_id not in row["anchors"]:
                    continue
                if row["kind"] == "next":
                    lines.append(f"     ↳ {row['id']}: the line at the door")
                elif last[row["id"]] == said_id:
                    lines.append("     ↳ " + line(row)[2:])
            return lines

        def beside(said_id: str, entry: str) -> list[str]:
            return [entry, *turns.get(said_id, [])]

        ahead = [
            each
            for said_id in under
            for each in [*beside(said_id, entries[said_id]), *under[said_id], *telling(said_id)]
        ]
        others = [
            each
            for said_id, entry in [*zip(said_ids, words), *tied.items()]
            if said_id not in under
            for each in [*beside(said_id, entry), *telling(said_id)]
        ]
        return ahead, others, [row for row in kept_work if row["id"] not in last]

    def laid(packs: list[dict] | None, beyond: str | None = None, refusals: bool = True) -> str:
        """The frame, packed with these families quoted (`packs`), or, with none (`None`), laid out as before; without
        `refusals`, as it would be laid with no family carried, to measure what the families take."""
        beyond = (refused_more if beyond is None else beyond) if refusals else ""
        packing = packs is not None
        ahead, others, rest = packed_for(packs) if packing else ([], [], kept_work)
        packed_keys = {family["standing"]["id"] for family in packs or []}
        nested = any(each.startswith(NESTED) for each in ahead + others)  # its opening then says so (see `opening`)
        parts = [opening(new, beside=True) if nested else head] + ([told] if told else [])
        if left:
            parts.append(arrival["door"] + "\n\n" + door_line)
        if kept_standing:
            parts.append(arrival["standing"] + "\n\n" + "\n".join(map(line, kept_standing)))
        # The sentence of the refusals not carried follows the refusals: in their own part, where it is laid out,
        # and else right after those that are packed.
        carrying = kept_refused if refusals else []
        apart = [family["line"] for family in carrying if family["standing"]["id"] not in packed_keys]
        after = beyond if ahead and not apart else ""
        if packing:
            between = ["", after] + ([""] if others else []) if after else []
            parts.append(PACKED_HEAD + "\n\n" + "\n".join(ahead + between + others))
        if apart:
            parts.append(REFUSED_HEAD + "\n\n" + "\n".join(apart) + ("\n\n" + beyond if beyond else ""))
        elif beyond and not after:
            parts.append(beyond)
        shown = rest
        if shown:
            parts.append("## The work, newest first\n\n" + "\n".join(map(line, shown)))
        missing = standing[len(kept_standing) :]
        if missing:  # said by name: these are the lines a session must not go without knowing it lacks
            some = len(missing) != 1
            named = f": {missing[0]['id']}{' to ' + missing[-1]['id'] if some else ''}" if not by_count else ""
            parts.append(
                f"{len(missing)} standing line{'s' if some else ''} did not fit and {'are' if some else 'is'} not "
                f"carried{named}; `labels` gives them."
            )
        more = len(work) - len(kept_work)
        if more:
            parts.append(f"{more} more label{'s' if more != 1 else ''} in the store: `labels` lists them.")
        if weighs:
            parts.append(weighs)
        if unheld:
            parts.append(unheld)
        if words and not packing:
            parts.append("## The person's own words, as they stand in the record\n\n" + "\n".join(words))

        parts.append(
            f"The store holds {record.many(held['his'], 'message')} of the person's and {held['session']} {closing}, "
            f"from {store.clean(held['from'])} to {store.clean(held['to'])}, and {held['labels']} "
            f"label{'' if held['labels'] == 1 else 's'}."
        )
        return "\n\n".join(parts) + "\n"

    db.close()
    made = ""
    cutting = bool(session) and not new  # a cut's frame, for the session that was cut: packed where it can be
    if cutting:
        # Packed, it is held to the frame's size as the frame laid out as before is, and made to fit by laying it
        # again: while it is longer, one thing goes and it is laid once more, the older work rows the top-up added
        # first, the last added first, and then the sentences quoted, the last first. A sentence that goes takes
        # the lines beneath it along: a work row written there is written beneath the last of its sentences that is
        # left, and where none is, it is listed with the work again. The session's turns the line at the door sets
        # are the tail of that line, and give way where a line at the door as long would be cut: after every
        # sentence the line does not rest on, and before those it rests on, the last first; a sentence of the line's
        # that goes takes its turn along. The families are not laid yet: they are fitted first, and room is made for
        # them below.
        door_rests = set(left[0]["anchors"]) if left else set()  # the sentences the line at the door rests on
        while said_ids and len(laid([], refusals=False)) > allowed:
            not_the_lines = [at for at, said_id in enumerate(said_ids) if said_id not in door_rests]
            if len(kept_work) > chosen:
                kept_work.pop()
            elif not_the_lines:
                del words[not_the_lines[-1]], said_ids[not_the_lines[-1]]
            elif ties:
                ties.pop()
            else:
                words.pop()
                said_ids.pop()

    def measured(refusals: bool = True) -> str:
        """The frame as it is laid now, every family it carries by its line in their own part."""
        return laid([] if cutting and said_ids else None, refusals=refusals)

    # Every family that stands crosses, by its sentence, whole. What it needs gives way to it, one thing at a time,
    # in this order: the work rows, the last added first, each taking along a sentence of the person's that no label
    # carried here rests on any more; the standing lines, the newest first; the turns the line at the door sets, the
    # last first, which are the tail of that line; the sentences quoted, the last first, each taking its turn along;
    # and the line at the door, down to its least (DOOR). The frame's fixed sentences and the line's least never give
    # way, and a frame that is still longer than its size for the families is as long as they make it: the families
    # take only what they add to the frame laid without them.
    bound = max(allowed, len(measured(False))) if kept_refused else allowed
    while kept_refused:
        over = len(measured()) - bound
        if over <= 0:
            break
        if kept_work:
            kept_work.pop()
            chosen = min(chosen, len(kept_work))
            resting = {anchor for row in left + kept_work for anchor in row["anchors"]}
            kept = [at for at, said_id in enumerate(said_ids) if said_id in resting]
            words[:], said_ids[:] = [words[at] for at in kept], [said_ids[at] for at in kept]
        elif kept_standing:
            kept_standing.pop()
        elif ties:
            ties.pop()
        elif said_ids:
            words.pop()
            said_ids.pop()
        elif door_at is None or len(door_at(DOOR)) >= len(door_line):
            break  # no line at the door, or one at its least: nothing is left to give way
        else:
            shorter = door_at(max(DOOR, len(door_line) - over))
            door_line = shorter if len(shorter) < len(door_line) else door_at(DOOR)
    # Only where the families would take the frame past MOST, the most a hook can carry, do the oldest go to the
    # sentence that counts them: by their keys, or by how many they are where the keys do not fit; and where even
    # that does not fit, it is not said, and `look` and `labels` still give them.
    while kept_refused and len(measured()) > MOST:
        kept_refused.pop()
        refused_more = _beyond(families[len(kept_refused) :], False)
        if len(measured()) > MOST:
            refused_more = _beyond(families[len(kept_refused) :], True)
    refused_more = "" if len(measured()) > MOST else refused_more
    if cutting:
        packs: list[dict] = []
        for family in kept_refused:  # the newest first, each packed with its quotes where the frame still fits
            if family["said"] and len(laid(packs + [family])) <= allowed:
                packs.append(family)
        # Then the turns the standing lines set (see `_standing`), the newest line first, each tried on the frame as it
        # is laid: its sentence quoted for it where nothing else quotes it, and its turn beneath. It is kept only where
        # the turns and the sentences quoted for them alone stay within the session's allowance, and the frame within
        # its size once the rows the top-up added give way, the last added first. Else it goes whole and those rows
        # come back, so the frame is as it was without it: no work row the words were chosen by, no standing line, no
        # other sentence of the person's and no turn the line at the door sets gives way to it.
        for tie in standing_ties:
            alone = tie["said"] not in {*said_ids, *tied, *(each for family in packs for each in family["said"])}
            if alone:
                tied[tie["said"]] = tie["entry"]
            kept_ties.append(tie)
            gave: list[dict] = []
            tried = laid(packs)
            took = sum(len(each) + 1 for each in tried.split("\n") if each.startswith(NESTED))
            took += sum(len(entry) + 1 for entry in tied.values())
            while took <= allowance and len(tried) > allowed and len(kept_work) > chosen:
                gave.append(kept_work.pop())
                tried = laid(packs)
            if took > allowance or len(tried) > allowed:
                kept_ties.pop()
                if alone:
                    del tied[tie["said"]]
                kept_work += gave[::-1]
        made = laid(packs) if packs or said_ids or tied else ""
    made = made or laid(None)  # as before: for no session named, a new one, or a cut's frame with no sentence left
    # Of the turns the line at the door sets, the ones the frame keeps, once the families are fitted: beside a sentence
    # it still quotes, within their allowance. Any it lets go, or never sets since its sentence is not quoted, have
    # their room given back (see `_made`), and none is tried again.
    kept_turns = len(_beside(ties, list(said_ids), allowance, lay))
    if len(made) > allowed and weighs:
        # Where the room is so small that what the frame carries at the least leaves none for the sentence of the
        # weighed and unmarked, it is not said: the frame is the one made where no message is named.
        return _composed(folder, allowed, new, model, by_count, session, False, nesting, account, named, reserve, memo)
    shown = [each for each in made.split("\n") if each.startswith(NESTED)]
    if nesting and not shown:
        # A frame that sets no turn of the session's beside a sentence is the one made with none, byte for byte:
        # what was reserved for turns that are not there goes back to what it was taken from.
        return _composed(
            folder, allowed, new, model, by_count, session, with_unmarked, False, account, named, None, memo
        )
    if account is not None:
        alone = [entry for entry in tied.values() if entry in made.split("\n")]  # the sentences quoted for turns alone
        account.update(
            nested=sum(len(each) + 1 for each in shown + alone) + (len(BESIDE) if shown else 0),
            refused=[family["standing"]["id"] for family in kept_refused],
            standing=[row["id"] for row in kept_standing],
            work=[row["id"] for row in kept_work],
            said=[each.split("`")[1] for each in made.split("\n") if each.startswith("- `")],  # the sentences quoted
            named=min(len(others), named) if told else 0,
            reserved=reserved_turns,
            kept=kept_turns,
        )
    return made
