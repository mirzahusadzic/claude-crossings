#!/usr/bin/env python3
"""Show what was said on given lines of a transcript, and nothing else.

Usage:  python3 crossing/read.py <transcript> <id or line> [<id or line> ...] [--cwd DIR]

A transcript row can also hold a session's reasoning block, tool traffic and harness
notes. None of that is printed: only the person's words or the session's reply.
A message is named by the start of its id (eight characters are enough), which stays the
same when a fork or a resume writes a new file; a line number holds for one file only. \
An id whose start names more than one row gives none of them, and says so. Where the person
switched Crossings on for the project (--cwd, default: here), nothing its home keeps out is
shown: a message struck, said while Crossings was off, or held by a session no person sat in.
It is the person's to run, from their own terminal, as the door's own verbs are.
This is the way to read a message back; the file itself is not opened raw.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import transcript  # noqa: E402

MOST = 20  # lines a call; reading a whole exchange back is not what this is for
PERSONS = "This is the person's to run, from their own terminal, so nothing was shown."
LINKED = "A file of this project's home is a link, so nothing was shown."


def said(path: Path, lines: set[int], ids: set[str] = frozenset(), out: set[str] = frozenset()) -> list[str]:
    """What was said on these lines of the transcript, and on the row each id's start names, in the
    file's order; an id whose start names more than one row gives none of them, and a line after the
    rest says so. A row whose id is among `out` (by its first eight characters: what the home keeps
    out, see handover.kept_out) is said to be kept out, and nothing of it is shown."""
    rows = list(transcript.rows(path))
    named = {i: [line for line, row in rows if str(row.get("uuid") or "").startswith(i)] for i in ids}
    wanted = set(lines) | {found[0] for found in named.values() if len(found) == 1}
    shown = []
    for line, row in rows:
        if line not in wanted:
            continue
        name = transcript.ident(row)
        where = f"{name or 'no id'} (line {line})"
        if name in out:
            shown.append(f"{where}: the home keeps this out, so nothing of it is shown")
            continue
        his, own = transcript.person(row), transcript.session(row)
        if his:
            shown += [f"{where}, the person: {text}" for text in his]
        elif own:
            shown += [f"{where}, the session: {text}" for text in own]
        else:
            shown.append(f"{where}: nothing was said here")
    return shown + [
        f"{i}: names {len(found)} messages in this transcript; name more of its id"
        for i, found in named.items()
        if len(found) > 1
    ]


def kept_out(path: Path, cwd: Path) -> set[str]:
    """What the home the door believes for the project `cwd` stands in keeps out of the rows of this
    transcript (see handover.kept_out); nothing where there is no such home. A home with a link below
    it is refused whole (record.Linked)."""
    from crossing import handover, record, store

    folder = store.kept(cwd)
    if folder is None:
        return set()
    record.sound(folder)  # a home with a link anywhere below it is refused whole, before anything of it is read
    return handover.kept_out(folder, path, list(transcript.rows(path)))


def main(argv: list[str] | None = None) -> int:
    """The reader's entry: the person's alone, as the door's own verbs are (door.personal), from their
    terminal or for the plugin's own hooks and module (`--by-hook`, `--by-module`, with the plugin's
    folder in CLAUDE_PLUGIN_ROOT)."""
    from argparse import Namespace

    from crossing import door

    given = list(sys.argv[1:] if argv is None else argv)
    flags = {each for each in given if each in ("--by-hook", "--by-module")}
    given = [each for each in given if each not in flags]
    cwd = Path(".")
    if "--cwd" in given:
        at = given.index("--cwd")
        cwd, given = Path(given[at + 1] if at + 1 < len(given) else "."), given[:at] + given[at + 2 :]
    wanted = [a.lower() for a in given[1:]]
    if len(given) < 2 or not all(len(a) >= 1 and all(c in "0123456789abcdef-" for c in a) for a in wanted):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if len(wanted) > MOST:
        print(f"at most {MOST} messages a call", file=sys.stderr)
        return 2
    if not door.personal(Namespace(by_hook="--by-hook" in flags, by_module="--by-module" in flags)):
        print(PERSONS, file=sys.stderr)
        return 1
    path = Path(given[0])
    # A short run of digits is a line of this file; anything longer is the start of an id.
    lines = {int(a) for a in wanted if a.isdigit() and len(a) <= 6}
    ids = {a for a in wanted if not (a.isdigit() and len(a) <= 6)}
    from crossing import record

    try:
        found = said(path, lines, ids, kept_out(path, cwd.resolve()))
    except record.Linked as err:  # a link in the home: nothing of it is read
        record.refused(err)
        print(LINKED, file=sys.stderr)
        return 1
    print("\n".join(found) if found else "no such message in this transcript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
