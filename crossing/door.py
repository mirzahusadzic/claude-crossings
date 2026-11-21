#!/usr/bin/env python3
"""The door to the store.

  door.py look
  door.py labels [id ...] [--kind relation|work|next|refused] [--day YYYY-MM-DD]
  door.py find <words> [--voice their|session] [--limit N]     word*  "a phrase"
  door.py thread <id> [--around N | --role pair:me|pair:them]
                                           with a role, a pair in place of the messages around: the session's turn
                                           (pair:me) or the person's (pair:them), with the other's next turn in
                                           answer, the one the message heads or the one it answers; too long to
                                           show whole, a page of it that starts at the message named
  door.py mark --kind relation|work|next|refused|silenced --whose their|session|both --anchors id,id <sentence>
                                           an id is a message's, or a label's key: the label then stands over that one,
                                           or, for a refusal, judges that one again, and for a silencing puts it to rest
  door.py frame [--size N]                 with --session or --transcript, a cut's frame for that session; where
                                           the line at the door or a standing line sets the session's turns
                                           beside the person's sentences, a sentence after the frame says what
                                           they take, at a terminal, for the door's server and with --trade
  door.py status
  door.py build
  door.py strike <id | label | session:id> [--why text]
  door.py copy
  door.py layer <model-key>                sign every label and every message of the session's that has
                                           no model as made with that one; one that has a model is left
  door.py home                             the folder of the project's home, where it has one
  door.py switch on|off|toggle|adopt       the person's switch for the project; adopt takes a home that
                                           holds what this computer has no record of switching on
  door.py words | page                     for the hooks module: the home's words for the cut, and its
                                           hand-over page; they read and write nothing
  door.py trace <json>                     for the hooks module: the trace of what a cut did
  door.py welcome <session id>             for the person's command, after it turns the switch: switched
                                           off, the note that tells the session so; switched on, the note
                                           that it is on again and the welcome, each where it is due

Every verb takes --cwd DIR (the project; default: here) and --home here|ours. The home on this
computer (ours) is offered only to a project where Crossings is switched on and on; from any
other, every verb says what it says of a project never switched on. With --transcript PATH the
archive is first brought up to date from that transcript: handed by its path, it is the
person's own act, and taken whole. With --session ID it is too, where a person sits in the
session (see record.attended): that is how the hooks module asks; the id is looked for as it is,
never as a pattern. The hooks' own build adds --by-hook, and then what a session no person sat
in held is passed over in a transcript named by its path as well.

`switch`, `strike`, `layer` and `copy`, `trace` and `welcome`, which write the home's kept files
for the hooks module, and --transcript, --session and --model on any verb, are the person's: they
run where the door stands at a real terminal, or where the plugin's own hooks or module call it
(--by-hook, --by-module, with the plugin's folder in CLAUDE_PLUGIN_ROOT), and --model also for the
door's server in its own process; anywhere else they say in one sentence that this is the
person's to run (see `personal`). `frame` and `page` carry nothing where no person sits in the
session (record.attended) and the door stands at no terminal. `words` and `page` read and write
nothing, and `build` writes the index alone, which is made from the plain files. With --touch a
thread, with a role or without, or a mark is noted in the home's plain log of what was pulled. With
--bare no answer names a file or a folder: that is how the door's server asks, so that nothing a
session reads points a hand at the file system. Nothing comes back without its place: an id, a
voice, a time, and the labels that rest there. No model is called.

A project's home is its own `crossings/` folder, or, where it has none, a folder outside it
that `switch on` makes. Either is believed only once the person has switched Crossings on in
that project, which `switch on` keeps in a record of the person's own, outside every project.
Until then Crossings was never switched on there: every other verb says so in a sentence, with
exit status 1, and makes nothing. A home that is there already and holds any file but a
`.gitignore`, which this record has no line for, is not switched on by `switch on`: it says what
is there, and `switch adopt` takes it. Switching on and adopting make the index anew from the
plain files, whatever database the folder held. A setting (CROSSING_HOME, CROSSING_HOMES, CROSSING_OURS,
CROSSING_SWITCHED) that names a place inside the project is not followed: every verb says so
in a sentence, with exit status 1. `switch on` and `status` narrow a home that is readable by
other accounts to its owner alone. `switch` is the person's, from their terminal or through their command, and
`strike`, `layer` and `copy` from their terminal; `home` prints the folder of a home that is believed, and
nothing otherwise; the door's server offers none of these. Switched off, a home is
still read, and nothing is added to it (`layer` signs nothing, and says so); and nothing said
until it is switched on again is ever kept, by any verb, from any transcript (see crossing/off.py).
No file of a home is read or written through a link:
where one is, the door says so in a sentence, with exit status 1, and writes nothing; and so for an id that
cannot name a file (record.ident). `status` and `look` from the person's terminal or for the plugin's own
hooks and module, not --bare, also say which kept messages look like they hold a key (store.flagged), and
`status` that the second copy's passphrase is taken from the environment where it is, and once that an older
second copy is no longer renewed; from anywhere else they answer as the door's server does, as --bare. A
strike's answer names the labels that rest on what it struck, and ends with what no strike can
reach; a strike that struck nothing says why in one sentence, with exit status 1.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import frame, layer, record, sample, second, store  # noqa: E402

VOICE = {store.HIS: "the person", store.OWN: "the session", store.PASTED: "pasted by the person"}
SHORT = 240  # characters of a label's sentence in a list; by its id it is given whole
# What `find` closes with where it shows a message in part.
EXCERPTS = (
    "These are excerpts where … stands; the record holds each message whole, and thread <id> gives it whole and in "
    "its place."
)
ASKING = ("look", "labels", "status")  # the verbs that call a refusal standing or silenced, for the model that asks
# How the person's switch stands, as their command says it; and what every other verb says of
# a project that has no home, where nothing is kept and nothing is made by looking.
SWITCHED = {
    "on": "Crossings is on for this project.",
    "again": "Crossings is on again for this project: what is said from now on is kept, and nothing said while "
    "it was off was kept.",
    "off": "Crossings is off for this project: no cut is counted, noted or answered, and nothing said from now "
    "until it is switched on again will be kept.",
    "never": "Crossings was never switched on for this project.",
    "joined": "Crossings is on for this folder: it shares the home of the folder above it, and what is said here "
    "is kept there from now on.",
    "alone": "This folder is its home's own, so there is no home above it to share: nothing was changed.",
    "occupied": "This folder's own home already holds files this computer has no record of switching on, so "
    "nothing was changed.",
    "restored": "Crossings is on again for this project. Its record of when Crossings was off had been taken "
    "away, cut short or damaged, so everything said before this moment that was not kept already is kept "
    "off the record; what is said from now on is kept.",
}
# Said where a folder lies below the folder of a home that is believed, and the person has not answered for
# it (see store.waiting): to the person at the switch and at their own door, and to a session's shell or the
# server without naming the folder.
BELOW = (
    "This folder lies below {}, whose home Crossings keeps, and nothing of that home is kept or read from here "
    "until you answer once for this folder: /crossings join shares it, /crossings here gives this folder a home of "
    "its own."
)
BELOW_BARE = (
    "This folder lies below the folder of another home, and the person has not shared it from here, so nothing "
    "is kept or read."
)
UNKEPT = (
    "The record of when Crossings was off could not be written in this project's home ({}), so the switch may "
    "not stand as asked: status says how it stands."
)
UNBUILT = (
    "The home was held by another act for five seconds, so the index was not made again this time; "
    "the plain files are as they were, and the next read or build makes it."
)
NOT_ON = "Crossings is not switched on for this project."
LINKED = "A file of this project's home is a link, so nothing was written."
UNNAMED = "An id given here cannot name a file (letters, digits, - and _ alone), so nothing was written."
# Said by the person's own status and look, never by the door's server: the session is not told.
FLAGGED = (
    "A kept message looks like it holds a key or a password ({0}), and door.py strike {0} removes it from the store."
)
COPY_KEY = (
    "The second copy's passphrase is taken from the environment (CROSSING_COPY_KEY), where every program the "
    "session starts can read it."
)
ASTRAY = "The setting {} names a place inside this project, so it was not followed."
RELATIVE = "The setting {} names no absolute path, so it was not followed."
# What a verb or an option that is the person's alone answers where the door stands at no terminal
# and was not called by the plugin's own hooks or module (see `personal`).
PERSONS = (
    "This is the person's to run, from their own terminal or with the plugin's command (/crossings), so "
    "nothing was done."
)
LOST = (
    "The record of when Crossings was off in this project is missing, shorter than it was, or holds a line that "
    "cannot be read as a span, so nothing more is archived here until the person switches Crossings on again."
)
SHELLED = "{} marked from a shell, not through the door, and shown to no one as marked: {}."
IGNORE_SAID = (
    "This project's home lies inside a repository, and its ignore file there does not leave out said/, "
    "where the words are kept: they could be committed with the work."
)
INSIDE = "This home's copy file names a place inside the project, so no second copy was made."
LINKED_HOME = (
    "This project's crossings folder is a link to {}, so Crossings was not switched on: a home is a folder of its own."
)
# What `frame` and `page` answer where no person sits in the session (see record.attended), and the
# door stands at no terminal: what crosses a cut is for a session a person sits in alone.
UNSEATED = "The frame and the hand-over are for sessions a person sits in, and this one is not, so nothing was carried."
# Said by the person's own status alone, each once.
DAMAGED = "A file of this home holds a line that cannot be read as text, and it is passed over wherever it is read: {}."
ARRIVED = "came into this home's pages without a mark through the door, and"
SIGNS_CAME = "came into this home without a signing through the door, and"
COLLIDED = "Two messages of this home share the id {0}: thread {0} names both, and a strike takes one by its whole id."
# The verbs that are the person's alone, or the hooks module's: those that write a kept file of the home.
PERSONAL = ("switch", "strike", "layer", "copy", "trace", "welcome")
# The roles `thread` is asked with to show a pair (see store.tied), named from the side of the session, which calls:
# me, the session; them, the person. Each by the voice whose turn heads the pair.
ROLES = {"pair:me": store.OWN, "pair:them": store.HIS}
UNROLED = "thread takes one of two roles: pair:me or pair:them."
# A role as it was spelled before, still taken, and meaning the same: an answer names it as ROLES does.
SPELLED = {"pair:him": "pair:them"}


def role_of(asked: object) -> str | None:
    """The role `thread` is asked with, as ROLES names it, in either spelling it is taken in; or None, for a word that
    is no role."""
    if not isinstance(asked, str):
        return None
    named = SPELLED.get(asked, asked)
    return named if named in ROLES else None


def strayed(name: str) -> str:
    """The sentence for a setting that was not followed (see record.astray)."""
    return (ASTRAY if os.path.isabs(os.environ.get(name) or "") else RELATIVE).format(name)


def personal(args: argparse.Namespace) -> bool:
    """Whether the door may do what is the person's alone: it stands at a real terminal (see
    record.terminal), or the plugin's own hooks or module called it, as their flag says together
    with the plugin's folder in CLAUDE_PLUGIN_ROOT (see record.from_plugin). Neither is a wall
    against a session with a shell: the hooks module also refuses a shell command that calls the
    door so (hooks/crossings.ts), and the wall is the person's own approval of commands."""
    return record.terminal() or ((args.by_hook or args.by_module) and record.from_plugin())


