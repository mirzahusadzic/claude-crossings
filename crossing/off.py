"""Off the record: when the person's switch for a project was off, and what was said then.

Each time the person switches Crossing off for a project, and each time they switch it on again,
the moment is kept in one plain file of the home, `off.txt`: a line a span, its two moments in
UTC, the last one with one moment alone while the project is off. Only the switch writes it
(store.switch). Nothing said inside a span is ever kept, by any reading of any transcript: a
message is off the record by when it was said, as the transcript's own time for it gives it, and
not by when it is archived. Nothing of what was said then is written here: no count, no id.

A span is recorded from the moment it begins. One that was never recorded (an older make of the
plugin, or a switch written by hand) is not guessed at.
"""

from __future__ import annotations

import datetime
import os
import re
import time
from pathlib import Path
from typing import Iterable, Iterator

from .record import lines_in, lines_of, nameable, within

FILE = "off.txt"
HEAD = (
    "# When Crossings was switched off for this project, and on again, in UTC: nothing said between is kept.\n"
    "# One line a span; a line with one moment alone is a span still open.\n"
)
UTC = datetime.timezone.utc
STAMP = re.compile(r"(\d{4})-(\d\d)-(\d\d)[T ](\d\d):(\d\d):(\d\d)(?:[.,](\d{1,9}))?(Z|[+-]\d\d:?\d\d)", re.I)

# The shape of a moment as a transcript writes one, its zone given or not: a time of any other shape is
# no time, and the archive keeps none for it (see store.archive).
SHAPE = re.compile(r"\d{4}-\d\d-\d\d[T ]\d\d:\d\d:\d\d(?:[.,]\d{1,9})?(?:Z|[+-]\d\d:?\d\d)?", re.I)

Span = tuple  # (start, end): two moments, the end None while the span is open


def moment(value) -> datetime.datetime | None:
    """A time as a transcript or this file writes it, in UTC; or nothing, where it cannot be read
    as one. A time that names no zone cannot be told apart from a local one, and is not read."""
    if not isinstance(value, str):
        return None
    found = STAMP.fullmatch(value.strip())
    if found is None:
        return None
    year, month, day, hour, minute, second, fraction, zone = found.groups()
    if zone.upper() == "Z":
        offset = datetime.timedelta(0)
    else:
        digits = zone[1:].replace(":", "")
        offset = (1 if zone[0] == "+" else -1) * datetime.timedelta(hours=int(digits[:2]), minutes=int(digits[2:]))
    try:
        return datetime.datetime(
            int(year),
            int(month),
            int(day),
            int(hour),
            int(minute),
            int(second),
            int((fraction or "0")[:6].ljust(6, "0")),
            tzinfo=datetime.timezone(offset),
        ).astimezone(UTC)
    except ValueError:  # a month, a day, an hour or a zone that is none
        return None


def now() -> str:
    """This moment, as the file keeps it."""
    return datetime.datetime.now(UTC).isoformat(timespec="microseconds")


def steady() -> float:
    """A clock that is never set back: seconds since the computer started, the time it slept
    counted where the system counts it (CLOCK_BOOTTIME, else CLOCK_MONOTONIC). Its reading as the
    switch turns a home off is kept in the person's record (see store._spans_kept), so that a span
    can be closed whole where the clock of the day was set back meanwhile (see `closed`)."""
    which = getattr(time, "CLOCK_BOOTTIME", None) or getattr(time, "CLOCK_MONOTONIC", None)
    return time.clock_gettime(which) if which is not None else time.monotonic()


def _lines(folder: Path) -> list[str]:
    """The file's lines as they stand, bytes that are no text kept as they are; none where there is
    no file. A file that is there and cannot be read is said so (OSError): what was said is then
    not archived at all, rather than archived as though no span were in it."""
    try:
        return lines_of(within(folder, FILE).read_text(encoding="utf-8", errors="surrogateescape"))
    except FileNotFoundError:
        return []


def _parsed(lines: list[str]) -> tuple[list[tuple[int, datetime.datetime, datetime.datetime | None]], int]:
    """Each span the lines hold, with the number of its line; and how many lines are no span and
    were passed over (see `_sorted`)."""
    found, passed = _sorted(lines)
    return found, len(passed)


