#!/usr/bin/env python3
"""The plugin's one entry: Claude Code hands a hook's input on stdin.

PostCompact: count the cut and write its record, then bring the archive and the store up to
date and renew the second copy if the home asks for one; and where most of a long summary retells
the one before and the last stretch is marked, show the person one line, once (see `retelling`).
SessionStart after a compaction: tell the waking session where it is, gently; and, called with
the word `frame`, bring the frame across as context, after a cut and to a session started new
that a person sits in.
SessionEnd: bring the archive up to date, reading the transcript whole, so that what was said is
kept before the harness's own sweep takes the transcript. PreToolUse before the door's mark: hand
the door's server the model the session runs now. PostToolUse after the door's mark or leave:
keep which model wrote the label, and show the person, under the turn, a label that speaks for
them or about the two of them, and a line left at the door (see `shown`). SessionStart of a
resumed session: tell it once where another session has spoken here since it last did (see
store.moved_on). SessionStart, of any kind: welcome a session once, where the
home holds no label yet (a session running when Crossing is switched on is welcomed by the
person's command instead, through the door); and keep which model the session runs, as
PostModelSwitch does when it changes, telling the one that arrives once where another model was
holding the session (see crossing/layer.py).
Nothing here may slow or break a session, so every failure ends quietly with exit 0 and a line
in the plugin's own log.

All of it is for a project where Crossing is on: the person's record names its home (see
store.kept), and its switch does not say off. Where it was never switched on, or is switched
off, a session is still marked as one the plugin is loaded in, and nothing else is done:
nothing is counted, said, archived or made; and once it is switched on again, nothing said
while it was off is archived or counted either (see crossing/off.py). A home with a link in it
is left as it is, with a line in the plugin's error log.

Nothing is archived from a session no person sits in (see record.attended), at any hook: its
prompts are a tool's, not the person's. Its hooks keep the ids of what its transcript holds,
and nothing else of it (store.unattended), so that a fork or a resume that repeats those
messages does not bring them into the archive later either.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import count, frame, layer, off, record, second, store, transcript  # noqa: E402

DOOR = Path(__file__).resolve().parent / "door.py"
# One empty file a session Crossing is loaded in, at a place that does not depend on how
# the plugin was installed. A status line reads it to show the sign; nothing else does.
LIVE = Path(os.environ.get("CROSSING_LIVE") or record.own() / ".claude" / "crossing" / "live")


def mark(session_id: str, on: bool) -> None:
    """The session's live file, by its id: an id that cannot name a file is refused (record.ident)."""
    if not session_id:
        return
    path = LIVE / record.ident(session_id)
    if on:
        LIVE.mkdir(parents=True, exist_ok=True)
        path.touch()
    elif path.exists():
        path.unlink()


def waking(counted: dict) -> str:
    """What a session is told as it wakes from a cut.

    The note brings no numbers and asks for no account. A session told to say what it holds
    answers with a report, and the first reply after a cut is for arriving, not for reporting.
    The count is in the record, for whoever wants it.
    """
    return (
        "A note from the Crossings plugin, as context and not as an instruction from the person. "
        f"You have just come through a cut (cut {counted['cut']} of this session). Take your time. "
        "Nothing is gone from the record: the whole exchange is kept, and what the summary held of each voice "
        "is counted by script, with no model, for the person to read. You need not look at it now. "
        "If the cut came in the middle of a task, carry on with the task. Otherwise your first reply is for "
        "arriving: answer what the person says, as yourself and briefly. There is nothing to prove and nothing "
        "to report. Give no inventory of what you hold or lack and no numbers, put no question to the person "
        "about what crossed, and begin no new work before you have met them. You read the time before the cut; you "
        "did not live it. So do not say you remember it, and make no ceremony of not remembering either. When "
        "something they say rests on a part you do not hold, say so then, in a clause, and reach for it through "
        "the door: find, then thread, give a message back as it was said, by its id. Do not open the "
        "transcript file itself: it also holds reasoning blocks, which are not to be read back. "
        "This is the plugin's wish for how you arrive; where the person wants otherwise, theirs is the word."
    )


