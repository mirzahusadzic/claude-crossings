"""Count what stood before a cut and how much of each voice its summary holds word for word.

"Word for word" is the whole claim. A summary can carry a reply's substance in other
words and get no credit here; matching words are not carriage either. The numbers say
where to look, and nothing more.
"""

from __future__ import annotations

import base64
import hashlib
import re
import time
from pathlib import Path

from . import transcript

RUN = 24  # characters in a row that count as "the summary holds this"
SHORT = 12  # a message shorter than this is too short to judge: any summary may hold it by chance
SENTENCE = 40  # a sentence shorter than this is not counted as one
DIGEST = 4  # bytes of a run's digest: enough that two runs are taken for one about once in four billion


class Late(Exception):
    """The count's time ran out inside the matching of one message (see `covered`)."""


def covered(text: str, summary: str, run: int = RUN, deadline: float | None = None) -> int:
    """Characters of text lying in some run of `run` or more that the summary holds. Each step
    searches the whole summary, so a long message against a long summary is slow: past `deadline`
    (by time.monotonic) it stops, and says so (`Late`), between two runs as at each step that
    lengthens one."""
    total = at = 0
    while at + run <= len(text):
        if deadline is not None and time.monotonic() > deadline:
            raise Late
        if text[at : at + run] in summary:
            end = at + run
            while end < len(text) and text[at : end + 1] in summary:
                if deadline is not None and time.monotonic() > deadline:
                    raise Late
                end += 1
            total += end - at
            at = end
        else:
            at += 1
    return total


def runs(text: str, key: bytes, run: int = RUN) -> set[bytes]:
    """The digests of every run of `run` characters a text holds, keyed with the home's own key
    (see record.runs_key): what a later summary is compared with, so that no text is kept. Without
    the key a digest could be checked against a guess, and a run that begins where a known one
    ends could be found from it character by character."""
    return {
        hashlib.blake2b(text[at : at + run].encode("utf-8"), key=key, digest_size=DIGEST).digest()
        for at in range(len(text) - run + 1)
    }


def retold(text: str, before: set[bytes], key: bytes, run: int = RUN) -> int:
    """Characters of a text lying in some run of `run` characters whose digest is among `before`,
    the runs of an earlier text: how much of it repeats that one word for word."""
    total = end = 0
    for at in range(len(text) - run + 1):
        if hashlib.blake2b(text[at : at + run].encode("utf-8"), key=key, digest_size=DIGEST).digest() in before:
            total += at + run - max(at, end)
            end = at + run
    return total


def packed(found: set[bytes]) -> str:
    """Digests as the sidecar keeps them: in their order, one string."""
    return base64.b64encode(b"".join(sorted(found))).decode("ascii")


def unpacked(text: object) -> set[bytes] | None:
    """Digests as `packed` keeps them; or nothing, where it is no such string."""
    try:
        data = base64.b64decode(text, validate=True) if isinstance(text, str) else None
    except ValueError:
        return None
    if data is None or len(data) % DIGEST:
        return None
    return {data[at : at + DIGEST] for at in range(0, len(data), DIGEST)}


def sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text) if len(s) >= SENTENCE]


def voice(messages: list[tuple[int, str, str]], summary: str, deadline: float) -> dict:
    """One voice's count. `messages` are (line, id, text). Past the deadline nothing is guessed:
    the count is marked unfinished, whether the deadline passed between two messages or in the
    matching of one."""
    out = {
        "messages": len(messages),
        "chars": sum(len(t) for _, _, t in messages),
        "whole": 0,
        "too_short": 0,
        "covered": 0,
        "sentences": 0,
        "sentences_found": 0,
        "finished": True,
        "pointers": [],
    }
    for line, ident, text in messages:
        if time.monotonic() > deadline:
            out["finished"] = False
            break
        if len(text) < SHORT:  # "Yes" is in every summary; it says nothing about this one
            out["too_short"] += 1
            out["pointers"].append({"line": line, "id": ident, "chars": len(text), "held": 0})
            continue
        whole = text in summary
        try:
            held = len(text) if whole else covered(text, summary, deadline=deadline)
        except Late:  # out of time inside this message: unfinished, as between two of them
            out["finished"] = False
            break
        out["whole"] += whole
        out["covered"] += held
        parts = sentences(text)
        out["sentences"] += len(parts)
        out["sentences_found"] += sum(1 for s in parts if s in summary)
        out["pointers"].append({"line": line, "id": ident, "chars": len(text), "held": held})
    return out