many = record.many  # a count with its noun: 1 label, 2 labels


def joined(items: list[str], last: str = " and ") -> str:
    """Items in a row: `a, b and c`, or with another word before the last."""
    return ", ".join(items[:-1]) + last + items[-1] if len(items) > 1 else "".join(items)


def unclaimed(held: dict) -> str:
    """What `switch on` says of a home that holds what this computer has no record of switching
    on (see store.unclaimed), in place of switching it on: its messages and labels, and what else
    is there."""
    more = (
        (["an index"] if held["index"] else [])
        + (["a hand-over page"] if held["page"] else [])
        + (
            [f"the setting file{'s' if len(held['settings']) > 1 else ''} {joined(held['settings'])}"]
            if held["settings"]
            else []
        )
        + (["models.txt"] if held["models"] else [])
        + ([many(held["others"], "other file")] if held["others"] else [])
    )
    beside = joined(more, ", and " if len(more) > 2 else " and ")
    return (
        f"This project's home already holds {many(held['messages'], 'message')} and "
        f"{many(held['labels'], 'label')}" + (f", and {beside}," if beside else "") + " that this computer has no "
        f"record of switching on, in {held['folder']}. "
        "Run the same command again with the word adopt (/crossings adopt, or door.py switch adopt from a shell) "
        "to take them as your own, or remove that folder first to start clean. Crossings was not switched on."
    )


def when(at: str) -> str:
    """A message's time as the door shows it, to the minute; cleaned (store.clean), since a home
    an older make wrote may hold a time a transcript gave that is no time."""
    return store.clean(at[:16]).replace("T", " ") + " UTC" if at else "no time"


def transcript_of(session: str) -> Path | None:
    """The transcript of a session, by its id, among the harness's projects in the person's own
    folder: the id must be one (record.ident), and is looked for as it is, never as a pattern."""
    record.ident(session)
    try:
        folders = sorted((record.own() / ".claude" / "projects").iterdir())
    except OSError:
        return None
    return next((each / f"{session}.jsonl" for each in folders if (each / f"{session}.jsonl").is_file()), None)


def by(label: dict, named: bool) -> str:
    """Which model made a label, in a home where more than one is known (`named`): for a label that
    is not the person's alone, and only where it is known."""
    return (
        f", written by {store.clean(label['model'])}"
        if named and label.get("model") and not store.persons(label)
        else ""
    )


def voiced(said: dict, named: bool) -> str:
    """Whose voice a message is in, with the model that made it where the session's voice is in
    more than one model's hand in this home."""
    return VOICE[said["voice"]] + (f" ({store.clean(said['model'])})" if named and said.get("model") else "")


def show_find(out: dict, named: bool = False) -> str:
    lines = [
        f'find "{store.clean(out["asked"])}"'
        + ("" if out["all_words"] else " (no message holds all of these words; any of them)")
    ]
    if not (out["labels"] or out["said"]):
        near = ", ".join(f"{store.clean(word)} ({n})" for word, n in out["nearest"])
        return (
            lines[0]
            + "\nNothing in the store holds these words. That is a miss, not a no: try other words."
            + (f"\nNearest words that are there: {near}." if near else "")
        )
    if out["labels"]:
        # Labels that hold every word are given whole. Those that merely share one word are few
        # and short, and a standing line among them is named, not recited.
        every = out["labels_all"]
        shown = out["labels"] if every else out["labels"][:3]
        lines += ["", "Labels:" if every else "Labels (holding any of these words):"] + [
            f"- {label['id']} ({label['kind']}, {store.owner(label['whose'])}{by(label, named)}): "
            f"a standing line about the two of you, not recited here; `labels {label['id']}` gives it."
            if label["kind"] == "relation" and not every
            else f"- {label['id']} ({label['kind']}, {store.owner(label['whose'])}{by(label, named)}): "
            + (
                store.clean(label["text"])
                if every or len(label["text"]) <= SHORT
                else store.clean(label["text"][:SHORT]).rstrip() + " […]"
            )
            + f" [{store.rests(label)}]"
            for label in shown
        ]
        if len(shown) < len(out["labels"]):
            more = len(out["labels"]) - len(shown)
            lines.append(f"{many(more, 'more label')} hold{'s' if more == 1 else ''} one of these words.")
    if out["said"]:
        lines += ["", "Said:"] + [
            f"- `{s['name']}` {voiced(s, named)}, {when(s['at'])}: {' '.join(store.clean(s['part']).split())}"
            + (f" (labels: {', '.join(s['labels'])})" if s["labels"] else "")
            for s in out["said"]
        ]
        # A message shown in part is an excerpt, and the record holds it whole: said so, so that a cut excerpt is
        # never taken for a message the record holds cut.
        whole = all(s["whole"] for s in out["said"])
        lines += ["", "For any of these in its place: thread <id>." if whole else EXCERPTS]
    return "\n".join(lines)


