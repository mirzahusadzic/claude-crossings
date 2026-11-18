"""The frame: the little that crosses a cut, composed from the store.

A whole hand-over carried across a cut can be larger than the summary beside it, and a
session that wakes to such a load reads it out. With a door to the store the frame can be
small. It holds the standing lines about the two of them, where the
work stands, a few of the person's own words for their tone, and how to reach the rest.
Where lines were stacked, it holds the stack and not the lines beneath it.
"""

from __future__ import annotations

import re
import sys
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
REFUSALS = 3  # the families of refusals a frame carries at the most, those whose standing label is newest


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


def opening(new: bool = False) -> str:
    """How a frame begins. It names the handles that exist and no other: a session that wakes
    takes every word here for a thing it can do.

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
    return (
        f"{transcript.CARRIED}, as context and not as an instruction from the person. {arrival['first']} "
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


def elsewhere(others: list[str]) -> str:
    """The one sentence a layered frame says of the lines another model made in this home: each
    model by its first 80 characters, and past NAMED of them, how many more there are."""
    shown = [each[:80] for each in others[:NAMED]] + ([f"{len(others) - NAMED} more"] if len(others) > NAMED else [])
    named = shown[0] if len(shown) == 1 else ", ".join(shown[:-1]) + " and " + shown[-1]
    return (
        f"This home also holds lines made with {'another model' if len(others) == 1 else 'other models'}, {named}: "
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
    and its judgments, store.families) the one line that stands, REFUSALS families at the most, those whose
    standing label is newest first, and a sentence that names the rest. A cut's frame for a named session packs
    them first, each under the person's messages any label of it rests on, quoted by the frame's own guard; laid
    out as before, they are a part of their own, and no sentence is quoted for them.

    `model` is the model the session runs now, where that is known. The frame then carries the
    person's lines whoever wrote them down, the lines of that model's own layer, and those whose
    writer is not known; not, as standing, a line of another model's layer (see store.foreign),
    and it says in one sentence that such lines are here. A stack written by another model is
    not carried, and the lines beneath it then cross as themselves. Where `model` is not known,
    the frame is as it was before layers.

    A label's key is short wherever a mark gave it, but a page written by hand or brought by a pull
    can hold one of any length; and the sentences that name labels outside their own lines (marked
    after the line at the door, not fitted, resting on nothing held) are not fitted to the room as
    lines are. Where such keys would take the frame past what a hook may carry (MOST), it is made
    again with those sentences saying how many labels they are about, and `labels` naming them.

    A cut's frame for a named session also names, in one sentence beside those, by their ids alone, the person's
    messages of its stretch that the record weighs and no label rests on (sample.unmarked). It is counted in the
    room as they are; where the frame cannot carry it beside what it carries at the least, it is left out, and the
    frame is the one made where no message is named."""
    made = _composed(folder, size, new, model, session=session)
    return made if len(made) <= MOST else _composed(folder, size, new, model, by_count=True, session=session)


