#!/usr/bin/env python3
"""Put the anchored words themselves beside a hand-over's labels, taken from the record.

Usage:  python3 crossing/handover.py <transcript> <hand-over.md>

A label is a sentence about a stretch of the record, and a sentence about someone's
words is not their words: a summary can hold the person's words exactly where a label
only paraphrases them. So for every message id a hand-over names, this
writes what was said there, word for word, into `<hand-over>.words.md` beside it. That
file is made again from the record whenever it is needed; the record is never changed.
Only what the person wrote and what the session answered is copied, through the same
reader as everywhere else in this plugin, and only what the home beside the page still
keeps: no message struck, nothing said while Crossing was off (by its spans and by the ids
noted then), and nothing a session no person sat in held. Where the home's record of when it
was off cannot be read, or what it held cannot be told (missing, holding fewer spans, ids or places
than it did, or with a line that is no span: see store.lost), no message is given. The page
is written through `within`, for its owner alone, as every file of a home is; where a file of
it is a link, nothing is written. It is the person's to run, as the door's own verbs are, and
writes only into a home the door believes for its project: anywhere else it says so in one
sentence, and writes nothing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from crossing import transcript  # noqa: E402

MOST = 700  # characters of one message carried; the rest stays in the record, by its id
# eight hex characters standing alone; the start of a longer id, as in a session's, is not one
ID = re.compile(r"(?<![0-9a-f-])[0-9a-f]{8}(?![0-9a-f-])")


def named(hand_over: str) -> list[str]:
    """The message ids a text names, in the order it first names them.

    About one id in forty has no letter in it. Such an id counts where it stands between
    backticks, as an anchor is written; a bare number of eight digits in a sentence is a number.
    Taking every id without a letter for a number would cost a label its anchor."""
    found = []
    for match in ID.finditer(hand_over):
        ticked = hand_over[match.start() - 1 : match.start()] == "`" and hand_over[match.end() : match.end() + 1] == "`"
        if ticked or not match.group(0).isdigit():
            found.append(match.group(0))
    return list(dict.fromkeys(found))


def words(
    path: Path, ids: list[str], most: int = MOST, folder: Path | None = None
) -> tuple[list[tuple[str, str, str]], list[str]]:
    """(id, voice, what was said) for each id found, and the ids the transcript does not hold.
    With the home `folder`, an id it keeps out (see `kept_out`) is in neither list."""
    found: dict[str, tuple[str, str]] = {}
    wanted, out = set(ids), set()
    rows = list(transcript.rows(path))
    if folder is not None:
        out = kept_out(folder, path, rows)
        wanted -= out
    for _, row in rows:
        name = transcript.ident(row)
        if name not in wanted or name in found:
            continue
        his, own = transcript.person(row), transcript.session(row)
        if his or own:
            text = " ".join(his or own)
            if len(text) > most:
                text = text[:most].rstrip() + " […]"
            found[name] = ("the person" if his else "the session", text)
    return [(i, *found[i]) for i in ids if i in found], [i for i in ids if i not in found and i not in out]


def kept_out(folder: Path, path: Path, rows: list) -> set[str]:
    """The ids, by their first eight characters, of the rows of this transcript that the home
    `folder` keeps out of everything it gives: struck (by the message's id, its whole id or its
    session), said inside a span when Crossing was off (by the spans of `off.txt` and the ids
    in `unsaid.txt`), held by a session no person sat in (`unattended.txt`), or whose id is no
    name. Where the record of the spans cannot be read, or what it held cannot be told (see
    store.lost), every row is kept out."""
    from crossing import off, record, store  # here alone: the store reads this file's `named`

    every = {transcript.ident(row) for _, row in rows}
    if store.lost(folder):
        return every
    try:
        spans, _ = off.spans(folder)
    except OSError:
        return every
    gone, unsaid, unheld = store.struck(folder), off.unsaid(folder), store.unheld(folder)
    session = f"session:{path.stem[:8]}"
    out = set()
    for _, row, _, inside in off.judged(rows, spans):
        uuid = str(row.get("uuid") or "")
        if not record.nameable(uuid):
            out.add(transcript.ident(row))
        elif inside or uuid in unsaid or uuid in unheld or session in gone or uuid in gone or uuid[:8] in gone:
            out.add(uuid[:8])
    return out


def page(path: Path, hand_over: Path) -> str:
    """The words page for the hand-over page `hand_over`, from the transcript at `path`, with
    what the home the page lies in keeps out left out (see `kept_out`)."""
    from crossing import record  # here alone: the store reads this file's `named`

    kept, missing = words(path, named("\n".join(record.lines_in(hand_over))), folder=hand_over.parent)
    lines = [
        "## The anchored words, from the record",
        "",
        "Word for word, as they stand in the transcript, for each message the labels name. "
        "A message cut short ends in […]; the whole of it is in the record under its id.",
        "",
    ]
    lines += [f"- `{name}`, {voice}: {text}" for name, voice, text in kept]
    if missing:
        lines += ["", "Named by a label and not in this transcript: " + ", ".join(f"`{m}`" for m in missing) + "."]
    return "\n".join(lines) + "\n"


PERSONS = "This is the person's to run, from their own terminal, so nothing was written."
UNBELIEVED = "This page lies in no home Crossings was switched on for, so nothing was written."
LINKED = "A file of this home is a link, so nothing was written."


def believed(folder: Path) -> Path | None:
    """The home the page's folder is, where the door believes it (store.kept): a home the person's
    record names for a project, which the door finds for that project, and which this folder is, by
    the files. A project's own `crossings` that is a link is no home, and a link to a home is not the
    home: only a home named outright (CROSSING_HOME) may be one, by its own name."""
    from crossing import record, store

    for project, _ in store.consented():
        found = store.kept(Path(project))
        if found is not None and record._same(found, folder) and (not folder.is_symlink() or folder == found):
            return found
    return None


def main(argv: list[str] | None = None) -> int:
    """The helper's entry: the person's alone, as the door's own verbs are (door.personal), from
    their terminal or for the plugin's own hooks and module (`--by-hook`, `--by-module`, with the
    plugin's folder in CLAUDE_PLUGIN_ROOT); and only into a home the door believes (`believed`)."""
    from argparse import Namespace

    from crossing import door, record

    given = list(sys.argv[1:] if argv is None else argv)
    flags = {each for each in given if each in ("--by-hook", "--by-module")}
    named_ = [each for each in given if each not in flags]
    if len(named_) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    record.private()  # the words page is its owner's alone, as every file of a home is
    if not door.personal(Namespace(by_hook="--by-hook" in flags, by_module="--by-module" in flags)):
        print(PERSONS, file=sys.stderr)
        return 1
    source, hand_over = Path(named_[0]), Path(named_[1])
    try:
        folder = believed(hand_over.parent)
        if folder is None:
            print(UNBELIEVED, file=sys.stderr)
            return 1
        record.sound(folder)  # a link anywhere in the home, and nothing is read or written
        out = record.within(folder, hand_over.with_suffix(".words.md").name)
        out.write_text(page(source, record.within(folder, hand_over.name)), encoding="utf-8")
    except record.Linked as err:
        record.refused(err)
        print(LINKED, file=sys.stderr)
        return 1
    print(hand_over.parent / out.name)  # by the path it was named by: the same folder, by the files
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