def row_of(label: dict, whole: bool = True, named: bool = False) -> str:
    """One label as a line: its kind where it is a silencing or one of a refusal's run (`run`),
    whose it is, its day, its state where that is not simply carried, the model that wrote it
    where that is known (given whole; or, in a home where more than one model is known, wherever
    the label is not the person's), its sentence, and in brackets what it rests on, the lines
    stacked beneath it first."""
    text = store.clean(
        label["text"] if whole or len(label["text"]) <= SHORT else label["text"][:SHORT].rstrip() + " […]"
    )
    day = f", {store.clean(label['day'])}" if label.get("day") else ""
    state = label.get("state", "carried")
    state = "" if state == "carried" else f", cooled beneath {label['parent']}" if state == "cooled" else f", {state}"
    if label.get("elsewhere"):  # the family stands otherwise for another model than for the one that asks
        state = (
            f", standing here: {label['elsewhere']} puts it to rest for another model alone"
            if label["kind"] == "refused"
            else f", at rest here: {label['elsewhere']} stands for another model alone"
        )
    elif label.get("alone"):  # the family is another model's alone, and this label stands in it for that model
        state = f", another model's alone, {'standing' if label['kind'] == 'refused' else 'at rest'} there"
    written = f", written by {store.clean(label['model'])}" if whole and label.get("model") else by(label, named)
    kind = f"{label['kind']}, " if label.get("run") or label.get("kind") == "silenced" else ""
    return (
        f"{'  ' * label.get('depth', 0)}- {label['id']} "
        f"({kind}{store.owner(label['whose'])}{day}{state}{written}): {text} "
        f"[{store.rests(label)}]"
    )


def standing_apart(refusals: dict) -> str:
    """The families of refusals as `look` counts them: those that stand, by the key that stands in each, and apart
    from them those that are silenced, for the model that asks (see store.refusals), and the clause that names those
    that stand otherwise for another model alone (see `elsewhere`)."""
    standing, silenced = refusals["standing"], refusals["silenced"]
    said = f"{many(len(standing), 'refusal')} standing" + (f" ({store.some(standing)})" if standing else "")
    said += f", {len(silenced)} silenced ({store.some(silenced)})" if silenced else ""
    return said + (f"; {elsewhere(refusals)}" if elsewhere(refusals) else "")


def elsewhere(refusals: dict) -> str:
    """The families of refusals that stand otherwise for another model alone than for the one that asks, by the key
    that stands in each here, or for that model: those at rest there alone, and those standing there alone (see
    store.refusals); and those that are another model's alone and at rest there, by the key that stands in each for
    that model; nothing where there are none."""
    rest, stand, away = refusals.get("rest", []), refusals.get("stand", []), refusals.get("away", [])
    return "; ".join(
        [f"{store.some(rest)} {'is' if len(rest) == 1 else 'are'} at rest for another model alone, not for this one"]
        * bool(rest)
        + [f"{store.some(stand)} stand{'s' if len(stand) == 1 else ''} for another model alone, not for this one"]
        * bool(stand)
        + [f"{store.some(away)} {'is' if len(away) == 1 else 'are'} another model's alone, at rest there"] * bool(away)
    )


def show_look(out: dict, bare: bool = False, named: bool = False) -> str:
    """The room. The standing lines are named by id and number only, and so is a stack over
    them; see store.look."""
    said = sum(d["his"] + d["session"] for d in out["days"])
    lines = [
        f"The store in outline: {many(len(out['days']), 'day')}, {many(said, 'message')}, "
        f"{many(out['labels'], 'label')}, {out['struck']} struck"
        + (f"; kept up to {when(out['last'])}." if out["last"] else "."),
        "",
        "Days:",
    ]
    days = [
        (
            (d["day"], 0, ""),
            f"- {store.clean(d['day']) or 'no date'}: {d['his']} of the person's, "
            f"{d['session']} of the session's" + (f", {d['pasted']} pasted" if d["pasted"] else ""),
        )
        for d in out["days"]
    ]
    days += [
        (
            (g["day"], 1, g["off"]),
            f"- off the record from {g['off']} "
            + (f"to {g['on']}" if g["on"] else "on, still off")
            + ": nothing said then was kept",
        )
        for g in out.get("off", [])
    ]
    lines += [line for _, line in sorted(days)]

    def span(ids: list[str]) -> str:
        return f"{len(ids)} ({ids[0]} to {ids[-1]})" if ids else "none"

    cooled, stacks = out["stacks"]["lines"], out["stacks"]["stacks"]
    lines += [
        "",
        f"Labels: {span(out['standing'])} standing, about the two of you; {span(out['work'])} about the work"
        + (f"; {standing_apart(out['refusals'])}" if any(out.get("refusals", {}).values()) else "")
        + (
            f"; {cooled} of the standing lines stand{'s' if cooled == 1 else ''} beneath {stacks} "
            f"stack{'s' if stacks != 1 else ''}."
            if stacks
            else "."
        ),
    ]
    if out["misaligned"]:
        lines.append(f"Misaligned stacks, to be written again: {store.some(out['misaligned'])}.")
    if out["unresolved"]:
        lines.append(f"Resting on what the archive no longer holds: {store.some(out['unresolved'])}.")
    if out["left"]:
        lines += ["", "Left at the door:", row_of({**out["left"], "whose": "the session's"}, named=named)]
        if out["left"].get("since"):
            lines.append(f"Marked after this line: {store.some(out['left']['since'])}.")  # as the frame says it
    if out["newest"]:
        lines += ["", "The newest about the work:"] + [
            row_of(label, whole=False, named=named) for label in out["newest"]
        ]
    lines += [
        "",
        "From here: labels (by kind, by day or by id), find, thread."
        if bare
        else "From here: labels [id ...] [--kind relation|work] [--day YYYY-MM-DD], find <words>, thread <id>.",
    ]
    if not bare and out.get("flagged"):  # the person's own look alone
        lines += [""] + [FLAGGED.format(each) for each in out["flagged"]]
    if out.get("lost"):
        lines += ["", LOST]
    return "\n".join(lines)


def show_labels(out: dict, whole: bool, bare: bool = False, named: bool = False) -> str:
    lines = [row_of(label, whole, named) for label in out["labels"]] or ["No label of that kind or day."]
    if out["missing"]:
        lines.append("No such label: " + ", ".join(out["missing"]) + ".")
    if out["more"]:
        lines.append(f"{out['more']} more, older: name a kind or a day.")
    if out["quiet"]:
        some = len(out["quiet"]) != 1
        lines.append(
            f"{len(out['quiet'])} standing line{'s' if some else ''} about the two of you "
            f"({out['quiet'][0]} to {out['quiet'][-1]}) {'are' if some else 'is'} not listed here: "
            + ("labels of the kind relation." if bare else "labels --kind relation.")
        )
    return "\n".join(lines)


def gap(span: dict) -> str:
    """A span when the switch was off, in the place of what was said then: its two moments, and nothing else."""
    return (
        f"(Crossings was off from {span['off']} "
        + (f"to {span['on']}" if span["on"] else "on, and is still off")
        + ": nothing said then was kept.)\n"
    )


QUOTED = "    > "  # before each line of a message in a thread: no line of the door's own begins so