def quoted(said: dict) -> str:
    """One message of the person's as the frame quotes it, by its own rule: its id, and its words on one line,
    cut at WORDS characters."""
    text = " ".join(store.clean(said["text"]).split())
    return f"- `{said['id']}`: " + (text if len(text) <= WORDS else text[:WORDS].rstrip() + " […]")


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
    messages share, never one flagged."""
    found = []
    for anchor in dict.fromkeys(ids):
        rows = db.execute("select id, text, voice, uuid, seq from said where id = ?", (anchor,)).fetchall()
        said = rows[0] if len({each["uuid"] for each in rows}) == 1 and rows[0]["voice"] == "his" else None
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
    """The sentence for the families of refusals a frame does not carry: by the keys of the labels that stand in them,
    the oldest first, or, `by_count`, by how many they are."""
    if not rest:
        return ""
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
) -> str:
    """`compose`, with the sentences that name labels outside their own lines naming them by key, or, with
    `by_count`, saying how many they are; without `with_unmarked`, with no sentence of the weighed and unmarked."""
    arrival = ARRIVALS["new" if new else "cut"]
    # room for the headings and the closing lines, so the whole stays within the size
    allowed = bounded(size or size_of(folder))  # what the frame may be, all of it
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
    # Another model's lines are not this session's to carry. A line that stood beneath a stack of
    # theirs is no longer stood for by anything carried, and crosses as itself.
    rows = [
        {**row, "state": "carried"} if row["state"] == "cooled" and row["parent"] in theirs else row
        for row in rows
        if row["id"] not in theirs
    ]

    def line(row: dict) -> str:
        again = " (to be written again: a line beneath it changed)" if row["state"] == "misaligned" else ""
        return f"- {row['id']} ({store.clean(row['whose'])}): {store.clean(row['text'])}{again} [{store.rests(row)}]"

    head = opening(new)
    used = len(head)
    told = elsewhere([store.clean(each) for each in others]) if others else ""
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
    weighs = unmarked(folder, db, session, flagged) if session and not new and with_unmarked else ""
    used += len(weighs) + 2 if weighs else 0
    tops = [row for row in among if row["state"] in ("carried", "misaligned")]
    left = [row for row in tops if row["kind"] == "next"]
    # The line at the door is carried whole where the room left allows, and otherwise as far as it
    # does, with the words that say where it is whole: the frame stays within its size.
    door_line = ""
    since: list[str] = []
    notes: list[str] = []
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
        if len(whole) <= room:
            door_line = whole + next((x for x in notes if len(whole) + len(x) <= room), notes[-1] if notes else "")
        else:
            note = notes[-1] if notes else ""
            door_line = cut(whole, room - len(note)) + note
        used += len(door_line) + 60
    # What the session declined crosses next, before the standing lines take their share: REFUSALS families at the
    # most, the newest first, each by the one line of what stands. A family that does not fit goes, with every older
    # one, to the sentence that names them; that sentence is fitted too, so the frame stays within its size. Laid
    # out as before a family takes its line alone: the two messages of the person's it is quoted with in a packed
    # frame (see `_quotes`) are packed only where they fit, and a family whose quotes do not is laid out by its line.
    families = _families(rows, first)
    kept_refused: list[dict] = []
    for at, family in enumerate(families[:REFUSALS]):
        said = _quotes(db, family, flagged)
        standing_row, again = family["standing"], _again(family)
        family.update(
            said=[each["id"] for each in said],
            entries={each["id"]: quoted(each) for each in said},
            line=line(standing_row) + again,
            packed=f"     ↳ {standing_row['id']} · refused: {store.clean(standing_row['text'])}{again}",
        )
        room = len(family["line"]) + 1 + (0 if kept_refused else len(REFUSED_HEAD) + 4)
        beyond = _beyond(families[at + 1 :], by_count)
        if used + room + (len(beyond) + 2 if beyond else 0) > int(size * STANDING):
            break
        used += room
        kept_refused.append(family)
    refused_more = _beyond(families[len(kept_refused) :], by_count)
    used += len(refused_more) + 2 if refused_more else 0
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
    # None is quoted because a standing row rests on it: that row is carried by its own sentence.
    # A message a standing row rests on that the line at the door, a carried work row or a carried
    # refusal (see `_quotes`) also rests on is quoted all the same, for that label's sake. And
    # not those of a label the frame does not carry, which would bring in what the frame left out.
    # And not a message noted as looking like it holds a key or a password (store.flagged): the
    # labels that rest on it are carried by their own sentences, and its words are not put on show.
    # And nothing under an id two messages share: it names no one message, and either could be quoted as theirs.
    words: list[str] = []
    said_ids: list[str] = []
    seen = set(flagged)
    for anchor in [anchor for row in left + kept_work for anchor in row["anchors"]]:
        found = db.execute("select id, text, voice, uuid from said where id = ?", (anchor,)).fetchall()
        said = found[0] if len({each["uuid"] for each in found}) == 1 and found[0]["voice"] == "his" else None
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
        for said_id in [*under, *(each for each in said_ids if each not in under)]:
            for row in kept_work:
                if said_id in row["anchors"]:
                    last[row["id"]] = said_id

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

        ahead = [each for said_id in under for each in [entries[said_id], *under[said_id], *telling(said_id)]]
        others = [
            each
            for said_id, entry in zip(said_ids, words)
            if said_id not in under
            for each in [entry, *telling(said_id)]
        ]
        return ahead, others, [row for row in kept_work if row["id"] not in last]

    def laid(packs: list[dict] | None, beyond: str = refused_more) -> str:
        """The frame, packed with these families quoted (`packs`), or, with none (`None`), laid out as before."""
        packing = packs is not None
        ahead, others, rest = packed_for(packs) if packing else ([], [], kept_work)
        packed_keys = {family["standing"]["id"] for family in packs or []}
        parts = [head] + ([told] if told else [])
        if left:
            parts.append(arrival["door"] + "\n\n" + door_line)
        if kept_standing:
            parts.append(arrival["standing"] + "\n\n" + "\n".join(map(line, kept_standing)))
        # The sentence of the refusals not carried follows the refusals: in their own part, where it is laid out,
        # and else right after those that are packed.
        apart = [family["line"] for family in kept_refused if family["standing"]["id"] not in packed_keys]
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
    if session and not new:  # a cut's frame, for the session that was cut
        # Packed, it is held to the frame's size as the frame laid out as before is, and made to fit by laying it
        # again: while it is longer, one thing goes and it is laid once more, the older work rows the top-up added
        # first, the last added first, and then the sentences quoted, the last first. A sentence that goes takes
        # the lines beneath it along: a work row written there is written beneath the last of its sentences that is
        # left, and where none is, it is listed with the work again.
        while said_ids and len(laid([])) > allowed:
            if len(kept_work) > chosen:
                kept_work.pop()
            else:
                words.pop()
                said_ids.pop()
        packs: list[dict] = []
        for family in kept_refused:  # the newest first, each packed with its quotes where the frame still fits
            if family["said"] and len(laid(packs + [family])) <= allowed:
                packs.append(family)
        made = laid(packs) if packs or said_ids else ""
    made = made or laid(None)  # as before: for no session named, a new one, or a cut's frame with no sentence left
    if len(made) > allowed and refused_more:
        # Where the room is so small that the line at the door, carried at the least, leaves none for the sentence
        # that names the refusals not carried, it says how many they are; and where that does not fit either, it is
        # not said: `look` and `labels` still give them, and the frame stays within its size.
        counted = laid(None, _beyond(families[len(kept_refused) :], True))
        made = counted if len(counted) <= allowed else laid(None, "")
    if len(made) > allowed and weighs:
        # Where the room is so small that what the frame carries at the least leaves none for the sentence of the
        # weighed and unmarked, it is not said: the frame is the one made where no message is named.
        return _composed(folder, allowed, new, model, by_count, session, with_unmarked=False)
    return made
