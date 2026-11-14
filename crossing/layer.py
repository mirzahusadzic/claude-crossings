"""Which model is there: for a session, as its hooks are told it, and for a call of the door's server.

Every line of the session's voice belongs to the layer of the model that made it (see store's
`persons` and `foreign`). What a frame carries, and what a stack may stand over, then depends on
which model is there now. Two plain files of the home hold what that takes, and neither says
who wrote a line: that is kept in one place alone, a message's `model` and `models.txt`.

  there.txt     the model a session runs now, as its hooks were told it: a line a change, its
                session as the archive names one, the model, and the moment in UTC. The newest
                line of a session stands, unless a message of its own is newer (see `current`).
  calling.txt   the model behind a call of `mark` through the door's server, which is told
                neither session nor model: the hook before the call writes the call's digest and
                the model, and the server takes the line of the same digest and strikes it out.

A model not known means no layering: everything is read as it was before layers. No model is
called here.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

from crossing import off, store
from crossing.record import lines_in, within

THERE = "there.txt"
CALLING = "calling.txt"
KEPT = 64  # lines of calling.txt kept: a call whose line is not taken leaves it, and the file stays small
KEY = re.compile(r"[^\s#]+")  # a model's key as models.txt can hold it: no space, and no mark that begins a note


def named(model) -> str:
    """A model's key as a hook's input gives it, or nothing where it gives none that can be kept
    (`<synthetic>` is the harness's, and no model)."""
    model = model.strip() if isinstance(model, str) else ""
    return model if KEY.fullmatch(model) and not model.startswith("<") else ""


def _lines(folder: Path, name: str) -> list[str]:
    try:
        return lines_in(within(folder, name))  # a line that is no text is passed over, and the rest read
    except OSError:
        return []


def there(folder: Path, session: str) -> tuple[str, str]:
    """The model the hooks were last told this session runs, and when; nothing where they were
    never told. A line that is not one is passed over."""
    found = ("", "")
    for line in _lines(folder, THERE):
        parts = line.split()
        if len(parts) == 3 and parts[0] == session and named(parts[1]) and off.moment(parts[2]):
            found = (parts[1], parts[2])
    return found


def arrive(folder: Path, session: str, model: str) -> None:
    """Keep that this session runs this model from now. A file that cannot be written says so."""
    fresh = not within(folder, THERE).exists()
    with open(within(folder, THERE), "a", encoding="utf-8") as handle:
        if fresh:
            handle.write("# The model each session runs, as its hooks were told it: session, model, when (UTC).\n")
        handle.write(f"{session} {model} {off.now()}\n")


def current(folder: Path, session: str) -> str:
    """The model this session runs now: the newer of what its hooks were last told (see `there`)
    and the model of its own newest message in the archive (store.spoke), where either is known.
    A harness that never says the model, or never says it changed, is read by what was said."""
    told, at = there(folder, session)
    said = store.newest(folder, session)
    model = str(said.get("model") or "")
    if not (model and told):
        return model or told
    spoken = off.moment(said.get("at"))
    return model if spoken is not None and spoken > off.moment(at) else told


def digest(name: str, given: dict) -> str:
    """A call of the door's, by its handle's name and its arguments as they were sent."""
    return hashlib.sha256(json.dumps([name, given], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[
        :16
    ]


def hand(folder: Path, name: str, given: dict, model: str) -> None:
    """Before a call of the door's server: the model behind it, for the server to take."""
    with open(within(folder, CALLING), "a", encoding="utf-8") as handle:
        handle.write(f"{digest(name, given)} {model}\n")


def handed(folder: Path, name: str, given: dict) -> str:
    """The model the hook before this call named for it, or nothing; its line is taken out, so that
    no later call is read by it. Two calls the same, from two sessions at the same moment, are the
    one case this cannot tell apart."""
    lines = _lines(folder, CALLING)
    wanted = digest(name, given)
    at = next((n for n in range(len(lines) - 1, -1, -1) if lines[n].split()[:1] == [wanted]), None)
    if at is None:
        return ""
    model = named(lines[at].split()[1] if len(lines[at].split()) == 2 else "")
    kept = (lines[:at] + lines[at + 1 :])[-KEPT:]
    fresh = within(folder, CALLING + ".new")
    fresh.write_text("".join(line + "\n" for line in kept), encoding="utf-8")
    os.replace(fresh, within(folder, CALLING))
    return model