# Said once a line, as the first work label is marked after the newest line left at the door.
OVERTAKEN = "The line at the door was left before this label: where it no longer holds, a new one can be left."
# Said where a label about the work or the two of you (a stack too) is longer than a list shows of one (SHORT), or a
# line left at the door is longer than TENTH, by the length of its sentence as it is kept (store.plain): the label is
# written all the same, and nothing is cut. Never of a refusal or a silencing: its sentence is the reason, and crosses
# whole.
TENTH = 900  # characters of a line left at the door: a tenth of a frame of the usual size (frame.SIZE)
LONG_LABEL = "This label is {} long: a list shows {} of one, and a frame may have no room for it."
LONG_LINE = (
    "This line is {} long: it takes room from the standing lines, the work and the person's own words. A shorter "
    "one can be left in its place."
)
# Said in their place where the person is shown the label under the turn (see hook.shown), cut at store.SHOWN: from
# there, and past what a list shows too.
LONG_SHOWN = "This label is {} long: the person is shown {} of one."
LONG_SHOWN_LISTED = (
    "This label is {} long: the person is shown {} of one, a list shows {}, and a frame may have no room for it."
)


def long_said(kind: str, said: str, shown: bool = False) -> str:
    """The sentence a mark's answer adds where what it wrote is long (see LONG_LABEL and LONG_LINE), or nothing; for a
    label the person is shown under the turn (`shown`), from store.SHOWN (see LONG_SHOWN)."""
    length = len(store.plain(said))
    counted = many(length, "character", grouped=True)
    if kind in ("work", "relation") and shown and length > store.SHOWN:
        return (
            LONG_SHOWN_LISTED.format(counted, store.SHOWN, SHORT)
            if length > SHORT
            else LONG_SHOWN.format(counted, store.SHOWN)
        )
    if kind in ("work", "relation") and length > SHORT:
        return LONG_LABEL.format(counted, SHORT)
    if kind == "next" and length > TENTH:
        return LONG_LINE.format(counted)
    return ""


def show_thread(out: dict, named: bool = False) -> str:
    asked = store.clean(out["asked"])
    if out.get("twins"):
        twins = [f"`{store.clean(each)}`" for each in out["twins"]]
        return (
            f"thread of `{asked}`: {'two' if len(twins) == 2 else len(twins)} messages are named `{asked}`, "
            f"{', '.join(twins[:-1])} and {twins[-1]}; thread with one of them gives that one."
        )
    if not out["found"]:
        return f"thread of `{asked}`: no such message in the store."
    # Numbered in the order they were said, with the one that was named marked in words: an order
    # left to be inferred from a list gets retold wrongly.
    lines = [f"thread of `{asked}`: {many(len(out['said']), 'message')}, in the order they were said", ""]
    gaps = out.get("gaps", [])
    for number, s in enumerate(out["said"], 1):
        lines += [gap(g) for g in gaps if g["before"] == s["seq"]]
        lines.append(
            f"{number}. `{s['name']}` {voiced(s, named)}, {when(s['at'])}"
            + (", the one you named" if s["is_asked"] else "")
            + (f" (labels: {', '.join(s['labels'])})" if s["labels"] else "")
            + ":"
        )
        # Each of the message's own lines is marked as its own, so that none can be taken for a line of the door's.
        lines += [QUOTED + part for part in store.clean(s["text"], lines=True).splitlines()] + [""]
    shown = {s["seq"] for s in out["said"]}
    lines += [gap(g) for g in gaps if g["before"] not in shown]  # after the newest of them
    if out["labels"]:
        lines += ["Labels resting here:"] + [
            f"- {label['id']} ({label['kind']}, "
            f"{store.owner(label['whose'])}{by(label, named)}): "
            f"{store.clean(label['text'])}"
            for label in out["labels"]
        ]
    return "\n".join(lines).rstrip()


def shortened(text: str, most: int) -> str:
    """A message's text as a list shows it: whole up to `most` characters, else cut there and marked so."""
    return text if len(text) <= most else text[:most].rstrip() + " […]"


def show_pair(out: dict, role: str, named: bool = False) -> str:
    """What `thread` answers asked with a role (see ROLES): the pair that role's voice heads, the message named stands
    in (see store.tied), a turn with the other voice's next turn beneath it in answer, in order. The first line says
    what was asked, the id and the role, whose turn heads the pair and how many messages each side holds; each
    message under its id, voice and time, numbered through the pair and cut as `thread` cuts the message it is asked
    of; after a message of the person's, what was pasted into it by each paste's id and length alone; a span when the
    switch was off in its place, as a thread says it; a sentence where the other voice said nothing after it in that
    session; a closing line with where the pair before this one and the pair after it begin, and the role that gives
    them, the other one, since each is headed by the other voice's turn; the keys of the labels resting on any message
    of the pair, without their sentences, where two or more lines left at the door among them are not listed but
    counted, with the newest by its key; and on a line of its own after it, only where a label rests on a text pasted
    into the pair, each such paste by its id with the keys resting on it, its lines left at the door counted alike
    (see `rested`). A pasted text is no message of the pair, so a label on a paste alone stands on that line alone,
    and one on a message of the pair as well stands on both. Both lines speak of the whole pair, whichever id named it
    and whichever voice heads it, also on a page. An id that names no message, or one two messages share, is answered
    as `thread` answers it; one whose turn opens its session and answers none of the role's voice, in one sentence
    that names the role that gives the pair it heads.

    A pair whose texts, as they are shown, fit within store.PAIRED characters together is shown whole. One that
    does not is a page that starts at the message named (at the one a paste was pasted into, for a paste's id) and
    runs on while the texts fit, stopping at the first that does not: one sentence says how many of the pair stand
    before it and where the pair begins, one how many come after the page, the last of them, and the id and the role,
    the same, that the next page of the same pair starts at. Each message keeps its number in the whole pair, and a
    span is said only before a message the page shows, or after the last of the pair where the page reaches it."""
    if not out["found"]:
        return show_thread(out)  # an id that names nothing, or one two messages share: as a thread says it
    asked = store.clean(out["asked"])
    called = f"thread of `{asked}` with the role `{role}`"
    flipped = next(each for each in ROLES if each != role)  # the role of the pairs before and after this one
    whose = VOICE[out["voice"]]
    other = VOICE[store.OWN if store.theirs(out["voice"]) else store.HIS]
    if not out["paired"]:
        return (
            f"{called}: {other}'s turn it stands in is the first of its session and answers no turn of {whose}'s, so "
            f"there is no such pair; the role `{flipped}` gives the pair it heads."
        )
    said = [*out["head"], *out["answer"]]
    texts = [shortened(s["text"], store.WHOLE) for s in said]
    first, end = 0, len(said)  # the page: from the first it shows to the first after it
    if sum(map(len, texts)) > store.PAIRED:  # too long to show whole: a page from the one named, while they fit
        first = next((at for at, s in enumerate(said) if s["is_asked"] or any(p["is_asked"] for p in s["pastes"])), 0)
        room, end = store.PAIRED - len(texts[first]), first + 1
        while end < len(said) and len(texts[end]) <= room:
            room -= len(texts[end])
            end += 1
    lines = [
        f"{called}: {whose}'s turn, {many(len(out['head']), 'message')}, and {other}'s answer, "
        f"{many(len(out['answer']), 'message')}, in the order they were said",
        "",
    ]
    if first:
        lines += [
            f"{many(first, 'message')} of this pair {'stands' if first == 1 else 'stand'} before the one you named and "
            f"{'is' if first == 1 else 'are'} not shown here; the pair begins at `{store.clean(said[0]['name'])}`.",
            "",
        ]
    gaps = list(out["gaps"])
    for number, (s, text) in enumerate(zip(said, texts), 1):
        # A span off the record stands before the first message said after it began, as in a thread.
        here = [g for g in gaps if g["before"] is not None and g["before"] <= s["seq"]]
        gaps = [g for g in gaps if g["before"] is None or g["before"] > s["seq"]]
        if not first < number <= end:
            continue  # not on this page: neither it nor a span that stands before it is said here
        lines += [gap(g) for g in here]
        lines.append(
            f"{number}. `{s['name']}` {voiced(s, named)}, {when(s['at'])}"
            + (", the one you named" if s["is_asked"] else "")
            + ":"
        )
        # Each of the message's own lines is marked as its own, as in a thread.
        lines += [QUOTED + part for part in store.clean(text, lines=True).splitlines()] + [""]
        if s["pastes"]:
            pastes = [
                f"`{store.clean(each['name'])}` ({each['length']:,} character{'' if each['length'] == 1 else 's'})"
                for each in s["pastes"]
            ]  # by id and length alone, never a word of what was pasted
            lines += [
                f"The person pasted {many(len(pastes), 'text')} into it, not shown here"
                + (", the one you named among them" if any(each["is_asked"] for each in s["pastes"]) else "")
                + f": {joined(pastes)}; thread gives {'it' if len(pastes) == 1 else 'each'} in its place.",
                "",
            ]
    if end == len(said):
        lines += [gap(g) for g in gaps]  # after the last of the pair, where the page reaches it
    else:
        after = len(said) - end
        lines += [
            f"{many(after, 'message')} of this pair {'comes' if after == 1 else 'come'} after this page"
            + (f", the last of them `{store.clean(said[-1]['name'])}`" if after > 1 else "")
            # with the same role, so that the next page is of this same pair
            + f"; thread of `{store.clean(said[end]['name'])}` with the role `{role}` goes on from there.",
            "",
        ]
    if not out["answer"]:
        lines += [f"{other.capitalize()} said nothing after it in that session.", ""]
    # Where the pair before this one and the pair after it begin, each only where there is one: each is headed by the
    # other voice's turn, so the other role gives it.
    before, following = (f"`{store.clean(out[side])}`" if out[side] else "" for side in ("before", "after"))
    if before and following:
        lines += [
            f"The pair before this one begins at {before}, and the pair after it at {following}; thread with the role "
            f"`{flipped}` gives each.",
            "",
        ]
    elif before or following:
        side = "before" if before else "after"
        lines += [
            f"The pair {side} this one begins at {before or following}; thread with the role `{flipped}` gives it.",
            "",
        ]
    # The labels on the pair's own messages; then, apart, those on what was pasted into it, which is no message of the
    # pair: each paste by its id, of the whole pair also on a page.
    pastes = [each for s in said for each in s["pastes"]]
    lines += [
        line
        for line in (
            rested([(out["labels"], "")], out["left"], "Labels resting here: ", "here", "here"),
            rested(
                [(each["labels"], f" on `{store.clean(each['name'])}`") for each in pastes],
                out["pasted_left"],
                "Resting on what was pasted into this pair: ",
                "on what was pasted into this pair",
                "there",
            ),
        )
        if line
    ]
    return "\n".join(lines).rstrip()