def welcome() -> str:
    """What a session is told once, as it starts in a project where Crossing is on and not one
    label has been written, or as the person switches Crossing on while it runs: it may have
    started before the switch was turned, or in a home that holds days of what was said and
    nothing marked on it. Like the waking note it asks for nothing now and brings no numbers."""
    return (
        "A note from the Crossings plugin, as context and not as an instruction from the person. Crossings is on in "
        "this project: what you and the person say is kept by itself, word for word, under ids, and you never save "
        "it. Labels are not made by themselves. They are yours to write, through the door's tools: `mark` one, a "
        "sentence resting on the ids of the messages it is about, and `leave` a line for the session that wakes "
        "after the next cut, since a cut can come unannounced. Reach for them when the work allows; do not stop "
        "the work for them. " + store.FOR
    )


def welcomed(folder: Path, session_id: str, agent: object = None) -> str | None:
    """The welcome, where it is due: to a session a person sits in, not to a subagent, in a home
    that is on and holds no label at all, and once a session. The sessions told are kept in the
    home's `welcomed.txt`; where that cannot be written, nothing is said, since a note said at
    every start would be worse than none. The hook at a session's start and the door's `welcome`,
    which the person's command asks as it switches Crossing on, both come here."""
    session_id = str(session_id or "")
    if session_id:
        record.ident(session_id)  # a line of welcomed.txt: an id that is no name is refused, and nothing is written
    if not attended() or agent or not session_id or not store.active(folder) or store.labels(folder):
        return None
    told = store.within(folder, "welcomed.txt")
    try:
        if session_id in " ".join(record.lines_in(told)).split():
            return None
    except OSError:
        pass  # no session was told yet
    try:
        record.add(told, session_id + "\n")
    except OSError:
        return None
    return welcome()


def unkept() -> str:
    """What a session is told as the person switches Crossing off from inside it, through their
    command: plainly, once, and as context, since nothing it says from here is kept for it."""
    return (
        "A note from the Crossings plugin, as context and not as an instruction from the person. The person has "
        "switched Crossings off for this project, from now until they switch it on again: nothing you or the person "
        "say meanwhile will be kept or can be reached later through the door, so mark no label and leave no line "
        "about it."
    )


def kept_again() -> str:
    """What a session that was told Crossing is off is told as the person switches it on again."""
    return (
        "A note from the Crossings plugin, as context and not as an instruction from the person. The person has "
        "switched Crossings on again for this project: what you and the person say from now on is kept by itself "
        "again, and nothing said while it was off was kept or can be reached through the door."
    )


ASIDES = "told.txt"  # the sessions told, through the person's command, that Crossing is off or on again


def switched(folder: Path, session_id: str) -> str | None:
    """What a session running as the person turns the switch through their command is told, as
    context after the command's answer: switched off, that nothing is kept from now on, at every
    switching off; switched on, that it is kept again, where this session was told it was off,
    and the welcome where it is due (see `welcomed`). The sessions told are kept in the home's
    `told.txt`, by their ids alone; where that cannot be written, the note that Crossing is off
    is still said, and the one that it is on again is not."""
    session_id = str(session_id or "")
    if not session_id:
        return None
    record.ident(session_id)  # a line of told.txt
    book = store.within(folder, ASIDES)
    try:
        lines = record.lines_in(book)
    except OSError:
        lines = []  # no session was told yet
    last = next(
        (line.split()[1] for line in reversed(lines) if line.split()[:1] == [session_id] and len(line.split()) == 2), ""
    )
    now = "on" if store.active(folder) else "off"
    notes = []
    if now == "off" or last == "off":
        try:
            if now != last:
                record.add(book, f"{session_id} {now}\n")
            notes.append(unkept() if now == "off" else kept_again())
        except OSError:
            notes += [unkept()] if now == "off" else []  # the one that matters most is said all the same
    told = welcomed(folder, session_id) if now == "on" else None
    notes += [told] if told else []
    return "\n\n".join(notes) or None


