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

ODD = "  A cut's record could not be read, so it was passed over: {}"


def _number(value) -> bool:
    """A figure as a count writes it: a number, and no truth value."""
    return type(value) in (int, float)


def _voice(v) -> bool:
    """Whether one voice of a cut's record has the shape the count writes."""
    return (
        isinstance(v, dict)
        and all(_number(v.get(name)) for name in ("covered", "chars", "messages"))
        and isinstance(v.get("pointers"), list)
        and all(isinstance(p, dict) and _number(p.get("held")) for p in v["pointers"])
    )


def _lines(c: dict, page: Path, cwd: Path) -> list[str]:
    """The lines of one cut's record. A record of any other shape than the count writes (no object, a
    voice without its figures, a figure that is no number) raises ValueError, and is passed over."""
    person, own = c.get("person"), c.get("session")
    before, after, took = (c.get(name) for name in ("tokens_before", "tokens_after", "cut_ms"))
    if not (_voice(person) and _voice(own)) or any(v is not None and not _number(v) for v in (before, after, took)):
        raise ValueError("a cut's record of another shape")
    none = lambda v: sum(1 for p in v["pointers"] if not p["held"])  # noqa: E731
    size = "size not given by the harness"
    if before:
        size = f"{before:,} → {after:,} tokens" if after is not None else f"{before:,} tokens before"
    if took:
        size += f" · the cut took {took / 1000:.0f} s"
    try:
        where = page.relative_to(cwd)
    except ValueError:
        where = page
    clean = store.clean  # a sidecar a hand or a repository wrote is shown by the one cleaning rule
    return [
        "",
        f"  {clean(c.get('counted_on', ''))} · session {clean(str(c.get('session_id', '')))[:8]}, "
        f"cut {clean(c.get('cut'))} · {clean(c.get('trigger') or 'trigger not given')}",
        f"    {size}",
        f"    held word for word: the person's {record.share(person['covered'], person['chars'])}"
        f" · the session's {record.share(own['covered'], own['chars'])}",
        f"    nothing held: {none(person)} of {record.many(person['messages'], 'message')} · "
        f"{none(own)} of {record.many(own['messages'], 'reply', 'replies')}",
        f"    {clean(where)}",
    ]


def block(cwd: Path, session: str | None = None) -> str:
    """The cuts on record in the project at `cwd`, of one session where it is named. A cut's record
    that cannot be read, or is of another shape than the count writes, is passed over with one line
    that names its file, and the others are shown."""
    cwd = cwd.resolve()  # as the home is found: a page beside the work is then named by a short path
    folder = store.kept(cwd)
    shown, odd = [], []
    for path in sorted(folder.glob("*-cut-*.json")) if folder is not None else ():
        try:
            counted = json.loads(store.within(folder, path.name).read_text(encoding="utf-8"))
        except ValueError:  # a sidecar that is no text, or no JSON
            record.passed(path)
            counted = None
        except OSError:  # one that cannot be opened
            counted = None
        except record.Linked as err:  # one that is a link: nothing is read through it
            record.refused(err)
            counted = None
        if isinstance(counted, dict) and (session is None or str(counted.get("session_id", "")).startswith(session)):
            try:
                shown.append(_lines(counted, path.with_suffix(".md"), cwd))
            except ValueError:
                odd.append(path.name)
        elif not isinstance(counted, dict) and (session is None or path.name.startswith(session[:8])):
            odd.append(path.name)  # whose it is cannot be told but by its name
    if not shown and not odd:
        return "Crossings\n  no cut on record in this project\n"
    count = len(shown)
    out = ["Crossings", f"  {count or 'no'} cut{'' if count <= 1 else 's'} on record in this project"]
    out += [ODD.format(store.clean(name)) for name in odd]
    for lines in shown:
        out += lines
    return "\n".join(out) + "\n"


def main() -> int:
    record.private()  # every folder and file it makes is its owner's alone, its log's among them
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    session = sys.argv[sys.argv.index("--session") + 1] if "--session" in sys.argv else None
    if session in args:
        args.remove(session)
    print(block(Path(args[0] if args else ".").resolve(), session), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