def rested(places: list[tuple[list[str], str]], left: list[str], lead: str, alone: str, after: str) -> str:
    """A line of `show_pair`'s, of the labels resting on something: `lead`, then each place's keys in the order
    written, followed by what names the place (nothing, for the pair's own messages), the places set apart by `; `.
    Lines left at the door (`left`, those among the keys of the kind `next`, in the order written) rest on many of the
    same messages, one after another, and only the newest is carried: two or more are counted, with the newest by its
    key, and not listed, in a sentence that says they rest `alone` where no key is listed, and `after`, with "too",
    where one is; one stays a key among the others. A place on which only counted lines rest is not named. Empty where
    no key rests."""
    left = left if len(left) > 1 else []
    listed = []
    for keys, place in places:
        shown = [key for key in keys if key not in left]
        if shown:
            listed.append(", ".join(shown) + place)
    sentences = [f"{lead}{'; '.join(listed)}."] if listed else []
    if left:
        where = f"{after} too" if listed else alone
        sentences.append(f"{many(len(left), 'line')} left at the door rest {where}, the newest of them {left[-1]}.")
    return " ".join(sentences)


def main(argv: list[str] | None = None, served: bool = False) -> int:
    """The door. `served` is the door's server calling in its own process (crossing/serve.py), which
    no command line can say: a label it marks is shown to the person by the hook after it."""
    parser = argparse.ArgumentParser(prog="door.py", description="The door to the Crossings store.")
    parser.add_argument(
        "verb",
        choices=[
            "look",
            "labels",
            "find",
            "thread",
            "mark",
            "frame",
            "status",
            "build",
            "strike",
            "copy",
            "home",
            "switch",
            "words",
            "page",
            "trace",
            "welcome",
            "layer",
        ],
    )
    parser.add_argument("rest", nargs="*")
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--home", choices=["here", "ours"], default="here")
    parser.add_argument("--session")
    parser.add_argument("--transcript")
    # The person's side in either spelling it is taken in, as it is offered (store.offered_as), which the usage names.
    parser.add_argument("--voice", type=store.offered_as, choices=[store.THEIR, store.OWN])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--around", type=int, default=2)
    parser.add_argument("--role")  # thread's: one of ROLES, and any other word is answered in a sentence
    parser.add_argument("--kind", choices=["relation", "work", "next", "refused", "silenced"])
    parser.add_argument("--day")
    parser.add_argument("--touch", action="store_true")
    parser.add_argument("--bare", action="store_true")
    parser.add_argument("--whose", type=store.offered_as, choices=[store.THEIR, store.OWN, "both"], default="session")
    parser.add_argument("--anchors", default="")
    parser.add_argument("--size", type=int)
    parser.add_argument("--why", default="")
    # frame's, for the person's command: the sentence after the frame of what the session's turns set in it take,
    # which the frame a cut carries, asked the same way, never holds
    parser.add_argument("--trade", action="store_true", help=argparse.SUPPRESS)
    # the hooks' own build, not the person's
    parser.add_argument("--by-hook", action="store_true", help=argparse.SUPPRESS)
    # the hooks module, for the person's command
    parser.add_argument("--by-module", action="store_true", help=argparse.SUPPRESS)
    # The model behind a call, as the server was handed it: the person's or the server's alone, since
    # it signs a label and decides which layer a stack may reach into.
    parser.add_argument("--model", default="", help=argparse.SUPPRESS)
    args = parser.parse_intermixed_args(argv)  # words and options in any order
    record.private()  # every folder and file the door makes is its owner's alone
    try:
        return answer(args, served)
    except record.Unnamed as err:  # an id that would name another file, or another line: nothing was written
        record.refused(err)
        print(UNNAMED)
        return 1
    except record.Linked as err:  # nothing was read or written through it
        record.refused(err)
        print(LINKED)
        return 1
    except sqlite3.OperationalError as err:  # no FTS5 here: the index cannot be made, and it is said so
        if not store.unsearchable(err):
            raise
        print(store.NO_SEARCH)
        return 1