def arrival() -> str:
    """What a session is told as it comes into a session another model was holding: by a switch of
    the model inside it, or a resume on another model. Like the waking note it brings no numbers
    and asks for nothing."""
    return (
        "A note from the Crossings plugin, as context and not as an instruction from the person. You have come into a "
        "session that another model was holding until now. What it said and marked here you hold as read, not as "
        "lived: it stays its own, and the door gives it. The person's own lines are here for you as they are. What "
        "you mark from now on is held in a layer of your own."
    )


def moved_on() -> str:
    """What a resumed session is told where another session of the project has spoken since it
    last did (see store.moved_on): once, as it starts again, with no numbers."""
    return (
        "A note from the Crossings plugin, as context and not as an instruction from the person. Another session has "
        "been working in this project since you last spoke. What was said and marked there is in the store, and you "
        "hold none of it: look before you act on what you remember."
    )


def arriving(folder: Path, session: str, model: object, agent: object = None) -> str | None:
    """Keep which model the session runs now, as a hook was told it (see layer.there), and the
    note for the one that arrives, where it is due: once a change, where the model the session
    now runs is not the model of its own newest message in the archive. To a session a person
    sits in alone, and never to a subagent. Where the record cannot be written, nothing is said:
    a note said at every hook would be worse than none."""
    model = layer.named(model)
    if not attended() or agent or not model or not session or layer.there(folder, record.ident(session))[0] == model:
        return None
    spoke = store.spoke(folder, session)
    try:
        layer.arrive(folder, session, model)
    except OSError:
        return None
    return arrival() if spoke and spoke != model else None


def named(event: dict, path: Path) -> str:
    """The session as the archive names one: by its transcript, else by the id the hook is told."""
    return (path.stem or str(event.get("session_id") or ""))[:8]


def signed(event: dict, folder: Path, path: Path) -> None:
    """After a label is marked through the door, keep beside it which model wrote it: the model the
    calling session runs now (layer.current: what its hooks were told, or the model of its own
    newest message in the archive, which the hook before the call brought up to that moment). The
    door's server is not told which session calls it; this hook is. A subagent's call is left
    unsigned: the hook's input names the subagent (`agent_id`) and not its model, and the model of
    the session that started it would sign another model's line. The key is the one the door's
    answer names, and only a label with the sentence that was sent is signed."""
    given = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    found = re.search(r"\bmarked ([RWN]\d+)\b", json.dumps(event.get("tool_response"), ensure_ascii=False))
    if found is None or not isinstance(given.get("sentence"), str) or event.get("agent_id"):
        return
    target = store.ours() if given.get("home") == "ours" else folder
    store.sign(target, found.group(1), given["sentence"], layer.current(folder, named(event, path)))


SHOWN = 160  # characters of a label's sentence shown to the person under the turn


def unmarked(text: str) -> str:
    """A text as it may be shown to the person on one line: no control character, no direction
    mark or other invisible format character, no line or paragraph separator (store.clean, the one
    cleaning there is)."""
    return store.clean(text)


def shown(event: dict, folder: Path) -> str | None:
    """After a label is marked through the door, the line the person is shown under the turn, as
    the harness shows a hook's `systemMessage` to the person and not to the model: where the label
    speaks for the person (its `whose` is theirs or both) or about the two of them (a standing
    line), and for every line left at the door. Text a session read can steer it to mark such a
    label, and it crosses every cut as standing. A work label of the session's own is not shown.
    The label is shown as its page holds it, by the key the door's answer names; nothing is
    blocked."""
    given = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
    found = re.search(r"\bmarked ([RWN]\d+)\b", json.dumps(event.get("tool_response"), ensure_ascii=False))
    if found is None:
        return None
    key = found.group(1)
    sentence = store.plain(given.get("sentence") if isinstance(given.get("sentence"), str) else "")
    target = store.ours() if given.get("home") == "ours" else folder
    label = next((each for each in store.labels(target) if each["id"] == key and each["text"] == sentence), None)
    if label is None:  # not in the page as it now stands: what was sent, as the server would have written it
        whose = given.get("whose") if given.get("whose") in ("his", "both") else "session"
        label = {"kind": store.KINDS[key[0]], "whose": whose, "text": sentence}
    text = unmarked(label["text"])
    text = text if len(text) <= SHOWN else text[:SHOWN].rstrip() + " […]"
    if label["kind"] == "next":
        return f"Crossings · left at the door: {text}"
    if label["kind"] == "relation" or label["whose"] in ("his", "both"):
        return f"Crossings · marked {key} ({unmarked(label['whose'])}): {text}"
    return None


