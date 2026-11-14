"""Read a Claude Code session transcript: who said what, and where the cuts are.

Every counting rule about what a row is lives in this file. Where a row is not what
these rules know, it is skipped, never guessed at. Nothing here keeps or prints text
on its own account; callers decide what leaves.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

# Text the harness puts into a user row that the person did not type.
# How this plugin opens the hand-over it carries across a cut (hooks/crossings.ts). The engine
# files that as a plain user row with no mark on it, so it is known here by its opening. A note
# carried before the plugin said its name as Crossings opens with the older words, and transcripts
# that hold one are read as they always were.
CARRIED = "A note from the Crossings plugin"
CARRIED_BEFORE = "A note from the Crossing plugin"
HARNESS_OPENINGS = ("<", "[SYSTEM NOTIFICATION", "Another Claude session", "Caveat:", CARRIED, CARRIED_BEFORE)
# What the person pasted into a message. The harness wraps it in a pair of tags that carry one id.
PASTE = re.compile(r'<pasted_content(?:\s+id="[^"]*")?\s*>(.*?)</pasted_content(?:\s+id="[^"]*")?\s*>', re.S)


def norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def unpasted(text: str) -> tuple[str, list[str]]:
    """A message as the person typed it, and what they pasted into it.

    A paste is someone else's words that the person handed over. In the typed text each one
    leaves a note of its size where it stood."""
    pastes: list[str] = []

    def noted(found: re.Match) -> str:
        pastes.append(found.group(1).strip())
        return f"[pasted: {len(pastes[-1])} characters]"

    return PASTE.sub(noted, text or ""), pastes


def rows(path: Path) -> Iterator[tuple[int, dict]]:
    with open(path, encoding="utf-8", errors="replace") as handle:
        for number, line in enumerate(handle, 1):
            try:
                row = json.loads(line)
            except ValueError:
                continue
            if isinstance(row, dict):
                yield number, row


def appended(path: Path, start: int = 0) -> Iterator[tuple[int, dict | None]]:
    """The complete lines of a transcript from the byte `start` on, each as the byte just after
    it and its row: None for a line that is not a row. A last line with no newline yet is being
    written, and is not given: it is read whole the next time. `rows` reads the same lines from
    the first; this one is for a reader that keeps how far it read (see store.archive)."""
    with open(path, "rb") as handle:
        handle.seek(start)
        at = start
        for line in handle:
            if not line.endswith(b"\n"):
                return
            at += len(line)
            try:
                row = json.loads(line.decode("utf-8", errors="replace"))
            except ValueError:
                row = None
            yield at, row if isinstance(row, dict) else None


def _message(row: dict) -> dict:
    """A row's `message`, where it is an object; else none: a row of a shape these rules do not
    know is passed over, never guessed at, and never an error."""
    found = row.get("message")
    return found if isinstance(found, dict) else {}


def _blocks(row: dict) -> list[dict]:
    """A row's blocks: its content as one text, or the objects of its list. A text block whose text
    is no string is none."""
    content = _message(row).get("content")
    if isinstance(content, str):
        return [{"type": "text", "text": content}]
    if not isinstance(content, list):
        return []
    return [b for b in content if isinstance(b, dict) and (b.get("type") != "text" or isinstance(b.get("text"), str))]


def _flat(value) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(_flat(v) for v in value)
    if isinstance(value, dict):
        return " ".join(_flat(v) for v in value.values())
    return "" if value is None else str(value)


def ident(row: dict) -> str:
    """The short form of a row's own id. A fork or a resume writes a new file in which a
    message sits on another line and keeps this id, so an anchor names the id."""
    return str(row.get("uuid") or "")[:8]


def sidechain(row: dict) -> bool:
    """Whether the harness marks a row as a subagent's own (`isSidechain`)."""
    return row.get("isSidechain") is True


def is_summary(row: dict) -> bool:
    return bool(row.get("isCompactSummary"))


def is_boundary(row: dict) -> bool:
    return row.get("type") == "system" and row.get("subtype") == "compact_boundary"


def person(row: dict, whole: bool = False) -> list[str]:
    """What the person wrote in this row: typed at the prompt, or sent while a turn ran.

    With `whole`, each text is given as it was sent, pastes included, for an archive; otherwise
    white space is folded and what was pasted is left out, for counting: a paste is not the
    person's words. A row a subagent's conversation holds (`isSidechain`) is no one's here: its
    prompt was written by the session, not the person."""
    if sidechain(row):
        return []
    if row.get("type") == "attachment":
        held = row.get("attachment") if isinstance(row.get("attachment"), dict) else {}
        origin = held.get("origin") if isinstance(held.get("origin"), dict) else {}
        human = origin.get("kind") == "human" or held.get("humanTurn") is True
        prompt = held.get("prompt") if isinstance(held.get("prompt"), str) else ""
        if held.get("type") == "queued_command" and human and norm(prompt):
            return [prompt.strip() if whole else norm(prompt)]
        return []
    # A tool's result, of whatever shape the harness gives it, is no one's words.
    if row.get("type") != "user" or row.get("toolUseResult") is not None or row.get("isMeta") or is_summary(row):
        return []
    said = []
    for block in _blocks(row):
        if block.get("type") != "text":
            continue
        sent = block.get("text", "")
        typed = norm(PASTE.sub(" ", sent))
        if typed.startswith(HARNESS_OPENINGS) or "system-reminder" in typed[:60]:
            continue
        if whole and (typed or PASTE.search(sent)):
            said.append(sent.strip())  # a message that is only a paste is still kept
        elif typed and not whole:
            said.append(typed)
    return said