def count(
    path: Path,
    summary: str | None = None,
    seconds: float = 8.0,
    pending: bool = False,
    spans: list = (),
    key: bytes | None = None,
    earlier=None,
    untold: bool = False,
    unsaid: frozenset = frozenset(),
) -> dict:
    """The counted part of the record of one cut of the transcript at `path`.

    With `pending`, the cut is the one a hook is being called about, which the transcript
    may not hold yet; without a summary nothing can be traced, and the count says so.
    Otherwise it is the last cut the transcript holds.

    A row said while the person's switch was off, inside one of `spans` (see crossing/off.py),
    is not counted at all: no message, no character and no pointer of it is kept; nor is a row whose
    id is among `unsaid`, the ids the home keeps as said while it was off (see off.UNSAID). With `untold`,
    what the home's record of those spans held cannot be told (see store.lost), so what was said
    off the record cannot be told from the rest: nothing said is counted or listed, and the count
    says so (`untold`), for the page to say it.

    With the home's `key`, the summary's runs are kept as digests (`summary_runs`), for the next
    cut to compare with; and where `earlier`, asked with this cut's ordinal, gives the digests of
    the summary of the same session's cut before, how many of its characters repeat that one
    (`retold`; nothing where there is none to compare with). Neither is a text.
    """
    from . import off  # here: off reads a home through record, which takes its figures from this file
    from .record import nameable

    if pending or summary is not None:
        ordinal, start, cut = transcript.locate(path, summary)
    else:
        ordinal, start, cut = transcript.last_written(path)
    his: list[tuple[int, str, str]] = []
    typed = sent_mid_turn = 0
    own: list[tuple[int, str, str]] = []
    calls = results = 0
    for line, row, _, inside in off.judged(transcript.rows(path), list(spans)):
        if line <= start or inside or untold or (unsaid and str(row.get("uuid") or "") in unsaid):
            continue
        if line >= cut.line:
            break
        # A subagent's row is no one's here, its tool traffic too; and a row whose id is no name is
        # passed over as every reading passes it over: it is archived by none, and no pointer names it.
        if transcript.sidechain(row) or not nameable(str(row.get("uuid") or "")):
            continue
        # One message a row, its text blocks joined as the archive joins them.
        said = transcript.norm("\n\n".join(transcript.person(row)))
        if said:
            if row.get("type") == "attachment":
                sent_mid_turn += 1
            else:
                typed += 1
            his.append((line, transcript.ident(row), said))
        spoken = transcript.norm("\n\n".join(transcript.session(row)))
        if spoken:
            own.append((line, transcript.ident(row), spoken))
        c, r = transcript.tool_traffic(row)
        calls, results = calls + c, results + r
    deadline = time.monotonic() + seconds
    before = earlier(ordinal) if key and earlier is not None else None
    person = voice(his, cut.summary, deadline)
    person["typed"], person["sent_mid_turn"] = typed, sent_mid_turn
    return {
        "cut": ordinal,
        "traced": bool(cut.summary),
        "boundary_line": cut.line,
        "summary_line": cut.summary_line,
        "span_starts_after": start,
        "trigger": cut.meta.get("trigger"),
        "tokens_before": cut.meta.get("preTokens"),
        "tokens_after": cut.meta.get("postTokens"),
        "cut_ms": cut.meta.get("durationMs"),
        "summary_chars": len(cut.summary),
        "summary_runs": packed(runs(cut.summary, key)) if key else None,
        "retold": retold(cut.summary, before, key) if before is not None else None,
        "person": person,
        "session": voice(own, cut.summary, deadline),
        "tool_call_chars": calls,
        "tool_result_chars": results,
        **({"untold": True} if untold else {}),
    }