def answer(args: argparse.Namespace, served: bool = False) -> int:
    cwd = Path(args.cwd).resolve()
    said = " ".join(args.rest).strip()
    if (args.verb in PERSONAL or args.transcript or args.session or (args.model and not served)) and not personal(args):
        print(PERSONS)  # a session's shell, or anything else that is not the person or the plugin
        return 1
    if args.session:
        record.ident(args.session)  # an id, looked for as it is: never a pattern
    narrowing = args.verb == "status" and not args.bare  # a status asked from any shell narrows a home left wide
    if args.verb in ("status", "look") and not personal(args):
        # A session's shell is answered as the door's server is: no folder of the home, no id that looks like a
        # key, no key the person alone is shown, and nothing said once is taken from the person's own status.
        args.bare = True
    if args.verb == "switch":
        if said.lower() not in ("on", "off", "toggle", "adopt", "join", "here"):
            print("switch takes one word: on, off, toggle, adopt, join or here.")
            return 2
        try:
            state = store.switch(cwd, said.lower())
        except OSError as err:  # the moment could not be kept: said, and not passed over
            print(UNKEPT.format(err.strerror or type(err).__name__))
            return 1
        if state == "astray":
            print(strayed(record.astray(cwd)))
            return 1
        if state == "unclaimed":
            print(unclaimed(store.unclaimed(cwd)))
            return 1
        if state == "linked":
            print(LINKED_HOME.format(store.here(cwd).resolve()))
            return 1
        if state == "below":
            print(BELOW.format(store.belongs(cwd)))
            return 1
        if state in ("alone", "occupied"):
            print(SWITCHED[state])
            return 1
        if state in ("on", "again", "restored"):
            folder = store.here(cwd)
            record.narrow(folder)  # what an older make left readable by other accounts
            source = Path(args.transcript) if args.transcript else transcript_of(args.session) if args.session else None
            if state != "on" and source is not None and source.is_file() and record.attended():
                # A span just closed: what this session said inside it is noted by id (see store.archive).
                if store.archive(source, folder):
                    with contextlib.suppress(OSError):  # held by another act: the next read makes the index
                        store.refresh(folder)
            if not store.searchable():  # said as it is switched on, before any search is asked for
                print(f"{SWITCHED[state]} {store.NO_SEARCH}")
                return 0
        print(SWITCHED[state])
        return 0
    stray = record.astray(cwd)
    if stray:
        print(strayed(stray))
        return 1
    # The home on this computer is no project's: it has no switch of its own, and is offered only
    # where the person switched Crossings on in this project, and it is on.
    ours = args.home == "ours"
    folder = store.offered(cwd) if ours else store.kept(cwd)
    # A folder below another home's, not answered for: no home is kept or read, and the guard on the archive's
    # files is still told where that home lies, so that it keeps a session here from opening it.
    above = None if ours or folder is not None else store.waiting(cwd)
    if args.verb == "home":
        folder = folder or above
        if folder is None or not folder.is_dir():
            return 1  # and nothing is said: there is no folder to name
        print(folder)
        return 0
    if folder is None:
        print(NOT_ON if above is None else BELOW_BARE if args.bare else BELOW.format(store.belongs(cwd)))
        return 1
    record.sound(folder)  # a link anywhere in the home, and nothing is read or written
    if narrowing:
        record.narrow(folder)  # what an older make left readable by other accounts
    on = ours or store.active(folder)  # switched off, a home is read and nothing is added to it
    if args.verb in ("frame", "page") and not (record.attended() or record.terminal()):
        print(UNSEATED)  # nothing is carried to a session no person sits in: a headless one, or any other tool's
        return 1
    if args.verb in ("words", "page", "trace"):
        return for_the_module(args.verb, folder, on, said)
    if args.verb == "welcome":
        # What a session running when the person turns the switch is told, through their
        # command: switched off, that nothing is kept from now; switched on again, that it is
        # kept again; and the welcome, by the rule a session's start is welcomed by (see
        # hook.welcomed and hook.switched).
        from crossing import hook  # here alone: no other verb needs the hooks' own script

        told = None if ours else hook.switched(folder, said)
        if told is None:
            return 1
        print(told)
        return 0
    if args.verb == "layer":
        # The person's, from a shell: the door's server does not offer it.
        key = layer.named(said) if len(args.rest) == 1 else ""
        if not key or key != said:
            print("layer takes one model's key, with no space in it: the model the lines with none were made with.")
            return 2
        if not on:  # switched off, nothing is added to a home: no line is signed, and nothing is written
            print("Crossings is switched off for this project, so nothing was signed.")
            return 1
        signed = store.layered(folder, key)
        if signed is None:
            print("Another act was writing this home, so nothing was signed: try again in a moment.")
            return 1
        labels, messages = signed
        print(
            f"Signed {many(labels, 'label')} and {many(messages, 'message')} of the session's as made with {key}; "
            "nothing that had a model was changed."
        )
        return 0

    if args.transcript:  # handed by its path: from a shell, the person's own act; or the hooks' own build
        source = Path(args.transcript)
    elif args.session and record.attended():  # the hooks module's way, for a session a person sits in alone
        source = transcript_of(args.session)
    else:
        source = None
    fresh = 0
    if source is not None and source.exists() and on and not ours:
        # A build is asked for at a session's end, and reads the transcript whole: what a marker
        # stepped over is kept there at the latest. What a session no person sat in held is
        # passed over, unless the person handed the transcript over themselves.
        fresh = store.archive(
            source,
            folder,
            whole=args.verb == "build",
            taken=bool(args.transcript) and not (args.by_hook or args.by_module),
        )
    try:
        if args.verb == "build" and folder.is_dir():  # the home on this computer is not made by a build
            store.build(folder)  # whole, always: the person's way to make the index again from the plain files
        elif fresh:
            store.refresh(folder)  # what was archived is added to the index, where nothing else changed
    except OSError:  # the home was held by another act all the while (see store._built)
        print(UNBUILT)
        return 1

    # The model that is there for this call: as the door's server was handed it (see crossing/layer.py),
    # or, where the session is named, what its hooks were told and what it said last. Not known, and
    # nothing is layered: everything is read as it was before layers.
    project = folder if not ours else store.kept(cwd)
    facing = layer.named(args.model) or (
        layer.current(project, source.stem[:8])
        if args.verb in ("mark", "frame", *ASKING) and source is not None and project is not None
        else ""
    )
    if served and not facing and args.verb in ASKING and project is not None:
        # What a refusal's family is called, standing or silenced, is said for the model that asks (see
        # store.refusals): through the server, the model of the session that spoke last, as `crossing` takes it.
        last = spoke_last(folder)
        facing = layer.current(project, last) if last else ""
    # The session a frame is for, as the archive names one: by its transcript, else by the id it was asked by.
    session = source.stem[:8] if source is not None else (args.session or "")[:8]
    # In a home where more than one model is known, the lists say which made each line of the session's.
    named = args.verb in ("look", "labels", "find", "thread") and len(store.known(folder)) > 1
    if args.verb == "look":
        out = store.look(folder, model=facing)
        if named and out["left"]:
            out["left"]["model"] = store.listed(folder, ids=(out["left"]["id"],))["labels"][0]["model"]
        print(show_look(out, args.bare, named))
    elif args.verb == "labels":
        out = store.listed(folder, args.kind, args.day, tuple(args.rest), model=facing)
        print(show_labels(out, bool(args.rest), args.bare, named))
    elif args.verb == "find":
        print(show_find(store.find(folder, said, args.voice, args.limit), named))
    elif args.verb == "thread" and args.role is not None:  # a pair in place of the messages around: --around is idle
        role = role_of(args.role)  # and so named in the answer, whichever spelling asked for it
        if role is None:
            print(UNROLED)
            return 2
        out = store.tied(folder, said.strip("`"), ROLES[role])
        if args.touch and on and out["found"] and out["paired"]:  # a pull as a thread's: the id named, and no more
            store.reached(folder, "thread", [out["asked"]])
        print(show_pair(out, role, named))
    elif args.verb == "thread":
        out = store.thread(folder, said.strip("`"), args.around)
        if args.touch and on and out["found"]:
            store.reached(folder, "thread", [out["asked"]])
        print(show_thread(out, named))
    elif args.verb == "mark":
        if not on:
            print("not marked: Crossings is switched off for this project")
            return 1
        # Which model wrote it, and which layer a stack may reach into, can be told only where the
        # model that marks is: named by the server's hand-off, or by the session that marks it.
        out = store.mark(
            folder,
            args.kind or "work",
            args.whose,
            said,
            args.anchors.replace(",", " ").split(),
            model=facing,
            facing=facing,
            persons=personal(args) and not served,
        )
        if args.touch and out["written"]:
            store.reached(folder, "mark", [out["id"], *out["anchors"]])
        if not out["written"]:
            print(f"not marked: {out['why']}")
            return 1
        written = store.settled(out_kind(args), args.whose)  # whose it was written as
        theirs = out_kind(args) == "relation" or store.theirs(written) or written == "both"  # as hook.shown asks
        if not served and theirs:
            store.shell_marked(folder, out["id"])  # no hook shows it to the person: their status will
        # The hook after the call shows it to the person under the turn: through the server the plugin started, whose
        # hook is wired to the door's own tools alone.
        shown = served and theirs and record.from_plugin()
        # after the key, how long it is where it is long, and then, once a line, that the line at the door is older
        overtaken = out_kind(args) == "work" and store.overtaken(folder, out["id"])
        added = [each for each in (long_said(out_kind(args), said, shown), OVERTAKEN if overtaken else "") if each]
        print(
            f"marked {out['id']}"
            + (f", in place of {' and '.join(out['replaced'])}" if out["replaced"] else "")
            + ("" if args.bare else f" in {out['page']}")
            + ("." + "".join(f" {each}" for each in added) if added else "")
        )
        if served and args.kind == "next":
            # A line left at the door through the server, while the session still holds what was said: the person's
            # messages the record weighs and no label rests on, for the session that spoke last, as `frame` finds it.
            last = spoke_last(folder)
            db = store._open(folder)
            try:
                weighs = sample.unmarked(folder, db, last, set(store.flagged(folder)))
            finally:
                db.close()
            if weighs:
                print("\n" + weighs)
    elif args.verb == "frame":
        size = frame.bounded(args.size) if args.size is not None else None  # a size of 0 is asked, and held
        held = store.status(folder) if served else {}
        if served and not any(held[each] for each in ("his", "session", "pasted", "labels", "struck")):
            # the door's server's `crossing`, in a room that holds nothing: no frame is made of it, and it is said as
            # `look` says it
            print(show_look(store.look(folder), bare=True), end="")
        else:
            if served:  # the server is told no session: the frame is the one of the session that spoke last here
                session = spoke_last(folder)
                facing = facing or (layer.current(project, session) if session and project is not None else "")
            # What the session's turns set beside the person's sentences take (see frame.trade) is told after the
            # frame and apart from it: to a session through the server, and to the person at their terminal or
            # through their command (--trade). The hooks module asks for a cut's frame as the command does, but
            # with no --trade, and carries what the door gives whole: so a carried frame never holds it. Where it is
            # told, it comes of the making that made the frame (see frame.with_trade).
            telling = served or args.trade or record.terminal()
            made, traded = (
                frame.with_trade(folder, size, model=facing, session=session)
                if telling
                else (frame.compose(folder, size, model=facing, session=session), "")
            )
            print(made + (f"\n{traded}\n" if traded else ""), end="")
    elif args.verb in ("status", "build"):
        held = store.status(folder, facing)
        apart = store.refusals(folder, facing)
        # What is said once is said only where it can be noted as told: a home switched off is read, and nothing
        # is written to it, so those sentences wait until it is on (see store.once).
        quiet = args.bare or not on
        print(
            holding(folder, held, args.bare)
            + (
                " Of the labels: {cooled} cooled, {misaligned} misaligned, {unresolved} unresolved.".format(
                    **held["states"]
                )
                if held["states"]["cooled"] or held["states"]["misaligned"] or held["states"]["unresolved"]
                else ""
            )
            + (
                f" Of the refusals, {len(apart['standing'])} stand{'s' if len(apart['standing']) == 1 else ''} and "
                f"{len(apart['silenced'])} {'is' if len(apart['silenced']) == 1 else 'are'} silenced"
                + (f"; {elsewhere(apart)}." if elsewhere(apart) else ".")
                if any(apart.values())
                else ""
            )
            + (
                f" It also holds {held['pasted']} pasted text{'s' if held['pasted'] != 1 else ''}, kept apart from "
                "the person's words."
                if held["pasted"]
                else ""
            )
            + (
                " Which model wrote it is known for {labels} of the labels and {session} of the session's "
                "messages.".format(**held["models"])
                if held["models"]["labels"] or held["models"]["session"]
                else ""
            )
            + (
                f" {held['unread']} line{'' if held['unread'] == 1 else 's'} of the archive could not be read and "
                f"{'was' if held['unread'] == 1 else 'were'} passed over."
                if held["unread"]
                else ""
            )
            + (
                f" Crossings was off here {held['off']} time{'' if held['off'] == 1 else 's'}"
                + (", the last still open" if held["off_now"] else "")
                + ": nothing said while it was off is kept."
                if held["off"]
                else ""
            )
            + (
                f" {held['off_unread']} line{'' if held['off_unread'] == 1 else 's'} of the record of "
                "when Crossings was off"
                + ("" if args.bare else f" ({folder / 'off.txt'})")
                + " could not be read and "
                + ("was" if held["off_unread"] == 1 else "were")
                + " passed over."
                if held["off_unread"]
                else ""
            )
            + (f" Newly archived: {fresh}." if fresh else "")
            + ("".join(" " + FLAGGED.format(each) for each in held["flagged"]) if not args.bare else "")
            + (" " + COPY_KEY if os.environ.get("CROSSING_COPY_KEY") and not args.bare else "")
            + (" " + LOST if held["lost"] else "")
            + (
                " "
                + SHELLED.format(
                    many(len(held["shelled"]), "label") + (" was" if len(held["shelled"]) == 1 else " were"),
                    ", ".join(held["shelled"]),
                )
                if held["shelled"] and not quiet
                else ""
            )
            + (" " + store.PASSING if not quiet and not ours and store.passed_note(cwd, folder, "status") else "")
            + (
                " " + IGNORE_SAID
                if not quiet
                and not ours
                and store.leaves_said(folder)
                and store.once(folder, store.IGNORED_TOLD, "said")
                else ""
            )
            + older_copy(args, cwd, folder, ours or quiet)
            + told_once(args, folder, held, quiet)
        )
        if held["shelled"] and not quiet and personal(args):
            store.shelled_told(folder, held["shelled"])  # told: the next status says only what is marked since
        if held["arrived"] and args.verb == "status" and not quiet and personal(args):
            store.arrived_told(folder, held["arrived"])
        if held["signs_arrived"] and args.verb == "status" and not quiet and personal(args):
            store.signs_arrived_told(folder, held["signs_arrived"])
        if held["collided"] and args.verb == "status" and not quiet and personal(args):
            store.collided_told(folder, held["collided"])
    elif args.verb == "strike":
        out = store.strike(folder, said, args.why)
        print(struck(out) if out["struck"] else f"not struck: {out['why']}")
        if not out["struck"]:
            return 1
    else:  # copy, the last of the verbs the parser lets through
        dest = second.destination(folder)
        if dest is None:
            print(f"No second copy is set for this home: {folder / 'copy'} names no folder.")
            return 1
        top = record.located(cwd)[1]
        if record.lies_in(dest, top):
            print(INSIDE)
            return 1
        try:
            out = second.make(folder, dest, second.named(top), top)
        except second.Failed as err:  # one sentence, and no command: the Keychain's holds the passphrase
            print(f"not copied: {err}")
            if args.by_hook:  # a session's end: no one reads what it prints, so the log keeps it
                record.log(f"not copied: {err}")
            return 1
        if args.by_hook and not out["copied"] and out["why"] != second.NOTHING:
            record.log(f"not copied: {out['why']}")
        print(
            f"copied {many(out['files'], 'plain file')}, encrypted, to {out['image']} ({many(out['bytes'], 'byte')}), "
            "and read back the same"
            if out["copied"]
            else f"not copied: {out['why']}"
        )
        return 0 if out["copied"] else 1
    return 0


