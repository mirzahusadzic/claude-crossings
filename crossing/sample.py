"""The home's side of the sampler: a session's stretch since its last cut, and its events.

A frame carries labels, which tell a story of what was said, and a few of the person's own words, chosen by
the frame's own rule (see crossing/frame.py). The events count what the stretch holds beside them: for each
message of the person's, whether a label rests on it, whether it was reached for, and whether a guard keeps
it out. They choose nothing and carry nothing. One sentence alone is said of them (`unmarked`): the ids of the
messages the sampler weighs and no label rests on, so that a session that still holds them can label them.

The arithmetic is not written here. It is in crossing/sampler, which sees events and nothing else: ids and
whole numbers, never a word of a message. This file is the home's side of it: the cut records and the log of
pulls are read here and handed to the sampler. Every value that decides what is counted is a setting fixed in
the sampler (`core.SETTINGS`); a home holds no file of them, and the person has no command for any of it.
"""

from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import record, store  # noqa: E402
from crossing.sampler import core, from_store  # noqa: E402


def _records(folder: Path, session: str) -> list[tuple[int, set[str]]]:
    """The session's recorded cuts, each by its number with the ids of the messages its sidecar's pointers name
    (`<session>-cut-<n>.json`, see record.write): what stood before that cut. A sidecar that cannot be read, or holds
    no record, is passed over, and so is a pointer that names no id. The session is matched as it is, never as a
    pattern."""
    named = re.compile(re.escape(session) + r"-cut-(\d+)\.json")
    found: list[tuple[int, set[str]]] = []
    for entry in sorted(store.within(folder).iterdir()):
        number = named.fullmatch(entry.name)
        if not number:
            continue
        try:
            side = json.loads(store.within(folder, entry.name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if not isinstance(side, dict):
            continue
        ids: set[str] = set()
        for voice in (side.get("person"), side.get("session")):
            pointers = voice.get("pointers") if isinstance(voice, dict) else None
            ids |= {
                pointer["id"]
                for pointer in (pointers if isinstance(pointers, list) else [])
                if isinstance(pointer, dict) and isinstance(pointer.get("id"), str)
            }
        found.append((int(number.group(1)), ids))
    return found


def _cut_ids(folder: Path, session: str) -> set[str]:
    """The ids of the messages the session's recorded cuts name, as each cut's sidecar keeps them (see `_records`):
    what stood before one of its cuts."""
    return {each for _, ids in _records(folder, session) for each in ids}


def _held(db: sqlite3.Connection, session: str, ids: set[str]) -> bool:
    """Whether the index still holds a message of the session's that is one of these."""
    named = sorted(ids)
    return (
        db.execute(
            f"select 1 from said where session = ? and voice != 'pasted' and id in ({', '.join('?' * len(named))}) "
            "limit 1",
            (session, *named),
        ).fetchone()
        is not None
    )


def _begun(folder: Path, db: sqlite3.Connection, session: str) -> set[str] | None:
    """The ids the session's stretch begins after: those its recorded cuts name. Nothing (None) where the start
    is not known.

    A cut's record names every message that stood before it, the last one too, and the hook that writes it and
    the hook that makes the frame for that cut may finish in either order. So where nothing of the person's was
    said in the session after the newest message its records name, the newest cut, by its number, is the one being
    crossed, or one just crossed: the stretch is the one that cut ended, and begins after the cuts before it, or,
    for a session's first cut, where the sampler's window places it, as it did before that record was written.
    Once the person has said something since, the stretch is the one since that cut.

    The start is not known where the cut the stretch begins after names no message of the session's that the
    index still holds (the person struck what it points at): the sampler's stretch would then begin after an
    older cut, or with its window, and hold what was said before that cut. A cut with no record that can be read
    is passed over (see `_records`), and a session with none is placed by the sampler's window, as before."""
    records = sorted(_records(folder, session), key=lambda each: each[0])
    if records and not _held(db, session, records[-1][1]):
        return None
    ids = {each for _, named in records for each in named}
    if records and not any(row["voice"] == from_store.HIS for row in from_store.stretch(db, session, ids, 0)):
        records = records[:-1]  # the cut that ended the stretch is on record already
        if records and not _held(db, session, records[-1][1]):
            return None
        ids = {each for _, named in records for each in named}
    return ids


def pulled(folder: Path) -> dict[str, int]:
    """How many pulls of the home's log (`reached.jsonl`, see store.reached) name each message, by its id of
    eight characters: a pull names it by that id, or by its whole one; an id with a `+` in it names a paste,
    which is not the person's words. A line that is no pull is passed over, and a pull counts once a message."""
    try:
        lines = record.lines_in(store.within(folder, "reached.jsonl"))
    except OSError:
        return {}
    counted: dict[str, int] = {}
    for line in lines:
        pull = store._pull(line) or {"ids": []}
        for each in {named[:8] for named in pull["ids"] if "+" not in named}:
            counted[each] = counted.get(each, 0) + 1
    return counted


def stretch(folder: Path, db: sqlite3.Connection, session: str, window: int) -> list[dict]:
    """The rows of the index the sampler draws on for a session, the oldest first: its own since the newest
    message any of its recorded cuts names, or from the newest `window` of the person's on where none does
    (the sampler's `stretch`, handed the ids the home's cut records name)."""
    return from_store.stretch(db, session, _cut_ids(folder, session) if session else set(), window)


def events(
    folder: Path,
    db: sqlite3.Connection,
    session: str,
    carried: list[dict],
    flagged: set[str],
    after: set[str] | None = None,
) -> list[dict]:
    """An event for every message of the person's in the session's stretch, and for any other a `carried` label
    rests on, the oldest first (the sampler's `events`), handed the ids the stretch begins after (`after`; where
    none is given, those the home's cut records name), the pulls its log counts and the window fixed in the
    sampler. An event holds ids and whole numbers alone."""
    cuts = after if after is not None else _cut_ids(folder, session) if session else set()
    return from_store.events(db, session, carried, pulled(folder), cuts, flagged, core.SEEDS["window"])


UNMARKED = 5  # the most messages the sentence of the weighed and unmarked names


def unmarked(folder: Path, db: sqlite3.Connection, session: str, flagged: set[str]) -> str:
    """The one sentence of the weighed and unmarked: the person's messages of the session's stretch since its last
    cut on which no label of any kind rests and no guard is, those the sampler weighs enough to take by rank (its
    own rule, `min_score` among it, under the settings fixed in it), UNMARKED at the most, the heaviest, in the
    order its pick ranks them. Each is given no length and the pick room for every one, so that the rule alone decides
    which are taken. By their ids alone, never a word of a message; one is said as one, and where there is none,
    or no session is named, nothing is said. Nor is anything said where the start of the stretch is not known (see
    `_begun`): no message from before the stretch is named. In a cut's frame the stretch is the one that cut ended,
    whether or not the cut's own record is written yet, and it stays so until the person says something after the
    cut. Said in the answer of a line left at the door through the server and in a cut's frame for the session
    that was cut; once a label rests on one, it is no longer named."""
    after = _begun(folder, db, session) if session else None
    if after is None:
        return ""
    found = [
        {**each, "length": 0}
        for each in events(folder, db, session, [], flagged, after)
        if each["in_stretch"] and not each["labelled"] and not each["guard"]
    ]
    ranked = core.pick(found, core.SEEDS, len(found))["ranked"]
    ids = [f"`{each['id']}`" for each in ranked if each["carried"]][:UNMARKED]
    if not ids:
        return ""
    if len(ids) == 1:
        return f"The record weighs this one, and no label rests on it: {ids[0]}; `thread` gives it in its place."
    return f"The record weighs these, and no label rests on them: {', '.join(ids)}; `thread` gives each in its place."
