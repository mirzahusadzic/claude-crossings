"""The index is added to, not made again: what an archive keeps is added to the database where
nothing else of the home changed, and the database so reached is the one a whole build makes
from the same plain files, table by table and row by row. Every other case is made whole. No
model, no network; every transcript is made up here.

Run with pytest, or without it:  python3 tests/test_index.py
"""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_edges import set_to, through  # noqa: E402
from test_store import in_person, sweep, switched_on  # noqa: E402  (and its data folder: no test reaches the real home)

from crossing import hook, off, store  # noqa: E402

WORDS = ("hull", "mast", "tern", "mooring", "sail", "keel", "tide", "rope", "grey", "spring", "anchor", "deck")


def at(second: int) -> str:
    """A made-up moment of a made-up day, `second` seconds after its start."""
    return f"2026-03-01T{second // 3600:02d}:{second // 60 % 60:02d}:{second % 60:02d}.000Z"


def spoken(n: int, when: str, voice: str = "user", text: str = "", model: str = "") -> dict:
    """A made-up row of a transcript, its id made from `n`: the person's, or the session's."""
    text = text or f"Made-up line {n} about the {WORDS[n % len(WORDS)]} and the {WORDS[n * 7 % len(WORDS)]}."
    message = {"role": voice, "content": text if voice == "user" else [{"type": "text", "text": text}]}
    if model:
        message["model"] = model
    return {"type": voice, "uuid": f"{n:08x}-0000-4000-8000-000000000000", "timestamp": when, "message": message}


def some(first: int, count: int, start: int) -> list[dict]:
    """Rows of both voices, a pasted text among them, one a second from `start` on."""
    rows = []
    for k, n in enumerate(range(first, first + count)):
        if n % 5 == 3:
            rows.append(
                spoken(
                    n,
                    at(start + k),
                    text=f'Look at this, line {n}: <pasted_content id="1">A pasted '
                    f"text {n} about the {WORDS[n % len(WORDS)]}.</pasted_content>",
                )
            )
        else:
            rows.append(
                spoken(n, at(start + k), "user" if n % 2 else "assistant", model="made-up-model" if n % 4 == 0 else "")
            )
    return rows


