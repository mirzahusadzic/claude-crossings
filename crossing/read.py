#!/usr/bin/env python3
"""Show what was said on given lines of a transcript, and nothing else.

Usage:  python3 crossing/read.py <transcript> <id or line> [<id or line> ...]

A transcript row can also hold a session's reasoning block, tool traffic and harness
notes. None of that is printed: only the person's words or the session's reply.
A message is named by the start of its id (eight characters are enough), which stays the
same when a fork or a resume writes a new file; a line number holds for one file only. \
This is the way to read a message back; the file itself is not opened raw.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import transcript  # noqa: E402

MOST = 20  # lines a call; reading a whole exchange back is not what this is for


def said(path: Path, lines: set[int], ids: set[str] = frozenset()) -> list[str]:
    out = []
    for line, row in transcript.rows(path):
        name = transcript.ident(row)
        if line not in lines and not any(name and name.startswith(i) for i in ids):
            continue
        his, own = transcript.person(row), transcript.session(row)
        where = f"{name or 'no id'} (line {line})"
        if his:
            out += [f"{where}, the person: {text}" for text in his]
        elif own:
            out += [f"{where}, the session: {text}" for text in own]
        else:
            out.append(f"{where}: nothing was said here")
    return out


def main() -> int:
    wanted = [a.lower() for a in sys.argv[2:]]
    if len(sys.argv) < 3 or not all(len(a) >= 1 and all(c in "0123456789abcdef-" for c in a) for a in wanted):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    if len(wanted) > MOST:
        print(f"at most {MOST} messages a call", file=sys.stderr)
        return 2
    # A short run of digits is a line of this file; anything longer is the start of an id.
    lines = {int(a) for a in wanted if a.isdigit() and len(a) <= 6}
    ids = {a for a in wanted if not (a.isdigit() and len(a) <= 6)}
    found = said(Path(sys.argv[1]), lines, ids)
    print("\n".join(found) if found else "no such message in this transcript")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