def spoke_last(folder: Path) -> str:
    """The session of the newest message the home's index holds, or nothing where it holds none. The door's server
    is told no session; the hook before each of its calls brings the archive up to date, so that in the ordinary
    case the session that spoke last is the one calling."""
    db = store._open(folder)
    try:
        row = db.execute("select session from said where session != '' order by seq desc limit 1").fetchone()
    finally:
        db.close()
    return row[0] if row else ""


def holding(folder: Path, held: dict, bare: bool) -> str:
    """What `status` says first: what the store holds, with the span of days its messages were said
    in where they have one; or, where it holds no message, no label and nothing struck, that it holds
    nothing yet."""
    store_ = "The store" + ("" if bare else f" at {folder}")
    if not (held["his"] or held["session"] or held["pasted"] or held["labels"] or held["struck"]):
        return f"{store_} holds nothing yet."
    days = f", {store.clean(held['from'])} to {store.clean(held['to'])}" if held["from"] else ""
    return (
        f"{store_} holds {many(held['his'], 'message')} of the person's and {held['session']} of the session's "
        f"({many(held['characters'], 'character')}{days}), {many(held['labels'], 'label')}, "
        f"and {held['struck']} struck."
    )


def told_once(args: argparse.Namespace, folder: Path, held: dict, quiet: bool = False) -> str:
    """The sentences of the person's own status that are said once each: the labels that came into
    the pages by no mark through the door (store.arrived), the lines of models.txt that came by no
    signing through the door (store.signs_arrived), the ids two messages share
    (store.collided), and the files that hold a line that is no text (store.damaged). The door's
    server is told none of them, and neither is a build, which the hooks run with no one to read it; nor
    is a status that is `quiet`, of a home switched off, where nothing can be noted as told."""
    if args.bare or quiet or args.verb != "status":
        return ""
    came = held["arrived"]
    out = ""
    if came:
        some = len(came) != 1
        out += (
            " "
            + (f"{len(came)} labels" if some else "A label")
            + f" {ARRIVED} cross{'' if some else 'es'} every cut as "
            f"any other: {', '.join(as_such(folder, came))}."
        )
    signs = held["signs_arrived"]
    if signs:
        some = len(signs) != 1
        out += (
            " "
            + (f"{len(signs)} lines" if some else "A line")
            + f" of models.txt {SIGNS_CAME} {'are' if some else 'is'} followed as any other: "
            + ", ".join(
                store.clean(each).replace("@", " ", 1).split()[0] + " by " + store.clean(each.split()[-1])
                for each in signs
            )
            + "."
        )
    out += "".join(" " + COLLIDED.format(each) for each in held["collided"])
    hurt = store.damaged(folder)
    return out + (" " + DAMAGED.format(", ".join(hurt)) if hurt else "")