def append(path: Path, rows: list[dict]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write("".join(json.dumps(r) + "\n" for r in rows))


def started(tmp_path: Path, count: int = 30) -> tuple[Path, Path, Path]:
    """A project switched on, with a transcript of `count` messages archived and indexed whole."""
    project = tmp_path / "project"
    (project / "crossings").mkdir(parents=True)
    switched_on(project)
    crossings, path = project / "crossings", tmp_path / "abcdef01-0101.jsonl"
    append(path, some(1, count, 0))
    assert store.archive(path, crossings) == count
    assert store.refresh(crossings) is False  # no database yet: made whole
    return project, crossings, path


TABLES = {
    "said": "select * from said order by seq",
    "said_fts": "select rowid, text from said_fts order by rowid",
    "label": "select * from label order by n",
    "label_fts": "select rowid, text from label_fts order by rowid",
    "anchor": "select rowid, * from anchor order by rowid",
    "beneath": "select rowid, * from beneath order by rowid",
    "word": "select * from word order by term",
    "unread": "select * from unread",
    "source": "select * from source order by name",
    "ordered": "select * from ordered",
}


def dump(made: Path) -> dict:
    """A database, table by table and row by row in a stable order, its schema and make, and what
    its full-text search answers to a set of queries, with their ranks."""
    db = sqlite3.connect(made)
    out = {
        "schema": db.execute("select type, name, tbl_name, sql from sqlite_master order by type, name").fetchall(),
        "make": db.execute("pragma user_version").fetchone()[0],
    }
    for name, sql in TABLES.items():
        out[name] = db.execute(sql).fetchall()
    for query in (*WORDS, "hul*", "made", '"made up line"', "pasted text", "line OR tern", "painted", "zzz"):
        out[f"said? {query}"] = db.execute(
            "select rowid, round(bm25(said_fts), 9) from said_fts where said_fts match ? order by rowid", (query,)
        ).fetchall()
        out[f"label? {query}"] = db.execute(
            "select rowid from label_fts where label_fts match ? order by rowid", (query,)
        ).fetchall()
    db.execute(
        "insert into said_fts(said_fts) values ('integrity-check')"
    )  # raises where the full-text index is unsound
    db.close()
    return out


def shown(project: Path, ids: list[str]) -> list[str]:
    """What the door says, from a shell, to status, look, labels, find and thread."""
    # status bare: the person's own says some things once (labels that arrived, ids shared), and is asked twice here
    asked = [
        ["status", "--bare"],
        ["look"],
        ["labels"],
        ["find", "hull"],
        ["find", "mooring", "tern"],
        ["find", "pasted"],
        ["find", "hul*"],
        ["find", "hulk"],
        ["find", "--voice", "his", "keel"],
    ] + [["thread", each] for each in ids]
    return [through(*argv, "--cwd", str(project))[1] for argv in asked]


def same_as_whole(project: Path, crossings: Path, ids: list[str]) -> None:
    """The database as it now stands is the one a build makes whole from the same plain files, and
    the door says the same of both."""
    told = (store.ARRIVED, store.COLLIDED)  # what the person's status, in `shown`, takes away once it is said
    plain = {
        p: p.read_bytes()
        for p in sorted(crossings.rglob("*"))
        if p.is_file() and "store.db" not in p.name and p.name not in told
    }
    reached, said = dump(crossings / "store.db"), shown(project, ids)
    store.build(crossings)
    assert {p: p.read_bytes() for p in plain} == plain  # a build reads the plain files and writes none
    whole = dump(crossings / "store.db")
    for name in whole:
        assert reached[name] == whole[name], name
    assert reached == whole and shown(project, ids) == said


def kept(crossings: Path, path: Path, expected: int) -> bool:
    """Archive the transcript as a hook does, and bring the index up to it: whether it was added to."""
    assert store.archive(path, crossings) == expected
    return store.refresh(crossings)


def ids(*numbers: int) -> list[str]:
    return [f"{n:08x}" for n in numbers]


# --- equality ----------------------------------------------------------------------------------------


def test_additions_in_several_steps_give_the_database_a_whole_build_gives(tmp_path):
    project, crossings, path = started(tmp_path)
    page = crossings / "said" / "abcdef01.jsonl"
    with open(page, "a", encoding="utf-8") as handle:  # an older make kept a message twice
        handle.write(page.read_text(encoding="utf-8").splitlines()[4] + "\n")
    store.build(crossings)
    assert store.status(crossings)["his"] + store.status(crossings)["session"] == 30
    looked = ids(1, 3, 5, 30, 31, 44, 63)
    same_as_whole(project, crossings, looked)
    built = (crossings / "store.db").stat().st_ino
    for step in range(3):  # both voices, pasted texts, the models of the session's
        append(path, some(31 + 10 * step, 10, 100 + 20 * step))
        assert kept(crossings, path, 10) is True
        assert (crossings / "store.db").stat().st_ino == built  # added to in its place, not made again
        same_as_whole(project, crossings, looked)
        built = (crossings / "store.db").stat().st_ino
    other = tmp_path / "fedcba98-0202.jsonl"  # another session: a page of the archive the index never read
    append(other, some(61, 6, 400))
    assert kept(crossings, other, 6) is True
    same_as_whole(project, crossings, looked)
    assert store.status(crossings)["pasted"] == sum(1 for n in range(1, 67) if n % 5 == 3)
    assert store.known(crossings) == ["made-up-model"]
    append(path, [spoken(80, at(500), text="One more line about the deck.")])
    with open(page, "a", encoding="utf-8") as handle:
        handle.write("not a line of the archive\n\n")  # passed over by a build, and by an addition alike
    assert kept(crossings, path, 1) is True
    assert store.status(crossings)["unread"] == 1
    same_as_whole(project, crossings, looked)


def test_what_is_said_off_the_record_is_kept_neither_way(tmp_path):
    project, crossings, path = started(tmp_path, 10)
    assert store.switch(project, "off") == "off"
    time.sleep(0.01)
    unsaid = off.now()
    append(path, [spoken(90, unsaid, text="Said off the record, about the zeppelin."), spoken(91, unsaid, "assistant")])
    time.sleep(0.01)
    assert store.switch(project, "on") == "again"
    assert store.archive(path, crossings) == 0  # nothing of it is kept
    time.sleep(0.01)
    append(path, [spoken(92, off.now()), spoken(93, off.now(), "assistant")])
    assert kept(crossings, path, 2) is True  # the index was made anew as it was switched on, with off.txt as it is
    append(path, [spoken(94, off.now())])
    assert kept(crossings, path, 1) is True
    same_as_whole(project, crossings, ids(1, 92, 94))
    assert "Nothing in the store holds these words" in through("find", "zeppelin", "--cwd", str(project))[1]
    assert not any(r["id"] in ids(90, 91) for r in store._archived(crossings))


def test_a_strike_between_two_additions_is_made_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    assert store.strike(crossings, ids(4)[0])["struck"]  # a strike makes it whole itself
    append(path, some(31, 5, 100))
    assert kept(crossings, path, 5) is True
    same_as_whole(project, crossings, ids(3, 5, 31))
    with open(
        crossings / "said" / "abcdef01.jsonl", "a", encoding="utf-8"
    ) as handle:  # what was struck, back by an older make
        handle.write(
            json.dumps(
                {
                    "uuid": f"{4:08x}-0000-4000-8000-000000000000",
                    "id": ids(4)[0],
                    "session": "abcdef01",
                    "voice": "his",
                    "at": at(150),
                    "text": "Back again.",
                }
            )
            + "\n"
        )
    assert store.refresh(crossings) is True and ids(4)[0] not in through("thread", ids(5)[0], "--cwd", str(project))[1]
    same_as_whole(project, crossings, ids(3, 5, 31))
    with open(crossings / "struck.txt", "a", encoding="utf-8") as handle:
        handle.write(ids(6)[0] + "\n")  # struck by hand: the line stays in the archive, and the index leaves it
    append(path, some(36, 5, 200))
    assert kept(crossings, path, 5) is False
    assert ids(6)[0] not in [r[0] for r in sqlite3.connect(crossings / "store.db").execute("select id from said")]
    same_as_whole(project, crossings, ids(5, 7, 36))
    # A struck line still in the archive: an archive asks the pages themselves what is held.
    reads, was = [], store._archived
    store._archived = lambda folder: reads.append(folder) or was(folder)
    try:
        append(path, some(41, 2, 300))
        assert kept(crossings, path, 2) is True and len(reads) == 1
    finally:
        store._archived = was
    same_as_whole(project, crossings, ids(7, 41))


def test_a_label_marked_or_changed_between_two_additions_is_made_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    assert store.mark(crossings, "work", "both", "The hull is grey.", ids(1, 2), model="made-up-model")["written"]
    append(path, some(31, 4, 100))
    assert kept(crossings, path, 4) is True  # the mark made it whole, with its page and its model in the record
    same_as_whole(project, crossings, ids(1, 31))
    label_page = next((crossings / "labels").glob("*.md"))
    with open(label_page, "a", encoding="utf-8") as handle:
        handle.write(f"| W2 | Written by hand. | both | `{ids(3)[0]}` |\n")
    append(path, some(35, 4, 200))
    assert kept(crossings, path, 4) is False
    same_as_whole(project, crossings, ids(3, 35))
    # A label signed after it was marked: models.txt changed, and the index with it, record and all (S13), so
    # what is archived next is added, and the database is still the one a whole build makes.
    assert store.sign(crossings, "W2", "Written by hand.", "made-up-model")
    append(path, some(39, 2, 300))
    assert kept(crossings, path, 2) is True
    same_as_whole(project, crossings, ids(3, 39))
    # A label resting on a message the archive does not hold yet: once it comes, the label's state changes.
    with open(label_page, "a", encoding="utf-8") as handle:
        handle.write(f"| W3 | Resting on what is to come. | both | `{ids(50)[0]}` |\n")
    store.build(crossings)
    assert store.status(crossings)["states"]["unresolved"] == 1
    append(path, [spoken(50, at(400)), spoken(51, at(401), "assistant")])
    assert kept(crossings, path, 2) is False
    assert store.status(crossings)["states"]["unresolved"] == 0
    same_as_whole(project, crossings, ids(50))


def test_a_message_earlier_than_the_newest_held_is_made_whole(tmp_path):
    """The database numbers every message in the order of its time: one that comes later and
    stands earlier would be numbered after what it stands before, so it is made whole."""
    project, crossings, path = started(tmp_path)
    append(path, [spoken(70, at(5)), spoken(71, at(6), "assistant")])  # earlier than what is there
    assert kept(crossings, path, 2) is False
    assert [r["id"] for r in store.thread(crossings, ids(70)[0], around=1)["said"]] == ids(
        6, 70, 7
    )  # in the order of time
    same_as_whole(project, crossings, ids(70))
    append(path, [spoken(72, "")])  # no time at all stands first
    assert kept(crossings, path, 1) is False
    same_as_whole(project, crossings, ids(72))
    append(path, [spoken(73, at(900)), spoken(74, at(900))])  # one moment for two: in the order of their lines
    assert kept(crossings, path, 2) is True
    append(path, [spoken(75, at(900))])  # the same moment, the same session, a later line: still after
    assert kept(crossings, path, 1) is True
    same_as_whole(project, crossings, ids(73, 75))


def test_a_message_kept_twice_since_the_index_was_made_is_made_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    page = crossings / "said" / "abcdef01.jsonl"
    twice = page.read_text(encoding="utf-8").splitlines()[2]
    elsewhere = crossings / "said" / "aaaaaaaa.jsonl"  # by an older make, on a page before the first
    elsewhere.write_text(
        json.dumps({**json.loads(twice), "text": "The same id, another text."}) + "\n", encoding="utf-8"
    )
    append(path, some(31, 2, 100))
    assert kept(crossings, path, 2) is False
    same_as_whole(project, crossings, ids(3, 31))


def test_every_page_changed_by_any_other_way_is_made_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    page = crossings / "said" / "abcdef01.jsonl"
    assert store.layered(crossings, "made-up-model")[1] > 0  # each page written again whole, and made whole
    append(path, some(31, 2, 100))
    assert kept(crossings, path, 2) is True
    whole = page.read_bytes()
    # The same size, written again: changed in place.
    page.write_bytes(whole.replace(b"Made-up line 1 ", b"Made-up line X "))
    append(path, some(33, 1, 200))
    assert kept(crossings, path, 1) is False
    same_as_whole(project, crossings, ids(1, 33))
    # Grown, and what stood just before its old end is not what was read.
    data = page.read_bytes()
    last = data.rindex(b"Made-up")
    page.write_bytes(data[:last] + b"Made-UP" + data[last + 7 :] + b"\n")
    assert store.refresh(crossings) is False
    # Older than the index's record of it.
    append(path, some(34, 1, 300))
    assert kept(crossings, path, 1) is True
    os.utime(page, ns=(10**9,) * 2)
    assert store.refresh(crossings) is False
    # A page whose last line was left unended, then grown.
    page.write_bytes(page.read_bytes() + b'{"half": ')
    store.build(crossings)
    page.write_bytes(page.read_bytes() + b"1}\n")
    assert store.refresh(crossings) is False
    # A page gone.
    other = tmp_path / "fedcba98-0202.jsonl"
    append(other, some(61, 2, 400))
    assert kept(crossings, other, 2) is True
    (crossings / "said" / "fedcba98.jsonl").unlink()
    assert store.refresh(crossings) is False
    same_as_whole(project, crossings, ids(34))
    # Shorter than its record.
    page.write_bytes(b"".join(page.read_bytes().splitlines(keepends=True)[:-2]))
    assert store.refresh(crossings) is False
    same_as_whole(project, crossings, ids(1))


def test_a_database_that_cannot_be_trusted_is_made_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    made = crossings / "store.db"
    db = sqlite3.connect(made)
    db.execute("pragma user_version = 3")  # another make
    db.commit()
    db.close()
    append(path, some(31, 2, 100))
    assert kept(crossings, path, 2) is False and dump(made)["make"] == store.MADE
    db = sqlite3.connect(made)
    db.execute("drop table source")  # made by a make that kept no record of its plain files
    db.commit()
    db.close()
    append(path, some(33, 2, 200))
    assert kept(crossings, path, 2) is False and dump(made)["source"]
    made.write_text("this is not a database", encoding="utf-8")
    append(path, some(35, 2, 300))
    assert kept(crossings, path, 2) is False  # an archive asked the pages, and the index was made whole
    made.unlink()
    append(path, some(37, 2, 400))
    assert kept(crossings, path, 2) is False and made.exists()
    same_as_whole(project, crossings, ids(37))


def test_an_addition_that_fails_or_finds_another_database_in_its_place_is_made_whole(tmp_path):
    project, crossings, path = started(tmp_path)
    was, failed = store._said_row, []

    def failing(db, seq, row):  # the addition fails once, halfway through; the whole build after it does not
        if seq > 31 and not failed:
            failed.append(seq)
            raise sqlite3.IntegrityError("made to fail here")
        was(db, seq, row)

    store._said_row = failing
    try:
        append(path, some(31, 3, 100))
        built = (crossings / "store.db").stat().st_ino
        assert kept(crossings, path, 3) is False and failed
        assert (crossings / "store.db").stat().st_ino != built  # made whole in its place
    finally:
        store._said_row = was
    same_as_whole(project, crossings, ids(31, 33))
    # A build that puts another database in the place of the one being added to, as it is opened.
    made, connect = crossings / "store.db", store.sqlite3.connect
    spare = tmp_path / "spare.db"
    shutil.copyfile(made, spare)

    def replacing(name, *args, **kwargs):
        db = connect(name, *args, **kwargs)
        if str(name) == str(made) and spare.exists():  # once
            os.replace(spare, made)
        return db

    append(path, some(34, 2, 200))
    assert store.archive(path, crossings) == 2
    store.sqlite3.connect = replacing
    try:
        assert store.refresh(crossings) is False
    finally:
        store.sqlite3.connect = connect
    same_as_whole(project, crossings, ids(34))


def test_a_whole_build_waits_for_an_addition_and_takes_its_place_after_it(tmp_path):
    project, crossings, path = started(tmp_path)
    made = crossings / "store.db"
    holding = sqlite3.connect(made)
    holding.execute("begin immediate")  # an addition under way
    holding.execute("insert into unread values (99)")
    assert (crossings / "store.db-journal").exists()
    before, store.WAIT = store.WAIT, 0.2
    try:
        start = time.monotonic()
        store.build(crossings)  # waited for it, as long as WAIT, and then put in its place all the same
        assert time.monotonic() - start >= 0.2
    finally:
        store.WAIT = before
        holding.rollback()
        holding.close()
    assert dump(made)["unread"] == [(0,)]
    same_as_whole(project, crossings, ids(1))


def test_a_whole_build_put_in_place_once_the_addition_under_way_is_done(tmp_path):
    project, crossings, path = started(tmp_path)
    made = crossings / "store.db"
    holding = sqlite3.connect(made, check_same_thread=False)
    holding.execute("begin immediate")
    holding.execute("insert into unread values (99)")
    done = []
    later = threading.Timer(0.3, lambda: (done.append(time.monotonic()), holding.commit(), holding.close()))
    later.start()
    store.build(crossings)
    later.join()
    assert done and time.monotonic() >= done[0] and dump(made)["unread"] == [(0,)]  # after it, and whole
    same_as_whole(project, crossings, ids(1))


def test_door_build_always_makes_it_whole_and_the_hooks_add(tmp_path):
    project, crossings, path = started(tmp_path)
    made = crossings / "store.db"
    append(path, some(31, 2, 100))
    built = made.stat().st_ino
    assert through("build", "--transcript", str(path), "--cwd", str(project))[0] == 0
    assert made.stat().st_ino != built  # made again, though only additions were new
    built = made.stat().st_ino
    assert through("build", "--cwd", str(project))[0] == 0 and made.stat().st_ino != built
    append(path, some(33, 2, 200))
    built = made.stat().st_ino
    assert "Newly archived: 2." in through("status", "--transcript", str(path), "--cwd", str(project))[1]
    assert made.stat().st_ino == built  # added to in its place
    same_as_whole(project, crossings, ids(33))
    event = {
        "hook_event_name": "PreToolUse",
        "tool_name": "mcp__plugin_crossing_door__find",
        "transcript_path": str(path),
        "cwd": str(project),
        "session_id": "abcdef01-0101",
    }
    append(path, some(35, 2, 300))
    built = made.stat().st_ino
    in_person(lambda _: hook.run(event))(tmp_path)
    assert made.stat().st_ino == built and store.status(crossings)["his"] + store.status(crossings)["session"] == 36
    with set_to(CROSSING_WAIT="1"):
        append(path, some(37, 2, 400))
        in_person(lambda _: hook.run({**event, "hook_event_name": "SessionEnd"}))(tmp_path)  # reads it whole, and adds
    assert made.stat().st_ino == built and store.status(crossings)["his"] + store.status(crossings)["session"] == 38
    same_as_whole(project, crossings, ids(37))


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
