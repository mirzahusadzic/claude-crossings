"""What an independent review of the store found, each with the test that holds it: a struck
session that stays struck in a transcript of any name, a byte that is no text and stops nothing,
a project's `crossings` that is a link, the frame and the hand-over kept from a session no person
sits in, a frame that stays within its most, one folder by either spelling of its letters, a cut
counted while the record of the spans is lost, keys taken from the pages under the lock, a strike
and `layer` that hold the lock and put each file in its place whole, a clock set back while
Crossings was off, labels that arrive with no mark, one lock for the person's record, ids of eight
characters that two messages share, and a subagent's rows. No model, no network, and nothing of
the person's: the Keychain is a stand-in.

Run with pytest, or without it:  python3 tests/test_review.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tests"))

from test_checks import NOT_ON, ON, shell  # noqa: E402
from test_count import BEFORE, SUMMARY, written  # noqa: E402
from test_edges import as_the_module, set_to, through, words_script  # noqa: E402
from test_homes import public  # noqa: E402
from test_off import says  # noqa: E402
from test_store import A, B, D, E, home, row, started_by, sweep, switched_on  # noqa: E402  (and its data folder)

from crossing import door, frame, handover, hook, off, record, show, store  # noqa: E402

WHOLE = "-0000-4000-8000-000000000000"  # what follows the first eight characters of a made-up message's id
# What the door says, as the person reads it: written out here, so that the words are held too.
LINKED_HOME = (
    "This project's crossings folder is a link to {}, so Crossings was not switched on: a home is a folder of "
    "its own.\n"
)
UNSEATED = (
    "The frame and the hand-over are for sessions a person sits in, and this one is not, so nothing was carried.\n"
)
TOO_LONG = "a label is one sentence, and this one is longer than 4,000 characters"
DAMAGED = "A file of this home holds a line that cannot be read as text, and it is passed over wherever it is read: {}."
ARRIVED = "A label came into this home's pages without a mark through the door, and crosses every cut as any other: {}."
COLLIDED = "Two messages of this home share the id {0}: thread {0} names both, and a strike takes one by its whole id."
UNTOLD = (
    "The record of when Crossings was off in this project is missing, shorter than it was, or holds a line that "
    "cannot be read as a span, so what was said off the record cannot be told from the rest, and nothing said is "
    "listed here."
)


def ids(folder: Path) -> list[str]:
    return [said["id"] for said in store._archived(folder)]


def words_page(crossings: Path) -> str:
    return (crossings / "hand-over.words.md").read_text(encoding="utf-8")


# --- 1: a struck session, through a fork or a resume ------------------------------------------------


def test_a_struck_session_stays_struck_in_a_transcript_of_any_name(tmp_path):
    crossings, path = home(tmp_path)
    project = str(crossings.parent)
    assert through("strike", "session:session-0001", "--cwd", project)[0] == 0
    assert ids(crossings) == []
    fork = (
        tmp_path / "forked-0002.jsonl"
    )  # a fork or a resume: the same rows, under the same ids, in a file of another name
    fork.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    assert store.archive(fork, crossings, whole=True) == 0 and ids(crossings) == []
    store.build(crossings)
    db = store._open(crossings)
    assert db.execute("select count(*) from said").fetchone()[0] == 0
    db.close()
    assert words_script(str(fork), str(crossings / "hand-over.md")).returncode == 0
    for gone in ("Tern", "hull", "Grey", A, B, D, E):
        assert f"`{gone}`, the" not in words_page(crossings) and "Tern" not in words_page(crossings), gone
    (crossings / "hand-over.words.md").write_text(f"- `{B}`, the session: Noted: Tern.\n", encoding="utf-8")
    shown = as_the_module("page", "--cwd", project, CLAUDE_CODE_ENTRYPOINT="cli")
    assert shown.returncode == 0 and "Noted: Tern" not in shown.stdout


# --- 2: one byte that is no text --------------------------------------------------------------------


def test_a_line_that_is_no_text_is_passed_over_and_the_persons_status_says_so_once(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    page = crossings / "said" / "session-.jsonl"
    with open(page, "ab") as handle:  # a page that ends inside a character of two bytes
        handle.write('{"uuid": "cut-short", "text": "caf'.encode("utf-8") + "é".encode("utf-8")[:1])
    later = tmp_path / "session-0003.jsonl"  # the same page: what is appended after the cut-short line is read whole
    later.write_text(json.dumps(row("user", "12345678", 9, "Said after the damage.")) + "\n", encoding="utf-8")
    assert store.archive(later, crossings) == 1  # archiving goes on
    assert "12345678" in ids(crossings) and A in ids(crossings)
    store.build(crossings)
    assert through("look", "--cwd", project)[0] == 0
    code, out = through("thread", "12345678", "--cwd", project)
    assert code == 0 and "Said after the damage." in out
    # One byte that is no text in what was struck: the token on that line still strikes.
    (crossings / "struck.txt").write_bytes(f"{A}  # a reason, cut short ".encode("utf-8") + b"\xe9\n\xff\xfe\n")
    store.build(crossings)
    assert through("look", "--cwd", project)[0] == 0
    assert through("thread", A, "--cwd", project) == (0, f"thread of `{A}`: no such message in the store.\n")
    told = through("status", "--cwd", project)[1]
    assert DAMAGED.format("said/session-.jsonl, struck.txt") in told, told
    assert "cannot be read as text" not in through("status", "--cwd", project)[1]  # once
    assert "cannot be read as text" not in shell("status", "--bare", "--cwd", project)[1]
    (crossings / "labels").mkdir()  # a label page with such a line, read by the hooks too
    (crossings / "labels" / "2026-11-12.md").write_bytes(
        b"| W7 | A label \xff. | session | `"
        + D.encode()
        + b"` |\n"
        + f"| W8 | Read as it was. | session | `{D}` |\n".encode()
    )
    assert [label["id"] for label in store.labels(crossings)] == ["R1", "W1", "W8"]
    (crossings / "abcdef01-cut-1.json").write_bytes(b'{"session_id": "\xff"}\n')  # a cut's sidecar, no text
    assert "no cut on record" in show.block(crossings.parent)
    assert DAMAGED.format("labels/2026-11-12.md") in through("status", "--cwd", project)[1]


# --- 3: a project's crossings that is a link ---------------------------------------------------------


def test_a_crossings_folder_that_is_a_link_is_refused_by_switch_on_and_adopt_and_is_no_home(tmp_path):
    project, elsewhere = tmp_path / "project", tmp_path / "elsewhere"
    project.mkdir()
    elsewhere.mkdir()
    (project / "crossings").symlink_to(elsewhere, target_is_directory=True)
    for word in ("on", "adopt", "toggle"):
        assert through("switch", word, "--cwd", str(project)) == (1, LINKED_HOME.format(elsewhere.resolve())), word
    assert list(elsewhere.iterdir()) == []
    assert store.consented() == set() or all(top != str(project.resolve()) for top, _ in store.consented())
    switched_on(project)  # a line an older make wrote for it
    assert store.kept(project) is None and through("look", "--cwd", str(project)) == (1, NOT_ON)
    (project / "crossings").unlink()
    (project / "crossings").symlink_to(tmp_path / "nowhere", target_is_directory=True)  # a link that leads nowhere
    assert through("switch", "on", "--cwd", str(project)) == (1, LINKED_HOME.format((tmp_path / "nowhere").resolve()))
    assert not record.outside(project.resolve()).exists()  # and no home was made outside the project in its place


# --- 4: the frame and the hand-over, for a session no person sits in ------------------------------------


def test_frame_and_page_carry_nothing_to_a_session_no_person_sits_in(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    for verb in ("frame", "page"):
        for started in ({"CLAUDE_CODE_ENTRYPOINT": "sdk-cli"}, {}):
            done = as_the_module(verb, "--cwd", project, **started)
            assert (done.returncode, done.stdout) == (1, UNSEATED), (verb, started)
        done = as_the_module(verb, "--cwd", project, CLAUDE_CODE_ENTRYPOINT="cli")
        assert done.returncode == 0 and "Tern" in done.stdout, verb
        with started_by("sdk-ts"):
            assert shell(verb, "--cwd", project) == (1, UNSEATED)
        assert through(verb, "--cwd", project)[0] == 0  # at the person's own terminal


# --- 5: the frame within its most -----------------------------------------------------------------------


def test_the_frame_never_exceeds_its_most_and_a_long_line_at_the_door_says_where_it_is_whole(tmp_path):
    crossings, _ = home(tmp_path)
    long = (
        "The next step is the hull, then the mast, then the sails. " * 520
    ).strip()  # written by hand, past any mark
    (crossings / "labels").mkdir()
    (crossings / "labels" / "2026-11-12.md").write_text(
        f"| # | Label | Whose | Anchors |\n| --- | --- | --- | --- |\n| N1 | {long} | session | `{D}` |\n",
        encoding="utf-8",
    )
    store.build(crossings)
    for size in (frame.MOST, frame.SIZE, frame.LEAST):
        for new in (False, True):
            text = frame.compose(crossings, size, new=new)
            assert len(text) <= frame.MOST and "`labels N1` gives it whole" in text, (size, new, len(text))
    usual = ("We keep to the plan the person set, one step a day. " * 39).strip()  # about 2,000 characters
    assert 1900 < len(usual) < 2100 and store.mark(crossings, "next", "session", usual, [D])["id"] == "N2"
    text = frame.compose(crossings)
    assert usual in text and "gives it whole" not in text
    over = "a" * 4001
    assert store.mark(crossings, "next", "session", over, [D]) == {"written": False, "why": TOO_LONG}
    assert through("mark", "--kind", "work", "--anchors", D, over, "--cwd", str(crossings.parent)) == (
        1,
        f"not marked: {TOO_LONG}\n",
    )
    assert store.mark(crossings, "work", "session", "b" * 4000, [D])["written"]
    many = [f"model-{n}" for n in range(11)]  # the sentence about other models' lines names a few, and counts the rest
    assert frame.elsewhere(many).startswith("This home also holds lines made with other models, model-0, model-1, ")
    assert "model-7 and 3 more:" in frame.elsewhere(many) and "model-8" not in frame.elsewhere(many)


# --- 6: one folder by either spelling of its letters ----------------------------------------------------------


def test_one_folder_is_one_home_by_whichever_spelling_of_its_letters_it_is_reached(tmp_path):
    (tmp_path / "Probe").mkdir()
    blind = (tmp_path / "probe").exists()
    (tmp_path / "Probe").rmdir()
    if not blind:  # a disk that tells the letters' case apart has two folders here, not one
        try:
            import pytest
        except ImportError:
            return
        pytest.skip("the disk tells the case of letters apart")
    project = tmp_path / "Tern"
    (project / ".git").mkdir(parents=True)  # no crossings/ folder: its home lies outside it
    assert through("switch", "on", "--cwd", str(project)) == (0, ON)
    for other in (tmp_path / "tern", tmp_path / "TERN"):
        assert record.home(other) == record.home(project)
        assert store.kept(other) is not None and store.kept(other) == store.kept(project)
    boat = tmp_path / "Boat"
    (boat / "crossings").mkdir(parents=True)
    assert through("switch", "on", "--cwd", str(tmp_path / "BOAT")) == (0, ON)
    assert store.kept(boat) is not None and store.kept(tmp_path / "boat") == store.kept(boat)
    assert through("switch", "on", "--cwd", str(boat)) == (0, ON)
    tops = [given["project"] for given in store._record_lines() if given["project"].startswith(str(tmp_path.resolve()))]
    assert len(tops) == len(set(tops)) == 2, tops  # one line a project, whichever way it was spelled


# --- 7: a cut counted while the record of the spans is lost ----------------------------------------------------


def test_a_cut_counted_while_the_record_of_the_spans_is_lost_lists_nothing_said(tmp_path):
    crossings = tmp_path / "crossings"
    crossings.mkdir()
    assert through("switch", "on", "--cwd", str(tmp_path)) == (0, ON)
    assert through("switch", "off", "--cwd", str(tmp_path))[0] == 0
    assert through("switch", "on", "--cwd", str(tmp_path))[0] == 0  # the person's record now counts its lines
    (crossings / off.FILE).unlink()
    assert store.lost(crossings)
    path = written(tmp_path, BEFORE)
    event = {"transcript_path": str(path), "cwd": str(tmp_path), "session_id": "abcdef0123456789"}
    with started_by("cli"), set_to(CROSSING_WAIT="1"):
        hook.run({**event, "hook_event_name": "PostCompact", "trigger": "auto", "compact_summary": SUMMARY})
    side = json.loads((crossings / "abcdef01-cut-1.json").read_text(encoding="utf-8"))
    for voice in ("person", "session"):
        assert side[voice]["pointers"] == [] and side[voice]["messages"] == side[voice]["chars"] == 0, voice
    assert UNTOLD in (crossings / "abcdef01-cut-1.md").read_text(encoding="utf-8")


# --- 9: keys from the pages, under the lock --------------------------------------------------------------------


def test_the_next_key_comes_from_the_pages_and_two_marks_at_once_take_two(tmp_path):
    crossings, _ = home(tmp_path)
    with open(crossings / "hand-over.md", "a", encoding="utf-8") as handle:  # by hand, since the index was made
        handle.write(f"| W2 | Written by hand. | session | `{D}` |\n")
    out = store.mark(crossings, "work", "session", "Marked through the door.", [D], day="2026-11-12")
    assert out["id"] == "W3", out
    assert {(label["id"], label["text"]) for label in store.labels(crossings)} >= {
        ("W2", "Written by hand."),
        ("W3", "Marked through the door."),
    }
    barrier, real, outs = threading.Barrier(2), store._sources, []

    def slow(folder):  # two marks that reach their write at the same moment, where nothing keeps them apart
        try:
            barrier.wait(timeout=1)
        except threading.BrokenBarrierError:
            pass
        return real(folder)

    def marking(sentence):
        outs.append(store.mark(crossings, "work", "session", sentence, [D], day="2026-11-12"))

    store._sources = slow
    try:
        both = [threading.Thread(target=marking, args=(f"One of two at once, the {n}.",)) for n in ("first", "second")]
        for each in both:
            each.start()
        for each in both:
            each.join(30)
    finally:
        store._sources = real
    assert len({out["id"] for out in outs}) == 2 and all(out["written"] for out in outs), outs
    kept = {label["text"]: label["id"] for label in store.labels(crossings)}
    assert {kept["One of two at once, the first."], kept["One of two at once, the second."]} == {
        out["id"] for out in outs
    }


# --- 10: a strike and layer, with the lock and in place --------------------------------------------------------


def test_a_strike_and_layer_hold_the_homes_lock_and_put_each_file_in_its_place_whole(tmp_path):
    crossings, _ = home(tmp_path)
    page, labels_page = crossings / "said" / "session-.jsonl", crossings / "hand-over.md"
    waited = store.WAIT
    store.WAIT = 0.2
    held = store._locked(crossings)  # an archive, a mark or another strike at work in the home
    try:
        out = store.strike(crossings, D)
        assert out["struck"] is False and "nothing was struck" in out["why"], out
        assert D in ids(crossings) and not (crossings / "struck.txt").exists()
        assert store.layered(crossings, "made-up-model") is None and not (crossings / "models.txt").exists()
        assert through("layer", "made-up-model", "--cwd", str(crossings.parent)) == (
            1,
            "Another act was writing this home, so nothing was signed: try again in a moment.\n",
        )
        assert store.mark(crossings, "work", "session", "Marked while the home was held.", [D]) == {
            "written": False,
            "why": "another act was writing this home, so nothing was marked: try again in a moment",
        }
    finally:
        store._unlocked(crossings, held)
        store.WAIT = waited
    before = (page.stat().st_ino, labels_page.stat().st_ino)
    assert store.strike(crossings, D)["struck"] and D not in ids(crossings)
    assert page.stat().st_ino != before[0]  # written beside itself, then put in its place
    assert store.strike(crossings, "W1")["struck"] and labels_page.stat().st_ino != before[1]
    assert store.layered(crossings, "made-up-model") == (1, 2)


# --- 11: a clock set back while Crossings is off ------------------------------------------------------------------


def test_a_clock_set_back_while_crossing_is_off_keeps_all_that_was_said_then_off_the_record(tmp_path):
    def off_and_on(folder: Path, steady_on: float) -> tuple[Path, Path]:
        project, home_, path = public(folder)
        path.write_text("", encoding="utf-8")
        assert through("switch", "on", "--cwd", str(project)) == (0, ON)
        clock, steady = {"now": "2026-11-11T10:00:00.000000+00:00"}, {"at": 1000.0}
        was_now, was_steady = off.now, getattr(off, "steady", None)
        off.now, off.steady = (lambda: clock["now"]), (lambda: steady["at"])
        try:
            assert through("switch", "off", "--cwd", str(project))[0] == 0
            says(path, "20000002", "Said while off, before the clock was set back.", at="2026-11-11T10:00:05.000Z")
            clock["now"], steady["at"] = (
                "2026-11-11T09:59:30.000000+00:00",
                steady_on,
            )  # the clock was set back meanwhile
            assert through("switch", "on", "--cwd", str(project)) == (0, door.SWITCHED["again"] + "\n")
        finally:
            off.now = was_now
            if was_steady is None:
                del off.steady
            else:
                off.steady = was_steady
        store.archive(path, home_, whole=True)
        return home_, path

    for steady_on in (
        1060.0,
        5.0,
    ):  # a minute later by the steady clock; or a computer started again, when it cannot tell
        home_, _ = off_and_on(tmp_path / str(int(steady_on)), steady_on)
        assert "20000002" not in ids(home_), steady_on
        spans, unread = off.spans(home_)
        assert unread == 0 and off.inside(off.moment("2026-11-11T10:00:05Z"), spans), (spans, steady_on)


# --- 12: labels that arrive with no mark -------------------------------------------------------------------------


def test_a_label_that_arrives_without_a_mark_is_named_once_by_the_persons_next_status(tmp_path):
    crossings, _ = home(tmp_path)  # its first build knew R1 and W1
    project = str(crossings.parent)
    assert store.mark(crossings, "work", "session", "Marked through the door.", [D])["id"] == "W2"
    with open(crossings / "hand-over.md", "a", encoding="utf-8") as handle:  # a pull, a checkout or a hand
        handle.write(f"| R2 | Arrived with a pull. | his | `{A}` |\n")
    store.build(crossings)
    assert "Arrived" not in shell("status", "--bare", "--cwd", project)[1]
    told = through("status", "--cwd", project)[1]
    assert ARRIVED.format("R2 (a standing line about the two of you, speaking for the person)") in told, told
    assert "without a mark" not in through("status", "--cwd", project)[1]  # once
    store.build(crossings)
    assert "without a mark" not in through("status", "--cwd", project)[1]
    page = crossings / "hand-over.md"  # a label reworded by hand arrives anew
    page.write_text(
        page.read_text(encoding="utf-8").replace("Arrived with a pull.", "Arrived, and reworded."), encoding="utf-8"
    )
    store.build(crossings)
    assert (
        ARRIVED.format("R2 (a standing line about the two of you, speaking for the person)")
        in through("status", "--cwd", project)[1]
    )


# --- 13: the person's record, one switch at a time -----------------------------------------------------------------


def test_two_switches_at_once_keep_every_line_of_the_persons_record(tmp_path):
    one, two = tmp_path / "one", tmp_path / "two"
    for project in (one, two):
        (project / "crossings").mkdir(parents=True)
    assert through("switch", "on", "--cwd", str(one)) == (0, ON)
    real, started = os.replace, []

    def replace(src, dst, *rest, **given):  # the record is rewritten while another switch writes its line
        if Path(dst) == store.switched() and not started:
            started.append(threading.Thread(target=store.consent, args=(two,)))
            started[0].start()
            started[0].join(0.5)
        return real(src, dst, *rest, **given)

    os.replace = replace
    try:
        assert through("switch", "off", "--cwd", str(one))[0] == 0
    finally:
        os.replace = real
    started[0].join(30)
    tops = {given["project"] for given in store._record_lines() if given["project"].startswith(str(tmp_path.resolve()))}
    assert tops == {str(one.resolve()), str(two.resolve())}, tops


# --- 15: ids of eight characters that two messages share -------------------------------------------------------------


def test_two_messages_that_share_an_eight_character_id_are_told_apart(tmp_path):
    crossings, _ = home(tmp_path)
    project = str(crossings.parent)
    first, twin = f"{A}{WHOLE}", f"{A}-1111-4000-8000-000000000000"
    other = row("user", A, 9, "Another message whose id begins the same.")
    other["uuid"] = twin
    path = tmp_path / "twin-0002.jsonl"
    path.write_text(json.dumps(other) + "\n", encoding="utf-8")
    assert store.archive(path, crossings) == 1
    store.build(crossings)
    code, out = through("strike", A, "--cwd", project)
    assert code == 1 and first in out and twin in out and "nothing was struck" in out, out
    assert ids(crossings).count(A) == 2 and not (crossings / "struck.txt").exists()
    code, out = through("thread", A, "--cwd", project)
    assert code == 0 and f"two messages are named `{A}`" in out and first in out and twin in out, out
    told = through("status", "--cwd", project)[1]
    assert COLLIDED.format(A) in told, told
    assert "share the id" not in through("status", "--cwd", project)[1]  # once
    assert through("strike", twin, "--cwd", project)[0] == 0
    assert [said["uuid"] for said in store._archived(crossings) if said["id"] == A] == [first]
    code, out = through("thread", A, "--cwd", project)
    assert code == 0 and "My boat is called Tern." in out


# --- 16: a subagent's rows ------------------------------------------------------------------------------------------------


def test_a_subagents_rows_are_never_archived_as_anyones_words(tmp_path):
    rows = [
        {**row("user", "51de0001", 1, "A prompt a subagent was given."), "isSidechain": True},
        {**row("assistant", "51de0002", 2, [{"type": "text", "text": "A subagent's answer."}]), "isSidechain": True},
        row("user", "0a0a0a0a", 3, "The person's own words."),
    ]
    crossings, path = home(tmp_path, rows=rows)
    assert ids(crossings) == ["0a0a0a0a"]
    kept, missing = handover.words(path, ["51de0001", "51de0002", "0a0a0a0a"])
    assert [k[0] for k in kept] == ["0a0a0a0a"] and missing == ["51de0001", "51de0002"]


if __name__ == "__main__":
    for name, test in sorted(globals().items()):
        if name.startswith("test_"):
            folder = Path(tempfile.mkdtemp(prefix="crossing-test-"))
            try:
                test(folder) if test.__code__.co_argcount else test()
            finally:  # a test that fails leaves nothing behind either
                sweep(folder)
            print("ok", name)
