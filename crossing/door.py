#!/usr/bin/env python3
"""The door to the store.

  door.py look
  door.py labels [id ...] [--kind relation|work|next] [--day YYYY-MM-DD]
  door.py find <words> [--voice his|session] [--limit N]       word*  "a phrase"
  door.py thread <id> [--around N]
  door.py mark --kind relation|work|next --whose his|session|both --anchors id,id <sentence>
                                           an id is a message's, or a label's key: the label then stands over that one
  door.py frame [--size N]
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
computer (ours) is offered only to a project where Crossing is switched on and on; from any
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
thread or a mark is noted in the home's plain log of what was pulled. With --bare no answer names
a file or a folder: that is how the door's server asks, so that nothing a session reads points a
hand at the file system. Nothing comes back without its place: an id, a voice, a time, and the
labels that rest there. No model is called.

A project's home is its own `crossings/` folder, or, where it has none, a folder outside it
that `switch on` makes. Either is believed only once the person has switched Crossing on in
that project, which `switch on` keeps in a record of the person's own, outside every project.
Until then Crossing was never switched on there: every other verb says so in a sentence, with
exit status 1, and makes nothing. A home that is there already and holds messages or labels
this record has no line for is not switched on by `switch on`: it says what is there, and
`switch adopt` takes it. A setting (CROSSING_HOME, CROSSING_HOMES, CROSSING_OURS,
CROSSING_SWITCHED) that names a place inside the project is not followed: every verb says so
in a sentence, with exit status 1. `switch on` and `status` narrow a home that is readable by
other accounts to its owner alone. `switch` is the person's, from their terminal or through their command, and
`strike`, `layer` and `copy` from their terminal; `home` prints the folder of a home that is believed, and
nothing otherwise; the door's server offers none of these. Switched off, a home is
still read, and nothing is added to it; and nothing said until it is switched on again is ever
kept, by any verb, from any transcript (see crossing/off.py). No file of a home is read or written through a link:
where one is, the door says so in a sentence, with exit status 1, and writes nothing; and so for an id that
cannot name a file (record.ident). `status` and `look` from a shell, not --bare, also say which kept
messages look like they hold a key (store.flagged), and `status` that the second copy's passphrase is taken
from the environment where it is, and once that an older second copy is no longer renewed. A
strike's answer names the labels that rest on what it struck, and ends with what no strike can
reach; a strike that struck nothing says why in one sentence, with exit status 1.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import frame, layer, record, second, store  # noqa: E402

VOICE = {"his": "the person", "session": "the session", "pasted": "pasted by the person"}
SHORT = 240  # characters of a label's sentence in a list; by its id it is given whole
# How the person's switch stands, as their command says it; and what every other verb says of
# a project that has no home, where nothing is kept and nothing is made by looking.
SWITCHED = {
    "on": "Crossings is on for this project.",
    "again": "Crossings is on again for this project: what is said from now on is kept, and nothing said while "
    "it was off was kept.",
    "off": "Crossings is off for this project: no cut is counted, noted or answered, and nothing said from now "
    "until it is switched on again will be kept.",
    "never": "Crossings was never switched on for this project.",
    "restored": "Crossings is on again for this project. Its record of when Crossings was off had been taken "
    "away or cut short, so everything said before this moment that was not kept already is kept "
    "off the record; what is said from now on is kept.",
}
UNKEPT = (
    "The record of when Crossings was off could not be written in this project's home ({}), so the switch may "
    "not stand as asked: status says how it stands."
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
    "The record of when Crossings was off in this project is missing or shorter than it was, so nothing more is "
    "archived here until the person switches Crossings on again."
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
COLLIDED = "Two messages of this home share the id {0}: thread {0} names both, and a strike takes one by its whole id."
# The verbs that are the person's alone, or the hooks module's: those that write a kept file of the home.
PERSONAL = ("switch", "strike", "layer", "copy", "trace", "welcome")


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


def many(n: int, word: str) -> str:
    return f"{n} {word}{'' if n == 1 else 's'}"


def unclaimed(held: dict) -> str:
    """What `switch on` says of a home that holds what this computer has no record of switching
    on (see store.unclaimed), in place of switching it on."""
    return (
        f"This project's home already holds {many(held['messages'], 'message')} and "
        f"{many(held['labels'], 'label')} that this computer has no record of switching on, in {held['folder']}. "
        "Run the same command again with the word adopt (/crossings adopt, or door.py switch adopt from a shell) "
        "to take them as your own, or remove that folder first to start clean. Crossings was not switched on."
    )


def when(at: str) -> str:
    return at[:16].replace("T", " ") + " UTC" if at else "no time"


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
            f"- {label['id']} ({label['kind']}, {store.clean(label['whose'])}{by(label, named)}): "
            f"a standing line about the two of you, not recited here; `labels {label['id']}` gives it."
            if label["kind"] == "relation" and not every
            else f"- {label['id']} ({label['kind']}, {store.clean(label['whose'])}{by(label, named)}): "
            + (
                store.clean(label["text"])
                if every or len(label["text"]) <= SHORT
                else store.clean(label["text"][:SHORT]).rstrip() + " […]"
            )
            + f" [{store.rests(label)}]"
            for label in shown
        ]
        if len(shown) < len(out["labels"]):
            lines.append(f"{len(out['labels']) - len(shown)} more labels hold one of these words.")
    if out["said"]:
        lines += ["", "Said:"] + [
            f"- `{s['id']}` {voiced(s, named)}, {when(s['at'])}: {' '.join(store.clean(s['part']).split())}"
            + (f" (labels: {', '.join(s['labels'])})" if s["labels"] else "")
            for s in out["said"]
        ]
        lines += ["", "For any of these in its place: thread <id>."]
    return "\n".join(lines)


def row_of(label: dict, whole: bool = True, named: bool = False) -> str:
    """One label as a line: whose it is, its day, its state where that is not simply carried,
    the model that wrote it where that is known (given whole; or, in a home where more than one
    model is known, wherever the label is not the person's), its sentence, and in brackets what
    it rests on, the lines stacked beneath it first."""
    text = store.clean(
        label["text"] if whole or len(label["text"]) <= SHORT else label["text"][:SHORT].rstrip() + " […]"
    )
    day = f", {label['day']}" if label.get("day") else ""
    state = label.get("state", "carried")
    state = "" if state == "carried" else f", cooled beneath {label['parent']}" if state == "cooled" else f", {state}"
    written = f", written by {store.clean(label['model'])}" if whole and label.get("model") else by(label, named)
    return (
        f"{'  ' * label.get('depth', 0)}- {label['id']} "
        f"({store.clean(label['whose'])}{day}{state}{written}): {text} "
        f"[{store.rests(label)}]"
    )


def show_look(out: dict, bare: bool = False, named: bool = False) -> str:
    """The room. The standing lines are named by id and number only, and so is a stack over
    them; see store.look."""
    said = sum(d["his"] + d["session"] for d in out["days"])
    lines = [
        f"The store in outline: {len(out['days'])} day{'s' if len(out['days']) != 1 else ''}, {said} messages, "
        f"{len(out['standing']) + len(out['work'])} labels, {out['struck']} struck"
        + (f"; kept up to {when(out['last'])}." if out["last"] else "."),
        "",
        "Days:",
    ]
    days = [
        (
            (d["day"], 0, ""),
            f"- {d['day'] or 'no date'}: {d['his']} of the person's, "
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


def show_thread(out: dict, named: bool = False) -> str:
    asked = store.clean(out["asked"])
    if out.get("twins"):
        twins = [f"`{store.clean(each)}`" for each in out["twins"]]
        return (
            f"thread of `{asked}`: {'two' if len(twins) == 2 else len(twins)} messages are named `{asked}`, "
            f"{', '.join(twins[:-1])} and {twins[-1]}; thread with a whole id gives each."
        )
    if not out["found"]:
        return f"thread of `{asked}`: no such message in the store."
    # Numbered in the order they were said, with the one that was named marked in words: an order
    # left to be inferred from a list gets retold wrongly.
    lines = [f"thread of `{asked}`: {len(out['said'])} messages, in the order they were said", ""]
    gaps = out.get("gaps", [])
    for number, s in enumerate(out["said"], 1):
        lines += [gap(g) for g in gaps if g["before"] == s["seq"]]
        lines.append(
            f"{number}. `{s['id']}` {voiced(s, named)}, {when(s['at'])}"
            + (", the one you named" if s["is_asked"] else "")
            + (f" (labels: {', '.join(s['labels'])})" if s["labels"] else "")
            + ":"
        )
        lines += ["    " + part for part in store.clean(s["text"], lines=True).splitlines()] + [""]
    shown = {s["seq"] for s in out["said"]}
    lines += [gap(g) for g in gaps if g["before"] not in shown]  # after the newest of them
    if out["labels"]:
        lines += ["Labels resting here:"] + [
            f"- {label['id']} ({label['kind']}, "
            f"{store.clean(label['whose'])}{by(label, named)}): "
            f"{store.clean(label['text'])}"
            for label in out["labels"]
        ]
    return "\n".join(lines).rstrip()


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
    parser.add_argument("--voice", choices=["his", "session"])
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--around", type=int, default=2)
    parser.add_argument("--kind", choices=["relation", "work", "next"])
    parser.add_argument("--day")
    parser.add_argument("--touch", action="store_true")
    parser.add_argument("--bare", action="store_true")
    parser.add_argument("--whose", choices=["his", "session", "both"], default="session")
    parser.add_argument("--anchors", default="")
    parser.add_argument("--size", type=int)
    parser.add_argument("--why", default="")
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
    if args.verb == "switch":
        if said.lower() not in ("on", "off", "toggle", "adopt"):
            print("switch takes one word: on, off, toggle or adopt.")
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
        if state in ("on", "again", "restored"):
            folder = store.here(cwd)
            record.narrow(folder)  # what an older make left readable by other accounts
            source = Path(args.transcript) if args.transcript else transcript_of(args.session) if args.session else None
            if state != "on" and source is not None and source.is_file() and record.attended():
                # A span just closed: what this session said inside it is noted by id (see store.archive).
                if store.archive(source, folder):
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
    # where the person switched Crossing on in this project, and it is on.
    ours = args.home == "ours"
    folder = store.offered(cwd) if ours else store.kept(cwd)
    if args.verb == "home":
        if folder is None or not folder.is_dir():
            return 1  # and nothing is said: there is no folder to name
        print(folder)
        return 0
    if folder is None:
        print(NOT_ON)
        return 1
    record.sound(folder)  # a link anywhere in the home, and nothing is read or written
    if args.verb == "status" and not args.bare:
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
    if args.verb == "build" and folder.is_dir():  # the home on this computer is not made by a build
        store.build(folder)  # whole, always: the person's way to make the index again from the plain files
    elif fresh:
        store.refresh(folder)  # what was archived is added to the index, where nothing else changed

    # The model that is there for this call: as the door's server was handed it (see crossing/layer.py),
    # or, where the session is named, what its hooks were told and what it said last. Not known, and
    # nothing is layered: everything is read as it was before layers.
    project = folder if not ours else store.kept(cwd)
    facing = layer.named(args.model) or (
        layer.current(project, source.stem[:8])
        if args.verb in ("mark", "frame") and source is not None and project is not None
        else ""
    )
    # In a home where more than one model is known, the lists say which made each line of the session's.
    named = args.verb in ("look", "labels", "find", "thread") and len(store.known(folder)) > 1
    if args.verb == "look":
        out = store.look(folder)
        if named and out["left"]:
            out["left"]["model"] = store.listed(folder, ids=(out["left"]["id"],))["labels"][0]["model"]
        print(show_look(out, args.bare, named))
    elif args.verb == "labels":
        print(
            show_labels(store.listed(folder, args.kind, args.day, tuple(args.rest)), bool(args.rest), args.bare, named)
        )
    elif args.verb == "find":
        print(show_find(store.find(folder, said, args.voice, args.limit), named))
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
        if not served and (out_kind(args) == "relation" or args.whose in ("his", "both")):
            store.shell_marked(folder, out["id"])  # no hook shows it to the person: their status will
        print(
            f"marked {out['id']}"
            + (f", in place of {' and '.join(out['replaced'])}" if out["replaced"] else "")
            + ("" if args.bare else f" in {out['page']}")
        )
    elif args.verb == "frame":
        print(frame.compose(folder, frame.bounded(args.size) if args.size else None, model=facing), end="")
    elif args.verb in ("status", "build"):
        held = store.status(folder)
        print(
            f"The store{'' if args.bare else f' at {folder}'} holds {held['his']} messages of the person's and "
            f"{held['session']} of the "
            f"session's ({held['characters']} characters, {held['from']} to {held['to']}), {held['labels']} labels, "
            f"and {held['struck']} struck."
            + (
                " Of the labels: {cooled} cooled, {misaligned} misaligned, {unresolved} unresolved.".format(
                    **held["states"]
                )
                if held["states"]["cooled"] or held["states"]["misaligned"] or held["states"]["unresolved"]
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
                if held["shelled"] and not args.bare
                else ""
            )
            + (" " + store.PASSING if not args.bare and not ours and store.passed_note(cwd, folder, "status") else "")
            + (
                " " + IGNORE_SAID
                if not args.bare
                and not ours
                and store.leaves_said(folder)
                and store.once(folder, store.IGNORED_TOLD, "said")
                else ""
            )
            + older_copy(args, cwd, folder, ours)
            + told_once(args, folder, held)
        )
        if held["shelled"] and not args.bare and personal(args):
            store.shelled_told(folder)  # told the person: the next status says only what is marked since
        if held["arrived"] and args.verb == "status" and not args.bare and personal(args):
            store.arrived_told(folder)
        if held["collided"] and args.verb == "status" and not args.bare and personal(args):
            store.collided_told(folder)
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
        out = second.make(folder, dest, second.named(top), top)
        print(
            f"copied {out['files']} plain files, encrypted, to {out['image']} ({out['bytes']} bytes), "
            "and read back the same"
            if out["copied"]
            else f"not copied: {out['why']}"
        )
        return 0 if out["copied"] else 1
    return 0


def told_once(args: argparse.Namespace, folder: Path, held: dict) -> str:
    """The sentences of the person's own status that are said once each: the labels that came into
    the pages by no mark through the door (store.arrived), the ids two messages share
    (store.collided), and the files that hold a line that is no text (store.damaged). The door's
    server is told none of them, and neither is a build, which the hooks run with no one to read it."""
    if args.bare or args.verb != "status":
        return ""
    came = held["arrived"]
    out = ""
    if came:
        some = len(came) != 1
        out += (
            " "
            + (f"{len(came)} labels" if some else "A label")
            + f" {ARRIVED} cross{'' if some else 'es'} every cut as "
            f"any other: {', '.join(came)}."
        )
    out += "".join(" " + COLLIDED.format(each) for each in held["collided"])
    hurt = store.damaged(folder)
    return out + (" " + DAMAGED.format(", ".join(hurt)) if hurt else "")


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
    whole, the labels left resting on what it took, and what no strike can reach."""
    some = len(out["dropped"]) > 1
    return (
        f"struck {out['token']}: {out['removed']} line(s) removed, and it will not come back at a build."
        + (f" Its words were taken out of {', '.join(out['mended'])}." if out["mended"] else "")
        + (
            f" The hand-over words page{'s' if some else ''} {', '.join(out['dropped'])} could not be mended "
            f"line by line and {'were' if some else 'was'} removed whole."
            if out["dropped"]
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
    and the trace of what a cut did, which is added only where Crossing is on."""
    if verb == "words":
        print(json.dumps({name: store.word(folder, name) for name in ("switch", "mode", "carry")}))
        return 0
    if verb == "page":
        page, words = (plain(folder, name) for name in ("hand-over.md", "hand-over.words.md"))
        if not page:
            return 1
        if words and any(each in words for each in store.kept_out_ids(folder)):
            words = ""  # a words page that names what was struck or kept off is not given: handover.py makes it again
        print(page + (f"\n\n{words}" if words else ""))
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


def plain(folder: Path, name: str) -> str:
    """A plain file of the home, as its text stands, or nothing where it cannot be read."""
    try:
        return "\n".join(record.lines_in(store.within(folder, name))).strip()  # a line that is no text is passed over
    except OSError:
        return ""


if __name__ == "__main__":
    raise SystemExit(main())
