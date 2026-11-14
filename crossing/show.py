#!/usr/bin/env python3
"""Print what a project's cuts kept, in a few lines: the part `/context` does not show.

Usage:  python3 crossing/show.py [project directory] [--session ID]

It reads the counted records only. No model, and no text of either voice.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import record, store  # noqa: E402


def block(cwd: Path, session: str | None = None) -> str:
    cwd = cwd.resolve()  # as the home is found: a page beside the work is then named by a short path
    folder = store.kept(cwd)
    kept = []
    for path in sorted(folder.glob("*-cut-*.json")) if folder is not None else ():
        try:
            counted = json.loads(store.within(folder, path.name).read_text(encoding="utf-8"))
        except ValueError:  # a sidecar that is no text, or no JSON, is passed over
            record.passed(path)
            continue
        if session is None or counted.get("session_id", "").startswith(session):
            kept.append((path.with_suffix(".md"), counted))
    if not kept:
        return "Crossings\n  no cut on record in this project\n"
    out = ["Crossings", f"  {len(kept)} cut{'s' if len(kept) != 1 else ''} on record in this project"]
    for page, c in kept:
        person, own = c["person"], c["session"]
        none = lambda v: sum(1 for p in v["pointers"] if not p["held"])  # noqa: E731
        size = (
            f"{c['tokens_before']:,} → {c['tokens_after']:,} tokens"
            if c.get("tokens_before")
            else "size not given by the harness"
        )
        if c.get("cut_ms"):
            size += f" · the cut took {c['cut_ms'] / 1000:.0f} s"
        try:
            where = page.relative_to(cwd)
        except ValueError:
            where = page
        out += [
            "",
            f"  {c.get('counted_on', '')} · session {str(c.get('session_id', ''))[:8]}, cut {c.get('cut')} · "
            f"{store.clean(c.get('trigger') or 'trigger not given')}",
            f"    {size}",
            f"    held word for word: the person's {record.share(person['covered'], person['chars'])}"
            f" · the session's {record.share(own['covered'], own['chars'])}",
            f"    nothing held: {none(person)} of {person['messages']} messages · "
            f"{none(own)} of {own['messages']} replies",
            f"    {where}",
        ]
    return "\n".join(out) + "\n"


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    session = sys.argv[sys.argv.index("--session") + 1] if "--session" in sys.argv else None
    if session in args:
        args.remove(session)
    print(block(Path(args[0] if args else ".").resolve(), session), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
