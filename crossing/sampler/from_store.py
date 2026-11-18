"""Events from the store's index: the person's messages a frame might carry, as the core takes them.

The adapter reads three tables of the index (`said`, `label` and `anchor`, see tests/sampler_schema.sql)
through an open connection, and is handed what else it needs: the carried labels, the pulls counted, the ids
the session's cut records name, the ids flagged and the window. It finds the stretch (see `stretch`), adds
every message of the person's that a carried label rests on wherever it lies, and makes each message one
event (see `crossing.sampler.core`). It writes nothing and quotes nothing, and reads neither the time of a
message nor its words: an event holds ids and counts alone.
"""

from __future__ import annotations

import sqlite3

HIS = "his"  # the voice the index gives the person's own messages
_ROWS = "select seq, uuid, id, voice from said"


def _rows(db: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict]:
    """The rows a query gives, each a dict by column, whatever rows the connection itself is set to make."""
    cursor = db.cursor()
    cursor.row_factory = None
    cursor.execute(sql, params)
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor]


def stretch(db: sqlite3.Connection, session: str, cut_ids: set[str], window: int) -> list[dict]:
    """The messages of either voice the sampler draws on, the oldest first, as the index orders them: the
    session's own, after the newest message any of its cut records names (`cut_ids`); and where none of those
    is held, from the newest `window` of the person's in it on. With no session named, the same of every
    session's messages, and no cut is read. A paste is a row of its own, and none of the person's words."""
    rows = _rows(db, f"{_ROWS} where voice != 'pasted' and (? = '' or session = ?) order by seq", (session, session))
    named = set(cut_ids) if session else set()
    last = max((n for n, row in enumerate(rows) if row["id"] in named), default=None)
    if last is not None:
        return rows[last + 1 :]
    his = [n for n, row in enumerate(rows) if row["voice"] == HIS]
    return rows[his[max(0, len(his) - window)] :] if window and his else []


def _guarded(said: str, anchored: int, twins: set[str], flagged: set[str], standing: set[str]) -> str:
    """The guard of the frame's that leaves a message of the person's out, by its id, where one does (`twin`,
    `flagged` or `standing`), or "" where none does."""
    if said in twins:
        return "twin"
    if said in flagged:
        return "flagged"
    return "standing" if said in standing and not anchored else ""


def events(
    db: sqlite3.Connection,
    session: str,
    carried: list[dict],
    pulled: dict[str, int],
    cut_ids: set[str],
    flagged: set[str],
    window: int,
) -> list[dict]:
    """The events of the person's messages a frame might carry under the sampler, the oldest first, as the
    index orders them: every one in the stretch (see `stretch`), and every one outside it that a `carried`
    label rests on, in any session. Each message, a row of the index, is one event however it is reached.

    In the stretch an event counts its distance from the end in the person's messages of the stretch (the
    newest at nought); outside it that is nought, and the core gives it no tail. Every event counts how many
    `carried` labels rest on it (`anchored`), how many labels of the home rest on it, of any kind and carried or
    not (`labelled`: the distinct labels the `anchor` table names its id under, read in one query for every
    event), how many pulls name it (`pulled`, by id), and the guard that leaves it out:
    its id is one two messages share (`twin`), it is among `flagged`, or a standing line rests on it and no
    carried label does (`standing`). Its `length`, the room its entry takes in a frame, is not the adapter's to
    know: an event has none here, the caller sets it before the pick, and a pick of one without it fails."""
    rows = stretch(db, session, cut_ids, window)
    his = sum(1 for row in rows if row["voice"] == HIS)
    anchored: dict[str, int] = {}
    for label in carried:
        for anchor in set(label["anchors"]):
            anchored[anchor] = anchored.get(anchor, 0) + 1
    standing = {
        row["said"]
        for row in _rows(
            db, "select anchor.said from anchor join label on label.id = anchor.label where label.kind = 'relation'"
        )
    }
    twins = {
        row["id"] for row in _rows(db, "select id from said where voice != 'pasted' group by id having count(*) > 1")
    }
    labelled = {
        row["said"]: row["labels"]
        for row in _rows(db, "select said, count(distinct label) as labels from anchor group by said")
    }

    def event(row: dict, in_stretch: bool, distance: int) -> dict:
        count = anchored.get(row["id"], 0)
        return {
            "id": row["id"],
            "in_stretch": in_stretch,
            "distance": distance,
            "anchored": count,
            "labelled": labelled.get(row["id"], 0),
            "pulled": pulled.get(row["id"], 0),
            "guard": _guarded(row["id"], count, twins, flagged, standing),
        }

    found: list[tuple[int, dict]] = []
    for row in rows:
        if row["voice"] == HIS:
            found.append((row["seq"], event(row, True, his - 1 - len(found))))
    inside = {row["seq"] for row in rows}
    for said in sorted(anchored):
        for row in _rows(db, f"{_ROWS} where id = ? and voice = ? order by seq", (said, HIS)):
            if row["seq"] not in inside:
                found.append((row["seq"], event(row, False, 0)))
    return [each for _, each in sorted(found, key=lambda pair: pair[0])]