# A summary is carried from cut to cut and retold each time. Where most of a long one now repeats
# the one before, the person is told once, under the turn, that a new session would lose nothing,
# where the last stretch is marked. The two figures may be set for a home in a plain file each, of
# one line: its characters (RETELLING_LENGTH) and its percent (RETELLING_SHARE).
LONG = 20000  # characters of a summary, at least
MOSTLY = 60  # percent of it, at least, repeating the summary of the cut before
RETELLING_LENGTH, RETELLING_SHARE = "retelling-length", "retelling-share"


def limits(folder: Path) -> tuple[int, int]:
    """The two figures for this home: each from its plain file where that holds a whole number of
    nought or more (the share may end in %), else the named constant."""
    found = []
    for name, given in ((RETELLING_LENGTH, LONG), (RETELLING_SHARE, MOSTLY)):
        try:
            text = store.within(folder, name).read_text(encoding="utf-8").strip().rstrip("%").strip()
        except (OSError, UnicodeDecodeError):
            text = ""
        found.append(int(text) if text.isdigit() and text.isascii() else given)
    return found[0], found[1]


def earlier(folder: Path, session_id: str, ordinal: int, key: bytes | None) -> set[bytes] | None:
    """The digests of the summary of the same session's cut before this one, as its sidecar keeps
    them, where they were made with this home's key; else nothing, and nothing is compared."""
    before = _sidecar(folder, session_id, ordinal - 1) if ordinal > 1 else None
    if not before or key is None or before.get("runs_of") != record.keyed(key):
        return None
    return count.unpacked(before.get("summary_runs"))


def _sidecar(folder: Path, session_id: str, ordinal: int) -> dict | None:
    """A cut's sidecar as it was written, or nothing where there is none or it is not one."""
    try:
        found = record.read(folder, session_id, ordinal)
    except (OSError, ValueError):
        return None
    return found if isinstance(found, dict) else None


def retold() -> str:
    """The line the person is shown where most of a long summary retells the one before (see
    `retelling`), with the number of the cut."""
    return (
        "Crossings · this session has been cut {} times and most of its summary now retells the one before; a new "
        "session would start from the store alone, and the last stretch is marked, so nothing would be lost by it."
    )


def retelling(counted: dict, folder: Path, session_id: str, key: bytes | None) -> str | None:
    """Keep beside the cut's count what the line for the person rests on, and give the line where it
    is due: the summary is at least as long as the home's length, at least the home's share of it
    repeats the summary of the cut before, a label rests on a message of the stretch since that cut,
    and a line was left at the door since it (a line at the door numbered past the newest there was
    at that cut). Once a cut: a cut counted again is not told again. Nothing of what was said is
    kept for it: the sidecar holds the digests of the summary's runs, a number of labels and a key."""
    stretch = {p["id"] for voice in ("person", "session") for p in counted[voice]["pointers"] if p.get("id")}
    held = store.labels(folder)
    counted["labelled"] = sum(
        1 for label in held if label["kind"] != "next" and any(a.split("+")[0] in stretch for a in label["anchors"])
    )
    counted["door"] = max((int(label["id"][1:]) for label in held if label["kind"] == "next"), default=0)
    counted["runs_of"] = record.keyed(key) if key else None
    now = _sidecar(folder, session_id, counted["cut"])
    counted["told"] = bool(now and now.get("told"))
    before = _sidecar(folder, session_id, counted["cut"] - 1) if counted["cut"] > 1 else None
    long, mostly = limits(folder)
    chars, retold_chars = counted["summary_chars"], counted.get("retold")
    left = bool(before) and isinstance(before.get("door"), int) and counted["door"] > before["door"]
    if (
        counted["told"]
        or retold_chars is None
        or chars < long
        or 100 * retold_chars < mostly * chars
        or not counted["labelled"]
        or not left
    ):
        return None
    counted["told"] = True
    return retold().format(counted["cut"])