SYNTHETIC = "<synthetic>"  # the model a row names where the harness wrote it in the session's place


def synthetic(row: dict) -> bool:
    """Whether the harness wrote this row in the session's place (its model is SYNTHETIC), as when it
    says the person is not logged in: nobody's words."""
    return _message(row).get("model") == SYNTHETIC


def session(row: dict, whole: bool = False) -> list[str]:
    """What the session said to the person in this row (its prose, not its tool calls). A subagent's
    row (`isSidechain`) is said to the session that started it, and not to the person; a row the
    harness wrote in the session's place (`synthetic`) is said by no one."""
    if row.get("type") != "assistant" or sidechain(row) or synthetic(row):
        return []
    texts = [b.get("text", "") for b in _blocks(row) if b.get("type") == "text"]
    return [t.strip() if whole else norm(t) for t in texts if norm(t)]


def model(row: dict) -> str:
    """The model a row of the session's own voice names, or nothing. A row of the person's names
    none, and a row the harness wrote in the session's place names `<synthetic>`, which is no model.
    A name is taken only where it passes the check a hook's model passes (layer.named): one with a
    space or a line break in it would be two words, or two lines, of the files that keep it."""
    from crossing.layer import named  # here: layer reads the store, which reads this file

    if row.get("type") != "assistant":
        return ""
    return named(_message(row).get("model"))


def tool_traffic(row: dict) -> tuple[int, int]:
    """Characters of tool calls and of tool results in this row."""
    calls = results = 0
    for block in _blocks(row):
        if block.get("type") == "tool_use":
            calls += len(json.dumps(block.get("input")))
        elif block.get("type") == "tool_result":
            results += len(_flat(block.get("content")))
    return calls, results


@dataclass
class Cut:
    line: int  # the boundary's line, or the last line when it is not written yet
    summary_line: int | None  # the line of the summary that follows it
    summary: str
    meta: dict  # the harness's own figures for the cut, when it gives them


# The harness's figures for a cut that are read, each with the kind of value it must be: a figure of
# any other shape is none, and the cut is still the cut, with no such figure.
FIGURES = {"trigger": (str,), "preTokens": (int, float), "postTokens": (int, float), "durationMs": (int, float)}


def figures(meta) -> dict:
    """Of a boundary's `compactMetadata`, the figures of FIGURES whose value has its kind (a number
    is never a truth value); nothing where it is no object."""
    if not isinstance(meta, dict):
        return {}
    return {name: meta[name] for name, kinds in FIGURES.items() if type(meta.get(name)) in kinds}


def cuts(path: Path) -> list[Cut]:
    found: list[Cut] = []
    for number, row in rows(path):
        if is_boundary(row):
            found.append(Cut(number, None, "", figures(row.get("compactMetadata"))))
        elif is_summary(row) and found and found[-1].summary_line is None:
            found[-1].summary_line = number
            found[-1].summary = norm(" ".join(b.get("text", "") for b in _blocks(row) if b.get("type") == "text"))
    return found


def last_written(path: Path) -> tuple[int, int, Cut]:
    """The last cut the transcript holds: its ordinal in the session, the line its span
    starts after, and the cut."""
    known = cuts(path)
    if not known:
        raise LookupError("the transcript holds no cut")
    start = (known[-2].summary_line or known[-2].line) if len(known) > 1 else 0
    return len(known), start, known[-1]


def _spoken_after(path: Path, line: int) -> bool:
    """Whether a row after this line of the transcript holds words of either voice."""
    return any(number > line and (person(row) or session(row)) for number, row in rows(path))


def locate(path: Path, summary: str | None = None) -> tuple[int, int, Cut]:
    """The cut a hook is being called about: its ordinal, the line its span starts after,
    and the cut.

    The harness calls SessionStart and then PostCompact before it writes the boundary, so at
    both moments the transcript does not hold the cut yet and the span runs to the end of the
    file. When a summary is handed over and the transcript already holds a cut with that
    summary, and nothing of either voice was said after that cut's summary, that cut is the one:
    the hook is being called again about it. A summary is a later cut's where something was said
    since, though it retell the one before word for word: that is the case the retelling line is
    for, and the later cut is a cut of its own, with the next ordinal.
    """
    known = cuts(path)
    wanted = norm(summary or "")
    if wanted:
        for index in range(len(known) - 1, -1, -1):
            if known[index].summary and known[index].summary[:400] == wanted[:400]:
                if _spoken_after(path, known[index].summary_line or known[index].line):
                    break  # said since that cut: this summary is a new cut's
                start = (known[index - 1].summary_line or known[index - 1].line) if index else 0
                return index + 1, start, known[index]
    with open(path, "rb") as handle:  # every line, also one that is not a row
        last = sum(1 for _ in handle)
    start = (known[-1].summary_line or known[-1].line) if known else 0
    return len(known) + 1, start, Cut(last + 1, None, wanted, {})