def _sorted(lines: list[str]) -> tuple[list[tuple[int, datetime.datetime, datetime.datetime | None]], list[int]]:
    """Each span the lines hold, with the number of its line; and the numbers of the lines that are
    no span. A span is one moment and, unless it is still open, a second as late or later. Only the
    last span can be open: an open one with another after it is no span."""
    found, passed = [], []
    for n, line in enumerate(lines):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        parts = line.split()
        times = [moment(part) for part in parts]
        if len(parts) not in (1, 2) or None in times or (len(times) == 2 and times[1] < times[0]):
            passed.append(n)
            continue
        found.append((n, times[0], times[1] if len(times) == 2 else None))
    shut = [each for each in found[:-1] if each[2] is not None] + found[-1:]
    kept = {each[0] for each in shut}
    return shut, sorted(passed + [each[0] for each in found if each[0] not in kept])


def untold(lines: list[str]) -> bool:
    """Whether the lines hold one that is no span after the last span from FIRST, which keeps
    everything said before its end off the record (see `everything_before`): what such a line
    held can no longer be told, and nothing is archived until the person switches on again (see
    store.lost). A line that is no span before such a span is kept off by it, whatever it held."""
    found, passed = _sorted(lines)
    first = moment(FIRST)
    covered = max((n for n, start, end in found if start == first and end is not None), default=-1)
    return any(n > covered for n in passed)


def counted(lines: list[str]) -> int:
    """How many spans the lines hold: a line that is no span, a blank one or a comment is none of
    them (see `_sorted`). The person's record keeps this count each time the switch writes the file
    (see store.lost), so that a span's line blanked or turned into a comment is missed by it."""
    return len(_sorted(lines)[0])


def spans(folder: Path) -> tuple[list[Span], int]:
    """The spans of the home, in the file's order; and how many of its lines could not be read.
    A file that is not there holds none."""
    found, unread = _parsed(_lines(folder))
    return [(start, end) for _, start, end in found], unread


def told(folder: Path) -> tuple[list[Span], int]:
    """The spans and the lines passed over, for showing them: a file that cannot be read at all
    shows no span, and one line that could not be read."""
    try:
        return spans(folder)
    except OSError:
        return [], 1


def _write(folder: Path, lines: list[str]) -> None:
    """The file whole, written beside itself and put in its place, so that it is never left half
    written. Lines that could not be read stay as they were."""
    fresh = within(folder, FILE + ".new")
    fresh.write_text("".join(line + "\n" for line in lines), encoding="utf-8", errors="surrogateescape")
    os.replace(fresh, within(folder, FILE))


def opened(folder: Path) -> bool:
    """Keep that the project is switched off from this moment: a new span, open. Where the last
    span is open already, it stays as it is, from its earlier moment. Gives whether one was opened."""
    lines = _lines(folder)
    found, _ = _parsed(lines)
    if found and found[-1][2] is None:
        return False
    _write(folder, (lines or HEAD.splitlines()) + [now()])
    return True


def closed(folder: Path, since: float | None = None) -> bool:
    """Keep that the project is switched on again at this moment: the open span is closed. Gives
    whether there was one to close.

    Where the clock reads earlier now than when the span was opened, it was set back while the
    switch was off. What was said before it went back bears times after this moment's, and what
    was said after it bears times before the span's opening. The span is then closed as far past
    its opening as the steady clock (see `steady`) has run since `since`, its reading as the span
    was opened; where that cannot be told (none was kept, or the computer was started again
    since), as far past its opening as the clock was found to have gone back. And a second span
    is kept, closed at this moment, of the line's own form: from this moment less what the steady
    clock ran, so that what was said after the clock went back is off as well; where that cannot
    be told, from FIRST, as `everything_before` keeps it. Spans closed so may keep off what is
    said in the moments before the switch was turned off, or after it is turned on: nothing said
    while it was off is kept."""
    lines = _lines(folder)
    found, _ = _parsed(lines)
    if not found or found[-1][2] is not None:
        return False
    n, opened = found[-1][0], found[-1][1]
    stamp = now()
    end = moment(stamp)
    more = []
    if end is not None and end < opened:  # the clock was set back while the switch was off
        ran = steady() - since if since is not None else -1.0
        back = (end - datetime.timedelta(seconds=ran)).isoformat(timespec="microseconds") if ran >= 0 else FIRST
        more = [f"{back} {stamp}"]  # what was said after the clock went back, by the clock as it reads now
        stamp = (opened + (datetime.timedelta(seconds=ran) if ran >= 0 else opened - end)).isoformat(
            timespec="microseconds"
        )
    lines[n] = f"{lines[n].strip()} {stamp}"
    _write(folder, lines + more)
    return True


FIRST = "1970-01-01T00:00:00.000000+00:00"  # earlier than any transcript's time: "everything before"