def handing(event: dict, folder: Path, path: Path) -> None:
    """Before a call of the door's `mark`, hand the server the model the session runs now, by the
    call's digest (see layer.hand): the server is told neither. Not for a subagent's call, whose
    model a hook is not told: that call is not layered."""
    tool = str(event.get("tool_name") or "")
    given = event.get("tool_input")
    if not tool.endswith("__mark") or event.get("agent_id") or not isinstance(given, dict):
        return
    model = layer.current(folder, named(event, path))
    if model:
        layer.hand(folder, "mark", given, model)


attended = record.attended  # whether a person sits in the session: the rule is record's, for the door too


def project(event: dict) -> Path:
    """The project's root. A hook is told the directory the shell stands in, and a `cd` in a shell
    call moves that; the root the harness exports does not move."""
    root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(root) if root and Path(root).is_dir() else Path(event.get("cwd") or ".")


def run(event: dict) -> str | None:
    name = event.get("hook_event_name")
    path = Path(event.get("transcript_path") or "")
    cwd = project(event)
    session_id = event.get("session_id") or path.stem
    if name == "SessionStart":
        mark(session_id, True)
    elif name == "SessionEnd":
        mark(session_id, False)
    folder = store.kept(cwd)
    # never switched on here, or switched off: the session is marked, and nothing else is done
    if folder is None or not store.active(folder):
        return None
    record.sound(folder)  # a link anywhere in the home: nothing is read or written, and the log says so
    if name == "PostCompact" and event.get("agent_id"):  # a subagent's own cut is not the session's: nothing is written
        return None
    person = attended()
    if not person and path.is_file():  # what it holds is known by its ids, and never archived
        store.unattended(path, folder)
    if name == "SessionEnd":
        if path.exists() and person:  # the whole transcript, as a safety net for anything a marker stepped over
            keep(path, cwd, wait=os.environ.get("CROSSING_WAIT") == "1", whole=True)
        return None
    if name == "PreToolUse":
        # Wired to the door's own tools alone. The door's server is not told which session is
        # calling, so what was just said is put into the archive here, a moment before it answers.
        if person and path.is_file() and store.archive(path, folder):
            store.refresh(folder)
        if person:
            handing(event, folder, path)
        return None
    if name == "PostToolUse":  # wired to the door's mark and leave alone
        signed(event, folder, path)
        line = shown(event, folder)  # for the person, under the turn; the model is not handed it
        return json.dumps({"systemMessage": line}, ensure_ascii=False) if line else None
    if name == "PostModelSwitch":
        # The model changed inside the session: kept as the one there now, and the one that arrives
        # is told, as context with this hook's answer, where another model was holding the session.
        if person and path.is_file() and store.archive(path, folder):
            store.refresh(folder)
        told = arriving(folder, named(event, path), event.get("to_model"), event.get("agent_id"))
        if told:
            return json.dumps({"hookSpecificOutput": {"hookEventName": "PostModelSwitch", "additionalContext": told}})
        return None
    if name == "PostCompact":
        # Nothing said while the switch was off is counted either: the spans are read first, and a
        # record of them that cannot be read stops the count here, with a line in the log.
        summary = event.get("compact_summary") or ""
        key = record.runs_key(folder) if len(transcript.norm(summary)) >= count.RUN else None
        counted = count.count(
            path,
            summary,
            pending=True,
            spans=off.spans(folder)[0],
            key=key,
            earlier=lambda ordinal: earlier(folder, session_id, ordinal, key),
            untold=store.lost(folder),
            unsaid=frozenset(off.unsaid(folder)),
        )
        counted["trigger"] = counted["trigger"] or event.get("trigger")
        line = retelling(counted, folder, session_id, key)
        record.write(counted, folder, session_id, path)  # counts, pointers and digests, and no text of either voice
        if person:
            keep(path, cwd, wait=True)
        # For the person, under the turn; the session is not handed it.
        return json.dumps({"systemMessage": line}, ensure_ascii=False) if line else None
    if name == "SessionStart":
        notes = []
        if event.get("source") == "compact" and person and not event.get("agent_id"):  # for a session a person sits in
            # The harness asks for this note before it hands over the summary (PostCompact), so
            # the note is about this cut by its ordinal and never about an earlier record.
            ordinal, _, _ = transcript.locate(path)
            notes.append(waking(record.read(folder, session_id, ordinal) or count.count(path, pending=True)))
        told = welcomed(folder, str(event.get("session_id") or ""), event.get("agent_id"))
        notes += [told] if told else []
        # Which model the session starts with; a resume on another model than the one that spoke last is told so.
        told = arriving(folder, named(event, path), event.get("model"), event.get("agent_id"))
        notes += [told] if told else []
        # A session that comes back, where another has been working here since it last spoke.
        if event.get("source") == "resume" and person and not event.get("agent_id"):
            if path.is_file() and store.archive(path, folder):  # up to this moment, so its own newest is known
                store.refresh(folder)
            if store.moved_on(folder, named(event, path), path):
                notes.append(moved_on())
        aside = passing(cwd, folder) if person and not event.get("agent_id") else None
        out = {"systemMessage": aside} if aside else {}
        if notes:
            out["hookSpecificOutput"] = {"hookEventName": "SessionStart", "additionalContext": "\n\n".join(notes)}
        return json.dumps(out, ensure_ascii=False) if out else None
    return None