def as_such(folder: Path, keys: list[str]) -> list[str]:
    """Labels by their keys, a standing line and one that speaks for the person (theirs or both)
    each said as such."""
    by = {label["id"]: label for label in store.labels(folder)}
    out = []
    for key in keys:
        label = by.get(key, {})
        such = (["a standing line about the two of you"] if label.get("kind") == "relation" else []) + (
            ["speaking for the person"] if store.theirs(label.get("whose")) or label.get("whose") == "both" else []
        )
        out.append(f"{key} ({', '.join(such)})" if such else key)
    return out


OLDER = (
    "An older second copy, {}, is named by the project's folder alone and is no longer renewed; it is left as it is."
)


def older_copy(args: argparse.Namespace, cwd: Path, folder: Path, ours: bool) -> str:
    """The sentence of the person's own status, once, for an image an earlier make named by the
    project's folder alone (see second.older): it is not renewed, and is left as it is."""
    if args.bare or ours or args.verb != "status" or not personal(args):
        return ""
    dest = second.destination(folder)
    image = second.older(dest, record.located(cwd)[1]) if dest is not None else None
    return " " + OLDER.format(image) if image is not None and store.once(folder, second.OLDER_TOLD, str(image)) else ""


def out_kind(args: argparse.Namespace) -> str:
    """The kind of label a mark asks for, as store.mark reads it."""
    return args.kind or "work"


def struck(out: dict) -> str:
    """What a strike says: how many lines went, the hand-over words pages it mended or took away
    whole (a session's strike takes every one), the labels left resting on what it took, and what no
    strike can reach."""
    some = len(out["dropped"]) > 1
    return (
        f"struck {out['token']}: {many(out['removed'], 'line')} removed, and it will not come back at a build."
        + (f" Its words were taken out of {', '.join(out['mended'])}." if out["mended"] else "")
        + (
            f" The hand-over words page{'s' if some else ''} {', '.join(out['dropped'])} could not be mended "
            f"line by line and {'were' if some else 'was'} removed whole."
            if out["dropped"]
            else ""
        )
        + (
            f" The hand-over words page{'s' if len(out['cleared']) > 1 else ''} {', '.join(out['cleared'])} "
            f"{'were' if len(out['cleared']) > 1 else 'was'} removed whole, as a session's strike takes every one: "
            "the next hand-over makes it again from the record."
            if out.get("cleared")
            else ""
        )
        + resting(out.get("resting", []))
        + " "
        + store.REACH
    )


def resting(keys: list[str]) -> str:
    """The labels that rest on a message a strike took, which it leaves as they are: by key, so
    that the person can strike them too."""
    if not keys:
        return ""
    if len(keys) == 1:
        return (
            f" The label that rests on what was struck stays as it is: {keys[0]}. door.py strike {keys[0]} "
            "takes it out as well."
        )
    return (
        f" The labels that rest on what was struck stay as they are: {', '.join(keys)}. door.py strike <key> takes "
        "each out as well."
    )


def for_the_module(verb: str, folder: Path, on: bool, said: str) -> int:
    """What the hooks module reads of a home and writes into it, through the door, so that no
    file of a home is reached by any other way than `within`: the one-word files that decide a
    cut, as one JSON object; the hand-over page, with its words beside it where there are any;
    and the trace of what a cut did, which is added only where Crossings is on."""
    if verb == "words":
        print(json.dumps({name: store.word(folder, name) for name in ("switch", "mode", "carry")}))
        return 0
    if verb == "page":
        text = handed_over(folder)
        if not text:
            return 1
        print(text)
        return 0
    try:
        trace = json.loads(said)
    except ValueError:
        trace = None
    if not isinstance(trace, dict):
        print("trace takes one JSON object.")
        return 2
    if not on:
        return 1
    store.within(folder, "last-cut.json").write_text(json.dumps(trace), encoding="utf-8")
    return 0


WORDS_HEAD = "## The anchored words, from the record"


def handed_over(folder: Path) -> str:
    """The hand-over page as the module carries it where no frame can be made: never raw. Its label
    rows alone, read as every label page is read (store.labels), each in the frame's own form and
    cleaned (store.clean); and of its words page only the ids of the lines of the form
    crossing/handover.py writes for a message one of those rows rests on, where it names nothing the
    home keeps out: each is given with the words the home's own archive holds under it (store.worded),
    never with the words the page holds, and an id the archive does not hold is not given; the line
    of what the transcript did not hold is written again from the ids of it those rows rest on. The
    whole within frame.MOST; nothing where the page holds no row."""
    gone = store.struck(folder)
    rows = [label for label in store.labels(folder) if label["page"] == "hand-over.md" and label["id"] not in gone]
    lines = [
        f"- {label['id']} ({store.owner(label['whose'])}): {store.clean(label['text'])} "
        f"[{store.rests({**label, 'beneath': [key for key, _ in label['beneath']]})}]"
        for label in rows
    ]
    rested = {anchor.split("+")[0] for label in rows for anchor in label["anchors"]}  # the ids the rows name
    words = plain(folder, "hand-over.words.md")
    if words and any(each in words for each in store.kept_out_ids(folder)):
        words = ""  # a words page that names what was struck or kept off is not given: handover.py makes it again
    written = words.split("\n")
    # The page names the ids alone: what is given under each is what the archive holds there, never the page's text.
    carried = list(dict.fromkeys(m.group(1) for m in map(store.WORDS.match, written) if m and m.group(1) in rested))
    held = store.worded(folder, set(carried)) if carried else {}
    said = [store.clean(held[each]) for each in carried if each in held]
    for line in written:
        if line.startswith(store.MISSING):
            missing = [each for each in re.findall(r"`([0-9a-f]{8})`", line) if each in rested]
            said += [store.MISSING + ", ".join(f"`{each}`" for each in missing) + "."] if missing else []
    out, used = [], 0
    for line in lines + ([""] + [WORDS_HEAD, ""] + said if said else []):
        if used + len(line) + 1 > frame.MOST:
            break
        out.append(line)
        used += len(line) + 1
    return "\n".join(out).strip() if lines else ""


def plain(folder: Path, name: str) -> str:
    """A plain file of the home, as its text stands, or nothing where it cannot be read."""
    try:
        return "\n".join(record.lines_in(store.within(folder, name))).strip()  # a line that is no text is passed over
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