def everything_before(folder: Path) -> None:
    """Keep that everything said before this moment is off the record: a span from FIRST to now.
    The switch writes it where the record of the spans was found missing, holding fewer than it did
    or damaged (see store.lost), since what it held can no longer be told."""
    lines = _lines(folder)
    _write(folder, (lines or HEAD.splitlines()) + [f"{FIRST} {now()}"])


# The ids of the rows a reading found inside a span, one a line, by id alone: never archived, by any
# reading, whether the record of the spans is there or not (see store.archive).
UNSAID = "unsaid.txt"


def unsaid(folder: Path) -> set[str]:
    """The ids kept in UNSAID. A line that is no id is passed over."""
    try:
        lines = lines_in(within(folder, UNSAID))
    except OSError:
        return set()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def unsaid_held(folder: Path) -> int:
    """How many ids UNSAID holds, each once, of the form `keep_unsaid` writes: a line blanked or
    damaged is none of them. Nought where there is no file; a file that is there and cannot be read
    is said so (OSError). The person's record keeps this count each time the switch writes the
    record of the spans (see store.lost)."""
    try:
        lines = lines_in(within(folder, UNSAID))
    except FileNotFoundError:
        return 0
    return len({line.strip() for line in lines if not line.startswith("#") and nameable(line.strip())})


def keep_unsaid(folder: Path, ids: list[str]) -> None:
    """Add these ids to UNSAID, each once. An id that is no name (record.ident) is left out."""
    there = unsaid(folder)
    new = [each for each in dict.fromkeys(ids) if each not in there and nameable(each)]
    if not new:
        return
    path = within(folder, UNSAID)
    fresh = not path.exists()
    with open(path, "a", encoding="utf-8") as handle:
        if fresh:
            handle.write("# What was said while Crossings was off, by id alone: never archived.\n")
        handle.write("".join(each + "\n" for each in new))


def inside(at: datetime.datetime, kept: list[Span]) -> Span | None:
    """The span this moment falls in, or nothing."""
    for start, end in kept:
        if start <= at and (end is None or at <= end):
            return (start, end)
    return None


def _between(before: datetime.datetime | None, after: datetime.datetime | None, kept: list[Span]) -> bool:
    """Whether a message with no time of its own, between a row of this time and one of that, may
    have been said inside a span: a row on either side is not known, or lies in one, or a span
    begins or ends between them."""
    if before is None or after is None or inside(before, kept) or inside(after, kept):
        return True
    return any(before <= start <= after or (end is not None and before <= end <= after) for start, end in kept)


def judged(
    items: Iterable[tuple[object, dict | None]], kept: list[Span], before: datetime.datetime | None = None
) -> Iterator[tuple[object, dict | None, datetime.datetime | None, bool]]:
    """Each line of a transcript, as (key, row), with its own time, and whether it was said
    inside a span. With no span at all, nothing is.

    A row with no time, or one that cannot be read as one, takes its place from the nearest rows
    on either side that have one, in the same file: it is off unless both are outside every span
    and no span begins or ends between them. `before` is the time of the last such row before the
    first line given, where the reading goes on from a marker. A row with none before it, or none
    after it yet, is off: at the end of a file, a whole reading decides it again once a row comes
    after it."""
    pending: list[tuple[object, dict | None]] = []
    for key, row in items:
        at = moment(row.get("timestamp")) if isinstance(row, dict) else None
        if not kept:
            yield key, row, at, False
            continue
        if at is None:
            pending.append((key, row))
            continue
        for waited, its in pending:
            yield waited, its, None, _between(before, at, kept)
        pending = []
        yield key, row, at, inside(at, kept) is not None
        before = at
    for waited, its in pending:
        yield waited, its, None, True


def last(at: datetime.datetime | None, kept: list[Span]) -> str:
    """The time a marker keeps of the last row read with one, so that a row with no time read
    next takes its place from it: a moment outside every span as it is, and one inside a span as
    that span's beginning, which the file holds already."""
    if at is None:
        return ""
    span = inside(at, kept)
    return (span[0] if span else at).isoformat(timespec="microseconds")


def said_at(at: datetime.datetime) -> str:
    """A moment as the archive's times are written (`2026-01-01T09:00:00.000Z`), for placing a
    span among the messages, which are in the order of those times."""
    return at.strftime("%Y-%m-%dT%H:%M:%S.") + f"{at.microsecond // 1000:03d}Z"


def shown(span: Span) -> tuple[str, str]:
    """A span's two moments as text, to the second, the second nothing while it is open."""
    start, end = span
    fmt = "%Y-%m-%d %H:%M:%S UTC"
    return start.strftime(fmt), end.strftime(fmt) if end is not None else ""
