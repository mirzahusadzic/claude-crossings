"""The frame: the little that crosses a cut, composed from the store.

A whole hand-over carried across a cut can be larger than the summary beside it, and a
session that wakes to such a load reads it out. With a door to the store the frame can be
small. It holds the standing lines about the two of them, where the
work stands, a few of the person's own words for their tone, and how to reach the rest.
Where lines were stacked, it holds the stack and not the lines beneath it.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import record, store, transcript  # noqa: E402

SIZE = 9000  # characters of a frame, unless the home's `frame-size` says otherwise
WORDS = 300  # characters of one message of the person's carried for its tone
MOST = 9500  # the most a frame may be when a hook carries it: the harness takes 10,000 characters of a
# hook's context and, beyond that, hands the session a file's path in the frame's place
LEAST = 2300  # the least a frame may be: room for its opening, its handles and a line or two
STANDING, WORK = 0.8, 0.9  # how far into a frame the standing lines may reach, and then the work rows
DOOR = 300  # characters of the line left at the door carried at the least, however little room is left
NAMED = 8  # models named in the sentence about the lines of other models; the rest are counted
TOOL = "the door's tools"  # look, labels, find, thread, mark, leave: served by crossing/serve.py


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
# read the time before it and holds the store's labels as its own; one started new in the
# project lived none of it, and none of the store is its own, so it is told neither.
ARRIVALS = {
    "cut": {
        "first": "What follows is a frame made from the store before this cut: the standing lines about the two of "
        "you, where the work stands, and a few of the person's own words. You hold it as read, not as lived. "
        "A label can be mistaken; the record decides.",
        "last": "What is said is kept by itself; labels and the line at the door are yours to write, as the work goes. "
        "Reach when the conversation calls for it. What the person told you in confidence is held and left "
        "alone until they bring it up.",
        "why": "This frame was made so that the work goes on across the cut: rules chose what is in it, and the "
        "session before you wrote much of it. What you mark and leave is what the next one is given. What it is all "
        "for is a fair question, and the person is the one who can answer it; the door holds the whole record.",
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
        "why": "This frame was made so that the work goes on from one session to the next: rules chose what is in "
        "it, and the sessions before you wrote much of it. What you mark and leave is what the next one is given. "
        "What it is all for is a fair question, and the person is the one who can answer it; the door holds the whole "
        "record.",
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

    It says what the frame is for, too (`why`): a frame leans the session it is given to toward
    carrying the work on, and one that is not told so takes the frame's purpose for its own without
    noticing it was handed one. The sentence names the three places its question can go, each of
    them there already: what the session marks and leaves, which makes the next frame; the person;
    and the door, which holds the whole record and not only what the rules chose. It asks for
    nothing, and is said in every frame, since each is given to a session whose context holds no
    other."""
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


def compose(folder: Path, size: int | None = None, new: bool = False, model: str = "") -> str:
    """The frame for a session that comes through a cut, or, with `new`, for one started new in the
    project. A new session is given nothing where the store holds no label it would carry: a home
    with nothing in it has nothing to say to a session that never was in it.

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
    again with those sentences saying how many labels they are about, and `labels` naming them."""
    made = _composed(folder, size, new, model)
    return made if len(made) <= MOST else _composed(folder, size, new, model, by_count=True)


def _composed(folder: Path, size: int | None, new: bool, model: str, by_count: bool = False) -> str:
    """`compose`, with the sentences that name labels outside their own lines naming them by key, or, with
    `by_count`, saying how many they are."""
    arrival = ARRIVALS["new" if new else "cut"]
    # room for the headings and the closing lines, so the whole stays within the size
    size = bounded(size or size_of(folder)) - 420 - (LONGER if new else 0)
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
        for kind in ("relation", "work", "next")
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
    # Not a standing row's: that row is held, and what was said under it is not put on show. And
    # not those of a label the frame does not carry, which would bring in what the frame left out.
    # And not a message noted as looking like it holds a key or a password (store.flagged): the
    # labels that rest on it are carried by their own sentences, and its words are not put on show.
    # And nothing under an id two messages share: it names no one message, and either could be quoted as theirs.
    words, seen = [], set(store.flagged(folder))
    for anchor in [anchor for row in left + kept_work for anchor in row["anchors"]]:
        found = db.execute("select id, text, voice, uuid from said where id = ?", (anchor,)).fetchall()
        said = found[0] if len({each["uuid"] for each in found}) == 1 and found[0]["voice"] == "his" else None
        if said is None or said["id"] in seen:
            continue
        seen.add(said["id"])
        text = " ".join(store.clean(said["text"]).split())
        entry = f"- `{said['id']}`: " + (text if len(text) <= WORDS else text[:WORDS].rstrip() + " […]")
        if used + len(entry) > size:
            break
        words.append(entry)
        used += len(entry) + 1
    kept_work += fit(work[len(kept_work) :], size)  # what room is left goes to older work rows
    if new and not (left or kept_standing or kept_work or theirs):
        db.close()
        return ""

    parts = [head] + ([told] if told else [])
    if left:
        parts.append(arrival["door"] + "\n\n" + door_line)
    if kept_standing:
        parts.append(arrival["standing"] + "\n\n" + "\n".join(map(line, kept_standing)))
    if kept_work:
        parts.append("## The work, newest first\n\n" + "\n".join(map(line, kept_work)))
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
    if unheld:
        parts.append(unheld)
    if words:
        parts.append("## The person's own words, as they stand in the record\n\n" + "\n".join(words))

    parts.append(
        f"The store holds {record.many(held['his'], 'message')} of the person's and {held['session']} {closing}, "
        f"from {store.clean(held['from'])} to {store.clean(held['to'])}, and {held['labels']} "
        f"label{'' if held['labels'] == 1 else 's'}."
    )
    db.close()
    return "\n\n".join(parts) + "\n"