def passing(cwd: Path, folder: Path) -> str | None:
    """What the person is shown under the turn, once, as a session starts: see `passed_over`."""
    said = store.passed_note(cwd, folder, "hook")
    return f"Crossings · {said}" if said else None


def carried(event: dict) -> str | None:
    """The frame, as context for a session starting again after a cut, or started new.

    The harness wraps what a SessionStart hook adds as a reminder of its own: the model reads it
    with its next request, at a cut the person chose and at one that came by itself alike, and
    nothing is drawn or filed as a message. Before this the frame went into the cut's answer
    as a message at every automatic cut, and the harness cuts by itself while the person is away.

    The hook is not told what set the cut off, so the plain files of the project's home
    decide alone: `beside` in `mode` and `note` in `carry`, where Crossing is on. The hooks
    module then adds nothing of its own.

    A session started new gets the frame by the same files, in words true for it, where a person
    sits in it and the store holds a label to carry. A resumed or forked session holds its own
    context, and a cleared one is left as it is.
    """
    source = event.get("source")
    if event.get("hook_event_name") != "SessionStart" or source not in ("compact", "startup") or event.get("agent_id"):
        return None
    new = source == "startup"
    if not attended():  # a session no person sits in is given no frame, after a cut or at its start
        return None
    folder = store.kept(project(event))
    if (
        folder is None
        or not store.active(folder)
        or store.word(folder, "mode") != "beside"
        or store.word(folder, "carry") != "note"
    ):
        return None
    record.sound(folder)
    path = Path(event.get("transcript_path") or "")
    if path.is_file():
        store.archive(path, folder)  # up to the cut, so the frame is made from all that was said
    store.refresh(folder)  # added to, or made whole where a page or a label changed by any other way
    # The model the session runs now, as the harness says it as the session starts, or as its hooks
    # were told it before: the frame is then that model's (see frame.compose). Not known, it is as it was.
    model = layer.named(event.get("model")) or layer.current(folder, named(event, path))
    text = frame.compose(folder, min(frame.size_of(folder), frame.MOST), new=new, model=model)
    if not text:  # a new session, and nothing in the store to carry to it
        return None
    labels = len(re.findall(r"^- [RW]\d+ \(", text, flags=re.M))
    trace = store.within(folder, "last-carry.json")
    try:
        trace.write_text(
            json.dumps(
                {
                    "at": "a new session" if new else "the cut",
                    "by": "the hook, as context",
                    "labels": labels,
                    "chars": len(text),
                }
            ),
            encoding="utf-8",
        )
    except OSError:
        pass  # the trace is a convenience
    counted = f"{labels} label{'' if labels == 1 else 's'}, {len(text)} characters; the rest is behind the door"
    crossed = "a frame was laid out for this new session" if new else "a frame crossed with this cut"
    return json.dumps(
        {
            "systemMessage": f"crossing · {crossed}: " + counted,
            "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text},
        }
    )


def keep(path: Path, cwd: Path, wait: bool, whole: bool = False) -> subprocess.Popen | None:
    """Bring the archive and the store up to date from this transcript, and renew the second
    copy where the home names a folder for one; nothing at all where Crossing is not on. A
    session that is ending is not held up: there the work goes on in a process of its own,
    which is given back so that whoever must be sure of its end can wait for it. That process
    is the door's `build`, which reads the transcript whole; `whole` asks the same here."""
    folder = store.kept(cwd)
    if folder is None or not store.active(folder):
        return None
    record.sound(folder)
    if not wait:  # the door takes a transcript by its path from the plugin's own hooks alone (see door.personal)
        return subprocess.Popen(
            [sys.executable, "-I", str(DOOR), "build", "--cwd", str(cwd), "--transcript", str(path), "--by-hook"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
            env={**os.environ, "CLAUDE_PLUGIN_ROOT": str(record.ROOT)},
        )
    store.archive(path, folder, whole=whole)
    store.refresh(folder)
    dest = second.destination(folder)
    if dest is not None:
        top = record.located(cwd)[1]
        if record.lies_in(dest, top):  # a copy's folder inside the project would put the words in it
            record.log(f"refused: the home's copy file names a place inside the project: {dest}")
        else:
            try:
                second.make(folder, dest, second.named(top), top)
            except second.Failed as err:  # a line in the log, and no command: the Keychain's holds the passphrase
                record.log(f"not copied: {err}")
    return None


data = record.data  # the plugin's own data folder, for its logs


def note(event: dict, **more) -> None:
    """One line a hook call, when CROSSING_DEBUG is not "0": which hook, when, and how large the
    transcript was at that moment and when it last changed, as the file system says. Sizes and
    names only, never text. The transcript itself is not opened: a log read at every call of
    every hook would cost more than all the rest."""
    if os.environ.get("CROSSING_DEBUG") == "0" or not isinstance(event, dict):
        return
    given = event.get("transcript_path")
    try:
        seen = os.stat(given if isinstance(given, str) and given else "")
        size, changed = seen.st_size, round(seen.st_mtime, 3)
    except (OSError, ValueError):  # no transcript yet, or a path that is none
        size = changed = None
    record.logged(
        data() / "calls.log",
        json.dumps(
            {
                "at": round(time.time(), 3),
                "event": event.get("hook_event_name"),
                "source": event.get("source"),
                "trigger": event.get("trigger"),
                "summary_chars": len(event.get("compact_summary") or ""),
                # what the harness itself says about the cache when a session resumes or forks
                **{
                    k: event[k]
                    for k in (
                        "context_tokens",
                        "prompt_cache_likely_expired",
                        "estimated_cache_write_usd",
                        "seconds_since_last_response",
                    )
                    if k in event
                },
                "transcript_bytes": size,
                "transcript_changed": changed,
                **more,
            }
        )
        + "\n",
    )


def main() -> int:
    record.private()  # every folder and file a hook makes is its owner's alone
    try:
        event = json.load(sys.stdin)
        # `frame`: the hook that carries, wired to cuts and new sessions
        asked = sys.argv[1] if len(sys.argv) > 1 else ""
        note(event, phase="start", asked=asked)
        out = carried(event) if asked == "frame" else run(event)
        note(event, phase="end", asked=asked, answered=bool(out))
        if out:
            print(out)
    except record.Linked as err:  # a link in the home: nothing was read or written through it
        record.refused(err)
    except Exception:  # never break a session over a count
        try:
            record.logged(data() / "errors.log", traceback.format_exc() + "\n")
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
